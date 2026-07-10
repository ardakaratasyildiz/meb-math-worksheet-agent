"""Türkçe dersi plugin'i + uniform içerik arayüzü.

Sınıflar 1-8 (ortaokul 5-8 = LGS). Pragmatik model: üniteler = TEMA, kazanımlar =
sınıf düzeyi çekirdek yetkinlikler + DYS dil bilgisi (bkz. curriculum.py). `enabled`
kalite kapısı feature-flag'ine (Settings.turkce_enabled) bağlı; parite öncesi kapalı.
"""
from __future__ import annotations

import random

from app.config import settings
from app.models.enums import QuestionType, SubjectId
from app.subjects.base import SubjectPlugin
from app.subjects.turkce import curriculum
from app.subjects.turkce.critic import CRITIC_SYSTEM_PROMPT
from app.subjects.turkce.curriculum import (
    GRADE_KAZANIMLAR,
    TURKCE_CURRICULUM,
    TrKazanim,
    TrUnit,
    find_unit_by_kazanim,
    get_unit,
    get_unit_kazanim,
    get_units_for_grade,
    is_unit_available,
)
from app.subjects.turkce.few_shot import TR_EXAMPLES as EXAMPLES
from app.subjects.turkce.prompt import (
    GENERIC_DIFFICULTY_HINT,
    SYSTEM_PROMPT,
    YENI_NESIL_BLOCK,
)

TURKCE = SubjectPlugin(
    id=SubjectId.TURKCE,
    display_name="Türkçe",
    slug="turkce",
    grades=tuple(sorted(TURKCE_CURRICULUM.keys())),
    enabled=settings.turkce_enabled,
)

DEFAULT_TYPES: list[QuestionType] = [
    QuestionType.OKUMA_PASAJI,
    QuestionType.KELIME_BILGISI,
    QuestionType.DIL_BILGISI,
    QuestionType.YAZIM_NOKTALAMA,
    QuestionType.COKTAN_SECMELI,
    QuestionType.ESLESTIRME,
    QuestionType.SIRALAMA,
]


def select_kazanimlar(
    grade: int, unit_id: str | None, kazanim_kod: str | None
) -> tuple[list[dict], str]:
    if not unit_id:
        raise ValueError("Türkçe üretimi tema bazlıdır: unit_id zorunlu.")
    unit = get_unit(grade, unit_id)
    if unit is None:
        raise ValueError(f"{grade}. sınıf Türkçe'de '{unit_id}' teması bulunmuyor.")
    if kazanim_kod is None:
        return list(unit["kazanimlar"]), unit["name"]
    for k in unit["kazanimlar"]:
        if k["kod"] == kazanim_kod:
            return [k], unit["name"]
    raise ValueError(
        f"'{kazanim_kod}' kodu {grade}. sınıf Türkçe kazanımları arasında bulunamadı."
    )


def collect_few_shot(
    grade: int,
    kazanimlar: list[dict],
    target_difficulty: str,
    max_total: int,
    rng: random.Random,
) -> list[dict]:
    by_kod = EXAMPLES.get(grade, {})
    pool: list[dict] = []
    for k in kazanimlar:
        pool.extend(by_kod.get(k["kod"], []))
    pool.sort(
        key=lambda e: (0 if e.get("difficulty") == target_difficulty else 1, rng.random())
    )
    return pool[:max_total]


__all__ = [
    "TURKCE",
    "TURKCE_CURRICULUM",
    "GRADE_KAZANIMLAR",
    "EXAMPLES",
    "CRITIC_SYSTEM_PROMPT",
    "SYSTEM_PROMPT",
    "YENI_NESIL_BLOCK",
    "GENERIC_DIFFICULTY_HINT",
    "DEFAULT_TYPES",
    "TrKazanim",
    "TrUnit",
    "curriculum",
    "select_kazanimlar",
    "collect_few_shot",
    "find_unit_by_kazanim",
    "get_unit",
    "get_unit_kazanim",
    "get_units_for_grade",
    "is_unit_available",
]
