"""İngilizce dersi plugin'i + uniform içerik arayüzü (agent plugin-driven akışı).

Sınıflar 2-8 (ortaokul 5-8 = LGS). İçerik İNGİLİZCE üretilir. `enabled` kalite
kapısı feature-flag'ine (Settings.ingilizce_enabled) bağlıdır — İngilizce, matematik/
fen paritesine gelene kadar canlıda AÇILMAZ (docs/SOZEL_DERSLER_PLAN.md).

Uniform arayüz (agent + registry bunları bekler): SYSTEM_PROMPT, CRITIC_SYSTEM_PROMPT,
YENI_NESIL_BLOCK, DEFAULT_TYPES, EXAMPLES, select_kazanimlar, collect_few_shot,
get_units_for_grade, get_unit, find_unit_by_kazanim.
"""
from __future__ import annotations

import random

from app.config import settings
from app.models.enums import QuestionType, SubjectId
from app.subjects.base import SubjectPlugin
from app.subjects.ingilizce import curriculum
from app.subjects.ingilizce.critic import CRITIC_SYSTEM_PROMPT
from app.subjects.ingilizce.curriculum import (
    ING_CURRICULUM,
    IngKazanim,
    IngUnit,
    find_unit_by_kazanim,
    get_unit,
    get_unit_kazanim,
    get_units_for_grade,
    is_unit_available,
)
from app.subjects.ingilizce.few_shot import ING_EXAMPLES as EXAMPLES
from app.subjects.ingilizce.prompt import (
    GENERIC_DIFFICULTY_HINT,
    SYSTEM_PROMPT,
    YENI_NESIL_BLOCK,
)

INGILIZCE = SubjectPlugin(
    id=SubjectId.INGILIZCE,
    display_name="İngilizce",
    slug="ingilizce",
    grades=tuple(sorted(ING_CURRICULUM.keys())),
    enabled=settings.ingilizce_enabled,
)

# İngilizce varsayılan soru tipleri (metin-güvenli MVP; görsel realia sonra).
DEFAULT_TYPES: list[QuestionType] = [
    QuestionType.COKTAN_SECMELI,
    QuestionType.KELIME_BILGISI,
    QuestionType.DIYALOG_TAMAMLAMA,
    QuestionType.OKUMA_PASAJI,
    QuestionType.BOSLUK_DOLDURMA,
    QuestionType.ESLESTIRME,
]


def select_kazanimlar(
    grade: int, unit_id: str | None, kazanim_kod: str | None
) -> tuple[list[dict], str]:
    """Tema kazanımlarını seçer → (kazanimlar, display_name). İngilizce tema bazlıdır."""
    if not unit_id:
        raise ValueError("İngilizce üretimi tema bazlıdır: unit_id zorunlu.")
    unit = get_unit(grade, unit_id)
    if unit is None:
        raise ValueError(f"{grade}. sınıf İngilizce'de '{unit_id}' teması bulunmuyor.")
    if kazanim_kod is None:
        return list(unit["kazanimlar"]), unit["name"]
    for k in unit["kazanimlar"]:
        if k["kod"] == kazanim_kod:
            return [k], unit["name"]
    raise ValueError(
        f"'{kazanim_kod}' kodu {grade}. sınıf İngilizce '{unit_id}' temasında bulunamadı."
    )


def collect_few_shot(
    grade: int,
    kazanimlar: list[dict],
    target_difficulty: str,
    max_total: int,
    rng: random.Random,
) -> list[dict]:
    """Statik few-shot (EXAMPLES). MVP'de boş → []. RAG yok."""
    by_kod = EXAMPLES.get(grade, {})
    pool: list[dict] = []
    for k in kazanimlar:
        pool.extend(by_kod.get(k["kod"], []))
    pool.sort(
        key=lambda e: (0 if e.get("difficulty") == target_difficulty else 1, rng.random())
    )
    return pool[:max_total]


__all__ = [
    "INGILIZCE",
    "ING_CURRICULUM",
    "EXAMPLES",
    "CRITIC_SYSTEM_PROMPT",
    "SYSTEM_PROMPT",
    "YENI_NESIL_BLOCK",
    "GENERIC_DIFFICULTY_HINT",
    "DEFAULT_TYPES",
    "IngKazanim",
    "IngUnit",
    "curriculum",
    "select_kazanimlar",
    "collect_few_shot",
    "find_unit_by_kazanim",
    "get_unit",
    "get_unit_kazanim",
    "get_units_for_grade",
    "is_unit_available",
]
