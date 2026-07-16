"""Clerk oturum JWT'sini sunucu-tarafı doğrulama (P0 — billing ön koşulu).

Bugün backend, istekteki `tenant_id`'ye (Clerk userId) DOĞRULAMADAN güveniyor
(bkz. app/routers/*). Premium/abonelik `tenant_id`'ye bağlandığı an, kullanıcı bu
değeri değiştirip bedava premium olabilir — ödeme geldiğinde kabul edilemez
(docs/IYZICO_ENTEGRASYON_PLANI.md §1 P0).

Bu modül tek işi yapar: frontend'in `Authorization: Bearer <Clerk session token>`
olarak gönderdiği token'ın imzasını Clerk JWKS'i ile doğrular ve `sub` claim'inden
DOĞRULANMIŞ tenant_id üretir. Kart/PII veya sır burada tutulmaz.

Kademeli açılış (additive, kırmadan):
  1. settings.clerk_issuer BOŞ → doğrulama devre dışı; dependency'ler None döner ve
     çağıran mevcut (client-supplied) davranışa düşer. Bugünkü prod aynen çalışır.
  2. clerk_issuer set + frontend token gönderir → doğrulama devreye girer; entitlement
     veren uçlar `resolve_tenant_id()` ile doğrulanmış kimliği tercih eder.

Kullanım (FastAPI):
    from app.services.clerk_auth import verified_tenant_id, resolve_tenant_id

    @router.get("/progress")
    def progress(tenant_id: str, verified: str | None = Depends(verified_tenant_id)):
        tid = resolve_tenant_id(verified, tenant_id)
        if tid is None:
            raise HTTPException(401, "Kimlik doğrulanamadı.")
        ...

Yeni (billing gibi) uçlar doğrudan strict `require_verified_tenant_id` kullanabilir.
"""
from __future__ import annotations

import logging
import threading

import jwt
from fastapi import Depends, Header, HTTPException

from app.config import settings

logger = logging.getLogger(__name__)

# JWKS istemcisi modül-seviyesinde tekil; url değişirse (config reload) yeniden kurulur.
# PyJWKClient kendi içinde kid→signing key cache tutar ve bilinmeyen kid görünce
# (anahtar rotasyonu) otomatik yeniden çeker.
_jwks_client: "jwt.PyJWKClient | None" = None
_jwks_client_url: str = ""
_lock = threading.Lock()


def _get_jwks_client() -> "jwt.PyJWKClient | None":
    """Yapılandırılmış JWKS URL'i için (cache'li) PyJWKClient döner; yoksa None."""
    global _jwks_client, _jwks_client_url
    url = settings.clerk_jwks_url_resolved
    if not url:
        return None
    with _lock:
        if _jwks_client is None or _jwks_client_url != url:
            try:
                # lifespan/cache_keys parametreleri PyJWT sürümüne göre değişebilir.
                _jwks_client = jwt.PyJWKClient(
                    url, cache_keys=True, lifespan=settings.clerk_jwks_cache_ttl
                )
            except TypeError:  # eski PyJWT — sade kurulum
                _jwks_client = jwt.PyJWKClient(url)
            _jwks_client_url = url
        return _jwks_client


def _extract_bearer(authorization: str | None) -> str | None:
    """`Authorization: Bearer <token>` başlığından token'ı ayıklar (yoksa None)."""
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer" and parts[1].strip():
        return parts[1].strip()
    return None


def verify_token(token: str) -> dict:
    """Token imzasını + exp/iss'i doğrular; claim sözlüğü döner.

    Doğrulama kapalıysa (issuer yok) RuntimeError; geçersiz token'da
    jwt.InvalidTokenError (ve alt sınıfları) fırlatır. Çağıran yakalamalı.
    """
    client = _get_jwks_client()
    if client is None:
        raise RuntimeError("Clerk auth yapılandırılmamış (clerk_issuer boş).")
    signing_key = client.get_signing_key_from_jwt(token)
    issuer = settings.clerk_issuer.strip().rstrip("/") or None
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        issuer=issuer,
        # Clerk oturum token'ında audience yok → aud doğrulamasını kapat.
        # `sub` (userId), `exp` ve `iss` zorunlu.
        options={"require": ["exp", "sub", "iss"], "verify_aud": False},
        leeway=30,  # saat kaymasına küçük tolerans
    )


def _verified_sub_or_none(authorization: str | None) -> str | None:
    """Ortak çekirdek: geçerli token'dan doğrulanmış `sub`, aksi halde None.

    Doğrulama kapalıyken veya token yok/geçersizken None döner (fırlatmaz) —
    strict/lenient dependency'ler bu değeri kendi politikasına göre yorumlar.
    """
    if not settings.clerk_auth_enabled:
        return None
    token = _extract_bearer(authorization)
    if not token:
        return None
    try:
        claims = verify_token(token)
    except Exception as exc:  # noqa: BLE001 — geçersiz/expired/ağ; sessiz reddet
        logger.info("Clerk token doğrulanamadı: %s", exc)
        return None
    sub = claims.get("sub")
    return sub if isinstance(sub, str) and sub else None


# --- FastAPI dependency'leri --------------------------------------------------

def verified_tenant_id(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> str | None:
    """Lenient: geçerli Clerk token'dan doğrulanmış tenant_id, yoksa None.

    Fırlatmaz. Mevcut uçlara additive eklemek için: sonucu `resolve_tenant_id()`
    ile client-supplied tenant'a karşı değerlendir.
    """
    return _verified_sub_or_none(authorization)


def require_verified_tenant_id(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> str:
    """Strict: doğrulanmış tenant_id şarttır; aksi halde 401 (auth kapalıysa 503).

    Yeni (billing gibi) uçlar için — client-supplied tenant'a hiç bakmaz.
    """
    if not settings.clerk_auth_enabled:
        raise HTTPException(
            status_code=503,
            detail="Kimlik doğrulama yapılandırılmamış (Clerk).",
        )
    tid = _verified_sub_or_none(authorization)
    if not tid:
        raise HTTPException(
            status_code=401,
            detail="Geçerli oturum gerekli (Authorization: Bearer <token>).",
        )
    return tid


def resolve_tenant_id(verified: str | None, supplied: str | None) -> str | None:
    """Güvenli tenant seçimi (spoof koruması).

    - Doğrulanmış kimlik varsa DAİMA onu kullan (client ne gönderirse göndersin).
    - Doğrulama AÇIK ama doğrulanmış kimlik yoksa → supplied'a GÜVENME (None döner;
      çağıran 401 vermeli). Spoof'u burada keser.
    - Doğrulama KAPALIYKEN (geçiş dönemi/dev) → supplied'a düş (bugünkü davranış).
    """
    if verified:
        return verified
    if settings.clerk_auth_enabled:
        return None
    return supplied


__all__ = [
    "verified_tenant_id",
    "require_verified_tenant_id",
    "resolve_tenant_id",
    "verify_token",
]
