"""Quiz paylaşımı testleri (Faz 3 PR A) — depo katmanı + anti-kopya.

Pytest gerektirmez — `python tests/test_sharing.py`. LLM/ağ çağrısı yok.
Paylaşım = link/kod ile bir quiz'in sahibi olmayanlara çözdürülmesi; sahip
sonuçları görür. Bu dosya store mantığını (asıl risk) doğrular.
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
            number=1, question="2 + 3 = ? A) 4 B) 5 C) 6 D) 7", answer="B",
            solution_steps="topla", kazanim_kod="M.5.1.1",
            question_type=QuestionType.COKTAN_SECMELI,
            options=["4", "5", "6", "7"], correct_index=1,
        ),
        Question(
            number=2, question="3 + 4 = ____", answer="7",
            solution_steps="", kazanim_kod="M.5.1.2",
            question_type=QuestionType.BOSLUK_DOLDURMA, blanks=["7"],
        ),
    ]


def _make_quiz(store: QuizStore, owner: str = "owner-1") -> str:
    rec = store.create(
        owner_tenant_id=owner, title="Paylaşım Quiz", grade=5,
        topic_id="dogal_sayilar", difficulty="orta",
        questions=[q.model_dump() for q in _sample_questions()],
    )
    return rec["id"]


def test_create_share() -> None:
    print("create_share — idempotent + ownership")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        store = QuizStore(db_path=str(Path(tmp) / "t.sqlite3"))
        try:
            quiz_id = _make_quiz(store, "owner-1")
            s1 = store.create_share(quiz_id=quiz_id, owner_tenant_id="owner-1")
            check(s1 is not None and bool(s1["share_code"]), "share oluştu, kod var")
            # İdempotent: tekrar → aynı kod (çift link yok)
            s2 = store.create_share(quiz_id=quiz_id, owner_tenant_id="owner-1")
            check(s2["share_code"] == s1["share_code"], "tekrar çağrı aynı kodu döndü")
            # Sahip olmayan paylaşamaz
            bad = store.create_share(quiz_id=quiz_id, owner_tenant_id="someone-else")
            check(bad is None, "sahip olmayan paylaşamaz (None)")
            # Olmayan quiz
            check(
                store.create_share(quiz_id="yok", owner_tenant_id="owner-1") is None,
                "olmayan quiz None",
            )
        finally:
            store.close()


def test_resolve_and_revoke() -> None:
    print("get_share_by_code + get_quiz_by_id + revoke")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        store = QuizStore(db_path=str(Path(tmp) / "t.sqlite3"))
        try:
            quiz_id = _make_quiz(store, "owner-1")
            share = store.create_share(quiz_id=quiz_id, owner_tenant_id="owner-1")
            code = share["share_code"]

            resolved = store.get_share_by_code(code)
            check(resolved is not None and resolved["quiz_id"] == quiz_id,
                  "kod → paylaşım çözüldü")
            # get_quiz_by_id sahip filtresi OLMADAN getirir (paylaşılan çözme)
            q = store.get_quiz_by_id(quiz_id)
            check(q is not None and len(q["questions"]) == 2,
                  "get_quiz_by_id owner-scope'suz getirdi")
            check(store.get_share_by_code("yokkod") is None, "geçersiz kod None")

            # revoke → kod artık çözülmez
            ok = store.revoke_share(share["id"], "owner-1")
            check(ok is True, "revoke başarılı")
            check(store.get_share_by_code(code) is None, "revoke sonrası kod None")
            # Başka sahip revoke edemez
            share2 = store.create_share(quiz_id=quiz_id, owner_tenant_id="owner-1")
            check(
                store.revoke_share(share2["id"], "baskasi") is False,
                "başka tenant revoke edemez",
            )
        finally:
            store.close()


def test_shared_attempt_and_results() -> None:
    print("paylaşılan deneme → sahip sonuç panosu (misafir + üye)")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        store = QuizStore(db_path=str(Path(tmp) / "t.sqlite3"))
        try:
            quiz_id = _make_quiz(store, "owner-1")
            share = store.create_share(quiz_id=quiz_id, owner_tenant_id="owner-1")
            sid = share["id"]
            pk = [{"kazanim_kod": "M.5.1.1", "correct": 1, "total": 1}]

            # Misafir çözüm (anon + label) — 1/2
            store.record_attempt(
                quiz_id=quiz_id, solver_tenant_id="anon",
                answers=[{"number": 1, "selected_index": 1}],
                score=1, total=2, duration_seconds=20, per_kazanim=pk,
                share_id=sid, solver_label="Ahmet",
            )
            # Giriş yapmış çözüm — 2/2
            store.record_attempt(
                quiz_id=quiz_id, solver_tenant_id="student-9",
                answers=[{"number": 1, "selected_index": 1}],
                score=2, total=2, duration_seconds=15, per_kazanim=pk,
                share_id=sid, solver_label=None,
            )

            res = store.share_results(sid, "owner-1")
            check(res is not None, "sahip sonuç panosunu aldı")
            check(res["question_count"] == 2, f"soru sayısı 2: {res['question_count']}")
            check(len(res["items"]) == 2, f"2 çözüm listede: {len(res['items'])}")
            labels = {i["solver_label"] for i in res["items"]}
            check("Ahmet" in labels, "misafir adı panoda görünür")
            # Sahip olmayan sonuçları göremez
            check(store.share_results(sid, "baskasi") is None, "sahip-olmayan None")

            # list_shares — sayaç + ortalama (50% ve 100% → ort 75)
            lst = store.list_shares("owner-1")
            check(len(lst) == 1, "1 paylaşım listede")
            check(lst[0]["attempt_count"] == 2, f"çözülme=2: {lst[0]['attempt_count']}")
            check(
                lst[0]["avg_score_pct"] == 75,
                f"ort. skor 75: {lst[0]['avg_score_pct']}",
            )
        finally:
            store.close()


def test_shared_anti_copy() -> None:
    print("anti-kopya — paylaşılan quiz cevapsız sunulur")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        store = QuizStore(db_path=str(Path(tmp) / "t.sqlite3"))
        try:
            quiz_id = _make_quiz(store, "owner-1")
            quiz = store.get_quiz_by_id(quiz_id)  # paylaşım yolundaki kayıt
            questions = [Question(**q) for q in quiz["questions"]]
            pub = _to_public(
                quiz_id=quiz["id"], title=quiz["title"], grade=quiz["grade"],
                topic_id=quiz["topic_id"], difficulty=Difficulty(quiz["difficulty"]),
                created_at=quiz["created_at"], questions=questions,
            )
            flat = str(pub.model_dump())
            check("answer" not in flat, "answer paylaşılanda yok")
            check("correct_index" not in flat, "correct_index paylaşılanda yok")
            check("'7'" not in flat or "blanks" not in flat, "boşluk cevabı sızmadı")
            check(pub.questions[0].options == ["4", "5", "6", "7"], "MCQ şıkları var")
        finally:
            store.close()


def test_app_imports() -> None:
    print("uygulama import — shared router kayıtlı")
    from app.main import app  # noqa: PLC0415

    paths = {r.path for r in app.routes}
    check("/api/shared/{code}" in paths, "GET /api/shared/{code} kayıtlı")
    check("/api/shared/{code}/attempt" in paths, "POST /api/shared/{code}/attempt kayıtlı")
    check("/api/quizzes/{quiz_id}/share" in paths, "POST .../share kayıtlı")
    check("/api/me/shares" in paths, "GET /api/me/shares kayıtlı")


def main() -> int:
    for fn in (
        test_create_share,
        test_resolve_and_revoke,
        test_shared_attempt_and_results,
        test_shared_anti_copy,
        test_app_imports,
    ):
        fn()
    print()
    if _failures:
        print(f"FAILED: {len(_failures)} assert düştü")
        return 1
    print("PASSED: paylaşım testleri geçti")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
