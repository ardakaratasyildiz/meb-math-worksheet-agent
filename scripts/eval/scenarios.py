"""A/B değerlendirmesi için kapsamlı senaryo seti.

Çeşitli (grade, topic, kazanim, difficulty) kombinasyonları —
Sprint 1+2 değişikliklerinin farklı bağlamlarda nasıl davrandığını gör.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.models.enums import Difficulty


@dataclass(frozen=True)
class Scenario:
    grade: int
    topic_id: str
    kazanim_kod: str
    difficulty: Difficulty
    label: str  # rapor/log için kısa isim


SCENARIOS: list[Scenario] = [
    Scenario(
        grade=1,
        topic_id="dogal_sayilar",
        kazanim_kod="M.1.1.1",
        difficulty=Difficulty.KOLAY,
        label="g1_dogal_kolay",
    ),
    Scenario(
        grade=2,
        topic_id="dogal_sayilar",
        kazanim_kod="M.2.1.1",
        difficulty=Difficulty.KOLAY,
        label="g2_dogal_kolay",
    ),
    Scenario(
        grade=5,
        topic_id="cebir",
        kazanim_kod="M.5.5.1",
        difficulty=Difficulty.ORTA,
        label="g5_cebir_orta",
    ),
    Scenario(
        grade=3,
        topic_id="dogal_sayilar",
        kazanim_kod="M.3.1.1",
        difficulty=Difficulty.KOLAY,
        label="g3_dogal_kolay",
    ),
    Scenario(
        grade=6,
        topic_id="kesirler",
        kazanim_kod="M.6.2.3",
        difficulty=Difficulty.ZOR,
        label="g6_kesir_zor",
    ),
    Scenario(
        grade=7,
        topic_id="veri_isleme",
        kazanim_kod="M.7.6.1",
        difficulty=Difficulty.ORTA,
        label="g7_veri_orta",
    ),
]
