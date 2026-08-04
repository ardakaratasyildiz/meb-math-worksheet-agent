"""Hesap silme (`POST /api/me/account/delete`) testleri.

Apple App Store 5.1.1(v) / Google Play veri-silme zorunluluğu — mağaza incelemesi
kullanıcının kendi hesabını TAMAMEN silebildiği bir uç olmadan reddediyor.

Kapsam:
  (a) her tablodan doğru tenant'ın satırları siliniyor
  (b) BAŞKA tenant'ın satırları duruyor (izolasyon)
  (c) usage_ledger/billing_events SİLİNMİYOR, anonimleşiyor (VUK saklama)
  (d) yanlış confirm → 400
  (e) oturumsuz → 401
  (f) idempotent (ikinci çağrı patlamıyor)
  (g) tablo yoksa patlamıyor (Turso migrasyon gecikmesi toleransı)

`python tests/test_account_delete.py` da çalışır (pytest.main runner — CI eval
test dosyalarını doğrudan çalıştırıyor, bkz. tests/test_ledger_failed_spend.py
deseni). GERÇEK knowledge_base/history.sqlite3'e HİÇ dokunulmaz — her test kendi
geçici DB dosyasında çalışır.
"""
from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("GEMINI_API_KEY", "fake-key-for-tests")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402
from app.security import limiter  # noqa: E402
from app.services import account_delete, clerk_admin  # noqa: E402
from app.services.billing_store import BillingStore  # noqa: E402
from app.services.classroom_store import ClassroomStore  # noqa: E402
from app.services.clerk_auth import require_verified_tenant_id  # noqa: E402
from app.services.email_prefs_store import EmailPrefsStore  # noqa: E402
from app.services.parent_link_store import ParentLinkStore  # noqa: E402
from app.services.quiz_store import QuizStore  # noqa: E402
from app.services.study_plan_store import StudyPlanStore  # noqa: E402
from app.services.top_up_store import TopUpStore  # noqa: E402
from app.services.usage_ledger import UsageLedger  # noqa: E402
from app.services.worksheet_history import WorksheetHistory  # noqa: E402

client = TestClient(app)


def _iso_in(days: float) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


@pytest.fixture
def tmp_db():
    """Taze geçici DB yolu — GERÇEK history.sqlite3'e asla DOKUNMAZ."""
    tmp = os.path.join(tempfile.gettempdir(), f"acct_del_{uuid.uuid4().hex}.sqlite3")
    yield tmp
    for suffix in ("", "-wal", "-shm"):
        try:
            os.remove(tmp + suffix)
        except OSError:
            pass


class _Fixtures:
    """tmp_db üzerinde `tenant_id` (silinecek kullanıcı) + `other`/`third` (kontrol —
    silinmemeli) verisi kurar; SPEC'teki her tablodan en az bir satır."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.tenant_id = "user_victim"
        self.other = "user_other"
        self.third = "user_third"
        t, o, th = self.tenant_id, self.other, self.third

        self.wh = WorksheetHistory(db_path=db_path)
        self.quiz = QuizStore(db_path=db_path)
        self.billing = BillingStore(db_path=db_path)
        self.topup = TopUpStore(db_path=db_path)
        self.email = EmailPrefsStore(db_path=db_path)
        self.plan = StudyPlanStore(db_path=db_path)
        self.parent = ParentLinkStore(db_path=db_path)
        self.classroom = ClassroomStore(db_path=db_path)
        self.ledger = UsageLedger(db_path=db_path)

        # worksheet_history
        self.wh.add(t, {"a": 1}, {"b": 2})
        self.wh.add(o, {"a": 1}, {"b": 2})

        # quizzes + attempts — çapraz senaryo:
        #   1) benim quiz'imi BAŞKASI çözmüş  → quiz silinince cascade ile gitmeli
        #   2) ben BAŞKASININ quiz'ini çözmüşüm → solver_tenant_id kuralıyla gitmeli
        #   3) başkası KENDİ quiz'ini kendi çözmüş → dokunulmamalı (kontrol)
        self.my_quiz = self.quiz.create(
            owner_tenant_id=t, title="Q1", grade=5, topic_id="konu",
            difficulty="orta", questions=[{"number": 1}],
        )
        self.other_quiz = self.quiz.create(
            owner_tenant_id=o, title="Q2", grade=5, topic_id="konu",
            difficulty="orta", questions=[{"number": 1}],
        )
        self.quiz.record_attempt(
            quiz_id=self.my_quiz["id"], solver_tenant_id=o, answers=[],
            score=1, total=1, duration_seconds=10, per_kazanim=[],
        )
        self.quiz.record_attempt(
            quiz_id=self.other_quiz["id"], solver_tenant_id=t, answers=[],
            score=1, total=1, duration_seconds=10, per_kazanim=[],
        )
        self.quiz.record_attempt(
            quiz_id=self.other_quiz["id"], solver_tenant_id=o, answers=[],
            score=1, total=1, duration_seconds=10, per_kazanim=[],
        )

        # mastery_state
        self.quiz.update_mastery(t, [{"kazanim_kod": "M.5.1.1", "correct": 1, "total": 1}])
        self.quiz.update_mastery(o, [{"kazanim_kod": "M.5.1.1", "correct": 1, "total": 1}])

        # shares: benim (owner=t), başkasının kendi (owner=o, target yok — kontrol),
        # başkasının BANA doğrudan paylaşımı (owner=o, target=t) — create_share() API'si
        # target_tenant_id desteklemiyor (yalnız 'link' tipi) → doğrudan SQL.
        self.my_share = self.quiz.create_share(quiz_id=self.my_quiz["id"], owner_tenant_id=t)
        self.other_share = self.quiz.create_share(quiz_id=self.other_quiz["id"], owner_tenant_id=o)
        with self.quiz._lock:
            self.quiz._db.execute(
                "INSERT INTO shares (id, quiz_id, owner_tenant_id, share_code, "
                "share_type, target_tenant_id, revoked, created_at) "
                "VALUES (?,?,?,?,?,?,0,?)",
                (uuid.uuid4().hex, self.other_quiz["id"], o, uuid.uuid4().hex[:10],
                 "user", t, 0.0),
            )
            self.quiz._db.commit()

        # study_plans / top_up_credits / email_prefs / subscriptions
        self.plan.save(t, "{}")
        self.plan.save(o, "{}")
        self.topup.add(t, 25)
        self.topup.add(o, 25)
        self.email.set(tenant_id=t, email="victim@x.com", newsletter_optin=True)
        self.email.set(tenant_id=o, email="other@x.com", newsletter_optin=True)
        self.billing.upsert(tenant_id=t, plan_code="pro", status="active",
                            current_period_end=_iso_in(20))
        self.billing.upsert(tenant_id=o, plan_code="pro", status="active",
                            current_period_end=_iso_in(20))

        # parent_codes / parent_links: t hem ÖĞRENCİ hem VELİ rolünde test edilir
        self.code_me = self.parent.get_or_create_code(t)
        self.code_other = self.parent.get_or_create_code(o)
        self.parent.link(parent_tenant_id=o, code=self.code_me, child_label="X")  # student=t
        self.parent.link(parent_tenant_id=t, code=self.code_other, child_label="Y")  # parent=t

        # classrooms: benim sınıfım (o üye), başkasının sınıfı (t + third üye)
        self.my_classroom = self.classroom.create_classroom(owner_tenant_id=t, name="C1")
        self.other_classroom = self.classroom.create_classroom(owner_tenant_id=o, name="C2")
        self.classroom.join_classroom(
            code=self.my_classroom["join_code"], student_tenant_id=o, display_name="Other"
        )
        self.classroom.join_classroom(
            code=self.other_classroom["join_code"], student_tenant_id=t, display_name="Me"
        )
        self.classroom.join_classroom(
            code=self.other_classroom["join_code"], student_tenant_id=th, display_name="Third"
        )
        self.a1 = self.classroom.create_assignment(
            classroom_id=self.my_classroom["id"], owner_tenant_id=t,
            quiz_id=self.my_quiz["id"], title="A1",
        )
        self.a2 = self.classroom.create_assignment(
            classroom_id=self.other_classroom["id"], owner_tenant_id=o,
            quiz_id=self.other_quiz["id"], title="A2",
        )

        # usage_ledger / billing_events — SİLİNMEZ, anonimleşecek
        self.ledger.record(tenant_id=t, model="m", prompt_tokens=10, completion_tokens=5,
                           cost_usd=0.1, question_count=1)
        self.ledger.record(tenant_id=o, model="m", prompt_tokens=10, completion_tokens=5,
                           cost_usd=0.2, question_count=1)
        self.billing.record_event(event_id="ev_t", event_type="sub.created",
                                  payload={"a": 1}, tenant_id=t)
        self.billing.record_event(event_id="ev_o", event_type="sub.created",
                                  payload={"a": 1}, tenant_id=o)

    def raw(self, sql: str, params: tuple = ()) -> list[tuple]:
        """Store bağlantılarından BAĞIMSIZ salt-okunur doğrulama sorgusu."""
        conn = sqlite3.connect(self.db_path)
        try:
            return conn.execute(sql, params).fetchall()
        finally:
            conn.close()


# ─────────────────────────────────────────── (a)+(b)+(c) purge_tenant doğruluğu


def test_purge_deletes_target_and_preserves_others(tmp_db, monkeypatch):
    fx = _Fixtures(tmp_db)
    monkeypatch.setattr(settings, "history_db_path", tmp_db)
    t, o = fx.tenant_id, fx.other

    removed = account_delete.purge_tenant(t)

    # worksheet_history
    assert fx.raw("SELECT COUNT(*) FROM worksheet_history WHERE tenant_id=?", (t,))[0][0] == 0
    assert fx.raw("SELECT COUNT(*) FROM worksheet_history WHERE tenant_id=?", (o,))[0][0] == 1

    # quizzes
    assert fx.raw("SELECT COUNT(*) FROM quizzes WHERE owner_tenant_id=?", (t,))[0][0] == 0
    assert fx.raw("SELECT COUNT(*) FROM quizzes WHERE owner_tenant_id=?", (o,))[0][0] == 1

    # attempts: yalnız "o kendi quiz'ini kendi çözdü" satırı kalmalı
    remaining_attempts = fx.raw("SELECT quiz_id, solver_tenant_id FROM attempts")
    assert remaining_attempts == [(fx.other_quiz["id"], o)]

    # mastery_state
    assert fx.raw("SELECT COUNT(*) FROM mastery_state WHERE tenant_id=?", (t,))[0][0] == 0
    assert fx.raw("SELECT COUNT(*) FROM mastery_state WHERE tenant_id=?", (o,))[0][0] == 1

    # shares: benimki + bana hedeflenen gitti; o'nun kendi (hedefsiz) paylaşımı kaldı
    remaining_shares = fx.raw("SELECT owner_tenant_id, target_tenant_id FROM shares")
    assert remaining_shares == [(o, None)]

    # study_plans / top_up_credits / email_prefs / subscriptions
    for tbl in ("study_plans", "top_up_credits", "email_prefs", "subscriptions"):
        assert fx.raw(f"SELECT COUNT(*) FROM {tbl} WHERE tenant_id=?", (t,))[0][0] == 0, tbl
        assert fx.raw(f"SELECT COUNT(*) FROM {tbl} WHERE tenant_id=?", (o,))[0][0] == 1, tbl

    # parent_codes: yalnız o'nun kodu kaldı; parent_links: t'ye değen HER iki satır da gitti
    assert fx.raw("SELECT student_tenant_id FROM parent_codes") == [(o,)]
    assert fx.raw("SELECT COUNT(*) FROM parent_links")[0][0] == 0

    # classrooms + cascade
    assert fx.raw("SELECT COUNT(*) FROM classrooms WHERE owner_tenant_id=?", (t,))[0][0] == 0
    assert fx.raw("SELECT COUNT(*) FROM classrooms WHERE owner_tenant_id=?", (o,))[0][0] == 1
    members = fx.raw("SELECT classroom_id, student_tenant_id FROM classroom_members")
    assert members == [(fx.other_classroom["id"], fx.third)]
    assignments = fx.raw("SELECT id FROM assignments")
    assert assignments == [(fx.a2["id"],)]

    # usage_ledger: SİLİNMEDİ, tenant_id anonimleşti (cost_usd korunur)
    anon = account_delete.anon_tenant_id(t)
    assert fx.raw("SELECT COUNT(*) FROM usage_ledger WHERE tenant_id=?", (t,))[0][0] == 0
    anon_rows = fx.raw("SELECT cost_usd FROM usage_ledger WHERE tenant_id=?", (anon,))
    assert len(anon_rows) == 1 and anon_rows[0][0] == pytest.approx(0.1)
    assert fx.raw("SELECT COUNT(*) FROM usage_ledger WHERE tenant_id=?", (o,))[0][0] == 1

    # billing_events: aynı şekilde anonimleşir
    assert fx.raw("SELECT COUNT(*) FROM billing_events WHERE tenant_id=?", (t,))[0][0] == 0
    assert fx.raw("SELECT COUNT(*) FROM billing_events WHERE tenant_id=?", (anon,))[0][0] == 1
    assert fx.raw("SELECT COUNT(*) FROM billing_events WHERE tenant_id=?", (o,))[0][0] == 1

    # dönen sayım dict'i doğru mu
    assert removed["worksheet_history"] == 1
    assert removed["quizzes"] == 1
    assert removed["attempts"] == 2  # cascade(1) + kendi denemesi(1)
    assert removed["mastery_state"] == 1
    assert removed["shares"] == 2  # kendi(1) + bana hedeflenen(1)
    assert removed["study_plans"] == 1
    assert removed["top_up_credits"] == 1
    assert removed["email_prefs"] == 1
    assert removed["subscriptions"] == 1
    assert removed["parent_codes"] == 1
    assert removed["parent_links"] == 2  # student(1) + parent(1)
    assert removed["classrooms"] == 1
    assert removed["classroom_members"] == 2  # cascade(1) + kendi üyeliği(1)
    assert removed["assignments"] == 1
    assert removed["usage_ledger_anonymized"] == 1
    assert removed["billing_events_anonymized"] == 1


def test_purge_untouched_tables_not_referenced(tmp_db, monkeypatch):
    """DOKUNULMAYAN tablolar (history/generation_cache/spare_questions/admin_audit)
    purge_tenant'ın döndürdüğü anahtarlarda hiç görünmemeli."""
    fx = _Fixtures(tmp_db)
    monkeypatch.setattr(settings, "history_db_path", tmp_db)
    removed = account_delete.purge_tenant(fx.tenant_id)
    for forbidden in ("history", "generation_cache", "spare_questions", "admin_audit"):
        assert forbidden not in removed


# ─────────────────────────────────────────── (f) idempotent + (g) tablo yok


def test_purge_idempotent(tmp_db, monkeypatch):
    fx = _Fixtures(tmp_db)
    monkeypatch.setattr(settings, "history_db_path", tmp_db)
    account_delete.purge_tenant(fx.tenant_id)
    second = account_delete.purge_tenant(fx.tenant_id)  # ikinci çağrı PATLAMAMALI
    assert all(v == 0 for v in second.values()), second


def test_purge_missing_tables_does_not_raise(tmp_db, monkeypatch):
    """Hiçbir store init edilmemiş taze DB — hiçbir tablo yok (Turso migrasyon
    gecikmesi simülasyonu). purge_tenant patlamamalı."""
    monkeypatch.setattr(settings, "history_db_path", tmp_db)
    removed = account_delete.purge_tenant("ghost_tenant")  # tmp_db dosyası hiç açılmadı
    assert isinstance(removed, dict)


def test_purge_empty_tenant_is_noop():
    assert account_delete.purge_tenant("") == {}


# ─────────────────────────────────────────── router: (d) 400 + (e) 401 + 503/502/200


def test_wrong_confirm_returns_400():
    limiter.reset()
    app.dependency_overrides[require_verified_tenant_id] = lambda: "user_router_400"
    try:
        r = client.post("/api/me/account/delete", json={"confirm": "yanlis"})
        assert r.status_code == 400
    finally:
        app.dependency_overrides.pop(require_verified_tenant_id, None)


def test_no_session_returns_401():
    limiter.reset()
    old_issuer = settings.clerk_issuer
    settings.clerk_issuer = "https://clerk.test.example.com"  # doğrulama AÇIK
    app.dependency_overrides.pop(require_verified_tenant_id, None)  # gerçek dependency çalışsın
    try:
        r = client.post("/api/me/account/delete", json={"confirm": "HESABIMI SIL"})
        assert r.status_code == 401  # Authorization header yok → spoof reddi
    finally:
        settings.clerk_issuer = old_issuer


def test_missing_clerk_secret_returns_503_before_deleting_anything(monkeypatch):
    limiter.reset()
    app.dependency_overrides[require_verified_tenant_id] = lambda: "user_router_503"
    old_secret = settings.clerk_secret_key
    settings.clerk_secret_key = ""
    called = {"purge": False}
    monkeypatch.setattr(
        account_delete, "purge_tenant",
        lambda tid: called.__setitem__("purge", True) or {},
    )
    try:
        r = client.post("/api/me/account/delete", json={"confirm": "HESABIMI SIL"})
        assert r.status_code == 503
        assert called["purge"] is False, "clerk secret yokken HİÇBİR ŞEY silinmemeli"
    finally:
        settings.clerk_secret_key = old_secret
        app.dependency_overrides.pop(require_verified_tenant_id, None)


def test_success_flow_deletes_and_calls_clerk(tmp_db, monkeypatch):
    limiter.reset()
    tid = "user_router_success"
    app.dependency_overrides[require_verified_tenant_id] = lambda: tid
    monkeypatch.setattr(settings, "history_db_path", tmp_db)
    old_secret = settings.clerk_secret_key
    settings.clerk_secret_key = "test_secret"
    called: dict = {}
    monkeypatch.setattr(clerk_admin, "delete_clerk_user", lambda t: called.setdefault("tenant_id", t))
    try:
        r = client.post("/api/me/account/delete", json={"confirm": "HESABIMI SIL"})
        assert r.status_code == 200
        body = r.json()
        assert body["deleted"] is True
        assert body["clerk_deleted"] is True
        assert isinstance(body["removed"], dict)
        assert called.get("tenant_id") == tid
    finally:
        settings.clerk_secret_key = old_secret
        app.dependency_overrides.pop(require_verified_tenant_id, None)


def test_clerk_failure_returns_502(tmp_db, monkeypatch):
    limiter.reset()
    tid = "user_router_502"
    app.dependency_overrides[require_verified_tenant_id] = lambda: tid
    monkeypatch.setattr(settings, "history_db_path", tmp_db)
    old_secret = settings.clerk_secret_key
    settings.clerk_secret_key = "test_secret"

    def _boom(_tid: str) -> None:
        raise RuntimeError("Clerk patladı")

    monkeypatch.setattr(clerk_admin, "delete_clerk_user", _boom)
    try:
        r = client.post("/api/me/account/delete", json={"confirm": "HESABIMI SIL"})
        assert r.status_code == 502
    finally:
        settings.clerk_secret_key = old_secret
        app.dependency_overrides.pop(require_verified_tenant_id, None)


def test_route_registered():
    paths = {r.path for r in app.routes}
    assert "/api/me/account/delete" in paths


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
