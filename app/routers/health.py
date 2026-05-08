"""Liveness ve readiness endpoint'leri.

- /healthz → process ayakta mı (Render & UptimeRobot ping hedefi).
- /readyz  → bağımlılıklar hazır mı (ChromaDB ulaşılabilir + Gemini key var).

Mevcut /health endpoint'i (app/main.py) basit OK döndürmeye devam eder; eski
client'ları kırmamak için saklı tutuldu.
"""
from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.config import settings
from app.services.retriever import get_retriever

router = APIRouter()


@router.get("/healthz", tags=["system"])
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz", tags=["system"])
def readyz(response: Response) -> dict[str, object]:
    checks: dict[str, object] = {}

    checks["gemini_api_key"] = bool(settings.gemini_api_key)

    retriever = get_retriever()
    if retriever is None:
        checks["chroma"] = {"ok": False, "count": 0}
    else:
        try:
            count = retriever.count()
            checks["chroma"] = {"ok": count > 0, "count": count}
        except Exception as exc:
            checks["chroma"] = {"ok": False, "error": str(exc)[:200]}

    all_ok = bool(checks["gemini_api_key"]) and bool(
        (checks["chroma"] if isinstance(checks["chroma"], dict) else {}).get("ok")
    )
    if not all_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"ready": all_ok, "checks": checks}
