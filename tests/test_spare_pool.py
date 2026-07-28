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
    PoolItem,
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


# --------------------------------- şema genişletmesi (Faz 1, §3d — soru deposu)

def test_pool_add_many_writes_new_columns():
    """Yeni kolonlar (subject/grade/unit_id/kazanim_kod/question_type/difficulty/
    source) add_many ile yazılıyor mu — ham SQL ile doğrula (take() yalnız
    Question döner, kolonlara erişmez)."""
    key = _pool_key(5, "dogal_sayilar", None, "orta")
    q = _q(0, "Ali 3 elma aldı, kaç elması var?")
    SPARE_POOL.add_many(
        key, [q],
        subject="matematik", grade=5, unit_id="dogal_sayilar",
        difficulty="orta", source="live-overshoot",
    )
    row = SPARE_POOL._db.execute(
        "SELECT subject, grade, unit_id, kazanim_kod, question_type, difficulty, source "
        "FROM spare_questions WHERE pool_key = ?",
        (key,),
    ).fetchone()
    assert row == ("matematik", 5, "dogal_sayilar", "MAT.5.1.1.1", "islem", "orta", "live-overshoot")


def test_pool_question_id_is_deterministic_content_hash():
    """question_id = sha1(norm_question)[:16] — aynı soru İKİ farklı pool_key'de
    bile aynı question_id'yi almalı (kalıcı kimlik içerik hash'idir, pool_key'e
    bağlı değil — ileride quiz cevaplarıyla eşleşecek §3d)."""
    import hashlib

    from app.services.diversity import normalize_question

    key_a = _pool_key(5, "dogal_sayilar", None, "orta")
    key_b = _pool_key(6, "kesirler", None, "zor")
    q = _q(0, "Sabit soru metni, kaç tane kaldı?")
    SPARE_POOL.add_many(key_a, [q])
    SPARE_POOL.add_many(key_b, [q])
    norm_q = normalize_question(q.question)
    expected = hashlib.sha1(norm_q.encode("utf-8")).hexdigest()[:16]
    rows = SPARE_POOL._db.execute(
        "SELECT DISTINCT question_id FROM spare_questions WHERE norm_question = ?",
        (norm_q,),
    ).fetchall()
    assert [r[0] for r in rows] == [expected]


def test_pool_critic_pass_and_verifier_model_stamped_when_provided():
    """'Bedava damga' (§3c): critic_pass/verifier_model geçilirse satıra yazılır,
    verified_at otomatik doldurulur (denetim zaman damgası)."""
    from app.services.diversity import normalize_question

    key = _pool_key(5, "dogal_sayilar", None, "orta")
    q = _q(1, "Bir teslim edilen soru, kaç tane kaldı?")
    SPARE_POOL.add_many(
        key, [q], source="live-delivered", critic_pass=1,
        verifier_model="gemini-2.5-flash-lite",
    )
    row = SPARE_POOL._db.execute(
        "SELECT critic_pass, verifier_model, verified_at, source FROM spare_questions "
        "WHERE pool_key = ? AND norm_question = ?",
        (key, normalize_question(q.question)),
    ).fetchone()
    assert row[0] == 1
    assert row[1] == "gemini-2.5-flash-lite"
    assert row[2] is not None, "verified_at critic_pass verilince otomatik dolmalı"
    assert row[3] == "live-delivered"


def test_pool_unstamped_overshoot_has_null_critic_pass():
    """Hiç denetlenmemiş artanlar critic_pass=NULL ile girer (Faz 2'de ilk servis
    anında tembel damgalanacak) — peşin damga yanlış bilgi olurdu."""
    from app.services.diversity import normalize_question

    key = _pool_key(5, "dogal_sayilar", None, "orta")
    q = _q(2, "Denetlenmemiş bir soru, kaç tane kaldı?")
    SPARE_POOL.add_many(key, [q], source="live-overshoot")
    row = SPARE_POOL._db.execute(
        "SELECT critic_pass, verified_at FROM spare_questions "
        "WHERE pool_key = ? AND norm_question = ?",
        (key, normalize_question(q.question)),
    ).fetchone()
    assert row[0] is None
    assert row[1] is None


def test_schema_migration_idempotent_on_populated_table():
    """Dolu tablo üzerinde `_init_db()` iki kez çağrılsa da mevcut veriler
    bozulmaz/silinmez ve istisna fırlatmaz (prod'da Turso'da dolu tabloya
    uygulanacak migrasyonun simülasyonu)."""
    key = _pool_key(5, "dogal_sayilar", None, "orta")
    SPARE_POOL.add_many(key, [_q(3, "Migrasyon testi sorusu, kaç tane kaldı?")])
    before = SPARE_POOL._db.execute("SELECT COUNT(*) FROM spare_questions").fetchone()[0]
    # Yeniden başlatma simülasyonu — istisna fırlatmamalı.
    SPARE_POOL._init_db()
    SPARE_POOL._init_db()
    after = SPARE_POOL._db.execute("SELECT COUNT(*) FROM spare_questions").fetchone()[0]
    assert before == after == 1, "migrasyon mevcut satırları bozmamalı/silmemeli"


def test_backfill_fills_question_id_for_legacy_rows():
    """Migrasyon öncesi yazılmış (question_id NULL) satırlar `_init_db()` çağrıldığında
    `norm_question`'dan tek seferlik best-effort backfill ile doldurulur."""
    import hashlib

    from app.services.diversity import normalize_question

    key = _pool_key(5, "dogal_sayilar", None, "orta")
    q = _q(4, "Eski satır simülasyonu, kaç tane kaldı?")
    norm_q = normalize_question(q.question)
    SPARE_POOL.add_many(key, [q])
    # Eski (migrasyon öncesi) satırı simüle etmek için question_id'yi elle NULL'a çek.
    SPARE_POOL._db.execute(
        "UPDATE spare_questions SET question_id = NULL WHERE pool_key = ? AND norm_question = ?",
        (key, norm_q),
    )
    SPARE_POOL._db.commit()
    SPARE_POOL._init_db()  # backfill tetiklenir
    row = SPARE_POOL._db.execute(
        "SELECT question_id FROM spare_questions WHERE pool_key = ? AND norm_question = ?",
        (key, norm_q),
    ).fetchone()
    expected = hashlib.sha1(norm_q.encode("utf-8")).hexdigest()[:16]
    assert row[0] == expected


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


def test_delivered_questions_stored_live_delivered_and_rejected_excluded(monkeypatch):
    """İş 3 (§3b-1, docs/COST_QUALITY_V2_PLAN.md): generate() sonunda TESLİM EDİLEN
    sorular `source='live-delivered'` + `critic_pass=1` ile depoya yazılır (bedava
    damga — critic zaten üretim sırasında geçti). Critic'in REDDETTİĞİ sorular
    depoda HİÇ görünmez — depo çöp biriktirmemeli."""
    from app.services import agent as A
    from app.services.agent import GeneratedBatch, GeneratedQuestion, GeminiAgent
    from app.services.critic import CriticVerdict
    from app.services.diversity import normalize_question
    from app.services.llm_providers import ProviderResponse, TokenUsage

    REJECTED_MARKER = "reddedilecek-soru-imzasi"

    def fake_chain(**kw):
        qs = []
        for i in range(10):
            stem = _STEMS[i % len(_STEMS)].format(n=i + 1)
            # İlk 3 soru critic'te reddedilecek — imza METNE gömülü (sayıya değil,
            # normalize_question sayıları <N>'e indirger; imza kelime olduğundan
            # dedup'ta çakışmaz).
            text = f"{REJECTED_MARKER}: {stem}" if i < 3 else stem
            qs.append(
                GeneratedQuestion(
                    question=text, answer=str(i), solution_steps="adım",
                    kazanim_kod="MAT.5.1.1.1", question_type=QuestionType.ISLEM,
                )
            )
        return ProviderResponse(
            parsed=GeneratedBatch(questions=qs), model_name="gemini-2.5-flash",
            provider="gemini",
            usage=TokenUsage(input_tokens=500, output_tokens=1000,
                             model_name="gemini-2.5-flash"),
        )

    class _FakeCritic:
        _last_usage = TokenUsage(input_tokens=5, output_tokens=5,
                                 model_name="gemini-2.5-flash-lite")

        def evaluate(self, questions, kazanimlar, difficulty, context=""):
            return [
                CriticVerdict(
                    question_index=i,
                    is_valid=REJECTED_MARKER not in questions[i].question,
                    confidence=0.95,
                )
                for i in range(len(questions))
            ]

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
    # Overshoot kapalı: 10 üretilir, 7 istenir, 3'ü doğal fazla (basit senaryo).
    monkeypatch.setattr(settings, "generation_overshoot_ratio", 1.0)

    agent = GeminiAgent()
    agent.thinking_budget = 512
    agent._gemini_provider = None
    agent._anthropic_provider = None
    agent._embedder = None
    agent._critics = {}

    questions = agent.generate(
        grade=5, topic_id="dogal_sayilar", kazanim_kod=None,
        difficulty=Difficulty.ORTA, question_count=7,
    )

    assert len(questions) == 7
    assert all(REJECTED_MARKER not in q.question for q in questions), (
        "reddedilen sorular teslim edilen sette OLMAMALI"
    )

    key = _pool_key(5, "dogal_sayilar", None, "orta")
    rows = SPARE_POOL._db.execute(
        "SELECT norm_question, source, critic_pass, verifier_model FROM spare_questions "
        "WHERE pool_key = ?",
        (key,),
    ).fetchall()
    stored_norms = {r[0] for r in rows}

    # Teslim edilen 7 sorunun HEPSİ depoda, 'live-delivered' + critic_pass=1 ile.
    delivered_norms = {normalize_question(q.question) for q in questions}
    assert delivered_norms <= stored_norms, "teslim edilen sorular depoya yazılmalı"
    for norm_q, source, critic_pass, verifier_model in rows:
        if norm_q in delivered_norms:
            assert source == "live-delivered"
            assert critic_pass == 1, "bedava damga: teslim edilen zaten critic'ten geçti"
            assert verifier_model == settings.critic_model

    # Critic'in reddettiği sorular depoda HİÇ YOK (depo çöp biriktirmemeli).
    assert not any(REJECTED_MARKER in n for n in stored_norms), (
        "elenen sorular depoya asla girmemeli"
    )


def test_delivered_questions_not_stamped_when_critic_fails_open(monkeypatch):
    """MUST-FIX 2 (denetim 2026-07-28): critic çağrı/parse hatasında BOŞ liste
    döner ve ana geçiş (agent.py) hiçbir soruyu düşürmez — COST_REDUCTION_PLAN
    §3.2'deki arıza modu (64K'ya dayanıp JSON kesilmesi vb.). Bu durumda teslim
    edilen sorular depoya YAZILIR (elenmediler, gerçekten teslim edildiler) ama
    `critic_pass` NULL kalmalı — 'denetlendi, geçti' YALANI depoya yazılmamalı,
    aksi halde Faz 2'nin tembel damgası bu soruları bir daha asla denetlemez."""
    from app.services import agent as A
    from app.services.agent import GeneratedBatch, GeneratedQuestion, GeminiAgent
    from app.services.diversity import normalize_question
    from app.services.llm_providers import ProviderResponse, TokenUsage

    def fake_chain(**kw):
        qs = [
            GeneratedQuestion(
                question=_STEMS[i % len(_STEMS)].format(n=i + 1),
                answer=str(i), solution_steps="adım", kazanim_kod="MAT.5.1.1.1",
                question_type=QuestionType.ISLEM,
            )
            for i in range(5)
        ]
        return ProviderResponse(
            parsed=GeneratedBatch(questions=qs), model_name="gemini-2.5-flash",
            provider="gemini",
            usage=TokenUsage(input_tokens=500, output_tokens=500,
                             model_name="gemini-2.5-flash"),
        )

    class _FailOpenCritic:
        """Gerçek `GeminiCritic.evaluate()`'in parse/API hatasında yaptığı gibi
        BOŞ liste döner — hiçbir soruyu düşürmez (fail-open)."""

        _last_usage = TokenUsage(input_tokens=5, output_tokens=5,
                                 model_name="gemini-2.5-flash-lite")

        def evaluate(self, questions, kazanimlar, difficulty, context=""):
            return []

    from app.services.history import GenerationHistory

    monkeypatch.setattr(A, "GENERATION_HISTORY", GenerationHistory(persist=False))
    monkeypatch.setattr(A, "call_with_chain", fake_chain)
    monkeypatch.setattr(A, "_collect_few_shot", lambda *a, **k: ([], "static"))
    monkeypatch.setattr(A, "_collect_textbook_context", lambda *a, **k: [])
    monkeypatch.setattr(GeminiAgent, "_get_critic", lambda self, subject=None: _FailOpenCritic())
    monkeypatch.setattr(GeminiAgent, "__init__", lambda self, **kw: None)
    monkeypatch.setattr(settings, "enable_semantic_dedup", False)
    monkeypatch.setattr(settings, "enable_math_verifier", False)
    monkeypatch.setattr(settings, "enable_critic", True)
    monkeypatch.setattr(settings, "enable_generation_cache", False)
    monkeypatch.setattr(settings, "generation_overshoot_ratio", 1.0)

    agent = GeminiAgent()
    agent.thinking_budget = 512
    agent._gemini_provider = None
    agent._anthropic_provider = None
    agent._embedder = None
    agent._critics = {}

    questions = agent.generate(
        grade=5, topic_id="dogal_sayilar", kazanim_kod=None,
        difficulty=Difficulty.ORTA, question_count=5,
    )

    assert len(questions) == 5, "critic fail-open iken de sorular teslim edilmeli"

    key = _pool_key(5, "dogal_sayilar", None, "orta")
    delivered_norms = {normalize_question(q.question) for q in questions}
    rows = SPARE_POOL._db.execute(
        "SELECT norm_question, source, critic_pass, verifier_model FROM spare_questions "
        "WHERE pool_key = ?",
        (key,),
    ).fetchall()
    stored = {r[0]: (r[1], r[2], r[3]) for r in rows}

    assert delivered_norms <= set(stored), "teslim edilen sorular yine de depoya yazılmalı"
    for norm_q in delivered_norms:
        source, critic_pass, verifier_model = stored[norm_q]
        assert source == "live-delivered"
        assert critic_pass is None, (
            "critic fail-open iken critic_pass=1 YALANI yazılmamalı (fail-CLOSED)"
        )
        assert verifier_model is None


# ------------------------------------------- Faz 2 (§3c): take_for_serving() + stamp()


def test_take_for_serving_returns_critic_pass_status():
    """`take_for_serving()` `take()` ile AYNI soruları döner ama her satırın
    `critic_pass` durumunu (`PoolItem.critic_pass`) da taşır — agent.py bununla
    'bedava' (1) / 'denetlenecek' (NULL) satırları ayırt eder."""
    key = _pool_key(5, "dogal_sayilar", None, "orta")
    q1 = _q(0, "Bedava soru, kaç tane kaldı?")
    q2 = _q(1, "Denetlenecek soru, kaç tane kaldı?")
    SPARE_POOL.add_many(key, [q1], source="live-delivered", critic_pass=1,
                         verifier_model="gemini-2.5-flash-lite")
    SPARE_POOL.add_many(key, [q2], source="live-overshoot")

    items = SPARE_POOL.take_for_serving(key, 10)
    assert all(isinstance(it, PoolItem) for it in items)
    by_text = {it.question.question: it.critic_pass for it in items}
    assert by_text[q1.question] == 1
    assert by_text[q2.question] is None


def test_take_for_serving_never_returns_critic_pass_zero_rows():
    """`critic_pass = 0` (critic'in reddettiği) satırlar `take_for_serving()`
    tarafından ASLA döndürülmez — reddedilen soru bir daha hiçbir isteğe gitmez."""
    from app.services.diversity import normalize_question

    key = _pool_key(5, "dogal_sayilar", None, "orta")
    rejected = _q(0, "Reddedilmiş soru, kaç tane kaldı?")
    ok = _q(1, "Geçerli soru, kaç tane kaldı?")
    SPARE_POOL.add_many(key, [rejected, ok])
    SPARE_POOL.stamp(
        key, [normalize_question(rejected.question)],
        critic_pass=0, verifier_model="gemini-2.5-flash-lite",
    )
    items = SPARE_POOL.take_for_serving(key, 10)
    texts = {it.question.question for it in items}
    assert rejected.question not in texts
    assert ok.question in texts
    # `take()` (eski API) da AYNI kuralı uygular.
    assert rejected.question not in {q.question for q in SPARE_POOL.take(key, 10)}


def test_take_for_serving_prefers_critic_pass_1_over_null():
    """Sıralama önce `critic_pass = 1` (bedava, LLM'siz), sonra NULL (denetlenecek)
    olacak şekilde — bedava sorular ÖNCE tükensin (Faz 2'nin asıl kazancı)."""
    # DİKKAT: normalize_question sayıları `<N>`'e indirger — şablon+sayı yerine
    # HER SORU farklı KELİMELERLE kurulmalı, aksi halde unique index'e çarpıp
    # tek satıra düşerler (bkz. dosya başındaki `_STEMS` notu).
    key = _pool_key(6, "kesirler", None, "kolay")
    verified = [
        _q(0, "Ayşe bahçeye fidan dikti, kaç fidan tuttu?"),
        _q(1, "Mehmet markette ekmek aldı, kaç ekmek kaldı?"),
        _q(2, "Kütüphaneye kitap bağışlandı, kaç kitap rafta?"),
    ]
    unverified = [
        _q(0, "Ali okula kalem getirdi, kaç kalem verdi?"),
        _q(1, "Zeynep pazardan meyve topladı, kaç meyve sattı?"),
        _q(2, "Sınıfta resim yarışması yapıldı, kaç resim asıldı?"),
    ]
    SPARE_POOL.add_many(key, unverified)  # ÖNCE eklenen (created_at daha eski)
    SPARE_POOL.add_many(key, verified, source="live-delivered", critic_pass=1,
                         verifier_model="gemini-2.5-flash-lite")
    items = SPARE_POOL.take_for_serving(key, 3)
    assert all(it.critic_pass == 1 for it in items), (
        "created_at daha eski olsa bile critic_pass=1 satırlar ÖNCE dönmeli"
    )


def test_stamp_updates_existing_null_row_to_pass_or_fail():
    """`stamp()` — tembel damga (§3c): `add_many`'nin INSERT OR IGNORE'unun
    GÜNCELLEYEMEDİĞİ mevcut satırı bir UPDATE ile damgalar."""
    from app.services.diversity import normalize_question

    key = _pool_key(5, "dogal_sayilar", None, "orta")
    q = _q(0, "Damgalanacak soru, kaç tane kaldı?")
    SPARE_POOL.add_many(key, [q])  # critic_pass NULL girer
    norm_q = normalize_question(q.question)

    n = SPARE_POOL.stamp(
        key, [norm_q], critic_pass=1, critic_confidence=0.92,
        verifier_model="gemini-2.5-flash-lite",
    )
    assert n == 1
    row = SPARE_POOL._db.execute(
        "SELECT critic_pass, critic_confidence, verifier_model, verified_at "
        "FROM spare_questions WHERE pool_key = ? AND norm_question = ?",
        (key, norm_q),
    ).fetchone()
    assert row[0] == 1 and row[1] == 0.92 and row[2] == "gemini-2.5-flash-lite"
    assert row[3] is not None

    # add_many'nin INSERT OR IGNORE'u bu satırı GÜNCELLEMEZ (regresyon kilidi):
    # aynı soruyu tekrar (damgasız gibi) eklemeye çalışmak damgayı SİLMEMELİ.
    SPARE_POOL.add_many(key, [q])
    row2 = SPARE_POOL._db.execute(
        "SELECT critic_pass FROM spare_questions WHERE pool_key = ? AND norm_question = ?",
        (key, norm_q),
    ).fetchone()
    assert row2[0] == 1, "add_many mevcut damgayı ezmemeli"


def test_stamp_is_best_effort_never_raises():
    """Havuz DB'si patlasa bile `stamp()` istisna fırlatmaz (bkz.
    `test_pool_is_best_effort_never_raises`)."""
    class _BoomDB:
        def execute(self, *a, **k):
            raise RuntimeError("database is locked")

        def commit(self):
            raise RuntimeError("database is locked")

    key = _pool_key(5, "dogal_sayilar", None, "orta")
    real_db = SPARE_POOL._db
    SPARE_POOL._db = _BoomDB()
    try:
        assert SPARE_POOL.stamp(key, ["bir norm soru"], critic_pass=1) == 0
        assert SPARE_POOL.take_for_serving(key, 5) == []
    finally:
        SPARE_POOL._db = real_db


# ------------------------------------------- MUST-FIX (Opus denetimi 2026-07-28):
# trim KORUMA sıralaması — used_count DEĞİL damga durumu esas alınmalı.


def test_trim_keeps_stamped_rows_even_if_heavily_used():
    """Faz 2'nin ekonomisinin regresyon kilidi. ESKİDEN trim `used_count ASC`
    sıralıyordu → EN AZ kullanılan tutulur, EN ÇOK kullanılan (== en çok
    damgalanıp bedava hâle gelen, `critic_pass=1`) satırlar SİLİNİRDİ; yerine
    `used_count=0` damgasız YENİ satırlar kalırdı — ödediğimiz her damga bir
    sonraki trim'de çöpe giderdi, bedava envanter hiç birikmezdi.

    FIX: trim önce `critic_pass=1` (damgalı, çok kullanılmış olsa bile) korur,
    sonra en yeni damgasız (`NULL`), İLK silinenler `critic_pass=0` (reddedilen,
    'mezar taşı') olur."""
    key = _pool_key(9, "kesirler", None, "zor")
    pool = type(SPARE_POOL)(max_per_key=3)
    try:
        heavy_pass = [
            _q(0, "Çok kullanılan bedava soru A, kaç tane kaldı?"),
            _q(1, "Çok kullanılan bedava soru B, kaç tane kaldı?"),
        ]
        pool.add_many(key, heavy_pass, source="live-delivered", critic_pass=1,
                       verifier_model="gemini-2.5-flash-lite")
        # used_count'u gerçekten yükselt (ESKİ politikada bu satırları SİLİNMEYE
        # aday yapardı — used_count ASC sıralamasında en SONA düşerlerdi).
        for _ in range(10):
            pool.take_for_serving(key, 2)

        rejected = _q(2, "Reddedilmiş soru, kaç tane kaldı?")
        pool.add_many(key, [rejected], critic_pass=0)

        unstamped = [
            _q(3, "Damgasız yeni soru C, kaç tane kaldı?"),
            _q(4, "Damgasız yeni soru D, kaç tane kaldı?"),
        ]
        # cap=3, bu çağrı sonrası TOPLAM 5 satır olur → trim TETİKLENİR.
        pool.add_many(key, unstamped)

        rows = pool._db.execute(
            "SELECT norm_question, critic_pass FROM spare_questions WHERE pool_key = ?",
            (key,),
        ).fetchall()
        assert len(rows) == 3, "cap=3 aşılmamalı"
        surviving = {r[0] for r in rows}
        from app.services.diversity import normalize_question

        assert normalize_question(heavy_pass[0].question) in surviving, (
            "çok kullanılmış AMA damgalı satır silinmemeli"
        )
        assert normalize_question(heavy_pass[1].question) in surviving, (
            "çok kullanılmış AMA damgalı satır silinmemeli"
        )
        assert normalize_question(rejected.question) not in surviving, (
            "critic_pass=0 (reddedilen) İLK silinmeli"
        )
    finally:
        pool.clear()


def test_add_many_does_not_reset_rejected_row_stamp_on_regeneration():
    """MUST-FIX madde 3: `critic_pass=0` bir satır "yeniden üretilirse" (aynı
    `norm_question` tekrar `add_many`'e verilirse) damgası NULL'a DÖNMEMELİ —
    `INSERT OR IGNORE` unique index'e çarpıp sessizce atlanır, mezar taşı korunur."""
    from app.services.diversity import normalize_question

    key = _pool_key(5, "dogal_sayilar", None, "orta")
    q = _q(0, "Reddedilecek soru, yeniden üretilirse kaç tane kaldı?")
    SPARE_POOL.add_many(key, [q])
    norm_q = normalize_question(q.question)
    n = SPARE_POOL.stamp(key, [norm_q], critic_pass=0, verifier_model="gemini-2.5-flash-lite")
    assert n == 1

    # Aynı soru (norm_question AYNI) "yeniden üretilip" depoya eklenmeye
    # çalışılırsa — ör. LLM aynı soruyu tekrar üretti — damga NULL'a dönmemeli.
    SPARE_POOL.add_many(key, [q])
    row = SPARE_POOL._db.execute(
        "SELECT critic_pass FROM spare_questions WHERE pool_key = ? AND norm_question = ?",
        (key, norm_q),
    ).fetchone()
    assert row[0] == 0, "reddedilen soru yeniden üretilince damga NULL'a dönmemeli (mezar taşı)"
    # take()/take_for_serving() de HÂLÂ bu satırı döndürmemeli.
    assert SPARE_POOL.take(key, 10) == []
    assert SPARE_POOL.take_for_serving(key, 10) == []


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
