"""Maliyet israfı fix'leri (2026-07-26 ölçümü) — iki regresyon testi.

1. `_build_worksheet` mixed/progressive modda `agent` değişkenine dokunup
   UnboundLocalError → HTTP 500 veriyordu: 3 bucket'lık ÜRETİM tamamlanıp para
   harcandıktan SONRA istek çöküyordu (canlıda doğrulandı: HTTP 500 / 41 sn).
2. `GeminiCritic.evaluate` tüm soruları tek çağrıda denetliyordu; 30+ soruda
   model yanıtı yozlaşıp çıktı tavanına dayanıyor (ölçülen: 65.524 token, 148 sn,
   kesik JSON → fail-open = filtreleme YOK). Artık `critic_batch_size`'lık
   gruplara bölünür, `max_output_tokens` sonlu, verdict index'i global'e ötelenir.
"""
import pytest

from app.config import settings
from app.models.enums import Difficulty, QuestionType, SubjectId
from app.models.schemas import GenerateWorksheetRequest, Question
from app.services.llm_cache import SPARE_POOL


@pytest.fixture(autouse=True)
def _clean_pool():
    """Faz 2 (§3b, docs/COST_QUALITY_V2_PLAN.md) sonrası GEREKLİ: pool-first
    serving artık HER `generate()` çağrısının BAŞINDA depoyu okur (eskiden
    yalnız post-filter eksiğinde okunuyordu). Bu dosyanın testleri gerçek
    `GeminiAgent.generate()`'i çağırıp sonunda teslim edilen soruları depoya
    yazıyor (`source='live-delivered'`, Faz 1'den beri); depo GERÇEK/kalıcı
    `knowledge_base/history.sqlite3` dosyasına yazdığından, temizlenmezse bir
    test kendi ÖNCEKİ koşusunun artığını "depo zaten dolu" sanıp fake LLM
    zincirini hiç çağırmadan yanlışlıkla geçebilir (ya da başka bir testin
    sorularını görebilir)."""
    SPARE_POOL.clear()
    yield
    SPARE_POOL.clear()


def _q(n: int) -> Question:
    return Question(
        number=n,
        question=f"{n} + {n} kaçtır?",
        answer=str(2 * n),
        solution_steps="A" * 1200,  # uzun çözüm → kesme davranışını da tetikler
        kazanim_kod="MAT.5.1.1.1",
        question_type=QuestionType.ISLEM,
        difficulty=Difficulty.ORTA,
    )


# ---------------------------------------------------------------- 1) mixed 500

@pytest.mark.parametrize("mode", ["mixed", "progressive"])
def test_build_worksheet_mixed_does_not_crash(monkeypatch, mode):
    """mixed/progressive artık 500 vermez ve metadata.model dolu gelir."""
    from app.routers import worksheets as W
    from app.services.agent import GeminiAgent

    counter = {"n": 0}

    def fake_generate(self, **kw):
        counter["n"] += 1
        start = counter["n"] * 100
        return [_q(start + i) for i in range(kw["question_count"])]

    monkeypatch.setattr(GeminiAgent, "generate", fake_generate)
    monkeypatch.setattr(GeminiAgent, "__init__", lambda self, **kw: None)
    monkeypatch.setattr(
        GeminiAgent, "build_last_trace",
        lambda self: __import__(
            "app.models.schemas", fromlist=["GenerationTrace"]
        ).GenerationTrace(
            few_shot_source="static", few_shot_count=0, textbook_count=0,
            model_used="gemini-2.5-flash", temperature=0.7, seed=1, retry_rounds=0,
            requested_count=6, delivered_count=6,
        ),
    )

    req = GenerateWorksheetRequest(
        subject=SubjectId.MATEMATIK, grade=5, topic_id="dogal_sayilar",
        question_count=10, difficulty=Difficulty.ORTA, difficulty_mode=mode,
    )
    worksheet, metadata = W._build_worksheet(req)
    assert worksheet.question_count == 10
    # Asıl regresyon: model adı trace'ten okunur, `agent` değişkenine dokunulmaz.
    assert metadata.model == "gemini-2.5-flash"
    assert metadata.trace is not None


# ------------------------------------------------------- 2) critic parçalama

class _FakeResp:
    def __init__(self, verdicts, in_tok=100, out_tok=50):
        from app.services.critic import CriticBatch
        self.parsed = CriticBatch(verdicts=verdicts)
        self.text = self.parsed.model_dump_json()

        class _UM:
            prompt_token_count = in_tok
            candidates_token_count = out_tok
            thoughts_token_count = 0

        self.usage_metadata = _UM()


def _make_critic(monkeypatch, captured):
    from app.services import critic as C

    class _FakeModels:
        def generate_content(self, *, model, contents, config):
            from app.services.critic import CriticVerdict
            captured.append({"config": config, "contents": contents})
            # Grup boyutunu prompt'taki "[i]" etiket sayısından türet.
            n = contents.count("] kazanım:")
            return _FakeResp([
                CriticVerdict(question_index=i, is_valid=True, confidence=0.9)
                for i in range(n)
            ])

    class _FakeClient:
        models = _FakeModels()

    monkeypatch.setattr(C.genai, "Client", lambda api_key: _FakeClient())
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    return C.GeminiCritic()


def test_critic_chunks_and_offsets_indices(monkeypatch):
    """25 soru → 3 çağrı (10+10+5); verdict index'leri GLOBAL (0..24), token toplanır."""
    captured: list = []
    monkeypatch.setattr(settings, "critic_batch_size", 10)
    critic = _make_critic(monkeypatch, captured)

    questions = [_q(i) for i in range(25)]
    verdicts = critic.evaluate(questions, [{"kod": "MAT.5.1.1.1", "metin": "toplama"}],
                              Difficulty.ORTA)

    assert len(captured) == 3, f"beklenen 3 grup çağrısı, olan {len(captured)}"
    assert [v.question_index for v in verdicts] == list(range(25))
    # Token kullanımı gruplar arasında BİRİKTİRİLİR (tek grubunki değil).
    assert critic._last_usage.input_tokens == 300
    assert critic._last_usage.output_tokens == 150


def test_critic_sets_finite_output_cap_and_truncates_solutions(monkeypatch):
    """Sonsuz çıktı yozlaşmasını kesen tavan + çözüm adımı kırpması."""
    captured: list = []
    monkeypatch.setattr(settings, "critic_batch_size", 10)
    critic = _make_critic(monkeypatch, captured)

    critic.evaluate([_q(i) for i in range(4)],
                    [{"kod": "MAT.5.1.1.1", "metin": "toplama"}], Difficulty.ORTA)

    cfg = captured[0]["config"]
    cap = getattr(cfg, "max_output_tokens", None)
    assert cap is not None and 0 < cap < 8192, f"sonlu tavan bekleniyordu, olan {cap}"
    # 1200 karakterlik çözüm kırpılmış olmalı.
    assert "…[kesildi]" in captured[0]["contents"]
    assert "A" * 1200 not in captured[0]["contents"]


# ------------------------------------------- 3) üretim çıktı tavanı (format-drop)

def test_output_cap_leaves_room_for_thinking():
    """Gemini 2.5+ thinking token'larını da max_output_tokens'a sayar → dinamik
    thinking'de tavan içerik + düşünme payı olmalı, yoksa MEŞRU üretim kesilir."""
    from app.services.agent import output_cap_for

    per_q = settings.generation_output_cap_per_question
    # Ölçülen en pahalı meşru üretim: 36 soru, 16.950 thinking + 7.188 içerik.
    cap_dynamic = output_cap_for(36, -1)
    assert cap_dynamic >= 16_950 + 7_188, "meşru geometri üretimi kesilirdi"
    # Thinking kapalıysa pay ayrılmaz (1-4. sınıf politikası).
    assert output_cap_for(36, 0) == 36 * per_q
    # Sabit bütçe → bütçe + %25 pay.
    assert output_cap_for(10, 512) == 10 * per_q + 640


def test_output_cap_below_model_hard_ceiling():
    """Tavan, modelin 64K sert tavanının ALTINDA kalmalı — yozlaşan üretim
    orada durdurulabilsin (ölçüm: tavansız çağrı 65.012 token yaktı)."""
    from app.services.agent import output_cap_for

    # En büyük gerçekçi batch: 20 soru × 1.8 overshoot = 36.
    assert output_cap_for(36, -1) < 65_536


def test_generation_call_passes_output_cap(monkeypatch):
    """Birincil üretim çağrısı tavanı GEÇİRİYOR olmalı (regresyon kilidi)."""
    from app.services import agent as A
    from app.services.agent import GeminiAgent, GeneratedBatch, GeneratedQuestion
    from app.services.history import GenerationHistory
    from app.services.llm_providers import ProviderResponse, TokenUsage

    seen: dict = {}

    def fake_chain(**kw):
        seen.update(kw)
        return ProviderResponse(
            parsed=GeneratedBatch(questions=[
                GeneratedQuestion(
                    question=f"Soru {w}: kaç eder?", answer="1",
                    solution_steps="adım", kazanim_kod="MAT.5.1.1.1",
                    question_type=QuestionType.ISLEM,
                )
                for w in ("bir", "iki", "üç", "dört", "beş")
            ]),
            model_name="gemini-2.5-flash", provider="gemini",
            usage=TokenUsage(input_tokens=10, output_tokens=10,
                             model_name="gemini-2.5-flash"),
        )

    monkeypatch.setattr(A, "call_with_chain", fake_chain)
    monkeypatch.setattr(A, "GENERATION_HISTORY", GenerationHistory(persist=False))
    monkeypatch.setattr(A, "_collect_few_shot", lambda *a, **k: ([], "static"))
    monkeypatch.setattr(A, "_collect_textbook_context", lambda *a, **k: [])
    monkeypatch.setattr(GeminiAgent, "__init__", lambda self, **kw: None)
    monkeypatch.setattr(GeminiAgent, "_get_critic", lambda self, subject=None: None)
    monkeypatch.setattr(settings, "enable_semantic_dedup", False)
    monkeypatch.setattr(settings, "enable_math_verifier", False)
    monkeypatch.setattr(settings, "enable_critic", False)
    monkeypatch.setattr(settings, "enable_generation_cache", False)

    agent = GeminiAgent()
    agent.thinking_budget = 512
    agent._gemini_provider = None
    agent._anthropic_provider = None
    agent._embedder = None
    agent._critics = {}
    agent.generate(grade=5, topic_id="dogal_sayilar", kazanim_kod=None,
                   difficulty=Difficulty.ORTA, question_count=5)

    cap = seen.get("max_output_tokens")
    assert cap is not None, "birincil üretim çağrısında çıktı tavanı yok"
    assert 0 < cap < 65_536


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
