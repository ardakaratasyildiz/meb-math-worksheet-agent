"""Admin key sabit-zaman + kod brute-force throttle testleri (güvenlik).

1) require_admin_key: hmac.compare_digest ile — doğru geçer, yanlış/None 401,
   ADMIN_API_KEY boşsa 503. (Timing yan-kanalı kapatıldı.)
2) /api/classrooms/join ve /api/me/link-child throttle'lı (10/dk) — kod tahmini
   enumerasyonu sınırlanır.

Pytest gerektirmez — `python tests/test_admin_and_throttle.py` da çalışır.
Not: throttle testi ilk sırada — limiter bucket'ı (IP-bazlı) taze olsun.
"""
from __future__ import annotations

import asyncio
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
from fastapi.testclient import TestClient  # noqa: E402

from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402
from app.routers.admin import require_admin_key  # noqa: E402

client = TestClient(app)
_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {msg}")
    if not cond:
        _failures.append(msg)


def _status(coro) -> int | None:
    """require_admin_key'i çalıştırır; HTTPException status'ünü (yoksa None) döner."""
    try:
        asyncio.run(coro)
        return None
    except HTTPException as e:
        return e.status_code


def test_throttle_join_and_link() -> None:
    print("kod brute-force throttle (join/link 10/dk → 429)")
    join = [
        client.post("/api/classrooms/join",
                    json={"tenant_id": "t1", "code": "ZZZZZZ", "display_name": "X"}).status_code
        for _ in range(13)
    ]
    check(429 in join, f"join 13 denemede 429 tetiklendi: {join.count(429)} adet")
    link = [
        client.post("/api/me/link-child",
                    json={"tenant_id": "veli1", "code": "ZZZZZZ", "child_label": "C"}).status_code
        for _ in range(13)
    ]
    check(429 in link, f"link-child 13 denemede 429 tetiklendi: {link.count(429)} adet")


def test_admin_key_constant_time() -> None:
    print("admin key sabit-zaman karşılaştırma (compare_digest)")
    prev = settings.admin_api_key
    try:
        settings.admin_api_key = "s3cret-admin-key"
        check(_status(require_admin_key(x_admin_key="s3cret-admin-key")) is None,
              "doğru key → geçer")
        check(_status(require_admin_key(x_admin_key="wrong")) == 401,
              "yanlış key → 401")
        check(_status(require_admin_key(x_admin_key=None)) == 401,
              "key yok (None) → 401 (compare_digest None'da patlamıyor)")
        settings.admin_api_key = ""
        check(_status(require_admin_key(x_admin_key="anything")) == 503,
              "ADMIN_API_KEY boş → 503 (devre dışı, fail-closed)")
    finally:
        settings.admin_api_key = prev


def _run() -> int:
    test_throttle_join_and_link()
    test_admin_key_constant_time()
    print()
    if _failures:
        print(f"❌ {len(_failures)} test BAŞARISIZ")
        for f in _failures:
            print(f"   - {f}")
        return 1
    print("✅ Tüm admin/throttle testleri geçti.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_run())
