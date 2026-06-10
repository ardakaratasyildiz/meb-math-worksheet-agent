"""Geçmiş deneme gözden geçirme testleri (quiz geçmişi — PR1).

Pytest gerektirmez — `python tests/test_attempt_review.py`. LLM/ağ/DB yok.
CI (eval.yml lint-import) bu dosyayı çalıştırır.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("GEMINI_API_KEY", "fake-key-for-tests")

from app.models.enums import QuestionType  # noqa: E402
from app.models.schemas import Question, SubmittedAnswer  # noqa: E402
from app.services.attempt_review import build_attempt_detail  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {msg}")
    if not cond:
        _failures.append(msg)


def _q(n, qtype, answer, **extra) -> Question:
    return Question(
        number=n, question="?", answer=answer, solution_steps="çözüm",
        kazanim_kod=extra.pop("kazanim_kod", "M.5.1.1"),
        question_type=qtype, **extra,
    )


def test_build_attempt_detail() -> None:
    print("build_attempt_detail — gözden geçirme")
    questions = [
        _q(1, QuestionType.COKTAN_SECMELI, "B", options=["4", "5", "6", "7"], correct_index=1),
        _q(2, QuestionType.DOGRU_YANLIS, "Doğru", correct_bool=True),
        _q(3, QuestionType.SALT_ISLEM, "3/4", kazanim_kod="M.5.1.2"),
    ]
    submitted = [
        SubmittedAnswer(number=1, selected_index=1),   # doğru
        SubmittedAnswer(number=2, bool_answer=False),  # yanlış
        # 3 numara cevapsız (boş)
    ]
    detail = build_attempt_detail(
        attempt_id="a1", quiz_id="q1",
        meta={"title": "Test Quiz", "grade": 5, "topic_id": "dogal_sayilar", "difficulty": "orta"},
        questions=questions, submitted=submitted,
        duration_seconds=42, completed_at="2026-06-10T00:00:00+00:00",
    )
    check(detail.score == 1 and detail.total == 3, f"skor 1/3: {detail.score}/{detail.total}")
    check(detail.title == "Test Quiz" and detail.grade == 5, "meta taşındı")
    check(len(detail.review) == 3, "3 soru review")
    check(detail.has_detail is True, "has_detail=True")

    r1, r2, r3 = detail.review
    # Soru 1: doğru, kullanıcının seçimi echo'lanır, doğru şık açık
    check(r1.is_correct is True, "soru1 doğru")
    check(r1.submitted is not None and r1.submitted.selected_index == 1, "soru1 kullanıcı cevabı echo")
    check(r1.options == ["4", "5", "6", "7"] and r1.correct_index == 1, "soru1 MCQ şık+doğru index")
    check(r1.correct_answer == "B", "soru1 doğru cevap açık")
    # Soru 2: yanlış
    check(r2.is_correct is False and r2.submitted.bool_answer is False, "soru2 yanlış + cevap echo")
    # Soru 3: cevapsız → submitted None, yanlış sayılır
    check(r3.submitted is None, "soru3 cevapsız → submitted None")
    check(r3.is_correct is False, "soru3 cevapsız yanlış")
    check(r3.correct_answer == "3/4", "soru3 doğru cevap açık")
    # Kazanım kırılımı
    by_k = {k.kazanim_kod: (k.correct, k.total) for k in detail.per_kazanim}
    check(by_k.get("M.5.1.1") == (1, 2), f"M.5.1.1 1/2: {by_k.get('M.5.1.1')}")
    check(by_k.get("M.5.1.2") == (0, 1), f"M.5.1.2 0/1: {by_k.get('M.5.1.2')}")


def main() -> int:
    test_build_attempt_detail()
    print()
    if _failures:
        print(f"FAILED: {len(_failures)} assert düştü")
        return 1
    print("PASSED: geçmiş gözden geçirme testleri geçti")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
