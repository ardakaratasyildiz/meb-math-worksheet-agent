"""Ödev çözme endpoint'leri (Faz 3.5 — Sınıf modeli, PR 2).

GET  /api/assignments/{id}          → ödev quiz'ini çözmek için getir (CEVAPSIZ),
                                       yalnız sınıf üyesi/sahibi.
POST /api/assignments/{id}/attempt  → cevapları puanla + kaydet (assignment_id +
                                       öğrencinin tenant'ına işlenir → kişisel
                                       ilerleme/mastery de güncellenir).

Anti-kopya: cevaplar sunucuda; _to_public ile soyma; puanlama sunucuda (grade_quiz).
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.models.enums import Difficulty
from app.models.schemas import (
    AttemptResult,
    Question,
    QuizPublic,
    SubmitAttemptRequest,
)
from app.routers.quizzes import _to_public
from app.security import require_api_key
from app.services.classroom_store import CLASSROOM_STORE
from app.services.grading import grade_quiz
from app.services.quiz_store import QUIZ_STORE

logger = logging.getLogger(__name__)

router = APIRouter()


def _resolve_assignment(assignment_id: str, tenant_id: str) -> dict:
    """Ödevi çözer + erişim kontrolü (sınıf üyesi/sahibi) + quiz'i getirir."""
    assignment = CLASSROOM_STORE.get_assignment(assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Ödev bulunamadı.")
    if not CLASSROOM_STORE.is_member(assignment["classroom_id"], tenant_id):
        raise HTTPException(status_code=403, detail="Bu ödeve erişimin yok.")
    quiz = QUIZ_STORE.get_quiz_by_id(assignment["quiz_id"])
    if quiz is None:
        raise HTTPException(status_code=404, detail="Ödev quiz'i artık mevcut değil.")
    return {"assignment": assignment, "quiz": quiz}


@router.get("/{assignment_id}", response_model=QuizPublic)
def get_assignment_quiz(
    assignment_id: str,
    tenant_id: str,
    _api_key: str = Depends(require_api_key),
) -> QuizPublic:
    """Ödev quiz'ini çözmek için getir — CEVAPSIZ, yalnız sınıf üyesi/sahibi."""
    quiz = _resolve_assignment(assignment_id, tenant_id)["quiz"]
    questions = [Question(**q) for q in quiz["questions"]]
    return _to_public(
        quiz_id=quiz["id"],
        title=quiz["title"],
        grade=quiz["grade"],
        topic_id=quiz["topic_id"],
        difficulty=Difficulty(quiz["difficulty"]),
        created_at=quiz["created_at"],
        questions=questions,
    )


@router.post("/{assignment_id}/attempt", response_model=AttemptResult)
def submit_assignment_attempt(
    assignment_id: str,
    req: SubmitAttemptRequest,
    _api_key: str = Depends(require_api_key),
) -> AttemptResult:
    """Ödev cevaplarını gönder → sunucuda puanla → öğrencinin tenant'ına + ödeve kaydet."""
    resolved = _resolve_assignment(assignment_id, req.tenant_id)
    assignment, quiz = resolved["assignment"], resolved["quiz"]
    stored = [Question(**q) for q in quiz["questions"]]

    results, score, total, per_kazanim = grade_quiz(stored, req.answers)
    per_kazanim_dicts = [k.model_dump() for k in per_kazanim]

    attempt = QUIZ_STORE.record_attempt(
        quiz_id=quiz["id"],
        solver_tenant_id=req.tenant_id,
        answers=[a.model_dump() for a in req.answers],
        score=score,
        total=total,
        duration_seconds=req.duration_seconds,
        per_kazanim=per_kazanim_dicts,
        quiz_snapshot={
            "title": quiz["title"],
            "grade": quiz["grade"],
            "topic_id": quiz["topic_id"],
            "difficulty": quiz["difficulty"],
            "questions": [q.model_dump() for q in stored],
        },
        assignment_id=assignment["id"],
    )
    # Öğrenci üye + giriş yapmış → kişisel ilerleme/mastery güncellenir (best-effort).
    try:
        QUIZ_STORE.update_mastery(req.tenant_id, per_kazanim_dicts)
    except Exception as exc:  # noqa: BLE001
        logger.warning("mastery güncelleme hatası (assignment, tenant=%s): %s", req.tenant_id, exc)

    logger.info(
        "assignment attempt: tenant=%s assignment=%s skor=%d/%d",
        req.tenant_id, assignment_id, score, total,
    )
    return AttemptResult(
        attempt_id=attempt["id"],
        quiz_id=quiz["id"],
        score=score,
        total=total,
        duration_seconds=req.duration_seconds,
        per_kazanim=per_kazanim,
        results=results,
        completed_at=attempt["completed_at"],
    )
