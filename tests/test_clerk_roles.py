"""Sunucu-tarafı rol kontrolü testleri (clerk_roles).

Pytest gerektirmez — `python tests/test_clerk_roles.py`. Ağ çağrısı yok:
_fetch_role monkeypatch'lenir.
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
from app.services import clerk_roles  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {msg}")
    if not cond:
        _failures.append(msg)


def _set_role(role: str | None) -> None:
    """_fetch_role'ü sabit role döndürecek şekilde patch'le + cache temizle."""
    clerk_roles._clear_cache()
    clerk_roles._fetch_role = lambda tid: role  # type: ignore[assignment]


def test_secret_disabled() -> None:
    print("test_secret_disabled")
    settings.clerk_secret_key = ""
    clerk_roles._clear_cache()
    check(clerk_roles.get_user_role("user_abc") is None, "secret yok → rol None")
    # enforce fail-open: secret yokken bloklamaz
    clerk_roles.enforce_role("user_abc", {"teacher"})
    check(True, "secret yok → enforce_role no-op (fail-open)")


def test_non_clerk_id() -> None:
    print("test_non_clerk_id")
    settings.clerk_secret_key = "sk_test_x"
    _set_role("teacher")
    check(clerk_roles.get_user_role(None) is None, "None id → None")
    check(clerk_roles.get_user_role("anon") is None, "non-clerk id (anon) → None")
    check(clerk_roles.get_user_role("user_1") == "teacher", "clerk id → rol döner")
    settings.clerk_secret_key = ""


def test_enforce_allowed() -> None:
    print("test_enforce_allowed")
    settings.clerk_secret_key = "sk_test_x"
    _set_role("teacher")
    clerk_roles.enforce_role("user_t", {"teacher", "admin"})
    check(True, "teacher + {teacher,admin} → izin (raise yok)")
    settings.clerk_secret_key = ""


def test_enforce_denied() -> None:
    print("test_enforce_denied")
    settings.clerk_secret_key = "sk_test_x"
    _set_role("student")
    try:
        clerk_roles.enforce_role("user_s", {"teacher", "admin"})
        check(False, "student create → 403 beklenir")
    except HTTPException as e:
        check(e.status_code == 403, "student + {teacher,admin} → 403")
    settings.clerk_secret_key = ""


def test_admin_allowed_both() -> None:
    print("test_admin_allowed_both")
    settings.clerk_secret_key = "sk_test_x"
    _set_role("admin")
    clerk_roles.enforce_role("user_a", {"teacher", "admin"})
    clerk_roles.enforce_role("user_a", {"student", "admin"})
    check(True, "admin → hem create hem join setinde izinli")
    settings.clerk_secret_key = ""


def test_role_none_fail_open() -> None:
    print("test_role_none_fail_open")
    settings.clerk_secret_key = "sk_test_x"
    _set_role(None)  # rol belirlenemedi (API hatası vb.)
    clerk_roles.enforce_role("user_x", {"teacher"})
    check(True, "rol None (belirlenemedi) → enforce no-op (fail-open)")
    settings.clerk_secret_key = ""


def test_cache_hit() -> None:
    print("test_cache_hit")
    settings.clerk_secret_key = "sk_test_x"
    clerk_roles._clear_cache()
    calls = {"n": 0}

    def counting_fetch(tid):  # noqa: ANN001
        calls["n"] += 1
        return "teacher"

    clerk_roles._fetch_role = counting_fetch  # type: ignore[assignment]
    clerk_roles.get_user_role("user_cache")
    clerk_roles.get_user_role("user_cache")
    check(calls["n"] == 1, "ikinci çağrı cache'ten (fetch 1 kez)")
    settings.clerk_secret_key = ""
    clerk_roles._clear_cache()


def _run() -> int:
    for fn in [
        test_secret_disabled, test_non_clerk_id, test_enforce_allowed,
        test_enforce_denied, test_admin_allowed_both, test_role_none_fail_open,
        test_cache_hit,
    ]:
        fn()
    print()
    if _failures:
        print(f"❌ {len(_failures)} test BAŞARISIZ:")
        for f in _failures:
            print(f"   - {f}")
        return 1
    print("✅ Tüm clerk_roles testleri geçti.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_run())
