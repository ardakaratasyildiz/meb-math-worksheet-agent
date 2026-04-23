from datetime import datetime, timezone
from functools import lru_cache

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.data.curriculum import get_topic
from app.models.enums import TopicId
from app.models.schemas import (
    AnswerKeyEntry,
    GenerateWorksheetRequest,
    GenerateWorksheetResponse,
    Worksheet,
    WorksheetMetadata,
)
from app.services.agent import AgentError, GeminiAgent

router = APIRouter()


@lru_cache(maxsize=1)
def _agent() -> GeminiAgent:
    return GeminiAgent()


def _validate_request(req: GenerateWorksheetRequest) -> None:
    valid_topic_ids = {t.value for t in TopicId}
    if req.topic_id not in valid_topic_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Geçersiz topic_id '{req.topic_id}'. Geçerliler: {sorted(valid_topic_ids)}",
        )
    topic = get_topic(req.grade, req.topic_id)
    if topic is None:
        raise HTTPException(
            status_code=400,
            detail=f"{req.grade}. sınıfta '{req.topic_id}' konusu müfredatta yok.",
        )
    if req.kazanim_kod is not None:
        if not any(k["kod"] == req.kazanim_kod for k in topic["kazanimlar"]):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"'{req.kazanim_kod}' kodu {req.grade}. sınıf '{req.topic_id}' "
                    "konusunda bulunamadı."
                ),
            )


@router.post("/generate", response_model=GenerateWorksheetResponse)
def generate_worksheet(req: GenerateWorksheetRequest) -> GenerateWorksheetResponse:
    _validate_request(req)
    topic = get_topic(req.grade, req.topic_id)
    assert topic is not None

    agent = _agent()
    try:
        questions = agent.generate(
            grade=req.grade,
            topic_id=req.topic_id,
            kazanim_kod=req.kazanim_kod,
            difficulty=req.difficulty,
            question_count=req.question_count,
        )
    except AgentError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if not questions:
        raise HTTPException(
            status_code=502,
            detail="Üretim sonucu boş geldi; lütfen tekrar deneyin.",
        )

    title = f"{req.grade}. Sınıf - {topic['name']} Çalışma Kağıdı"

    worksheet = Worksheet(
        title=title,
        grade=req.grade,
        topic=topic["name"],
        difficulty=req.difficulty,
        question_count=len(questions),
        questions=questions,
        answer_key=[
            AnswerKeyEntry(number=q.number, answer=q.answer) for q in questions
        ],
    )
    metadata = WorksheetMetadata(
        generated_at=datetime.now(tz=timezone.utc),
        model=agent.last_model_used,
    )
    return GenerateWorksheetResponse(worksheet=worksheet, metadata=metadata)
