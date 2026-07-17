"""Premium yetkilendirme (entitlement) + kota — TEK karar noktası.

Abonelik durumunun kaynak-of-truth'u `billing_store.subscriptions` satırıdır
(webhook/callback ile senkronlanır). Bu modül o satırdan **plan** ve **kota**
kararını verir. Karar HER ZAMAN sunucu tarafında; çağıranlar client'tan gelen bir
bayrağa/tenant'a ASLA güvenmez (bkz. clerk_auth doğrulaması).

Model (MONETIZATION_PLAN §2, 2026-07-16):
  free (satırsız, 100 soru/ay) · trial (7g kartsız tam-Pro) · pro (1000 soru/ay) ·
  pro-plus (fair-use sınırsız — arka planda makul tavan).

Kademeli açılış:
  - settings.premium_all=True → herkes pro-plus (dev/demo/dark-launch; BUGÜNKÜ prod).
  - billing canlı olunca premium_all=False → gerçek abonelik/kota farkı devreye girer.
  - Kota enforcement (402) generate uçlarında + settings.billing_enabled arkasında (ayrı PR).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.config import settings
from app.services.billing_store import BILLING_STORE, STATUS_TRIALING
from app.services.usage_ledger import USAGE_LEDGER

_IST = timezone(timedelta(hours=3))  # Türkiye — aylık reset takvim ayına göre

PLAN_FREE = "free"
PLAN_TRIAL = "trial"
PLAN_PRO = "pro"
PLAN_PRO_PLUS = "pro-plus"


def _month_start_ts() -> float:
    """İçinde bulunulan takvim ayının başı (Türkiye saati) → unix saniye."""
    now = datetime.now(_IST)
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return start.timestamp()


def plan_of(tenant_id: str | None) -> str:
    """Kullanıcının EFEKTİF planı: free | trial | pro | pro-plus.

    Anonim (tenant yok) → free. premium_all/allowlist dev override'ları pro-plus sayar.
    """
    if not tenant_id:
        return PLAN_FREE
    if settings.premium_all:  # dev/demo/dark-launch — bugünkü prod davranışı
        return PLAN_PRO_PLUS
    sub = BILLING_STORE.get_active(tenant_id)  # yalnız erişim VEREN satır (period kontrollü)
    if sub:
        if sub["status"] == STATUS_TRIALING:
            return PLAN_TRIAL
        return sub["plan_code"]  # "pro" | "pro-plus"
    if tenant_id in settings.premium_tenant_id_set:  # allowlist (dev)
        return PLAN_PRO_PLUS
    return PLAN_FREE


def is_premium(tenant_id: str | None) -> bool:
    """Kullanıcı ücretli/deneme erişimine sahip mi? (plan free değilse premium)."""
    return plan_of(tenant_id) != PLAN_FREE


def is_premium_for_model(tenant_id: str | None) -> bool:
    """MODEL-tier kararı için premium — `premium_all` dark-launch bayrağını YOK SAYAR.

    is_premium() dark-launch'ta herkese True döner (premium_all) → pahalı 3.5 modeli
    ödeyen olmadan herkese verirdi. Model seçimi bunun yerine GERÇEK abonelik/trial'a
    (billing_store.get_active) veya dev allowlist'ine bakar. Ödeyen kullanıcı ~0 olduğu
    sürece herkes ucuz model alır (maliyet). Ödeme canlı olunca premium ayrımı otomatik
    devreye girer. Anonim → False.
    """
    if not tenant_id:
        return False
    if BILLING_STORE.get_active(tenant_id) is not None:
        return True
    return tenant_id in settings.premium_tenant_id_set


def wants_yeni_nesil(tenant_id: str | None) -> bool:
    """'Yeni nesil / senaryo' üretim modu açılsın mı? (gizli kalite kaldıracı.)

    Özellik anahtarı AÇIK ve kullanıcı premium (pro/pro-plus/trial) ise True.
    Kullanıcı bu kararı göremez/değiştiremez.
    """
    return settings.premium_yeni_nesil and is_premium(tenant_id)


def quota_limit(plan: str) -> int:
    """Plana göre aylık soru kotası. pro-plus/trial = fair-use tavanı ('sınırsız')."""
    if plan == PLAN_FREE:
        return settings.free_monthly_questions
    if plan == PLAN_PRO:
        return settings.pro_monthly_questions
    # pro-plus + trial → fair-use makul tavan
    return settings.pro_plus_fair_use_questions


def ensure_trial(tenant_id: str | None) -> None:
    """Doğrulanmış kullanıcının İLK üretiminde 7g kartsız reverse trial başlatır.

    Zaten bir abonelik satırı varsa (trial kullanılmış / aktif abone) DOKUNMAZ.
    iyzico çağrısı YOK — trial tamamen bizde tutulur (MONETIZATION_PLAN §2).
    """
    if not tenant_id:
        return
    if BILLING_STORE.get(tenant_id) is None:
        BILLING_STORE.start_trial(tenant_id)


def enforce_quota(tenant_id: str | None, requested: int = 1) -> None:
    """Generate uçları için kota kapısı. Aşımda HTTP 402 + paywall sinyali fırlatır.

    - `settings.billing_enabled` KAPALIYKEN no-op (bugünkü davranış; kademeli açılış).
    - Yalnız DOĞRULANMIŞ tenant'a uygulanır → anonim (tenant None) kotasız kalır
      (SEO motoru bozulmasın). Client-supplied tenant'a GÜVENİLMEZ (bkz. clerk_auth).
    - İlk üretimde reverse trial'ı otomatik başlatır (ensure_trial).
    """
    if not settings.billing_enabled or not tenant_id:
        return
    ensure_trial(tenant_id)
    q = check_quota(tenant_id, requested=requested)
    if not q["allowed"]:
        from fastapi import HTTPException  # local import — entitlements'ı saf tut

        raise HTTPException(
            status_code=402,
            detail={
                "error": "quota_exceeded",
                "message": "Aylık üretim hakkın doldu. Devam etmek için Pro'ya geçebilirsin.",
                "plan": q["plan"],
                "limit": q["limit"],
                "used": q["used"],
            },
        )


def check_quota(tenant_id: str | None, requested: int = 0) -> dict:
    """Aylık kota durumu. Enforcement değil — saf sorgu (çağıran 402 kararını verir).

    Anonim üretim kotasızdır (SEO motoru) → daima allowed. Cache-hit üretimler
    kotadan düşmez (usage_ledger.questions_used_since cache_hit=0 filtreler).

    Dönen: {plan, limit, used, remaining, allowed}
      allowed = kalan kota `requested` (en az 1) soruya yetiyor mu. requested=0 →
      'en az 1 slot var mı' (dolu değil mi); requested=N → N soru üretilebilir mi.
    """
    if not tenant_id:
        return {"plan": "anon", "limit": None, "used": 0, "remaining": None, "allowed": True}
    plan = plan_of(tenant_id)
    limit = quota_limit(plan)
    used = USAGE_LEDGER.questions_used_since(tenant_id, _month_start_ts())
    remaining = max(0, limit - used)
    return {
        "plan": plan,
        "limit": limit,
        "used": used,
        "remaining": remaining,
        "allowed": remaining >= max(requested, 1),
    }
