"""Kalite terazisi — sınav arabası (docs/COST_QUALITY_V2_PLAN.md §2c/2d).

İki soruyu AYRI ölçer:
  S1 (kalite):  denetleyici BOZUK sette kusuru yakalıyor mu?  → recall
  S2 (maliyet): denetleyici ALTIN sette iyi soruyu boşuna eliyor mu? → yanlış-alarm

İki katman AYRI raporlanır:
  Katman 1 — deterministik (bedava, LLM yok):
      structured.structured_content_issue, structured.reference_integrity_issue,
      math_verifier (yalnız salt_islem/islem).
  Katman 2 — LLM critic (GeminiCritic, flash-lite, gruplu):
      settings.critic_min_confidence eşiği ÜRETİMDEKİ (agent.py) mantıkla BİREBİR
      uygulanır: `not is_valid and confidence >= critic_min_confidence` → red.

Maliyet disiplini: bir kusur tipinin 5 örneği DE deterministik katmanda
yakalanmışsa o tip için critic ÇAĞRILMAZ (bütçe — zaten cevap biliniyor).
Varsayılan koşuda toplam critic çağrısı ~26 (≤30 hedefi).

FAIL-OPEN AYRIMI (2026-07-28 must-fix — terazinin KENDİSİ fail-open'a kör olmasın):
`GeminiCritic.evaluate()` sunucu hatasında (ör. 503) İÇERİDE kendi retry'ını
tüketip BOŞ liste döner (bkz. app/services/critic.py `_evaluate_chunk`). Dışarıdan
tek sinyal budur. Bu terazi o sinyali "critic yakalayamadı" (0/5) ile
KARIŞTIRMAZ: eksik verdict'li kayıtlar bir kez YENİDEN denenir; hâlâ eksikse
`unmeasured` ("ölçülemedi") sayılır ve critic paydasından DÜŞER — asla
"yakalanmadı" hücresine karışmaz. Bkz. `critic_flags()`.

Kullanım:
    python scripts/eval/quality_bench.py --no-llm
    python scripts/eval/quality_bench.py --limit 50 --iters 2 --out PATH
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from app.config import settings  # noqa: E402
from app.data.curriculum import get_topics_for_grade  # noqa: E402
from app.models.enums import Difficulty, QuestionType, SubjectId  # noqa: E402
from app.models.schemas import Question  # noqa: E402
from app.services.math_verifier import verify_batch as verify_math_batch  # noqa: E402
from app.services.structured import (  # noqa: E402
    reference_integrity_issue,
    structured_content_issue,
)
from app.subjects import get_content_module  # noqa: E402

DEFAULT_GOLD = ROOT / "knowledge_base" / "eval" / "gold" / "gold_questions.json"
DEFAULT_BROKEN = ROOT / "knowledge_base" / "eval" / "gold" / "broken_questions.json"
DEFAULT_OUT_DIR = ROOT / "knowledge_base" / "eval" / "gold"

_MATH_VERIFIABLE = {QuestionType.SALT_ISLEM.value, QuestionType.ISLEM.value}

# Kaba maliyet tahmini (flash-lite, ~10 soru/grup) — plan §2c: 240 soru/~24 çağrı
# ≈ $0.02 → çağrı başına ~$0.00083. Kesin değil, yalnız ÖN TAHMİN (rapor başında).
_EST_USD_PER_CALL = 0.02 / 24


# ── Yardımcılar ───────────────────────────────────────────────────────────────

def _load(path: Path) -> list[dict]:
    if not path.exists():
        print(f"HATA: {path} yok. Önce build_gold_set.py / mutations.py koş.")
        raise SystemExit(1)
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["questions"]


def _rec_id(rec: dict) -> str:
    return rec.get("broken_id") or rec.get("gold_id") or rec.get("question", "")[:30]


def _to_question(rec: dict, number: int) -> Question:
    try:
        qtype = QuestionType(rec["question_type"])
    except ValueError:
        qtype = QuestionType.SOZEL_PROBLEM
    return Question(
        number=number,
        question=rec["question"],
        answer=rec["answer"],
        solution_steps=rec.get("solution_steps") or "",
        kazanim_kod=rec["kazanim_kod"],
        question_type=qtype,
        options=rec.get("options"),
        correct_index=rec.get("correct_index"),
    )


_KAZANIM_TEXT_CACHE: dict[tuple[str, int, str], str | None] = {}


def _kazanim_text_in_subject(subject: str, grade: int, kazanim_kod: str) -> str | None:
    """Tek bir dersin müfredatında kazanım kodunu arar. Bulamazsa None."""
    if subject == "matematik":
        for topic in get_topics_for_grade(grade):
            for k in topic["kazanimlar"]:
                if k["kod"] == kazanim_kod:
                    return k["metin"]
        return None
    try:
        content = get_content_module(SubjectId(subject))
    except ValueError:
        return None
    if content is None:
        return None
    found = content.find_unit_by_kazanim(kazanim_kod)
    if found is None:
        return None
    g, unit = found
    k = content.get_unit_kazanim(g, unit["unit_id"], kazanim_kod)
    return k["metin"] if k is not None else None


_ALL_SUBJECTS = ["matematik", "turkce", "sosyal", "ingilizce", "fen"]


def _kazanim_text(subject: str, grade: int, kazanim_kod: str) -> str | None:
    """Kazanım kodunu GERÇEK metne çözer (agent.py'nin yaptığı gibi ÖNCE kaydın
    kendi dersinde). `kazanim_mismatch` mutasyonu kasıtlı olarak BAŞKA bir dersin
    GEÇERLİ kodunu yazdığı için (ör. matematik sorusuna 'TR.8.SAN.1'), kaydın
    kendi dersinde bulunamazsa TÜM derslerde aranır — bu, critic'e "iddia edilen
    kazanımın GERÇEK tanımı" verir (bir editörün yapacağı gibi: kod ne anlama
    geliyor, bak) → critic domain uyumsuzluğunu (edebi sanat tanımı vs. matematik
    sorusu) fark etme ŞANSI bulur. Hiçbir derste bulunamazsa None (çağıran
    kaydı 'çözülemedi' sayıp critic katmanından atlar)."""
    key = (subject, grade, kazanim_kod)
    if key in _KAZANIM_TEXT_CACHE:
        return _KAZANIM_TEXT_CACHE[key]

    text = _kazanim_text_in_subject(subject, grade, kazanim_kod)
    if text is None:
        for other_subject in _ALL_SUBJECTS:
            if other_subject == subject:
                continue
            for other_grade in range(1, 9):
                text = _kazanim_text_in_subject(other_subject, other_grade, kazanim_kod)
                if text is not None:
                    break
            if text is not None:
                break
    _KAZANIM_TEXT_CACHE[key] = text
    return text


def det_issue(rec: dict) -> str | None:
    """Katman 1 — deterministik doğrulayıcıların ÜÇÜ de dener. İlk bulunan neden
    döner; hiçbiri bulamazsa None (geçer)."""
    try:
        qtype = QuestionType(rec["question_type"])
    except ValueError:
        return None
    question = rec["question"]

    issue = structured_content_issue(qtype, question)
    if issue:
        return f"structured_content_issue: {issue}"

    issue = reference_integrity_issue(question)
    if issue:
        return f"reference_integrity_issue: {issue}"

    if rec["question_type"] in _MATH_VERIFIABLE:
        q = _to_question(rec, 1)
        verdicts = verify_math_batch([q])
        for v in verdicts:
            if v.is_verifiable and not v.is_valid:
                return f"math_verifier: {v.reason}"
    return None


class CriticUnavailable(Exception):
    pass


def _get_critic():
    if not settings.gemini_api_key:
        raise CriticUnavailable("GEMINI_API_KEY boş")
    from app.services.critic import CriticError, GeminiCritic
    try:
        return GeminiCritic()
    except CriticError as exc:
        raise CriticUnavailable(str(exc)) from exc


def _build_kazanimlar_and_difficulty(resolved: list[tuple[int, dict]]) -> tuple[list[dict], Difficulty]:
    seen_kod: set[str] = set()
    kazanimlar: list[dict] = []
    for _, rec in resolved:
        kod = rec["kazanim_kod"]
        if kod not in seen_kod:
            seen_kod.add(kod)
            kazanimlar.append(
                {"kod": kod, "metin": _kazanim_text(rec["subject"], rec["grade"], kod) or kod}
            )
    # Tek çağrıda TEK zorluk gerekir — grubun ÇOĞUNLUK zorluğu kullanılır (yaklaşıklık;
    # bench basitliği için kabul edilebilir, agent.py prod akışında zaten tek-zorluklu
    # bucket'lar geçer).
    diffs = Counter(rec["difficulty"] for _, rec in resolved)
    majority = diffs.most_common(1)[0][0]
    try:
        difficulty = Difficulty(majority)
    except ValueError:
        difficulty = Difficulty.ORTA
    return kazanimlar, difficulty


def _call_critic(
    critic, subset: list[tuple[int, dict]], kazanimlar: list[dict], difficulty: Difficulty
) -> tuple[list, set[int]]:
    """subset: [(orijinal_index, rec), ...] — YEREL index'lerle (0..len(subset)-1)
    critic'e sorar. Dönüş: (verdicts, dönen_yerel_index_kümesi). Beklenmeyen bir
    istisna da fail-open gibi ele alınır (boş sonuç) — bu fonksiyon HİÇ raise etmez."""
    questions = [_to_question(rec, n + 1) for n, (_, rec) in enumerate(subset)]
    try:
        verdicts = critic.evaluate(questions, kazanimlar, difficulty, context="") or []
    except Exception as exc:  # noqa: BLE001 — critic.py normalde raise etmez; savunma amaçlı.
        print(f"UYARI: critic.evaluate() beklenmeyen istisna fırlattı (fail-open sayılıyor): {exc}")
        verdicts = []
    got = {v.question_index for v in verdicts if 0 <= v.question_index < len(subset)}
    return verdicts, got


def critic_flags(
    critic, records: list[dict]
) -> tuple[list[bool], list[int], list[int], bool]:
    """records listesindeki her kayıt için critic'in RED edip etmediğini döner
    (üretimdeki agent.py mantığıyla BİREBİR: not is_valid AND confidence >= eşik).

    Dönüş: (flags, unresolved, unmeasured, fail_open_detected)
      - unresolved:  kazanım metni çözülemediği için critic'e HİÇ gönderilmeyen
        orijinal index'ler (bench sınırlaması — critic'in suçu değil).
      - unmeasured:  critic'e gönderildi ama verdict HİÇ dönmedi (fail-open —
        ör. 503, `_evaluate_chunk` içeride retry'ını tüketip boş döndü) — bir kez
        YENİDEN denendi, hâlâ eksikse burada. "yakalanmadı" (False) İLE ASLA
        KARIŞTIRILMAZ; çağıran bu kayıtları critic paydasından düşürmeli.
      - fail_open_detected: bu çağrıda EN AZ bir fail-open belirtisi görüldü mü
        (ilk deneme eksik döndüyse True, retry sonucu ne olursa olsun).
    """
    resolved: list[tuple[int, dict]] = []
    unresolved: list[int] = []
    for i, rec in enumerate(records):
        text = _kazanim_text(rec["subject"], rec["grade"], rec["kazanim_kod"])
        if text is None:
            unresolved.append(i)
        else:
            resolved.append((i, rec))

    flags = [False] * len(records)
    if not resolved:
        return flags, unresolved, [], False

    kazanimlar, difficulty = _build_kazanimlar_and_difficulty(resolved)

    def _apply(verdicts, subset: list[tuple[int, dict]]) -> None:
        for v in verdicts:
            if (
                0 <= v.question_index < len(subset)
                and not v.is_valid
                and v.confidence >= settings.critic_min_confidence
            ):
                orig_idx = subset[v.question_index][0]
                flags[orig_idx] = True

    verdicts, got = _call_critic(critic, resolved, kazanimlar, difficulty)
    fail_open_detected = len(got) < len(resolved)
    _apply(verdicts, resolved)

    missing_local = [i for i in range(len(resolved)) if i not in got]
    unmeasured: list[int] = []
    if missing_local:
        retry_subset = [resolved[i] for i in missing_local]
        verdicts2, got2 = _call_critic(critic, retry_subset, kazanimlar, difficulty)
        _apply(verdicts2, retry_subset)
        still_missing_local = [i for i in range(len(retry_subset)) if i not in got2]
        unmeasured = [retry_subset[i][0] for i in still_missing_local]

    return flags, unresolved, unmeasured, fail_open_detected


# ── Maliyet tahmini (ÇAĞRI YAPMADAN) ─────────────────────────────────────────

def estimate_critic_calls(gold: list[dict], broken: list[dict], limit: int | None) -> int:
    """Bir TEK koşu için tahmini critic çağrı sayısı (--iters ile main() çarpar)."""
    by_defect: dict[str, list[dict]] = {}
    for rec in broken:
        by_defect.setdefault(rec["defect_type"], []).append(rec)

    total = 0
    for _defect_type, group in by_defect.items():
        det_n = sum(1 for r in group if det_issue(r) is not None)
        if det_n < len(group):
            total += math.ceil(len(group) / max(1, settings.critic_batch_size))

    gold_for_alarm = gold if limit is None else gold[:limit]
    det_false_n = sum(1 for r in gold_for_alarm if det_issue(r) is not None)
    remaining_n = len(gold_for_alarm) - det_false_n
    total += math.ceil(remaining_n / max(1, settings.critic_batch_size))
    return total


# ── Ana bench mantığı ─────────────────────────────────────────────────────────

def run_bench(
    gold: list[dict],
    broken: list[dict],
    use_llm: bool,
    limit: int | None,
) -> dict:
    result: dict = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "settings": {
            "critic_min_confidence": settings.critic_min_confidence,
            "critic_batch_size": settings.critic_batch_size,
            "critic_model": settings.critic_model,
        },
        "llm_enabled": False,
        "defect_types": {},
        "gold_false_alarm": {},
        "fail_open_batches": 0,
        "unmeasured_ids": [],
    }

    critic = None
    if use_llm:
        try:
            critic = _get_critic()
            result["llm_enabled"] = True
        except CriticUnavailable as exc:
            print(f"UYARI: LLM critic devre dışı ({exc}) — yalnız Katman 1 raporlanır.")
            use_llm = False

    by_defect: dict[str, list[dict]] = {}
    for rec in broken:
        by_defect.setdefault(rec["defect_type"], []).append(rec)

    gold_for_alarm = gold if limit is None else gold[:limit]
    det_false = [det_issue(r) is not None for r in gold_for_alarm]
    det_false_n = sum(det_false)
    remaining_for_critic = [r for r, flagged in zip(gold_for_alarm, det_false) if not flagged]

    fail_open_batches = 0
    unmeasured_ids: list[str] = []

    for defect_type, group in sorted(by_defect.items()):
        det_flags = [det_issue(r) is not None for r in group]
        det_n = sum(det_flags)
        critic_n: int | None = None
        critic_flags_list = [False] * len(group)
        unresolved: list[int] = []
        unmeasured: list[int] = []
        if use_llm and det_n < len(group):
            try:
                critic_flags_list, unresolved, unmeasured, fail_open = critic_flags(critic, group)
                if fail_open:
                    fail_open_batches += 1
                unmeasured_ids.extend(_rec_id(group[i]) for i in unmeasured)
                critic_evaluated_n = len(group) - len(unresolved) - len(unmeasured)
                critic_n = sum(critic_flags_list) if critic_evaluated_n > 0 else None
            except CriticUnavailable as exc:
                print(f"UYARI: critic çağrısı başarısız ({defect_type}): {exc}")
                critic_n = None
                unresolved = []
                unmeasured = []
        union_caught = sum(1 for a, b in zip(det_flags, critic_flags_list) if a or b)
        critic_evaluated_n = len(group) - len(unresolved) - len(unmeasured)
        result["defect_types"][defect_type] = {
            "n": len(group),
            "det_caught": det_n,
            "critic_caught": critic_n,
            "critic_evaluated": critic_evaluated_n,
            "critic_skipped_fully_det_caught": det_n == len(group),
            "critic_unresolved_kazanim": len(unresolved),
            "critic_unmeasured_fail_open": len(unmeasured),
            "union_caught": union_caught,
            "recall_pct": round(100 * union_caught / len(group), 1) if group else 0.0,
        }

    # ── Altın set: yanlış-alarm ───────────────────────────────────────────────
    critic_false_n = 0
    critic_unresolved_n = 0
    critic_unmeasured_n = 0
    if use_llm:
        chunk = settings.critic_batch_size
        for start in range(0, len(remaining_for_critic), chunk):
            group = remaining_for_critic[start:start + chunk]
            try:
                flags, unresolved, unmeasured, fail_open = critic_flags(critic, group)
                if fail_open:
                    fail_open_batches += 1
                unmeasured_ids.extend(_rec_id(group[i]) for i in unmeasured)
                critic_false_n += sum(flags)
                critic_unresolved_n += len(unresolved)
                critic_unmeasured_n += len(unmeasured)
            except CriticUnavailable as exc:
                print(f"UYARI: critic çağrısı başarısız (altın set): {exc}")
                break

    total_n = len(gold_for_alarm)
    overall_false = det_false_n + critic_false_n
    critic_truly_evaluated = len(remaining_for_critic) - critic_unresolved_n - critic_unmeasured_n
    result["gold_false_alarm"] = {
        "total": total_n,
        "det_false": det_false_n,
        "critic_evaluated": critic_truly_evaluated if use_llm else 0,
        "critic_false": critic_false_n if use_llm else None,
        "critic_unresolved_kazanim": critic_unresolved_n,
        "critic_unmeasured_fail_open": critic_unmeasured_n,
        "overall_false": overall_false,
        "overall_pct": round(100 * overall_false / total_n, 1) if total_n else 0.0,
    }
    result["fail_open_batches"] = fail_open_batches
    result["unmeasured_ids"] = unmeasured_ids
    return result


def _flag(recall_pct: float) -> str:
    if recall_pct >= 80:
        return "OK"
    if recall_pct >= 40:
        return f"UYARI %{100 - recall_pct:.0f} kacak"
    return "KOR NOKTA"


def format_report(result: dict) -> str:
    lines: list[str] = []
    lines.append(f"Kalite terazisi — {result['generated_at']}")
    lines.append(
        f"critic_min_confidence={result['settings']['critic_min_confidence']} "
        f"critic_batch_size={result['settings']['critic_batch_size']} "
        f"model={result['settings']['critic_model']} "
        f"LLM={'AÇIK' if result['llm_enabled'] else 'KAPALI (--no-llm ya da key yok)'}"
    )
    fail_open_batches = result.get("fail_open_batches", 0)
    unmeasured_ids = result.get("unmeasured_ids", [])
    if fail_open_batches:
        lines.append(
            f"UYARI: bu koşu KISMİ — {fail_open_batches} critic grubu fail-open oldu "
            f"(503/vb., yeniden-deneme sonrası bile), {len(unmeasured_ids)} soru "
            "ÖLÇÜLEMEDİ. Bu sorular 'yakalanmadı' SAYILMADI — critic paydasından "
            "düşürüldü (aşağıda 'ölçülemedi' notuyla ayrı görünür)."
        )
    lines.append("")
    header = f"{'kusur tipi':<30}{'det.':>8}{'critic':>14}{'toplam':>10}  bayrak"
    lines.append(header)
    lines.append("-" * len(header))
    for defect_type, row in sorted(result["defect_types"].items()):
        n = row["n"]
        det_s = f"{row['det_caught']}/{n}"
        if row["critic_caught"] is None:
            critic_s = "-"
        else:
            critic_s = f"{row['critic_caught']}/{row['critic_evaluated']}"
        total_s = f"{row['union_caught']}/{n}"
        flag = _flag(row["recall_pct"])
        notes = []
        if row["critic_unresolved_kazanim"]:
            notes.append(f"{row['critic_unresolved_kazanim']} kazanım çözülemedi")
        if row["critic_unmeasured_fail_open"]:
            notes.append(f"{row['critic_unmeasured_fail_open']} ölçülemedi (fail-open)")
        extra = f"  ({', '.join(notes)})" if notes else ""
        lines.append(f"{defect_type:<30}{det_s:>8}{critic_s:>14}{total_s:>10}  {flag}{extra}")
    lines.append("")
    fa = result["gold_false_alarm"]
    if result["llm_enabled"]:
        lines.append(
            f"ALTIN SET yanlış-alarm: det {fa['det_false']}/{fa['total']}  "
            f"critic {fa['critic_false']}/{fa['critic_evaluated']}  "
            f"toplam %{fa['overall_pct']}"
        )
        notes = []
        if fa["critic_unresolved_kazanim"]:
            notes.append(f"{fa['critic_unresolved_kazanim']} kazanım çözülemedi")
        if fa["critic_unmeasured_fail_open"]:
            notes.append(f"{fa['critic_unmeasured_fail_open']} ölçülemedi (fail-open)")
        if notes:
            lines.append(f"  ({', '.join(notes)}, critic'e gönderilmedi/sayılmadı)")
    else:
        lines.append(
            f"ALTIN SET yanlış-alarm (yalnız Katman 1): det {fa['det_false']}/{fa['total']} "
            f"(%{round(100 * fa['det_false'] / fa['total'], 1) if fa['total'] else 0.0}) "
            "— critic KOŞULMADI"
        )
    return "\n".join(lines)


def aggregate_results(results: list[dict]) -> dict:
    """--iters N>1: tip başına min/max/ortalama (koşu-arası oynama gerçek —
    tek koşuya karar bağlanmaz, bkz. plan §7 '±%15 varyans' dersi)."""
    defect_types = sorted(results[0]["defect_types"].keys())
    agg: dict = {"iters": len(results), "defect_types": {}, "gold_false_alarm": {}}
    for dt in defect_types:
        recalls = [r["defect_types"][dt]["recall_pct"] for r in results]
        det_caught = [r["defect_types"][dt]["det_caught"] for r in results]
        critic_caught = [
            r["defect_types"][dt]["critic_caught"] for r in results
            if r["defect_types"][dt]["critic_caught"] is not None
        ]
        agg["defect_types"][dt] = {
            "recall_pct_min": min(recalls),
            "recall_pct_max": max(recalls),
            "recall_pct_mean": round(statistics.mean(recalls), 1),
            "det_caught_stable": len(set(det_caught)) == 1,
            "critic_caught_min": min(critic_caught) if critic_caught else None,
            "critic_caught_max": max(critic_caught) if critic_caught else None,
        }
    overall_pcts = [r["gold_false_alarm"]["overall_pct"] for r in results]
    agg["gold_false_alarm"] = {
        "overall_pct_min": min(overall_pcts),
        "overall_pct_max": max(overall_pcts),
        "overall_pct_mean": round(statistics.mean(overall_pcts), 1),
    }
    agg["total_fail_open_batches"] = sum(r.get("fail_open_batches", 0) for r in results)
    agg["total_unmeasured"] = sum(len(r.get("unmeasured_ids", [])) for r in results)
    return agg


def format_aggregate(agg: dict) -> str:
    lines = [f"\n=== {agg['iters']} koşu özeti (min/max/ortalama) ==="]
    header = f"{'kusur tipi':<30}{'recall min':>12}{'max':>8}{'ort':>8}  stabil-det?"
    lines.append(header)
    lines.append("-" * len(header))
    for dt, row in sorted(agg["defect_types"].items()):
        stable = "evet" if row["det_caught_stable"] else "HAYIR (beklenmez, det. deterministik)"
        lines.append(
            f"{dt:<30}{row['recall_pct_min']:>11.1f}%{row['recall_pct_max']:>7.1f}%"
            f"{row['recall_pct_mean']:>7.1f}%  {stable}"
        )
    fa = agg["gold_false_alarm"]
    lines.append("")
    lines.append(
        f"ALTIN SET yanlış-alarm (toplam %): min {fa['overall_pct_min']} max "
        f"{fa['overall_pct_max']} ort {fa['overall_pct_mean']}"
    )
    lines.append(
        f"Toplam fail-open grubu: {agg['total_fail_open_batches']}  "
        f"Toplam ölçülemeyen soru: {agg['total_unmeasured']}"
    )
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gold", type=Path, default=DEFAULT_GOLD)
    ap.add_argument("--broken", type=Path, default=DEFAULT_BROKEN)
    ap.add_argument("--no-llm", action="store_true", help="Yalnız Katman 1 (deterministik, ücretsiz).")
    ap.add_argument("--limit", type=int, default=None, help="Altın setten örnekleme (ilk N).")
    ap.add_argument(
        "--iters", type=int, default=1,
        help="Aynı seti N kez koş, tip başına min/max/ortalama bas (koşu-arası oynama gerçek).",
    )
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--stamp", type=str, default=None, help="Çıktı dosya adında kullanılacak zaman damgası.")
    args = ap.parse_args()

    gold = _load(args.gold)
    broken = _load(args.broken)
    use_llm = not args.no_llm
    iters = max(1, args.iters)

    per_iter_calls = estimate_critic_calls(gold, broken, args.limit)
    total_calls = per_iter_calls * iters
    print(
        f"[tahmin] critic çağrı sayısı ~{total_calls} (~${total_calls * _EST_USD_PER_CALL:.4f})"
        + (f"  ({iters} koşu × ~{per_iter_calls}/koşu)" if iters > 1 else "")
    )
    if use_llm and per_iter_calls > 30:
        print(
            f"UYARI: tek koşu tahmini çağrı sayısı ({per_iter_calls}) 30 hedefinin "
            "üzerinde — --limit ile altın set örneklemesini küçültmeyi düşün."
        )

    results = []
    for i in range(iters):
        if iters > 1:
            print(f"\n--- Koşu {i + 1}/{iters} ---")
        result = run_bench(gold, broken, use_llm=use_llm, limit=args.limit)
        results.append(result)
        print(format_report(result))

    if iters > 1:
        agg = aggregate_results(results)
        print(format_aggregate(agg))
        payload = {"iterations": results, "aggregate": agg}
    else:
        payload = results[0]

    stamp = args.stamp or time.strftime("%Y%m%d_%H%M%S")
    out_path = args.out or (DEFAULT_OUT_DIR / f"bench_{stamp}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nHam sonuç: {out_path}")


if __name__ == "__main__":
    main()
