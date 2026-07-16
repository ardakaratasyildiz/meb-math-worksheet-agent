"""me.py tenant guard testleri (P0 wiring).

_require_tenant: doğrulanmış kimliği tercih eder; auth açıkken doğrulanmamış
istekte 401; auth kapalıyken supplied'a düşer (bugünkü davranış).

Pytest gerektirmez — `python tests/test_me_tenant_guard.py`.
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
from app.routers.me import _require_tenant  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {msg}")
    if not cond:
        _failures.append(msg)


def test_auth_disabled_uses_supplied() -> None:
    print("test_auth_disabled_uses_supplied")
    settings.clerk_issuer = ""  # doğrulama kapalı
    check(
        _require_tenant(None, "user_supplied") == "user_supplied",
        "auth kapalı → supplied tenant kullanılır (bugünkü davranış)",
    )


def test_auth_disabled_empty_supplied_401() -> None:
    print("test_auth_disabled_empty_supplied_401")
    settings.clerk_issuer = ""
    try:
        _require_tenant(None, "")
        check(False, "boş tenant 401 vermeli")
    except HTTPException as e:
        check(e.status_code == 401, "auth kapalı + boş supplied → 401")


def test_auth_enabled_prefers_verified() -> None:
    print("test_auth_enabled_prefers_verified")
    settings.clerk_issuer = "https://clerk.test.example.com"
    check(
        _require_tenant("verified_u", "spoofed") == "verified_u",
        "auth açık → doğrulanmış tenant, supplied yok sayılır (spoof koruması)",
    )
    settings.clerk_issuer = ""


def test_auth_enabled_no_verified_401() -> None:
    print("test_auth_enabled_no_verified_401")
    settings.clerk_issuer = "https://clerk.test.example.com"
    try:
        _require_tenant(None, "spoofed")
        check(False, "auth açık + doğrulanmamış → 401 vermeli")
    except HTTPException as e:
        check(
            e.status_code == 401,
            "auth açık + verified yok → 401 (supplied'a güvenilmez)",
        )
    settings.clerk_issuer = ""


def _run() -> int:
    test_auth_disabled_uses_supplied()
    test_auth_disabled_empty_supplied_401()
    test_auth_enabled_prefers_verified()
    test_auth_enabled_no_verified_401()
    print()
    if _failures:
        print(f"❌ {len(_failures)} test BAŞARISIZ:")
        for f in _failures:
            print(f"   - {f}")
        return 1
    print("✅ Tüm me tenant-guard testleri geçti.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_run())
