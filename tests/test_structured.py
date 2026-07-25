"""Yapısal cevap katmanı testleri (Adım 0).

Pytest gerektirmez — doğrudan `python tests/test_structured.py` ile koşar; bir
assert düşerse non-zero exit. CI (eval.yml lint-import) bu dosyayı çalıştırır.
LLM/ağ çağrısı yok, saf deterministik.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Windows konsolu (cp1252) Türkçe/matematik karakterlerini basamıyor → utf-8 zorla.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

# Repo kökünü import path'e ekle (tests/ alt dizininden koşulduğunda).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.enums import QuestionType  # noqa: E402
from app.models.schemas import Question  # noqa: E402
from app.services.math_verifier import numeric_equivalent  # noqa: E402
from app.services.structured import (  # noqa: E402
    SOLVABLE_TYPES,
    count_blanks,
    derive_structured_fields,
    structured_content_issue,
    validate_structured,
)

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if cond:
        print(f"  ok   {msg}")
    else:
        print(f"  FAIL {msg}")
        _failures.append(msg)


def _q(qtype: QuestionType, *, question: str, answer: str, **extra) -> Question:
    return Question(
        number=1,
        question=question,
        answer=answer,
        solution_steps="",
        kazanim_kod="M.5.1.1",
        question_type=qtype,
        **extra,
    )


# ── numeric_equivalent ───────────────────────────────────────────────────────
def test_numeric_equivalent() -> None:
    print("numeric_equivalent")
    check(numeric_equivalent("1/2", "0,5") is True, "1/2 ≡ 0,5 (Türkçe ondalık)")
    check(numeric_equivalent("0.5", "1/2") is True, "0.5 ≡ 1/2")
    check(numeric_equivalent("3 tam 1/4", "13/4") is True, "3 tam 1/4 ≡ 13/4")
    check(numeric_equivalent("12", "12") is True, "12 ≡ 12")
    check(numeric_equivalent("12", "13") is False, "12 ≢ 13")
    check(numeric_equivalent("elma", "12") is None, "parse edilemeyen → None")


# ── Çoktan seçmeli ───────────────────────────────────────────────────────────
def test_mcq_derive_and_validate() -> None:
    print("coktan_secmeli derive+validate")
    q = _q(
        QuestionType.COKTAN_SECMELI,
        question="2 + 3 kaçtır? A) 4 B) 5 C) 6 D) 7",
        answer="B",
    )
    d = derive_structured_fields(q)
    check(d.options == ["4", "5", "6", "7"], f"şıklar çıkarıldı: {d.options}")
    check(d.correct_index == 1, f"correct_index=1 (B): {d.correct_index}")
    ok, issues = validate_structured(d)
    check(ok, f"geçerli MCQ valide: {issues}")

    # Cevap şık metniyle verilmiş (harf değil)
    q2 = _q(
        QuestionType.COKTAN_SECMELI,
        question="Hangisi çift? A) 3 B) 7 C) 8 D) 9",
        answer="8",
    )
    d2 = derive_structured_fields(q2)
    check(d2.correct_index == 2, f"metin-eşleşmeli cevap → index 2: {d2.correct_index}")

    # Geçersiz: correct_index aralık dışı
    bad = _q(
        QuestionType.COKTAN_SECMELI,
        question="x?",
        answer="A",
        options=["1", "2"],
        correct_index=5,
    )
    ok_bad, issues_bad = validate_structured(bad)
    check(not ok_bad, f"aralık-dışı correct_index reddedildi: {issues_bad}")

    # Geçersiz: tek şık
    bad2 = _q(QuestionType.COKTAN_SECMELI, question="x?", answer="A", options=["1"], correct_index=0)
    ok_b2, _ = validate_structured(bad2)
    check(not ok_b2, "tek şıklı MCQ reddedildi")

    # Şıklar metne gömülüyse METİN otoriter (LLM'in options/correct_index'i güvenilmez;
    # sıra kayması / harf uyumsuzluğu yanlış puanlamaya yol açıyordu). Gösterilen sıra
    # = metindeki sıra; index answer harfinden.
    pre = _q(
        QuestionType.COKTAN_SECMELI,
        question="A) 4 B) 5",
        answer="A",
        options=["dört", "beş"],
        correct_index=1,
    )
    dpre = derive_structured_fields(pre)
    check(dpre.options == ["4", "5"], f"metin şıkları otoriter: {dpre.options}")
    check(dpre.correct_index == 0, f"cevap A → index 0 (LLM'in 1'i değil): {dpre.correct_index}")

    # Bug B: cevap TAM şık metniyle ("B) goes") gelse de harf→index doğru.
    q3 = _q(
        QuestionType.COKTAN_SECMELI,
        question="She ___ to school. A) go B) goes C) going D) is go",
        answer="B) goes",
    )
    d3 = derive_structured_fields(q3)
    check(d3.options == ["go", "goes", "going", "is go"], f"4 şık: {d3.options}")
    check(d3.correct_index == 1, f"'B) goes' → index 1: {d3.correct_index}")

    # Bug A: 5. şık (E) parser'da yutulur → tam 4 şık (A-D).
    q4 = _q(
        QuestionType.COKTAN_SECMELI,
        question="Which? A) run B) runs C) running D) ran E) runned",
        answer="B",
    )
    d4 = derive_structured_fields(q4)
    check(
        len(d4.options) == 4 and d4.options[3] == "ran",
        f"E) yutuldu, 4 şık: {d4.options}",
    )


# ── Doğru/Yanlış ─────────────────────────────────────────────────────────────
def test_bool_derive_and_validate() -> None:
    print("dogru_yanlis derive+validate")
    for ans, expected in [("Doğru", True), ("yanlış", False), ("D", True), ("Y", False)]:
        d = derive_structured_fields(_q(QuestionType.DOGRU_YANLIS, question="5>3?", answer=ans))
        check(d.correct_bool is expected, f"'{ans}' → {expected}: {d.correct_bool}")
        ok, _ = validate_structured(d)
        check(ok, f"'{ans}' valide geçerli")

    bad = derive_structured_fields(_q(QuestionType.DOGRU_YANLIS, question="?", answer="belki"))
    ok_bad, issues = validate_structured(bad)
    check(not ok_bad, f"belirsiz cevap reddedildi: {issues}")


# ── Boşluk doldurma ──────────────────────────────────────────────────────────
def test_blank_derive_and_validate() -> None:
    print("bosluk_doldurma derive+validate")
    # Tek boşluk
    q = _q(QuestionType.BOSLUK_DOLDURMA, question="3 + 4 = ____", answer="7")
    d = derive_structured_fields(q)
    check(d.blanks == ["7"], f"tek boşluk: {d.blanks}")
    check(validate_structured(d)[0], "tek boşluk valide geçerli")

    # Çoklu boşluk, metin 2 işaret içeriyor
    q2 = _q(
        QuestionType.BOSLUK_DOLDURMA,
        question="En küçük asal ____, ilk çift sayı ____.",
        answer="2; 2",
    )
    d2 = derive_structured_fields(q2)
    check(d2.blanks == ["2", "2"], f"iki boşluk ayrıştı: {d2.blanks}")
    check(count_blanks(q2.question) == 2, "metinde 2 boşluk sayıldı")
    check(validate_structured(d2)[0], "iki boşluk valide geçerli")

    # Uyuşmazlık: metin 2 boşluk, cevap 1 → reddedilir
    mismatch = _q(
        QuestionType.BOSLUK_DOLDURMA,
        question="a = ____, b = ____",
        answer="5",
    )
    dm = derive_structured_fields(mismatch)
    ok_m, issues_m = validate_structured(dm)
    check(not ok_m, f"boşluk-sayısı uyuşmazlığı yakalandı: {issues_m}")


# ── Salt işlem (sayısal) ─────────────────────────────────────────────────────
def test_numeric_validate() -> None:
    print("salt_islem validate")
    ok, _ = validate_structured(_q(QuestionType.SALT_ISLEM, question="1/2 + 1/4 = ?", answer="3/4"))
    check(ok, "parse edilebilir sayısal cevap geçerli")
    ok2, issues = validate_structured(_q(QuestionType.SALT_ISLEM, question="?", answer="yedi"))
    check(not ok2, f"sözel ('yedi') sayısal cevap reddedildi: {issues}")


# ── Çözülebilir olmayan tip ──────────────────────────────────────────────────
def test_non_solvable_passthrough() -> None:
    print("çözülebilir olmayan tip")
    q = _q(QuestionType.SOZEL_PROBLEM, question="Ali'nin 3 elması var...", answer="5 elma")
    d = derive_structured_fields(q)
    check(d is q, "sözel problem değiştirilmeden döner")
    check(validate_structured(q) == (True, []), "sözel problem yapısal denetimden muaf")
    check(QuestionType.SOZEL_PROBLEM not in SOLVABLE_TYPES, "sozel_problem çözülebilir değil")
    check(len(SOLVABLE_TYPES) == 4, "Adım 0: 4 çözülebilir tip")


# ── Yapısal içerik eksikliği (eşleştirme/sıralama boş gövde) ──────────────────
def test_structured_content_issue() -> None:
    print("yapısal içerik eksikliği (eşleştirme/sıralama)")
    # eşleştirme: yalnız yönerge, öğe/şık yok → düşürülür
    check(
        structured_content_issue(QuestionType.ESLESTIRME, "Aşağıdaki kavramları eşleştiriniz.")
        is not None,
        "boş eşleştirme (yalnız yönerge) düşürülür",
    )
    # eşleştirme: GFM tablo → korunur
    tbl = "Eşleştir:\n| Öğe | Karşılık |\n|---|---|\n| 1. Çığ | a. Yamaç |\n| 2. Sel | b. Akarsu |"
    check(
        structured_content_issue(QuestionType.ESLESTIRME, tbl) is None,
        "tablolu eşleştirme korunur",
    )
    # eşleştirme: iki liste (I/II + a/b) → korunur
    lists = "Eşleştir:\nI. Deprem\nII. Sel\n\na. Fay\nb. Akarsu"
    check(
        structured_content_issue(QuestionType.ESLESTIRME, lists) is None,
        "iki-listeli eşleştirme korunur",
    )
    # sıralama: öğe listesi yok → düşürülür
    check(
        structured_content_issue(QuestionType.SIRALAMA, "Olayları sıralayınız.") is not None,
        "boş sıralama (yalnız yönerge) düşürülür",
    )
    # sıralama: öğe listesi var → korunur
    check(
        structured_content_issue(QuestionType.SIRALAMA, "Sırala:\nI. Biri\nII. İkisi\nIII. Üçü")
        is None,
        "öğe-listeli sıralama korunur",
    )
    # ilgisiz tip → etkilenmez
    check(
        structured_content_issue(QuestionType.COKTAN_SECMELI, "Soru? A) x B) y") is None,
        "coktan_secmeli bu kontrolden etkilenmez",
    )


def main() -> int:
    for fn in (
        test_numeric_equivalent,
        test_mcq_derive_and_validate,
        test_bool_derive_and_validate,
        test_blank_derive_and_validate,
        test_numeric_validate,
        test_non_solvable_passthrough,
        test_structured_content_issue,
    ):
        fn()
    print()
    if _failures:
        print(f"FAILED: {len(_failures)} assert düştü")
        return 1
    print("PASSED: tüm yapısal cevap testleri geçti")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
