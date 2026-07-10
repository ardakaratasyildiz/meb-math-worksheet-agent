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

from app.config import settings
from app.models.enums import SubjectId
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
