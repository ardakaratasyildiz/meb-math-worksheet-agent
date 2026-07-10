"""Ders (subject) registry — çok-ders ekseninin tek giriş noktası.

Kullanım:
    from app.models.enums import SubjectId
    from app.subjects import get_subject, subject_enabled, available_subjects, get_content_module

`get_subject()` varsayılan matematik döner → subject verilmeyen eski çağrılar aynen çalışır.
`subject_enabled()` feature-flag'i SETTINGS'TEN CANLI okur (import-time snapshot değil) →
env/flag flip'i yeniden import gerektirmez. Router'lar kapalı derse 4xx döndürmeli.
`get_content_module()` non-math dersin içerik modülünü (prompt/critic/few-shot/curriculum +
select_kazanimlar/collect_few_shot/DEFAULT_TYPES uniform arayüzü) döner; matematik → None
(matematik akışı kendi klasik yolunu kullanır).

Yeni ders eklemek: paket oluştur (uniform arayüzle) → burada SUBJECTS + SUBJECT_FLAGS +
_CONTENT'e kaydet. Gerisi (agent/router/frontend) otomatik.

bkz. docs/FEN_BILIMLERI_PLAN.md, docs/SOZEL_DERSLER_PLAN.md.
"""
from __future__ import annotations

from types import ModuleType

from app.config import settings
from app.models.enums import SubjectId
from app.subjects import fen as _fen_mod
from app.subjects import ingilizce as _ing_mod
from app.subjects.base import SubjectPlugin
from app.subjects.fen import FEN
from app.subjects.ingilizce import INGILIZCE
from app.subjects.matematik import MATEMATIK

SUBJECTS: dict[SubjectId, SubjectPlugin] = {
    SubjectId.MATEMATIK: MATEMATIK,
    SubjectId.FEN: FEN,
    SubjectId.INGILIZCE: INGILIZCE,
}

# Ders → Settings feature-flag alan adı (matematik her zaman açık, flag yok).
SUBJECT_FLAGS: dict[SubjectId, str] = {
    SubjectId.FEN: "fen_enabled",
    SubjectId.TURKCE: "turkce_enabled",
    SubjectId.SOSYAL: "sosyal_enabled",
    SubjectId.INGILIZCE: "ingilizce_enabled",
}

# Ders → içerik modülü (uniform arayüz: SYSTEM_PROMPT/CRITIC_SYSTEM_PROMPT/
# YENI_NESIL_BLOCK/DEFAULT_TYPES/EXAMPLES + select_kazanimlar/collect_few_shot +
# get_units_for_grade/get_unit/find_unit_by_kazanim). Matematik yok (klasik yol).
_CONTENT: dict[SubjectId, ModuleType] = {
    SubjectId.FEN: _fen_mod,
    SubjectId.INGILIZCE: _ing_mod,
}


def get_subject(subject_id: SubjectId = SubjectId.MATEMATIK) -> SubjectPlugin:
    return SUBJECTS.get(subject_id, MATEMATIK)


def subject_enabled(subject_id: SubjectId) -> bool:
    """Ders canlıda açık mı — feature-flag SETTINGS'ten CANLI okunur. Matematik hep açık."""
    if subject_id == SubjectId.MATEMATIK:
        return True
    flag = SUBJECT_FLAGS.get(subject_id)
    return bool(flag and getattr(settings, flag, False))


def is_enabled(subject_id: SubjectId) -> bool:
    """subject_enabled ile aynı (geriye uyum adı)."""
    return subject_enabled(subject_id)


def get_content_module(subject_id: SubjectId) -> ModuleType | None:
    """Non-math dersin içerik modülü; matematik/tanımsız → None."""
    return _CONTENT.get(subject_id)


def available_subjects(include_disabled: bool = False) -> list[SubjectPlugin]:
    """Aktif dersler (varsayılan, flag canlı). include_disabled=True → hepsi."""
    return [
        s
        for sid, s in SUBJECTS.items()
        if include_disabled or subject_enabled(sid)
    ]


__all__ = [
    "SubjectPlugin",
    "SUBJECTS",
    "SUBJECT_FLAGS",
    "get_subject",
    "subject_enabled",
    "is_enabled",
    "get_content_module",
    "available_subjects",
]
