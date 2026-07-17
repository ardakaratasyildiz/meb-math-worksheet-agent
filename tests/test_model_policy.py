"""Model + thinking seçim politikası (model_for / thinking_for_model /
model_and_thinking_for) testleri — 2026-07 maliyet optimizasyonu.

Politika: 1-4→ucuz · geometri→güçlü · 8+premium→güçlü · 5-7+premium+ZOR→güçlü ·
diğer→ucuz. thinking: 1-4→0, 5-7(ucuz)→512, 8(ucuz)→-1, güçlü model→-1.
"""
import pytest

from app.config import settings
from app.models.enums import Difficulty, SubjectId
from app.services.agent import (
    is_geometry_theme,
    model_and_thinking_for,
    model_for,
    thinking_for_model,
)

CHEAP = settings.gemini_model_grade_1_4   # 2.5-flash
STRONG = settings.gemini_model_grade_5_8  # 3.5-flash


@pytest.mark.parametrize("grade", [1, 2, 3, 4])
def test_grades_1_4_always_cheap(grade):
    for prem in (False, True):
        for diff in Difficulty:
            assert model_for(grade, is_geometry=False, difficulty=diff, is_premium=prem) == CHEAP


def test_geometry_always_strong_5_8():
    for grade in (5, 6, 7, 8):
        for prem in (False, True):
            assert model_for(grade, is_geometry=True, difficulty=Difficulty.KOLAY, is_premium=prem) == STRONG


def test_grade_8_premium_gate():
    # Ücretsiz 8 (geometri dışı) → ucuz; premium 8 → güçlü (komple).
    assert model_for(8, is_geometry=False, difficulty=Difficulty.ORTA, is_premium=False) == CHEAP
    assert model_for(8, is_geometry=False, difficulty=Difficulty.ORTA, is_premium=True) == STRONG


def test_grade_5_7_premium_zor_only():
    # Ücretsiz 5-7 → hep ucuz.
    for diff in Difficulty:
        assert model_for(6, is_geometry=False, difficulty=diff, is_premium=False) == CHEAP
    # Premium 5-7: yalnız ZOR güçlü, kolay/orta ucuz.
    assert model_for(6, is_geometry=False, difficulty=Difficulty.KOLAY, is_premium=True) == CHEAP
    assert model_for(6, is_geometry=False, difficulty=Difficulty.ORTA, is_premium=True) == CHEAP
    assert model_for(6, is_geometry=False, difficulty=Difficulty.ZOR, is_premium=True) == STRONG


def test_thinking_budget_policy():
    assert thinking_for_model(3, CHEAP) == 0
    assert thinking_for_model(6, CHEAP) == 512
    assert thinking_for_model(8, CHEAP) == -1
    # Güçlü model her sınıfta dinamik (kaliteyi koru).
    assert thinking_for_model(6, STRONG) == -1
    assert thinking_for_model(8, STRONG) == -1


def test_geometry_detection_math_only():
    assert is_geometry_theme(SubjectId.MATEMATIK, 6, "geometri", None) is True
    assert is_geometry_theme(SubjectId.MATEMATIK, 6, "cebir", None) is False
    # Non-math derste geometri teması yok.
    assert is_geometry_theme(SubjectId.FEN, 6, "geometri", None) is False


def test_model_and_thinking_together():
    # Ücretsiz 6 geometri → güçlü + dinamik.
    m, tb = model_and_thinking_for(6, subject=SubjectId.MATEMATIK, topic_id="geometri",
                                   unit_id=None, difficulty=Difficulty.KOLAY, is_premium=False)
    assert (m, tb) == (STRONG, -1)
    # Ücretsiz 6 cebir → ucuz + 512.
    m, tb = model_and_thinking_for(6, subject=SubjectId.MATEMATIK, topic_id="cebir",
                                   unit_id=None, difficulty=Difficulty.ORTA, is_premium=False)
    assert (m, tb) == (CHEAP, 512)
    # Ücretsiz 3 → ucuz + 0.
    m, tb = model_and_thinking_for(3, subject=SubjectId.MATEMATIK, topic_id="dogal_sayilar",
                                   unit_id=None, difficulty=Difficulty.KOLAY, is_premium=False)
    assert (m, tb) == (CHEAP, 0)


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-q"]))
