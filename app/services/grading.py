"""LLM'siz otomatik puanlama (öğrenme döngüsü — Adım 2).

Çözülebilir 4 tipin her biri deterministik kurallarla puanlanır → etkileşim başına
maliyet ~$0, anlık sonuç:

  coktan_secmeli  → seçilen indeks == correct_index
  dogru_yanlis    → bool == correct_bool
  bosluk_doldurma → her boşluk: sayısal denklik (SymPy) VEYA normalize string eşleşme
  salt_islem      → sayısal denklik (numeric_equivalent)

Normalizasyon false-negative'i (doğruyu yanlış sayma) en aza indirir: "1/2"≡"0,5",
boşlukta büyük/küçük harf + Türkçe + boşluk toleransı.
"""
from __future__ import annotations

import re
import unicodedata

from app.models.enums import QuestionType
from app.models.schemas import (
    KazanimBreakdown,
    Question,
    QuestionResult,
    SubmittedAnswer,
)
from app.services.math_verifier import numeric_equivalent


def _normalize_text(s: str) -> str:
    """Boşluk/büyük-küçük/aksan toleranslı normalize (string-eşleşme için)."""
    if not s:
        return ""
    s = s.strip().casefold()
    # Aksan/diakritik sadeleştir (Türkçe ı/İ casefold ile zaten ele alınır).
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip(" .,:;!?")


def _match_blank(submitted: str, expected: str) -> bool:
    """Tek boşluk eşleşmesi: önce sayısal denklik, olmazsa normalize string."""
    n = numeric_equivalent(submitted, expected)
    if n is not None:
        return n
    return _normalize_text(submitted) == _normalize_text(expected)


def grade_question(stored: Question, submitted: SubmittedAnswer | None) -> bool:
    """Tek soruyu puanla. Cevap yoksa/eksikse yanlış sayılır (fail-closed)."""
    if submitted is None:
        return False
    t = stored.question_type

    if t == QuestionType.COKTAN_SECMELI:
        return (
            submitted.selected_index is not None
            and submitted.selected_index == stored.correct_index
        )

    if t == QuestionType.DOGRU_YANLIS:
        return (
            submitted.bool_answer is not None
            and submitted.bool_answer == stored.correct_bool
        )

    if t == QuestionType.BOSLUK_DOLDURMA:
        if not submitted.texts or not stored.blanks:
            return False
        if len(submitted.texts) != len(stored.blanks):
            return False
        return all(_match_blank(s, e) for s, e in zip(submitted.texts, stored.blanks))

    if t == QuestionType.SALT_ISLEM:
        if not submitted.texts:
            return False
        return numeric_equivalent(submitted.texts[0], stored.answer) is True

    # Çözülebilir olmayan tip puanlanamaz → yanlış (bu havuza hiç girmemeli).
    return False


def grade_quiz(
    stored_questions: list[Question],
    submitted: list[SubmittedAnswer],
) -> tuple[list[QuestionResult], int, int, list[KazanimBreakdown]]:
    """Tüm quiz'i puanla.

    Dönüş: (soru sonuçları, doğru sayısı, toplam, kazanım kırılımı).
    Çözüm sonrası geri bildirim: her sonuçta doğru cevap + çözüm açığa çıkar.
    """
    by_number = {a.number: a for a in submitted}
    results: list[QuestionResult] = []
    score = 0
    # kazanım → [correct, total]
    per_k: dict[str, list[int]] = {}

    for q in stored_questions:
        is_correct = grade_question(q, by_number.get(q.number))
        if is_correct:
            score += 1
        bucket = per_k.setdefault(q.kazanim_kod, [0, 0])
        bucket[1] += 1
        if is_correct:
            bucket[0] += 1
        results.append(
            QuestionResult(
                number=q.number,
                is_correct=is_correct,
                kazanim_kod=q.kazanim_kod,
                question_type=q.question_type,
                correct_answer=q.answer,
                solution_steps=q.solution_steps,
                options=q.options if q.question_type == QuestionType.COKTAN_SECMELI else None,
                correct_index=q.correct_index
                if q.question_type == QuestionType.COKTAN_SECMELI
                else None,
            )
        )

    per_kazanim = [
        KazanimBreakdown(kazanim_kod=k, correct=v[0], total=v[1])
        for k, v in per_k.items()
    ]
    return results, score, len(stored_questions), per_kazanim
