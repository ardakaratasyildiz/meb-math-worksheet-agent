"""Kota kapısı altyapı hatasında ÜRETİMİ DURDURMAZ (fail-open).

Pytest gerektirmez — `python tests/test_quota_fail_open.py`. LLM/ağ çağrısı yok.

NEDEN: `billing_enabled=True` + `premium_all=False` 2026-08-21'de açıldı; o günden
beri giriş yapmış HER üretim `enforce_quota` zincirinden geçiyor (billing_store /
parent_link_store / top_up_store / usage_ledger — prod'da Turso). Zincir korumasızdı:
tek bir DB hatası HTTP 500'e dönüşüp kullanıcının HİÇ soru üretememesine yol açar,
üstelik anonim istekler kapıya girmediği için çalışmaya devam ettiğinden hata
"mobil bozuk" gibi görünür. Doğru arıza yönü: sayaç okunamıyorsa hizmeti kesme,
ERROR logla. 402 (gerçek kota kararı) ise DAİMA geçmeli — yutulmamalı.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("GEMINI_API_KEY", "fake-key-for-tests")

from fastapi import HTTPException  # noqa: E402

from app.config import settings  # noqa: E402
from app.services import entitlements  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if cond:
        print(f"  ok   {msg}")
    else:
        _failures.append(msg)
        print(f"  FAIL {msg}")


class _Boom:
    """Her okumada patlayan depo (Turso arızası taklidi)."""

    def get_active(self, *a, **k):
        raise RuntimeError("turso: no such table: subscriptions")

    def get(self, *a, **k):
        raise RuntimeError("turso: connection reset")

    def start_trial(self, *a, **k):
        raise RuntimeError("turso: read-only database")


def test_enforce_quota_fails_open() -> None:
    print("\n[1] depo patlarsa üretim GEÇER (500 değil)")
    prev_store, prev_flag = entitlements.BILLING_STORE, settings.billing_enabled
    entitlements.BILLING_STORE = _Boom()  # type: ignore[assignment]
    settings.billing_enabled = True
    try:
        entitlements.enforce_quota("user_boom")
        check(True, "enforce_quota istisna fırlatmadı (fail-open)")
    except Exception as exc:  # noqa: BLE001
        check(False, f"enforce_quota patladı: {type(exc).__name__}: {exc}")
    finally:
        entitlements.BILLING_STORE, settings.billing_enabled = prev_store, prev_flag


def test_model_and_plan_decisions_fail_safe() -> None:
    print("\n[2] model/plan kararı GÜVENLİ yöne düşer (premium değil / free)")
    prev = entitlements.BILLING_STORE
    entitlements.BILLING_STORE = _Boom()  # type: ignore[assignment]
    try:
        check(
            entitlements.is_premium_for_model("user_boom") is False,
            "is_premium_for_model → False (pahalı model bedava dağıtılmaz)",
        )
        check(
            entitlements.has_paid_access("user_boom") is False,
            "has_paid_access → False (filigran korunur)",
        )
        if not settings.premium_all:
            check(entitlements.plan_of("user_boom") == "free", "plan_of → free")
    finally:
        entitlements.BILLING_STORE = prev


def test_real_quota_402_still_raised() -> None:
    print("\n[3] GERÇEK kota kararı (402) yutulmaz")
    prev_flag = settings.billing_enabled
    prev_check = entitlements.check_quota
    settings.billing_enabled = True
    entitlements.check_quota = lambda tenant_id, requested=0: {  # type: ignore[assignment]
        "plan": "free", "limit": 10, "used": 10, "remaining": 0, "allowed": False,
        "block_reason": "monthly", "plan_remaining": 0, "topup_balance": 0,
        "daily_limit": 2, "daily_remaining": 0, "owner": tenant_id,
    }
    try:
        entitlements.enforce_quota("user_full")
        check(False, "kota dolu olmasına rağmen 402 fırlatılmadı")
    except HTTPException as exc:
        check(exc.status_code == 402, f"402 fırlatıldı (status={exc.status_code})")
        check(
            isinstance(exc.detail, dict) and exc.detail.get("error") == "quota_exceeded",
            "402 gövdesi paywall sinyalini taşıyor",
        )
    except Exception as exc:  # noqa: BLE001
        check(False, f"beklenmeyen hata: {type(exc).__name__}: {exc}")
    finally:
        settings.billing_enabled = prev_flag
        entitlements.check_quota = prev_check  # type: ignore[assignment]


def main() -> int:
    for fn in (
        test_enforce_quota_fails_open,
        test_model_and_plan_decisions_fail_safe,
        test_real_quota_402_still_raised,
    ):
        fn()
    print()
    if _failures:
        print(f"FAILED: {len(_failures)} assert düştü")
        return 1
    print("PASSED: kota kapısı fail-open, 402 korunuyor")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
