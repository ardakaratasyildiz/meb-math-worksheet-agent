"""Matematik dersi plugin'i (ilk/varsayılan ders).

Faz 0: sadece meta. Sınıf aralığı mevcut CURRICULUM'dan türetilir → tek doğruluk
kaynağı korunur (grade 8 GRADE8_LGS_PLAN ile açılınca otomatik yansır).
"""
from __future__ import annotations

from app.data.curriculum import CURRICULUM
from app.models.enums import SubjectId
from app.subjects.base import SubjectPlugin

MATEMATIK = SubjectPlugin(
    id=SubjectId.MATEMATIK,
    display_name="Matematik",
    slug="matematik",
    grades=tuple(sorted(CURRICULUM.keys())),
    enabled=True,
)
