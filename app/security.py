"""API key auth + rate limit yardımcıları.

Auth devre dışı (api_keys boş) → tüm istekler "anonymous" olarak limit'lenir.
Auth açık → Geçerli X-API-Key header gerekir; rate limit key bazlı.
"""
from __future__ import annotations

from fastapi import Header, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.services.clerk_auth import verified_sub_from_header


def _identifier(request: Request) -> str:
    """Rate-limit anahtarı: DOĞRULANMIŞ oturum varsa per-kullanıcı, yoksa per-IP.

    NOT: X-API-Key AUTH içindir ve prod'da tüm tarayıcı istekleri AYNI public
    key'i (NEXT_PUBLIC_API_KEY) gönderir → onunla key'lemek herkesi tek bucket'a
    koyar. Bu yüzden rate-limit kimliği auth'tan ayrıştırılmıştır.

    GÜVENLİK: Kimlik, doğrulanmış Clerk oturumundan (`Authorization: Bearer`)
    türetilir — spoof edilebilen `X-Tenant-Id` header'ından DEĞİL. Aksi halde
    saldırgan her istekte rastgele bir X-Tenant-Id göndererek her seferinde yeni
    bir bucket açar ve limiti tamamen aşar (LLM uçlarında maliyet-DoS). Doğrulanmış
    kimlik yoksa (anonim /generate veya Clerk kapalıyken) IP'ye düşülür.
    """
    verified = verified_sub_from_header(request.headers.get("Authorization"))
    if verified:
        return f"tenant:{verified}"
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(
    key_func=_identifier,
    default_limits=[],  # endpoint başına @limiter.limit(...) ile uygula
)


async def require_api_key(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> str:
    """API key auth dependency. Auth devre dışıyken anonymous geçer."""
    valid_keys = settings.api_key_list
    if not valid_keys:
        return "anonymous"
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="X-API-Key header'ı gerekli.",
        )
    if x_api_key not in valid_keys:
        raise HTTPException(
            status_code=401,
            detail="Geçersiz API key.",
        )
    return x_api_key


def rate_limit_string() -> str:
    """Settings'ten saatlik + dakikalık limiti string formatına çevirir."""
    return f"{settings.rate_limit_per_minute}/minute;{settings.rate_limit_per_hour}/hour"
