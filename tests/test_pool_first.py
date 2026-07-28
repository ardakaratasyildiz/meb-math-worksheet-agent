"""Depo (soru havuzu) BİRİNCİL servis yolu + tembel damga testleri (Faz 2).

Bağlam (docs/COST_QUALITY_V2_PLAN.md §3b, §3c): Faz 1'de havuz yalnız
post-filter EKSİĞİNİ kapatıyordu — LLM her zaman ÖNCE çağrılıyordu, teslim
edilenler de yalnız Faz 1 sonunda havuza yazılıyordu. Faz 2 akışı tersine
çevirir: `cache → DEPO (istenen sayının TAMAMI) → yalnız EKSİK kadar LLM`.
İkinci kazanım: `critic_pass = 1` damgalı depo soruları filtrelerden (math_verifier
+ critic) HİÇ geçirilmeden servis edilir — her depo isabeti artık BEDAVA.

Bu dosya `app/services/agent.py::GeminiAgent.generate()`'in pool-first bloğunu
uçtan uca (fake LLM provider + fake critic ile) test eder. Havuzun kendi
CRUD davranışı (`take_for_serving`, `stamp`) `tests/test_spare_pool.py`'da.
"""
import pytest

from app.config import settings
from app.models.enums import Difficulty, QuestionType
from app.services.llm_cache import GENERATION_CACHE, SPARE_POOL, _pool_key

# DİKKAT: `normalize_question` sayıları `<N>`'e indirger — depoya yazılan her
# test sorusu FARKLI KELİMELERLE kurulmalı (bkz. test_spare_pool.py başlığı),
# aksi halde unique index'e çarpıp tek satıra düşerler.
_POOL_STEMS = [
    "Ayşe bahçeye fidan dikti, kaç fidan tuttu?",
    "Mehmet markette ekmek aldı, kaç ekmek kaldı?",
    "Kütüphaneye kitap bağışlandı, kaç kitap rafta?",
    "Ali okula kalem getirdi, kaç kalem verdi?",
    "Zeynep pazardan meyve topladı, kaç meyve sattı?",
    "Sınıfta resim yarışması yapıldı, kaç resim asıldı?",
    "Çiftlikte tavuk sayıldı, kaçı yumurtladı?",
    "Trende vagon vardı, kaçı doluydu?",
    "Fırında ekmek pişti, kaçı satıldı?",
    "Bahçede çiçek açtı, kaçı soldu?",
    "Otobüste yolcu vardı, kaçı indi?",
    "Kasada lira birikti, ne kadar harcandı?",
    "Öğretmen defter dağıttı, kaç defter kaldı?",
    "Hafta sonu kilometre yürüdün, ne kadar yol kaldı?",
    "Sıraya öğrenci girdi, sıra kaç kişilik?",
    "Markette süt alındı, kaç litre satıldı?",
    "Depoya kumaş geldi, kaç top kaldı?",
    "Atölyede masa yapıldı, kaçı boyandı?",
    "Parkta salıncak kuruldu, kaçı kırıldı?",
    "Manavda karpuz satıldı, kaçı bozuktu?",
    "Terzi düğme dikti, kaç düğme arttı?",
    "Kasap et tarttı, kaç kilo kaldı?",
    "Postacı mektup dağıttı, kaç mektup kaldı?",
    "Bakkal şeker sattı, kaç paket kaldı?",
    "Ressam tablo çizdi, kaçı satıldı?",
]


def _pool_question(i: int, marker: str = "", question_type: QuestionType = QuestionType.ISLEM):
    from app.models.schemas import Question

    text = _POOL_STEMS[i % len(_POOL_STEMS)]
    if marker:
        text = f"{marker}: {text}"
    return Question(
        number=i + 1,
        question=text,
        answer=str(i),
        solution_steps="adım",
        kazanim_kod="MAT.5.1.1.1",
        question_type=question_type,
        difficulty=Difficulty.ORTA,
    )


def _seed_pool(
    key: str, count: int, *, critic_pass=None, marker: str = "", start: int = 0,
    question_type: QuestionType = QuestionType.ISLEM,
):
    """`count` adet YAPISAL FARKLI soru ekler (hepsi aynı `critic_pass` durumunda)."""
    qs = [_pool_question(start + i, marker=marker, question_type=question_type) for i in range(count)]
    kw = {}
    if critic_pass is not None:
        kw = dict(critic_pass=critic_pass, verifier_model=settings.critic_model)
    added = SPARE_POOL.add_many(key, qs, source="live-overshoot", **kw)
    assert added == count, f"beklenen {count} eklendi, gerçek {added} — stem çakışması olabilir"
    return qs


def _pool_question_for_type(i: int, qtype: QuestionType, marker: str = ""):
    """`_pool_question` ile AYNI ama metne TİP adını gömer — farklı tiplerden
    aynı index'li (i) sorular bile YAPISAL olarak çakışmasın diye (aksi halde
    unique index (pool_key, norm_question) farklı tiplerdeki aynı-index'li
    soruları tek satıra düşürebilirdi)."""
    from app.models.schemas import Question

    text = f"[{qtype.value}] {_POOL_STEMS[i % len(_POOL_STEMS)]}"
    if marker:
        text = f"{marker}: {text}"
    return Question(
        number=i + 1,
        question=text,
        answer=str(i),
        solution_steps="adım",
        kazanim_kod="MAT.5.1.1.1",
        question_type=qtype,
        difficulty=Difficulty.ORTA,
    )


def _seed_pool_with_counts(
    key: str, counts: dict[QuestionType, int], *, critic_pass=None,
):
    """Her tip için `counts[qt]` adet YAPISAL FARKLI soru ekler — VARSAYILAN
    yapılandırmayla (`pool_first_respect_type_mix=True`) tip-farkında pool-first
    yolunu test edebilmek için (Opus denetimi 2026-07-28, 3. tur): `_seed_pool`
    tek tiple dolduruyordu, bu da tip-farkında seçim AÇIKKEN kovanın
    `question_count`'un TAMAMINI hiç karşılayamamasına yol açıyordu — Faz 2'nin
    çekirdek garantileri (0 LLM/0 critic, tenant tekrarı, tembel damga kazancı)
    yalnızca ÜRETİMDE KULLANILMAYAN (bayrak kapalı) yapılandırmada kanıtlanmış
    oluyordu. Bu yardımcı, GERÇEK hedef dağılıma (`distribute_question_types`)
    oturan (veya onu bilerek aşan/eksik bırakan) bir kova kurar."""
    kw: dict = {}
    if critic_pass is not None:
        kw = dict(critic_pass=critic_pass, verifier_model=settings.critic_model)
    for qt, n in counts.items():
        if n <= 0:
            continue
        qs = [_pool_question_for_type(i, qt) for i in range(n)]
        added = SPARE_POOL.add_many(key, qs, source="live-overshoot", **kw)
        assert added == n, f"{qt.value}: beklenen {n} eklendi, gerçek {added}"


@pytest.fixture(autouse=True)
def _clean_state():
    SPARE_POOL.clear()
    GENERATION_CACHE.clear()
    yield
    SPARE_POOL.clear()
    GENERATION_CACHE.clear()


def _make_agent(monkeypatch, fake_chain, fake_critic_factory=None, history=None):
    """Ortak agent kurulumu — test_spare_pool.py'daki kalıple aynı: `__init__`
    stub'lanır, provider/embedder/critic monkeypatch'lenir, GENERATION_HISTORY
    (varsayılan) taze bir bellek-içi örnekle izole edilir.

    `enable_generation_cache=False`: bu dosyanın testleri DEPO'yu (cache
    KATMANININ ALTINDAKİ katman) izole test eder — `generation_cache` aynı
    fiziksel sqlite dosyasına yazdığından (mevcut kalıp, test_spare_pool.py'daki
    `test_critic_shortfall_filled_from_spares_without_extra_llm_call` ve
    `test_delivered_questions_...` testlerinde de aynı sebeple kapatılıyor)
    kapatılmazsa önceki bir test/koşu aynı (grade, topic, kazanım, zorluk,
    count) anahtarına yazdıysa bu testler cache-hit'e düşüp depo/LLM hiç
    çalışmadan yanlışlıkla 'geçebilir'.

    `pool_first_respect_type_mix=False`: bu dosyanın çoğu testi AGREGE pool-first
    mekaniğini test eder (tam/kısmi karşılama, tembel damga, tenant tekrarı) —
    tip karışımı DEĞİL. Testlerin `_seed_pool` yardımcısı tüm satırları TEK tiple
    (ISLEM) doldurur; tip-farkında seçim AÇIKKEN (varsayılan config) her tip
    yalnız kendi kotasını alır ve tek-tipli bir kova artık `question_count`'un
    TAMAMINI karşılayamaz (bu doğru davranış — bkz. `test_pool_first_respects_type_mix_*`).
    Bu yüzden tip-mix'e ÖZEL olmayan testler burada kapatır; tip-mix testleri
    kendi içinde AÇIKÇA True'ya çevirir."""
    from app.services import agent as A
    from app.services.agent import GeminiAgent
    from app.services.history import GenerationHistory

    monkeypatch.setattr(settings, "enable_generation_cache", False)
    monkeypatch.setattr(settings, "pool_first_respect_type_mix", False)

    hist = history if history is not None else GenerationHistory(persist=False)
    monkeypatch.setattr(A, "GENERATION_HISTORY", hist)
    monkeypatch.setattr(A, "call_with_chain", fake_chain)
    monkeypatch.setattr(A, "_collect_few_shot", lambda *a, **k: ([], "static"))
    monkeypatch.setattr(A, "_collect_textbook_context", lambda *a, **k: [])
    if fake_critic_factory is not None:
        monkeypatch.setattr(GeminiAgent, "_get_critic", lambda self, subject=None: fake_critic_factory())
    monkeypatch.setattr(GeminiAgent, "__init__", lambda self, **kw: None)

    agent = GeminiAgent()
    agent.thinking_budget = 512
    agent.model = "gemini-2.5-flash"  # __init__ stub'landığından elle set (last_model_used fallback'i)
    agent._gemini_provider = None
    agent._anthropic_provider = None
    agent._embedder = None
    agent._critics = {}
    return agent, hist


def _no_llm_call(**kw):
    raise AssertionError("LLM üretim çağrısı (call_with_chain) YAPILMAMALIYDI — depo tamamını karşılamalıydı.")


class _NoCallCritic:
    """`evaluate()` çağrılırsa patlar — critic_pass=1 satırlar critic'i HİÇ görmemeli."""

    _last_usage = None

    def evaluate(self, questions, kazanimlar, difficulty, context=""):
        raise AssertionError("Critic ÇAĞRILMAMALIYDI — critic_pass=1 satırlar filtresiz servis edilir.")


# ------------------------------------------------------- İş 1: pool-first akış


def test_pool_fully_satisfies_no_llm_call(monkeypatch):
    """Depo istenen sayının TAMAMINI (10) karşılıyorsa LLM üretim çağrısı HİÇ
    yapılmaz VE critic_pass=1 olduğundan critic de HİÇ çağrılmaz. Trace
    pool_hit_count == question_count olmalı, model/provider='pool', maliyet=0."""
    key = _pool_key(5, "dogal_sayilar", None, "orta")
    _seed_pool(key, 10, critic_pass=1)

    agent, _ = _make_agent(monkeypatch, _no_llm_call, fake_critic_factory=_NoCallCritic)
    monkeypatch.setattr(settings, "enable_pool_first_serving", True)
    monkeypatch.setattr(settings, "enable_spare_pool", True)

    questions = agent.generate(
        grade=5, topic_id="dogal_sayilar", kazanim_kod=None,
        difficulty=Difficulty.ORTA, question_count=10,
    )

    assert len(questions) == 10
    trace = agent.build_last_trace()
    assert trace.pool_hit_count == 10
    assert trace.requested_count == 10
    assert trace.delivered_count == 10
    assert trace.model_used == "pool"
    assert trace.provider == "pool"
    assert trace.estimated_cost_usd == 0.0
    assert trace.prompt_tokens == 0 and trace.completion_tokens == 0


def test_pool_partial_only_missing_generated(monkeypatch):
    """Depo yalnız 4/10 karşılıyorsa üretim hedefi (`distribute_question_types`'a
    verilen `total`) KALAN (6) sayıya göre hesaplanmalı — istenen 10'a göre değil."""
    key = _pool_key(5, "dogal_sayilar", None, "orta")
    _seed_pool(key, 4, critic_pass=1)

    from app.services import agent as A
    from app.services.agent import GeneratedBatch, GeneratedQuestion

    seen_totals = []
    real_distribute = A.distribute_question_types

    def _spy_distribute(total, *a, **k):
        seen_totals.append(total)
        return real_distribute(total, *a, **k)

    calls = {"n": 0}

    def fake_chain(**kw):
        calls["n"] += 1
        from app.services.llm_providers import ProviderResponse, TokenUsage

        qs = [
            GeneratedQuestion(
                question=f"llm-üretimi: {_POOL_STEMS[(i + 20) % len(_POOL_STEMS)]}",
                answer=str(i), solution_steps="adım", kazanim_kod="MAT.5.1.1.1",
                question_type=QuestionType.ISLEM,
            )
            for i in range(6)
        ]
        return ProviderResponse(
            parsed=GeneratedBatch(questions=qs), model_name="gemini-2.5-flash",
            provider="gemini",
            usage=TokenUsage(input_tokens=500, output_tokens=500,
                             model_name="gemini-2.5-flash"),
        )

    monkeypatch.setattr(A, "distribute_question_types", _spy_distribute)
    monkeypatch.setattr(settings, "enable_pool_first_serving", True)
    monkeypatch.setattr(settings, "enable_spare_pool", True)
    monkeypatch.setattr(settings, "generation_overshoot_ratio", 1.0)
    monkeypatch.setattr(settings, "enable_critic", False)
    monkeypatch.setattr(settings, "enable_math_verifier", False)

    agent, _ = _make_agent(monkeypatch, fake_chain)

    questions = agent.generate(
        grade=5, topic_id="dogal_sayilar", kazanim_kod=None,
        difficulty=Difficulty.ORTA, question_count=10,
    )

    assert len(questions) == 10
    assert calls["n"] == 1, "yalnız TEK üretim çağrısı yapılmalıydı (eksik=6, retry gerekmedi)"
    assert seen_totals[0] == 6, (
        f"üretim hedefi KALAN sayıya (6) göre hesaplanmalıydı, gelen: {seen_totals[0]}"
    )
    trace = agent.build_last_trace()
    assert trace.pool_hit_count == 4


# ------------------------------------------------------------ İş 2: tembel damga


def test_critic_pass_one_skips_critic_entirely(monkeypatch):
    """`critic_pass=1` (bedava damgalı) sorular servis edilirken critic HİÇ
    çağrılmaz — Faz 2'nin asıl kazancı."""
    key = _pool_key(5, "dogal_sayilar", None, "orta")
    _seed_pool(key, 5, critic_pass=1)

    agent, _ = _make_agent(monkeypatch, _no_llm_call, fake_critic_factory=_NoCallCritic)
    monkeypatch.setattr(settings, "enable_pool_first_serving", True)
    monkeypatch.setattr(settings, "enable_spare_pool", True)
    monkeypatch.setattr(settings, "enable_critic", True)

    questions = agent.generate(
        grade=5, topic_id="dogal_sayilar", kazanim_kod=None,
        difficulty=Difficulty.ORTA, question_count=5,
    )
    assert len(questions) == 5


def test_critic_pass_null_calls_critic_and_stamps_row(monkeypatch):
    """`critic_pass IS NULL` soru servis edilirken critic BİR KEZ çağrılır ve
    sonuç (`critic_pass=1`, `verifier_model`, `verified_at`) satıra UPDATE ile
    yazılır (`stamp()`) — bir sonraki serviste artık ücretsiz olur."""
    from app.services.diversity import normalize_question
    from app.services.llm_providers import TokenUsage

    key = _pool_key(5, "dogal_sayilar", None, "orta")
    qs = _seed_pool(key, 5, critic_pass=None)

    class _AcceptAllCritic:
        _last_usage = TokenUsage(input_tokens=5, output_tokens=5,
                                 model_name="gemini-2.5-flash-lite")
        calls = 0

        def evaluate(self, questions, kazanimlar, difficulty, context=""):
            type(self).calls += 1
            from app.services.critic import CriticVerdict
            return [
                CriticVerdict(question_index=i, is_valid=True, confidence=0.9)
                for i in range(len(questions))
            ]

    agent, _ = _make_agent(monkeypatch, _no_llm_call, fake_critic_factory=_AcceptAllCritic)
    monkeypatch.setattr(settings, "enable_pool_first_serving", True)
    monkeypatch.setattr(settings, "enable_spare_pool", True)
    monkeypatch.setattr(settings, "enable_critic", True)
    monkeypatch.setattr(settings, "enable_math_verifier", False)

    questions = agent.generate(
        grade=5, topic_id="dogal_sayilar", kazanim_kod=None,
        difficulty=Difficulty.ORTA, question_count=5,
    )

    assert len(questions) == 5
    assert _AcceptAllCritic.calls >= 1, "NULL satırlar için critic çağrılmalıydı"
    for q in qs:
        row = SPARE_POOL._db.execute(
            "SELECT critic_pass, verifier_model, verified_at FROM spare_questions "
            "WHERE pool_key = ? AND norm_question = ?",
            (key, normalize_question(q.question)),
        ).fetchone()
        assert row[0] == 1, "critic geçti → satır critic_pass=1 ile damgalanmalıydı"
        assert row[1] == settings.critic_model
        assert row[2] is not None


def test_critic_fail_open_keeps_row_null(monkeypatch):
    """Critic fail-open (BOŞ liste) olduğunda soru yine servis edilir (bugünkü
    fail-open davranışı) ama satır damgalanmaz — FAIL-CLOSED (§3c): 'denetlendi,
    geçti' YALANI yazılmaz, satır NULL kalır, sonraki serviste yeniden denetlenir."""
    from app.services.diversity import normalize_question
    from app.services.llm_providers import TokenUsage

    key = _pool_key(5, "dogal_sayilar", None, "orta")
    qs = _seed_pool(key, 5, critic_pass=None)

    class _FailOpenCritic:
        _last_usage = TokenUsage(input_tokens=5, output_tokens=5,
                                 model_name="gemini-2.5-flash-lite")

        def evaluate(self, questions, kazanimlar, difficulty, context=""):
            return []  # gerçek GeminiCritic.evaluate()'in fail-open dönüşü

    agent, _ = _make_agent(monkeypatch, _no_llm_call, fake_critic_factory=_FailOpenCritic)
    monkeypatch.setattr(settings, "enable_pool_first_serving", True)
    monkeypatch.setattr(settings, "enable_spare_pool", True)
    monkeypatch.setattr(settings, "enable_critic", True)
    monkeypatch.setattr(settings, "enable_math_verifier", False)

    questions = agent.generate(
        grade=5, topic_id="dogal_sayilar", kazanim_kod=None,
        difficulty=Difficulty.ORTA, question_count=5,
    )

    assert len(questions) == 5, "critic fail-open iken de sorular servis edilmeli"
    for q in qs:
        row = SPARE_POOL._db.execute(
            "SELECT critic_pass FROM spare_questions WHERE pool_key = ? AND norm_question = ?",
            (key, normalize_question(q.question)),
        ).fetchone()
        assert row[0] is None, "fail-open iken critic_pass=1 YALANI yazılmamalı"


def test_critic_rejects_stamps_zero_and_never_served_again(monkeypatch):
    """Critic reddettiğinde satır `critic_pass=0` ile damgalanır, soru bu
    istekte servis EDİLMEZ (eksik LLM top-up ile kapatılır) ve sonraki
    `take()`/`take_for_serving()` onu bir daha ASLA döndürmez."""
    from app.services.diversity import normalize_question
    from app.services.llm_providers import ProviderResponse, TokenUsage
    from app.services.agent import GeneratedBatch, GeneratedQuestion

    MARKER = "HAVUZ-REDDEDILECEK"
    key = _pool_key(5, "dogal_sayilar", None, "orta")
    rejected_qs = _seed_pool(key, 3, critic_pass=None, marker=MARKER)

    def fake_chain(**kw):
        qs = [
            GeneratedQuestion(
                question=f"llm-üretimi: {_POOL_STEMS[(i + 20) % len(_POOL_STEMS)]}",
                answer=str(i), solution_steps="adım", kazanim_kod="MAT.5.1.1.1",
                question_type=QuestionType.ISLEM,
            )
            for i in range(3)
        ]
        return ProviderResponse(
            parsed=GeneratedBatch(questions=qs), model_name="gemini-2.5-flash",
            provider="gemini",
            usage=TokenUsage(input_tokens=500, output_tokens=500,
                             model_name="gemini-2.5-flash"),
        )

    class _RejectMarkedCritic:
        _last_usage = TokenUsage(input_tokens=5, output_tokens=5,
                                 model_name="gemini-2.5-flash-lite")

        def evaluate(self, questions, kazanimlar, difficulty, context=""):
            from app.services.critic import CriticVerdict
            return [
                CriticVerdict(
                    question_index=i,
                    is_valid=MARKER not in questions[i].question,
                    confidence=0.95,
                )
                for i in range(len(questions))
            ]

    agent, _ = _make_agent(monkeypatch, fake_chain, fake_critic_factory=_RejectMarkedCritic)
    monkeypatch.setattr(settings, "enable_pool_first_serving", True)
    monkeypatch.setattr(settings, "enable_spare_pool", True)
    monkeypatch.setattr(settings, "enable_critic", True)
    monkeypatch.setattr(settings, "enable_math_verifier", False)
    monkeypatch.setattr(settings, "generation_overshoot_ratio", 1.0)

    questions = agent.generate(
        grade=5, topic_id="dogal_sayilar", kazanim_kod=None,
        difficulty=Difficulty.ORTA, question_count=3,
    )

    assert len(questions) == 3
    assert all(MARKER not in q.question for q in questions), (
        "critic'in reddettiği depo soruları TESLİM EDİLMEMELİ"
    )
    for q in rejected_qs:
        row = SPARE_POOL._db.execute(
            "SELECT critic_pass FROM spare_questions WHERE pool_key = ? AND norm_question = ?",
            (key, normalize_question(q.question)),
        ).fetchone()
        assert row[0] == 0, "critic reddettiği satır critic_pass=0 ile damgalanmalı"

    # Bir sonraki take()/take_for_serving() bu soruları BİR DAHA döndürmemeli.
    again = SPARE_POOL.take_for_serving(key, 10)
    assert not any(MARKER in it.question.question for it in again)
    again2 = SPARE_POOL.take(key, 10)
    assert not any(MARKER in q.question for q in again2)


# --------------------------------------------------- kullanıcı tekrarı garantisi


def test_same_tenant_never_gets_same_question_twice(monkeypatch):
    """EN ÖNEMLİ GARANTİ: aynı kullanıcı iki `generate()` çağrısında KESİŞMEYEN
    soru setleri almalı (depo çapraz-kullanıcı serbest ama aynı kullanıcıya
    tekrar YASAK)."""
    key = _pool_key(5, "dogal_sayilar", None, "orta")
    _seed_pool(key, 20, critic_pass=1)

    from app.services.history import GenerationHistory

    hist = GenerationHistory(persist=False)
    agent, _ = _make_agent(monkeypatch, _no_llm_call, fake_critic_factory=_NoCallCritic, history=hist)
    monkeypatch.setattr(settings, "enable_pool_first_serving", True)
    monkeypatch.setattr(settings, "enable_spare_pool", True)

    first = agent.generate(
        grade=5, topic_id="dogal_sayilar", kazanim_kod=None,
        difficulty=Difficulty.ORTA, question_count=10, tenant_id="ogretmen-A",
    )
    second = agent.generate(
        grade=5, topic_id="dogal_sayilar", kazanim_kod=None,
        difficulty=Difficulty.ORTA, question_count=10, tenant_id="ogretmen-A",
    )

    assert len(first) == 10 and len(second) == 10
    first_texts = {q.question for q in first}
    second_texts = {q.question for q in second}
    assert not (first_texts & second_texts), (
        "aynı kullanıcı iki çağrıda AYNI soruyu almamalı"
    )


def test_different_tenant_can_get_same_questions(monkeypatch):
    """Çapraz-kullanıcı tekrar İSTENEN davranış: farklı kullanıcı depodan AYNI
    soruları alabilmeli (doluluk eşiği / karışım oranı kuralı YOK)."""
    key = _pool_key(5, "dogal_sayilar", None, "orta")
    _seed_pool(key, 5, critic_pass=1)

    from app.services.history import GenerationHistory

    hist = GenerationHistory(persist=False)
    agent, _ = _make_agent(monkeypatch, _no_llm_call, fake_critic_factory=_NoCallCritic, history=hist)
    monkeypatch.setattr(settings, "enable_pool_first_serving", True)
    monkeypatch.setattr(settings, "enable_spare_pool", True)

    teacher_a = agent.generate(
        grade=5, topic_id="dogal_sayilar", kazanim_kod=None,
        difficulty=Difficulty.ORTA, question_count=5, tenant_id="ogretmen-A",
    )
    teacher_b = agent.generate(
        grade=5, topic_id="dogal_sayilar", kazanim_kod=None,
        difficulty=Difficulty.ORTA, question_count=5, tenant_id="ogretmen-B",
    )

    assert {q.question for q in teacher_a} == {q.question for q in teacher_b}, (
        "farklı kullanıcılar depodan AYNI soru setini alabilmeli (çapraz kullanım)"
    )


# ------------------------------------------------------------- bayrak/regresyon


def test_enable_pool_first_serving_false_keeps_old_behavior(monkeypatch):
    """`enable_pool_first_serving=False` → bugünkü davranış birebir: depo TAM
    yeterli olsa bile LLM ÖNCE çağrılır (eski akış), pool_hit_count=0."""
    from app.services.llm_providers import ProviderResponse, TokenUsage
    from app.services.agent import GeneratedBatch, GeneratedQuestion

    key = _pool_key(5, "dogal_sayilar", None, "orta")
    _seed_pool(key, 10, critic_pass=1)

    calls = {"n": 0}

    def fake_chain(**kw):
        calls["n"] += 1
        qs = [
            GeneratedQuestion(
                question=f"llm-üretimi: {_POOL_STEMS[(i + 20) % len(_POOL_STEMS)]}",
                answer=str(i), solution_steps="adım", kazanim_kod="MAT.5.1.1.1",
                question_type=QuestionType.ISLEM,
            )
            for i in range(10)
        ]
        return ProviderResponse(
            parsed=GeneratedBatch(questions=qs), model_name="gemini-2.5-flash",
            provider="gemini",
            usage=TokenUsage(input_tokens=500, output_tokens=500,
                             model_name="gemini-2.5-flash"),
        )

    agent, _ = _make_agent(monkeypatch, fake_chain)
    monkeypatch.setattr(settings, "enable_pool_first_serving", False)
    monkeypatch.setattr(settings, "enable_spare_pool", True)
    monkeypatch.setattr(settings, "enable_critic", False)
    monkeypatch.setattr(settings, "enable_math_verifier", False)
    monkeypatch.setattr(settings, "generation_overshoot_ratio", 1.0)

    questions = agent.generate(
        grade=5, topic_id="dogal_sayilar", kazanim_kod=None,
        difficulty=Difficulty.ORTA, question_count=10,
    )

    assert len(questions) == 10
    assert calls["n"] == 1, "bayrak kapalıyken LLM ESKİ AKIŞTA HER ZAMAN çağrılmalı"
    trace = agent.build_last_trace()
    assert trace.pool_hit_count == 0


def test_enable_spare_pool_false_path_not_broken(monkeypatch):
    """`enable_spare_pool=False` → havuz tamamen devre dışı, üretim yalnız LLM'den
    gelir; hiçbir havuz çağrısı yapılmadan akış bozulmadan tamamlanır."""
    from app.services.llm_providers import ProviderResponse, TokenUsage
    from app.services.agent import GeneratedBatch, GeneratedQuestion

    key = _pool_key(5, "dogal_sayilar", None, "orta")
    _seed_pool(key, 10, critic_pass=1)  # havuzda soru olsa bile...

    calls = {"n": 0}

    def fake_chain(**kw):
        calls["n"] += 1
        qs = [
            GeneratedQuestion(
                question=f"llm-üretimi: {_POOL_STEMS[(i + 20) % len(_POOL_STEMS)]}",
                answer=str(i), solution_steps="adım", kazanim_kod="MAT.5.1.1.1",
                question_type=QuestionType.ISLEM,
            )
            for i in range(10)
        ]
        return ProviderResponse(
            parsed=GeneratedBatch(questions=qs), model_name="gemini-2.5-flash",
            provider="gemini",
            usage=TokenUsage(input_tokens=500, output_tokens=500,
                             model_name="gemini-2.5-flash"),
        )

    agent, _ = _make_agent(monkeypatch, fake_chain)
    monkeypatch.setattr(settings, "enable_pool_first_serving", True)
    monkeypatch.setattr(settings, "enable_spare_pool", False)  # ← devre dışı
    monkeypatch.setattr(settings, "enable_critic", False)
    monkeypatch.setattr(settings, "enable_math_verifier", False)
    monkeypatch.setattr(settings, "generation_overshoot_ratio", 1.0)

    questions = agent.generate(
        grade=5, topic_id="dogal_sayilar", kazanim_kod=None,
        difficulty=Difficulty.ORTA, question_count=10,
    )

    assert len(questions) == 10
    assert calls["n"] == 1
    trace = agent.build_last_trace()
    assert trace.pool_hit_count == 0
    # Havuzdaki sorular (enable_spare_pool=False olduğundan) HİÇ dokunulmadı.
    assert SPARE_POOL.stats()["total_entries"] == 10


# --------------------------------------------- SHOULD-FIX: tip-farkında seçim
# (Opus denetimi 2026-07-28) — kovada BASKIN tek tip kağıdın TAMAMINI ele
# geçirmemeli; her tip yalnız KENDİ hedef kotası kadar depodan çekilmeli.


def test_pool_first_respects_type_mix_does_not_collapse_to_single_type(monkeypatch):
    """Kovada YALNIZ `islem` tipi varken 10 soru istenirse, depo yalnız o tipin
    hedef KOTASINI (ORTA/dogal_sayilar, question_count=10 için tip başına
    ağırlık 1 — `distribute_question_types` ile doğrulanmış) verir; kağıt
    TEK TİPE düşmez, kalanı LLM farklı tiplerle tamamlar."""
    from app.services.llm_providers import ProviderResponse, TokenUsage
    from app.services.agent import GeneratedBatch, GeneratedQuestion

    key = _pool_key(5, "dogal_sayilar", None, "orta")
    _seed_pool(key, 20, critic_pass=1, question_type=QuestionType.ISLEM)

    def fake_chain(**kw):
        qs = [
            GeneratedQuestion(
                question=f"llm-üretimi sözel: {_POOL_STEMS[(i + 20) % len(_POOL_STEMS)]}",
                answer=str(i), solution_steps="adım", kazanim_kod="MAT.5.1.1.1",
                question_type=QuestionType.SOZEL_PROBLEM,
            )
            for i in range(9)
        ]
        return ProviderResponse(
            parsed=GeneratedBatch(questions=qs), model_name="gemini-2.5-flash",
            provider="gemini",
            usage=TokenUsage(input_tokens=500, output_tokens=500,
                             model_name="gemini-2.5-flash"),
        )

    agent, _ = _make_agent(monkeypatch, fake_chain)
    monkeypatch.setattr(settings, "enable_pool_first_serving", True)
    monkeypatch.setattr(settings, "enable_spare_pool", True)
    monkeypatch.setattr(settings, "pool_first_respect_type_mix", True)  # ← test konusu
    monkeypatch.setattr(settings, "enable_critic", False)
    monkeypatch.setattr(settings, "enable_math_verifier", False)
    monkeypatch.setattr(settings, "generation_overshoot_ratio", 1.0)

    questions = agent.generate(
        grade=5, topic_id="dogal_sayilar", kazanim_kod=None,
        difficulty=Difficulty.ORTA, question_count=10,
    )

    assert len(questions) == 10
    islem_count = sum(1 for q in questions if q.question_type == QuestionType.ISLEM)
    assert islem_count == 1, f"tip kotası aşılmamalı (beklenen 1), gelen: {islem_count}"
    assert any(q.question_type != QuestionType.ISLEM for q in questions), (
        "kağıt TEK TİPE düşmemeli — depo tek tip taşısa bile diğer tipler LLM'den gelmeli"
    )
    trace = agent.build_last_trace()
    assert trace.pool_hit_count == 1, "yalnız islem kotası kadarı (1) depodan gelmeli"


def test_pool_first_type_mix_disabled_allows_single_type_collapse(monkeypatch):
    """Regresyon kilidi: `pool_first_respect_type_mix=False` iken eski (tip-farkında
    OLMAYAN) davranış korunur — kovada tek tip varsa kağıt o tipe TAMAMEN
    düşebilir (bu, bayrağın 'eskiye dönüş' sözleşmesi)."""
    key = _pool_key(5, "dogal_sayilar", None, "orta")
    _seed_pool(key, 10, critic_pass=1, question_type=QuestionType.ISLEM)

    agent, _ = _make_agent(monkeypatch, _no_llm_call, fake_critic_factory=_NoCallCritic)
    monkeypatch.setattr(settings, "enable_pool_first_serving", True)
    monkeypatch.setattr(settings, "enable_spare_pool", True)
    monkeypatch.setattr(settings, "pool_first_respect_type_mix", False)

    questions = agent.generate(
        grade=5, topic_id="dogal_sayilar", kazanim_kod=None,
        difficulty=Difficulty.ORTA, question_count=10,
    )

    assert len(questions) == 10
    assert all(q.question_type == QuestionType.ISLEM for q in questions)


# ------------------------------------------------------------------------
# VARSAYILAN yapılandırma (Opus denetimi 2026-07-28, 3. tur — "tek kalan iş"):
# `_make_agent` diğer testlerde `pool_first_respect_type_mix=False` yapıyor
# (haklı gerekçeyle — `_seed_pool` tek tiple dolduruyor). Ama bu, Faz 2'nin
# ÇEKİRDEK garantilerinin (0 LLM/0 critic, tenant tekrarı, tembel damga kazancı)
# yalnızca ÜRETİMDE HİÇ KULLANILMAYACAK bir yapılandırmada kanıtlandığı
# anlamına geliyordu — bayrak üretimde True. Aşağıdaki testler AYNI üç garantiyi
# VARSAYILAN (bayrak True, tip-farkında) yolda kilitler; `_seed_pool_with_counts`
# gerçek hedef dağılıma (`distribute_question_types`) oturan bir kova kurar.
# ------------------------------------------------------------------------


def test_default_config_pool_fully_satisfies_no_llm_no_critic(monkeypatch):
    """Faz 2'nin ASIL gerekçesi — VARSAYILAN (tip-farkında) yolda: depo GERÇEK
    hedef dağılımın (10 tip × ağırlık 1) TAMAMINI karşılıyorsa 0 LLM üretim
    çağrısı + 0 critic çağrısı, `pool_hit_count == question_count`."""
    from app.services.diversity import distribute_question_types

    key = _pool_key(5, "dogal_sayilar", None, "orta")
    target = distribute_question_types(
        10, Difficulty.ORTA, topic_id="dogal_sayilar", allowed_types=None, yeni_nesil=False,
    )
    assert sum(target.values()) == 10, "test varsayımı: dağıtım 10'a tam otursun"
    _seed_pool_with_counts(key, target, critic_pass=1)

    agent, _ = _make_agent(monkeypatch, _no_llm_call, fake_critic_factory=_NoCallCritic)
    monkeypatch.setattr(settings, "enable_pool_first_serving", True)
    monkeypatch.setattr(settings, "enable_spare_pool", True)
    monkeypatch.setattr(settings, "pool_first_respect_type_mix", True)  # ← ÜRETİM varsayılanı

    questions = agent.generate(
        grade=5, topic_id="dogal_sayilar", kazanim_kod=None,
        difficulty=Difficulty.ORTA, question_count=10,
    )

    assert len(questions) == 10
    trace = agent.build_last_trace()
    assert trace.pool_hit_count == 10
    assert trace.model_used == "pool"
    assert trace.provider == "pool"
    assert trace.estimated_cost_usd == 0.0


def test_default_config_same_tenant_never_repeats(monkeypatch):
    """En önemli garanti — VARSAYILAN (tip-farkında) yolda: aynı kullanıcı iki
    `generate()` çağrısında KESİŞMEYEN soru setleri alır. Kova hedef dağılımın
    İKİ KATINI taşır ki her tip için 2. çağrıda da tam kota kalsın."""
    from app.services.diversity import distribute_question_types

    key = _pool_key(5, "dogal_sayilar", None, "orta")
    target = distribute_question_types(
        10, Difficulty.ORTA, topic_id="dogal_sayilar", allowed_types=None, yeni_nesil=False,
    )
    double_counts = {qt: n * 2 for qt, n in target.items()}
    _seed_pool_with_counts(key, double_counts, critic_pass=1)

    from app.services.history import GenerationHistory

    hist = GenerationHistory(persist=False)
    agent, _ = _make_agent(monkeypatch, _no_llm_call, fake_critic_factory=_NoCallCritic, history=hist)
    monkeypatch.setattr(settings, "enable_pool_first_serving", True)
    monkeypatch.setattr(settings, "enable_spare_pool", True)
    monkeypatch.setattr(settings, "pool_first_respect_type_mix", True)

    first = agent.generate(
        grade=5, topic_id="dogal_sayilar", kazanim_kod=None,
        difficulty=Difficulty.ORTA, question_count=10, tenant_id="ogretmen-A",
    )
    second = agent.generate(
        grade=5, topic_id="dogal_sayilar", kazanim_kod=None,
        difficulty=Difficulty.ORTA, question_count=10, tenant_id="ogretmen-A",
    )

    assert len(first) == 10 and len(second) == 10
    first_texts = {q.question for q in first}
    second_texts = {q.question for q in second}
    assert not (first_texts & second_texts), (
        "aynı kullanıcı iki çağrıda AYNI soruyu almamalı (tip-farkında yolda da)"
    )


def test_default_config_critic_pass_one_skips_critic(monkeypatch):
    """Tembel damganın asıl kazancı — VARSAYILAN (tip-farkında) yolda: tüm
    satırlar `critic_pass=1` olduğunda critic HİÇ çağrılmaz VE hiçbir satır
    yeniden damgalanmaz (DB'de değişiklik yok, olduğu gibi kalır)."""
    from app.services.diversity import distribute_question_types
    from app.services.diversity import normalize_question

    key = _pool_key(5, "dogal_sayilar", None, "orta")
    target = distribute_question_types(
        10, Difficulty.ORTA, topic_id="dogal_sayilar", allowed_types=None, yeni_nesil=False,
    )
    _seed_pool_with_counts(key, target, critic_pass=1)
    before = {
        (r[0], r[1]) for r in SPARE_POOL._db.execute(
            "SELECT norm_question, verified_at FROM spare_questions WHERE pool_key = ?",
            (key,),
        ).fetchall()
    }

    agent, _ = _make_agent(monkeypatch, _no_llm_call, fake_critic_factory=_NoCallCritic)
    monkeypatch.setattr(settings, "enable_pool_first_serving", True)
    monkeypatch.setattr(settings, "enable_spare_pool", True)
    monkeypatch.setattr(settings, "pool_first_respect_type_mix", True)

    questions = agent.generate(
        grade=5, topic_id="dogal_sayilar", kazanim_kod=None,
        difficulty=Difficulty.ORTA, question_count=10,
    )

    assert len(questions) == 10
    after = {
        (r[0], r[1]) for r in SPARE_POOL._db.execute(
            "SELECT norm_question, verified_at FROM spare_questions WHERE pool_key = ?",
            (key,),
        ).fetchall()
    }
    assert before == after, "critic hiç çağrılmadığından hiçbir satır yeniden damgalanmamalı"


def test_pool_first_type_deficit_isolated_surplus_type_not_reinflated(monkeypatch):
    """Sınır durumu (Opus denetimi 2026-07-28, 3. tur, madde 3): bir tipte
    FAZLASIYLA stok, başka bir tipte HİÇ stok yokken — fazla olan tip KOTASINI
    aşmamalı (kağıt hedef dağılımdan sapmamalı) ve LLM'e giden `distribution`
    YALNIZ eksik tipi istemeli (fazla olan tipi YENİDEN ŞİŞİRMEMELİ)."""
    from app.services import agent as A
    from app.services.diversity import distribute_question_types
    from app.services.llm_providers import ProviderResponse, TokenUsage
    from app.services.agent import GeneratedBatch, GeneratedQuestion

    key = _pool_key(5, "dogal_sayilar", None, "orta")
    target = distribute_question_types(
        10, Difficulty.ORTA, topic_id="dogal_sayilar", allowed_types=None, yeni_nesil=False,
    )
    SURPLUS_TYPE = QuestionType.SALT_ISLEM
    MISSING_TYPE = QuestionType.KAVRAM_SORUSU
    assert target.get(SURPLUS_TYPE, 0) >= 1 and target.get(MISSING_TYPE, 0) >= 1, (
        "test varsayımı: her iki tip de hedef dağıtımda yer almalı"
    )

    counts = dict(target)
    counts[SURPLUS_TYPE] = target[SURPLUS_TYPE] + 4  # kotanın ÜSTÜNDE stok
    counts[MISSING_TYPE] = 0  # HİÇ yok
    _seed_pool_with_counts(key, counts, critic_pass=1)

    captured: dict = {}
    real_build_prompt = A.build_user_prompt

    def _spy_build_prompt(**kw):
        captured["distribution"] = dict(kw.get("distribution") or {})
        return real_build_prompt(**kw)

    def fake_chain(**kw):
        qs = [
            GeneratedQuestion(
                question=f"llm-üretimi eksik-tip: {_POOL_STEMS[0]}",
                answer="1", solution_steps="adım", kazanim_kod="MAT.5.1.1.1",
                question_type=MISSING_TYPE,
            )
        ]
        return ProviderResponse(
            parsed=GeneratedBatch(questions=qs), model_name="gemini-2.5-flash",
            provider="gemini",
            usage=TokenUsage(input_tokens=200, output_tokens=200,
                             model_name="gemini-2.5-flash"),
        )

    agent, _ = _make_agent(monkeypatch, fake_chain)
    monkeypatch.setattr(A, "build_user_prompt", _spy_build_prompt)
    monkeypatch.setattr(settings, "enable_pool_first_serving", True)
    monkeypatch.setattr(settings, "enable_spare_pool", True)
    monkeypatch.setattr(settings, "pool_first_respect_type_mix", True)
    monkeypatch.setattr(settings, "enable_critic", False)
    monkeypatch.setattr(settings, "enable_math_verifier", False)
    monkeypatch.setattr(settings, "generation_overshoot_ratio", 1.0)

    questions = agent.generate(
        grade=5, topic_id="dogal_sayilar", kazanim_kod=None,
        difficulty=Difficulty.ORTA, question_count=10,
    )

    assert len(questions) == 10
    surplus_count = sum(1 for q in questions if q.question_type == SURPLUS_TYPE)
    missing_count = sum(1 for q in questions if q.question_type == MISSING_TYPE)
    assert surplus_count == target[SURPLUS_TYPE], (
        f"fazla stoklu tip KOTAsını aşmamalı (beklenen {target[SURPLUS_TYPE]}, gelen {surplus_count})"
    )
    assert missing_count == target[MISSING_TYPE]

    # LLM'e verilen dağıtım YALNIZ eksik tipi istemeli — fazlası olan tip
    # (SURPLUS_TYPE) `distribution`'da HİÇ görünmemeli (yeniden şişirilmemeli).
    assert captured["distribution"] == {MISSING_TYPE: target[MISSING_TYPE]}
    assert SURPLUS_TYPE not in captured["distribution"]

    trace = agent.build_last_trace()
    assert trace.pool_hit_count == 10 - target[MISSING_TYPE]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
