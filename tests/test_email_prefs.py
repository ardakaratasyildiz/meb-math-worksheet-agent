"""E-posta tercihleri (KVKK opt-in) testleri — Track 2 temeli.

`python tests/test_email_prefs.py`. LLM/ağ yok.
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

from app.services.email_prefs_store import EmailPrefsStore  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {msg}")
    if not cond:
        _failures.append(msg)


def test_prefs() -> None:
    print("email prefs — get/set/opt-in listesi")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        store = EmailPrefsStore(db_path=str(Path(tmp) / "t.sqlite3"))
        try:
            check(store.get("u1") is None, "başta tercih yok (None → onay kartı)")
            store.set(tenant_id="u1", email="ali@x.com", newsletter_optin=True)
            p = store.get("u1")
            check(p is not None and p["newsletter_optin"] is True, "opt-in True kaydedildi")
            check(p["email"] == "ali@x.com", "e-posta saklandı")
            # Geri alma (unsubscribe)
            store.set(tenant_id="u1", email="ali@x.com", newsletter_optin=False)
            check(store.get("u1")["newsletter_optin"] is False, "opt-out güncellendi")
            # Opt-in listesi yalnız onaylı + e-postalı
            store.set(tenant_id="u2", email="ayse@x.com", newsletter_optin=True)
            store.set(tenant_id="u3", email=None, newsletter_optin=True)  # e-posta yok
            opted = store.list_opted_in()
            ids = {o["tenant_id"] for o in opted}
            check(ids == {"u2"}, f"opt-in listesi yalnız u2: {ids}")
        finally:
            store.close()


def test_app_imports() -> None:
    print("uygulama import — email-prefs endpoint'leri kayıtlı")
    from app.main import app  # noqa: PLC0415

    paths = {r.path for r in app.routes}
    check("/api/me/email-prefs" in paths, "GET/POST /api/me/email-prefs kayıtlı")


def main() -> int:
    for fn in (test_prefs, test_app_imports):
        fn()
    print()
    if _failures:
        print(f"FAILED: {len(_failures)} assert düştü")
        return 1
    print("PASSED: email prefs testleri geçti")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
