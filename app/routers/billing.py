"""Billing webhook uçları — sağlayıcıdan (RevenueCat) gelen abonelik olayları.

RevenueCat webhook'u X-API-Key GÖNDERMEZ; kendi paylaşımlı-sır Authorization
header'ıyla doğrulanır (settings.revenuecat_webhook_auth). Bu yüzden require_api_key
DEĞİL, buradaki özel doğrulama kullanılır.
"""
from __future__ import annotations

import hmac
import logging

from fastapi import APIRouter, Header, HTTPException, Request

from app.config import settings
from app.services import revenuecat

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/revenuecat/webhook")
async def revenuecat_webhook(
    request: Request,
    authorization: str | None = Header(default=None),
) -> dict:
    """RevenueCat abonelik olayı alır → billing_store senkronu (idempotent).

    Auth: settings.revenuecat_webhook_auth SET ise Authorization birebir eşleşmeli
    (aksi 401). BOŞ ise doğrulama atlanır + uyarı (yalnız sandbox/dev olmalı).
    """
    expected = settings.revenuecat_webhook_auth
    if expected:
        if not authorization or not hmac.compare_digest(authorization, expected):
            raise HTTPException(status_code=401, detail="unauthorized")
    else:
        logger.warning(
            "RevenueCat webhook auth sırrı ayarlı DEĞİL — doğrulama atlandı "
            "(yalnız sandbox/dev; prod'da REVENUECAT_WEBHOOK_AUTH set et)."
        )

    try:
        body = await request.json()
    except Exception as exc:  # noqa: BLE001 — gövde JSON değil
        raise HTTPException(status_code=400, detail="invalid json") from exc

    return revenuecat.process_webhook(body if isinstance(body, dict) else {})
