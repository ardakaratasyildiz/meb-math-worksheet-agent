"""API key auth + rate limit yardımcıları.

Auth devre dışı (api_keys boş) → tüm istekler "anonymous" olarak limit'lenir.
Auth açık → Geçerli X-API-Key header gerekir; rate limit key bazlı.
"""
from __future__ import annotations

from fastapi import Header, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings


def _identifier(request: Request) -> str:
    """Rate-limit anahtarı: API key varsa onu, yoksa IP'yi kullan."""
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"key:{api_key}"
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
