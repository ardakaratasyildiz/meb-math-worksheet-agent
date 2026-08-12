"""Premium yetkilendirme (entitlement) + kota — TEK karar noktası.

Abonelik durumunun kaynak-of-truth'u `billing_store.subscriptions` satırıdır
(webhook/callback ile senkronlanır). Bu modül o satırdan **plan** ve **kota**
kararını verir. Karar HER ZAMAN sunucu tarafında; çağıranlar client'tan gelen bir
bayrağa/tenant'a ASLA güvenmez (bkz. clerk_auth doğrulaması).

Model (MONETIZATION_PLAN §2, 2026-07-24 — kağıt-bazlı + AİLE PAYLAŞIMLI havuz):
  free (10 kağıt/ay, günde en çok 2) · trial (7g kartsız, 20 kağıt, Pro+ kalitesi) ·
  pro (50 kağıt/ay) · pro-plus (120 kağıt/ay).
  Kota birimi = ÇALIŞMA KAĞIDI (soru değil); açık sayı (gizli tavan yok). Çocuk, PREMIUM
  velisinin planını miras alır ve aile TEK kota havuzunu paylaşır (_billing_owner/_family_tenants).

Kademeli açılış:
  - settings.premium_all=True → herkes pro-plus (dev/demo/dark-launch; BUGÜNKÜ prod).
  - billing canlı olunca premium_all=False → gerçek abonelik/kota farkı devreye girer.
  - Kota enforcement (402) generate uçlarında + settings.billing_enabled arkasında (ayrı PR).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.config import settings
from app.services.billing_store import BILLING_STORE, STATUS_TRIALING
from app.services.parent_link_store import PARENT_LINK_STORE
from app.services.top_up_store import TOP_UP_STORE
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


def _day_start_ts() -> float:
    """İçinde bulunulan günün başı (Türkiye saati) → unix saniye. Günlük tavan için."""
    now = datetime.now(_IST)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start.timestamp()


def _own_active_plan(tenant_id: str) -> str | None:
    """Tenant'ın KENDİ (miras değil) aktif planı: pro | pro-plus | trial; yoksa None.
    premium_all/allowlist dev override'ları pro-plus sayar."""
    if settings.premium_all:  # dev/demo/dark-launch — bugünkü prod davranışı
        return PLAN_PRO_PLUS
    sub = BILLING_STORE.get_active(tenant_id)  # yalnız erişim VEREN satır (period kontrollü)
    if sub:
        return PLAN_TRIAL if sub["status"] == STATUS_TRIALING else sub["plan_code"]
    if tenant_id in settings.premium_tenant_id_set:  # allowlist (dev)
        return PLAN_PRO_PLUS
    return None


def _billing_owner(tenant_id: str) -> tuple[str, str]:
    """(sahip_tenant, plan) — kota/entitlement havuzunun SAHİBİ + planı.

    Tenant kendi aboneliğine sahipse o; değilse PREMIUM bir velisi varsa o veli (AİLE
    MİRASI — çocuk velinin planını alır); hiçbiri yoksa (tenant, free). Aile PAYLAŞIMLI
    kota havuzunun sahibini belirler → check_quota bu sahibin ailesini tek havuz sayar.
    """
    own = _own_active_plan(tenant_id) if tenant_id else None
    if own:
        return tenant_id, own
    for parent in PARENT_LINK_STORE.parents_of(tenant_id or ""):
        p_plan = _own_active_plan(parent)
        if p_plan:
            return parent, p_plan  # miras: premium velinin planı + havuzu
    return tenant_id or "", PLAN_FREE


def _family_tenants(owner_tenant: str) -> list[str]:
    """Paylaşımlı havuzu paylaşan tenant'lar: sahip (veli/kendisi) + bağlı çocuklar."""
    if not owner_tenant:
        return []
    kids = [c["student_id"] for c in PARENT_LINK_STORE.list_children(owner_tenant)]
    return [owner_tenant, *kids]


def plan_of(tenant_id: str | None) -> str:
    """Kullanıcının EFEKTİF planı (AİLE MİRASI dahil): free | trial | pro | pro-plus.

    Anonim (tenant yok) → free. Çocuk, PREMIUM velisinin planını miras alır (paylaşımlı
    kota). premium_all/allowlist dev override'ları pro-plus sayar.
    """
    if not tenant_id:
        return PLAN_FREE
    return _billing_owner(tenant_id)[1]


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
    if tenant_id in settings.premium_tenant_id_set:
        return True
    # Aile mirası: PREMIUM velisi olan çocuk da model-premium (havuz paylaşımlı → bağlı).
    for parent in PARENT_LINK_STORE.parents_of(tenant_id):
        if BILLING_STORE.get_active(parent) is not None or parent in settings.premium_tenant_id_set:
            return True
    return False


def wants_yeni_nesil(tenant_id: str | None) -> bool:
    """'Yeni nesil / senaryo' üretim modu açılsın mı? (gizli kalite kaldıracı.)

    Özellik anahtarı AÇIK ve kullanıcı premium (pro/pro-plus/trial) ise True.
    Kullanıcı bu kararı göremez/değiştiremez.
    """
    return settings.premium_yeni_nesil and is_premium(tenant_id)


def yeni_nesil_for_bucket(tenant_id: str | None, difficulty) -> bool:
    """Bir üretim bucket'ı (zorluk) için yeni_nesil açık mı — teaser mantığı.

    Premium (wants_yeni_nesil) → full: HER bucket yeni_nesil. Ücretsiz → TEASER:
    yalnız `free_yeni_nesil_bucket` zorluğundaki bucket. Böylece ücretsiz kullanıcı
    her kağıtta bir tadımlık yeni_nesil görür, soru-başına bölme/ekstra çağrı olmadan
    (mevcut zorluk bucket'ına biner). Dark-launch'ta premium_all herkesi premium
    yaptığı için teaser dormant; premium_all=False olunca ücretsizde devreye girer.
    difficulty: Difficulty enum ya da str ("kolay"/"orta"/"zor").
    """
    if wants_yeni_nesil(tenant_id):
        return True
    if not settings.free_yeni_nesil_enabled:
        return False
    dv = getattr(difficulty, "value", difficulty)
    return dv == settings.free_yeni_nesil_bucket


def quota_limit(plan: str) -> int:
    """Plana göre aylık ÇALIŞMA KAĞIDI kotası (açık sayı; MONETIZATION_PLAN §2).

    trial = Pro+ KALİTESİ (yeni_nesil vb. wants_yeni_nesil'den gelir) ama KENDİ adedi
    (`trial_worksheets`) — Pro+ tavanı verilirse deneme, ödeyen müşteriden pahalıya gelir.
    """
    if plan == PLAN_FREE:
        return settings.free_monthly_worksheets
    if plan == PLAN_TRIAL:
        return settings.trial_worksheets
    if plan == PLAN_PRO:
        return settings.pro_monthly_worksheets
    return settings.pro_plus_monthly_worksheets


def daily_limit(plan: str) -> int | None:
    """Plana göre GÜNLÜK kağıt tavanı; tavansız planlarda None.

    Yalnız ücretsiz kademede var (KARAR 2026-08-12): aylık hak ilk günlerde tükenmesin
    + ücretsiz trafiğin günlük maliyeti öngörülebilir olsun. Deneme/ücretli planlarda
    tavan YOK — denemede 7 gün × 2 = 14 < 20 olur, kullanıcı hakkını kullanamazdı.
    """
    if plan != PLAN_FREE:
        return None
    return settings.free_daily_worksheets or None


def ensure_trial(tenant_id: str | None) -> None:
    """Doğrulanmış kullanıcının İLK üretiminde 7g kartsız reverse trial başlatır.

    Zaten bir abonelik satırı varsa (trial kullanılmış / aktif abone) DOKUNMAZ.
    iyzico çağrısı YOK — trial tamamen bizde tutulur (MONETIZATION_PLAN §2).
    """
    if not tenant_id:
        return
    if BILLING_STORE.get(tenant_id) is None:
        BILLING_STORE.start_trial(tenant_id)


def credit_topup(tenant_id: str | None, product_id: str, *, provider_ref: str | None = None) -> int:
    """RevenueCat consumable satın alımı → ek kağıt kredisi ekle (webhook girişi).

    product_id `settings.topup_product_credits` ile kağıt sayısına eşlenir. Kredi HAVUZ
    SAHİBİNE (ödeyen) eklenir → aile paylaşır. provider_ref = işlem id (idempotency).
    Eklenen kağıt sayısını döner (bilinmeyen ürün / eklenemezse 0).
    """
    if not tenant_id or not product_id:
        return 0
    credits = settings.topup_product_credits.get(product_id, 0)
    if credits <= 0:
        return 0
    owner, _ = _billing_owner(tenant_id)
    ok = TOP_UP_STORE.add(owner or tenant_id, credits, provider_ref=provider_ref)
    return credits if ok else 0


def enforce_quota(tenant_id: str | None, requested: int = 1) -> None:
    """Generate uçları için kota kapısı. Aşımda HTTP 402 + paywall sinyali fırlatır.

    - `settings.billing_enabled` KAPALIYKEN no-op (bugünkü davranış; kademeli açılış).
    - Yalnız DOĞRULANMIŞ tenant'a uygulanır → anonim (tenant None) kotasız kalır
      (SEO motoru bozulmasın). Client-supplied tenant'a GÜVENİLMEZ (bkz. clerk_auth).
    - İlk üretimde reverse trial'ı otomatik başlatır (ensure_trial).
    """
    if not settings.billing_enabled or not tenant_id:
        return
    # Trial YALNIZ solo + kapsamsız kullanıcıya: aile mirası varsa (premium veli) çocuğa
    # KENDİ trial'ını açma — yoksa havuz parent yerine çocuğun trial'ına kayardı.
    owner, plan = _billing_owner(tenant_id)
    if plan == PLAN_FREE and owner == tenant_id:
        ensure_trial(tenant_id)
    q = check_quota(tenant_id, requested=requested)
    if not q["allowed"]:
        from fastapi import HTTPException  # local import — entitlements'ı saf tut

        daily_block = q.get("block_reason") == "daily"
        if daily_block:
            d = q.get("daily_limit") or 0
            message = (
                f"Bugünlük ücretsiz hakkın doldu (günde {d} kağıt). Yarın yenilenir — "
                "beklemeden devam etmek istersen Pro'ya geçebilirsin."
            )
        else:
            message = "Bu ayki çalışma kağıdı hakkın doldu. Pro'ya geç ya da ek paket al."

        raise HTTPException(
            status_code=402,
            detail={
                # İki ayrı durum: günlük tavan GEÇİCİ (yarın açılır), aylık kota kalıcı.
                # İstemci buna göre farklı mesaj/CTA gösterir — günlük engelde "Pro'ya geç"
                # tek başına yanlış olur (kullanıcı yarın zaten devam edecek).
                "error": "daily_limit_reached" if daily_block else "quota_exceeded",
                "message": message,
                "plan": q["plan"],
                "limit": q["limit"],
                "used": q["used"],
                "daily_limit": q.get("daily_limit"),
                "daily_remaining": q.get("daily_remaining"),
                "topup_balance": q.get("topup_balance", 0),
            },
        )
    # Plan kotası bittiyse bu üretim EK PAKETTEN karşılanır → 1 kredi düş (havuz sahibinde,
    # en erken biten önce). Plan içindeyse dokunma (kullanım usage_ledger'dan sayılır).
    if q.get("plan_remaining", 1) <= 0 and q.get("topup_balance", 0) > 0:
        TOP_UP_STORE.consume(q.get("owner") or tenant_id, requested)


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
    owner, plan = _billing_owner(tenant_id)          # aile mirası → havuz sahibi + plan
    limit = quota_limit(plan)                        # kağıt/ay
    family = _family_tenants(owner)                  # veli + bağlı çocuklar = TEK havuz
    used = USAGE_LEDGER.worksheets_used_since(family, _month_start_ts())  # kağıt, cache-hit hariç
    plan_remaining = max(0, limit - used)
    topup = TOP_UP_STORE.balance(owner)              # ek paket kredisi (havuz sahibinde, süreli)
    remaining = plan_remaining + topup

    # Günlük tavan (yalnız ücretsiz) — aylık hakla AYRI bir kapı; havuz aile geneli.
    d_limit = daily_limit(plan)
    used_today = (
        USAGE_LEDGER.worksheets_used_since(family, _day_start_ts()) if d_limit else 0
    )
    daily_remaining = max(0, d_limit - used_today) if d_limit else None

    need = max(requested, 1)
    monthly_ok = remaining >= need
    daily_ok = daily_remaining is None or daily_remaining >= need
    # Aylık bitmişse ONU söyle (yükseltme mesajı doğru olsun); yalnız aylık hak varken
    # günlük tavana takılıyorsa "yarın devam" mesajı gider.
    block_reason = None if (monthly_ok and daily_ok) else ("monthly" if not monthly_ok else "daily")

    return {
        "plan": plan,
        "limit": limit,
        "used": used,
        "plan_remaining": plan_remaining,
        "topup_balance": topup,
        "remaining": remaining,
        "daily_limit": d_limit,
        "used_today": used_today,
        "daily_remaining": daily_remaining,
        "owner": owner,
        "allowed": monthly_ok and daily_ok,
        "block_reason": block_reason,
    }
