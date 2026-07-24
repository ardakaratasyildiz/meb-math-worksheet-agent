"""Fen Bilimleri dersi plugin'i (ilk yeni ders).

Sınıflar 3-8 (bkz. docs/FEN_UNITE_YAPISI.md). `enabled`, kalite kapısı
feature-flag'ine (Settings.fen_enabled) bağlıdır: Fen içeriği matematik
paritesine gelene kadar (docs/FEN_BILIMLERI_PLAN.md Faz 6) üretim/rotalar
canlıda AÇILMAZ.

İçerik: `curriculum.py` (ünite + kazanım, 2024 TYMM'den türetildi;
`scripts/derive_fen_curriculum.py`). prompt / few_shot / critic sonraki
alt-adımlarda eklenecek.
"""
from __future__ import annotations

import random

from app.config import settings
from app.models.enums import QuestionType, SubjectId
from app.subjects.base import SubjectPlugin
from app.subjects.fen import curriculum
from app.subjects.fen.critic import CRITIC_SYSTEM_PROMPT
from app.subjects.fen.curriculum import (
    FEN_CURRICULUM,
    FenKazanim,
    FenUnit,
    find_unit_by_kazanim,
    get_unit,
    get_unit_kazanim,
    get_units_for_grade,
    is_unit_available,
)
from app.subjects.fen.few_shot import FEN_EXAMPLES
from app.subjects.fen.prompt import (
    GENERIC_DIFFICULTY_HINT,
    SYSTEM_PROMPT,
    YENI_NESIL_BLOCK,
)

FEN = SubjectPlugin(
    id=SubjectId.FEN,
    display_name="Fen Bilimleri",
    slug="fen",
    grades=tuple(sorted(FEN_CURRICULUM.keys())),
    enabled=settings.fen_enabled,
)

# ── Uniform içerik arayüzü (agent plugin-driven akışının kullandığı) ──────────
# Fen varsayılan soru tipleri (kullanıcı tip seçmediyse): metin + görselli
# (math'e özgü islem/salt_islem hariç).
DEFAULT_TYPES: list[QuestionType] = [
    QuestionType.COKTAN_SECMELI,
    QuestionType.DOGRU_YANLIS,
    QuestionType.BOSLUK_DOLDURMA,
    QuestionType.ESLESTIRME,
    QuestionType.TABLO_SORUSU,
    QuestionType.GRAFIK_OKUMA,
]
# NOT (Fen A, 2026-07): GORSEL_GEOMETRI (ham <svg> bilimsel diyagram) DEFAULT'tan
# ÇIKARILDI — model devre/Punnett/hücre gibi diyagramları güvenilir SVG üretemiyordu
# (figür drop'u). Fen görselleri artık {{table}}/{{chart}} + metin betimleme ile
# karşılanır (bkz. prompt.py). Kullanıcı açıkça question_types ile isterse yine üretilir.


def select_kazanimlar(
    grade: int, unit_id: str | None, kazanim_kod: str | None
) -> tuple[list[dict], str]:
    """Ünite kazanımlarını seçer → (kazanimlar, display_name). Fen ünite bazlıdır."""
    if not unit_id:
        raise ValueError("Fen üretimi ünite bazlıdır: unit_id zorunlu.")
    unit = get_unit(grade, unit_id)
    if unit is None:
        raise ValueError(f"{grade}. sınıf Fen'de '{unit_id}' ünitesi bulunmuyor.")
    if kazanim_kod is None:
        return list(unit["kazanimlar"]), unit["name"]
    for k in unit["kazanimlar"]:
        if k["kod"] == kazanim_kod:
            return [k], unit["name"]
    raise ValueError(
        f"'{kazanim_kod}' kodu {grade}. sınıf Fen '{unit_id}' ünitesinde bulunamadı."
    )


def collect_few_shot(
    grade: int,
    kazanimlar: list[dict],
    target_difficulty: str,
    max_total: int,
    rng: random.Random,
) -> list[dict]:
    """Statik few-shot (gerçek MEB LGS soruları). RAG yok. Hedef zorluk önce."""
    by_kod = FEN_EXAMPLES.get(grade, {})
    pool: list[dict] = []
    for k in kazanimlar:
        pool.extend(by_kod.get(k["kod"], []))
    seen: set[str] = set()
    uniq: list[dict] = []
    for ex in pool:
        key = ex.get("question", "")[:80]
        if key in seen:
            continue
        seen.add(key)
        uniq.append(ex)
    uniq.sort(
        key=lambda e: (0 if e.get("difficulty") == target_difficulty else 1, rng.random())
    )
    return uniq[:max_total]

__all__ = [
    "FEN",
    "FEN_CURRICULUM",
    "FEN_EXAMPLES",
    "CRITIC_SYSTEM_PROMPT",
    "SYSTEM_PROMPT",
    "YENI_NESIL_BLOCK",
    "GENERIC_DIFFICULTY_HINT",
    "FenKazanim",
    "FenUnit",
    "curriculum",
    "find_unit_by_kazanim",
    "get_unit",
    "get_unit_kazanim",
    "get_units_for_grade",
    "is_unit_available",
]
