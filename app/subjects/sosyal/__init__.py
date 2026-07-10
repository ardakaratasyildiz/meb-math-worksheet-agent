"""Sosyal Bilgiler dersi plugin'i + uniform içerik arayüzü.

Kapsam: Hayat Bilgisi (1-3), Sosyal Bilgiler (4-7), 8. sınıf T.C. İnkılap Tarihi (LGS)
— tek `sosyal` dersi altında (sınıf → program otomatik). `enabled` kalite kapısı
feature-flag'ine (Settings.sosyal_enabled) bağlı; parite öncesi canlıda AÇILMAZ.
"""
from __future__ import annotations

import random

from app.config import settings
from app.models.enums import QuestionType, SubjectId
from app.subjects.base import SubjectPlugin
from app.subjects.sosyal import curriculum
from app.subjects.sosyal.critic import CRITIC_SYSTEM_PROMPT
from app.subjects.sosyal.curriculum import (
    SOS_CURRICULUM,
    SosKazanim,
    SosUnit,
    find_unit_by_kazanim,
    get_unit,
    get_unit_kazanim,
    get_units_for_grade,
    is_unit_available,
)
from app.subjects.sosyal.few_shot import SOS_EXAMPLES as EXAMPLES
from app.subjects.sosyal.prompt import (
    GENERIC_DIFFICULTY_HINT,
    SYSTEM_PROMPT,
    YENI_NESIL_BLOCK,
)

SOSYAL = SubjectPlugin(
    id=SubjectId.SOSYAL,
    display_name="Sosyal Bilgiler",
    slug="sosyal",
    grades=tuple(sorted(SOS_CURRICULUM.keys())),
    enabled=settings.sosyal_enabled,
)

# Metin-güvenli varsayılan tipler (harita/görsel realia sonra).
DEFAULT_TYPES: list[QuestionType] = [
    QuestionType.COKTAN_SECMELI,
    QuestionType.DOGRU_YANLIS,
    QuestionType.BOSLUK_DOLDURMA,
    QuestionType.ESLESTIRME,
    QuestionType.SIRALAMA,
    QuestionType.KAYNAK_METIN,
    QuestionType.TABLO_SORUSU,
]


def select_kazanimlar(
    grade: int, unit_id: str | None, kazanim_kod: str | None
) -> tuple[list[dict], str]:
    if not unit_id:
        raise ValueError("Sosyal üretimi ünite bazlıdır: unit_id zorunlu.")
    unit = get_unit(grade, unit_id)
    if unit is None:
        raise ValueError(f"{grade}. sınıf Sosyal'de '{unit_id}' ünitesi bulunmuyor.")
    if kazanim_kod is None:
        return list(unit["kazanimlar"]), unit["name"]
    for k in unit["kazanimlar"]:
        if k["kod"] == kazanim_kod:
            return [k], unit["name"]
    raise ValueError(
        f"'{kazanim_kod}' kodu {grade}. sınıf Sosyal '{unit_id}' ünitesinde bulunamadı."
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
    "SOSYAL",
    "SOS_CURRICULUM",
    "EXAMPLES",
    "CRITIC_SYSTEM_PROMPT",
    "SYSTEM_PROMPT",
    "YENI_NESIL_BLOCK",
    "GENERIC_DIFFICULTY_HINT",
    "DEFAULT_TYPES",
    "SosKazanim",
    "SosUnit",
    "curriculum",
    "select_kazanimlar",
    "collect_few_shot",
    "find_unit_by_kazanim",
    "get_unit",
    "get_unit_kazanim",
    "get_units_for_grade",
    "is_unit_available",
]
