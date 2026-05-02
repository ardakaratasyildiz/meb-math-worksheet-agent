"""Few-shot örneklerini kazanım koduna + zorluğa + isteğe göre seçen yardımcı.

Seçim skorlaması (en yüksek öncelikli):
    +10  hedef zorlukla eşleşme (target_difficulty)
    + 5  tercih edilen tiplerden biri (preferred_types)
    - 2  daha önce seçilmişlerle her bağlam token'ı çakışması başına (diversity penalty)
    + 0-0.99 rastgele tiebreak
"""
import random

from app.data.few_shot import EXAMPLES_BY_GRADE
from app.models.enums import QuestionType
from app.services.diversity import extract_context_tokens

DIVERSITY_PENALTY_PER_TOKEN = 2.0


def _score(
    example: dict,
    target_difficulty: str | None,
    preferred_types: list[QuestionType] | None,
    used_tokens: set[str],
    rng: random.Random,
) -> float:
    score = rng.random()
    if target_difficulty is not None and example.get("difficulty") == target_difficulty:
        score += 10.0
    if preferred_types and example.get("type") in preferred_types:
        score += 5.0
    if used_tokens:
        ex_tokens = extract_context_tokens(example.get("question", ""))
        overlap = len(ex_tokens & used_tokens)
        score -= DIVERSITY_PENALTY_PER_TOKEN * overlap
    return score


def select_diverse(
    pool: list[dict],
    max_count: int,
    target_difficulty: str | None,
    preferred_types: list[QuestionType] | None,
    rng: random.Random,
    seed_used_tokens: set[str] | None = None,
) -> list[dict]:
    """Greedy MMR: aday havuzdan max_count adet seç, bağlam çakışmasını cezalandır.

    Her seçim sonrası 'kullanılmış token' havuzu güncellenir; bir sonraki adım
    bu havuzla çakışan örnekleri düşürür. seed_used_tokens çağrı dışından
    (örn. başka kazanımlardan) gelen token'ları başlangıç havuzuna koymak için.
    """
    if not pool:
        return []
    selected: list[dict] = []
    used_tokens: set[str] = set(seed_used_tokens or set())
    remaining = list(pool)
    for _ in range(min(max_count, len(pool))):
        if not remaining:
            break
        scored = [
            (_score(ex, target_difficulty, preferred_types, used_tokens, rng), ex)
            for ex in remaining
        ]
        scored.sort(key=lambda s: s[0], reverse=True)
        best = scored[0][1]
        selected.append(best)
        used_tokens.update(extract_context_tokens(best.get("question", "")))
        remaining.remove(best)
    return selected


def get_examples_for_kazanim(
    grade: int,
    kazanim_kod: str,
    max_count: int = 3,
    preferred_types: list[QuestionType] | None = None,
    target_difficulty: str | None = None,
    rng: random.Random | None = None,
    seed_used_tokens: set[str] | None = None,
) -> list[dict]:
    """Bir kazanım kodu için, hedef zorluğa ve tipe göre öncelenmiş few-shot örnekleri.

    seed_used_tokens önceki kazanımlardan/üretimlerden gelen bağlamları engellemek için.
    """
    rng = rng or random
    pool = EXAMPLES_BY_GRADE.get(grade, {}).get(kazanim_kod, [])
    if not pool:
        return []
    return select_diverse(
        pool=pool,
        max_count=max_count,
        target_difficulty=target_difficulty,
        preferred_types=preferred_types,
        rng=rng,
        seed_used_tokens=seed_used_tokens,
    )


def has_examples(grade: int, kazanim_kod: str) -> bool:
    return bool(EXAMPLES_BY_GRADE.get(grade, {}).get(kazanim_kod))


def all_kazanim_codes(grade: int) -> list[str]:
    return list(EXAMPLES_BY_GRADE.get(grade, {}).keys())
