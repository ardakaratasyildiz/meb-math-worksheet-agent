import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from functools import lru_cache
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response, StreamingResponse

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
logger = logging.getLogger(__name__)


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


def _split_difficulty_buckets(total: int) -> dict["Difficulty", int]:
    """Karışık/progresyon modu için zorluk dağılımı.

    Hedef oran: kolay 30%, orta 40%, zor 30%. Toplam < 5 için anlamlı bölüm
    çıkmayacağından tek seviye fallback verilir.
    """
    from app.models.enums import Difficulty
    if total < 5:
        return {Difficulty.ORTA: total}
    kolay = max(1, total * 3 // 10)
    zor = max(1, total * 3 // 10)
    orta = total - kolay - zor
    if orta < 1:
        return {Difficulty.ORTA: total}
    return {Difficulty.KOLAY: kolay, Difficulty.ORTA: orta, Difficulty.ZOR: zor}


def _build_worksheet(req: GenerateWorksheetRequest) -> tuple[Worksheet, WorksheetMetadata]:
    """Ortak üretim mantığı: hem JSON hem PDF endpoint'leri kullanır.

    Sprint 12-A toggle paketi (2026-05-19):
        difficulty_mode = "single"     → tek difficulty ile mevcut akış
        difficulty_mode = "mixed"      → kolay/orta/zor 3 ayrı agent.generate;
                                         birleştirilip rastgele karıştırılır.
        difficulty_mode = "progressive"→ aynı 3 batch; kolay → orta → zor sırası.
        question_types verilirse agent.generate'e allowed_types geçer.
    """
    from app.models.enums import Difficulty as _Diff
    _validate_request(req)
    topic = get_topic(req.grade, req.topic_id)
    assert topic is not None

    agent = _agent()

    def _gen(diff: _Diff, count: int) -> list:
        return agent.generate(
            grade=req.grade,
            topic_id=req.topic_id,
            kazanim_kod=req.kazanim_kod,
            difficulty=diff,
            question_count=count,
            tenant_id=req.tenant_id,
            allowed_types=req.question_types,
        )

    if req.difficulty_mode == "single":
        try:
            questions = _gen(req.difficulty, req.question_count)
        except AgentError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        trace_for_meta = agent.build_last_trace()
        worksheet_difficulty = req.difficulty
    else:
        # Mixed/progressive: kolay/orta/zor 3 ayrı agent.generate çağrısı.
        # Her çağrı içinde ~3-5 LLM call var → 3 bucket = ~10-15 Gemini çağrısı
        # saniyeler içinde. Free-tier rate limit / 503 nedeniyle bir bucket
        # fail edebilir. Bucket-başına hata yakalanır: en az 1 bucket başarılı
        # olduğu sürece kısmi sonuç döndürülür (tüm istek çökmez). Bucket'lar
        # arasına kısa gecikme — rate limit burst'ünü yumuşatır.
        buckets = _split_difficulty_buckets(req.question_count)
        collected: list = []
        bucket_errors: list[str] = []
        bucket_seq = [d for d in (_Diff.KOLAY, _Diff.ORTA, _Diff.ZOR)
                      if buckets.get(d, 0) > 0]
        for idx, diff in enumerate(bucket_seq):
            n = buckets[diff]
            try:
                collected.extend(_gen(diff, n))
            except AgentError as exc:
                logger.warning(
                    "Bucket başarısız (diff=%s, n=%s): %s — kısmi sonuçla devam.",
                    diff.value, n, exc,
                )
                bucket_errors.append(f"{diff.value}: {exc}")
            # Son bucket değilse rate limit burst'ünü yumuşat.
            if idx < len(bucket_seq) - 1:
                time.sleep(1.5)

        if not collected:
            # Hiçbir bucket başarılı olmadı — gerçek hata.
            detail = "Üretim başarısız (tüm zorluk grupları hata verdi). "
            if bucket_errors:
                detail += "Sebep: " + " | ".join(bucket_errors[:3])
            raise HTTPException(status_code=502, detail=detail)

        if req.difficulty_mode == "mixed":
            import random as _random
            _random.shuffle(collected)
        # progressive ise zaten kolay→orta→zor sırasında toplandı.
        from app.models.schemas import Question as _Q
        questions = [
            q.model_copy(update={"number": i + 1}) if isinstance(q, _Q) else q
            for i, q in enumerate(collected)
        ]
        trace_for_meta = agent.build_last_trace()
        worksheet_difficulty = req.difficulty

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
        difficulty=worksheet_difficulty,
        question_count=len(questions),
        questions=questions,
        answer_key=[
            AnswerKeyEntry(number=q.number, answer=q.answer) for q in questions
        ],
    )
    metadata = WorksheetMetadata(
        generated_at=datetime.now(tz=timezone.utc),
        model=agent.last_model_used,
        trace=trace_for_meta,
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


# Türkçe karakterleri ASCII karşılıklarına çevirir; başlığa benzer şekilde
# frontend/lib'de de aynı haritalama var (PDF dosya adı tutarlılığı için).
_TURKISH_TRANSLIT = str.maketrans({
    "ş": "s", "Ş": "S",
    "ı": "i", "İ": "I",
    "ğ": "g", "Ğ": "G",
    "ç": "c", "Ç": "C",
    "ö": "o", "Ö": "O",
    "ü": "u", "Ü": "U",
})


def _build_pdf_filename(worksheet: Worksheet) -> str:
    title_ascii = worksheet.title.translate(_TURKISH_TRANSLIT)
    cleaned = "".join(
        c if c.isalnum() or c in " -_" else " " for c in title_ascii
    )
    parts = [p for p in cleaned.split() if p]
    slug = "_".join(parts) if parts else "Calisma_Kagidi"
    today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    return f"SoruAtolyesi_{slug}_{today}.pdf"


def _pdf_response(
    worksheet: Worksheet,
    include_answer_key: bool = True,
    include_solutions: bool = True,
) -> Response:
    pdf_bytes = render_worksheet_pdf(
        worksheet,
        include_answer_key=include_answer_key,
        include_solutions=include_solutions,
    )
    filename = _build_pdf_filename(worksheet)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
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
    return _pdf_response(
        worksheet,
        include_answer_key=req.include_answer_key,
        include_solutions=req.include_solutions,
    )


@router.post("/render.pdf")
def render_existing_worksheet(
    worksheet: Worksheet,
    include_answer_key: bool = True,
    include_solutions: bool = True,
    _api_key: str = Depends(require_api_key),
) -> Response:
    """Önceden üretilmiş bir worksheet JSON'unu PDF'e çevirir.

    LLM çağrısı YAPMAZ → rate limit yok; sadece auth kontrolü.
    Frontend hızlı tekrar PDF üretebilir. Toggle'lar query parametresi olarak
    geçer: ?include_answer_key=false&include_solutions=false (sınav modu).
    """
    return _pdf_response(
        worksheet,
        include_answer_key=include_answer_key,
        include_solutions=include_solutions,
    )


# ---- SSE streaming endpoint (Sprint 7) ----------------------------------
# Pragmatik MVP: agent.generate hâlâ blocking (Gemini batch response).
# Endpoint blocking üretim sonrası her soruyu ayrı SSE event olarak yollar →
# frontend EventSource canlı akış hissi verir, perceived latency düşer.
# Gerçek token-by-token streaming Sprint 7.5'te (Gemini streaming API + agent
# refactor) eklenecek.


async def _stream_worksheet_events(
    req: GenerateWorksheetRequest,
) -> AsyncIterator[str]:
    """SSE event akışı üretir. Format:
        event: meta        — başlangıç (request echo)
        event: question    — her soru
        event: complete    — final worksheet + metadata
        event: error       — hata
    """

    def sse(event: str, data: dict | str) -> str:
        body = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
        return f"event: {event}\ndata: {body}\n\n"

    # Hand-off başlangıç event'i — frontend "bağlantı kuruldu" olarak gösterir
    yield sse("meta", {
        "grade": req.grade,
        "topic_id": req.topic_id,
        "kazanim_kod": req.kazanim_kod,
        "difficulty": req.difficulty.value if hasattr(req.difficulty, "value") else req.difficulty,
        "question_count": req.question_count,
    })

    try:
        worksheet, metadata = await asyncio.to_thread(_build_worksheet, req)
    except HTTPException as exc:
        yield sse("error", {"detail": exc.detail, "status": exc.status_code})
        return
    except Exception as exc:  # noqa: BLE001
        yield sse("error", {"detail": str(exc)[:500], "status": 500})
        return

    # Her soru ayrı event — frontend skeleton'ları teker teker doldurur.
    for q in worksheet.questions:
        yield sse("question", q.model_dump(mode="json"))
        await asyncio.sleep(0.05)  # küçük gecikme → akış hissi

    yield sse(
        "complete",
        {
            "worksheet": worksheet.model_dump(mode="json"),
            "metadata": metadata.model_dump(mode="json"),
        },
    )


@router.post("/generate.stream")
@limiter.limit(rate_limit_string())
def generate_worksheet_stream(
    request: Request,
    req: GenerateWorksheetRequest,
    _api_key: str = Depends(require_api_key),
) -> StreamingResponse:
    """SSE streaming üretim. Frontend EventSource ile bağlanır."""
    return StreamingResponse(
        _stream_worksheet_events(req),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",  # Render/Nginx proxy buffer'ını kapat
        },
    )
