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

            # due_at (son teslim) — opsiyonel; verilince listede döner
            import time as _t
            due = _t.time() + 3 * 86400
            a2 = cs.create_assignment(
                classroom_id=c["id"], owner_tenant_id="teacher-1",
                quiz_id=quiz_id, title="Süreli ödev", due_at=due,
            )
            row = next(x for x in cs.list_assignments(c["id"]) if x["id"] == a2["id"])
            check(row["due_at"] is not None, "due_at listede döndü")
            mine = next(
                x for x in cs.list_my_assignments("stu-1")
                if x["assignment_id"] == a2["id"]
            )
            check(mine["due_at"] is not None, "öğrenci ödevinde due_at var")
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


def test_first_attempt_counts_not_max() -> None:
    """H2 anti-kopya: tekrar çözmeye izin var ama İLK deneme sayılır (MAX değil).

    Senaryo: öğrenci ödevi bir kez düşük puanla gönderir (cevap anahtarını görür),
    sonra tam puanla yeniden gönderir. Hem 'Ödevlerim' hem öğretmen panosu İLK
    (düşük) skoru göstermeli → cevap anahtarıyla puan şişirilemez.
    """
    print("İlk-deneme sayılır (tekrar serbest, MAX değil)")
    import time as _t
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
            # 1. deneme — düşük (0/1)
            qs.record_attempt(
                quiz_id=quiz_id, solver_tenant_id="stu-1",
                answers=[{"number": 1, "texts": ["3"]}],
                score=0, total=1, duration_seconds=10,
                per_kazanim=[{"kazanim_kod": "M.5.1.1", "correct": 0, "total": 1}],
                assignment_id=a["id"],
            )
            _t.sleep(0.05)  # distinct completed_at (epoch) → deterministik sıralama
            # 2. deneme — cevabı görüp tam puan (1/1)
            qs.record_attempt(
                quiz_id=quiz_id, solver_tenant_id="stu-1",
                answers=[{"number": 1, "texts": ["4"]}],
                score=1, total=1, duration_seconds=5,
                per_kazanim=[{"kazanim_kod": "M.5.1.1", "correct": 1, "total": 1}],
                assignment_id=a["id"],
            )
            # Öğrencinin kendi görünümü — İLK skor (0), MAX (1) değil
            mine = cs.list_my_assignments("stu-1")[0]
            check(mine["score"] == 0, f"Ödevlerim İLK skoru gösterir (0), beklenen 0 → {mine['score']}")
            # Öğretmen panosu — İLK skor (0), MAX (1) değil
            res = cs.assignment_results(a["id"], "teacher-1")
            ali = next(i for i in res["items"] if i["display_name"] == "Ali")
            check(ali["score"] == 0, f"Pano İLK skoru gösterir (0), beklenen 0 → {ali['score']}")
            check(ali["solved"] is True, "iki deneme sonrası solved True")
        finally:
            cs.close(); qs.close()


def test_pdf_assignment() -> None:
    print("PDF ödev — tip + worksheet snapshot")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        db = str(Path(tmp) / "t.sqlite3")
        qs = QuizStore(db_path=db)
        cs = ClassroomStore(db_path=db)
        try:
            c = cs.create_classroom(owner_tenant_id="teacher-1", name="5/A")
            cs.join_classroom(code=c["join_code"], student_tenant_id="stu-1", display_name="Ali")
            ws = '{"title":"Kesirler Kağıdı","grade":5,"topic":"kesirler"}'
            a = cs.create_assignment(
                classroom_id=c["id"], owner_tenant_id="teacher-1",
                quiz_id="", title="Kesirler Kağıdı",
                assignment_type="pdf", worksheet_json=ws,
            )
            check(a is not None, "pdf ödev atandı")
            got = cs.get_assignment(a["id"])
            check(got["assignment_type"] == "pdf", "tip pdf")
            check(got["worksheet_json"] == ws, "worksheet snapshot saklandı")
            # Listede tip görünür
            la = cs.list_assignments(c["id"])[0]
            check(la["assignment_type"] == "pdf", "list_assignments tip pdf")
            mine = cs.list_my_assignments("stu-1")[0]
            check(mine["assignment_type"] == "pdf", "öğrenci ödevinde tip pdf")
            check(mine["solved"] is False, "çözülmeden pdf ödev solved False")
        finally:
            cs.close(); qs.close()


def test_pdf_assignment_solve_tracked() -> None:
    """PR2: worksheet (pdf) ödevi sistem-içi çözülür → attempt quiz_id="" + assignment_id
    ile kaydedilir → Ödevlerim + öğretmen panosu skoru gösterir (quiz ödeviyle aynı yol)."""
    print("PDF worksheet ödevi — sistem-içi çöz + skor takibi")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        db = str(Path(tmp) / "t.sqlite3")
        qs = QuizStore(db_path=db)
        cs = ClassroomStore(db_path=db)
        try:
            c = cs.create_classroom(owner_tenant_id="teacher-1", name="5/A")
            cs.join_classroom(code=c["join_code"], student_tenant_id="stu-1", display_name="Ali")
            ws = '{"title":"Kesirler","grade":5,"topic":"kesirler"}'
            a = cs.create_assignment(
                classroom_id=c["id"], owner_tenant_id="teacher-1",
                quiz_id="", title="Kesirler", assignment_type="pdf", worksheet_json=ws,
            )
            # Worksheet ödevi çözümü: quiz kaydı yok → quiz_id="" + assignment_id
            qs.record_attempt(
                quiz_id="", solver_tenant_id="stu-1",
                answers=[{"number": 1, "texts": ["yarım"]}],
                score=2, total=3, duration_seconds=40,
                per_kazanim=[{"kazanim_kod": "M.5.1.1", "correct": 2, "total": 3}],
                assignment_id=a["id"],
            )
            mine = cs.list_my_assignments("stu-1")[0]
            check(mine["solved"] is True, "worksheet ödevi çözülünce solved True")
            check(mine["score"] == 2 and mine["total"] == 3, "worksheet skoru 2/3")
            res = cs.assignment_results(a["id"], "teacher-1")
            ali = next(i for i in res["items"] if i["display_name"] == "Ali")
            check(ali["solved"] is True and ali["score"] == 2, "pano: Ali worksheet 2/3 çözdü")
        finally:
            cs.close(); qs.close()


def test_delete_assignment() -> None:
    print("öğretmen ödev silme — yalnız sahip; denemeler tarihsel kalır")
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
            qs.record_attempt(
                quiz_id=quiz_id, solver_tenant_id="stu-1",
                answers=[{"number": 1, "texts": ["4"]}],
                score=1, total=1, duration_seconds=10,
                per_kazanim=[{"kazanim_kod": "M.5.1.1", "correct": 1, "total": 1}],
                assignment_id=a["id"],
            )
            # Yetkisiz: üye/yabancı silemez
            check(cs.delete_assignment(a["id"], "stu-1") is False, "üye ödevi silemez")
            check(cs.delete_assignment(a["id"], "stranger") is False, "yabancı silemez")
            check(len(cs.list_assignments(c["id"])) == 1, "yetkisiz denemeler ödevi silmedi")
            # Sahip siler
            check(cs.delete_assignment(a["id"], "teacher-1") is True, "sahip ödevi sildi")
            check(cs.get_assignment(a["id"]) is None, "silinen ödev yok")
            check(len(cs.list_assignments(c["id"])) == 0, "sınıf ödev listesi boş")
            check(cs.list_my_assignments("stu-1") == [], "öğrencinin ödevi kalmadı")
            # Deneme kaydı tarihsel olarak durur (quiz geçmişinde)
            recent = qs.recent_attempts("stu-1")
            check(len(recent) == 1, "çözüm denemesi tarihsel olarak korundu")
            # Var olmayan ödev
            check(cs.delete_assignment("yok", "teacher-1") is False, "olmayan ödev False")
        finally:
            cs.close(); qs.close()


def test_app_imports() -> None:
    print("uygulama import — assignment endpoint'leri kayıtlı")
    from app.main import app  # noqa: PLC0415

    # OpenAPI şeması sürümden bağımsız tam-nitelikli path verir (app.routes taraması
    # Starlette sürümüne göre iç router'ları farklı sarar → openapi güvenli).
    paths = set(app.openapi()["paths"].keys())
    check("/api/assignments/{assignment_id}" in paths, "GET /api/assignments/{id}")
    check("/api/assignments/{assignment_id}/attempt" in paths, "POST .../attempt")
    check("/api/assignments/{assignment_id}/results" in paths, "GET .../results")
    check("/api/assignments/{assignment_id}/worksheet" in paths, "GET .../worksheet (pdf)")
    check("/api/classrooms/{classroom_id}/assignments" in paths, "POST classroom assignments")
    check("/api/classrooms/{classroom_id}/assignments/pdf" in paths, "POST pdf assignment")
    check("/api/me/quizzes" in paths, "GET /api/me/quizzes")
    check("/api/me/assignments" in paths, "GET /api/me/assignments")


def main() -> int:
    for fn in (
        test_assign_and_access,
        test_my_assignments_solved,
        test_assignment_results,
        test_first_attempt_counts_not_max,
        test_pdf_assignment,
        test_pdf_assignment_solve_tracked,
        test_delete_assignment,
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
