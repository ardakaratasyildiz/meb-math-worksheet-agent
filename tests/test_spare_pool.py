"""Yedek soru havuzu + israf-token defteri + kısa çözüm modu testleri (Faz 1).

Bağlam (docs/COST_REDUCTION_PLAN.md): `generation_overshoot_ratio=1.8` hedefin
~2 katı soru ürettiriyor, fazlalar KIRPILIP ATILIYORDU (20 soruluk kağıt için 36
üretim → ~12 çöp). Artık fazlalar havuza yazılır ve post-filter eksiği önce
havuzdan karşılanır; LLM top-up (ölçüm: 19-24K çıktı token'ı) son çare.
"""
import pytest

from app.config import settings
from app.models.enums import Difficulty, QuestionType
from app.models.schemas import Question
from app.services.llm_cache import (
    GENERATION_CACHE,
    SPARE_POOL,
    _cache_key,
    _pool_key,
)


# DİKKAT: `normalize_question` sayıları `<N>`'e indirger → yalnız sayıları
# farklı sorular YAPISAL DUPLİKAT sayılır (havuzun unique index'i de buna
# dayanır). Bu yüzden test soruları farklı KELİMELERLE kurulur.
_STEMS = [
    "Ali {n} elma aldı, kaç elması var?",
    "Bir otobüste {n} yolcu vardı, kaç yolcu indi?",
    "Öğretmen {n} defter dağıttı, kaç defter kaldı?",
    "Hafta sonu {n} kilometre yürüdün, ne kadar yol kaldı?",
    "Sınıfta {n} öğrenci sıraya girdi, sıra kaç kişilik?",
    "Marketten {n} litre süt alındı, kaç litre satıldı?",
    "Bahçeye {n} fidan dikildi, kaç fidan tuttu?",
    "Kütüphaneden {n} kitap ödünç verildi, kaçı geri geldi?",
    "Fırında {n} ekmek pişti, kaçı satıldı?",
    "Trende {n} vagon vardı, kaçı doluydu?",
    "Çiftlikte {n} tavuk sayıldı, kaçı yumurtladı?",
    "Kasada {n} lira birikti, ne kadar harcandı?",
]


def _q(n: int, text: str | None = None) -> Question:
    return Question(
        number=n,
        question=text or _STEMS[n % len(_STEMS)].format(n=n + 1),
        answer=str(2 * n),
        solution_steps=f"{n} + {n} = {2 * n}",
        kazanim_kod="MAT.5.1.1.1",
        question_type=QuestionType.ISLEM,
        difficulty=Difficulty.ORTA,
    )


@pytest.fixture(autouse=True)
def _clean_pool():
    SPARE_POOL.clear()
    yield
    SPARE_POOL.clear()


# ------------------------------------------------------------------ havuz

def test_pool_key_has_no_question_count():
    """Havuz soru-BAZLI: anahtar soru sayısı taşımaz (10'luk stok 20'lik isteğe hizmet eder)."""
    k = _pool_key(5, "dogal_sayilar", None, "orta")
    assert "q10" not in k and "q20" not in k
    # Cache anahtarı ise sayı taşır (mevcut davranış korunuyor).
    assert "q10" in _cache_key(5, "dogal_sayilar", None, "orta", 10)


def test_pool_add_take_roundtrip():
    key = _pool_key(5, "dogal_sayilar", None, "orta")
    assert SPARE_POOL.add_many(key, [_q(i) for i in range(5)]) == 5
    taken = SPARE_POOL.take(key, 3)
    assert len(taken) == 3
    assert all(isinstance(q, Question) for q in taken)


def test_pool_take_does_not_delete_but_prefers_unused():
    """Soru silinmez (farklı kullanıcılara tekrar servis = maliyet düşüşü);
    az kullanılmış olan öncelenir."""
    key = _pool_key(6, "kesirler", None, "kolay")
    SPARE_POOL.add_many(key, [_q(i) for i in range(4)])
    first = {q.question for q in SPARE_POOL.take(key, 2)}
    second = {q.question for q in SPARE_POOL.take(key, 2)}
    # Stok tükenmedi ve ikinci çekim HENÜZ kullanılmamışları getirdi.
    assert len(first) == 2 and len(second) == 2
    assert not (first & second), "az-kullanılmış öncelemesi çalışmıyor"
    assert SPARE_POOL.stats()["total_entries"] == 4


def test_pool_take_respects_tenant_history():
    """Aynı kullanıcıya daha önce gitmiş soru havuzdan tekrar verilmez."""
    from app.services.diversity import normalize_question

    key = _pool_key(7, "oranti", None, "orta")
    qs = [_q(i) for i in range(3)]
    SPARE_POOL.add_many(key, qs)
    seen = {normalize_question(qs[0].question), normalize_question(qs[1].question)}
    taken = SPARE_POOL.take(key, 3, exclude_norms=seen)
    assert [q.question for q in taken] == [qs[2].question]


def test_pool_dedupes_structurally_identical_questions():
    """Havuz yapısal duplikat tutmaz: yalnız SAYILARI farklı soru aynı sayılır
    (normalize_question sayıyı `<N>` yapar — BatchDeduplicator ile aynı semantik)."""
    key = _pool_key(5, "dogal_sayilar", None, "zor")
    SPARE_POOL.add_many(key, [_q(1, "Ali 5 elma aldı, kaç elması var?")])
    SPARE_POOL.add_many(key, [_q(1, "Ali 9 elma aldı, kaç elması var?")])
    assert SPARE_POOL.stats()["total_entries"] == 1


def test_pool_trims_to_max_per_key():
    pool = type(SPARE_POOL)(max_per_key=5)
    key = _pool_key(8, "cebir", None, "orta")
    pool.add_many(key, [_q(i) for i in range(12)])
    rows = pool.take(key, 100)
    assert len(rows) <= 5
    pool.clear()


# ------------------------------------------ sınav modu çözüm kısaltma: GERİ ALINDI

def test_no_concise_solution_key_split():
    """Sınav modunda çözüm kısaltma DENENDİ ve GERİ ALINDI (2026-07-26 A/B):
    çözüm adımları çıktı maliyetinin ~%28'i, kısaltma bunun %29'unu kesiyor →
    kağıt maliyetinin ~%8'i, koşu-arası varyansın (±%15) ALTINDA. Karşılığında
    cache/havuz anahtarı ikiye bölünüyordu (ödevler daima include_solutions=False
    gönderir) → yeniden kullanım kaybı kazançtan büyük.

    Bu test anahtar bölünmesinin geri gelmemesini kilitler."""
    import inspect

    from app.prompts.templates import build_user_prompt

    assert "kisacozum" not in _cache_key(5, "dogal_sayilar", None, "orta", 10)
    assert "kisacozum" not in _pool_key(5, "dogal_sayilar", None, "orta")
    # Prompt üreticisi de çözüm-kısaltma parametresi taşımamalı.
    assert "concise_solutions" not in inspect.signature(build_user_prompt).parameters


# --------------------------------------------- israf (başarısız çağrı) token'ı

def test_failed_call_tokens_are_reported_not_lost():
    """Şema-drop eden çağrının token'ı ProviderResponse.wasted ile geri döner —
    Google faturalıyor, defter de saymalı."""
    from app.services.llm_providers import (
        ProviderError,
        ProviderResponse,
        TokenUsage,
        call_with_chain,
    )
    from pydantic import BaseModel

    class _Schema(BaseModel):
        ok: bool = True

    class _FakeGemini:
        models = ["bad-model", "gemini-2.5-flash"]

        def generate(self, system, prompt, schema, temperature, model=None,
                     max_output_tokens=None):
            if model == "bad-model":
                # 5000 çıktı token'ı yakıp şemaya uymayan yanıt döndü.
                raise ProviderError(
                    "şemaya uymadı",
                    usage=TokenUsage(input_tokens=1000, output_tokens=5000,
                                     model_name="gemini-2.5-flash"),
                )
            return ProviderResponse(
                parsed=_Schema(), model_name=model, provider="gemini",
                usage=TokenUsage(input_tokens=100, output_tokens=200,
                                 model_name=model),
            )

    resp = call_with_chain(
        system="s", prompt="p", schema=_Schema, temperature=0.5,
        gemini=_FakeGemini(), anthropic=None,
    )
    assert len(resp.wasted) == 1
    assert resp.wasted[0].output_tokens == 5000
    assert resp.wasted_cost_usd > 0, "israf maliyeti hesaplanmalı"


def test_pool_is_best_effort_never_raises():
    """Havuz DB'si patlasa bile ne add_many ne take istisna fırlatır.

    Prod'da havuz Turso'ya yazar ve mixed modda 3 bucket PARALEL koşar; çıplak
    bir DB hatası bucket'ın `except Exception`'ına düşüp HAZIR SORULARI çöpe
    atardı (canlıda 5 soruluk kağıtta orta bucket'ın 3 sorusu böyle kayboldu)."""
    class _BoomDB:
        def execute(self, *a, **k):
            raise RuntimeError("database is locked")

        def commit(self):
            raise RuntimeError("database is locked")

    key = _pool_key(5, "dogal_sayilar", None, "orta")
    SPARE_POOL.add_many(key, [_q(0), _q(1)])  # önce gerçek veri yaz
    # monkeypatch DEĞİL: fixture teardown'ı (clear) monkeypatch geri almasından
    # ÖNCE koşuyor → bozuk DB ile temizlik patlıyordu. Elle geri yükle.
    real_db = SPARE_POOL._db
    SPARE_POOL._db = _BoomDB()
    try:
        # Hiçbiri patlamamalı; take boş liste dönmeli.
        assert SPARE_POOL.add_many(key, [_q(2)]) == 0
        assert SPARE_POOL.take(key, 5) == []
    finally:
        SPARE_POOL._db = real_db


def test_pro_removed_from_fallback_chain():
    """gemini-2.5-pro ($10/1M çıktı, thinking kapatılamaz) fallback'ten çıkarıldı."""
    assert "pro" not in settings.gemini_fallback_models


# ------------------------------------------- entegrasyon: top-up'sız doldurma

def test_critic_shortfall_filled_from_spares_without_extra_llm_call(monkeypatch):
    """ASIL DAVRANIŞ: critic soru düşürdüğünde eksik, overshoot fazlalarından
    kapanır → İKİNCİ bir LLM üretim çağrısı ATILMAZ (eskiden 19-24K çıktı
    token'lık top-up çağrısı gidiyordu)."""
    from app.services import agent as A
    from app.services.agent import GeneratedBatch, GeneratedQuestion, GeminiAgent
    from app.services.critic import CriticVerdict
    from app.services.llm_providers import ProviderResponse, TokenUsage

    calls = {"n": 0}

    def fake_chain(**kw):
        calls["n"] += 1
        # Overshoot: 20 hedef × 1.8 → ~36 soru döndür (yapısal olarak farklı).
        # 36 YAPISAL OLARAK FARKLI soru: varyant eki de kelime olmalı — sayı
        # kullanılırsa normalize_question onu `<N>` yapar ve varyantlar çakışır.
        _variants = ["sabah", "akşam", "öğlen"]
        qs = [
            GeneratedQuestion(
                question=(
                    f"{_variants[i // 12]} vakti: "
                    + _STEMS[i % len(_STEMS)].format(n=i + 1)
                ),
                answer=str(i), solution_steps="adım", kazanim_kod="MAT.5.1.1.1",
                question_type=QuestionType.ISLEM,
            )
            for i in range(36)
        ]
        return ProviderResponse(
            parsed=GeneratedBatch(questions=qs), model_name="gemini-2.5-flash",
            provider="gemini",
            usage=TokenUsage(input_tokens=1000, output_tokens=9000,
                             model_name="gemini-2.5-flash"),
        )

    class _FakeCritic:
        _last_usage = TokenUsage(input_tokens=10, output_tokens=10,
                                 model_name="gemini-2.5-flash-lite")

        def evaluate(self, questions, kazanimlar, difficulty, context=""):
            # İlk 5 soruyu reddet → 5 eksik oluşsun.
            return [
                CriticVerdict(question_index=i, is_valid=i >= 5, confidence=0.95)
                for i in range(len(questions))
            ]

    # Üretim geçmişi KALICI (history.sqlite3): izole edilmezse bu testin ilk
    # koşusu soruları kaydeder, ikinci koşuda dedup hepsini eler (test idempotent
    # olmaz). Belleğe alınmış taze bir geçmişle koş.
    from app.services.history import GenerationHistory

    monkeypatch.setattr(A, "GENERATION_HISTORY", GenerationHistory(persist=False))
    monkeypatch.setattr(A, "call_with_chain", fake_chain)
    monkeypatch.setattr(A, "_collect_few_shot", lambda *a, **k: ([], "static"))
    monkeypatch.setattr(A, "_collect_textbook_context", lambda *a, **k: [])
    monkeypatch.setattr(GeminiAgent, "_get_critic", lambda self, subject=None: _FakeCritic())
    monkeypatch.setattr(GeminiAgent, "__init__", lambda self, **kw: None)
    monkeypatch.setattr(settings, "enable_semantic_dedup", False)
    monkeypatch.setattr(settings, "enable_math_verifier", False)
    monkeypatch.setattr(settings, "enable_critic", True)
    monkeypatch.setattr(settings, "enable_generation_cache", False)
    monkeypatch.setattr(settings, "generation_overshoot_ratio", 1.8)

    agent = GeminiAgent()
    agent.thinking_budget = 512  # __init__ stub'landı; çıktı tavanı bunu okur
    agent._gemini_provider = None
    agent._anthropic_provider = None
    agent._embedder = None
    agent._critics = {}

    questions = agent.generate(
        grade=5, topic_id="dogal_sayilar", kazanim_kod=None,
        difficulty=Difficulty.ORTA, question_count=20,
    )

    assert len(questions) == 20, "eksik, yedeklerden tamamlanmalıydı"
    assert calls["n"] == 1, (
        f"top-up LLM çağrısı atılmamalıydı (atılan üretim çağrısı: {calls['n']})"
    )
    # Kalan fazlalar stoğa yazıldı → sonraki istek daha az üretim yapar.
    assert SPARE_POOL.stats()["total_entries"] > 0, "kalan fazlalar havuza yazılmalı"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
