"""Quiz store + anti-kopya stripping testleri (Adım 1).

Pytest gerektirmez — `python tests/test_quiz_store.py`. LLM/ağ çağrısı yok;
üretim hattı (agent.generate) test edilmez, yalnız kalıcılık + cevap-soyma.
CI (eval.yml lint-import) bu dosyayı çalıştırır.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import güvenliği: config gemini_api_key="" default'lar ama net olmak için set et.
os.environ.setdefault("GEMINI_API_KEY", "fake-key-for-tests")

from app.models.enums import Difficulty, QuestionType  # noqa: E402
from app.models.schemas import Question  # noqa: E402
from app.routers.quizzes import _to_public  # noqa: E402
from app.services.quiz_store import QuizStore  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {msg}")
    if not cond:
        _failures.append(msg)


def _sample_questions() -> list[Question]:
    return [
        Question(
            number=1, question="2 + 3 kaçtır? A) 4 B) 5 C) 6 D) 7", answer="B",
            solution_steps="topla", kazanim_kod="M.5.1.1",
            question_type=QuestionType.COKTAN_SECMELI,
            options=["4", "5", "6", "7"], correct_index=1,
        ),
        Question(
            number=2, question="5 asal sayıdır.", answer="Doğru",
            solution_steps="", kazanim_kod="M.5.1.2",
            question_type=QuestionType.DOGRU_YANLIS, correct_bool=True,
        ),
        Question(
            number=3, question="3 + 4 = ____", answer="7",
            solution_steps="", kazanim_kod="M.5.1.3",
            question_type=QuestionType.BOSLUK_DOLDURMA, blanks=["7"],
        ),
        Question(
            number=4, question="1/2 + 1/4 = ?", answer="3/4",
            solution_steps="ortak payda", kazanim_kod="M.5.1.4",
            question_type=QuestionType.SALT_ISLEM,
        ),
    ]


def test_store_crud() -> None:
    print("quiz store CRUD + ownership")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        store = QuizStore(db_path=str(Path(tmp) / "t.sqlite3"))
        try:
            qs = _sample_questions()
            rec = store.create(
                owner_tenant_id="user-1", title="Test Quiz", grade=5,
                topic_id="dogal_sayilar", difficulty="orta",
                questions=[q.model_dump() for q in qs],
            )
            check(bool(rec["id"]), "create id döndü")

            got = store.get(rec["id"], "user-1")
            check(got is not None, "sahip quiz'i getirebildi")
            check(len(got["questions"]) == 4, f"4 soru saklandı: {len(got['questions'])}")
            # Sunucu tarafı kayıt CEVAPLI saklanır (puanlama için)
            check(got["questions"][0]["answer"] == "B", "sunucuda cevap saklı (B)")
            check(got["questions"][0]["correct_index"] == 1, "sunucuda correct_index saklı")

            # Ownership: başka tenant erişemez
            check(store.get(rec["id"], "user-2") is None, "başka tenant erişemez")
            # Yok olan id
            check(store.get("yok", "user-1") is None, "olmayan id None")

            # list — meta, sorular hariç
            lst = store.list("user-1")
            check(len(lst) == 1 and lst[0]["id"] == rec["id"], "list meta döndü")
            check("questions" not in lst[0], "list sorulari icermez (hafif)")
        finally:
            store.close()


def test_to_public_anti_copy() -> None:
    print("_to_public anti-kopya stripping")
    qs = _sample_questions()
    pub = _to_public(
        quiz_id="q1", title="T", grade=5, topic_id="dogal_sayilar",
        difficulty=Difficulty.ORTA, created_at="2026-06-10T00:00:00+00:00",
        questions=qs,
    )
    dumped = pub.model_dump()
    flat = str(dumped)
    # CEVAP SIZMAMALI
    check("answer" not in flat, "answer alanı public'te yok")
    check("correct_index" not in flat, "correct_index public'te yok")
    check("correct_bool" not in flat, "correct_bool public'te yok")
    check("solution_steps" not in flat, "solution_steps public'te yok")
    # MCQ şıkları (cevap değil) gönderilir
    mcq = pub.questions[0]
    check(mcq.options == ["4", "5", "6", "7"], f"MCQ şıkları gönderildi: {mcq.options}")
    # blanks (cevap) yerine yalnız blank_count
    blank_q = pub.questions[2]
    check(blank_q.blank_count == 1, f"boşluk sayısı gönderildi: {blank_q.blank_count}")
    check(not hasattr(blank_q, "blanks"), "blanks (cevap) public şemada yok")
    # D/Y ve sayısal sorularda options/blank_count None
    check(pub.questions[1].options is None, "D/Y'de options yok")
    check(pub.questions[3].blank_count is None, "salt_islem'de blank_count yok")
    check(pub.question_count == 4, "question_count=4")


def main() -> int:
    for fn in (test_store_crud, test_to_public_anti_copy):
        fn()
    print()
    if _failures:
        print(f"FAILED: {len(_failures)} assert düştü")
        return 1
    print("PASSED: quiz store + anti-kopya testleri geçti")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
