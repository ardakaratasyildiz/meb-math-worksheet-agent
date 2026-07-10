"""Ders (subject) registry — çok-ders ekseninin tek giriş noktası.

Kullanım:
    from app.models.enums import SubjectId
    from app.subjects import get_subject, is_enabled, available_subjects

`get_subject()` varsayılan matematik döner → subject verilmeyen eski çağrılar
aynen çalışır. Fen gibi feature-flag'li derslerin canlıda açık olup olmadığını
`is_enabled()` ile kontrol edin (router'lar kapalı derse 4xx döndürmeli).

bkz. docs/FEN_BILIMLERI_PLAN.md (Faz 0).
"""
from __future__ import annotations

from app.models.enums import SubjectId
from app.subjects.base import SubjectPlugin
from app.subjects.fen import FEN
from app.subjects.matematik import MATEMATIK

SUBJECTS: dict[SubjectId, SubjectPlugin] = {
    SubjectId.MATEMATIK: MATEMATIK,
    SubjectId.FEN: FEN,
}


def get_subject(subject_id: SubjectId = SubjectId.MATEMATIK) -> SubjectPlugin:
    """Ders plugin'ini döner. Bilinmeyen id (teorik) → matematik'e düşer."""
    return SUBJECTS.get(subject_id, MATEMATIK)


def is_enabled(subject_id: SubjectId) -> bool:
    """Ders canlıda açık mı (feature-flag). Kapalıysa üretim reddedilmeli."""
    plugin = SUBJECTS.get(subject_id)
    return bool(plugin and plugin.enabled)


def available_subjects(include_disabled: bool = False) -> list[SubjectPlugin]:
    """Aktif dersler (varsayılan). include_disabled=True → hepsi (admin/staging)."""
    return [s for s in SUBJECTS.values() if include_disabled or s.enabled]


__all__ = [
    "SubjectPlugin",
    "SUBJECTS",
    "get_subject",
    "is_enabled",
    "available_subjects",
]
