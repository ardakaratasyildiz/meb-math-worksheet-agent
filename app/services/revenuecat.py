"""RevenueCat webhook → abonelik senkronu (mobil IAP yolu).

Mobil uygulama IAP satın alımını RevenueCat üzerinden yapar. RevenueCat abonelik
yaşam döngüsü olaylarını (satın alma/yenileme/iptal/süre dolumu/ödeme sorunu) bize
webhook ile bildirir. Bu modül olayı `billing_store.subscriptions` satırına eşler —
iyzico ile ORTAK depo; `entitlements` yalnız oraya bakar (provider-agnostik).

Sözleşme:
  - app_user_id = Clerk userId (mobil, RevenueCat appUserID'yi böyle set eder) = tenant_id.
    Anonim ("$RCAnonymousID:...") → henüz kimliğe bağlı değil, atlanır.
  - İki AYRI yol: abonelik olayları `subscriptions` satırına yazılır; ek paket (top-up,
    consumable) satırına HİÇ dokunmaz, `top_up_store` kredisine gider. Ürün kimliği
    `settings.topup_product_credits` içindeyse ek paket sayılır.
  - Idempotency: event.id → billing_store.record_event (tekrar gelen atlanır; RevenueCat
    retry güvenliği).
  - Karar HER ZAMAN sunucuda; client bayrağına asla güvenilmez.

Referans: https://www.revenuecat.com/docs/integrations/webhooks/event-types-and-fields
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.config import settings
from app.services.entitlements import credit_topup
from app.services.billing_store import (
    BILLING_STORE,
    STATUS_ACTIVE,
    STATUS_CANCELED,
    STATUS_EXPIRED,
    STATUS_PAST_DUE,
    STATUS_TRIALING,
)

logger = logging.getLogger(__name__)

PROVIDER = "revenuecat"

# Abonelik durumuna EŞLENEN olaylar (period_type=TRIAL ise active yerine trialing).
_ACTIVATING = {
    "INITIAL_PURCHASE",
    "RENEWAL",
    "UNCANCELLATION",
    "PRODUCT_CHANGE",
    "NON_RENEWING_PURCHASE",
}
# Sessizce yok sayılan (abonelik durumunu değiştirmeyen) olaylar.
_IGNORED = {"TEST", "SUBSCRIBER_ALIAS", "TRANSFER"}


def _ms_to_iso(ms: object) -> str | None:
    """RevenueCat epoch-ms → ISO-8601 UTC. Geçersiz/None → None."""
    try:
        if ms is None:
            return None
        return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).isoformat()
    except (ValueError, TypeError, OverflowError, OSError):
        return None


def plan_for(event: dict) -> str:
    """Olaydan plan_code çıkar: config eşlemesi > 'plus' sezgisi > 'pro' fallback."""
    product_id = str(event.get("product_id") or "")
    ents = event.get("entitlement_ids") or []
    pmap = settings.revenuecat_product_dict
    if product_id in pmap:
        return pmap[product_id]
    text = (product_id + " " + " ".join(str(e) for e in ents)).lower()
    return "pro-plus" if "plus" in text else "pro"


def _status_for(event_type: str, is_trial: bool) -> str | None:
    """Olay türü → abonelik durumu. Eşlenmemiş tür → None (yok say)."""
    if event_type == "EXPIRATION":
        return STATUS_EXPIRED
    if event_type == "BILLING_ISSUE":
        return STATUS_PAST_DUE
    if event_type == "SUBSCRIPTION_PAUSED":
        return STATUS_CANCELED  # duraklatma → erişim yok (entitling değil)
    if event_type == "CANCELLATION":
        # Otomatik yenileme kapatıldı; period_end'e kadar erişim SÜRER (cancel flag ile).
        return STATUS_ACTIVE
    if event_type in _ACTIVATING:
        return STATUS_TRIALING if is_trial else STATUS_ACTIVE
    return None


def process_webhook(body: dict) -> dict:
    """RevenueCat webhook gövdesini işler → abonelik satırını günceller.

    Dönen: {"status": ...} — "ok" | "duplicate" | "ignored" | "skipped".
    Her zaman 2xx döndürülür (webhook'u başarılı say); iş kararı gövdede.
    """
    event = (body or {}).get("event") or {}
    event_id = event.get("id")
    event_type = str(event.get("type") or "").upper()
    app_user_id = event.get("app_user_id")

    if not event_id or not event_type:
        logger.warning("RevenueCat webhook: event.id/type eksik → atlandı")
        return {"status": "skipped", "reason": "missing_id_or_type"}

    if not app_user_id or str(app_user_id).startswith("$RCAnonymousID"):
        # Kimliğe bağlanmamış anonim satın alma → tenant yok, senkronlanamaz.
        logger.info("RevenueCat webhook: anonim/bağlanmamış app_user_id → atlandı (%s)", event_type)
        return {"status": "skipped", "reason": "anonymous_user"}

    tenant_id = str(app_user_id)

    # Idempotency: aynı event tekrar gelirse no-op (RevenueCat retry güvenliği).
    is_new = BILLING_STORE.record_event(
        event_id=str(event_id), event_type=event_type, payload=body, tenant_id=tenant_id
    )
    if not is_new:
        return {"status": "duplicate", "event_id": str(event_id)}

    if event_type in _IGNORED:
        BILLING_STORE.mark_event_processed(str(event_id))
        return {"status": "ignored", "event_type": event_type}

    # ── Ek paket (top-up / consumable) — ABONELİK DEĞİL, kredi ────────────────
    # Ürün kimliği topup listesindeyse olay türüne bakmadan buraya düşer. Aksi halde
    # NON_RENEWING_PURCHASE `_ACTIVATING`'e girip abonelik satırının ÜZERİNE yazıyordu:
    # tüketilebilir üründe bitiş tarihi olmadığı için satır erişim vermez hale geliyor,
    # yani ek paket alan Pro abonesi hem kredisini alamıyor hem aboneliğini kaybediyordu.
    # (Ek paket zaten yalnız aktif aboneye satılıyor → senaryo istisna değil, kural.)
    product_id = str(event.get("product_id") or "")
    if product_id in settings.topup_product_credits:
        credited = credit_topup(
            tenant_id,
            product_id,
            provider_ref=str(event.get("transaction_id") or event.get("id") or ""),
        )
        BILLING_STORE.mark_event_processed(str(event_id))
        logger.info(
            "RevenueCat top-up: tenant=%s ürün=%s → +%s kağıt", tenant_id, product_id, credited
        )
        return {"status": "ok", "tenant_id": tenant_id, "topup_product": product_id,
                "credited": credited}

    is_trial = str(event.get("period_type") or "").upper() == "TRIAL"
    status = _status_for(event_type, is_trial)
    if status is None:
        logger.info("RevenueCat webhook: eşlenmemiş tür '%s' → yok sayıldı", event_type)
        BILLING_STORE.mark_event_processed(str(event_id))
        return {"status": "ignored", "event_type": event_type}

    plan_code = plan_for(event)
    period_end = _ms_to_iso(event.get("expiration_at_ms"))

    BILLING_STORE.upsert(
        tenant_id=tenant_id,
        plan_code=plan_code,
        status=status,
        provider=PROVIDER,
        provider_ref=str(event.get("original_transaction_id") or event.get("product_id") or ""),
        customer_ref=tenant_id,
        trial_end=period_end if is_trial else None,
        current_period_end=period_end,
        cancel_at_period_end=(event_type == "CANCELLATION"),
    )
    BILLING_STORE.mark_event_processed(str(event_id))
    logger.info(
        "RevenueCat senkron: tenant=%s type=%s → plan=%s status=%s",
        tenant_id, event_type, plan_code, status,
    )
    return {
        "status": "ok",
        "tenant_id": tenant_id,
        "plan": plan_code,
        "subscription_status": status,
    }
