"""Render uçları — istemci-tarafı görüntüleme için sunucu render'ı.

/api/render/math: soru metnindeki LaTeX ($...$ / $$...$$) bloklarını SVG'ye
render eder (matplotlib mathtext). Mobil `QuestionText` tek çağrıda segmentleri
alıp düz metni + keskin matematik SVG'sini gösterir (Unicode yaklaşımının yerine).
Web `rehype-katex` kullandığından bu uç mobil-odaklı.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.security import limiter, require_api_key
from app.services import math_renderer

router = APIRouter()


class MathRenderRequest(BaseModel):
    text: str = Field(..., max_length=8000)
    font_size: int = Field(16, ge=8, le=40)


class MathSegment(BaseModel):
    kind: str  # "text" | "math"
    text: str = ""  # düz metin İÇERİĞİ veya matematik Unicode fallback'i
    svg: str | None = None  # math + render başarılıysa SVG; aksi halde None
    display: bool = False  # $$...$$ (blok) mu


class MathRenderResponse(BaseModel):
    segments: list[MathSegment]


@router.post("/math", response_model=MathRenderResponse)
@limiter.limit("60/minute;600/hour")
def render_math(
    request: Request,  # noqa: ARG001 — slowapi limiter için gerekli
    req: MathRenderRequest,
    _api_key: str = Depends(require_api_key),
) -> MathRenderResponse:
    """Metindeki matematik bloklarını SVG'ye render eder → segment listesi."""
    segments = math_renderer.render_text_math_segments(req.text, font_size=req.font_size)
    return MathRenderResponse(segments=[MathSegment(**s) for s in segments])
