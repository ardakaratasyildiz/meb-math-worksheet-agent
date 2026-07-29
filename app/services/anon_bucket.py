"""Anonim çeşitlilik kovası — anonim isteklere IP-türevli history kimliği.

NEDEN (2026-07-29 ölçümü, docs/COST_QUALITY_V2_PLAN.md dışı ek bulgu):
`GeminiAgent.generate()` history anahtarını `tenant_id or DEFAULT_TENANT` ile
kuruyordu; `DEFAULT_TENANT = "__shared__"` olduğu için **bütün anonim üretimler
tek kovayı** paylaşıyordu. Teslim edilen her soru o kovaya "görülmüş" yazılıyor,
`GenerationCache.get()` ise bir cached set'te TEK BİR görülmüş soru bulunca seti
tamamen atlıyor (`has_overlap` → continue). Sonuç: anonim trafikte cache
YAZILIYOR ama bir daha okunamıyor. Canlı defterde 97 üretimde 3 cache isabeti
(%3) bu yüzden. `history_seen_unbounded=True` (2026-07-28) durumu kalıcılaştırdı.

Bu modül iki amacı birbirinden ayırır:
    - "aynı ziyaretçiye aynı soruyu vermeme"  → ziyaretçi-bazlı kova (burada)
    - "üretilmiş seti başka ziyaretçiye verme" → cache'in asıl işi (artık mümkün)

IP KAYNAĞI: `request.client.host` Render proxy'si arkasında GERÇEK istemciyi
vermez (uvicorn `--proxy-headers` bayrağı yok, `forwarded_allow_ips` varsayılanı
`127.0.0.1` ve Render'ın iç proxy'si o değil) → `X-Forwarded-For`'un İLK girdisi
kullanılır; `app/routers/admin.py::get_admin_actor` da aynı nedenle böyle yapar.

SPOOF: XFF istemci tarafından uydurulabilir. Burada güvenlik etkisi YOKTUR —
kova yalnız hangi soru çeşitliliği penceresine düşüleceğini belirler; yetki,
kota ve maliyet kaydı `tenant_id`'den gelir (bu modül onlara DOKUNMAZ). Uydurma
XFF'in tek etkisi "boş kova" = daha ÇOK cache isabeti = daha AZ maliyet, yani
kötüye kullanım güdüsü ters yönde. (Rate limit için aynı şey geçerli DEĞİL;
oradaki kimlik bilinçli olarak `app/security.py`'de ayrı tutulur.)

KABUL EDİLEN ÖDÜNLER (bilinçli):
    - İki FARKLI anonim ziyaretçi artık aynı soruları görebilir. Bu bir gerileme
      değil, cache'in tanımı; "aynı KİŞİ aynı soruyu görmesin" garantisi ziyaretçi
      kovası içinde korunur (bkz. tests/test_anon_variation_bucket.py).
    - IP değişimi (mobil şebeke, NAT) kovayı sıfırlar → ziyaretçi daha önce
      gördüğü bir seti tekrar alabilir. Giriş yapan kullanıcıda bu risk yok
      (tenant_id önceliklidir).
    - Ortak IP (okul/kurum NAT'ı) tek kova paylaşır → aynı ağdaki iki kişi
      birbirinden farklı soru alır. Sınıf içinde istenen davranış zaten bu.

KVKK: ham IP hiçbir yere yazılmaz — yalnız HMAC-SHA256'nın ilk 12 hex'i kovada
görünür ve o da tuzsuz geri çevrilemez.
"""
from __future__ import annotations

import hmac
from hashlib import sha256

from app.config import settings

# Tuz verilmediğinde kullanılan sabit. Rastgele/proses-başına DEĞİL: örnekler
# arasında ve restart sonrası AYNI kalmalı, yoksa kovalar durmadan sıfırlanır.
_DEFAULT_SALT = "soruatolyesi/anon-variation/v1"

PREFIX = "anon:"


def client_ip(request) -> str | None:
    """Gerçek istemci IP'si — XFF'in ilk girdisi, yoksa soket adresi.

    XFF zinciri `client, proxy1, proxy2` sırasındadır → ilk girdi istemci.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        first = forwarded.split(",")[0].strip()
        if first:
            return first
    client = getattr(request, "client", None)
    return getattr(client, "host", None) or None


def anon_variation_key(request) -> str | None:
    """Anonim istek için history kovası kimliği (`anon:<12 hex>`) ya da None.

    None döner: bayrak kapalı VEYA IP hiç çıkarılamadı → çağıran taraf
    `DEFAULT_TENANT`'a düşer (eski davranış). Giriş yapmış kullanıcıda bu
    fonksiyon çağrılsa bile `tenant_id` öncelikli olduğu için etkisi yoktur.
    """
    if not settings.anon_variation_bucket:
        return None
    ip = client_ip(request)
    if not ip:
        return None
    salt = (settings.anon_variation_salt or "").strip() or _DEFAULT_SALT
    digest = hmac.new(salt.encode("utf-8"), ip.encode("utf-8"), sha256).hexdigest()
    return f"{PREFIX}{digest[:12]}"
