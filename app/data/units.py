"""MEB TYMM (Türkiye Yüzyılı Maarif Modeli) ünite (TEMA) katmanı.

Uygulama seçim + üretim akışı sınıf → **ünite (tema)** → kazanım şeklinde çalışır.
Veri kaynağı `app/data/units.json`; MEB öğretim programından (tymm.meb.gov.tr)
kazınıp `scripts/build_units.py` ile üretilir (TEK komut, elle düzenleme YOK).

Köprü (crosswalk): her ünite/kazanım bir eski `topic_id`'ye (`legacy_topic_id`)
eşlenir → ChromaDB + few-shot havuzu yeniden etiketlenmeden RAG/tip-dağılımı eski
kod yollarını aynen kullanır. Bkz. `resolve_legacy_topic`.

Kazanım kod formatı: MAT.{sınıf}.{tema}.{kazanım_no}  (örn. "MAT.7.1.1")
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import NotRequired, TypedDict

_DATA_PATH = Path(__file__).resolve().parent / "units.json"


class UnitKazanim(TypedDict):
    kod: str
    metin: str
    legacy_topic_id: str
    difficulty_hints: NotRequired[dict[str, str]]


class Unit(TypedDict):
    unit_id: str          # kararlı slug, örn. "mat-7-tema-1-sayilar-ve-nicelikler-1"
    unite_id: int         # MEB kaynak id (izlenebilirlik)
    grade: int
    no: int               # tema sırası
    name: str             # temizlenmiş tema adı
    legacy_topic_id: str  # tema → eski konu köprüsü (varsayılan)
    kazanimlar: list[UnitKazanim]


def _load() -> dict[int, list[Unit]]:
    if not _DATA_PATH.exists():
        return {}
    raw = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    return {int(g): units for g, units in raw.items()}


# grade → sıralı üniteler
UNITS: dict[int, list[Unit]] = _load()


def get_units_for_grade(grade: int) -> list[Unit]:
    return list(UNITS.get(grade, []))


def get_unit(grade: int, unit_id: str) -> Unit | None:
    for u in UNITS.get(grade, []):
        if u["unit_id"] == unit_id:
            return u
    return None


def get_unit_kazanim(grade: int, unit_id: str, kazanim_kod: str) -> UnitKazanim | None:
    unit = get_unit(grade, unit_id)
    if unit is None:
        return None
    for k in unit["kazanimlar"]:
        if k["kod"] == kazanim_kod:
            return k
    return None


def resolve_legacy_topic(
    grade: int, unit_id: str, kazanim_kod: str | None = None
) -> str | None:
    """Ünite/kazanım → eski topic_id (RAG + tip-dağılımı köprüsü).

    kazanim_kod verilirse o kazanımın konusu; yoksa ünitenin varsayılan konusu.
    """
    unit = get_unit(grade, unit_id)
    if unit is None:
        return None
    if kazanim_kod is not None:
        for k in unit["kazanimlar"]:
            if k["kod"] == kazanim_kod:
                return k.get("legacy_topic_id", unit["legacy_topic_id"])
    return unit["legacy_topic_id"]


def find_unit_by_kazanim(kazanim_kod: str) -> tuple[int, Unit] | None:
    """Kazanım kodundan (grade, unit) çözer — regenerate / rollup için."""
    for grade, units in UNITS.items():
        for u in units:
            for k in u["kazanimlar"]:
                if k["kod"] == kazanim_kod:
                    return grade, u
    return None


def is_unit_available(grade: int, unit_id: str) -> bool:
    return get_unit(grade, unit_id) is not None
