"""billing_store + entitlements testleri (iyzico ön koşulu — §4).

Pytest gerektirmez — `python tests/test_billing_store.py`.
BillingStore + UsageLedger geçici DB'de; entitlements bu instance'lara bağlanır
(singleton'lar monkeypatch edilir).
"""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("GEMINI_API_KEY", "fake-key-for-tests")

from app.config import settings  # noqa: E402
from app.services import entitlements  # noqa: E402
from app.services.billing_store import BillingStore  # noqa: E402
from app.services.top_up_store import TopUpStore  # noqa: E402
from app.services.usage_ledger import UsageLedger  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {msg}")
    if not cond:
        _failures.append(msg)


def _iso_in(days: float) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


# Ortak geçici DB (billing + usage aynı dosyayı paylaşır)
_TMP = tempfile.mkdtemp()
_DB = str(Path(_TMP) / "billing_test.sqlite3")
STORE = BillingStore(db_path=_DB)
LEDGER = UsageLedger(db_path=_DB)
TOPUP = TopUpStore(db_path=_DB)

# entitlements singleton'larını test instance'larına bağla
entitlements.BILLING_STORE = STORE
entitlements.USAGE_LEDGER = LEDGER
entitlements.TOP_UP_STORE = TOPUP


# Aile-bağ store (parent_link) fake'i — miras + paylaşımlı havuz testleri + izolasyon.
class _FakeLinks:
    def __init__(self) -> None:
        self._children: dict[str, list[str]] = {}
        self._parents: dict[str, list[str]] = {}

    def list_children(self, parent: str) -> list[dict]:
        return [{"student_id": c, "label": "C", "linked_at": ""} for c in self._children.get(parent, [])]

    def parents_of(self, child: str) -> list[str]:
        return list(self._parents.get(child, []))

    def link_family(self, parent: str, children: list[str]) -> None:
        self._children[parent] = children
        for c in children:
            self._parents.setdefault(c, []).append(parent)


FAKELINKS = _FakeLinks()
entitlements.PARENT_LINK_STORE = FAKELINKS


# ── 1. BillingStore CRUD + get_active durum mantığı ──────────────────────────

def test_store_empty() -> None:
    print("test_store_empty")
    check(STORE.get("u_none") is None, "kayıt yok → get None")
    check(STORE.get_active("u_none") is None, "kayıt yok → get_active None")


def test_start_trial() -> None:
    print("test_start_trial")
    sub = STORE.start_trial("u_trial", days=7)
    check(sub is not None and sub["status"] == "trialing", "trial başlatıldı → trialing")
    check(sub["plan_code"] == "trial", "trial plan_code=trial")
    check(STORE.get_active("u_trial") is not None, "aktif trial → get_active döner")
    # ikinci kez → None (trial zaten kullanılmış)
    check(STORE.start_trial("u_trial") is None, "mevcut satır varsa start_trial None")


def test_trial_expired() -> None:
    print("test_trial_expired")
    STORE.upsert(tenant_id="u_texp", plan_code="trial", status="trialing",
                 trial_end=_iso_in(-1))
    check(STORE.get("u_texp") is not None, "süresi geçmiş trial satırı var")
    check(STORE.get_active("u_texp") is None, "trial_end geçmiş → get_active None")


def test_active_pro() -> None:
    print("test_active_pro")
    STORE.upsert(tenant_id="u_pro", plan_code="pro", status="active",
                 current_period_end=_iso_in(20), provider_ref="sub_123")
    act = STORE.get_active("u_pro")
    check(act is not None and act["plan_code"] == "pro", "aktif pro → get_active pro")
    check(act["provider_ref"] == "sub_123", "provider_ref korunur")


def test_past_due_grace() -> None:
    print("test_past_due_grace")
    STORE.upsert(tenant_id="u_pd", plan_code="pro", status="past_due",
                 current_period_end=_iso_in(3))
    check(STORE.get_active("u_pd") is not None,
          "past_due + period_end gelecekte → erişim sürer (dunning grace)")
    STORE.upsert(tenant_id="u_pd2", plan_code="pro", status="past_due",
                 current_period_end=_iso_in(-3))
    check(STORE.get_active("u_pd2") is None, "past_due + period_end geçmiş → erişim yok")


def test_canceled_and_expired() -> None:
    print("test_canceled_and_expired")
    STORE.upsert(tenant_id="u_cx", plan_code="pro", status="canceled",
                 current_period_end=_iso_in(10))
    check(STORE.get_active("u_cx") is None, "canceled → get_active None (durum entitling değil)")
    STORE.upsert(tenant_id="u_ex", plan_code="pro", status="expired",
                 current_period_end=_iso_in(-1))
    check(STORE.get_active("u_ex") is None, "expired → get_active None")


def test_upsert_preserves_created_at() -> None:
    print("test_upsert_preserves_created_at")
    a = STORE.upsert(tenant_id="u_up", plan_code="pro", status="active",
                     current_period_end=_iso_in(30))
    b = STORE.upsert(tenant_id="u_up", plan_code="pro-plus", status="active",
                     current_period_end=_iso_in(30))
    check(a["created_at"] == b["created_at"], "upsert created_at'ı korur")
    check(b["plan_code"] == "pro-plus", "upsert plan_code'u günceller (yükseltme)")


def test_cancel_flag() -> None:
    print("test_cancel_flag")
    STORE.upsert(tenant_id="u_cf", plan_code="pro", status="active",
                 current_period_end=_iso_in(30))
    STORE.set_cancel_at_period_end("u_cf", True)
    check(STORE.get("u_cf")["cancel_at_period_end"] is True, "cancel_at_period_end işaretlendi")
    check(STORE.get_active("u_cf") is not None,
          "dönem sonu iptal işaretli ama period_end'e kadar erişim sürer")


# ── 2. billing_events idempotency ────────────────────────────────────────────

def test_event_idempotency() -> None:
    print("test_event_idempotency")
    check(STORE.record_event(event_id="ev1", event_type="sub.created",
                             payload={"a": 1}, tenant_id="u_pro") is True,
          "yeni event → True")
    check(STORE.record_event(event_id="ev1", event_type="sub.created",
                             payload={"a": 1}) is False,
          "aynı event_id tekrar → False (idempotent, iyzico retry güvenliği)")
    check(STORE.is_event_processed("ev1") is False, "yeni event processed=False")
    STORE.mark_event_processed("ev1")
    check(STORE.is_event_processed("ev1") is True, "mark sonrası processed=True")


# ── 3. entitlements plan / is_premium ────────────────────────────────────────

def test_plan_premium_all() -> None:
    print("test_plan_premium_all")
    settings.premium_all = True
    check(entitlements.plan_of("anybody") == "pro-plus", "premium_all → pro-plus")
    check(entitlements.is_premium("anybody") is True, "premium_all → is_premium True")
    settings.premium_all = False


def test_plan_resolution() -> None:
    print("test_plan_resolution")
    settings.premium_all = False
    settings.premium_tenant_ids = ""
    check(entitlements.plan_of(None) == "free", "anonim → free")
    check(entitlements.plan_of("u_none") == "free", "abonesiz → free")
    check(entitlements.is_premium("u_none") is False, "free → is_premium False")
    check(entitlements.plan_of("u_trial") == "trial", "aktif trial → plan trial")
    check(entitlements.is_premium("u_trial") is True, "trial → is_premium True")
    check(entitlements.plan_of("u_pro") == "pro", "aktif pro → plan pro")
    check(entitlements.plan_of("u_up") == "pro-plus", "aktif pro-plus → plan pro-plus")
    check(entitlements.plan_of("u_texp") == "free", "trial süresi geçmiş → free")


def test_allowlist_dev() -> None:
    print("test_allowlist_dev")
    settings.premium_all = False
    settings.premium_tenant_ids = "dev_user_1"
    check(entitlements.plan_of("dev_user_1") == "pro-plus", "allowlist → pro-plus")
    settings.premium_tenant_ids = ""


# ── 4. Kota (check_quota / quota_limit) ──────────────────────────────────────

def test_quota_limits() -> None:
    print("test_quota_limits")
    settings.free_monthly_worksheets = 10
    settings.pro_monthly_worksheets = 50
    settings.pro_plus_monthly_worksheets = 120
    check(entitlements.quota_limit("free") == 10, "free kota 10 kağıt")
    check(entitlements.quota_limit("pro") == 50, "pro kota 50 kağıt")
    check(entitlements.quota_limit("pro-plus") == 120, "pro-plus kota 120 kağıt")
    check(entitlements.quota_limit("trial") == 120, "trial → pro-plus kotası (120)")


def test_check_quota() -> None:
    print("test_check_quota")
    settings.premium_all = False
    settings.premium_tenant_ids = ""
    settings.free_monthly_worksheets = 100
    settings.pro_monthly_worksheets = 1000

    # Anonim → kotasız
    q = entitlements.check_quota(None)
    check(q["allowed"] is True and q["limit"] is None, "anonim → kotasız (allowed)")

    # Sahte usage ledger ile kontrollü kullanım
    class _FakeLedger:
        used = 0
        def worksheets_used_since(self, tenant_ids, since_ts):  # noqa: ARG002
            return self.used

    fake = _FakeLedger()
    entitlements.USAGE_LEDGER = fake

    fake.used = 40
    q = entitlements.check_quota("u_none")  # free
    check(q["plan"] == "free" and q["allowed"] is True and q["remaining"] == 60,
          "free 40/100 kullanılmış → allowed, remaining 60")

    fake.used = 100
    q = entitlements.check_quota("u_none")
    check(q["allowed"] is False and q["remaining"] == 0,
          "free 100/100 → dolu (allowed False)")

    fake.used = 95
    q = entitlements.check_quota("u_none", requested=10)
    check(q["allowed"] is False, "free 95 + 10 istek > 100 → reddedilir")
    q = entitlements.check_quota("u_none", requested=5)
    check(q["allowed"] is True, "free 95 + 5 istek = 100 → izin")

    # pro kullanıcı 1000'e kadar
    fake.used = 500
    q = entitlements.check_quota("u_pro")
    check(q["plan"] == "pro" and q["allowed"] is True and q["remaining"] == 500,
          "pro 500/1000 → allowed")

    entitlements.USAGE_LEDGER = LEDGER  # geri yükle


def test_family_shared_quota() -> None:
    """Aile: çocuk premium velinin planını MİRAS alır + aile TEK kota havuzunu paylaşır."""
    print("test_family_shared_quota")
    settings.premium_all = False
    settings.premium_tenant_ids = ""
    settings.pro_monthly_worksheets = 50
    STORE.upsert(tenant_id="u_parent", plan_code="pro", status="active",
                 current_period_end=_iso_in(20))
    FAKELINKS.link_family("u_parent", ["u_kid1", "u_kid2"])

    check(entitlements.plan_of("u_kid1") == "pro", "çocuk premium velinin planını miras alır")
    check(entitlements.is_premium("u_kid2") is True, "çocuk is_premium (aile mirası)")
    check(entitlements.is_premium_for_model("u_kid1") is True, "çocuk model-premium (aile mirası)")

    class _FakeLedger:
        seen = None
        def worksheets_used_since(self, tenant_ids, since_ts):  # noqa: ARG002
            self.seen = list(tenant_ids)
            return 30
    fake = _FakeLedger()
    entitlements.USAGE_LEDGER = fake
    q = entitlements.check_quota("u_kid1")
    check(set(fake.seen or []) == {"u_parent", "u_kid1", "u_kid2"},
          "havuz = veli + bağlı çocuklar (tek paylaşımlı sayaç)")
    check(q["plan"] == "pro" and q["limit"] == 50 and q["used"] == 30 and q["remaining"] == 20,
          "çocuk sorgusu → veli planı (pro) + aile havuzu (50 limit, 30 kullanılmış → 20 kalan)")
    entitlements.USAGE_LEDGER = LEDGER


# ── 5. ensure_trial + enforce_quota (Faz A: kota kapısı + reverse trial) ──────

def test_ensure_trial() -> None:
    print("test_ensure_trial")
    entitlements.USAGE_LEDGER = LEDGER
    entitlements.ensure_trial("u_et_new")
    sub = STORE.get("u_et_new")
    check(sub is not None and sub["status"] == "trialing",
          "yeni tenant → ensure_trial trialing satırı açar")
    # Mevcut abone → dokunma
    entitlements.ensure_trial("u_pro")
    check(STORE.get("u_pro")["plan_code"] == "pro", "mevcut abone → ensure_trial no-op")
    entitlements.ensure_trial(None)  # anonim → hata vermez
    check(True, "anonim ensure_trial → no-op (hata yok)")


def test_enforce_quota() -> None:
    print("test_enforce_quota")
    from fastapi import HTTPException

    settings.premium_all = False
    settings.premium_tenant_ids = ""
    settings.free_monthly_worksheets = 100

    class _FakeLedger:
        used = 100
        def worksheets_used_since(self, tenant_ids, since_ts):  # noqa: ARG002
            return self.used

    entitlements.USAGE_LEDGER = _FakeLedger()

    # billing KAPALI → dolu olsa bile no-op (bugünkü davranış)
    settings.billing_enabled = False
    entitlements.enforce_quota("u_texp", 5)  # u_texp = süresi geçmiş trial → free
    check(True, "billing_enabled=False → enforce_quota no-op")

    # billing AÇIK + free dolu (100/100) → 402
    settings.billing_enabled = True
    try:
        entitlements.enforce_quota("u_texp", 1)
        check(False, "free dolu → 402 beklenir")
    except HTTPException as e:
        ok = e.status_code == 402 and isinstance(e.detail, dict) and \
            e.detail.get("error") == "quota_exceeded"
        check(ok, "free dolu + billing açık → 402 quota_exceeded + paywall sinyali")

    # anonim → kotasız (no-op)
    entitlements.enforce_quota(None, 50)
    check(True, "anonim → enforce_quota no-op (SEO kotasız)")

    # yeni tenant → ensure_trial trial açar → fair-use → bloklanmaz
    entitlements.enforce_quota("u_fresh_eq", 5)
    fresh = STORE.get("u_fresh_eq")
    check(fresh is not None and fresh["status"] == "trialing",
          "yeni tenant enforce → trial başlar, bloklanmaz (tam-Pro 7g)")

    settings.billing_enabled = False
    entitlements.USAGE_LEDGER = LEDGER


def test_topup() -> None:
    """Ek kağıt paketi: kredi ekleme (idempotent) + kota-üstü tüketim + tükenince 402."""
    print("test_topup")
    from fastapi import HTTPException
    settings.premium_all = False
    settings.premium_tenant_ids = ""
    settings.billing_enabled = True
    settings.pro_monthly_worksheets = 2
    settings.topup_products = "topup-25:25,topup-75:75"
    t = "u_topup"
    STORE.upsert(tenant_id=t, plan_code="pro", status="active", current_period_end=_iso_in(20))

    class _FakeLedger:  # plan kotası dolu (2/2)
        def worksheets_used_since(self, tenant_ids, since_ts):  # noqa: ARG002
            return 2
    entitlements.USAGE_LEDGER = _FakeLedger()

    # topup yok + plan dolu → 402
    try:
        entitlements.enforce_quota(t)
        check(False, "topup yok + plan dolu → 402 beklenir")
    except HTTPException as e:
        check(e.status_code == 402, "plan dolu, topup yok → 402")

    # credit_topup: bilinmeyen ürün → 0; +25 ekle; aynı tx idempotent
    check(entitlements.credit_topup(t, "yok_urun") == 0, "bilinmeyen ürün → 0 kredi")
    check(entitlements.credit_topup(t, "topup-25", provider_ref="tx_1") == 25, "topup-25 → 25 kredi")
    check(entitlements.credit_topup(t, "topup-25", provider_ref="tx_1") == 0, "aynı tx → idempotent 0")

    q = entitlements.check_quota(t)
    check(q["plan_remaining"] == 0 and q["topup_balance"] == 25 and q["allowed"] is True,
          "plan dolu ama topup 25 → allowed")

    # kota-üstü üretim → topup'tan 1 düşer
    entitlements.enforce_quota(t)
    check(TOPUP.balance(t) == 24, "plan dolu + üretim → topup 25→24 düştü")

    settings.billing_enabled = False
    entitlements.USAGE_LEDGER = LEDGER


def _run() -> int:
    for fn in [
        test_store_empty, test_start_trial, test_trial_expired, test_active_pro,
        test_past_due_grace, test_canceled_and_expired, test_upsert_preserves_created_at,
        test_cancel_flag, test_event_idempotency, test_plan_premium_all,
        test_plan_resolution, test_allowlist_dev, test_quota_limits, test_check_quota,
        test_family_shared_quota, test_ensure_trial, test_enforce_quota, test_topup,
    ]:
        fn()
    print()
    if _failures:
        print(f"❌ {len(_failures)} test BAŞARISIZ:")
        for f in _failures:
            print(f"   - {f}")
        return 1
    print("✅ Tüm billing_store + entitlements testleri geçti.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_run())
