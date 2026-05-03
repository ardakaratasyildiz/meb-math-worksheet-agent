from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.routers import curriculum, worksheets
from app.security import limiter

app = FastAPI(
    title="MEB Matematik Çalışma Kağıdı Üretici",
    description="MEB müfredatına uygun (1-7. sınıf) matematik soruları üreten Gemini tabanlı mikroservis.",
    version="0.1.0",
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


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
