from datetime import datetime, timezone
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response

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
from app.security import limiter, rate_limit_string, require_api_key
from app.services.agent import AgentError, GeminiAgent
from app.services.pdf_renderer import render_worksheet_pdf

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


def _build_worksheet(req: GenerateWorksheetRequest) -> tuple[Worksheet, WorksheetMetadata]:
    """Ortak üretim mantığı: hem JSON hem PDF endpoint'leri kullanır."""
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
            tenant_id=req.tenant_id,
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
        trace=agent.build_last_trace(),
    )
    return worksheet, metadata


@router.post("/generate", response_model=GenerateWorksheetResponse)
@limiter.limit(rate_limit_string())
def generate_worksheet(
    request: Request,
    req: GenerateWorksheetRequest,
    _api_key: str = Depends(require_api_key),
) -> GenerateWorksheetResponse:
    worksheet, metadata = _build_worksheet(req)
    return GenerateWorksheetResponse(worksheet=worksheet, metadata=metadata)


def _pdf_response(worksheet: Worksheet) -> Response:
    pdf_bytes = render_worksheet_pdf(worksheet)
    safe_title = (
        worksheet.title.replace(" ", "_")
        .replace("/", "-")
        .encode("ascii", "ignore")
        .decode()
    ) or "worksheet"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_title}.pdf"',
        },
    )


@router.post("/generate.pdf")
@limiter.limit(rate_limit_string())
def generate_worksheet_pdf(
    request: Request,
    req: GenerateWorksheetRequest,
    _api_key: str = Depends(require_api_key),
) -> Response:
    """Üretim + PDF render tek call'da. Rate limit + auth uygulanır (LLM çağrısı yapar)."""
    worksheet, _ = _build_worksheet(req)
    return _pdf_response(worksheet)


@router.post("/render.pdf")
def render_existing_worksheet(
    worksheet: Worksheet,
    _api_key: str = Depends(require_api_key),
) -> Response:
    """Önceden üretilmiş bir worksheet JSON'unu PDF'e çevirir.

    LLM çağrısı YAPMAZ → rate limit yok; sadece auth kontrolü.
    Frontend hızlı tekrar PDF üretebilir.
    """
    return _pdf_response(worksheet)
