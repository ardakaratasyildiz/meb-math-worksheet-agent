"""2026-08-24/25 genel denetim turunun dört düzeltmesi.

Pytest gerektirmez — `python tests/test_audit_fixes_202608.py`. LLM/ağ çağrısı yok.

1) `/generate.stream` doğrulanmış kimliği BAĞLAR. 2026-08-21'de eklenen
   `_bind_verified_tenant` üç üretim ucundan ikisine konmuş, web'in gerçekte
   kullandığı stream ucu atlanmıştı → kota/defter gövdeden gelen `tenant_id`'ye
   yazılıyordu (sayaç artmıyor + geçmişte görünmüyor) ve gövdedeki tenant istemci
   beyanı olduğu için başkasının kimliğini yazan biri onun geçmişine kağıt
   yazdırıp `is_premium_for_model` üzerinden ONUN premium modelini alabiliyordu.

3) Ek paket kredisi üretimden ÖNCE düşülüyor ama üretim çökerse İADE EDİLİYOR.
   Eskiden iade yolu yoktu: ödeyen kullanıcı almadığı kağıdın kredisini
   kaybediyordu (plan kotasında bu düşünülmüştü, ek pakette değil).

4) Agent artık İSTEK BAŞINA izole. `GeminiAgent` üretim izlerini örnek durumunda
   tutuyor; `@lru_cache`'li paylaşılan örnek eşzamanlı isteklerde maliyeti/modeli
   yanlış tenant'a yazıyordu (üretim 30-90 sn → çakışma kaçınılmaz).

5) `/regenerate-question` doğrulanmış kimliği kullanır (diğer uçlarla tutarlı).
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

import inspect  # noqa: E402

from app.config import settings  # noqa: E402
from app.routers import quizzes as quizzes_router  # noqa: E402
from app.routers import worksheets as ws  # noqa: E402
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


def test_stream_binds_verified_tenant() -> None:
    print("\n[1] üretim uçlarının HEPSİ doğrulanmış kimliği bağlıyor")
    for name in ("generate_worksheet", "generate_worksheet_pdf", "generate_worksheet_stream"):
        fn = getattr(ws, name)
        src = inspect.getsource(inspect.unwrap(fn))
        check("_bind_verified_tenant" in src, f"{name}: _bind_verified_tenant çağrılıyor")
    # stream jeneratörü iade parametrelerini alıyor mu (kredi geri verme yolu)
    sig = inspect.signature(ws._stream_worksheet_events)
    check("topup_charged" in sig.parameters, "stream jeneratörü topup_charged alıyor")
    check("quota_tenant" in sig.parameters, "stream jeneratörü quota_tenant alıyor")


def test_regenerate_question_uses_verified() -> None:
    print("\n[5] /regenerate-question doğrulanmış kimliği kullanıyor")
    sig = inspect.signature(inspect.unwrap(ws.regenerate_question))
    check("verified" in sig.parameters, "verified bağımlılığı var")
    src = inspect.getsource(inspect.unwrap(ws.regenerate_question))
    check("req.tenant_id = verified" in src, "doğrulanmış kimlik gövdeye yazılıyor")


def test_agents_are_isolated_per_request() -> None:
    print("\n[4] agent istek başına İZOLE (paylaşılan örnek yok)")
    # NOT: tests/test_study_plan.py import edilirken `settings.gemini_api_key`'i
    # KALICI olarak boşaltıyor (monkeypatch DEĞİL) ve pytest tüm test modüllerini
    # koşudan ÖNCE import ediyor → agent kurulumu AgentError veriyor. Bu test sıradan
    # bağımsız olsun diye anahtarı kendisi kurup geri koyar.
    prev_key = settings.gemini_api_key
    settings.gemini_api_key = prev_key or "fake-key-for-tests"
    try:
        for mod, label in ((ws, "worksheets"), (quizzes_router, "quizzes")):
            fn = mod._agent_for_model
            check(
                not hasattr(fn, "cache_info"),
                f"{label}._agent_for_model artık lru_cache'li DEĞİL",
            )
            a = fn("gemini-2.5-flash", 0)
            b = fn("gemini-2.5-flash", 0)
            check(a is not b, f"{label}: aynı model için AYRI nesne döner")
    finally:
        settings.gemini_api_key = prev_key


def test_topup_refunded_when_generation_fails() -> None:
    print("\n[3] üretim çökerse ek paket kredisi İADE edilir")
    tmp = os.path.join(tempfile.mkdtemp(), "topup.sqlite3")
    e.BILLING_STORE = BillingStore(db_path=tmp)
    e.PARENT_LINK_STORE = ParentLinkStore(db_path=tmp)
    e.TOP_UP_STORE = TopUpStore(db_path=tmp)
    e.USAGE_LEDGER = UsageLedger(db_path=tmp)
    prev_flag, prev_all = settings.billing_enabled, settings.premium_all
    settings.billing_enabled = True
    settings.premium_all = False
    try:
        tid = "user_topup"
        # Pro abone + planı BİTMİŞ gibi davran (check_quota'yı sabitle) + 25 kredi
        e.BILLING_STORE.upsert(
            tenant_id=tid, plan_code="pro", status="active",
            current_period_end="2099-01-01T00:00:00+00:00",
        )
        e.TOP_UP_STORE.add(tid, 25, provider_ref="test-1")
        check(e.TOP_UP_STORE.balance(tid) == 25, "başlangıç bakiyesi 25")

        prev_check = e.check_quota
        e.check_quota = lambda tenant_id, requested=0: {  # type: ignore[assignment]
            "plan": "pro", "limit": 50, "used": 50, "remaining": 25, "allowed": True,
            "block_reason": None, "plan_remaining": 0,
            "topup_balance": e.TOP_UP_STORE.balance(tid), "owner": tid,
            "daily_limit": None, "daily_remaining": None,
        }
        try:
            charged = e.enforce_quota(tid)
            check(charged is True, "kapı ek paketten düştüğünü BİLDİRİYOR")
            check(e.TOP_UP_STORE.balance(tid) == 24, "kredi düşüldü (24)")
            # üretim çöktü → iade
            refunded = e.refund_topup(tid)
            check(refunded == 1, "1 kredi iade edildi")
            check(e.TOP_UP_STORE.balance(tid) == 25, "bakiye eski hâline döndü (25)")
            # iade HAVADAN kredi yaratmaz
            e.refund_topup(tid)
            e.refund_topup(tid)
            check(e.TOP_UP_STORE.balance(tid) == 25, "fazla iade paketi amount üstüne çıkarmaz")
        finally:
            e.check_quota = prev_check  # type: ignore[assignment]
    finally:
        settings.billing_enabled, settings.premium_all = prev_flag, prev_all


def test_generation_paths_refund_on_failure() -> None:
    print("\n[3b] üretim uçları hata yolunda iade çağırıyor")
    for name in ("generate_worksheet", "generate_worksheet_pdf"):
        src = inspect.getsource(inspect.unwrap(getattr(ws, name)))
        check("refund_topup" in src, f"{name}: hata yolunda refund_topup var")
    src = inspect.getsource(ws._stream_worksheet_events)
    check(src.count("refund_topup") >= 2, "stream: iki hata dalında da iade var")
    src = inspect.getsource(inspect.unwrap(quizzes_router.create_quiz))
    check(src.count("refund_topup") >= 2, "quiz: hata + boş sonuç yolunda iade var")


def main() -> int:
    for fn in (
        test_stream_binds_verified_tenant,
        test_regenerate_question_uses_verified,
        test_agents_are_isolated_per_request,
        test_topup_refunded_when_generation_fails,
        test_generation_paths_refund_on_failure,
    ):
        fn()
    print()
    if _failures:
        print(f"FAILED: {len(_failures)} assert düştü")
        return 1
    print("PASSED: denetim turu düzeltmeleri yerinde")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
