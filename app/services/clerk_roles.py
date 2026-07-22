"""Sunucu-tarafı ROL kontrolü — Clerk publicMetadata.role'ü backend'de doğrular.

Rol kaynak-of-truth'u Clerk `publicMetadata.role` (sunucu-set, kalıcı; bkz. frontend
`/api/role`). Frontend UI zaten role göre ayrışıyor; bu modül aynı kararı BACKEND'de
zorlar → öğrenci create-classroom, öğretmen join-classroom gibi uçları API'den de
çağıramaz (UI baypası kapanır).

Rolü Clerk Backend API'den (GET /v1/users/{id}) `CLERK_SECRET_KEY` ile çeker, bellekte
cache'ler (rol kalıcı → uzun TTL). Karar HER ZAMAN doğrulanmış tenant_id üzerinden
verilir (bkz. clerk_auth.require_tenant).

Kademeli açılış: `clerk_secret_key` BOŞ → rol belirlenemez → enforce_role **fail-open**
(bloklamaz; bugünkü davranış). Secret set edilince enforcement devreye girer.
"""
from __future__ import annotations

import logging
import threading
import time

import requests

from app.config import settings

logger = logging.getLogger(__name__)

_CLERK_API = "https://api.clerk.com/v1"
# tenant_id -> (fetched_at, role|None)
_cache: dict[str, tuple[float, str | None]] = {}
_lock = threading.Lock()


def _fetch_role(tenant_id: str) -> str | None:
    """Clerk Backend API'den publicMetadata.role çeker (hata → None, fail-open)."""
    try:
        r = requests.get(
            f"{_CLERK_API}/users/{tenant_id}",
            headers={"Authorization": f"Bearer {settings.clerk_secret_key.strip()}"},
            timeout=6,
        )
    except Exception as exc:  # noqa: BLE001 — ağ hatası enforcement'ı bloklamasın
        logger.warning("Clerk rol çekilemedi (%s): %s", tenant_id, exc)
        return None
    if r.status_code != 200:
        logger.warning("Clerk user fetch %s → HTTP %s", tenant_id, r.status_code)
        return None
    try:
        pm = (r.json() or {}).get("public_metadata") or {}
    except ValueError:
        return None
    role = pm.get("role")
    return role if isinstance(role, str) and role else None


def get_user_role(tenant_id: str | None) -> str | None:
    """Doğrulanmış tenant'ın rolü (student|teacher|parent|admin) — cache'li. Yoksa None.

    None döner: secret yok · anon/non-Clerk id · API hatası · rol atanmamış.
    """
    if not tenant_id or not tenant_id.startswith("user_"):
        return None
    if not settings.clerk_secret_key.strip():
        return None
    now = time.time()
    with _lock:
        hit = _cache.get(tenant_id)
        if hit and now - hit[0] < settings.clerk_role_cache_ttl:
            return hit[1]
    role = _fetch_role(tenant_id)
    with _lock:
        _cache[tenant_id] = (now, role)
    return role


_SELECTABLE_ROLES = {"student", "teacher", "parent"}


def set_user_role(tenant_id: str, role: str) -> str:
    """Kullanıcının publicMetadata.role'ünü Clerk Backend API ile set eder (TEK SEFERLİK).

    - role selectable olmalı (student|teacher|parent); admin buradan verilemez.
    - Zaten bir rol atanmışsa DEĞİŞTİRMEZ → mevcut rolü döner (onboarding tek seferlik;
      frontend /api/role deseniyle aynı). Böylece kullanıcı rolünü sonradan değiştiremez.
    - clerk_secret_key yoksa RuntimeError (çağıran 503 döndürebilir).

    Dönen: efektif rol (yeni set edilen ya da zaten var olan).
    """
    if role not in _SELECTABLE_ROLES:
        raise ValueError("Geçersiz rol.")
    secret = settings.clerk_secret_key.strip()
    if not secret:
        raise RuntimeError("Clerk secret yapılandırılmamış.")

    # Tek seferlik: zaten bir rol (selectable ya da admin) varsa dokunma.
    existing = _fetch_role(tenant_id)
    if existing:
        with _lock:
            _cache[tenant_id] = (time.time(), existing)
        return existing

    try:
        r = requests.patch(
            f"{_CLERK_API}/users/{tenant_id}/metadata",
            headers={
                "Authorization": f"Bearer {secret}",
                "Content-Type": "application/json",
            },
            json={"public_metadata": {"role": role}},
            timeout=6,
        )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Clerk rol yazılamadı: {exc}") from exc
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Clerk rol yazma başarısız (HTTP {r.status_code}).")

    with _lock:
        _cache[tenant_id] = (time.time(), role)
    return role


def enforce_role(tenant_id: str | None, allowed: set[str]) -> None:
    """Rol `allowed` içinde değilse HTTP 403. Rol belirlenemezse fail-open (bloklamaz).

    fail-open: clerk_secret_key kapalıyken / geçiş döneminde mevcut davranışı korur;
    secret set edilince gerçek enforcement başlar. Admin genelde tüm allowed setlerine
    çağıran tarafından dahil edilir.
    """
    role = get_user_role(tenant_id)
    if role is None:
        return  # belirlenemedi → bloklama (kademeli açılış / dayanıklılık)
    if role not in allowed:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=403,
            detail="Bu işlem için yetkin yok.",
        )


def _clear_cache() -> None:
    """Test yardımcısı — rol cache'ini temizler."""
    with _lock:
        _cache.clear()
