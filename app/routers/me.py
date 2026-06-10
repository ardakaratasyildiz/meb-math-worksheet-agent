"""Kullanıcı (öğrenci) ilerleme endpoint'leri (öğrenme döngüsü — Adım 3).

GET /api/me/progress → kazanım-bazlı ustalık + genel özet + zayıf kazanımlar.
LLM çağrısı yok (saf sayım) → rate limit yok, yalnız auth.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.models.schemas import ProgressResponse
from app.security import require_api_key
from app.services.progress import build_progress
from app.services.quiz_store import QUIZ_STORE

router = APIRouter()


@router.get("/progress", response_model=ProgressResponse)
def get_progress(
    tenant_id: str,
    _api_key: str = Depends(require_api_key),
) -> ProgressResponse:
    """Kullanıcının kazanım ustalığı + zayıf konuları + genel özeti."""
    mastery_rows = QUIZ_STORE.get_mastery(tenant_id)
    quizzes_solved = QUIZ_STORE.count_attempts(tenant_id)
    recent = QUIZ_STORE.recent_attempts(tenant_id, limit=10)
    return build_progress(mastery_rows, quizzes_solved, recent)
