"""Sınıf-bazlı model seçimi (model_for_grade) testleri.

Kural: 1-4. sınıf → gemini_model_grade_1_4 (hafif/ucuz flash 2.5),
       5-8. sınıf → gemini_model_grade_5_8 (güçlü Gemini 3 flash).
"""
import pytest

from app.config import settings
from app.services.agent import model_for_grade


@pytest.mark.parametrize("grade", [1, 2, 3, 4])
def test_lower_grades_use_light_model(grade):
    assert model_for_grade(grade) == settings.gemini_model_grade_1_4


@pytest.mark.parametrize("grade", [5, 6, 7, 8])
def test_upper_grades_use_strong_model(grade):
    assert model_for_grade(grade) == settings.gemini_model_grade_5_8


def test_default_model_strings():
    # Varsayılan politika: 1-4 flash 2.5, 5-8 Gemini 3 flash.
    assert settings.gemini_model_grade_1_4 == "gemini-2.5-flash"
    assert settings.gemini_model_grade_5_8 == "gemini-3.5-flash"


def test_boundary_at_four_five():
    # Sınır: 4 hâlâ hafif, 5 güçlü.
    assert model_for_grade(4) == settings.gemini_model_grade_1_4
    assert model_for_grade(5) == settings.gemini_model_grade_5_8


def test_selected_models_are_priced():
    # Maliyet takibi için seçilen modeller fiyat tablosunda kayıtlı olmalı
    # (aksi halde estimated_cost_usd 0 döner → cost-meter yanlış).
    from app.services.llm_providers import PRICING_USD_PER_1M_TOKENS

    assert settings.gemini_model_grade_1_4 in PRICING_USD_PER_1M_TOKENS
    assert settings.gemini_model_grade_5_8 in PRICING_USD_PER_1M_TOKENS
