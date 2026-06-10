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

    # LLM zaten doldurmuşsa derive üzerine yazmaz
    pre = _q(
        QuestionType.COKTAN_SECMELI,
        question="A) 4 B) 5",
        answer="A",
        options=["dört", "beş"],
        correct_index=0,
    )
    dpre = derive_structured_fields(pre)
    check(dpre.options == ["dört", "beş"], "mevcut options korunur (LLM önceliği)")


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


def main() -> int:
    for fn in (
        test_numeric_equivalent,
        test_mcq_derive_and_validate,
        test_bool_derive_and_validate,
        test_blank_derive_and_validate,
        test_numeric_validate,
        test_non_solvable_passthrough,
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
