"""Faz 3 — Çıkarılan soruların CEVAP DOĞRULAMASI (math_verifier + critic).

Pilot bulgusu: çıkmış-sorular PDF'lerinde ayrı cevap anahtarı olmadığında model
cevabı TAHMİN ediyor, bazıları yanlış (örn. çözüm=4 ama cevap=C). Doğrulamadan
few-shot havuzuna ingest etmek modele yanlış desen öğretir → bu adım ZORUNLU.

Akış:
  1. processed/questions_grade{N}.json yükle.
  2. Her soruyu `Question` nesnesine sar (tip eşlemesi ile).
  3. `math_verifier` (SymPy, deterministik, ÜCRETSİZ) — aritmetik tipleri kontrol et.
  4. `GeminiCritic` (LLM judge) — kazanım+zorluk gruplarında matematik doğruluğu,
     çözüm tutarlılığı, kazanım/zorluk uyumu.
  5. Karar:
       - math_verifier is_valid=False → RED (deterministik, kesin).
       - critic is_valid=False & confidence >= eşik → RED.
       - aksi → KABUL.
  6. Çıktı: questions_grade{N}_validated.json (kabul) + questions_grade{N}_rejected.json (red+sebep).

Kullanım:
    python scripts/validate_questions.py --grade 5
    python scripts/validate_questions.py --grade 5 --no-critic   # sadece SymPy (bedava)
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import settings  # noqa: E402
from app.data.curriculum import CURRICULUM  # noqa: E402
from app.models.enums import Difficulty, QuestionType  # noqa: E402
from app.models.schemas import Question  # noqa: E402
from app.services import math_verifier  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                    datefmt="%H:%M:%S")
logger = logging.getLogger("validate_questions")

PROCESSED_DIR = ROOT / "knowledge_base" / "processed"

# Extractor tipleri → QuestionType enum (enum'da olmayanları eşle)
_TYPE_MAP = {
    "acik_uclu": "sozel_problem",
    "open_ended": "sozel_problem",
    "multiple_choice": "coktan_secmeli",
    "siralanan": "siralama",
}

# ── Ucuz sezgisel ön-eleme (LLM'siz, deterministik) ──
# Çıkarım artefaktlarını yakalar: çözümün cevap anahtarıyla çeliştiği ("cevap
# anahtarı X dediği için Y'yi işaretle") ve aşırı büyük (dev SVG / birleşmiş) sorular.
_CONTRADICTION_RE = re.compile(r"cevap anahtar\w*.{0,60}(i[şs]aretl)", re.IGNORECASE | re.DOTALL)
_MAX_QUESTION_CHARS = 6000


def _heuristic_reject(ex: dict) -> str | None:
    """LLM'siz kesin-red gerekçesi döndürür (yoksa None)."""
    q = ex.get("question") or ""
    ans = ex.get("answer")
    sol = ex.get("solution") or ""
    if not q.strip():
        return "boş soru metni"
    if ans is None or str(ans).strip() == "":
        return "boş cevap"
    if len(q) > _MAX_QUESTION_CHARS:
        return f"aşırı büyük soru ({len(q)} karakter > {_MAX_QUESTION_CHARS})"
    if _CONTRADICTION_RE.search(sol):
        return "çözüm-cevap çelişkisi (cevap anahtarı ile işaretlenen uyuşmuyor)"
    return None


def _to_question_type(raw: str) -> QuestionType:
    mapped = _TYPE_MAP.get(raw, raw)
    try:
        return QuestionType(mapped)
    except ValueError:
        return QuestionType.SOZEL_PROBLEM  # güvenli varsayılan (verifier'ı tetiklemez)


def _find_kazanim(code: str) -> dict | None:
    if not code or not code.startswith("M."):
        return None
    try:
        grade = int(code.split(".")[1])
    except (IndexError, ValueError):
        return None
    for topic in CURRICULUM.get(grade, {}).values():
        for k in topic["kazanimlar"]:
            if k["kod"] == code:
                return k
    return None


def _to_question(ex: dict, index: int) -> Question:
    return Question(
        number=index,
        question=ex["question"],
        answer=ex["answer"],
        solution_steps=ex.get("solution") or "",
        kazanim_kod=ex.get("kazanim_kod") or "",
        question_type=_to_question_type(ex.get("question_type", "coktan_secmeli")),
    )


def run(grade: int, use_critic: bool = True, reuse_rejects: bool = False) -> None:
    in_path = PROCESSED_DIR / f"questions_grade{grade}.json"
    if not in_path.exists():
        raise SystemExit(f"Girdi yok: {in_path} (önce extract_questions.py çalıştır)")

    examples = json.loads(in_path.read_text(encoding="utf-8"))["examples"]
    logger.info("Yüklenen soru: %d", len(examples))

    questions = [_to_question(e, i) for i, e in enumerate(examples)]

    # ── Önceki critic redlerini taşı (zero-cost, LLM emeğini koru) ──
    prior_reject: dict[int, str] = {}
    if reuse_rejects:
        rej_path = PROCESSED_DIR / f"questions_grade{grade}_rejected.json"
        if rej_path.exists():
            prev = json.loads(rej_path.read_text(encoding="utf-8")).get("examples", [])
            prev_by_id = {e.get("id"): (e.get("reject_reason") or "önceki red") for e in prev if e.get("id")}
            for i, e in enumerate(examples):
                if e.get("id") in prev_by_id:
                    prior_reject[i] = prev_by_id[e["id"]]
            logger.info("önceki critic redleri taşındı: %d", len(prior_reject))
        else:
            logger.warning("--reuse-rejects verildi ama %s yok", rej_path.name)

    # ── 0. Sezgisel ön-eleme (LLM'siz, deterministik) ──
    heuristic_reject = {
        i: reason for i, e in enumerate(examples)
        if (reason := _heuristic_reject(e))
    }
    logger.info("sezgisel ön-eleme: %d REDDEDİLDİ (çelişki/boyut/boş)", len(heuristic_reject))

    # ── 1. math_verifier (deterministik, ücretsiz) ──
    math_verdicts = math_verifier.verify_batch(questions)
    math_reject = {
        v.question_index: v.reason for v in math_verdicts
        if v.is_verifiable and not v.is_valid
        and v.question_index not in heuristic_reject and v.question_index not in prior_reject
    }
    math_checked = sum(1 for v in math_verdicts if v.is_verifiable)
    logger.info("math_verifier: %d soru kontrol edildi, %d REDDEDİLDİ",
                math_checked, len(math_reject))

    # ── 2. critic (LLM judge), kazanım+zorluk gruplarında ──
    critic_reject: dict[int, list[str]] = {}
    if use_critic:
        from app.services.critic import GeminiCritic
        critic = GeminiCritic()
        threshold = settings.critic_min_confidence

        groups: dict[tuple[str, str], list[int]] = defaultdict(list)
        for i, e in enumerate(examples):
            if i in math_reject or i in heuristic_reject or i in prior_reject:
                continue  # zaten elendi
            groups[(e.get("kazanim_kod") or "", e.get("difficulty") or "orta")].append(i)

        # Büyük grupları alt-batch'lere böl (tek critic çağrısına ~15 soru → truncation önle)
        CHUNK = 15
        sub_batches: list[tuple[str, str, list[int]]] = []
        for (kod, diff), idxs in groups.items():
            for s in range(0, len(idxs), CHUNK):
                sub_batches.append((kod, diff, idxs[s:s + CHUNK]))

        logger.info("critic: %d grup → %d alt-batch (eşik confidence=%.2f)",
                    len(groups), len(sub_batches), threshold)
        for bi, (kod, diff, idxs) in enumerate(sub_batches, 1):
            kaz = _find_kazanim(kod)
            kazanimlar = [kaz] if kaz else []
            try:
                difficulty = Difficulty(diff)
            except ValueError:
                difficulty = Difficulty.ORTA
            sub_questions = [questions[i] for i in idxs]
            verdicts = critic.evaluate(sub_questions, kazanimlar, difficulty)
            for v in verdicts:
                if 0 <= v.question_index < len(idxs):
                    real_idx = idxs[v.question_index]
                    if not v.is_valid and v.confidence >= threshold:
                        critic_reject[real_idx] = v.issues or ["critic: geçersiz"]
            if bi % 20 == 0:
                logger.info("  critic alt-batch %d/%d, şu ana dek %d red", bi, len(sub_batches), len(critic_reject))
        logger.info("critic: %d soru REDDEDİLDİ", len(critic_reject))

    # ── 3. Ayır ──
    kept: list[dict] = []
    rejected: list[dict] = []
    for i, e in enumerate(examples):
        if i in heuristic_reject:
            rejected.append({**e, "reject_reason": f"heuristic: {heuristic_reject[i]}", "reject_by": "heuristic"})
        elif i in prior_reject:
            rejected.append({**e, "reject_reason": prior_reject[i], "reject_by": "critic(prev)"})
        elif i in math_reject:
            rejected.append({**e, "reject_reason": f"math: {math_reject[i]}", "reject_by": "math_verifier"})
        elif i in critic_reject:
            rejected.append({**e, "reject_reason": "; ".join(critic_reject[i]), "reject_by": "critic"})
        else:
            kept.append(e)

    out_kept = PROCESSED_DIR / f"questions_grade{grade}_validated.json"
    out_rej = PROCESSED_DIR / f"questions_grade{grade}_rejected.json"
    out_kept.write_text(json.dumps({"examples": kept}, ensure_ascii=False, indent=2), encoding="utf-8")
    out_rej.write_text(json.dumps({"examples": rejected}, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== DOĞRULAMA ÖZETİ ===")
    print(f"Sınıf            : {grade}")
    print(f"Girdi            : {len(examples)}")
    print(f"KABUL            : {len(kept)}")
    print(f"RED (heuristic)  : {len(heuristic_reject)}")
    print(f"RED (critic-prev): {len(prior_reject)}")
    print(f"RED (math)       : {len(math_reject)}")
    print(f"RED (critic)     : {len(critic_reject)}")
    print(f"Kabul oranı      : {len(kept)/len(examples)*100:.0f}%")
    print(f"\nÇıktılar:\n  {out_kept}\n  {out_rej}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--grade", type=int, required=True)
    parser.add_argument("--no-critic", action="store_true", help="Sadece math_verifier + heuristic (bedava)")
    parser.add_argument("--reuse-rejects", action="store_true",
                        help="Önceki questions_grade{N}_rejected.json redlerini taşı (critic emeğini koru, bedava)")
    args = parser.parse_args()
    run(grade=args.grade, use_critic=not args.no_critic, reuse_rejects=args.reuse_rejects)


if __name__ == "__main__":
    main()
