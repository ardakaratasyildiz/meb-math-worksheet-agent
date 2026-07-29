"""Anonim çeşitlilik kovası — cache'in anonim trafikte çalıştığını kanıtlar.

ÖLÇÜLEN HATA (2026-07-29): `GeminiAgent.generate()` history anahtarını
`tenant_id or DEFAULT_TENANT` ile kuruyordu; `DEFAULT_TENANT="__shared__"`
olduğundan BÜTÜN anonim üretimler tek kovayı paylaşıyordu. Teslim edilen her
soru o kovaya "görülmüş" yazılıyor, `GenerationCache.get()` ise bir cached set'te
TEK BİR görülmüş soru bulunca seti tamamen atlıyor → anonim trafikte cache
yazılıyor ama BİR DAHA ASLA okunamıyordu (canlı defter: 97 üretimde 3 isabet).

Kritik ayrım ve bu dosyanın iki çekirdek testi:
    - FARKLI ziyaretçi (farklı IP) → cache HIT olmalı (kazanç buradan gelir)
    - AYNI ziyaretçi (aynı IP)     → cache HIT OLMAMALI (çeşitlilik korunur)

NOT (bilinçli izolasyon): bu dosya GERÇEK `knowledge_base/history.sqlite3`'e
DOKUNMAZ. Sebebi ölçülmüş bir kirlilik: `GENERATION_CACHE`/`SPARE_POOL`/
`USAGE_LEDGER` modül-seviyesi singleton'lar ve varsayılan olarak o gerçek
dosyaya yazıyor → maliyet defteri test satırlarıyla doluyordu (28 Tem'de 84
uydurma "kağıt", 26 Tem'de 34). İzolasyon `_isolated_cache` fixture'ında
TAZE bir `GenerationCache` örneği kurup `agent` modülündeki adı yamalayarak
yapılır; env değişkeniyle DEĞİL, çünkü singleton'lar import anında kuruluyor ve
tam suite koşusunda başka bir test dosyası app'i önce import edebiliyor.
"""
import os
import sys
import tempfile
import uuid
from pathlib import Path

# CI ("Unit tests" adımı) bu dosyayı `python tests/test_x.py` ile DOĞRUDAN
# çalıştırıyor → repo kökü sys.path'te olmaz. Bkz. memory/ci-eval-runs-tests-directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("GEMINI_API_KEY", "fake-key-for-tests")

import pytest  # noqa: E402

from app.config import settings  # noqa: E402
from app.models.enums import Difficulty, QuestionType  # noqa: E402
from app.services.anon_bucket import PREFIX, anon_variation_key, client_ip  # noqa: E402

_REAL_DB = "history.sqlite3"


@pytest.fixture
def _isolated_cache(monkeypatch):
    """Geçici dosyaya bağlı TAZE cache + depo; `agent` modülündeki adları yamalar."""
    from app.services import agent as A
    from app.services.llm_cache import GenerationCache, SpareQuestionPool

    tmp = os.path.join(tempfile.gettempdir(), f"anon_bucket_{uuid.uuid4().hex}.sqlite3")
    # db_path AÇIKÇA geçilir (settings'e güvenilmez): singleton'lar import anında
    # kuruluyor, tam suite koşusunda başka dosya app'i önce import edebiliyor.
    cache = GenerationCache(db_path=tmp, max_per_key=settings.generation_cache_max_per_key)
    pool = SpareQuestionPool(db_path=tmp)
    assert _REAL_DB not in cache._db_path, "cache GERÇEK DB'ye bağlandı — test iptal"
    monkeypatch.setattr(A, "GENERATION_CACHE", cache)
    monkeypatch.setattr(A, "SPARE_POOL", pool)
    yield cache
    try:
        cache.clear()
        pool.clear()
    finally:
        for suffix in ("", "-wal", "-shm"):
            try:
                os.remove(tmp + suffix)
            except OSError:
                pass


# --------------------------------------------------------------- IP çıkarımı


class _FakeClient:
    def __init__(self, host):
        self.host = host


class _FakeRequest:
    """Sadece anon_bucket'ın okuduğu iki alan: headers + client."""

    def __init__(self, headers=None, host=None):
        self.headers = headers or {}
        self.client = _FakeClient(host) if host else None


def test_client_ip_prefers_forwarded_header():
    """Render proxy'si arkasında `request.client.host` proxy'yi gösterir →
    X-Forwarded-For'un İLK girdisi (gerçek istemci) kullanılmalı."""
    req = _FakeRequest({"x-forwarded-for": "203.0.113.9, 10.0.0.1, 10.0.0.2"}, host="10.0.0.1")
    assert client_ip(req) == "203.0.113.9"


def test_client_ip_falls_back_to_socket():
    assert client_ip(_FakeRequest(host="198.51.100.7")) == "198.51.100.7"
    assert client_ip(_FakeRequest()) is None


def test_variation_key_is_stable_per_ip_and_differs_across_ips():
    a1 = anon_variation_key(_FakeRequest(host="203.0.113.1"))
    a2 = anon_variation_key(_FakeRequest(host="203.0.113.1"))
    b = anon_variation_key(_FakeRequest(host="203.0.113.2"))
    assert a1 == a2, "aynı IP → aynı kova (çeşitlilik penceresi korunmalı)"
    assert a1 != b, "farklı IP → farklı kova (cache paylaşımı açılmalı)"
    assert a1.startswith(PREFIX)


def test_variation_key_does_not_leak_raw_ip():
    """KVKK: ham IP kovada görünmemeli (yalnız HMAC'in ilk 12 hex'i)."""
    ip = "203.0.113.55"
    key = anon_variation_key(_FakeRequest(host=ip))
    assert ip not in key
    assert len(key) == len(PREFIX) + 12


def test_variation_key_none_when_flag_off(monkeypatch):
    """Bayrak kapalı → None → çağıran taraf eski `__shared__` davranışına döner."""
    monkeypatch.setattr(settings, "anon_variation_bucket", False)
    assert anon_variation_key(_FakeRequest(host="203.0.113.1")) is None


def test_salt_change_reshuffles_buckets(monkeypatch):
    req = _FakeRequest(host="203.0.113.1")
    monkeypatch.setattr(settings, "anon_variation_salt", "tuz-a")
    first = anon_variation_key(req)
    monkeypatch.setattr(settings, "anon_variation_salt", "tuz-b")
    assert anon_variation_key(req) != first


# ------------------------------------------- çekirdek: cache anonimde çalışıyor

# DİKKAT (ölçülmüş tuzak): `normalize_question` sayıları `<N>`'e indirger →
# "set1: Ayşe..." ile "set2: Ayşe..." AYNI normalize metne düşer ve ikinci set
# "zaten görülmüş" sayılıp dedup'a takılır (sonra top-up turları çağrı sayacını
# kirletir). Bu yüzden her çağrı KELİME OLARAK farklı stem'ler almalı — marker
# eklemek YETMEZ. Bkz. tests/test_pool_first.py başlığındaki aynı uyarı.
_STEMS = [
    # 1. çağrı
    "Ayşe bahçeye fidan dikti, kaç fidan tuttu?",
    "Mehmet markette ekmek aldı, kaç ekmek kaldı?",
    "Kütüphaneye kitap bağışlandı, kaç kitap rafta?",
    "Ali okula kalem getirdi, kaç kalem verdi?",
    "Zeynep pazardan meyve topladı, kaç meyve sattı?",
    # 2. çağrı
    "Sınıfta resim yarışması yapıldı, kaç resim asıldı?",
    "Çiftlikte tavuk sayıldı, kaçı yumurtladı?",
    "Trende vagon vardı, kaçı doluydu?",
    "Fırında ekmek pişti, kaçı satıldı?",
    "Bahçede çiçek açtı, kaçı soldu?",
    # 3. çağrı
    "Otobüste yolcu vardı, kaçı indi?",
    "Kasada lira birikti, ne kadar harcandı?",
    "Öğretmen defter dağıttı, kaç defter kaldı?",
    "Manavda karpuz satıldı, kaçı bozuktu?",
    "Sıraya öğrenci girdi, sıra kaç kişilik?",
    # 4. çağrı
    "Terzi düğme dikti, kaç düğme arttı?",
    "Kasap et tarttı, kaç kilo kaldı?",
    "Postacı mektup dağıttı, kaç mektup kaldı?",
    "Bakkal şeker sattı, kaç paket kaldı?",
    "Ressam tablo çizdi, kaçı satıldı?",
]
_PER_CALL = 5


def _questions(call_no: int):
    """`call_no`. çağrı için 5 adet KELİME OLARAK farklı soru (bkz. yukarıdaki uyarı)."""
    from app.services.agent import GeneratedQuestion

    start = ((call_no - 1) * _PER_CALL) % len(_STEMS)
    stems = _STEMS[start:start + _PER_CALL]
    assert len(stems) == _PER_CALL, "stem havuzu tükendi — _STEMS'e yeni blok ekle"
    return [
        GeneratedQuestion(
            question=s,
            answer=str(i),
            solution_steps="adım",
            kazanim_kod="MAT.5.1.1.1",
            question_type=QuestionType.ISLEM,
        )
        for i, s in enumerate(stems)
    ]


class _AcceptAllCritic:
    """Her soruyu geçirir — critic AĞA ÇIKMAMALI (aksi halde test gerçek
    Gemini'ye vurup 503 retry'a giriyor ve çağrı sayacı anlamsızlaşıyor)."""

    def __init__(self):
        from app.services.llm_providers import TokenUsage

        self._last_usage = TokenUsage(
            input_tokens=5, output_tokens=5, model_name="gemini-2.5-flash-lite"
        )

    def evaluate(self, questions, kazanimlar, difficulty, context=""):
        from app.services.critic import CriticVerdict

        return [
            CriticVerdict(question_index=i, is_valid=True, confidence=0.9)
            for i in range(len(questions))
        ]


def _agent(monkeypatch, fake_chain):
    """Cache AÇIK, depo KAPALI agent — bu dosya cache katmanını izole eder."""
    from app.services import agent as A
    from app.services.agent import GeminiAgent
    from app.services.history import GenerationHistory

    monkeypatch.setattr(settings, "enable_generation_cache", True)
    monkeypatch.setattr(settings, "enable_pool_first_serving", False)
    monkeypatch.setattr(settings, "enable_spare_pool", False)
    # Üretimdeki asıl senaryo: görülmüş-set tavansız (2026-07-28 varsayılanı).
    monkeypatch.setattr(settings, "history_seen_unbounded", True)
    # Overshoot 1.0: fake chain tam `question_count` kadar soru döndürüyor; 1.8'de
    # hedef 9 olur, 5 gelir ve top-up turları çağrı sayacını kirletir. Bu dosyanın
    # ölçtüğü şey cache isabeti — overshoot davranışı test_pool_first'ün işi.
    monkeypatch.setattr(settings, "generation_overshoot_ratio", 1.0)

    # TEK paylaşılan history örneği = üretimdeki modül singleton'ının eşleniği.
    hist = GenerationHistory(persist=False)
    monkeypatch.setattr(A, "GENERATION_HISTORY", hist)
    monkeypatch.setattr(A, "call_with_chain", fake_chain)
    monkeypatch.setattr(A, "_collect_few_shot", lambda *a, **k: ([], "static"))
    monkeypatch.setattr(A, "_collect_textbook_context", lambda *a, **k: [])
    monkeypatch.setattr(
        GeminiAgent, "_get_critic", lambda self, subject=None: _AcceptAllCritic()
    )
    monkeypatch.setattr(GeminiAgent, "__init__", lambda self, **kw: None)

    agent = GeminiAgent()
    agent.thinking_budget = 0
    agent.model = "gemini-2.5-flash"
    agent._gemini_provider = None
    agent._anthropic_provider = None
    agent._embedder = None
    agent._critics = {}
    return agent


def _gen(agent, *, variation_key):
    return agent.generate(
        grade=5, topic_id="dogal_sayilar", kazanim_kod=None,
        difficulty=Difficulty.ORTA, question_count=5,
        variation_key=variation_key,
    )


class _Chain:
    """LLM yerine HER çağrıda FARKLI bir set döndürür; çağrı sayısını sayar.

    Setlerin farklı olması şart: aynı olsalardı "cache mi yoksa taze üretim mi"
    ayırt edilemezdi. `calls` sayacı testlerin asıl ölçütü.
    """

    def __init__(self):
        self.calls = 0

    def __call__(self, **kw):
        from app.services.agent import GeneratedBatch
        from app.services.llm_providers import ProviderResponse, TokenUsage

        self.calls += 1
        return ProviderResponse(
            parsed=GeneratedBatch(questions=_questions(self.calls)),
            model_name="gemini-2.5-flash",
            provider="gemini",
            usage=TokenUsage(
                input_tokens=500, output_tokens=500, model_name="gemini-2.5-flash"
            ),
        )


def test_second_visitor_gets_cache_hit(monkeypatch, _isolated_cache):
    """ASIL KAZANÇ: ziyaretçi A üretir → ziyaretçi B (farklı IP) cache'ten okur.

    Düzeltmeden önce her ikisi de `__shared__` kovasındaydı: A'nın soruları
    ortak görülmüş-sete yazılıyor, B'nin cache lookup'ı o yüzden set'i atlıyor
    ve B de sıfırdan (paralı) üretim yapıyordu.
    """
    chain = _Chain()
    agent = _agent(monkeypatch, chain)
    a = anon_variation_key(_FakeRequest(host="203.0.113.1"))
    b = anon_variation_key(_FakeRequest(host="203.0.113.2"))

    first = _gen(agent, variation_key=a)
    assert chain.calls == 1, "ilk ziyaretçi taze üretmeli"
    assert len(first) == 5

    second = _gen(agent, variation_key=b)
    assert chain.calls == 1, "ikinci ziyaretçi cache'ten okumalı — LLM tekrar çağrılmamalı"
    assert agent._last_cache_hit is True
    assert agent._last_cost_usd == 0
    assert {q.question for q in second} == {q.question for q in first}


def test_same_visitor_does_not_get_the_same_set(monkeypatch, _isolated_cache):
    """ÖDÜN KORUNUYOR: aynı ziyaretçi "yeniden üret" derse aynı kağıdı almaz."""
    chain = _Chain()
    agent = _agent(monkeypatch, chain)
    a = anon_variation_key(_FakeRequest(host="203.0.113.1"))

    first = _gen(agent, variation_key=a)
    second = _gen(agent, variation_key=a)

    assert chain.calls == 2, "aynı ziyaretçi cache'ten OKUMAMALI (çeşitlilik)"
    assert agent._last_cache_hit is False
    assert {q.question for q in second} != {q.question for q in first}


def test_shared_bucket_regression_without_variation_key(monkeypatch, _isolated_cache):
    """Bayrak kapalıyken (variation_key=None) ESKİ hata aynen geri gelir.

    Bu test düzeltmenin gerçekten `variation_key`'den geldiğini kanıtlar:
    iki farklı ziyaretçi de `__shared__`'a düşerse ikinci istek cache'i
    kaçırır ve yeniden üretim yapar.
    """
    chain = _Chain()
    agent = _agent(monkeypatch, chain)

    _gen(agent, variation_key=None)
    _gen(agent, variation_key=None)
    assert chain.calls == 2, "ortak kovada ikinci istek cache'i kaçırır (eski davranış)"


def test_tenant_id_wins_over_variation_key(monkeypatch, _isolated_cache):
    """Giriş yapmış kullanıcıda kimlik ZAYIFLATILMAZ: tenant_id önceliklidir →
    aynı kullanıcı farklı IP'den gelse de kendi görülmüş-setini taşır."""
    chain = _Chain()
    agent = _agent(monkeypatch, chain)

    agent.generate(
        grade=5, topic_id="dogal_sayilar", kazanim_kod=None,
        difficulty=Difficulty.ORTA, question_count=5,
        tenant_id="user_42", variation_key=anon_variation_key(_FakeRequest(host="203.0.113.1")),
    )
    agent.generate(
        grade=5, topic_id="dogal_sayilar", kazanim_kod=None,
        difficulty=Difficulty.ORTA, question_count=5,
        tenant_id="user_42", variation_key=anon_variation_key(_FakeRequest(host="198.51.100.9")),
    )
    assert chain.calls == 2, "aynı tenant, IP değişse bile kendi setini tekrar almamalı"


# ------------------------------------------------- router bağlantısı (wiring)


def _capture_variation_keys(monkeypatch):
    """`_build_worksheet`'i yakalar; uçların geçtiği variation_key'leri toplar."""
    from app.routers import worksheets as W

    seen: list[str | None] = []

    def fake_build(req, *, variation_key=None):
        seen.append(variation_key)
        from app.models.schemas import AnswerKeyEntry, Worksheet, WorksheetMetadata
        from datetime import datetime, timezone

        ws = Worksheet(
            title="t", grade=req.grade, topic="Doğal Sayılar ve İşlemler",
            difficulty=req.difficulty, question_count=1,
            questions=[], answer_key=[],
        )
        meta = WorksheetMetadata(
            generated_at=datetime.now(tz=timezone.utc), model="fake", trace=None
        )
        return ws, meta

    monkeypatch.setattr(W, "_build_worksheet", fake_build)
    monkeypatch.setattr(W.entitlements, "enforce_quota", lambda *a, **k: None)
    return seen


def test_generate_endpoint_passes_per_visitor_key(monkeypatch):
    """/generate iki farklı X-Forwarded-For için FARKLI kova geçmeli.

    Bu test bağlantıyı (wiring) kanıtlar: mekanizma agent'ta doğru olsa bile uç
    nokta anahtarı geçirmezse canlıda hiçbir şey değişmez.
    """
    from fastapi.testclient import TestClient

    from app.main import app

    seen = _capture_variation_keys(monkeypatch)
    client = TestClient(app)
    body = {
        "grade": 5, "topic_id": "dogal_sayilar", "difficulty": "orta",
        "question_count": 5,
    }
    for ip in ("203.0.113.1", "203.0.113.2", "203.0.113.1"):
        r = client.post("/api/worksheets/generate", json=body,
                        headers={"X-Forwarded-For": ip})
        assert r.status_code == 200, r.text

    assert len(seen) == 3
    assert all(k and k.startswith(PREFIX) for k in seen), f"kova geçilmedi: {seen}"
    assert seen[0] != seen[1], "farklı IP → farklı kova"
    assert seen[0] == seen[2], "aynı IP → aynı kova"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
