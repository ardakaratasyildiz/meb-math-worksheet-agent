import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.routers import (
    admin,
    assignments,
    billing,
    classrooms,
    curriculum,
    health,
    me,
    quizzes,
    render,
    shared,
    worksheets,
)
from app.security import limiter

logger = logging.getLogger(__name__)


def _init_sentry() -> None:
    """SENTRY_DSN ayarlıysa Sentry SDK'yı başlat. DSN yoksa sessiz geç."""
    if not settings.sentry_dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.sentry_environment,
            release=settings.sentry_release,
            traces_sample_rate=settings.sentry_traces_sample_rate,
            integrations=[StarletteIntegration(), FastApiIntegration()],
        )
        logger.info("Sentry initialized (env=%s)", settings.sentry_environment)
    except Exception as exc:
        # Sentry init başarısız olursa app yine ayağa kalksın.
        logger.warning("Sentry başlatılamadı: %s", exc)


_init_sentry()

app = FastAPI(
    title="MEB Matematik Çalışma Kağıdı Üretici",
    description="MEB müfredatına uygun (1-8. sınıf) matematik soruları üreten Gemini tabanlı mikroservis.",
    version="0.1.0",
)

# CORS — frontend domain'leri için izin (Vercel + lokal dev)
#
# GÜVENLİK: `allow_origins=["*"]` (CORS_ORIGINS boşken varsayılan) İLE
# `allow_credentials=True` BİRLİKTE kullanılamaz — Starlette bu kombinasyonda
# gelen Origin'i aynen yansıtır ve `Access-Control-Allow-Credentials: true` verir,
# yani HERHANGİ bir web sitesi kurbanın tarayıcısı üzerinden kimlik-doğrulamalı
# cross-origin istek atıp yanıtı okuyabilir. Auth burada tamamen header-tabanlı
# (Authorization: Bearer / X-API-Key), cookie DEĞİL → credentials'a gerek yok.
# Bu yüzden credentials yalnızca AÇIK (explicit, non-wildcard) bir origin listesi
# yapılandırıldığında etkinleşir; wildcard/boşta kapalıdır.
_cors_origins = settings.cors_origin_list
_allow_credentials = bool(_cors_origins) and "*" not in _cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc: RateLimitExceeded):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=429,
        content={
            "detail": f"Rate limit aşıldı: {exc.detail}",
        },
    )


app.include_router(curriculum.router, prefix="/api/curriculum", tags=["curriculum"])
app.include_router(worksheets.router, prefix="/api/worksheets", tags=["worksheets"])
app.include_router(quizzes.router, prefix="/api/quizzes", tags=["quizzes"])
app.include_router(shared.router, prefix="/api/shared", tags=["shared"])
app.include_router(classrooms.router, prefix="/api/classrooms", tags=["classrooms"])
app.include_router(assignments.router, prefix="/api/assignments", tags=["assignments"])
app.include_router(me.router, prefix="/api/me", tags=["me"])
app.include_router(billing.router, prefix="/api/billing", tags=["billing"])
app.include_router(render.router, prefix="/api/render", tags=["render"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(health.router, tags=["system"])


@app.api_route("/health", methods=["GET", "HEAD"], tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
