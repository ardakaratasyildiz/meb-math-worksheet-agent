"""Paylaşılan quiz — public çözme (öğrenme döngüsü — Faz 3 paylaşım, PR A).

GET  /api/shared/{code}          → cevapsız quiz (çözmek için). Login GEREKMEZ —
                                   viral giriş noktası; misafir de çözer.
POST /api/shared/{code}/attempt  → cevapları sunucuda puanla + kaydet. Misafir
                                   (tenant_id yok) ya da giriş yapmış çözen.

Anti-kopya: GET cevapsız (quizzes._to_public ile soyma). Puanlama sunucuda
(grade_quiz), cevaplar yalnız gönderimden sonra sonuçta döner. Public /attempt
per-IP rate-limitli (brute-force ile cevap madenciliğini yavaşlatır).
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from app.models.enums import Difficulty
from app.models.schemas import (
    AttemptResult,
    Question,
    QuizPublic,
    SharedAttemptRequest,
)
from app.routers.quizzes import _to_public
from app.security import limiter, rate_limit_string, require_api_key
from app.services.grading import grade_quiz
from app.services.quiz_store import QUIZ_STORE

logger = logging.getLogger(__name__)

router = APIRouter()

# Misafir (giriş yapmamış) çözen için solver_tenant_id sentinel'i. Kişisel
# ilerleme/mastery bu kullanıcı için güncellenmez (gerçek tenant yok).
_ANON_SOLVER = "anon"


def _resolve_shared_quiz(code: str) -> dict:
    """Kodu aktif paylaşıma, paylaşımı quiz'e çözer. Yoksa 404."""
    share = QUIZ_STORE.get_share_by_code(code)
    if share is None:
        raise HTTPException(
            status_code=404, detail="Paylaşım bulunamadı veya kaldırılmış."
        )
    quiz = QUIZ_STORE.get_quiz_by_id(share["quiz_id"])
    if quiz is None:
        raise HTTPException(status_code=404, detail="Quiz artık mevcut değil.")
    return {"share": share, "quiz": quiz}


@router.get("/{code}", response_model=QuizPublic)
def get_shared_quiz(
    code: str,
    _api_key: str = Depends(require_api_key),
) -> QuizPublic:
    """Paylaşılan quiz'i çözmek için getir — CEVAPSIZ, login gerekmez."""
    quiz = _resolve_shared_quiz(code)["quiz"]
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


@router.post("/{code}/attempt", response_model=AttemptResult)
@limiter.limit(rate_limit_string())
def submit_shared_attempt(
    request: Request,
    code: str,
    req: SharedAttemptRequest,
    _api_key: str = Depends(require_api_key),
) -> AttemptResult:
    """Paylaşılan quiz cevaplarını gönder → sunucuda puanla → sonuç.

    Çözüm sahibin sonuç panosuna düşer (share_id). Giriş yapmış çözende ayrıca
    kişisel ilerleme/mastery güncellenir; misafirde güncellenmez.
    """
    resolved = _resolve_shared_quiz(code)
    share, quiz = resolved["share"], resolved["quiz"]
    stored = [Question(**q) for q in quiz["questions"]]

    results, score, total, per_kazanim = grade_quiz(stored, req.answers)
    per_kazanim_dicts = [k.model_dump() for k in per_kazanim]

    solver = req.tenant_id or _ANON_SOLVER
    attempt = QUIZ_STORE.record_attempt(
        quiz_id=quiz["id"],
        solver_tenant_id=solver,
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
        share_id=share["id"],
        solver_label=req.solver_label,
    )
    # Mastery yalnız giriş yapmış çözen için (gerçek tenant). Best-effort.
    if req.tenant_id:
        try:
            QUIZ_STORE.update_mastery(req.tenant_id, per_kazanim_dicts)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "mastery güncelleme hatası (shared, tenant=%s): %s",
                req.tenant_id, exc,
            )

    logger.info(
        "shared attempt: code=%s solver=%s skor=%d/%d",
        code, solver, score, total,
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
