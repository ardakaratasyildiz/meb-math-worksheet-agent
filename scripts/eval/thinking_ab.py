"""Thinking-bütçesi A/B — grade 8, yeni_nesil (premium) yolu, ders ders.

Amaç: gemini_thinking_budget'ı -1 (dinamik/sınırsız, mevcut prod) yerine sabit
tavana çekmenin KALİTE ve MALİYETE etkisini GERÇEK sayılarla ölçmek. Yalnız
grade 8'i test eder — thinking=-1 sadece orada (grade_8 + güçlü model) geçerli;
grade 5-7 zaten 512'ye, 1-4 = 0'a kapalı, dokunulmuyor.

Her (ders × thinking_seviyesi × iterasyon) için agent.generate(yeni_nesil=True)
çağırır, trace'ten maliyet/token, critic/teslim'den kalite proxy'si toplar, ham
soruları JSON'a döker (elle kalite kıyası için).

Kullanım:
    PYTHONIOENCODING=utf-8 python scripts/eval/thinking_ab.py --smoke
    PYTHONIOENCODING=utf-8 python scripts/eval/thinking_ab.py --iters 2 --qcount 10
    PYTHONIOENCODING=utf-8 python scripts/eval/thinking_ab.py --levels dynamic,cap1024

Maliyet uyarısı: grade 8 + premium → güçlü model (3.5-flash) + (kontrolde) sınırsız
thinking → çağrı başına PAHALI olabilir. Matris'i küçük tut.
"""
from __future__ import annotations

import argparse
import json
import logging
import statistics
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from app.config import settings  # noqa: E402
from app.models.enums import Difficulty, SubjectId, QuestionType  # noqa: E402
import app.services.agent as agent_mod  # noqa: E402
from app.services.agent import GeminiAgent  # noqa: E402
from app.services.history import GENERATION_HISTORY  # noqa: E402

# --- B kaldıracı: SVG-figür tiplerini tip dağıtımından çıkar (97 "şekilsiz" drop kaynağı).
# yeni_nesil modda diversity.py figür payını 1.5× artırıyor; combo config'te bunu tersine
# çevirip figür tiplerini metin tiplerine dağıtırız. distribute_question_types agent
# namespace'inde çağrılıyor → orada patch'lenir.
_FIG_TYPES = {QuestionType.GORSEL_GEOMETRI, QuestionType.ORUNTU_SEKIL, QuestionType.GRAFIK_OKUMA}
_ORIG_DIST = agent_mod.distribute_question_types


def _no_figure_dist(total, difficulty, topic_id=None, allowed_types=None, yeni_nesil=False):
    if allowed_types is not None:
        allowed_types = {t for t in allowed_types if t not in _FIG_TYPES}
    d = _ORIG_DIST(total, difficulty, topic_id, allowed_types, yeni_nesil)
    removed = sum(v for k, v in list(d.items()) if k in _FIG_TYPES)
    d = {k: v for k, v in d.items() if k not in _FIG_TYPES}
    if removed and d:  # figür payını en büyük metin tipine ekle
        top = max(d, key=d.get)
        d[top] = d[top] + removed
    return d

logger = logging.getLogger("thinking_ab")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


@dataclass(frozen=True)
class Scen:
    label: str
    subject: SubjectId
    topic_id: str | None      # math (legacy) yolu
    unit_id: str | None       # non-math + yeni MEB ünite yolu
    kazanim_kod: str
    difficulty: Difficulty


ZOR = Difficulty.ZOR
ORTA = Difficulty.ORTA

# Grade 8 senaryoları (subject_resolve haritalamasından doğrulanmış kodlar).
SCENARIOS: list[Scen] = [
    Scen("mat_geometri", SubjectId.MATEMATIK, "geometri", None, "M.8.4.1.4", ZOR),
    Scen("mat_cebir",    SubjectId.MATEMATIK, "cebir",    None, "M.8.2.1.1", ZOR),
    Scen("fen",       SubjectId.FEN,       None, "fen-8-unite-3-yasamin-gizemi",        "FB.8.3.3.2", ZOR),
    Scen("turkce",    SubjectId.TURKCE,    None, "turkce-8-tema-3-doga-ve-insan",       "TR.8.OKA.3", ZOR),
    Scen("sosyal",    SubjectId.SOSYAL,    None, "sosyal-8-unite-3-mill-mucadele",      "İTA.8.3.3",  ZOR),
    Scen("ingilizce", SubjectId.INGILIZCE, None, "ingilizce-8-tema-3-personal-life-and-well-being-with-mobile-phones-an", "ENG.8.3.G1", ZOR),
]

# Thinking seviyeleri. Bütçe DOĞRUDAN GeminiAgent(thinking_budget=) ile geçilir
# (production yolu: routers model_and_thinking_for → GeminiAgent(model=, thinking_budget=)).
# GeminiAgent() argümansız kurulursa thinking_budget=None → SDK dinamik → override ETKİSİZ.
LEVELS: dict[str, int] = {
    "dynamic": -1,    # KONTROL = mevcut prod (sınırsız/dinamik)
    "cap2048": 2048,
    "cap1024": 1024,
    "cap512": 512,
    "cap0": 0,        # thinking tamamen kapalı (alt sınır referansı)
}

# Test modeli — gözlemlenen prod modeli (grade 8, ödeyen yokken ucuz model).
TEST_MODEL = "gemini-2.5-flash"


@dataclass
class RunRow:
    level: str
    scen: str
    iter: int
    model: str = ""
    delivered: int = 0
    requested: int = 0
    critic_rejected: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    duration_s: float = 0.0
    error: str | None = None
    questions: list[dict] = field(default_factory=list)


def run_one(agent: GeminiAgent, scen: Scen, qcount: int, tenant: str) -> RunRow:
    row = RunRow(level="", scen=scen.label, iter=0)
    start = time.time()
    try:
        qs = agent.generate(
            grade=8,
            topic_id=scen.topic_id,
            kazanim_kod=scen.kazanim_kod,
            difficulty=scen.difficulty,
            question_count=qcount,
            tenant_id=tenant,
            yeni_nesil=True,
            unit_id=scen.unit_id,
            subject=scen.subject,
        )
        tr = agent.build_last_trace().model_dump()
        row.model = tr.get("model_used", "")
        row.delivered = tr.get("delivered_count", 0)
        row.requested = tr.get("requested_count", 0)
        row.critic_rejected = tr.get("critic_rejected", 0)
        row.prompt_tokens = tr.get("prompt_tokens", 0)
        row.completion_tokens = tr.get("completion_tokens", 0)
        row.cost_usd = tr.get("estimated_cost_usd", 0.0)
        row.questions = [
            {"q": q.question, "a": q.answer, "type": q.question_type.value,
             "steps": (q.solution_steps or "")[:600]}
            for q in qs
        ]
    except Exception as exc:  # noqa: BLE001
        row.error = str(exc)
        logger.warning("  [%s] HATA: %s", scen.label, exc)
    finally:
        row.duration_s = time.time() - start
    return row


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--levels", type=str, default="dynamic,cap2048,cap1024")
    ap.add_argument("--iters", type=int, default=2)
    ap.add_argument("--qcount", type=int, default=10)
    ap.add_argument("--subjects", type=str, default=None,
                    help="Senaryo label'ları (virgülle). Boş=hepsi.")
    ap.add_argument("--smoke", action="store_true",
                    help="Hızlı doğrulama: dynamic × tüm senaryo × 1 iter × 3 soru.")
    ap.add_argument("--out-dir", type=str, default=str(ROOT / "knowledge_base" / "eval"))
    args = ap.parse_args()

    if args.smoke:
        args.levels = "dynamic"
        args.iters = 1
        args.qcount = 3

    levels = [l.strip() for l in args.levels.split(",") if l.strip()]
    # "combo" = A+B+C birleşik (thinking dinamik + critic 0.75 + overshoot 1.8 + figür-strip).
    bad = [l for l in levels if l not in LEVELS and l != "combo"]
    if bad:
        logger.error("Geçersiz seviye: %s (geçerli: %s + combo)", bad, list(LEVELS))
        sys.exit(2)

    scens = SCENARIOS
    if args.subjects:
        want = {s.strip() for s in args.subjects.split(",")}
        scens = [s for s in SCENARIOS if s.label in want]
        if not scens:
            logger.error("Senaryo bulunamadı: %s", want)
            sys.exit(2)

    # A/B izolasyonu: cache KAPALI (aksi halde bir seviye diğerinin sonucunu çeker),
    # fallback KAPALI (429 başka modele düşüp maliyeti kirletmesin → error kaydı).
    settings.enable_generation_cache = False
    settings.gemini_fallback_models = ""
    settings.enable_critic = True
    settings.enable_semantic_dedup = True

    logger.info("Thinking A/B | levels=%s iters=%d qcount=%d scen=%d",
                levels, args.iters, args.qcount, len(scens))

    rows: list[RunRow] = []
    for level in levels:
        if level == "combo":
            # A+B+C: thinking DİNAMİK korunur (kaliteyi bozmadığı test edildi);
            # yalnız format-drop döngüsü kısılır.
            budget = -1                                    # thinking dinamik (baseline ile aynı)
            settings.critic_min_confidence = 0.75          # A: tartışmalı redleri geçir
            settings.generation_overshoot_ratio = 1.8      # C: drop'ları ilk çağrıda absorbe et
            agent_mod.distribute_question_types = _no_figure_dist  # B: SVG-figür tiplerini çıkar
        else:
            budget = LEVELS[level]
            settings.critic_min_confidence = 0.6           # baseline değerleri
            settings.generation_overshoot_ratio = 1.3
            agent_mod.distribute_question_types = _ORIG_DIST
        # KRİTİK: bütçeyi DOĞRUDAN constructor'a geç (production yolu). Settings
        # override'ı tek başına ETKİSİZ — agent.generate model_and_thinking_for
        # ÇAĞIRMAZ; thinking constructor'da sabitlenir. (Settings de tutarlılık için set.)
        settings.gemini_thinking_budget_grade_8 = budget
        settings.gemini_thinking_budget_strong = budget
        logger.info("=" * 60)
        logger.info("LEVEL=%s (thinking_budget=%d, model=%s, critic_conf=%.2f, overshoot=%.1f)",
                    level, budget, TEST_MODEL, settings.critic_min_confidence,
                    settings.generation_overshoot_ratio)
        GENERATION_HISTORY.clear()
        agent = GeminiAgent(model=TEST_MODEL, thinking_budget=budget)
        tenant = f"think_{level}"
        for scen in scens:
            for it in range(args.iters):
                r = run_one(agent, scen, args.qcount, tenant)
                r.level = level
                r.iter = it
                rows.append(r)
                logger.info(
                    "  %-12s it%d: model=%s del=%d/%d critic_rej=%d compl_tok=%d cost=$%.4f %.1fs%s",
                    scen.label, it, r.model or "-", r.delivered, r.requested,
                    r.critic_rejected, r.completion_tokens, r.cost_usd, r.duration_s,
                    f" ERR" if r.error else "",
                )
        GENERATION_HISTORY.clear()

    # -- Rapor -------------------------------------------------------------
    rate = settings.usd_try_rate
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Ham (sorular dahil) — elle kalite kıyası için.
    raw = [
        {k: v for k, v in r.__dict__.items()}
        for r in rows
    ]
    raw_path = out_dir / f"thinking_raw_{ts}.json"
    raw_path.write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8")

    # Özet: (level, scen) kırılımı + level toplamı.
    def agg(subset: list[RunRow]) -> dict:
        ok = [r for r in subset if not r.error and r.delivered > 0]
        n = len(ok)
        if n == 0:
            return {"n_ok": 0, "n_err": len(subset)}
        cost = statistics.mean(r.cost_usd for r in ok)
        compl = statistics.mean(r.completion_tokens for r in ok)
        deliv = statistics.mean(r.delivered / r.requested for r in ok if r.requested)
        seen = [(r.delivered + r.critic_rejected) for r in ok]
        cpass = statistics.mean(
            r.delivered / (r.delivered + r.critic_rejected)
            for r in ok if (r.delivered + r.critic_rejected) > 0
        )
        dur = statistics.mean(r.duration_s for r in ok)
        return {
            "n_ok": n, "n_err": len(subset) - n,
            "cost_usd": round(cost, 5), "cost_try": round(cost * rate, 3),
            "compl_tokens": round(compl), "delivered_ratio": round(deliv, 3),
            "critic_pass": round(cpass, 3), "dur_s": round(dur, 1),
        }

    report: dict = {"timestamp": ts, "usd_try_rate": rate,
                    "iters": args.iters, "qcount": args.qcount,
                    "by_level": {}, "by_level_scen": {}}
    for level in levels:
        report["by_level"][level] = agg([r for r in rows if r.level == level])
        for scen in scens:
            key = f"{level}|{scen.label}"
            report["by_level_scen"][key] = agg(
                [r for r in rows if r.level == level and r.scen == scen.label]
            )
    rep_path = out_dir / f"thinking_summary_{ts}.json"
    rep_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    # Konsol tablosu
    print("\n" + "=" * 78)
    print(f"THINKING A/B — grade 8, yeni_nesil (premium). kur=₺{rate}/$")
    print("=" * 78)
    print(f"{'level':<9} {'scen':<13} {'model':<18} {'$/kağıt':>8} {'₺/kağıt':>8} "
          f"{'compl_tok':>9} {'teslim':>7} {'critic':>7}")
    for level in levels:
        for scen in scens:
            a = report["by_level_scen"][f"{level}|{scen.label}"]
            model = next((r.model for r in rows
                          if r.level == level and r.scen == scen.label and r.model), "-")
            if a.get("n_ok"):
                print(f"{level:<9} {scen.label:<13} {model:<18} "
                      f"{a['cost_usd']:>8.4f} {a['cost_try']:>8.2f} "
                      f"{a['compl_tokens']:>9} {a['delivered_ratio']:>7.2f} {a['critic_pass']:>7.2f}")
            else:
                print(f"{level:<9} {scen.label:<13} {'ERROR':<18} (n_err={a.get('n_err')})")
    print("-" * 78)
    for level in levels:
        a = report["by_level"][level]
        if a.get("n_ok"):
            print(f"{level:<9} {'TOPLAM':<13} {'':<18} {a['cost_usd']:>8.4f} {a['cost_try']:>8.2f} "
                  f"{a['compl_tokens']:>9} {a['delivered_ratio']:>7.2f} {a['critic_pass']:>7.2f}")
    print("=" * 78)
    print(f"Ham çıktı (sorular): {raw_path}")
    print(f"Özet: {rep_path}")


if __name__ == "__main__":
    main()
