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


# Şapkalı (circumflex) ünlüler önceden-birleşik karakterlerdir; casefold/NFKC bunları
# sadeleştirmez. "beşerî" ≡ "beşeri" eşleşsin diye â/î/û → a/i/u katlanır (Sosyal'de
# "beşerî" cevabı, kullanıcının "beşeri" girişiyle eşleşmiyordu — WS-5.2).
_CIRCUMFLEX_FOLD = str.maketrans("âîûÂÎÛ", "aiuaiu")


def _normalize_text(s: str) -> str:
    """Boşluk/büyük-küçük/aksan toleranslı normalize (string-eşleşme için)."""
    if not s:
        return ""
    s = s.strip().casefold()
    # Aksan/diakritik sadeleştir (Türkçe ı/İ casefold ile zaten ele alınır).
    s = unicodedata.normalize("NFKC", s)
    s = s.translate(_CIRCUMFLEX_FOLD)  # şapkalı ünlüler: â/î/û → a/i/u
    s = re.sub(r"\s+", " ", s)
    return s.strip(" .,:;!?")


def _match_blank(submitted: str, expected: str) -> bool:
    """Tek boşluk eşleşmesi: önce sayısal denklik, olmazsa normalize string."""
    n = numeric_equivalent(submitted, expected)
    if n is not None:
        return n
    return _normalize_text(submitted) == _normalize_text(expected)


def _match_free_text(submitted: SubmittedAnswer | None, expected: str) -> bool:
    """Serbest-metin cevabı → cevap anahtarına normalize/sayısal eşleştir.

    Worksheet ödevlerinin sistem-içi çözümünde (open_ended_text_match=True) yapılandırılmamış
    tipler için kullanılır: öğrenci cevabını metin kutusuna yazar, sunucu _match_blank ile
    (sayısal denklik VEYA aksan/boşluk/büyük-küçük toleranslı string) cevap anahtarıyla
    karşılaştırır. Self-eval YOK, LLM YOK. Kısa/kesin cevaplarda güvenilir; uzun serbest
    metinde farklı ifade haksız 'yanlış' verebilir (bilinen sınır).
    """
    if not submitted or not submitted.texts:
        return False
    guess = submitted.texts[0]
    if not guess or not guess.strip():
        return False
    return _match_blank(guess, expected)


def grade_question(
    stored: Question,
    submitted: SubmittedAnswer | None,
    *,
    open_ended_text_match: bool = False,
) -> bool:
    """Tek soruyu puanla. Cevap yoksa/eksikse yanlış sayılır (fail-closed).

    open_ended_text_match=True (worksheet ödevi sistem-içi çözümü): yapılandırılmamış /
    açık uçlu tipler ÖZ-DEĞERLENDİRME yerine cevap anahtarına normalize metin-eşleştirmeyle
    puanlanır. Yapısal 4 tip (çoktan seçmeli, doğru-yanlış, boşluk, salt işlem) her iki modda
    da aynı deterministik kuralla puanlanır. Varsayılan (False) = Çöz&Geliş davranışı korunur.
    """
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

    # Açık uçlu (sozel_problem) — Çöz&Geliş'te ÖZ-DEĞERLENDİRME (öğrenci cevabı görüp
    # "doğru bildim" = bool_answer=True der). Worksheet ödevinde ise self-eval yerine
    # cevap anahtarına metin-eşleştirme (open_ended_text_match).
    if t == QuestionType.SOZEL_PROBLEM:
        if open_ended_text_match:
            return _match_free_text(submitted, stored.answer)
        return submitted.bool_answer is True

    # Diğer yapılandırılmamış tipler (tablo, okuma pasajı, eşleştirme, sıralama, görsel
    # geometri…): Çöz&Geliş'te bu havuza girmezler (yanlış). Worksheet ödevinde öğrenci
    # cevabını metin kutusuna yazar → cevap anahtarına eşleştirilir.
    if open_ended_text_match:
        return _match_free_text(submitted, stored.answer)
    return False


def grade_quiz(
    stored_questions: list[Question],
    submitted: list[SubmittedAnswer],
    *,
    open_ended_text_match: bool = False,
) -> tuple[list[QuestionResult], int, int, list[KazanimBreakdown]]:
    """Tüm quiz'i puanla.

    Dönüş: (soru sonuçları, doğru sayısı, toplam, kazanım kırılımı).
    Çözüm sonrası geri bildirim: her sonuçta doğru cevap + çözüm açığa çıkar.

    open_ended_text_match: worksheet ödevi sistem-içi çözümünde True — açık uçlu/
    yapılandırılmamış tipler self-eval yerine metin-eşleştirmeyle puanlanır (bkz. grade_question).
    """
    by_number = {a.number: a for a in submitted}
    results: list[QuestionResult] = []
    score = 0
    # kazanım → [correct, total]
    per_k: dict[str, list[int]] = {}

    for q in stored_questions:
        is_correct = grade_question(
            q, by_number.get(q.number), open_ended_text_match=open_ended_text_match
        )
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
