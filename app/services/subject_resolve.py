"""kazanim_kod → (ders, okunur konu adı, sınıf) — ortak çözümleme.

İlerleme panosu ders-bazlı gruplama için her kazanım kodunu TEK yoldan çözer.
Veritabanında `subject` saklanmaz; kazanım kodu zaten dersi + sınıfı taşır
(M./MAT. = matematik, FB./F. = fen, T. = türkçe, SB. = sosyal, E# = ingilizce).
Bu sayede eski (hepsi matematik) satırlar da, yeni ders satırları da migrasyonsuz
çözülür.

Çözüm sırası (ilk eşleşen kazanır):
  1) matematik ünite (MAT.*)      → app.data.units.find_unit_by_kazanim
  2) matematik legacy (M.*)       → app.data.curriculum.CURRICULUM taraması
  3) her matematik-dışı ders      → <ders>.find_unit_by_kazanim (uniform arayüz)
  4) fallback                     → koddan prefix/sınıf türet, konu adı "Genel"
"""
from __future__ import annotations

import re
from functools import lru_cache

from app.data import units as _math_units
from app.data.curriculum import CURRICULUM as _MATH_CURRICULUM
from app.models.enums import SubjectId
from app.subjects import SUBJECT_FLAGS, get_content_module

# Prefix → ders (yalnız fallback; gerçek kodlar zaten curriculum'dan çözülür).
# Sıra önemli: daha uzun/özel prefix önce ("MAT." > "M.", "TR." > "T.").
_PREFIX_SUBJECT: list[tuple[str, SubjectId]] = [
    ("MAT.", SubjectId.MATEMATIK),
    ("M.", SubjectId.MATEMATIK),
    ("FB.", SubjectId.FEN),
    ("F.", SubjectId.FEN),
    ("TR.", SubjectId.TURKCE),
    ("T.", SubjectId.TURKCE),
    ("İTA.", SubjectId.SOSYAL),
    ("ITA.", SubjectId.SOSYAL),
    ("SOS.", SubjectId.SOSYAL),
    ("SB.", SubjectId.SOSYAL),
    ("ENG.", SubjectId.INGILIZCE),
]


def _grade_from_kod(kod: str) -> int | None:
    """Koddan sınıfı çıkarır: 'M.5.2.1'→5, 'FB.8.3.1'→8, 'E5.3'→5."""
    m = re.search(r"\.(\d+)\.", kod)  # X.<grade>.Y
    if m:
        g = int(m.group(1))
        return g if 1 <= g <= 8 else None
    m2 = re.search(r"[A-Za-z](\d)", kod)  # E5.3 → 5
    if m2:
        g = int(m2.group(1))
        return g if 1 <= g <= 8 else None
    return None


def _subject_from_prefix(kod: str) -> SubjectId:
    up = kod.upper()
    for pfx, sid in _PREFIX_SUBJECT:
        if up.startswith(pfx):
            return sid
    if len(up) > 1 and up[0] == "E" and up[1].isdigit():
        return SubjectId.INGILIZCE
    return SubjectId.MATEMATIK


def _legacy_math_topic(kod: str) -> tuple[int, str] | None:
    """Legacy matematik kodu (M.*) → (sınıf, konu adı). CURRICULUM taraması."""
    for grade, topics in _MATH_CURRICULUM.items():
        for topic in topics.values():
            for k in topic.get("kazanimlar", []):
                if k.get("kod") == kod:
                    return grade, topic.get("name", "Matematik")
    return None


@lru_cache(maxsize=4096)
def resolve_kazanim(kod: str) -> tuple[SubjectId, str, int | None]:
    """kazanim_kod → (SubjectId, okunur konu/ünite adı, sınıf). Bilinmezse fallback.

    Sonuç kod başına cache'lenir (müfredat statik → güvenli).
    """
    if not kod:
        return SubjectId.MATEMATIK, "Genel", None

    # 1) Matematik ünite (MAT.*)
    mu = _math_units.find_unit_by_kazanim(kod)
    if mu:
        grade, unit = mu
        return SubjectId.MATEMATIK, unit.get("name", "Genel"), grade

    # 2) Matematik legacy (M.*)
    lm = _legacy_math_topic(kod)
    if lm:
        grade, name = lm
        return SubjectId.MATEMATIK, name, grade

    # 3) Matematik-dışı dersler (fen, türkçe, sosyal, ingilizce)
    for sid in SUBJECT_FLAGS:
        mod = get_content_module(sid)
        finder = getattr(mod, "find_unit_by_kazanim", None) if mod else None
        if finder is None:
            continue
        found = finder(kod)
        if found:
            grade, unit = found
            return sid, unit.get("name", "Genel"), grade

    # 4) Fallback — koddan türet
    return _subject_from_prefix(kod), "Genel", _grade_from_kod(kod)
