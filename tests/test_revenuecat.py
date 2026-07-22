"""RevenueCat webhook → abonelik senkronu testleri (mobil IAP yolu).

Pytest gerektirmez — `python tests/test_revenuecat.py`.
BillingStore geçici DB'de; revenuecat + entitlements singleton'ları o instance'a
bağlanır (monkeypatch). Karar mantığı (olay türü → durum, plan eşleme, idempotency)
ve entitlements entegrasyonu doğrulanır.
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
from app.services import entitlements, revenuecat  # noqa: E402
from app.services.billing_store import BillingStore  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {msg}")
    if not cond:
        _failures.append(msg)


def _ms_in(days: float) -> int:
    return int((datetime.now(timezone.utc) + timedelta(days=days)).timestamp() * 1000)


def _ev(
    etype: str,
    *,
    user: str = "u_rc",
    product: str = "pro_monthly",
    period: str = "NORMAL",
    exp_days: float = 30,
    ents: list[str] | None = None,
    eid: str | None = None,
) -> dict:
    return {
        "event": {
            "id": eid or f"evt_{etype}_{user}",
            "type": etype,
            "app_user_id": user,
            "product_id": product,
            "period_type": period,
            "expiration_at_ms": _ms_in(exp_days),
            "entitlement_ids": ents or [],
        }
    }


# Geçici DB + test store'una bağla
_TMP = tempfile.mkdtemp()
STORE = BillingStore(db_path=str(Path(_TMP) / "rc_test.sqlite3"))
revenuecat.BILLING_STORE = STORE
entitlements.BILLING_STORE = STORE
settings.premium_all = False
settings.premium_tenant_ids = ""


# ── 1. plan_for eşleme ───────────────────────────────────────────────────────

def test_plan_for() -> None:
    print("test_plan_for")
    settings.revenuecat_product_map = "pro_monthly:pro,plus_yearly:pro-plus"
    check(revenuecat.plan_for({"product_id": "pro_monthly"}) == "pro", "config map → pro")
    check(revenuecat.plan_for({"product_id": "plus_yearly"}) == "pro-plus", "config map → pro-plus")
    settings.revenuecat_product_map = ""
    check(revenuecat.plan_for({"product_id": "premium_plus_x"}) == "pro-plus", "'plus' sezgisi → pro-plus")
    check(
        revenuecat.plan_for({"product_id": "sa_monthly", "entitlement_ids": ["plus"]}) == "pro-plus",
        "entitlement 'plus' → pro-plus",
    )
    check(revenuecat.plan_for({"product_id": "sa_monthly"}) == "pro", "fallback → pro")


# ── 2. Satın alma / yenileme → active ────────────────────────────────────────

def test_initial_purchase() -> None:
    print("test_initial_purchase")
    r = revenuecat.process_webhook(_ev("INITIAL_PURCHASE", user="u_buy"))
    check(r["status"] == "ok" and r["subscription_status"] == "active", "initial → ok/active")
    check(STORE.get_active("u_buy") is not None, "aktif abonelik → get_active döner")
    check(entitlements.plan_of("u_buy") == "pro", "plan_of → pro")
    check(entitlements.is_premium("u_buy") is True, "is_premium True")


def test_trial_period() -> None:
    print("test_trial_period")
    revenuecat.process_webhook(_ev("INITIAL_PURCHASE", user="u_tr", period="TRIAL"))
    check(entitlements.plan_of("u_tr") == "trial", "TRIAL period → plan trial")
    sub = STORE.get("u_tr")
    check(sub["status"] == "trialing" and sub["trial_end"], "trialing + trial_end set")


def test_renewal_updates_period() -> None:
    print("test_renewal_updates_period")
    revenuecat.process_webhook(_ev("INITIAL_PURCHASE", user="u_rn", exp_days=1))
    revenuecat.process_webhook(_ev("RENEWAL", user="u_rn", exp_days=45, eid="evt_rn_2"))
    sub = STORE.get("u_rn")
    check(sub["status"] == "active", "renewal → active")
    check(STORE.get_active("u_rn") is not None, "yenilenen period_end gelecekte → erişim")


# ── 3. İptal / süre dolumu / ödeme sorunu ────────────────────────────────────

def test_cancellation_grace() -> None:
    print("test_cancellation_grace")
    revenuecat.process_webhook(_ev("INITIAL_PURCHASE", user="u_cx", exp_days=20))
    r = revenuecat.process_webhook(_ev("CANCELLATION", user="u_cx", exp_days=20, eid="evt_cx_2"))
    check(r["subscription_status"] == "active", "cancellation → durum hâlâ active")
    sub = STORE.get("u_cx")
    check(sub["cancel_at_period_end"] is True, "cancel_at_period_end işaretlendi")
    check(STORE.get_active("u_cx") is not None, "period_end'e kadar erişim SÜRER (grace)")


def test_expiration() -> None:
    print("test_expiration")
    revenuecat.process_webhook(_ev("INITIAL_PURCHASE", user="u_ex", exp_days=10))
    revenuecat.process_webhook(_ev("EXPIRATION", user="u_ex", exp_days=-1, eid="evt_ex_2"))
    check(STORE.get("u_ex")["status"] == "expired", "expiration → expired")
    check(STORE.get_active("u_ex") is None, "expired → erişim yok")
    check(entitlements.plan_of("u_ex") == "free", "süresi dolmuş → free")


def test_billing_issue() -> None:
    print("test_billing_issue")
    revenuecat.process_webhook(_ev("BILLING_ISSUE", user="u_bi", exp_days=3))
    check(STORE.get("u_bi")["status"] == "past_due", "billing_issue → past_due")
    check(STORE.get_active("u_bi") is not None, "past_due + period gelecekte → dunning grace erişimi")


# ── 4. Idempotency + atlanan olaylar ─────────────────────────────────────────

def test_idempotency() -> None:
    print("test_idempotency")
    ev = _ev("INITIAL_PURCHASE", user="u_id", eid="evt_dup")
    r1 = revenuecat.process_webhook(ev)
    r2 = revenuecat.process_webhook(ev)
    check(r1["status"] == "ok", "ilk geliş → ok")
    check(r2["status"] == "duplicate", "aynı event.id tekrar → duplicate (idempotent)")


def test_anonymous_skipped() -> None:
    print("test_anonymous_skipped")
    r = revenuecat.process_webhook(_ev("INITIAL_PURCHASE", user="$RCAnonymousID:abc", eid="evt_anon"))
    check(r["status"] == "skipped" and r["reason"] == "anonymous_user", "anonim app_user_id → skipped")


def test_ignored_and_unmapped() -> None:
    print("test_ignored_and_unmapped")
    r = revenuecat.process_webhook(_ev("TEST", user="u_ig", eid="evt_test"))
    check(r["status"] == "ignored", "TEST türü → ignored")
    r = revenuecat.process_webhook(_ev("SOME_FUTURE_TYPE", user="u_un", eid="evt_un"))
    check(r["status"] == "ignored", "eşlenmemiş tür → ignored (abonelik değişmez)")
    check(STORE.get("u_un") is None, "eşlenmemiş tür → abonelik satırı açılmaz")


def test_malformed() -> None:
    print("test_malformed")
    check(revenuecat.process_webhook({})["status"] == "skipped", "boş gövde → skipped")
    check(
        revenuecat.process_webhook({"event": {"type": "RENEWAL"}})["status"] == "skipped",
        "id/app_user_id yok → skipped",
    )


def _run() -> int:
    for fn in [
        test_plan_for, test_initial_purchase, test_trial_period,
        test_renewal_updates_period, test_cancellation_grace, test_expiration,
        test_billing_issue, test_idempotency, test_anonymous_skipped,
        test_ignored_and_unmapped, test_malformed,
    ]:
        fn()
    print()
    if _failures:
        print(f"❌ {len(_failures)} test BAŞARISIZ:")
        for f in _failures:
            print(f"   - {f}")
        return 1
    print("✅ Tüm RevenueCat webhook testleri geçti.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_run())
