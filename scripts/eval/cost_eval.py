"""Gerçek prod cost eval — D1 (yapısal MC) + D2b (geo direktifi) + A+C canlı ayarlarla.

config defaults kullanılır (critic 0.75 / overshoot 1.8 = A+C prod). Grade 8, mixed
default dağıtım (figürler DAHİL), yeni_nesil (premium yolu), dynamic thinking (prod grade-8).
Amaç: D1+D2b öncesi baseline'la (geometri ₺7.64 / cebir ₺4.76 / fen ₺4.05 / türkçe ₺1.41)
₺/kağıt + drop kıyası.

Kullanım: PYTHONIOENCODING=utf-8 python scripts/eval/cost_eval.py [--iters 2] [--qcount 10]
"""
from __future__ import annotations
import argparse, io, logging, re, statistics, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from app.config import settings  # noqa: E402
from app.models.enums import Difficulty, SubjectId  # noqa: E402
from app.services.agent import GeminiAgent  # noqa: E402
from app.services.history import GENERATION_HISTORY  # noqa: E402

# agent drop loglarını yakala
_buf = io.StringIO()
_h = logging.StreamHandler(_buf); _h.setLevel(logging.INFO)
logging.getLogger("app.services.agent").addHandler(_h)
logging.getLogger("app.services.agent").setLevel(logging.INFO)

SCEN = [
    ("mat_geometri", SubjectId.MATEMATIK, "geometri", None, "M.8.4.1.4", Difficulty.ZOR),
    ("mat_cebir",    SubjectId.MATEMATIK, "cebir",    None, "M.8.2.1.1", Difficulty.ZOR),
    ("fen",       SubjectId.FEN,    None, "fen-8-unite-3-yasamin-gizemi",   "FB.8.3.3.2", Difficulty.ZOR),
    ("turkce",    SubjectId.TURKCE, None, "turkce-8-tema-3-doga-ve-insan",  "TR.8.OKA.3", Difficulty.ZOR),
]
BASELINE = {"mat_geometri": 7.64, "mat_cebir": 4.76, "fen": 4.05, "turkce": 1.41}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iters", type=int, default=2)
    ap.add_argument("--qcount", type=int, default=10)
    args = ap.parse_args()

    # PROD ayarları: cache kapalı (gerçek üretim ölç), fallback kapalı (izolasyon).
    # critic/overshoot DOKUNULMAZ → config default = A+C (0.75/1.8).
    settings.enable_generation_cache = False
    settings.gemini_fallback_models = ""
    rate = settings.usd_try_rate

    # prod grade-8: ucuz model (odeyen yok) + dynamic thinking (grade_8=-1)
    agent = GeminiAgent(model="gemini-2.5-flash", thinking_budget=-1)
    rows: dict[str, list[dict]] = {}
    for label, subj, topic, unit, kaz, diff in SCEN:
        rows[label] = []
        for it in range(args.iters):
            _buf.truncate(0); _buf.seek(0)
            GENERATION_HISTORY.clear()
            try:
                qs = agent.generate(
                    grade=8, topic_id=topic, unit_id=unit, kazanim_kod=kaz,
                    difficulty=diff, question_count=args.qcount, tenant_id=f"cost_{label}_{it}",
                    yeni_nesil=True, subject=subj,
                )
                tr = agent.build_last_trace().model_dump()
                log = _buf.getvalue()
                rows[label].append({
                    "delivered": tr.get("delivered_count", 0),
                    "requested": tr.get("requested_count", 0),
                    "critic_rej": tr.get("critic_rejected", 0),
                    "cost": tr.get("estimated_cost_usd", 0.0),
                    "tok": tr.get("completion_tokens", 0),
                    "drop_svg": len(re.findall(r"Bozuk SVG|Şekilsiz görsel", log)),
                    "drop_mc": len(re.findall(r"şıksız|Yapısal şıksız|Şıksız", log)),
                    "geo_used": log.count("{{geo") + 1 if False else None,
                })
                print(f"  {label} it{it}: del={rows[label][-1]['delivered']}/{args.qcount} "
                      f"cost=${rows[label][-1]['cost']:.4f} (₺{rows[label][-1]['cost']*rate:.2f}) "
                      f"critic_rej={rows[label][-1]['critic_rej']} drop_svg={rows[label][-1]['drop_svg']} "
                      f"drop_mc={rows[label][-1]['drop_mc']}")
            except Exception as e:  # noqa: BLE001
                print(f"  {label} it{it}: HATA {e}")

    print("\n" + "=" * 72)
    print(f"COST EVAL — D1+D2b+A+C canlı · grade 8 · dynamic thinking · kur ₺{rate}/$")
    print("=" * 72)
    print(f"{'ders':<14} {'₺/kağıt':>9} {'baseline':>9} {'değişim':>9} {'teslim':>7} {'svg_drop':>9} {'mc_drop':>8}")
    tot_now = []
    for label, _, _, _, _, _ in SCEN:
        ok = [r for r in rows[label] if r["delivered"] > 0]
        if not ok:
            print(f"{label:<14} {'ERROR':>9}"); continue
        try_paper = statistics.mean(r["cost"] for r in ok) * rate
        deliv = statistics.mean(r["delivered"] / r["requested"] for r in ok if r["requested"])
        svgd = statistics.mean(r["drop_svg"] for r in ok)
        mcd = statistics.mean(r["drop_mc"] for r in ok)
        base = BASELINE.get(label, 0)
        chg = f"{(try_paper-base)/base*100:+.0f}%" if base else "-"
        tot_now.append(try_paper)
        print(f"{label:<14} {try_paper:>8.2f} {base:>9.2f} {chg:>9} {deliv:>7.2f} {svgd:>9.1f} {mcd:>8.1f}")
    if tot_now:
        base_tot = statistics.mean(BASELINE.values())
        print("-" * 72)
        print(f"{'ORTALAMA':<14} {statistics.mean(tot_now):>8.2f} {base_tot:>9.2f} "
              f"{(statistics.mean(tot_now)-base_tot)/base_tot*100:>+8.0f}%")


if __name__ == "__main__":
    main()
