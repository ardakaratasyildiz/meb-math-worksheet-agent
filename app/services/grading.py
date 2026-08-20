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
from app.services.math_verifier import numeric_equivalent, strip_latex_math


# Şapkalı (circumflex) ünlüler önceden-birleşik karakterlerdir; casefold/NFKC bunları
# sadeleştirmez. "beşerî" ≡ "beşeri" eşleşsin diye â/î/û → a/i/u katlanır (Sosyal'de
# "beşerî" cevabı, kullanıcının "beşeri" girişiyle eşleşmiyordu — WS-5.2).
_CIRCUMFLEX_FOLD = str.maketrans("âîûÂÎÛ", "aiuaiu")

# Üst simgeler → `^n`. NFKC bunları SESSİZCE düz rakama çöktürüyordu: "13⁶" → "136".
# Sonuç: öğrencinin yazdığı "13^6" cevap anahtarıyla eşleşmiyor (haksız yanlış) ve
# tersine "136" yazan öğrenci DOĞRU sayılıyordu. NFKC'den ÖNCE `^`'lı forma çevirip
# bilgiyi koruyoruz (saha bildirimi, 2026-08-20).
_SUPERSCRIPT_TO_CARET = {
    "⁰": "^0", "¹": "^1", "²": "^2", "³": "^3", "⁴": "^4",
    "⁵": "^5", "⁶": "^6", "⁷": "^7", "⁸": "^8", "⁹": "^9",
}
_SUPERSCRIPT_RUN_RE = re.compile(r"[⁰¹²³⁴⁵⁶⁷⁸⁹]+")


def _fold_superscripts(s: str) -> str:
    """Bitişik üst simge dizisini tek üsse toplar: "10²³" → "10^23"."""
    return _SUPERSCRIPT_RUN_RE.sub(
        lambda m: "^" + "".join(_SUPERSCRIPT_TO_CARET[c][1] for c in m.group(0)), s
    )


def _normalize_text(s: str) -> str:
    """Boşluk/büyük-küçük/aksan toleranslı normalize (string-eşleşme için).

    Matematik notasyonu da tek bir yazıma indirgenir: LaTeX sınırlayıcı/komutları
    temizlenir ve üst simgeler `^n` olur → "$13^6$" ≡ "13⁶" ≡ "13^6",
    "$\\sqrt{18}$" ≡ "√18" ≡ "sqrt(18)".
    """
    if not s:
        return ""
    s = _fold_superscripts(s)  # NFKC'den ÖNCE — üs bilgisi kaybolmasın
    s = strip_latex_math(s)  # $…$, \times, \frac, \sqrt, √ → sade metin
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


# Cümle içinde geçen kısa cevabı kabul etmek için üst sınır: "12 elma", "222",
# "asit" gibi anahtarlar. Uzun anahtarlarda kapsama testi anlamsız/riskli olur.
_MAX_CONTAINS_LEN = 24


def _contains_answer(sub_norm: str, exp_norm: str) -> bool:
    """Öğrenci cevabı anahtarı CÜMLE İÇİNDE tam sözcük olarak barındırıyor mu?

    Öğrenci "cevap 222" ya da "222 sayfa" yazdığında da doğru saymak için. Sözcük
    sınırı şart (aksi halde "222" değeri "1222" içinde eşleşirdi). 1 karakterlik
    anahtarlarda uygulanmaz — "2" neredeyse her cümlede bulunur.
    """
    if len(exp_norm) < 2 or len(exp_norm) > _MAX_CONTAINS_LEN:
        return False
    return re.search(rf"(?<!\w){re.escape(exp_norm)}(?!\w)", sub_norm) is not None


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
    if _match_blank(guess, expected):
        return True
    # Cümleyle yazılmış kısa cevap ("cevap 222", "222 sayfa") haksız yanlış olmasın.
    return _contains_answer(_normalize_text(guess), _normalize_text(expected))


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
    # Açık uçlu (sozel_problem): CEVAP YAZILIR, sunucu anahtara eşleştirir — her iki
    # modda aynı (KULLANICI KARARI 2026-08-13). Eskiden Çöz&Geliş'te öz-değerlendirme
    # vardı ("cevabı gör → kendini işaretle"); kaldırıldı. Geriye uyum: yalnız metin
    # HİÇ gelmediyse eski istemcinin bool_answer'ı okunur.
    if t == QuestionType.SOZEL_PROBLEM:
        if submitted.texts and any((s or "").strip() for s in submitted.texts):
            return _match_free_text(submitted, stored.answer)
        return submitted.bool_answer is True

    # Diğer yapılandırılmamış tipler (tablo, okuma pasajı, eşleştirme, sıralama, görsel
    # geometri…): Çöz&Geliş üretiminde bu tipler havuza girmez (quizzes._SOLVABLE_TYPES),
    # ama eski/harici kayıtlar için cevabı yok saymak yerine anahtara eşleştiriyoruz —
    # öğrencinin doğru yazdığı cevabı sessizce yanlış saymak en kötü davranış.
    return _match_free_text(submitted, stored.answer)


def _display_answer(q: Question) -> str:
    """Sonuç ekranında gösterilecek "doğru cevap" metni.

    Boşluk doldurmada PUANLAMA `q.blanks`'e bakar ama gösterim `q.answer`'a
    bakıyordu; model bazen answer alanına yalnız İLK boşluğu yazdığı için ekranda
    "Doğru cevap: 13" görünüp 4 boşluklu soru yanlış sayılıyordu (öğrenci "ben 13
    yazdım" diyor). Gösterimi puanlanan anahtarla aynı kaynağa bağlıyoruz.
    """
    if q.question_type == QuestionType.BOSLUK_DOLDURMA and q.blanks:
        if len(q.blanks) > 1:
            return "; ".join(b.strip() for b in q.blanks)
        return q.blanks[0].strip() or q.answer
    return q.answer


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
                correct_answer=_display_answer(q),
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
