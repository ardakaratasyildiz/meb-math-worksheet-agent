from fastapi import FastAPI

from app.routers import curriculum, worksheets

app = FastAPI(
    title="MEB Matematik Çalışma Kağıdı Üretici",
    description="MEB müfredatına uygun (1-7. sınıf) matematik soruları üreten Gemini tabanlı mikroservis.",
    version="0.1.0",
)

app.include_router(curriculum.router, prefix="/api/curriculum", tags=["curriculum"])
app.include_router(worksheets.router, prefix="/api/worksheets", tags=["worksheets"])


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
