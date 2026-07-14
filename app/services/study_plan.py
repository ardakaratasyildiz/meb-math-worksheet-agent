"""AI destekli haftalık çalışma programı (WS-6a).

7 günlük (Pazartesi→Pazar) çeşitli bir program KURULUR — yalnız eksikler değil:
  • odak (focus)   → zayıf kazanımlar (öğrenilecek/pekiştirilecek)
  • tekrar (review)→ daha önce çalışılmış konuların tekrarı (unutmayı önler)
  • karışık (mixed)→ genel/karışık deneme (farklı konulardan)
Gün-gün deterministik kurulur (doğru ders/sınıf/kazanım deep-link'leriyle — LLM link
uydurmaz), sonra bir LLM geçişiyle her güne motive edici başlık/ipucu + özet EKLENİR.
LLM erişilemez/yavaşsa deterministik metne düşülür (fail-open + sıkı timeout) → endpoint
asla LLM yüzünden asılı kalmaz.
"""
from __future__ import annotations

import logging
from collections import deque

from google import genai
from google.genai import types
from pydantic import BaseModel

from app.config import settings
from app.models.schemas import (
    KazanimProgress,
    ProgressResponse,
    StudyPlanDay,
    StudyPlanResponse,
)

logger = logging.getLogger(__name__)

# Haftalık şablon: gün adı + tercih edilen tür. Veri yetmezse tür otomatik düşer
# (focus→review→mixed). Böylece program HER ZAMAN 7 gün, dengeli ve çeşitli.
_WEEK: list[tuple[str, str]] = [
    ("Pazartesi", "focus"),
    ("Salı", "focus"),
    ("Çarşamba", "review"),
    ("Perşembe", "focus"),
    ("Cuma", "mixed"),
    ("Cumartesi", "review"),
    ("Pazar", "mixed"),
]

_Q_BY_KIND = {"focus": 10, "review": 8, "mixed": 12}
_LLM_TIMEOUT_MS = 15_000  # genai çağrısı bu süreyi aşarsa fail-open


class _DayEnrich(BaseModel):
    day_no: int
    title: str
    tip: str


class _PlanEnrich(BaseModel):
    summary: str
    days: list[_DayEnrich]


_SYSTEM = """Sen destekleyici bir öğrenme koçusun. Öğrenciye 7 günlük, çeşitli bir
haftalık çalışma programının metnini yazıyorsun. Sana gün gün: gün adı, TÜR ve konu
verilir. Türler:
- focus: zayıf/eksik konu — pekiştirme günü.
- review: daha önce çalışılmış konunun tekrarı — unutmayı önleme.
- mixed: karışık genel tekrar/deneme — farklı konulardan.
Her gün için:
- title: 3-6 kelimelik, türe uygun, cesaretlendirici ama abartısız başlık.
- tip: tek cümlelik SOMUT çalışma önerisi (o güne/konuya özgü; tekrar günü "hızlı gözden
  geçir", karışık gün "süre tutarak dene" gibi türle uyumlu).
Ayrıca 1-2 cümlelik, haftanın dengesini (öğren + tekrar et + dene) anlatan bir summary yaz.
Türkçe, öğrenciye "sen" diliyle, gerçekçi ve pozitif. Konuyu YANLIŞ tanıtma; yalnız verilen
konulara sadık kal. Yalnız JSON döndür."""


# ── deterministik metin (fail-open) ──────────────────────────────────────────
def _fallback_title(kind: str, topic: str) -> str:
    if kind == "review":
        return f"{topic} tekrarı"
    if kind == "mixed":
        return "Karışık genel tekrar"
    return f"{topic} pekiştirme"


def _fallback_tip(kind: str, topic: str) -> str:
    if kind == "review":
        return f"{topic} konusunu hızlıca gözden geçir, birkaç soruyla hatırla."
    if kind == "mixed":
        return "Farklı konulardan karışık sorularla, süre tutarak kendini dene."
    return f"Önce {topic} konusunun temel kavramlarını gözden geçir, ardından soruları çöz."


def _topic_of(k: KazanimProgress) -> str:
    return k.topic_name or k.kazanim_kod or "Bu konu"


def _dominant_subject(mastery: list[KazanimProgress]) -> tuple[str, int | None]:
    """Karışık günler için en çok çalışılan ders (+ o dersteki en çok çalışılan sınıf)."""
    if not mastery:
        return "matematik", None
    by_subj: dict[str, int] = {}
    for m in mastery:
        by_subj[m.subject or "matematik"] = by_subj.get(m.subject or "matematik", 0) + m.total
    subject = max(by_subj, key=lambda s: by_subj[s])
    grade = next((m.grade for m in mastery if (m.subject or "matematik") == subject and m.grade), None)
    return subject, grade


def build_study_plan(
    progress: ProgressResponse, days_target: int = len(_WEEK)
) -> StudyPlanResponse:
    """Zayıf + tekrar + karışık karışımından 7 günlük çeşitli program üretir."""
    if progress.summary.total_answered == 0:
        return StudyPlanResponse(
            summary="Henüz çözümün yok. İlk quizini çöz; eksiklerine göre sana özel "
            "bir haftalık program hazırlayalım.",
            days=[],
        )

    weak_q: deque[KazanimProgress] = deque(progress.weak)
    weak_codes = {k.kazanim_kod for k in progress.weak}
    # Tekrar havuzu: zayıf OLMAYAN, yeterince çalışılmış kazanımlar (güçlü→zayıf sırada,
    # güvenle tekrar edilecekler önce). progress.mastery zaten zayıf→güçlü sıralı.
    review_q: deque[KazanimProgress] = deque(
        k
        for k in reversed(progress.mastery)
        if k.kazanim_kod not in weak_codes and k.total >= 1
    )
    dom_subject, dom_grade = _dominant_subject(progress.mastery)

    days: list[StudyPlanDay] = []
    for i, (weekday, pref) in enumerate(_WEEK[:days_target]):
        kind = pref
        item: KazanimProgress | None = None

        if pref == "focus":
            if weak_q:
                item = weak_q.popleft()
            elif review_q:
                item, kind = review_q.popleft(), "review"
            else:
                kind = "mixed"
        elif pref == "review":
            if review_q:
                item = review_q.popleft()
            elif weak_q:
                item, kind = weak_q.popleft(), "focus"
            else:
                kind = "mixed"
        # pref == "mixed" → item None, kind mixed

        if item is not None:
            topic = _topic_of(item)
            days.append(
                StudyPlanDay(
                    day_no=i + 1,
                    weekday=weekday,
                    kind=kind,
                    title=_fallback_title(kind, topic),
                    subject=item.subject or "matematik",
                    grade=item.grade,
                    kazanim_kod=item.kazanim_kod,
                    topic_name=topic,
                    question_count=_Q_BY_KIND[kind],
                    tip=_fallback_tip(kind, topic),
                    ratio=item.ratio,
                )
            )
        else:  # karışık genel tekrar — tek kazanıma bağlı değil
            days.append(
                StudyPlanDay(
                    day_no=i + 1,
                    weekday=weekday,
                    kind="mixed",
                    title=_fallback_title("mixed", ""),
                    subject=dom_subject,
                    grade=dom_grade,
                    kazanim_kod="",
                    topic_name="Karışık genel tekrar",
                    question_count=_Q_BY_KIND["mixed"],
                    tip=_fallback_tip("mixed", ""),
                    ratio=0.0,
                )
            )

    summary = (
        "Haftaya yayılmış dengeli bir program: eksik konularını pekiştir, "
        "öğrendiklerini tekrar et ve karışık sorularla kendini dene."
    )
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
        except Exception as exc:  # noqa: BLE001 — fail-open (LLM asla endpoint'i düşürmez)
            logger.warning("Study plan LLM enrich başarısız (deterministik'e düşüldü): %s", exc)

    return StudyPlanResponse(summary=summary, days=days, ai_generated=ai)


def _llm_enrich(days: list[StudyPlanDay]) -> _PlanEnrich | None:
    # Sıkı timeout: yavaş/asılı LLM çağrısı endpoint'i bekletmesin (fail-open'a düşer).
    client = genai.Client(
        api_key=settings.gemini_api_key,
        http_options=types.HttpOptions(timeout=_LLM_TIMEOUT_MS),
    )
    lines = [
        f"Gün {d.day_no} ({d.weekday}) · tür={d.kind} · "
        + (
            f"{d.subject} · {d.grade or '?'}. sınıf · {d.topic_name} "
            f"(mevcut doğruluk %{round(d.ratio * 100)})"
            if d.kind != "mixed"
            else "karışık genel tekrar (farklı konulardan)"
        )
        for d in days
    ]
    prompt = (
        "7 günlük haftalık program (gün gün):\n"
        + "\n".join(lines)
        + "\n\nHer gün için türe uygun title ve tip üret; bir de genel summary yaz."
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
