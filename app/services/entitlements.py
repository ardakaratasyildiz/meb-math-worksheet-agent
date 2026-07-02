"""Premium yetkilendirme (entitlement) seam.

Gerçek bir billing/abonelik sistemi henüz yok. Bu modül "premium kullanıcı"
kararını TEK bir yerde toplar; ileride Clerk publicMetadata / Stripe / iyzico
gibi bir kaynağa bağlamak yalnızca bu dosyayı değiştirmeyi gerektirsin.

ÖNEMLİ: Karar HER ZAMAN sunucu tarafında verilir. Çağıranlar client'tan gelen
bir bayrağa ASLA güvenmez — böylece ücretsiz kullanıcı istekle premium kaliteyi
(yeni nesil sorular) elde edemez.

Bugünkü kaynak (app/config.py):
  - settings.premium_all=True → herkes premium (dev/demo/A-B testi)
  - tenant_id, settings.premium_tenant_ids allowlist'inde → premium
"""
from __future__ import annotations

from app.config import settings


def is_premium(tenant_id: str | None) -> bool:
    """Verilen kullanıcı (Clerk userId = tenant_id) premium mi?

    Anonim / giriş yapmamış (tenant_id yok) → ücretsiz.
    """
    if settings.premium_all:
        return True
    if not tenant_id:
        return False
    return tenant_id in settings.premium_tenant_id_set


def wants_yeni_nesil(tenant_id: str | None) -> bool:
    """Bu kullanıcı için 'yeni nesil / senaryo' üretim modu açılsın mı?

    Özellik anahtarı (premium_yeni_nesil) AÇIK ve kullanıcı premium ise True.
    Kullanıcı bu kararı göremez/değiştiremez — gizli kalite kaldıracıdır.
    """
    return settings.premium_yeni_nesil and is_premium(tenant_id)
