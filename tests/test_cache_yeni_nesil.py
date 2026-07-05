"""Cache'in yeni_nesil (premium) ayrımı için testler.

Doğrulanan davranış:
- yeni_nesil cache anahtarına dahildir → premium ve normal setler AYRI havuzda.
- Normal mod anahtarı SONEK EKLEMEZ (eski cache kayıtları geçerli kalır).
- put/get roundtrip: premium set premium isteyene döner, normal isteyene DÖNMEZ.
"""
import tempfile
from pathlib import Path

import pytest

from app.models.enums import QuestionType
from app.models.schemas import Question
from app.services.llm_cache import GenerationCache, _cache_key


def _q(n: int) -> Question:
    return Question(
        number=n,
        question=f"Soru {n}: 2+{n}=?",
        answer=str(2 + n),
        solution_steps=f"2+{n}={2 + n}",
        kazanim_kod="M.5.1.1",
        question_type=QuestionType.SALT_ISLEM,
    )


@pytest.fixture()
def cache():
    with tempfile.TemporaryDirectory() as d:
        c = GenerationCache(db_path=str(Path(d) / "cache.sqlite3"))
        try:
            yield c
        finally:
            # Windows: tempdir silinebilsin diye SQLite bağlantısını kapat.
            if c._db is not None:
                c._db.close()


def test_cache_key_normal_has_no_premium_suffix():
    # Backward-compat: normal mod anahtarı eski formatla birebir aynı olmalı.
    key = _cache_key(5, "kesirler", "M.5.1.1", "orta", 10, None, False)
    assert key == "g5|kesirler|M.5.1.1|orta|q10|tall"
    assert "premium" not in key


def test_cache_key_yeni_nesil_appends_premium():
    key = _cache_key(5, "kesirler", "M.5.1.1", "orta", 10, None, True)
    assert key.endswith("|premium")


def test_normal_and_premium_are_separate_pools(cache):
    qs = [_q(i) for i in range(10)]
    # Premium set yaz.
    cache.put(5, "kesirler", "M.5.1.1", "orta", 10, qs, None, yeni_nesil=True)

    # Premium isteyen HIT alır.
    got_premium = cache.get(5, "kesirler", "M.5.1.1", "orta", 10, yeni_nesil=True)
    assert got_premium is not None
    assert len(got_premium) == 10

    # Normal isteyen aynı parametrelerle MISS alır (ayrı havuz).
    got_normal = cache.get(5, "kesirler", "M.5.1.1", "orta", 10, yeni_nesil=False)
    assert got_normal is None


def test_normal_set_reused_across_users(cache):
    # 1. kullanıcı üretti → cache'e yazıldı.
    qs = [_q(i) for i in range(10)]
    cache.put(5, "kesirler", "M.5.1.1", "orta", 10, qs, None, yeni_nesil=False)
    # 2. kullanıcı (tenant yok — anahtar tenant içermez) aynı seti HIT alır.
    got = cache.get(5, "kesirler", "M.5.1.1", "orta", 10, yeni_nesil=False)
    assert got is not None
    assert {q.question for q in got} == {q.question for q in qs}


def test_history_overlap_skips_set(cache):
    qs = [_q(i) for i in range(10)]
    cache.put(5, "kesirler", "M.5.1.1", "orta", 10, qs, None, yeni_nesil=True)
    from app.services.diversity import normalize_question

    # Kullanıcının geçmişinde tek set'in tüm soruları var → overlap → MISS.
    seen = {normalize_question(q.question) for q in qs}
    got = cache.get(
        5, "kesirler", "M.5.1.1", "orta", 10,
        exclude_questions=seen, yeni_nesil=True,
    )
    assert got is None
