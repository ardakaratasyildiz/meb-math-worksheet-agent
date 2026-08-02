"""Clerk Backend API — kullanıcı hesabını SİLME (mağaza veri-silme zorunluluğu).

`clerk_roles.py`'deki Clerk Backend API çağrı deseniyle (`_CLERK_API`, `requests`,
timeout=6) aynı; sorumluluk ayrımı için ayrı modül — rol OKUMA/YAZMA'dan farklı,
GERİ DÖNDÜRÜLEMEZ bir işlem (hesap kapatma).
"""
from __future__ import annotations

import logging

import requests

from app.config import settings

logger = logging.getLogger(__name__)

_CLERK_API = "https://api.clerk.com/v1"


def delete_clerk_user(tenant_id: str) -> None:
    """Clerk kullanıcısını Backend API ile SİLER.

    Kullanıcı zaten yoksa (HTTP 404) başarı sayılır (idempotent — ikinci silme
    denemesi patlamamalı). `settings.clerk_secret_key` boşsa çağıran ÖNCE kontrol
    etmeli (bkz. app/routers/me.py — 503, hiçbir şey silinmeden); yine de burada
    da korunur (RuntimeError).

    Hata halinde RuntimeError fırlatır — çağıran (router) 502 döndürmeli: yerel
    veri zaten silindi ama Clerk hesabı kapatılamadı.
    """
    secret = settings.clerk_secret_key.strip()
    if not secret:
        raise RuntimeError("Clerk secret yapılandırılmamış.")
    try:
        r = requests.delete(
            f"{_CLERK_API}/users/{tenant_id}",
            headers={"Authorization": f"Bearer {secret}"},
            timeout=6,
        )
    except Exception as exc:  # noqa: BLE001 — ağ hatası da çağıranda 502'ye düşer
        raise RuntimeError(f"Clerk kullanıcı silme isteği başarısız: {exc}") from exc
    if r.status_code == 404:
        return  # kullanıcı zaten yok → başarı say (idempotent)
    if r.status_code not in (200, 202, 204):
        raise RuntimeError(f"Clerk kullanıcı silme başarısız (HTTP {r.status_code}).")


__all__ = ["delete_clerk_user"]
