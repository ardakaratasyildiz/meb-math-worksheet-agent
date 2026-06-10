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
from app.routers.quizzes import (  # noqa: E402
    _resolve_solvable_types,
    _split_buckets,
    _to_public,
)
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


def test_advanced_options_helpers() -> None:
    print("gelişmiş seçenek helper'ları (tip filtresi + bucket)")
    # None → 4 çözülebilir tip
    check(len(_resolve_solvable_types(None)) == 4, "None → 4 tip")
    # Çözülebilir olmayan tip elenir
    mixed = _resolve_solvable_types(
        [QuestionType.COKTAN_SECMELI, QuestionType.SOZEL_PROBLEM]
    )
    check(mixed == [QuestionType.COKTAN_SECMELI], f"sözel elendi: {mixed}")
    # Hiç çözülebilir yoksa boş (router 400 döner)
    check(_resolve_solvable_types([QuestionType.SOZEL_PROBLEM]) == [], "çözülebilir yoksa boş")
    # Bucket dağılımı
    b10 = _split_buckets(10)
    check(sum(b10.values()) == 10, f"bucket toplamı 10: {b10}")
    check(len(b10) == 3, "10 soru 3 zorluğa bölünür")
    check(_split_buckets(3) == {Difficulty.ORTA: 3}, "az soru tek seviye (orta)")


def test_attempt_history() -> None:
    print("attempt geçmişi — snapshot + trim-proof + legacy")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        store = QuizStore(db_path=str(Path(tmp) / "t.sqlite3"))
        try:
            qs = _sample_questions()
            quiz = store.create(
                owner_tenant_id="u1", title="Geçmiş Quiz", grade=5,
                topic_id="dogal_sayilar", difficulty="orta",
                questions=[q.model_dump() for q in qs],
            )
            snapshot = {
                "title": "Geçmiş Quiz", "grade": 5, "topic_id": "dogal_sayilar",
                "difficulty": "orta", "questions": [q.model_dump() for q in qs],
            }
            att = store.record_attempt(
                quiz_id=quiz["id"], solver_tenant_id="u1",
                answers=[{"number": 1, "selected_index": 1}],
                score=3, total=4, duration_seconds=30,
                per_kazanim=[{"kazanim_kod": "M.5.1.1", "correct": 3, "total": 4}],
                quiz_snapshot=snapshot,
            )
            # list_attempts
            lst = store.list_attempts("u1")
            check(len(lst) == 1, f"1 deneme listede: {len(lst)}")
            check(lst[0]["title"] == "Geçmiş Quiz" and lst[0]["score"] == 3, "liste meta+skor")
            check(lst[0]["has_detail"] is True, "snapshot → has_detail True")
            # get_attempt
            got = store.get_attempt(att["id"], "u1")
            check(got is not None and got["snapshot"] is not None, "get_attempt snapshot var")
            check(len(got["snapshot"]["questions"]) == 4, "snapshot 4 soru")
            check(got["answers"][0]["selected_index"] == 1, "kullanıcı cevabı saklı")
            # Ownership
            check(store.get_attempt(att["id"], "u2") is None, "başka tenant erişemez")
            check(store.list_attempts("u2") == [], "başka tenant boş liste")

            # TRIM-PROOF: quiz silinse bile geçmiş çalışır (snapshot sayesinde)
            store._db.execute("DELETE FROM quizzes")  # type: ignore[union-attr]
            store._db.commit()  # type: ignore[union-attr]
            lst2 = store.list_attempts("u1")
            check(len(lst2) == 1 and lst2[0]["has_detail"] is True, "quiz silinse de liste+detay")
            got2 = store.get_attempt(att["id"], "u1")
            check(got2["snapshot"] is not None, "quiz silinse de snapshot reconstruct")

            # LEGACY: snapshot'sız (NULL) kayıt + quiz yok → has_detail False
            store._db.execute(  # type: ignore[union-attr]
                "INSERT INTO attempts (id, quiz_id, solver_tenant_id, answers_json, "
                "score, total, duration_seconds, per_kazanim_json, completed_at, "
                "quiz_snapshot_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)",
                ("legacy1", "goneQuiz", "u1", "[]", 2, 5, None, "[]", 9999999999.0),
            )
            store._db.commit()  # type: ignore[union-attr]
            legacy = next(x for x in store.list_attempts("u1") if x["attempt_id"] == "legacy1")
            check(legacy["has_detail"] is False, "legacy NULL-snapshot + quiz yok → has_detail False")
            lg = store.get_attempt("legacy1", "u1")
            check(lg is not None and lg["snapshot"] is None, "legacy get_attempt snapshot None")
        finally:
            store.close()


def main() -> int:
    for fn in (
        test_store_crud,
        test_to_public_anti_copy,
        test_advanced_options_helpers,
        test_attempt_history,
    ):
        fn()
    print()
    if _failures:
        print(f"FAILED: {len(_failures)} assert düştü")
        return 1
    print("PASSED: quiz store + anti-kopya testleri geçti")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
