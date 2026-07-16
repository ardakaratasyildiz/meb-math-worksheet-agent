"""Router tenant-guard testleri (IDOR/spoof regresyon kilidi).

Bağlam: `X-API-Key` prod'da PUBLIC bir tarayıcı key'idir; kullanıcı ayrımı
`tenant_id`'ye dayanır. Clerk JWT doğrulaması AÇIKKEN, tenant-kapsamlı uçlar
client-supplied `tenant_id`'ye GÜVENMEMELİ (aksi halde saldırgan public key +
kurbanın userId'si ile başkasının verisini okur/siler — IDOR).

Bu test, `me.py` DIŞINDA sonradan korunan router'ların (classrooms, worksheets
history, quizzes) `require_tenant` kapısını gerçekten çağırdığını TestClient ile
doğrular:
  - Clerk KAPALI  → supplied tenant kullanılır (200, geriye uyumlu davranış).
  - Clerk AÇIK + geçerli oturum YOK → 401 (spoof reddedilir), Bearer olmadan.

Pytest gerektirmez — `python tests/test_router_tenant_guard.py` da çalışır
(CI eval test dosyalarını doğrudan koşar).
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

from fastapi.testclient import TestClient  # noqa: E402

from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)

# Yeni korunan, gövde gerektirmeyen GET uçları (kimlik kapısı store'dan ÖNCE çalışır).
_GUARDED_GET = [
    "/api/classrooms?tenant_id=victim_user_123",
    "/api/worksheets/history?tenant_id=victim_user_123",
    "/api/quizzes/nonexistent_quiz?tenant_id=victim_user_123",
]

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {msg}")
    if not cond:
        _failures.append(msg)


def test_auth_enabled_rejects_spoofed_tenant() -> None:
    """Clerk açık + Bearer yok → tüm korunan uçlar 401 (client tenant'a güvenilmez)."""
    print("test_auth_enabled_rejects_spoofed_tenant")
    settings.clerk_issuer = "https://clerk.test.example.com"
    try:
        for url in _GUARDED_GET:
            r = client.get(url)  # Authorization header YOK → doğrulanmış kimlik yok
            check(r.status_code == 401, f"401 (spoof reddi): {url} → {r.status_code}")
    finally:
        settings.clerk_issuer = ""


def test_auth_disabled_allows_supplied_tenant() -> None:
    """Clerk kapalı → supplied tenant kullanılır (geriye uyumlu; 401 DEĞİL)."""
    print("test_auth_disabled_allows_supplied_tenant")
    settings.clerk_issuer = ""
    # Bilinmeyen tenant → 200 + boş veri (401 OLMAMALI; kimlik kapısı düşmez).
    r1 = client.get("/api/classrooms?tenant_id=whoever_123")
    check(r1.status_code == 200, f"classrooms clerk-kapalı → 200 ({r1.status_code})")
    r2 = client.get("/api/worksheets/history?tenant_id=whoever_123")
    check(r2.status_code == 200, f"worksheets/history clerk-kapalı → 200 ({r2.status_code})")


def _run() -> int:
    test_auth_enabled_rejects_spoofed_tenant()
    test_auth_disabled_allows_supplied_tenant()
    print()
    if _failures:
        print(f"❌ {len(_failures)} test BAŞARISIZ:")
        for f in _failures:
            print(f"   - {f}")
        return 1
    print("✅ Tüm router tenant-guard testleri geçti.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_run())
