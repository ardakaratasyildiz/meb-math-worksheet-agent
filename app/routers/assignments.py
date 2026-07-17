"""Ödev çözme endpoint'leri (Faz 3.5 — Sınıf modeli, PR 2).

GET  /api/assignments/{id}          → ödev quiz'ini çözmek için getir (CEVAPSIZ),
                                       yalnız sınıf üyesi/sahibi.
POST /api/assignments/{id}/attempt  → cevapları puanla + kaydet (assignment_id +
                                       öğrencinin tenant'ına işlenir → kişisel
                                       ilerleme/mastery de güncellenir).

Anti-kopya: cevaplar sunucuda; _to_public ile soyma; puanlama sunucuda (grade_quiz).
"""
from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, HTTPException

from app.models.enums import Difficulty
from app.models.schemas import (
    AssignmentResultItem,
    AssignmentResultsResponse,
    AssignmentWorksheetResponse,
    AttemptResult,
    Question,
    QuizPublic,
    SubmitAttemptRequest,
    Worksheet,
)
from app.routers.quizzes import _to_public
from app.security import require_api_key
from app.services.classroom_store import CLASSROOM_STORE
from app.services.clerk_auth import require_tenant, verified_tenant_id
from app.services.grading import grade_quiz
from app.services.quiz_store import QUIZ_STORE

logger = logging.getLogger(__name__)

router = APIRouter()


def _load_solvable(assignment_id: str, tenant_id: str) -> dict:
    """Ödevi çöz + erişim kontrolü (sınıf üyesi/sahibi) + çözülebilir içeriği getir.

    İki ödev tipini de destekler:
      - quiz  → QUIZ_STORE'daki quiz'in soruları; açık uçlu ÖZ-DEĞERLENDİRME (answer_mode=quiz).
      - pdf   → worksheet_json'daki sorular; açık uçlu/yapılandırılmamış tipler METİN-EŞLEŞTİRME
                (answer_mode=worksheet, quiz_id="" → attempt yalnız assignment_id'ye bağlanır).

    Dönüş: assignment, questions (list[Question]), meta (title/grade/topic_id/difficulty/
    created_at), answer_mode, quiz_id (attempt kaydı için).
    """
    assignment = CLASSROOM_STORE.get_assignment(assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Ödev bulunamadı.")
    if not CLASSROOM_STORE.is_member(assignment["classroom_id"], tenant_id):
        raise HTTPException(status_code=403, detail="Bu ödeve erişimin yok.")

    if assignment.get("assignment_type") == "pdf":
        if not assignment.get("worksheet_json"):
            raise HTTPException(status_code=404, detail="Ödev içeriği bulunamadı.")
        try:
            worksheet = Worksheet(**json.loads(assignment["worksheet_json"]))
        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            logger.error("worksheet ödevi parse hatası: %s", exc)
            raise HTTPException(status_code=500, detail="Ödev içeriği okunamadı.") from exc
        return {
            "assignment": assignment,
            "questions": worksheet.questions,
            "meta": {
                "title": assignment["title"] or worksheet.title,
                "grade": worksheet.grade,
                "topic_id": worksheet.topic,
                "difficulty": worksheet.difficulty,
                "created_at": assignment.get("created_at", ""),
            },
            "answer_mode": "worksheet",
            "quiz_id": "",  # worksheet ödevinin quiz kaydı yok → attempt assignment_id'ye bağlanır
        }

    # Varsayılan: quiz ödevi
    quiz = QUIZ_STORE.get_quiz_by_id(assignment["quiz_id"])
    if quiz is None:
        raise HTTPException(status_code=404, detail="Ödev quiz'i artık mevcut değil.")
    return {
        "assignment": assignment,
        "questions": [Question(**q) for q in quiz["questions"]],
        "meta": {
            "title": quiz["title"],
            "grade": quiz["grade"],
            "topic_id": quiz["topic_id"],
            "difficulty": quiz["difficulty"],
            "created_at": quiz["created_at"],
        },
        "answer_mode": "quiz",
        "quiz_id": quiz["id"],
    }


@router.get("/{assignment_id}", response_model=QuizPublic)
def get_assignment_quiz(
    assignment_id: str,
    tenant_id: str,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> QuizPublic:
    """Ödevi çözmek için getir — CEVAPSIZ, yalnız sınıf üyesi/sahibi. Quiz + worksheet ödevi."""
    tenant_id = require_tenant(verified, tenant_id)
    resolved = _load_solvable(assignment_id, tenant_id)
    meta = resolved["meta"]
    return _to_public(
        quiz_id=resolved["quiz_id"] or assignment_id,
        title=meta["title"],
        grade=meta["grade"],
        topic_id=meta["topic_id"],
        difficulty=Difficulty(meta["difficulty"]),
        created_at=meta["created_at"],
        questions=resolved["questions"],
        answer_mode=resolved["answer_mode"],
    )


@router.post("/{assignment_id}/attempt", response_model=AttemptResult)
def submit_assignment_attempt(
    assignment_id: str,
    req: SubmitAttemptRequest,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> AttemptResult:
    """Ödev cevaplarını gönder → sunucuda puanla → öğrencinin tenant'ına + ödeve kaydet.

    Worksheet ödevinde açık uçlu/yapılandırılmamış tipler cevap anahtarına metin-eşleştirmeyle
    puanlanır (open_ended_text_match); quiz ödevinde açık uçlu öz-değerlendirmeyle.
    """
    req.tenant_id = require_tenant(verified, req.tenant_id)
    resolved = _load_solvable(assignment_id, req.tenant_id)
    assignment = resolved["assignment"]
    stored = resolved["questions"]
    is_worksheet = resolved["answer_mode"] == "worksheet"

    results, score, total, per_kazanim = grade_quiz(
        stored, req.answers, open_ended_text_match=is_worksheet
    )
    per_kazanim_dicts = [k.model_dump() for k in per_kazanim]

    attempt = QUIZ_STORE.record_attempt(
        quiz_id=resolved["quiz_id"],
        solver_tenant_id=req.tenant_id,
        answers=[a.model_dump() for a in req.answers],
        score=score,
        total=total,
        duration_seconds=req.duration_seconds,
        per_kazanim=per_kazanim_dicts,
        quiz_snapshot={
            "title": resolved["meta"]["title"],
            "grade": resolved["meta"]["grade"],
            "topic_id": resolved["meta"]["topic_id"],
            "difficulty": resolved["meta"]["difficulty"],
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
        quiz_id=resolved["quiz_id"],
        score=score,
        total=total,
        duration_seconds=req.duration_seconds,
        per_kazanim=per_kazanim,
        results=results,
        completed_at=attempt["completed_at"],
    )


@router.get("/{assignment_id}/worksheet", response_model=AssignmentWorksheetResponse)
def get_assignment_worksheet(
    assignment_id: str,
    tenant_id: str,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> AssignmentWorksheetResponse:
    """PDF ödevinin worksheet'ini getir — yalnız sınıf üyesi/sahibi. Öğrenci istemcide
    PDF'e render eder (cevap anahtarı kapalı)."""
    tenant_id = require_tenant(verified, tenant_id)
    assignment = CLASSROOM_STORE.get_assignment(assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Ödev bulunamadı.")
    if not CLASSROOM_STORE.is_member(assignment["classroom_id"], tenant_id):
        raise HTTPException(status_code=403, detail="Bu ödeve erişimin yok.")
    if assignment.get("assignment_type") != "pdf" or not assignment.get("worksheet_json"):
        raise HTTPException(status_code=404, detail="Bu ödev bir PDF ödevi değil.")
    try:
        data = json.loads(assignment["worksheet_json"])
        worksheet = Worksheet(**data)
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        logger.error("pdf ödev worksheet parse hatası: %s", exc)
        raise HTTPException(status_code=500, detail="Ödev içeriği okunamadı.") from exc
    return AssignmentWorksheetResponse(title=assignment["title"], worksheet=worksheet)


@router.get("/{assignment_id}/results", response_model=AssignmentResultsResponse)
def get_assignment_results(
    assignment_id: str,
    tenant_id: str,
    verified: str | None = Depends(verified_tenant_id),
    _api_key: str = Depends(require_api_key),
) -> AssignmentResultsResponse:
    """Ödevin sonuç panosu — sınıf roster'ı bazlı (çözen/çözmeyen). Yalnız sınıf sahibi."""
    tenant_id = require_tenant(verified, tenant_id)
    data = CLASSROOM_STORE.assignment_results(assignment_id, tenant_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Ödev bulunamadı.")
    return AssignmentResultsResponse(
        title=data["title"],
        question_count=data["question_count"],
        member_count=data["member_count"],
        solved_count=data["solved_count"],
        items=[AssignmentResultItem(**i) for i in data["items"]],
    )
