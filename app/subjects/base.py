"""Ders (subject) ekseni — plugin altyapısı (Faz 0).

Her ders bir `SubjectPlugin` ile tanımlanır: kimlik + görünen ad + slug (rota /
ChromaDB metadata anahtarı) + desteklenen sınıflar + feature-flag.

Faz 0 KAPSAMI: yalnızca ders kimliği/meta + registry. İçerik sağlayıcıları
(curriculum, system_prompt, critic_prompt, few_shot, question_types, renderer)
sonraki alt-adımda eklenecek. Bu aşamada **matematik davranışı DEĞİŞMEZ** —
generation pipeline'ı hâlâ mevcut math modüllerini doğrudan kullanır; registry
şimdilik yalnızca subject ekseni + fen feature-flag'i için altyapı sağlar.

bkz. docs/FEN_BILIMLERI_PLAN.md (Faz 0).
"""
from __future__ import annotations

from dataclasses import dataclass

from app.models.enums import SubjectId


@dataclass(frozen=True)
class SubjectPlugin:
    """Bir dersin kimlik + yetenek tanımı. Şimdilik saf metadata (davranış taşımaz)."""

    id: SubjectId
    display_name: str          # UI/SEO görünen ad — "Matematik", "Fen Bilimleri"
    slug: str                  # rota + ChromaDB metadata anahtarı — "matematik", "fen"
    grades: tuple[int, ...]    # desteklenen sınıflar
    enabled: bool              # feature flag: kalite kapısı geçilene kadar False (fen)

    def supports_grade(self, grade: int) -> bool:
        return grade in self.grades
