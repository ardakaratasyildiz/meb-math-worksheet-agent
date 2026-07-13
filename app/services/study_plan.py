"""AI destekli haftalık çalışma programı (WS-6a).

Öğrencinin ZAYIF kazanımlarından (ProgressResponse.weak) deterministik bir gün-gün
program KURULUR (doğru ders/sınıf/kazanım deep-link'leriyle — LLM link uydurmaz),
sonra bir LLM geçişiyle her güne motive edici başlık/ipucu + genel özet EKLENİR.
LLM erişilemezse deterministik başlık/ipuçlarına düşülür (fail-open).
"""
from __future__ import annotations

import logging

from google import genai
from google.genai import types
from pydantic import BaseModel

from app.config import settings
from app.models.schemas import ProgressResponse, StudyPlanDay, StudyPlanResponse

logger = logging.getLogger(__name__)

_MAX_DAYS = 5
_QUESTIONS_PER_DAY = 10


class _DayEnrich(BaseModel):
    day_no: int
    title: str
    tip: str


class _PlanEnrich(BaseModel):
    summary: str
    days: list[_DayEnrich]


_SYSTEM = """Sen destekleyici bir öğrenme koçusun. Öğrencinin ZAYIF olduğu konulara
göre kısa, motive edici bir haftalık çalışma programı metni yazıyorsun. Sana gün gün
konu listesi verilir. Her gün için:
- title: 3-6 kelimelik, cesaretlendirici ama abartısız bir başlık.
- tip: tek cümlelik SOMUT bir çalışma önerisi (o konuya özgü; genel-geçer değil).
Ayrıca 1-2 cümlelik genel bir summary yaz.
Türkçe, öğrenciye "sen" diliyle, gerçekçi ve pozitif. Konuyu YANLIŞ tanıtma; yalnız
verilen konulara sadık kal. Yalnız JSON döndür."""


def _fallback_title(topic: str) -> str:
    return f"{topic} pekiştirme"


def _fallback_tip(topic: str) -> str:
    return f"Önce {topic} konusunun temel kavramlarını gözden geçir, ardından soruları çöz."


def build_study_plan(
    progress: ProgressResponse, days_target: int = _MAX_DAYS
) -> StudyPlanResponse:
    """Zayıf kazanımlardan haftalık program üretir. weak zaten zayıf→güçlü sıralı."""
    weak = progress.weak[:days_target]
    if not weak:
        if progress.summary.total_answered == 0:
            return StudyPlanResponse(
                summary="Henüz çözümün yok. İlk quizini çöz; eksiklerine göre sana özel "
                "bir haftalık program hazırlayalım.",
                days=[],
            )
        return StudyPlanResponse(
            summary="Şu an belirgin bir zayıf konun görünmüyor — güzel gidiyorsun! "
            "Güçlü olduğun konuları pekiştirmeye ve yeni konulara devam et.",
            days=[],
        )

    days: list[StudyPlanDay] = []
    for i, k in enumerate(weak):
        topic = k.topic_name or k.kazanim_kod or "Bu konu"
        days.append(
            StudyPlanDay(
                day_no=i + 1,
                title=_fallback_title(topic),
                subject=k.subject or "matematik",
                grade=k.grade,
                kazanim_kod=k.kazanim_kod,
                topic_name=topic,
                question_count=_QUESTIONS_PER_DAY,
                tip=_fallback_tip(topic),
                ratio=k.ratio,
            )
        )

    summary = "Eksik olduğun konulara göre hazırlanmış, güne yayılmış bir çalışma programı."
    ai = False
    if settings.gemini_api_key:
        try:
            enrich = _llm_enrich(days)
            if enrich is not None:
                by_no = {d.day_no: d for d in enrich.days}
                for d in days:
                    e = by_no.get(d.day_no)
                    if e is None:
                        continue
                    if e.title.strip():
                        d.title = e.title.strip()
                    if e.tip.strip():
                        d.tip = e.tip.strip()
                if enrich.summary.strip():
                    summary = enrich.summary.strip()
                ai = True
        except Exception as exc:  # noqa: BLE001 — fail-open
            logger.warning("Study plan LLM enrich başarısız (deterministik'e düşüldü): %s", exc)

    return StudyPlanResponse(summary=summary, days=days, ai_generated=ai)


def _llm_enrich(days: list[StudyPlanDay]) -> _PlanEnrich | None:
    client = genai.Client(api_key=settings.gemini_api_key)
    lines = [
        f"Gün {d.day_no}: {d.subject} · {d.grade or '?'}. sınıf · {d.topic_name} "
        f"(mevcut doğruluk %{round(d.ratio * 100)}, {d.question_count} soru önerildi)"
        for d in days
    ]
    prompt = (
        "Öğrencinin zayıf olduğu konular (gün gün):\n"
        + "\n".join(lines)
        + "\n\nHer gün için title ve tip üret; bir de genel summary yaz."
    )
    config = types.GenerateContentConfig(
        system_instruction=_SYSTEM,
        temperature=0.5,
        response_mime_type="application/json",
        response_schema=_PlanEnrich,
    )
    resp = client.models.generate_content(
        model=settings.critic_model, contents=prompt, config=config
    )
    parsed = getattr(resp, "parsed", None)
    if isinstance(parsed, _PlanEnrich):
        return parsed
    text = getattr(resp, "text", None)
    return _PlanEnrich.model_validate_json(text) if text else None
