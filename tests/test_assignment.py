"""Ödev (assignment) testleri (Faz 3.5 PR 2) — ata/erişim/çözüldü durumu.

Pytest gerektirmez — `python tests/test_assignment.py`. QuizStore + ClassroomStore
aynı geçici DB'yi paylaşır (assignments↔attempts JOIN için).
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

os.environ.setdefault("GEMINI_API_KEY", "fake-key-for-tests")

from app.services.classroom_store import ClassroomStore  # noqa: E402
from app.services.quiz_store import QuizStore  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {msg}")
    if not cond:
        _failures.append(msg)


def _make_quiz(qs: QuizStore, owner: str = "teacher-1") -> str:
    rec = qs.create(
        owner_tenant_id=owner, title="5/A Quiz", grade=5,
        topic_id="dogal_sayilar", difficulty="orta",
        questions=[{"number": 1, "question": "2+2?", "answer": "4",
                    "solution_steps": "", "kazanim_kod": "M.5.1.1",
                    "question_type": "salt_islem"}],
    )
    return rec["id"]


def test_assign_and_access() -> None:
    print("ödev atama + erişim kontrolü")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        db = str(Path(tmp) / "t.sqlite3")
        qs = QuizStore(db_path=db)
        cs = ClassroomStore(db_path=db)
        try:
            quiz_id = _make_quiz(qs, "teacher-1")
            c = cs.create_classroom(owner_tenant_id="teacher-1", name="5/A")
            cs.join_classroom(code=c["join_code"], student_tenant_id="stu-1", display_name="Ali")

            # Sahip ödev atar
            a = cs.create_assignment(
                classroom_id=c["id"], owner_tenant_id="teacher-1",
                quiz_id=quiz_id, title="Ödev 1",
            )
            check(a is not None and bool(a["id"]), "ödev atandı")
            # Sahip olmayan atayamaz
            check(
                cs.create_assignment(classroom_id=c["id"], owner_tenant_id="stu-1",
                                     quiz_id=quiz_id, title="X") is None,
                "sahip olmayan ödev atayamaz",
            )
            # get_assignment
            got = cs.get_assignment(a["id"])
            check(got is not None and got["quiz_id"] == quiz_id, "get_assignment çalışıyor")
            # is_member: öğretmen + öğrenci evet, yabancı hayır
            check(cs.is_member(c["id"], "teacher-1") is True, "sahip is_member")
            check(cs.is_member(c["id"], "stu-1") is True, "öğrenci is_member")
            check(cs.is_member(c["id"], "stranger") is False, "yabancı is_member değil")
            # list_assignments
            check(len(cs.list_assignments(c["id"])) == 1, "sınıfta 1 ödev")
        finally:
            cs.close(); qs.close()


def test_my_assignments_solved() -> None:
    print("Ödevlerim — çözülmeden / çözüldükten sonra")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        db = str(Path(tmp) / "t.sqlite3")
        qs = QuizStore(db_path=db)
        cs = ClassroomStore(db_path=db)
        try:
            quiz_id = _make_quiz(qs, "teacher-1")
            c = cs.create_classroom(owner_tenant_id="teacher-1", name="5/A")
            cs.join_classroom(code=c["join_code"], student_tenant_id="stu-1", display_name="Ali")
            a = cs.create_assignment(
                classroom_id=c["id"], owner_tenant_id="teacher-1",
                quiz_id=quiz_id, title="Ödev 1",
            )
            # Çözülmeden
            mine = cs.list_my_assignments("stu-1")
            check(len(mine) == 1, f"öğrencinin 1 ödevi: {len(mine)}")
            check(mine[0]["solved"] is False, "başta solved False")
            check(mine[0]["classroom_name"] == "5/A", "sınıf adı geliyor")
            check(mine[0]["score"] is None, "çözülmeden skor None")
            # Çözüm kaydı (assignment_id ile)
            qs.record_attempt(
                quiz_id=quiz_id, solver_tenant_id="stu-1",
                answers=[{"number": 1, "texts": ["4"]}],
                score=1, total=1, duration_seconds=10,
                per_kazanim=[{"kazanim_kod": "M.5.1.1", "correct": 1, "total": 1}],
                assignment_id=a["id"],
            )
            mine2 = cs.list_my_assignments("stu-1")
            check(mine2[0]["solved"] is True, "çözünce solved True")
            check(mine2[0]["score"] == 1 and mine2[0]["total"] == 1, "skor 1/1")
            # Katılmayan öğrencinin ödevi yok
            check(cs.list_my_assignments("stu-2") == [], "katılmayanın ödevi yok")
        finally:
            cs.close(); qs.close()


def test_assignment_results() -> None:
    print("öğretmen sonuç panosu (roster: çözen/çözmeyen)")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        db = str(Path(tmp) / "t.sqlite3")
        qs = QuizStore(db_path=db)
        cs = ClassroomStore(db_path=db)
        try:
            quiz_id = _make_quiz(qs, "teacher-1")
            c = cs.create_classroom(owner_tenant_id="teacher-1", name="5/A")
            cs.join_classroom(code=c["join_code"], student_tenant_id="stu-1", display_name="Ali")
            cs.join_classroom(code=c["join_code"], student_tenant_id="stu-2", display_name="Ayşe")
            a = cs.create_assignment(
                classroom_id=c["id"], owner_tenant_id="teacher-1",
                quiz_id=quiz_id, title="Ödev 1",
            )
            # Sadece stu-1 çözer
            qs.record_attempt(
                quiz_id=quiz_id, solver_tenant_id="stu-1",
                answers=[{"number": 1, "texts": ["4"]}],
                score=1, total=1, duration_seconds=12,
                per_kazanim=[{"kazanim_kod": "M.5.1.1", "correct": 1, "total": 1}],
                assignment_id=a["id"],
            )
            res = cs.assignment_results(a["id"], "teacher-1")
            check(res is not None, "sahip sonuç panosunu aldı")
            check(res["member_count"] == 2, f"2 üye roster: {res['member_count']}")
            check(res["solved_count"] == 1, f"1 çözen: {res['solved_count']}")
            check(res["question_count"] == 1, f"soru sayısı 1: {res['question_count']}")
            by = {i["display_name"]: i for i in res["items"]}
            check(by["Ali"]["solved"] is True and by["Ali"]["score"] == 1, "Ali çözdü 1/1")
            check(by["Ayşe"]["solved"] is False, "Ayşe çözmedi (roster'da görünür)")
            # Sahip olmayan göremez
            check(cs.assignment_results(a["id"], "stu-1") is None, "sahip-olmayan None")
        finally:
            cs.close(); qs.close()


def test_app_imports() -> None:
    print("uygulama import — assignment endpoint'leri kayıtlı")
    from app.main import app  # noqa: PLC0415

    paths = {r.path for r in app.routes}
    check("/api/assignments/{assignment_id}" in paths, "GET /api/assignments/{id}")
    check("/api/assignments/{assignment_id}/attempt" in paths, "POST .../attempt")
    check("/api/assignments/{assignment_id}/results" in paths, "GET .../results")
    check("/api/classrooms/{classroom_id}/assignments" in paths, "POST classroom assignments")
    check("/api/me/quizzes" in paths, "GET /api/me/quizzes")
    check("/api/me/assignments" in paths, "GET /api/me/assignments")


def main() -> int:
    for fn in (
        test_assign_and_access,
        test_my_assignments_solved,
        test_assignment_results,
        test_app_imports,
    ):
        fn()
    print()
    if _failures:
        print(f"FAILED: {len(_failures)} assert düştü")
        return 1
    print("PASSED: ödev testleri geçti")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
