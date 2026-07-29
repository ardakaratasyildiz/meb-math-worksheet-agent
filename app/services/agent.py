"""Gemini tabanlı soru üretim servisi."""
import logging
import random
import re
import time

from google import genai
from pydantic import BaseModel

from app.config import settings
from app.data.curriculum import Kazanim, get_topic
from app.data.units import get_unit, resolve_legacy_topic
from app.models.enums import Difficulty, QuestionType, SubjectId
from app.models.schemas import Question, SolutionStep, repair_latex_control_chars
from app.prompts.templates import (
    SYSTEM_PROMPT,
    build_retry_prompt,
    build_user_prompt,
)
from app.services.critic import CriticError, GeminiCritic
from app.services.diversity import (
    BatchDeduplicator,
    SemanticDeduplicator,
    distribute_question_types,
    extract_context_tokens,
    normalize_question,
)
from app.services.embedder import EmbedderError, GeminiEmbedder
from app.services.examples import get_examples_for_kazanim, select_diverse
from app.services.llm_cache import GENERATION_CACHE, SPARE_POOL, _pool_key
from app.services.structured import (
    _answer_letter,
    _parse_mcq,
    leftover_directive_issue,
    reference_integrity_issue,
    structured_content_issue,
    truncated_stem_issue,
)
from app.services.llm_providers import (
    AnthropicProvider,
    GeminiProvider,
    ProviderError,
    call_with_chain,
)
from app.services.math_verifier import verify_batch as verify_math_batch
from app.services.history import DEFAULT_TENANT, GENERATION_HISTORY, HistoryKey
from app.services.retriever import ExampleRetriever, get_retriever
from app.services.svg_utils import (
    extract_svg_blocks,
    is_valid_svg,
    process_chart_directives,
    process_geo_directives,
    process_pattern_directives,
    process_table_directives,
)
from app.subjects import get_content_module

logger = logging.getLogger(__name__)

# "4 şık, tek doğru, answer=harf" yapısal olarak ÖZDEŞ tipler → hepsi coktan_secmeli gibi
# işlenir: şıklar .options'tan/metinden alınır, <4 ise ELENİR, correct_index türetilir ve
# şıklar metne DETERMİNİSTİK gömülür (PDF/web/mobil hepsi gösterir). Türkçe okuma_pasaji/
# kelime_bilgisi/dil_bilgisi/yazim_noktalama şıksız gövdeyle yayınlanıyordu (WS: Erdemler PDF).
_MC_TYPES = frozenset({
    QuestionType.COKTAN_SECMELI,
    QuestionType.OKUMA_PASAJI,
    QuestionType.KELIME_BILGISI,
    QuestionType.DIL_BILGISI,
    QuestionType.YAZIM_NOKTALAMA,
})


def model_for_grade(grade: int) -> str:
    """Sınıfa göre KABA model (geriye-uyum + testler). Ayrıntılı politika için
    model_for() kullanılır. 1-4 → ucuz (2.5-flash); 5-8 → güçlü (3.5-flash)."""
    return (
        settings.gemini_model_grade_1_4
        if grade <= 4
        else settings.gemini_model_grade_5_8
    )


def is_geometry_theme(
    subject: SubjectId, grade: int, topic_id: str | None, unit_id: str | None
) -> bool:
    """Üretim geometri temasında mı? (model_for: geometri → güçlü model.)

    Yalnız matematik; non-math derste geometri teması yok → False. Ünite akışında
    legacy topic'e köprülenir (resolve_legacy_topic). Fail-safe: hata → False.
    """
    if subject != SubjectId.MATEMATIK:
        return False
    if topic_id == "geometri":
        return True
    if unit_id:
        try:
            return resolve_legacy_topic(grade, unit_id, None) == "geometri"
        except Exception:  # noqa: BLE001 — tespit hatası üretimi bozmasın
            return False
    return False


def model_for(
    grade: int,
    *,
    is_geometry: bool,
    difficulty: "Difficulty | None",
    is_premium: bool,
) -> str:
    """Model seçim politikası (bkz. config yorumu). Ucuz=2.5-flash, güçlü=3.5-flash.

    1-4 → ucuz · geometri → güçlü · 8+premium → güçlü · 5-7+premium+ZOR → güçlü ·
    diğer → ucuz. is_premium = GERÇEK abonelik (entitlements.is_premium_for_model),
    premium_all dark-launch DEĞİL.
    """
    cheap = settings.gemini_model_grade_1_4
    strong = settings.gemini_model_grade_5_8
    if grade <= 4:
        return cheap
    if is_geometry:
        return strong
    if grade >= 8:
        return strong if is_premium else cheap
    # 5-7: premium'da yalnız ZOR bucket güçlü modele gider (kalan bucket'lar ucuz;
    # ekstra çağrı yok — zorluk bucket'ları zaten ayrı üretiliyor).
    if is_premium and difficulty == Difficulty.ZOR:
        return strong
    return cheap


def output_cap_for(question_count: int, thinking_budget: int | None) -> int:
    """Üretim çağrısı için `max_output_tokens` — yozlaşma/format-drop israfını keser.

    Tavan yoksa model bazen kendini tekrar edip modelin 64K çıktı tavanına kadar
    yazıyor, JSON kesiliyor ve TÜM token boşa gidiyor (ölçüm: tek istekte ~99K
    çıktı token'ı / ~6.3 TL). Tavan içerik + thinking payından oluşur:

    - içerik: `question_count × generation_output_cap_per_question`
      (ölçülen normal tüketim ~420-450 token/soru → 900 iki kat pay)
    - thinking: Gemini 2.5+ düşünme token'larını da max_output_tokens'a SAYAR →
      bütçe 0 ise pay yok, N>0 ise N + %25, dinamik (-1) ise sabit cömert pay.

    Tavana dayanmak = kesik JSON = şema-drop olduğundan cömert tutulur; amaç
    meşru üretimi kesmek değil, YOZLAŞMAYI erken durdurmaktır.
    """
    content = max(1, question_count) * settings.generation_output_cap_per_question
    if thinking_budget is None or thinking_budget < 0:
        think = settings.generation_output_cap_thinking_allowance
    elif thinking_budget == 0:
        think = 0
    else:
        think = int(thinking_budget * 1.25)
    return max(8192, content + think)


def thinking_for_model(grade: int, model: str) -> int:
    """Sınıf+model'e göre thinking bütçesi. Güçlü model (3.5, geometri/premium) →
    dinamik (kaliteyi koru). Ucuz model: 1-4→0, 5-7→512, 8→-1. Config'ten okunur."""
    if model == settings.gemini_model_grade_5_8:
        return settings.gemini_thinking_budget_strong
    if grade <= 4:
        return settings.gemini_thinking_budget_grade_1_4
    if grade <= 7:
        return settings.gemini_thinking_budget_grade_5_7
    return settings.gemini_thinking_budget_grade_8


def model_and_thinking_for(
    grade: int,
    *,
    subject: SubjectId,
    topic_id: str | None,
    unit_id: str | None,
    difficulty: "Difficulty | None",
    is_premium: bool,
) -> tuple[str, int]:
    """(model, thinking_budget) — üretim çağrısı/bucket'ı için tek karar noktası."""
    geo = is_geometry_theme(subject, grade, topic_id, unit_id)
    model = model_for(grade, is_geometry=geo, difficulty=difficulty, is_premium=is_premium)
    return model, thinking_for_model(grade, model)


class GeneratedQuestion(BaseModel):
    """Gemini'den dönen ham üretim. solution_steps şimdilik str — Gemini
    response_schema union types ile her zaman güvenli değil; Question.solution_steps
    daha sonra frontend tarafında parse edilebilir list'e çevrilebilir
    (`parse_solution_steps`)."""

    question: str
    answer: str
    solution_steps: str
    kazanim_kod: str
    question_type: QuestionType
    # Çoktan seçmeli şıkları — YAPISAL alan (D1). Model şıkları (harf öneki YOK) buraya
    # yazar; structured output zorunlu kıldığından "şıksız MC" drop'u biter. `question`
    # yalnız soru kökünü taşır; backend şıkları metne DETERMİNİSTİK gömer (eski render'lar
    # geriye-uyumlu okur). MC dışı tiplerde None.
    options: list[str] | None = None


class GeneratedBatch(BaseModel):
    questions: list[GeneratedQuestion]


class AgentError(Exception):
    pass


def _select_kazanimlar(
    grade: int, topic_id: str, kazanim_kod: str | None
) -> list[Kazanim]:
    topic = get_topic(grade, topic_id)
    if topic is None:
        raise AgentError(f"{grade}. sınıfta '{topic_id}' konusu bulunmuyor.")
    if kazanim_kod is None:
        return list(topic["kazanimlar"])
    for k in topic["kazanimlar"]:
        if k["kod"] == kazanim_kod:
            return [k]
    raise AgentError(
        f"'{kazanim_kod}' kodu {grade}. sınıf '{topic_id}' konusunda bulunamadı."
    )


def _select_kazanimlar_by_unit(
    grade: int, unit_id: str, kazanim_kod: str | None
) -> list[Kazanim]:
    """MEB TYMM ünite (tema) kazanımlarını seçer.

    Dönen dict'ler `Kazanim` gibi kullanılır; ek `legacy_topic_id` anahtarı RAG/
    ders-kitabı retrieval'ında kazanım-bazlı köprü için taşınır (few-shot fonksiyonları
    `k.get("legacy_topic_id", topic_id)` ile okur). difficulty_hints yoktur → prompt
    genel zorluk kalibrasyonuna düşer (bkz. templates._format_kazanim_block).
    """
    unit = get_unit(grade, unit_id)
    if unit is None:
        raise AgentError(f"{grade}. sınıfta '{unit_id}' ünitesi bulunmuyor.")
    if kazanim_kod is None:
        return list(unit["kazanimlar"])
    for k in unit["kazanimlar"]:
        if k["kod"] == kazanim_kod:
            return [k]
    raise AgentError(
        f"'{kazanim_kod}' kodu {grade}. sınıf '{unit_id}' ünitesinde bulunamadı."
    )


def _collect_few_shot_static(
    grade: int,
    kazanimlar: list[Kazanim],
    distribution: dict[QuestionType, int],
    target_difficulty: str,
    max_total: int,
    rng: random.Random,
) -> list[dict]:
    """Statik (manuel) few-shot havuzundan örnek toplar — RAG kapalıysa veya fallback.

    Kazanımlar arası bağlam token havuzu paylaşılır → aynı isim/nesne tekrar etmez.
    """
    preferred = list(distribution.keys())
    pool: list[dict] = []
    used_tokens: set[str] = set()
    for k in kazanimlar:
        examples = get_examples_for_kazanim(
            grade,
            k["kod"],
            max_count=2,
            preferred_types=preferred,
            target_difficulty=target_difficulty,
            rng=rng,
            seed_used_tokens=used_tokens,
        )
        for ex in examples:
            used_tokens.update(extract_context_tokens(ex.get("question", "")))
        pool.extend(examples)
    pool.sort(
        key=lambda e: (0 if e.get("difficulty") == target_difficulty else 1, rng.random()),
    )
    return pool[:max_total]


def _collect_few_shot_rag(
    retriever: ExampleRetriever,
    grade: int,
    topic_id: str,
    kazanimlar: list[Kazanim],
    target_difficulty: str,
    max_total: int,
    rng: random.Random,
) -> list[dict]:
    """Her hedef kazanım için vector store'dan örnek çeker, birleştirir."""
    pool: list[dict] = []
    per_kazanim = max(2, max_total // max(len(kazanimlar), 1))
    for k in kazanimlar:
        query = f"{k['metin']} {k.get('difficulty_hints', {}).get(target_difficulty, '')}"
        # Köprü: ünite kazanımları MAT.* kodlu (KB'de yok) → kazanım-bazlı legacy_topic_id
        # ile filtrele. Eski müfredat kazanımlarında bu anahtar yok → topic_id kullanılır.
        # retriever fallback zinciri (grade, topic_id, difficulty) semantik sorguyla eşler.
        eff_topic = k.get("legacy_topic_id", topic_id)
        retrieved = retriever.retrieve(
            query_text=query,
            grade=grade,
            kazanim_kod=k["kod"],
            topic_id=eff_topic,
            difficulty=target_difficulty,
            k=per_kazanim,
            rng=rng,
        )
        pool.extend(retrieved)

    # Önce hedef zorluk eşleşenleri öne al, sonra MMR ile bağlam çakışması cezalı seç.
    matching = [e for e in pool if e.get("difficulty") == target_difficulty]
    others = [e for e in pool if e.get("difficulty") != target_difficulty]
    rng.shuffle(matching)
    rng.shuffle(others)
    ordered = matching + others
    return select_diverse(
        pool=ordered,
        max_count=max_total,
        target_difficulty=target_difficulty,
        preferred_types=None,
        rng=rng,
    )


def _collect_few_shot(
    grade: int,
    topic_id: str,
    kazanimlar: list[Kazanim],
    distribution: dict[QuestionType, int],
    target_difficulty: str,
    max_total: int,
    rng: random.Random,
) -> tuple[list[dict], str]:
    """RAG veya statik havuzdan few-shot toplar. İkinci değer kaynak ('rag' / 'static').

    Fail-open: RAG yolu (query embedding + Chroma) hata verirse — özellikle paralel
    bucket'larda eşzamanlı embedding çağrıları embedding endpoint'ini 429'layabilir —
    statik havuza düşülür, üretim çökmez.
    """
    if settings.use_rag:
        retriever = get_retriever()
        if retriever is not None and retriever.count() > 0:
            try:
                rag_pool = _collect_few_shot_rag(
                    retriever, grade, topic_id, kazanimlar, target_difficulty, max_total, rng
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "RAG few-shot başarısız (embedding/retrieval), statik havuza düşülüyor: %s",
                    exc,
                )
                rag_pool = []
            if rag_pool:
                return rag_pool, "rag"
    static_pool = _collect_few_shot_static(
        grade, kazanimlar, distribution, target_difficulty, max_total, rng
    )
    return static_pool, "static"


def _collect_textbook_context(
    grade: int,
    topic_id: str,
    kazanimlar: list[Kazanim],
    target_difficulty: str,
    max_total: int = 3,
    rng: random.Random | None = None,
) -> list[dict]:
    """MEB ders kitabından bağlam chunk'ları çeker. RAG kapalıysa veya retriever yoksa boş döner."""
    if not settings.use_rag:
        return []
    retriever = get_retriever()
    if retriever is None or retriever.count() == 0:
        return []
    pool: list[dict] = []
    per_kazanim = max(1, max_total // max(len(kazanimlar), 1))
    seen_ids: set[str] = set()
    for k in kazanimlar:
        query = f"{k['metin']} {k.get('difficulty_hints', {}).get(target_difficulty, '')}"
        eff_topic = k.get("legacy_topic_id", topic_id)  # köprü (bkz. _collect_few_shot_rag)
        try:
            chunks = retriever.retrieve_textbook(
                query_text=query,
                grade=grade,
                kazanim_kod=k["kod"],
                topic_id=eff_topic,
                k=per_kazanim,
                rng=rng,
            )
        except Exception as exc:
            logger.warning("Textbook retrieval başarısız (%s): %s", k["kod"], exc)
            continue
        for c in chunks:
            cid = f"{c.get('source')}|{c.get('page_start')}|{c.get('header')}|{(c.get('question') or '')[:60]}"
            if cid in seen_ids:
                continue
            seen_ids.add(cid)
            pool.append(c)
    return pool[:max_total]


DIFFICULTY_TEMPERATURES: dict[Difficulty, float] = {
    Difficulty.KOLAY: 0.55,
    Difficulty.ORTA: 0.80,
    Difficulty.ZOR: 1.00,
}

TEMPERATURE_JITTER = 0.10  # ±0.10 etrafında rastgele kayma
RETRY_TEMPERATURE_BOOST = 0.15  # retry round'da bu kadar artır
TEMPERATURE_MAX = 1.5
TEMPERATURE_MIN = 0.0


def _clamp_temp(t: float) -> float:
    return max(TEMPERATURE_MIN, min(TEMPERATURE_MAX, t))


def _collect_critic_context(
    subject: SubjectId,
    grade: int,
    kazanimlar: list[dict],
    max_chunks: int = 6,
) -> str:
    """Non-math ders için critic'e verilecek REFERANS ders kitabı bağlamı (RAG).

    Fen chunk'ları subject=fen + grade ile çekilir (kazanım koduyla değil — Fen
    chunk'larında kazanım tag yok; grade+subject+embedding benzerliği yeterli).
    Matematik için boş döner (math kendi doğrulayıcılarını kullanır)."""
    if subject == SubjectId.MATEMATIK or not settings.use_rag:
        return ""
    retriever = get_retriever()
    if retriever is None or retriever.count() == 0:
        return ""
    subj = subject.value if hasattr(subject, "value") else str(subject)
    seen: set[str] = set()
    parts: list[str] = []
    per = max(1, max_chunks // max(len(kazanimlar), 1))
    for k in kazanimlar:
        try:
            chunks = retriever.retrieve_textbook(
                query_text=k.get("metin", ""),
                grade=grade,
                kazanim_kod=None,
                topic_id="",  # eşleşmez → (subject, grade) fallback'ine düşer (embedding)
                k=per,
                subject=subj,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Critic context retrieval başarısız (%s): %s", subj, exc)
            continue
        for c in chunks:
            txt = (c.get("question") or "").strip()
            key = txt[:80]
            if not txt or key in seen:
                continue
            seen.add(key)
            parts.append(txt)
            if len(parts) >= max_chunks:
                break
        if len(parts) >= max_chunks:
            break
    return "\n---\n".join(parts)


class GeminiAgent:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        fallback_models: list[str] | None = None,
        thinking_budget: int | None = None,
    ) -> None:
        key = api_key or settings.gemini_api_key
        if not key:
            raise AgentError("GEMINI_API_KEY ayarı boş. .env dosyanızı kontrol edin.")
        self.client = genai.Client(api_key=key)  # legacy (kullanılmıyor)
        self.model = model or settings.gemini_model
        self.fallback_models = (
            fallback_models if fallback_models is not None else settings.fallback_model_list
        )
        # None → thinking config'e dokunma (SDK varsayılanı). Sınıf-bazlı değer
        # çağıran tarafından thinking_budget_for_grade ile geçilir.
        self.thinking_budget = thinking_budget
        try:
            self._gemini_provider: GeminiProvider | None = GeminiProvider(
                primary_model=self.model,
                fallback_models=self.fallback_models,
                thinking_budget=thinking_budget,
            )
        except ProviderError as exc:
            raise AgentError(str(exc)) from exc
        # Anthropic fallback opsiyonel; api key yoksa veya flag kapalıysa None.
        self._anthropic_provider: AnthropicProvider | None = None
        if settings.enable_anthropic_fallback and settings.anthropic_api_key:
            try:
                self._anthropic_provider = AnthropicProvider()
            except ProviderError as exc:
                logger.warning("Anthropic fallback başlatılamadı: %s", exc)
        self._embedder: GeminiEmbedder | None = None
        # Critic subject başına cache'lenir (her dersin kendi doğrulayıcı prompt'u var).
        self._critics: dict[SubjectId, GeminiCritic] = {}

    def _get_embedder(self) -> GeminiEmbedder | None:
        """Lazy init. Embedding API erişilemezse None döner — semantic dedup atlanır."""
        if self._embedder is not None:
            return self._embedder
        try:
            self._embedder = GeminiEmbedder()
            return self._embedder
        except EmbedderError as exc:
            logger.warning("Embedder başlatılamadı, semantic dedup devre dışı: %s", exc)
            return None

    def _get_critic(
        self, subject: SubjectId = SubjectId.MATEMATIK
    ) -> GeminiCritic | None:
        cached = self._critics.get(subject)
        if cached is not None:
            return cached
        # Ders-özel critic prompt'u; non-math dersler kendi CRITIC_SYSTEM_PROMPT'unu kullanır.
        sys_prompt: str | None = None
        if subject != SubjectId.MATEMATIK:
            content = get_content_module(subject)
            if content is not None:
                sys_prompt = content.CRITIC_SYSTEM_PROMPT
        try:
            critic = GeminiCritic(system_prompt=sys_prompt)
            self._critics[subject] = critic
            return critic
        except CriticError as exc:
            logger.warning("Critic başlatılamadı, doğrulama devre dışı: %s", exc)
            return None

    def generate(
        self,
        grade: int,
        topic_id: str | None,
        kazanim_kod: str | None,
        difficulty: Difficulty,
        question_count: int,
        seed: int | None = None,
        temperature: float | None = None,
        max_retry_rounds: int = 1,
        include_textbook: bool = True,
        tenant_id: str | None = None,
        allowed_types: list[QuestionType] | None = None,
        yeni_nesil: bool = False,
        unit_id: str | None = None,
        subject: SubjectId = SubjectId.MATEMATIK,
        variation_key: str | None = None,
    ) -> list[Question]:
        # Seed jitter: aynı parametrelerle yapılan art arda çağrılar farklı sonuç versin.
        if seed is None:
            seed = time.time_ns() % (2**31)
        rng = random.Random(seed)
        if temperature is None:
            base_temp = DIFFICULTY_TEMPERATURES[difficulty]
            jitter = rng.uniform(-TEMPERATURE_JITTER, TEMPERATURE_JITTER)
            temperature = _clamp_temp(base_temp + jitter)

        # ── Ders (subject) çözümü — plugin-driven ──────────────────────────────
        # Matematik (default) yolu birebir korunur. Non-math dersler (fen, ingilizce,
        # …) içerik modülünü (get_content_module) getirir: system_prompt / yeni_nesil
        # bloğu / critic / few-shot / curriculum / DEFAULT_TYPES. RAG + textbook +
        # math_verifier YALNIZ matematikte (Chroma'da yok, SymPy math'e özel).
        is_math = subject == SubjectId.MATEMATIK
        content = None if is_math else get_content_module(subject)
        if not is_math and content is None:
            raise AgentError(f"Bilinmeyen/desteklenmeyen ders: {subject}")
        SUBJ_SYSTEM_PROMPT = SYSTEM_PROMPT if is_math else content.SYSTEM_PROMPT
        SUBJ_YN_BLOCK = None if is_math else content.YENI_NESIL_BLOCK

        # Seçim akışı: non-math (ünite) / yeni MEB ünite (unit_id) / eski konu (topic_id).
        # Köprü: ünite yolunda RAG/tip-dağılımı için legacy topic türetilir; cache/history
        # namespace'i selection_key ile ayrılır → farklı üniteler/dersler karışmaz.
        if not is_math:
            try:
                kazanimlar, display_name = content.select_kazanimlar(
                    grade, unit_id, kazanim_kod
                )
            except ValueError as exc:
                raise AgentError(str(exc)) from exc
            dist_topic = None  # non-math'te topic-bazlı görsel dağıtım yok
            selection_key = f"{subject.value}:{unit_id}"
        elif unit_id:
            kazanimlar = _select_kazanimlar_by_unit(grade, unit_id, kazanim_kod)
            unit = get_unit(grade, unit_id)
            assert unit is not None  # _select_kazanimlar_by_unit doğruladı
            display_name = unit["name"]
            dist_topic = resolve_legacy_topic(grade, unit_id, kazanim_kod) or "dogal_sayilar"
            selection_key = unit_id
        else:
            kazanimlar = _select_kazanimlar(grade, topic_id, kazanim_kod)
            _topic = get_topic(grade, topic_id)
            if _topic is None:
                raise AgentError(f"{grade}. sınıfta '{topic_id}' konusu bulunmuyor.")
            display_name = _topic["name"]
            dist_topic = topic_id
            selection_key = topic_id
        # Kullanıcı tip filtresi — None ise tüm tipler.
        allowed_set: set[QuestionType] | None = (
            set(allowed_types) if allowed_types else None
        )
        # Non-math: kullanıcı tip seçmediyse dersin varsayılan tipleri (math'e özgü
        # islem/salt_islem hariç). DEFAULT_TYPES ders içerik modülünden gelir.
        if not is_math and allowed_set is None:
            allowed_set = set(content.DEFAULT_TYPES)
        # History anahtarı — hem cache lookup hem depo/dedup hem üretim sonrası
        # kayıt için. selection_key (unit_id veya topic_id) namespace'i ayırır.
        #
        # `variation_key` (anonim çeşitlilik kovası, bkz. app/services/anon_bucket.py):
        # tenant_id YOKSA devreye girer. Eskiden anonim isteklerin TAMAMI
        # `DEFAULT_TENANT`'ı paylaşıyordu → teslim edilen her soru ortak "görülmüş"
        # kümesine yazılıyor, cache'teki her set o kümeyle çakıştığı için ATLANIYOR
        # ve anonim trafikte cache pratikte hiç tutmuyordu. Sıra ÖNEMLİ: giriş
        # yapmış kullanıcıda tenant_id her zaman kazanır (kimlik zayıflatılmaz).
        history_key: HistoryKey = (
            tenant_id or variation_key or DEFAULT_TENANT,
            grade,
            selection_key,
            kazanim_kod or "__AUTO__",
            difficulty.value,
        )
        # Kalıcı görülmüş-set — TEK sorgu (§3a). Eskiden cache branch'i içinde
        # `history_seen_norm` adıyla, üretim sonrası tekrar `history_seen` adıyla
        # İKİ KEZ hesaplanıyordu (GenerationHistory anahtar başına zaten cache'lediği
        # için ikinci çağrı ucuzdu ama gereksizdi). Depo (§3b) da aynı kümeyi
        # exclude_norms olarak kullanır → tek sefer hesaplanıp HER YERDE aynı
        # isimle paylaşılır (cache lookup, pool-first, dedup.prime, vb.).
        history_seen = GENERATION_HISTORY.seen_questions(history_key)

        # --- Cache lookup (Sprint 6) ---------------------------------------
        # Aynı (grade, topic, kazanım, zorluk, count, tip, yeni_nesil) için önceden
        # üretilmiş set varsa LLM çağrısını atla. Kullanıcının history'sinde bulunan
        # sorulara sahip set'ler atlanır → tekrar dağıtım önlenir.
        # yeni_nesil (premium) setleri de cache'lenir; cache anahtarına dahil
        # olduğundan normal setlerle ayrı havuzda tutulur (kaliteler karışmaz).
        if settings.enable_generation_cache:
            cached = GENERATION_CACHE.get(
                grade=grade,
                topic_id=selection_key,
                kazanim_kod=kazanim_kod,
                difficulty=difficulty.value,
                question_count=question_count,
                exclude_questions=history_seen,
                allowed_types=allowed_types,
                yeni_nesil=yeni_nesil,
            )
            if cached is not None:
                # Trace bilgilerini cache hit moduna ayarla.
                self._last_few_shot_source = "cache"
                self._last_few_shot_count = 0
                self._last_textbook_count = 0
                self._last_retrieval_avg_distance = None
                self._last_model_used = "cache"
                self._last_provider = "cache"
                self._last_temperature = 0.0
                self._last_final_temperature = 0.0
                self._last_seed = seed
                self._last_retry_rounds = 0
                self._last_dedup_rejected_string = 0
                self._last_dedup_rejected_semantic = 0
                self._last_math_verifier_rejected = 0
                self._last_critic_rejected = 0
                self._last_requested_count = question_count
                self._last_delivered_count = len(cached)
                self._last_cache_hit = True
                self._last_prompt_tokens = 0
                self._last_completion_tokens = 0
                self._last_cost_usd = 0.0
                self._last_pool_hit_count = 0
                self._last_pool_math_rejected = 0
                self._last_pool_critic_rejected = 0
                # History'e yine de kaydet — sonraki çağrıda aynı set'i tekrar
                # vermemek için (overlap kontrolü exclude_questions ile yapılıyor).
                for q in cached:
                    GENERATION_HISTORY.record(
                        history_key,
                        normalize_question(q.question),
                        extract_context_tokens(q.question),
                        embedding=None,
                    )
                logger.info("Üretim cache hit — LLM çağrısı atlandı (%d soru).", len(cached))
                return cached

        # --- Depo (spare pool) anahtarı ------------------------------------
        # Cache MISS sonrası, LLM'DEN ÖNCE gerekir (§3b): pool-first serving
        # akışı prompt kurulmadan/few-shot çekilmeden önce depoyu dener.
        pool_key = _pool_key(
            grade, selection_key, kazanim_kod, difficulty.value,
            allowed_types, yeni_nesil,
        )

        # Cost metering — bu generate() boyunca tüm LLM çağrılarının (üretim +
        # retry + critic + pool-first tembel damga çağrısı) token toplamı.
        # NOT: eskiden bu bloğun hemen üstünde, ilk LLM çağrısından hemen önce
        # tanımlıydı; pool-first bloğu da critic çağırabildiğinden buraya (LLM
        # çağrısından ÖNCEye) taşındı.
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_cost_usd = 0.0
        math_rejected = 0
        critic_rejected = 0
        # Pool-first'in denetlediği/elediği ESKİ havuz satırları — Küçük 1
        # (Opus denetimi 2026-07-28): `math_rejected`/`critic_rejected`'tan AYRI
        # tutulur, aksi halde "üretim kalitesi düştü" ile "havuz temizliği
        # yapıldı" ölçümde ayırt edilemezdi (plan §7). Bu ikisi YALNIZ
        # `_pool_first_fill()` içinde artar; aşağıdaki TAZE üretim/top-up
        # geçişleri hâlâ `math_rejected`/`critic_rejected`'a yazar.
        pool_math_rejected = 0
        pool_critic_rejected = 0
        # Critic FAIL-OPEN izleyicisi (MUST-FIX 2, denetim 2026-07-28): critic
        # çağrı/parse hatasında BOŞ liste döner ve hiçbir soruyu düşürmez
        # (COST_REDUCTION_PLAN §3.2'deki arıza modu). Bu durumda sorular "denetlendi,
        # geçti" DEĞİL, "hiç denetlenmedi" sayılmalı — aksi halde depo damgası (§3c)
        # yanlış bilgiyi kalıcı hâle getirir. None = hiç critic çağrısı yapılmadı;
        # True = en az bir çağrı verdict ÜRETTİ ve henüz hiçbiri boş dönmedi;
        # False = en az bir çağrı (sorular varken) boş döndü → bir daha ASLA
        # True'ya dönmez (şüphe varsa NULL/fail-CLOSED — bkz. damga blokları).
        critic_verdicts_ok: bool | None = None

        # Critic bağlamı (non-math RAG) tek generate() içinde DEĞİŞMEZ → bir kez
        # topla, tüm critic geçişlerinde (pool-first dahil) yeniden kullan.
        _critic_ctx_cache: dict[str, str] = {}

        def _critic_context() -> str:
            if "v" not in _critic_ctx_cache:
                _critic_ctx_cache["v"] = _collect_critic_context(
                    subject, grade, kazanimlar
                )
            return _critic_ctx_cache["v"]

        def _apply_post_filters(qs: list, embs: list) -> tuple[list, list, int, int, list]:
            """math_verifier + critic uygular → (kalan, embedding, math_red,
            critic_red, critic_reddettiği_sorular). Critic token'ı toplam maliyete
            eklenir. Son eleman (§3c tembel damga): critic'in SPESİFİK olarak
            reddettiği `Question` nesneleri — math_verifier'ın elediği sorular
            BURADA yer almaz (deterministik/LLM-siz, damga bunları kapsamaz;
            bir dahaki serviste yeniden ve ucuza denetlenirler)."""
            nonlocal total_prompt_tokens, total_completion_tokens, total_cost_usd
            nonlocal critic_verdicts_ok
            m_rej = c_rej = 0
            critic_rejected_qs: list = []
            if settings.enable_math_verifier and is_math and qs:
                verdicts_v = verify_math_batch(qs)
                drop_v = {
                    v.question_index for v in verdicts_v
                    if v.is_verifiable and not v.is_valid
                }
                if drop_v:
                    qs = [q for i, q in enumerate(qs) if i not in drop_v]
                    if embs:
                        embs = [e for i, e in enumerate(embs) if i not in drop_v]
                    m_rej = len(drop_v)
            if settings.enable_critic and qs:
                _critic = self._get_critic(subject)
                if _critic is not None:
                    _raw_verdicts_c = _critic.evaluate(
                        qs, kazanimlar, difficulty, context=_critic_context()
                    )
                    # Fail-open izleyicisi (MUST-FIX 2) — ana geçişteki mantıkla AYNI.
                    if _raw_verdicts_c:
                        if critic_verdicts_ok is not False:
                            critic_verdicts_ok = True
                    else:
                        critic_verdicts_ok = False
                    verdicts_c = _raw_verdicts_c or []
                    _cu = getattr(_critic, "_last_usage", None)
                    if _cu is not None:
                        total_prompt_tokens += _cu.input_tokens
                        total_completion_tokens += _cu.output_tokens
                        total_cost_usd += _cu.estimated_cost_usd
                    drop_c = {
                        v.question_index for v in verdicts_c
                        if (
                            not v.is_valid
                            and v.confidence >= settings.critic_min_confidence
                            and 0 <= v.question_index < len(qs)
                        )
                    }
                    if drop_c:
                        critic_rejected_qs = [q for i, q in enumerate(qs) if i in drop_c]
                        qs = [q for i, q in enumerate(qs) if i not in drop_c]
                        if embs:
                            embs = [e for i, e in enumerate(embs) if i not in drop_c]
                        c_rej = len(drop_c)
            return qs, embs, m_rej, c_rej, critic_rejected_qs

        # ── Depo (spare pool): BİRİNCİL servis yolu (Faz 2, §3b/§3c) ────────
        # Hedef akış: `cache → DEPO (istenen sayının TAMAMI) → yalnız EKSİK
        # kadar LLM`. Kural (kullanıcı kararı, §3b): çapraz-kullanıcı tekrar
        # SERBEST (doluluk eşiği yok, depoda ne varsa verilir); tek kısıt aynı
        # kullanıcıya tekrar (history_seen → exclude_norms). Seçim used_count
        # ASC + `_select_rows`'un critic_pass=1 önceliği (bedava sorular önce
        # tükensin).
        #
        # Tembel damga (§3c): `critic_pass == 1` satırlar filtrelerden HİÇ
        # geçirilmeden servis edilir (LLM görmez, marjinal maliyet ~0).
        # `critic_pass is None` satırlar BİR KEZ `_apply_post_filters`'tan
        # (math_verifier + critic) geçirilir; sonuç `SPARE_POOL.stamp()` ile
        # satıra yazılır — FAIL-CLOSED: critic bu turda fail-open olduysa
        # (`critic_verdicts_ok` False/None) hiçbir şey damgalanmaz, satır NULL
        # kalır ve bir sonraki serviste yeniden (ve ucuza) denetlenir.
        #
        # Tip-farkında seçim (SHOULD-FIX, Opus denetimi 2026-07-28): kovanın
        # İÇİNDEKİ tip karışımı eskiden gözetilmiyordu — `_select_rows` yalnız
        # used_count'a bakıyordu, kovada BASKIN tek tip (ör. yalnız `islem`)
        # kağıdın TAMAMINI ele geçirebilirdi (soru tipi çeşitliliği bir ürün
        # özelliği, Sprint 12-A). Fix: `pool_first_respect_type_mix=True` iken
        # hedef dağılım (`distribute_question_types`, OVERSHOOT'SUZ — gerçek
        # hedef) pool-first'ten ÖNCE hesaplanır ve her tip YALNIZ KENDİ kotası
        # kadar depodan çekilir; bir tipte havuz yetmezse eksik o tipin LLM
        # hedefine (`type_deficit`) devredilir — `llm_target`/`distribution`
        # aşağıda bu eksiklerin TOPLAMINA göre kurulur (bkz. altta).
        pool_questions: list[Question] = []
        pool_embeddings: list[list[float]] = []
        _pool_exclude = set(history_seen)
        _POOL_FIRST_MAX_ROUNDS = 3  # BEST-EFFORT tavan — pool küçükse hızlı pes et

        def _pool_first_fill(target_n: int, qtype: "QuestionType | None") -> int:
            """`qtype` (None ise tüm tipler) için depodan en fazla `target_n`
            soru çeker; `pool_questions`/`pool_embeddings`'e EKLER, doldurulan
            sayıyı döner. `pool_math_rejected`/`pool_critic_rejected`'ı
            artırır (TAZE üretim sayaçlarından AYRI — Küçük 1)."""
            nonlocal pool_math_rejected, pool_critic_rejected, critic_verdicts_ok
            filled = 0
            rounds = 0
            qtype_value = getattr(qtype, "value", None) if qtype is not None else None
            while filled < target_n and rounds < _POOL_FIRST_MAX_ROUNDS:
                rounds += 1
                need = target_n - filled
                try:
                    items = SPARE_POOL.take_for_serving(
                        pool_key, need, exclude_norms=_pool_exclude,
                        question_type=qtype_value,
                    )
                except Exception as exc:  # noqa: BLE001 — havuz BEST-EFFORT
                    logger.warning("Havuz okuması (pool-first) başarısız (yutuldu): %s", exc)
                    break
                if not items:
                    break
                exhausted = len(items) < need
                verified = [it for it in items if it.critic_pass == 1]
                unverified = [it for it in items if it.critic_pass is None]
                for it in verified:
                    if filled >= target_n:
                        break
                    pool_questions.append(it.question)
                    pool_embeddings.append([])
                    _pool_exclude.add(normalize_question(it.question.question))
                    filled += 1
                for it in unverified:
                    _pool_exclude.add(normalize_question(it.question.question))
                if unverified and filled < target_n:
                    u_qs = [it.question for it in unverified]
                    u_embs: list = [[] for _ in u_qs]
                    kept, kept_embs, m_rej, c_rej, critic_rej_qs = _apply_post_filters(
                        u_qs, u_embs
                    )
                    pool_math_rejected += m_rej
                    pool_critic_rejected += c_rej
                    if critic_verdicts_ok:
                        if kept:
                            try:
                                SPARE_POOL.stamp(
                                    pool_key,
                                    [normalize_question(q.question) for q in kept],
                                    critic_pass=1,
                                    verifier_model=settings.critic_model,
                                )
                            except Exception as exc:  # noqa: BLE001
                                logger.warning("Havuz damgalama (geçti) başarısız: %s", exc)
                        if critic_rej_qs:
                            try:
                                SPARE_POOL.stamp(
                                    pool_key,
                                    [normalize_question(q.question) for q in critic_rej_qs],
                                    critic_pass=0,
                                    verifier_model=settings.critic_model,
                                )
                            except Exception as exc:  # noqa: BLE001
                                logger.warning("Havuz damgalama (reddetti) başarısız: %s", exc)
                    for q in kept:
                        if filled >= target_n:
                            break
                        pool_questions.append(q)
                        pool_embeddings.append([])
                        filled += 1
                if exhausted:
                    break
            return filled

        type_deficit: dict[QuestionType, int] = {}
        if settings.enable_pool_first_serving and settings.enable_spare_pool:
            if settings.pool_first_respect_type_mix:
                _pool_target_distribution = distribute_question_types(
                    question_count, difficulty, topic_id=dist_topic,
                    allowed_types=allowed_set, yeni_nesil=yeni_nesil,
                )
                for _qt, _target_n in _pool_target_distribution.items():
                    _filled = _pool_first_fill(_target_n, _qt)
                    _deficit = _target_n - _filled
                    if _deficit > 0:
                        type_deficit[_qt] = _deficit
            else:
                # Eski (tip-farkında OLMAYAN) davranış: toplam sayı hedefiyle çek,
                # tip karışımı tesadüfe kalır.
                _pool_first_fill(question_count, None)

        pool_hit_count = len(pool_questions)
        self._last_pool_hit_count = pool_hit_count
        llm_target = question_count - pool_hit_count

        if llm_target <= 0:
            # Depo TAMAMINI karşıladı — LLM'e HİÇ gidilmez: few-shot/textbook
            # retrieval'ı da atlanır (onlar da maliyet — RAG embedding çağrısı).
            questions = [
                q.model_copy(update={"number": i + 1})
                for i, q in enumerate(pool_questions[:question_count])
            ]
            accepted_embeddings = pool_embeddings[:question_count]
            self._last_few_shot_source = "pool"
            self._last_few_shot_count = 0
            self._last_textbook_count = 0
            self._last_retrieval_avg_distance = None
            self._last_model_used = "pool"
            self._last_provider = "pool"
            self._last_temperature = 0.0
            self._last_final_temperature = 0.0
            self._last_seed = seed
            self._last_retry_rounds = 0
            self._last_dedup_rejected_string = 0
            self._last_dedup_rejected_semantic = 0
            # math_rejected/critic_rejected TAZE üretimi sayar — bu yolda hiç
            # LLM üretimi olmadığından 0 (bkz. math_rejected/critic_rejected init).
            self._last_math_verifier_rejected = math_rejected
            self._last_critic_rejected = critic_rejected
            self._last_pool_math_rejected = pool_math_rejected
            self._last_pool_critic_rejected = pool_critic_rejected
            self._last_requested_count = question_count
            self._last_delivered_count = len(questions)
            self._last_cache_hit = False
            self._last_prompt_tokens = total_prompt_tokens
            self._last_completion_tokens = total_completion_tokens
            self._last_cost_usd = total_cost_usd
            for q in questions:
                GENERATION_HISTORY.record(
                    history_key,
                    normalize_question(q.question),
                    extract_context_tokens(q.question),
                    embedding=None,
                )
            logger.info(
                "Depo tamamını karşıladı — LLM çağrısı atlandı (%d soru, pool_hit=%d).",
                len(questions), pool_hit_count,
            )
            return questions

        # ── Buradan itibaren yalnız EKSİK (`llm_target`) kadar üretim yapılır ──
        # Over-generation (latency): ilk batch'i hedeften fazla iste ki math/critic
        # elemeleri seri top-up turu açmadan absorbe edilsin. Eleme oranı ~%41
        # üretimde >0; overshoot bunları tek çağrıda karşılar. `llm_target`
        # (depo düşüldükten sonra KALAN gerçek hedef) retry/top-up durdurma
        # koşulu ve sondaki kırpma için korunur; yalnızca İLK çağrının
        # dağıtım+prompt hedefi büyür.
        from math import ceil as _ceil
        _overshoot = settings.generation_overshoot_ratio or 1.0
        if (
            settings.enable_pool_first_serving and settings.enable_spare_pool
            and settings.pool_first_respect_type_mix and type_deficit
        ):
            # Tip-bazlı eksik ZATEN biliniyor (§ yukarıda) — `distribute_question_types`'ı
            # TEKRAR çağırıp ağırlık şemasından yeni bir dağılım türetmek yerine
            # (ki bu, eksik OLMAYAN bir tipe pay ayırıp kağıdı yine dengesiz
            # bırakabilirdi) doğrudan eksik dict'i (overshoot ile ölçeklenmiş)
            # dağıtım olarak kullanılır — toplamı `llm_target`'a en yakın (overshoot
            # payıyla biraz üstünde) tutulur.
            if _overshoot > 1.0:
                distribution = {qt: _ceil(n * _overshoot) for qt, n in type_deficit.items()}
            else:
                distribution = dict(type_deficit)
            gen_target = sum(distribution.values())
        else:
            gen_target = _ceil(llm_target * _overshoot) if _overshoot > 1.0 else llm_target
            distribution = distribute_question_types(
                gen_target, difficulty, topic_id=dist_topic, allowed_types=allowed_set,
                yeni_nesil=yeni_nesil,
            )

        if not is_math:
            # Non-math: RAG yok (Chroma'da ders dökümanı yok) → gerçek MEB/LGS few-shot.
            few_shot = content.collect_few_shot(
                grade, kazanimlar, difficulty.value, 6, rng
            )
            few_shot_source = "static"
        else:
            few_shot, few_shot_source = _collect_few_shot(
                grade,
                dist_topic,
                kazanimlar,
                distribution,
                target_difficulty=difficulty.value,
                max_total=6,
                rng=rng,
            )
        self._last_few_shot_source = few_shot_source
        self._last_few_shot_count = len(few_shot)
        textbook_chunks: list[dict] = []
        if include_textbook and is_math:
            textbook_chunks = _collect_textbook_context(
                grade=grade,
                topic_id=dist_topic,
                kazanimlar=kazanimlar,
                target_difficulty=difficulty.value,
                max_total=3,
                rng=rng,
            )
        self._last_textbook_count = len(textbook_chunks)
        # Retrieval güveni: few-shot + textbook chunk distance'larının ortalaması.
        distances: list[float] = []
        for chunk in (*few_shot, *textbook_chunks):
            d = chunk.get("distance") if isinstance(chunk, dict) else None
            if isinstance(d, (int, float)):
                distances.append(float(d))
        self._last_retrieval_avg_distance = (
            sum(distances) / len(distances) if distances else None
        )
        logger.info(
            "Few-shot kaynağı: %s (%s örnek) | textbook chunks: %s",
            few_shot_source, len(few_shot), len(textbook_chunks),
        )
        # history_key/history_seen yukarıda (cache lookup + pool-first için) TEK
        # sefer hesaplandı — burada tekrar hesaplanmaz.
        history_contexts = GENERATION_HISTORY.context_exclusions(history_key)
        history_embeddings = GENERATION_HISTORY.seen_embeddings(history_key)
        # NOT (Faz 2, §3b — İş 3, docs/COST_QUALITY_V2_PLAN.md): `context_exclusions`/
        # `seen_embeddings` hâlâ `GENERATION_HISTORY`'nin `capacity_per_key=30`'luk
        # SINIRLI belleğine dayanır (bilinçli — prompt token'ı/RAM freni, `seen_questions()`
        # gibi tavansız DEĞİL). Depo birincil yol olunca aynı kovadan çok daha fazla
        # soru akacak (çapraz-kullanıcı serbest tekrar kullanım), ama bu iki mekanizmanın
        # penceresi bilerek dar kalmaya devam ediyor — biri "neden dedup/bağlam penceresi
        # bu kadar dar" diye şaşırırsa diye not: bu bir eksiklik değil, kasıtlı ödün.
        if pool_questions:
            # Bağlam çakışmasını azalt: depodan servis edilen soruların bağlam
            # kelimeleri de prompt'un context_exclusions'ına katılır — AMA mevcut
            # SINIRLI (capped, max 15) mekanizma korunur, tavan KALDIRILMAZ
            # (prompt şişmesi = girdi maliyeti artışı, Faz 1'de bilinçli korunmuştu).
            _pool_ctx_tokens: set[str] = set()
            for _pq in pool_questions:
                _pool_ctx_tokens.update(extract_context_tokens(_pq.question))
            if _pool_ctx_tokens:
                history_contexts = sorted(set(history_contexts) | _pool_ctx_tokens)[:15]

        user_prompt = build_user_prompt(
            grade=grade,
            topic_name=display_name,
            kazanimlar=kazanimlar,
            difficulty=difficulty,
            question_count=gen_target,  # over-generation: ilk çağrı hedefi (sonda kırpılır)
            distribution=distribution,
            few_shot_examples=few_shot,
            context_exclusions=history_contexts,
            few_shot_source=few_shot_source,
            textbook_chunks=textbook_chunks,
            yeni_nesil=yeni_nesil,
            yeni_nesil_block=SUBJ_YN_BLOCK,
        )

        dedup = BatchDeduplicator()
        dedup.prime(history_seen)
        # Depodan servis edilenler de dedup'a girer (§3b, İş 1 nokta 4): yeni
        # üretilen sorular pool-delivered sorunun YAPISAL kopyası olmasın.
        for _pq in pool_questions:
            dedup.add(_pq.question)

        semantic_dedup: SemanticDeduplicator | None = None
        embedder: GeminiEmbedder | None = None
        if settings.enable_semantic_dedup:
            embedder = self._get_embedder()
            if embedder is not None:
                semantic_dedup = SemanticDeduplicator(
                    threshold=settings.semantic_dedup_threshold
                )
                semantic_dedup.prime(history_embeddings)

        # Sorulardan kabul edilenlerin embedding'lerini topla — history kaydı için.
        # (Yalnız BU LLM üretim/top-up geçişinin embedding'leri; depo sorularının
        # embedding'i yok — `pool_embeddings` ile en sonda AYRI birleştirilir.)
        accepted_embeddings: list[list[float]] = []

        valid_kazanim_codes = {k["kod"] for k in kazanimlar}
        fallback_kazanim = kazanimlar[0]["kod"]

        # total_prompt_tokens/total_completion_tokens/total_cost_usd/critic_verdicts_ok
        # yukarıda (pool-first bloğundan ÖNCE) tanımlandı — burada TEKRAR
        # sıfırlanmaz (aksi halde pool-first'ün critic maliyeti/fail-open bayrağı
        # kaybolurdu).

        # İlk üretim — provider chain (Gemini → Anthropic) ile.
        try:
            result = call_with_chain(
                system=SUBJ_SYSTEM_PROMPT,
                prompt=user_prompt,
                schema=GeneratedBatch,
                temperature=temperature,
                gemini=self._gemini_provider,
                anthropic=self._anthropic_provider,
                # Yozlaşma freni: tavansız çağrıda model 64K'ya kadar yazıp
                # kesik JSON üretebiliyor → tüm token çöp (bkz. output_cap_for).
                max_output_tokens=output_cap_for(gen_target, self.thinking_budget),
            )
        except ProviderError as exc:
            raise AgentError(str(exc)) from exc
        self._last_model_used = result.model_name
        self._last_provider = result.provider
        if result.usage is not None:
            total_prompt_tokens += result.usage.input_tokens
            total_completion_tokens += result.usage.output_tokens
            total_cost_usd += result.usage.estimated_cost_usd
        # Başarısız denemelerin (şema-drop / 429-retry / atlanan fallback modeli)
        # token'ları da faturalanır → deftere ekle, yoksa defter faturanın altında kalır.
        total_cost_usd += result.wasted_cost_usd
        batch = result.parsed
        if not isinstance(batch, GeneratedBatch):
            raise AgentError("Provider beklenmedik tip döndürdü.")
        candidates = self._process_batch(
            batch, dedup, valid_kazanim_codes, fallback_kazanim, starting_number=1,
            allowed_types=allowed_set,
        )
        questions, new_embs = self._apply_semantic_dedup(
            candidates, embedder, semantic_dedup
        )
        accepted_embeddings.extend(new_embs)

        # Eksik kaldıysa yeniden üretim. Sıcaklığı boost ederek yaratıcılığı arttır.
        retry_round = 0
        retry_temperature = temperature
        while (
            len(questions) < llm_target
            and retry_round < max_retry_rounds
            and batch.questions  # ilk çağrı tamamen boşsa retry etme
        ):
            missing = llm_target - len(questions)
            retry_temperature = _clamp_temp(retry_temperature + RETRY_TEMPERATURE_BOOST)
            # Hangi tipten kaç eksik kaldığını hesapla — model bu dağılımı hedeflesin.
            produced_by_type: dict[QuestionType, int] = {}
            for q in questions:
                produced_by_type[q.question_type] = produced_by_type.get(q.question_type, 0) + 1
            missing_distribution: dict[QuestionType, int] = {}
            for qt, target in distribution.items():
                deficit = target - produced_by_type.get(qt, 0)
                if deficit > 0:
                    missing_distribution[qt] = deficit
            # missing_distribution toplamı `missing`'i aşabilir (bazı tipler fazla üretilmiş olabilir);
            # toplam tutması için en az ihtiyaç duyulanı önceliklendir, gerekirse kırp.
            total_missing_dist = sum(missing_distribution.values())
            if total_missing_dist > missing and total_missing_dist > 0:
                scale = missing / total_missing_dist
                missing_distribution = {
                    qt: max(1, round(v * scale)) for qt, v in missing_distribution.items()
                }
            retry_prompt = build_retry_prompt(
                original_user_prompt=user_prompt,
                already_generated_questions=[q.question for q in questions],
                missing_count=missing,
                missing_distribution=missing_distribution if missing_distribution else None,
            )
            logger.info(
                "Eksik %s soru için yeniden üretim (round %s, temp=%.2f)",
                missing,
                retry_round + 1,
                retry_temperature,
            )
            try:
                result2 = call_with_chain(
                    system=SUBJ_SYSTEM_PROMPT,
                    prompt=retry_prompt,
                    schema=GeneratedBatch,
                    temperature=retry_temperature,
                    gemini=self._gemini_provider,
                    anthropic=self._anthropic_provider,
                    max_output_tokens=output_cap_for(missing, self.thinking_budget),
                )
                self._last_model_used = result2.model_name
                self._last_provider = result2.provider
                if result2.usage is not None:
                    total_prompt_tokens += result2.usage.input_tokens
                    total_completion_tokens += result2.usage.output_tokens
                    total_cost_usd += result2.usage.estimated_cost_usd
                total_cost_usd += result2.wasted_cost_usd
                batch2 = result2.parsed
                if not isinstance(batch2, GeneratedBatch):
                    raise ProviderError("Provider beklenmedik tip döndürdü.")
            except ProviderError as exc:
                logger.warning("Retry başarısız, mevcut sorularla devam ediliyor: %s", exc)
                break
            more_candidates = self._process_batch(
                batch2,
                dedup,
                valid_kazanim_codes,
                fallback_kazanim,
                starting_number=len(questions) + 1,
                allowed_types=allowed_set,
            )
            more, more_embs = self._apply_semantic_dedup(
                more_candidates, embedder, semantic_dedup
            )
            if not more:
                break
            take = more[:missing]
            questions.extend(take)
            accepted_embeddings.extend(more_embs[: len(take)])
            retry_round += 1

        # Hedef sayıyı (llm_target — depo düşüldükten sonraki KALAN hedef) aşmasın.
        # FAZLALAR ATILMAZ: overshoot (1.8) ile üretilip kırpılan geçerli sorular
        # `spare_candidates`'a alınır; post-filter eksiği önce BURADAN, sonra
        # kalıcı havuzdan karşılanır — LLM top-up çağrısı (ölçüm: 19-24K çıktı
        # token'ı) ancak ikisi de yetmezse atılır. `pool_key` yukarıda (pool-first
        # bloğundan önce) zaten hesaplandı, burada tekrar hesaplanmaz.
        spare_candidates = questions[llm_target:]
        spare_embeddings = accepted_embeddings[llm_target:]
        questions = questions[:llm_target]
        accepted_embeddings = accepted_embeddings[: len(questions)]

        # Deterministic math verifier: SymPy ile aritmetik doğrulama.
        # Critic'ten ÖNCE çalışır — ucuz, hızlı, yanılma payı yok.
        # Non-math'te SymPy math_verifier ATLANIR (aritmetik doğrulama math'e özel;
        # sözel/fen soruları verifiable değil → no-op olurdu, netlik için atlanır).
        # NOT: `math_rejected` burada SIFIRLANMAZ — pool-first bloğunun (varsa)
        # katkısı korunur, bu geçiş yalnız ÜSTÜNE EKLER (+=, aşağıda).
        if settings.enable_math_verifier and questions and is_math:
            verdicts = verify_math_batch(questions)
            drop_indices: set[int] = set()
            for v in verdicts:
                if v.is_verifiable and not v.is_valid:
                    drop_indices.add(v.question_index)
                    logger.info(
                        "Math verifier reddetti [%s]: %s | %s",
                        v.question_index,
                        questions[v.question_index].question[:80],
                        v.reason,
                    )
            if drop_indices:
                kept_pairs = [
                    (q, accepted_embeddings[i] if i < len(accepted_embeddings) else None)
                    for i, q in enumerate(questions)
                    if i not in drop_indices
                ]
                questions = [
                    q.model_copy(update={"number": idx + 1})
                    for idx, (q, _) in enumerate(kept_pairs)
                ]
                accepted_embeddings = [
                    emb if emb is not None else []
                    for _, emb in kept_pairs
                ]
                math_rejected += len(drop_indices)

        # `_critic_ctx_cache`/`_critic_context()` yukarıda (pool-first bloğundan
        # önce) tanımlandı — burada tekrar tanımlanmaz, aynı cache paylaşılır
        # (bağlam tek generate() içinde değişmez, tekrar RAG çağrısı yapılmaz).

        # Critic geçişi: matematik doğruluğu + kazanım/zorluk uyumu kontrolü.
        # NOT: `critic_rejected` burada SIFIRLANMAZ (pool-first katkısı korunur).
        if settings.enable_critic and questions:
            # DÜZELTME: subject'i geçir — Fen soruları ana geçişte de bilimsel-
            # doğruluk prompt'uyla denetlensin (önceden math critic'ine düşüyordu).
            critic = self._get_critic(subject)
            if critic is not None:
                # Non-math: referans ders kitabı bağlamını (RAG) critic'e ver → olgusal
                # doğrulama kitaba dayansın (Fen "hücre duvarı" vb. hatalar).
                verdicts = critic.evaluate(
                    questions, kazanimlar, difficulty, context=_critic_context()
                )
                # Fail-open izleyicisi (MUST-FIX 2): sorular vardı, verdict
                # gelmediyse critic aslında hiçbir şeyi denetlemedi (parse/API
                # hatası best-effort yutulmuş olabilir) → bir daha True olamaz.
                if verdicts:
                    if critic_verdicts_ok is not False:
                        critic_verdicts_ok = True
                else:
                    critic_verdicts_ok = False
                _cu = getattr(critic, "_last_usage", None)
                if _cu is not None:
                    total_prompt_tokens += _cu.input_tokens
                    total_completion_tokens += _cu.output_tokens
                    total_cost_usd += _cu.estimated_cost_usd
                if verdicts:
                    drop_indices: set[int] = set()
                    for v in verdicts:
                        if (
                            not v.is_valid
                            and v.confidence >= settings.critic_min_confidence
                            and 0 <= v.question_index < len(questions)
                        ):
                            drop_indices.add(v.question_index)
                            logger.info(
                                "Critic reddetti [%s] (conf=%.2f): %s | issues=%s",
                                v.question_index, v.confidence,
                                questions[v.question_index].question[:80],
                                v.issues,
                            )
                    if drop_indices:
                        kept_pairs = [
                            (q, accepted_embeddings[i] if i < len(accepted_embeddings) else None)
                            for i, q in enumerate(questions)
                            if i not in drop_indices
                        ]
                        # Numaraları yeniden sıkıştır; embedding listesini hizalı tut.
                        questions = [
                            q.model_copy(update={"number": idx + 1})
                            for idx, (q, _) in enumerate(kept_pairs)
                        ]
                        accepted_embeddings = [
                            emb if emb is not None else []
                            for _, emb in kept_pairs
                        ]
                        critic_rejected += len(drop_indices)

        # ── Post-filter doldurma ────────────────────────────────────────────
        # math_verifier/critic soru düşürdüyse eksiği kapat. SIRA (maliyet):
        #   1) bu istekte fazla üretilmiş yedekler  → BEDAVA (zaten ödendi)
        #   2) kalıcı yedek havuzu                  → BEDAVA (önceki istekler)
        #   3) LLM top-up çağrısı                   → PAHALI (son çare)
        # Eskiden yalnız (3) vardı ve fazlalar çöpe gidiyordu.
        # `_apply_post_filters` yukarıda (pool-first bloğundan önce) zaten
        # tanımlandı — burada tekrar tanımlanmaz, AYNI closure kullanılır.

        # Havuz BEST-EFFORT: yazma/okuma hatası üretimi ASLA düşürmemeli.
        # Prod'da havuz Turso'ya yazar ve mixed modda 3 bucket PARALEL thread'te
        # koşar; bir DB hatası (kilit/istemci) çıplak bırakılırsa bucket'ın
        # `except Exception`'ı HAZIR SORULARI çöpe atar (canlıda 5 istenen kağıtta
        # orta bucket'ın 3 sorusu böyle kayboldu → 2/5 teslim). `llm_cache.put`
        # de aynı sözleşmeyi kullanıyor ("Cache yazımı başarısız (yutuldu)").
        def _pool_add(
            qs: list,
            *,
            source: str = "live-overshoot",
            critic_pass: int | None = None,
            verifier_model: str | None = None,
        ) -> None:
            # source varsayılanı 'live-overshoot': bu yardımcı bugüne kadar yalnız
            # kırpılan/kullanılmayan fazlalar için çağrılıyordu (§3d — sorgulanabilir
            # `source` alanı). Teslim edilenler generate() sonunda AYRI parametrelerle
            # çağırır (source='live-delivered', bkz. aşağı).
            if not (settings.enable_spare_pool and qs):
                return
            try:
                SPARE_POOL.add_many(
                    pool_key,
                    qs,
                    subject=getattr(subject, "value", str(subject)),
                    grade=grade,
                    unit_id=selection_key,
                    difficulty=difficulty.value,
                    source=source,
                    critic_pass=critic_pass,
                    verifier_model=verifier_model,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Havuz yazımı başarısız (yutuldu): %s", exc)

        def _pool_take(n: int) -> list:
            if not settings.enable_spare_pool or n <= 0:
                return []
            try:
                return SPARE_POOL.take(pool_key, n, exclude_norms=history_seen)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Havuzdan çekim başarısız (yutuldu): %s", exc)
                return []

        def _accept(new_qs: list, new_embs: list) -> int:
            """Kabul edilenleri `questions`'a ekler (numaraları sıkı tutar). Eklenen sayı."""
            nonlocal questions, accepted_embeddings
            take_n = llm_target - len(questions)
            if take_n <= 0 or not new_qs:
                return 0
            base_no = len(questions)
            taken = [
                q.model_copy(update={"number": base_no + i + 1})
                for i, q in enumerate(new_qs[:take_n])
            ]
            questions.extend(taken)
            if new_embs:
                accepted_embeddings.extend(new_embs[: len(taken)])
            return len(taken)

        # (1)+(2): LLM'siz kaynaklar.
        if len(questions) < llm_target:
            free_qs: list = list(spare_candidates)
            # Embedding listesi soru listesiyle HİZALI olmalı: `_apply_post_filters`
            # elemeyi index'e göre yapıyor. Semantic dedup kapalıysa embedding
            # listesi boş gelir → boş yer tutucularla hizala.
            free_embs: list = (
                list(spare_embeddings)
                if len(spare_embeddings) == len(spare_candidates)
                else [[] for _ in spare_candidates]
            )
            if len(free_qs) < (llm_target - len(questions)):
                drawn = _pool_take(
                    (llm_target - len(questions) - len(free_qs)) * 2
                )
                # Havuzdan gelenler bu batch'te tekrar olmasın.
                for q in drawn:
                    if not dedup.is_duplicate(q.question):
                        dedup.add(q.question)
                        free_qs.append(q)
                        free_embs.append([])
            if free_qs:
                kept, kept_embs, m_rej, c_rej, _cr_qs = _apply_post_filters(free_qs, free_embs)
                math_rejected += m_rej
                critic_rejected += c_rej
                filled = _accept(kept, kept_embs)
                # Filtreden geçip KULLANILMAYANLAR havuza (stok).
                if len(kept) > filled:
                    _pool_add(kept[filled:])
                if filled:
                    logger.info(
                        "Post-filter eksiği LLM'siz kapatıldı: +%d soru "
                        "(yedek=%d havuz-dahil, kalan eksik=%d)",
                        filled, len(free_qs), llm_target - len(questions),
                    )
            else:
                _pool_add(spare_candidates)
        else:
            # Eksik yok → tüm fazlalar doğrudan stoğa.
            _pool_add(spare_candidates)

        # (3) LLM top-up — yalnız hâlâ eksikse.
        post_filter_rounds = 0
        POST_FILTER_MAX_RETRIES = 2
        while (
            len(questions) < llm_target
            and post_filter_rounds < POST_FILTER_MAX_RETRIES
        ):
            missing = llm_target - len(questions)
            retry_temperature = _clamp_temp(retry_temperature + RETRY_TEMPERATURE_BOOST)
            retry_prompt = build_retry_prompt(
                original_user_prompt=user_prompt,
                already_generated_questions=[q.question for q in questions],
                missing_count=missing,
                missing_distribution=None,
            )
            logger.info(
                "Post-filter top-up [%s/%s]: eksik=%s temp=%.2f",
                post_filter_rounds + 1, POST_FILTER_MAX_RETRIES,
                missing, retry_temperature,
            )
            try:
                result_pf = call_with_chain(
                    system=SUBJ_SYSTEM_PROMPT,
                    prompt=retry_prompt,
                    schema=GeneratedBatch,
                    temperature=retry_temperature,
                    gemini=self._gemini_provider,
                    anthropic=self._anthropic_provider,
                    # ÇIKTI TAVANI: top-up "N soru daha" istiyor ama model hedefi
                    # aşıp ilk batch'ten büyük yanıt üretebiliyor (ölçüm: 5 eksik
                    # soru için 24.302 çıktı token'ı).
                    max_output_tokens=output_cap_for(missing + 2, self.thinking_budget),
                )
                self._last_model_used = result_pf.model_name
                self._last_provider = result_pf.provider
                if result_pf.usage is not None:
                    total_prompt_tokens += result_pf.usage.input_tokens
                    total_completion_tokens += result_pf.usage.output_tokens
                    total_cost_usd += result_pf.usage.estimated_cost_usd
                total_cost_usd += result_pf.wasted_cost_usd
                batch_pf = result_pf.parsed
                if not isinstance(batch_pf, GeneratedBatch) or not batch_pf.questions:
                    break
            except ProviderError as exc:
                logger.warning("Post-filter LLM çağrısı başarısız: %s", exc)
                break

            new_candidates = self._process_batch(
                batch_pf, dedup, valid_kazanim_codes,
                fallback_kazanim, starting_number=len(questions) + 1,
                allowed_types=allowed_set,
            )
            new_questions, new_embs = self._apply_semantic_dedup(
                new_candidates, embedder, semantic_dedup
            )
            if not new_questions:
                post_filter_rounds += 1
                continue

            new_questions, new_embs, _m, _c, _cr_qs = _apply_post_filters(new_questions, new_embs)
            math_rejected += _m
            critic_rejected += _c
            if not new_questions:
                post_filter_rounds += 1
                continue

            # En fazla `missing` kadar al; FAZLASI havuza (bir sonraki isteğe stok).
            filled = _accept(new_questions, new_embs)
            if len(new_questions) > filled:
                _pool_add(new_questions[filled:])
            post_filter_rounds += 1

        # ── Depo + üretim birleştirme (§3b) ─────────────────────────────────
        # `questions` şu ana kadar YALNIZ bu LLM geçişinin (üretim+retry+top-up)
        # sonucuydu (`llm_target`'a göre sınırlı); pool-first bloğunun getirdiği
        # `pool_questions` (varsa) şimdi BAŞA eklenir ve numaralandırma 1..N olarak
        # yeniden sıkıştırılır (mevcut `_accept`/math-critic filtrelerindeki
        # `model_copy(update={"number": ...})` kalıbı). Toplam `question_count`'u
        # aşmaz (savunma amaçlı kırpma — normalde zaten aşmaz).
        if pool_questions:
            _merged = list(pool_questions) + list(questions)
            _merged_embs = list(pool_embeddings) + list(accepted_embeddings)
            questions = [
                q.model_copy(update={"number": i + 1})
                for i, q in enumerate(_merged[:question_count])
            ]
            accepted_embeddings = _merged_embs[:question_count]

        # Trace bilgilerini sakla.
        self._last_dedup_rejected_string = dedup.rejected_count
        self._last_dedup_rejected_semantic = (
            semantic_dedup.rejected_count if semantic_dedup else 0
        )
        self._last_math_verifier_rejected = math_rejected
        self._last_critic_rejected = critic_rejected
        self._last_pool_math_rejected = pool_math_rejected
        self._last_pool_critic_rejected = pool_critic_rejected
        self._last_retry_rounds = retry_round
        self._last_temperature = temperature  # initial (jitter sonrası)
        self._last_final_temperature = retry_temperature if retry_round > 0 else temperature
        self._last_seed = seed
        self._last_requested_count = question_count
        self._last_delivered_count = len(questions)
        # self._last_pool_hit_count zaten pool-first bloğunun hemen sonrasında
        # atandı (bu birleştirmeden ETKİLENMEZ — pool_hit_count sabit kalır).
        # Embedding maliyeti (semantic dedup) — küçük ama "gerçek toplam" için dahil.
        if self._embedder is not None:
            _eu = getattr(self._embedder, "_last_usage", None)
            if _eu is not None:
                total_prompt_tokens += _eu.input_tokens
                total_cost_usd += _eu.estimated_cost_usd
        self._last_prompt_tokens = total_prompt_tokens
        self._last_completion_tokens = total_completion_tokens
        self._last_cost_usd = total_cost_usd
        # Yapılandırılmış cost log — Render/Sentry agregasyonu için kolay parse.
        logger.info(
            "cost_meter | grade=%s topic=%s kazanim=%s diff=%s "
            "prompt_tokens=%d completion_tokens=%d cost_usd=%.6f model=%s",
            grade, dist_topic, kazanim_kod or "AUTO", difficulty.value,
            total_prompt_tokens, total_completion_tokens, total_cost_usd,
            self._last_model_used,
        )

        # History'e kayıt: üretilen her soruyu normalize + bağlamlarıyla + embedding'iyle sakla.
        for idx, q in enumerate(questions):
            emb = accepted_embeddings[idx] if idx < len(accepted_embeddings) else None
            GENERATION_HISTORY.record(
                history_key,
                normalize_question(q.question),
                extract_context_tokens(q.question),
                embedding=emb,
            )

        # Cache write: başarılı üretim sonrası cache'e ekle (gelecek isteklerde hit için).
        # Yalnızca tam istenen sayıda soru üretildiyse (kısmi setler tekrar tetiklemesin).
        self._last_cache_hit = False
        if (
            settings.enable_generation_cache
            and len(questions) == question_count
        ):
            try:
                GENERATION_CACHE.put(
                    grade=grade,
                    topic_id=selection_key,
                    kazanim_kod=kazanim_kod,
                    difficulty=difficulty.value,
                    question_count=question_count,
                    questions=questions,
                    allowed_types=allowed_types,
                    yeni_nesil=yeni_nesil,
                    )
            except Exception as exc:
                logger.warning("Cache yazımı başarısız (yutuldu): %s", exc)

        # Depo (Faz 1, §3b-1): TESLİM EDİLEN sorular da havuza yazılır — eskiden
        # yalnız `spare_candidates` (kırpılan artık) yazılıyordu, teslim edilenler
        # depoya HİÇ girmiyordu; bu yüzden X kullanıcısına verilen sorular Y
        # kullanıcısına asla servis edilemiyordu. Elenenler zaten bu noktaya kadar
        # `questions`'a hiç girmedi (math_verifier/critic önceden düşürdü) →
        # depo çöp biriktirmez. "Bedava damga" (§3c): bu sorular ZATEN
        # `_apply_post_filters`/critic geçişinden geçti (enable_critic açıksa) →
        # tekrar servis edilirken critic'i tekrar ödemesin.
        #
        # FAIL-CLOSED (MUST-FIX 2, denetim 2026-07-28): `critic_verdicts_ok`
        # False/None ise critic ya hiç çalışmadı ya da fail-open modda (boş
        # verdict) hiçbir şeyi denetlemedi — bu durumda `critic_pass=1` YALAN
        # olurdu (denetlenmemiş soru sonsuza dek "temiz" damgalanırdı, Faz 2'nin
        # tembel damgası onu bir daha asla denetlemez). Şüphe varsa NULL bırak.
        # Pool-origin sorular (varsa) BU HAVUZDA zaten var — `add_many`'nin
        # INSERT OR IGNORE'u onlar için no-op olurdu (unique index çarpar) ama
        # gereksiz bir DB round-trip'i olmasın diye burada AYIKLANIR; onların
        # damgası zaten pool-first bloğunda (bedava geçti ya da tembel
        # damgalandı) yazıldı.
        _llm_delivered = questions
        if pool_questions:
            _pool_norms = {normalize_question(pq.question) for pq in pool_questions}
            _llm_delivered = [
                q for q in questions if normalize_question(q.question) not in _pool_norms
            ]
        if settings.enable_spare_pool and _llm_delivered:
            _delivered_critic_pass = (
                1 if (settings.enable_critic and critic_verdicts_ok) else None
            )
            _pool_add(
                _llm_delivered,
                source="live-delivered",
                critic_pass=_delivered_critic_pass,
                verifier_model=(
                    settings.critic_model if _delivered_critic_pass else None
                ),
            )

        return questions

    @property
    def last_model_used(self) -> str:
        return getattr(self, "_last_model_used", self.model)

    @property
    def last_few_shot_source(self) -> str:
        return getattr(self, "_last_few_shot_source", "static")

    @property
    def last_textbook_count(self) -> int:
        return getattr(self, "_last_textbook_count", 0)

    def build_last_trace(self) -> "GenerationTrace":
        from app.models.schemas import GenerationTrace
        return GenerationTrace(
            few_shot_source=getattr(self, "_last_few_shot_source", "static"),
            few_shot_count=getattr(self, "_last_few_shot_count", 0),
            textbook_count=getattr(self, "_last_textbook_count", 0),
            retrieval_avg_distance=getattr(self, "_last_retrieval_avg_distance", None),
            model_used=self.last_model_used,
            provider=getattr(self, "_last_provider", "gemini"),
            temperature=getattr(self, "_last_temperature", 0.0),
            final_temperature=getattr(self, "_last_final_temperature", None),
            seed=getattr(self, "_last_seed", 0),
            retry_rounds=getattr(self, "_last_retry_rounds", 0),
            dedup_rejected_string=getattr(self, "_last_dedup_rejected_string", 0),
            dedup_rejected_semantic=getattr(self, "_last_dedup_rejected_semantic", 0),
            math_verifier_rejected=getattr(self, "_last_math_verifier_rejected", 0),
            critic_rejected=getattr(self, "_last_critic_rejected", 0),
            requested_count=getattr(self, "_last_requested_count", 0),
            delivered_count=getattr(self, "_last_delivered_count", 0),
            cache_hit=getattr(self, "_last_cache_hit", False),
            prompt_tokens=getattr(self, "_last_prompt_tokens", 0),
            completion_tokens=getattr(self, "_last_completion_tokens", 0),
            estimated_cost_usd=getattr(self, "_last_cost_usd", 0.0),
            pool_hit_count=getattr(self, "_last_pool_hit_count", 0),
            pool_math_rejected=getattr(self, "_last_pool_math_rejected", 0),
            pool_critic_rejected=getattr(self, "_last_pool_critic_rejected", 0),
        )

    @staticmethod
    def _process_batch(
        batch: GeneratedBatch,
        dedup: BatchDeduplicator,
        valid_kazanim_codes: set[str],
        fallback_kazanim: str,
        starting_number: int = 1,
        allowed_types: set[QuestionType] | None = None,
    ) -> list[Question]:
        """Ham batch'i numaralanmış Question listesine çevirir; dedup paylaşımlı.

        allowed_types: dersin/kullanıcının izin verdiği tipler. Model bunun DIŞINDA
            bir tip döndürebiliyor ve bu sessiz bir felakete yol açıyordu — bkz.
            aşağıdaki tip-kaçağı bloğu. None → kontrol yapılmaz (matematik yolu).
        """
        # Şekilli tipte figür ZORUNLU: model "görseldeki ölçüye göre" deyip şekil
        # üretmezse soru cevaplanamaz → ele. (grafik_okuma direktifi bu aşamada
        # process_chart_directives ile SVG'ye dönüşmüş olur.)
        _figure_types = {
            QuestionType.GORSEL_GEOMETRI,
            QuestionType.ORUNTU_SEKIL,
            QuestionType.GRAFIK_OKUMA,
        }
        questions: list[Question] = []
        for raw in batch.questions:
            if dedup.is_duplicate(raw.question):
                continue
            # ── Tip kaçağı (ÖLÇÜLDÜ 2026-07-29, canlı 7. sınıf Sosyal kağıtları) ──
            # Model, istenen dağılımın DIŞINDA bir tip döndürebiliyor: sosyal
            # sorulara matematiğe özel `salt_islem` etiketi kondu (sosyal
            # DEFAULT_TYPES'ta böyle bir tip YOK). `salt_islem` `_MC_TYPES`'ta
            # olmadığı için 4-şık kapısı ATLANDI ve "…aşağıdakilerden hangisi
            # değildir?" soruları ŞIKSIZ teslim edildi — cevaplanamaz, cevap
            # anahtarında "A" yazıyor ama şık yok. Prompt de yalnız dağılımı
            # listeliyor, "listede olmayan tip YASAK" demiyordu (o da düzeltildi).
            #
            # Sıra önemli: ÖNCE kurtarmayı dene (şıklar varsa MC gibi işle, bedava),
            # ancak kurtarılamıyorsa ele. `qt` bundan sonra raw.question_type
            # YERİNE kullanılır — aksi halde kurtarma yarıda kalırdı.
            qt = raw.question_type
            if allowed_types and qt not in allowed_types:
                _opts = [o.strip() for o in (raw.options or []) if o and o.strip()]
                _inline, _ = _parse_mcq(raw.question, raw.answer)
                if len(_opts) >= 4 or (_inline and len(_inline) >= 4):
                    logger.info(
                        "Tip kaçağı kurtarıldı (%s → coktan_secmeli): %s",
                        qt.value, raw.question[:70],
                    )
                    qt = QuestionType.COKTAN_SECMELI
                else:
                    logger.info(
                        "İzinsiz tip atıldı (%s, şık yok): %s",
                        qt.value, raw.question[:70],
                    )
                    continue
            q_text = process_geo_directives(
                process_table_directives(
                    process_pattern_directives(
                        process_chart_directives(
                            repair_latex_control_chars(raw.question).strip()
                        )
                    )
                )
            )
            if qt in _figure_types and "<svg" not in q_text:
                logger.info(
                    "Şekilsiz görsel-tip sorusu atıldı (%s): %s",
                    qt.value, raw.question[:70],
                )
                continue
            # SVG geçerlilik: şekilli tipte gömülü SVG bloğu/bloklarının HER BİRİ geçerli
            # olmalı. q_text "metin + <svg>" biçiminde olduğundan TÜM metni DEĞİL, ÇIKARILAN
            # <svg> bloğunu doğrula (is_valid_svg girdinin <svg ile başlamasını şart koşar →
            # tüm metin verilirse geçerli figür de yanlışlıkla elenirdi). {{geo}}/{{chart}}/
            # {{pattern}} direktifleri bu aşamada zaten deterministik SVG'ye dönüşmüş olur.
            if qt in _figure_types and "<svg" in q_text:
                _blocks = extract_svg_blocks(q_text)
                _bad = next(
                    (is_valid_svg(s)[1] for _, _, s in _blocks if not is_valid_svg(s)[0]),
                    None,
                )
                if not _blocks or _bad:
                    logger.info(
                        "Bozuk SVG atıldı (%s, %s): %s",
                        qt.value, _bad or "svg bloğu yok", raw.question[:70],
                    )
                    continue
            # Çoktan seçmeli — YAPISAL şıklar (D1). Model `options` alanına 4 şık yazar
            # (structured output → şıksız drop biter); backend cevap harfini doğrular,
            # correct_index'i türetir ve şıkları metne DETERMİNİSTİK gömer (eski render'lar
            # geriye-uyumlu). Alan boşsa (eski-format model) gömülü metinden parse edilir.
            mc_options: list[str] | None = None
            mc_correct_index: int | None = None
            if qt in _MC_TYPES:
                opts = [o.strip() for o in (raw.options or []) if o and o.strip()]
                if len(opts) < 4:
                    parsed, _ = _parse_mcq(q_text, raw.answer)  # geriye-uyum: gömülü metin
                    if parsed and len(parsed) >= 4:
                        opts = [o.strip() for o in parsed[:4] if o.strip()]
                if len(opts) != 4:
                    logger.info("Yapısal şıksız/eksik MC atıldı (%s, %d şık): %s",
                                qt.value, len(opts), raw.question[:70])
                    continue
                letter = _answer_letter(raw.answer)
                if not letter or letter not in ("A", "B", "C", "D"):
                    logger.info("MC cevap harfi çözülemedi (%r): %s",
                                (raw.answer or "")[:30], raw.question[:70])
                    continue
                mc_options = opts
                mc_correct_index = ("A", "B", "C", "D").index(letter)
                # Şıklar metinde henüz yoksa deterministik göm (eski PDF/web/mobil metni okur).
                if not all(f"{L})" in q_text for L in ("A", "B", "C", "D")):
                    q_text = q_text.rstrip() + "\n\n" + "\n".join(
                        f"{L}) {o}" for L, o in zip(("A", "B", "C", "D"), opts)
                    )
            # İşlenmemiş `{{...}}` direktifi: model satır ayracını (`;;`) atlayınca
            # process_table_directives bozuk kabul edip metni AYNEN geri veriyor →
            # öğrenci ham kodu görüyor (canlı kağıtta ölçüldü). DİKKAT: bu kontrol
            # reference_integrity_issue'dan ÖNCE gelmeli — ham direktifin içindeki
            # `|` işaretleri oradaki markdown-tablo dedektörünü kandırıp "tablo atfı
            # var ama tablo yok" kapısını sessizce açıyor.
            directive_issue = leftover_directive_issue(q_text)
            if directive_issue:
                logger.info(
                    "İşlenmemiş direktif atıldı (%s): %s", directive_issue, raw.question[:70]
                )
                continue
            # Kesik kök: cümle ortasında biten soru cevaplanamaz (canlı kağıtta
            # ölçüldü: "…fethedilen yerlerdeki halka gösterilen"). Kalite terazisinde
            # `truncated_stem` 0/5 yakalanıyordu — kontrol hiç yoktu.
            trunc_issue = truncated_stem_issue(q_text)
            if trunc_issue:
                logger.info(
                    "Kesik kök atıldı (%s): %s", trunc_issue, raw.question[:70]
                )
                continue
            # Atıf bütünlüğü: "öncüllere/görsele/tabloya göre" deyip o öğeyi İÇERMEYEN
            # soru cevaplanamaz → ele (top-up doldurur). WS-5.27.
            ref_issue = reference_integrity_issue(q_text)
            if ref_issue:
                logger.info(
                    "Atıf bütünlüğü ihlali (%s): %s", ref_issue, raw.question[:70]
                )
                continue
            # Eşleştirme/sıralama: gövde yalnız yönerge, öğe/şık listesi yok →
            # cevaplanamaz (WS: sosyal PDF boş eşleştirme/sıralama) → ele, top-up doldurur.
            content_issue = structured_content_issue(qt, q_text)
            if content_issue:
                logger.info(
                    "Yapısal içerik eksik (%s): %s", content_issue, raw.question[:70]
                )
                continue
            # Dangling HTML tag: "altı çizili" yazılı ama <u> tag'i var, tırnak yok → ele.
            # Model prompt'ta tırnak kullansın dedirtilse de fallback kontrol.
            has_underline_markup = "<u>" in q_text or "<b>" in q_text or "<i>" in q_text
            has_quoted_markup = '"' in q_text
            if has_underline_markup and not has_quoted_markup:
                logger.info(
                    "Dangling HTML tag (tırnak yok): %s", raw.question[:70]
                )
                continue
            kod = raw.kazanim_kod if raw.kazanim_kod in valid_kazanim_codes else fallback_kazanim
            dedup.add(raw.question)
            steps = raw.solution_steps
            if isinstance(steps, str):
                # Onarımı strip'ten ÖNCE yap: baştaki \frac gibi bir komut
                # \x0c'ye dönüşmüşse strip() o ipucunu silerdi.
                steps = repair_latex_control_chars(steps).strip()
            questions.append(
                Question(
                    number=starting_number + len(questions),
                    question=q_text,
                    answer=repair_latex_control_chars(raw.answer).strip(),
                    solution_steps=steps,
                    kazanim_kod=kod,
                    question_type=qt,
                    options=mc_options,
                    correct_index=mc_correct_index,
                )
            )
        return questions

    @staticmethod
    def _apply_semantic_dedup(
        candidates: list[Question],
        embedder: GeminiEmbedder | None,
        semantic_dedup: SemanticDeduplicator | None,
    ) -> tuple[list[Question], list[list[float]]]:
        """String dedup'tan geçmiş soruları embedding ile yeniden eler.

        Embedder veya semantic_dedup yoksa fail-open: hepsini geçirir, embedding boş döner.
        """
        if not candidates:
            return [], []
        if embedder is None or semantic_dedup is None:
            return candidates, []

        texts = [q.question for q in candidates]
        try:
            embeddings = embedder.embed_many(texts)
        except EmbedderError as exc:
            logger.warning("Batch embedding başarısız, semantic dedup atlanıyor: %s", exc)
            return candidates, []

        accepted: list[Question] = []
        accepted_embs: list[list[float]] = []
        next_number = candidates[0].number
        for q, emb in zip(candidates, embeddings):
            is_dup, sim = semantic_dedup.is_duplicate(emb)
            if is_dup:
                semantic_dedup.record_rejection()
                logger.info(
                    "Semantic duplicate atıldı (sim=%.3f): %s",
                    sim, q.question[:80],
                )
                continue
            semantic_dedup.add(emb)
            # Numaralandırmayı sıkı tut (semantic eleme sonrası boşluk kalmasın).
            accepted.append(q.model_copy(update={"number": next_number}))
            accepted_embs.append(emb)
            next_number += 1
        return accepted, accepted_embs
