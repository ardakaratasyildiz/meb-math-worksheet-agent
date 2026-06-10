"""Kullanıcı (öğrenci) ilerleme endpoint'leri (öğrenme döngüsü — Adım 3).

GET /api/me/progress → kazanım-bazlı ustalık + genel özet + zayıf kazanımlar.
LLM çağrısı yok (saf sayım) → rate limit yok, yalnız auth.
"""
from __future__ import annotations

import time
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.models.schemas import (
    AttemptDetail,
    AttemptHistoryItem,
    AttemptHistoryResponse,
    GamificationResponse,
    ProgressResponse,
    Question,
    SubmittedAnswer,
)
from app.security import require_api_key
from app.services.attempt_review import build_attempt_detail
from app.services.gamification import build_gamification
from app.services.progress import build_daily_trend, build_progress
from app.services.quiz_store import QUIZ_STORE

_IST = timezone(timedelta(hours=3))

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
    resp = build_progress(mastery_rows, quizzes_solved, recent)
    # 30 günlük gün-bazlı trend (Türkiye günü).
    since = time.time() - 30 * 86400
    today = datetime.now(_IST).date()
    resp.daily_trend = build_daily_trend(
        QUIZ_STORE.attempts_since(tenant_id, since), today
    )
    return resp


@router.get("/gamification", response_model=GamificationResponse)
def get_gamification(
    tenant_id: str,
    _api_key: str = Depends(require_api_key),
) -> GamificationResponse:
    """XP / seviye / seri. Rozetler frontend'de mastery'den türetilir."""
    mastery_rows = QUIZ_STORE.get_mastery(tenant_id)
    total_correct = sum(int(m.get("correct", 0)) for m in mastery_rows)
    quizzes_solved = QUIZ_STORE.count_attempts(tenant_id)
    active_dates = [
        date.fromisoformat(s)
        for s in QUIZ_STORE.distinct_attempt_dates(tenant_id)
    ]
    today = datetime.now(_IST).date()
    return build_gamification(total_correct, quizzes_solved, active_dates, today)


@router.get("/attempts", response_model=AttemptHistoryResponse)
def list_attempts(
    tenant_id: str,
    limit: int = 50,
    _api_key: str = Depends(require_api_key),
) -> AttemptHistoryResponse:
    """Kullanıcının geçmiş çözüm denemeleri — en yeni önce."""
    rows = QUIZ_STORE.list_attempts(tenant_id, limit=limit)
    return AttemptHistoryResponse(
        items=[AttemptHistoryItem(**r) for r in rows]
    )


@router.get("/attempts/{attempt_id}", response_model=AttemptDetail)
def get_attempt_detail(
    attempt_id: str,
    tenant_id: str,
    _api_key: str = Depends(require_api_key),
) -> AttemptDetail:
    """Geçmiş bir denemenin tam gözden geçirmesi (soru + doğru cevap + senin cevabın)."""
    rec = QUIZ_STORE.get_attempt(attempt_id, tenant_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Deneme bulunamadı.")
    snapshot = rec.get("snapshot")
    if not snapshot:
        # Eski/snapshot'sız kayıt + quiz de silinmiş → yalnız skor özeti.
        return AttemptDetail(
            attempt_id=rec["attempt_id"],
            quiz_id=rec["quiz_id"],
            title="Quiz",
            grade=None,
            topic_id="",
            difficulty="orta",
            score=rec["score"],
            total=rec["total"],
            duration_seconds=rec.get("duration_seconds"),
            completed_at=rec["completed_at"],
            has_detail=False,
        )
    questions = [Question(**q) for q in snapshot.get("questions", [])]
    submitted = [SubmittedAnswer(**a) for a in rec.get("answers", [])]
    return build_attempt_detail(
        attempt_id=rec["attempt_id"],
        quiz_id=rec["quiz_id"],
        meta=snapshot,
        questions=questions,
        submitted=submitted,
        duration_seconds=rec.get("duration_seconds"),
        completed_at=rec["completed_at"],
    )
