"""Few-shot örneklerini kazanım koduna + zorluğa + isteğe göre seçen yardımcı.

Seçim skorlaması (en yüksek öncelikli):
    +10  hedef zorlukla eşleşme (target_difficulty)
    + 5  tercih edilen tiplerden biri (preferred_types)
    + 0-0.99 rastgele tiebreak
"""
import random

from app.data.few_shot import EXAMPLES_BY_GRADE
from app.models.enums import QuestionType


def _score(
    example: dict,
    target_difficulty: str | None,
    preferred_types: list[QuestionType] | None,
    rng: random.Random,
) -> float:
    score = rng.random()
    if target_difficulty is not None and example.get("difficulty") == target_difficulty:
        score += 10.0
    if preferred_types and example.get("type") in preferred_types:
        score += 5.0
    return score


def get_examples_for_kazanim(
    grade: int,
    kazanim_kod: str,
    max_count: int = 3,
    preferred_types: list[QuestionType] | None = None,
    target_difficulty: str | None = None,
    rng: random.Random | None = None,
) -> list[dict]:
    """Bir kazanım kodu için, hedef zorluğa ve tipe göre öncelenmiş few-shot örnekleri."""
    rng = rng or random
    pool = EXAMPLES_BY_GRADE.get(grade, {}).get(kazanim_kod, [])
    if not pool:
        return []
    scored = [(_score(ex, target_difficulty, preferred_types, rng), ex) for ex in pool]
    scored.sort(key=lambda s: s[0], reverse=True)
    return [ex for _, ex in scored[:max_count]]


def has_examples(grade: int, kazanim_kod: str) -> bool:
    return bool(EXAMPLES_BY_GRADE.get(grade, {}).get(kazanim_kod))


def all_kazanim_codes(grade: int) -> list[str]:
    return list(EXAMPLES_BY_GRADE.get(grade, {}).keys())
