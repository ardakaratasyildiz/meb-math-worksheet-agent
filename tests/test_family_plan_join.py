"""Veli↔çocuk bağı kurulunca çocuk HEMEN velinin planına dahil olur.

Pytest gerektirmez — `python tests/test_family_plan_join.py`. Ağ çağrısı yok
(geçici DB dosyası).

SAHA BULGUSU (kullanıcı sorusu 2026-08-24, yerel simülasyonla doğrulandı):
"Veli Pro aldı, çocuğu bunu nasıl kullanacak?" akışı çalışıyordu AMA çocuk hesabı
uygulamayı veliden ÖNCE kullandıysa `enforce_quota` ona otomatik 7 günlük deneme
açıyor; `_billing_owner` da çocuğun KENDİ aktif satırını velinin ÜCRETLİ planına
tercih ediyordu. Sonuç: veli Pro aldığı hâlde çocuk 7 gün aile havuzuna girmiyor,
ekranda "deneme" (20 kağıt, ayrı havuz) görüyordu.

    çocuk2 kendi planı: trial
    çocuk2 (veliye BAĞLANDIKTAN sonra): trial   ← Pro değil
    çocuk2 kota: limit=20 owner=user_cocuk2     ← velinin havuzuna girmedi

KARAR (kullanıcı): bağlanma anında çocuğun denemesi KAPATILIR ve çocuk plana
dahil edilir (entitlements.absorb_into_family → BILLING_STORE.end_trial_now).
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

from app.config import settings  # noqa: E402
from app.services import entitlements as e  # noqa: E402
from app.services.billing_store import BillingStore  # noqa: E402
from app.services.parent_link_store import ParentLinkStore  # noqa: E402
from app.services.top_up_store import TopUpStore  # noqa: E402
from app.services.usage_ledger import UsageLedger  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if cond:
        print(f"  ok   {msg}")
    else:
        _failures.append(msg)
        print(f"  FAIL {msg}")


def _fresh_stores() -> None:
    """Her senaryo temiz bir DB ile koşar (singleton'lar geçici dosyaya bağlanır)."""
    tmp = os.path.join(tempfile.mkdtemp(), "family.sqlite3")
    e.BILLING_STORE = BillingStore(db_path=tmp)
    e.PARENT_LINK_STORE = ParentLinkStore(db_path=tmp)
    e.TOP_UP_STORE = TopUpStore(db_path=tmp)
    e.USAGE_LEDGER = UsageLedger(db_path=tmp)


def _make_pro_parent(parent: str) -> None:
    e.BILLING_STORE.upsert(
        tenant_id=parent, plan_code="pro", status="active",
        current_period_end="2099-01-01T00:00:00+00:00",
    )


def _link(parent: str, child: str) -> bool:
    code = e.PARENT_LINK_STORE.get_or_create_code(child)
    assert e.PARENT_LINK_STORE.link(parent, code, "Çocuk") == child
    return e.absorb_into_family(child, parent)  # link_child'ın yaptığı iş


def test_clean_child_inherits() -> None:
    print("\n[1] hiç kullanmamış çocuk → bağlanınca velinin planı + havuzu")
    _fresh_stores()
    _make_pro_parent("veli")
    check(e.plan_of("cocuk") == "free", "bağlanmadan önce ücretsiz")
    absorbed = _link("veli", "cocuk")
    check(absorbed is False, "kapatılacak deneme yok → False")
    check(e.plan_of("cocuk") == "pro", "bağlandıktan sonra plan pro")
    q = e.check_quota("cocuk")
    check(q["owner"] == "veli" and q["limit"] == 50, "kota havuzu velinin (50 kağıt)")
    check(e.is_premium_for_model("cocuk"), "premium model")
    check(e.has_paid_access("cocuk"), "filigransız PDF")


def test_child_with_own_trial_joins_immediately() -> None:
    print("\n[2] KENDİ denemesi olan çocuk → deneme kapanır, HEMEN plana girer")
    _fresh_stores()
    prev = settings.billing_enabled
    settings.billing_enabled = True
    try:
        _make_pro_parent("veli")
        e.enforce_quota("cocuk")  # ilk üretim → kendi 7 günlük denemesi açılır
        check(e.plan_of("cocuk") == "trial", "bağ öncesi kendi denemesinde")
        absorbed = _link("veli", "cocuk")
        check(absorbed is True, "deneme kapatıldı")
        check(e.plan_of("cocuk") == "pro", "artık velinin planında (eskiden 7 gün trial kalıyordu)")
        q = e.check_quota("cocuk")
        check(q["owner"] == "veli", "aile havuzuna girdi")
        check(q["limit"] == 50, "Pro kotası (20'lik deneme değil)")
    finally:
        settings.billing_enabled = prev


def test_no_second_trial_after_absorb() -> None:
    print("\n[3] deneme SİLİNMEZ, expired olur → ikinci deneme kazanılmaz")
    _fresh_stores()
    prev = settings.billing_enabled
    settings.billing_enabled = True
    try:
        _make_pro_parent("veli")
        e.enforce_quota("cocuk")
        _link("veli", "cocuk")
        row = e.BILLING_STORE.get("cocuk")
        check(row is not None and row["status"] == "expired", "satır expired (kayıt korunur)")
        e.ensure_trial("cocuk")  # yeniden deneme açılmaya çalışılır
        row = e.BILLING_STORE.get("cocuk")
        check(row is not None and row["status"] == "expired", "yeni deneme AÇILMADI")
    finally:
        settings.billing_enabled = prev


def test_paid_child_subscription_untouched() -> None:
    print("\n[4] çocuğun KENDİ ÜCRETLİ aboneliğine dokunulmaz (para çöpe gitmez)")
    _fresh_stores()
    _make_pro_parent("veli")
    e.BILLING_STORE.upsert(
        tenant_id="cocuk", plan_code="pro-plus", status="active",
        current_period_end="2099-01-01T00:00:00+00:00",
    )
    absorbed = _link("veli", "cocuk")
    check(absorbed is False, "ücretli abonelik kapatılmadı")
    row = e.BILLING_STORE.get("cocuk")
    check(row is not None and row["status"] == "active", "satır hâlâ active")
    check(e.plan_of("cocuk") == "pro-plus", "çocuk kendi (daha iyi) planında kalır")


def test_parent_without_plan_does_not_burn_child_trial() -> None:
    print("\n[5] velinin verecek planı yoksa çocuğun denemesi YAKILMAZ")
    _fresh_stores()
    prev = settings.billing_enabled
    prev_all = settings.premium_all
    settings.billing_enabled = True
    settings.premium_all = False
    try:
        e.enforce_quota("cocuk")  # çocuğun kendi denemesi
        check(e.plan_of("cocuk") == "trial", "çocuk denemede")
        absorbed = e.absorb_into_family("cocuk", "veli_ucretsiz")
        check(absorbed is False, "ücretsiz veli çocuğun denemesini kapatamaz")
        check(e.plan_of("cocuk") == "trial", "çocuk denemesini korudu")
    finally:
        settings.billing_enabled = prev
        settings.premium_all = prev_all


def main() -> int:
    for fn in (
        test_clean_child_inherits,
        test_child_with_own_trial_joins_immediately,
        test_no_second_trial_after_absorb,
        test_paid_child_subscription_untouched,
        test_parent_without_plan_does_not_burn_child_trial,
    ):
        fn()
    print()
    if _failures:
        print(f"FAILED: {len(_failures)} assert düştü")
        return 1
    print("PASSED: çocuk bağlanınca velinin planına hemen dahil oluyor")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
