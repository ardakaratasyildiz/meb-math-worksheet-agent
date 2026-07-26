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
    reference_integrity_issue,
    structured_content_issue,
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
        # Over-generation (latency): ilk batch'i hedeften fazla iste ki math/critic
        # elemeleri seri top-up turu açmadan absorbe edilsin. Eleme oranı ~%41
        # üretimde >0; overshoot bunları tek çağrıda karşılar. question_count
        # (gerçek hedef) cache anahtarı, retry/top-up durdurma koşulu ve sondaki
        # kırpma için korunur; yalnızca İLK çağrının dağıtım+prompt hedefi büyür.
        from math import ceil as _ceil
        _overshoot = settings.generation_overshoot_ratio or 1.0
        gen_target = _ceil(question_count * _overshoot) if _overshoot > 1.0 else question_count
        distribution = distribute_question_types(
            gen_target, difficulty, topic_id=dist_topic, allowed_types=allowed_set,
            yeni_nesil=yeni_nesil,
        )

        # History anahtarı — hem cache lookup hem üretim sonrası kayıt için.
        # selection_key (unit_id veya topic_id) namespace'i ayırır.
        history_key: HistoryKey = (
            tenant_id or DEFAULT_TENANT,
            grade,
            selection_key,
            kazanim_kod or "__AUTO__",
            difficulty.value,
        )

        # --- Cache lookup (Sprint 6) ---------------------------------------
        # Aynı (grade, topic, kazanım, zorluk, count, tip, yeni_nesil) için önceden
        # üretilmiş set varsa LLM çağrısını atla. Kullanıcının history'sinde bulunan
        # sorulara sahip set'ler atlanır → tekrar dağıtım önlenir.
        # yeni_nesil (premium) setleri de cache'lenir; cache anahtarına dahil
        # olduğundan normal setlerle ayrı havuzda tutulur (kaliteler karışmaz).
        if settings.enable_generation_cache:
            history_seen_norm = GENERATION_HISTORY.seen_questions(history_key)
            cached = GENERATION_CACHE.get(
                grade=grade,
                topic_id=selection_key,
                kazanim_kod=kazanim_kod,
                difficulty=difficulty.value,
                question_count=question_count,
                exclude_questions=history_seen_norm,
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
        # history_key yukarıda cache lookup için tanımlandı (cache devredeyken).
        # Cache devre dışıysa burada üret (selection_key = unit_id veya topic_id).
        if not settings.enable_generation_cache:
            history_key = (
                tenant_id or DEFAULT_TENANT,
                grade,
                selection_key,
                kazanim_kod or "__AUTO__",
                difficulty.value,
            )
        history_seen = GENERATION_HISTORY.seen_questions(history_key)
        history_contexts = GENERATION_HISTORY.context_exclusions(history_key)
        history_embeddings = GENERATION_HISTORY.seen_embeddings(history_key)

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
        accepted_embeddings: list[list[float]] = []

        valid_kazanim_codes = {k["kod"] for k in kazanimlar}
        fallback_kazanim = kazanimlar[0]["kod"]

        # Cost metering — bu generate() boyunca tüm LLM call'ların token toplamı.
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_cost_usd = 0.0

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
            batch, dedup, valid_kazanim_codes, fallback_kazanim, starting_number=1
        )
        questions, new_embs = self._apply_semantic_dedup(
            candidates, embedder, semantic_dedup
        )
        accepted_embeddings.extend(new_embs)

        # Eksik kaldıysa yeniden üretim. Sıcaklığı boost ederek yaratıcılığı arttır.
        retry_round = 0
        retry_temperature = temperature
        while (
            len(questions) < question_count
            and retry_round < max_retry_rounds
            and batch.questions  # ilk çağrı tamamen boşsa retry etme
        ):
            missing = question_count - len(questions)
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

        # Hedef sayıyı aşmasın. FAZLALAR ATILMAZ: overshoot (1.8) ile üretilip
        # kırpılan geçerli sorular `spare_candidates`'a alınır; post-filter
        # eksiği önce BURADAN, sonra kalıcı havuzdan karşılanır — LLM top-up
        # çağrısı (ölçüm: 19-24K çıktı token'ı) ancak ikisi de yetmezse atılır.
        spare_candidates = questions[question_count:]
        spare_embeddings = accepted_embeddings[question_count:]
        questions = questions[:question_count]
        accepted_embeddings = accepted_embeddings[: len(questions)]
        pool_key = _pool_key(
            grade, selection_key, kazanim_kod, difficulty.value,
            allowed_types, yeni_nesil,
        )

        # Deterministic math verifier: SymPy ile aritmetik doğrulama.
        # Critic'ten ÖNCE çalışır — ucuz, hızlı, yanılma payı yok.
        # Non-math'te SymPy math_verifier ATLANIR (aritmetik doğrulama math'e özel;
        # sözel/fen soruları verifiable değil → no-op olurdu, netlik için atlanır).
        math_rejected = 0
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
                math_rejected = len(drop_indices)

        # Critic bağlamı (non-math RAG) tek generate() içinde DEĞİŞMEZ → bir kez
        # topla, tüm critic geçişlerinde yeniden kullan. Eskiden her top-up turu
        # yeniden çağırıyordu (her çağrı = embedding API isteği).
        _critic_ctx_cache: dict[str, str] = {}

        def _critic_context() -> str:
            if "v" not in _critic_ctx_cache:
                _critic_ctx_cache["v"] = _collect_critic_context(
                    subject, grade, kazanimlar
                )
            return _critic_ctx_cache["v"]

        # Critic geçişi: matematik doğruluğu + kazanım/zorluk uyumu kontrolü.
        critic_rejected = 0
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
                        critic_rejected = len(drop_indices)

        # ── Post-filter doldurma ────────────────────────────────────────────
        # math_verifier/critic soru düşürdüyse eksiği kapat. SIRA (maliyet):
        #   1) bu istekte fazla üretilmiş yedekler  → BEDAVA (zaten ödendi)
        #   2) kalıcı yedek havuzu                  → BEDAVA (önceki istekler)
        #   3) LLM top-up çağrısı                   → PAHALI (son çare)
        # Eskiden yalnız (3) vardı ve fazlalar çöpe gidiyordu.
        def _apply_post_filters(qs: list, embs: list) -> tuple[list, list, int, int]:
            """math_verifier + critic uygular → (kalan, embedding, math_red, critic_red).
            Critic token'ı toplam maliyete eklenir."""
            nonlocal total_prompt_tokens, total_completion_tokens, total_cost_usd
            m_rej = c_rej = 0
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
                    verdicts_c = _critic.evaluate(
                        qs, kazanimlar, difficulty, context=_critic_context()
                    ) or []
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
                        qs = [q for i, q in enumerate(qs) if i not in drop_c]
                        if embs:
                            embs = [e for i, e in enumerate(embs) if i not in drop_c]
                        c_rej = len(drop_c)
            return qs, embs, m_rej, c_rej

        # Havuz BEST-EFFORT: yazma/okuma hatası üretimi ASLA düşürmemeli.
        # Prod'da havuz Turso'ya yazar ve mixed modda 3 bucket PARALEL thread'te
        # koşar; bir DB hatası (kilit/istemci) çıplak bırakılırsa bucket'ın
        # `except Exception`'ı HAZIR SORULARI çöpe atar (canlıda 5 istenen kağıtta
        # orta bucket'ın 3 sorusu böyle kayboldu → 2/5 teslim). `llm_cache.put`
        # de aynı sözleşmeyi kullanıyor ("Cache yazımı başarısız (yutuldu)").
        def _pool_add(qs: list) -> None:
            if not (settings.enable_spare_pool and qs):
                return
            try:
                SPARE_POOL.add_many(pool_key, qs)
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
            take_n = question_count - len(questions)
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
        if len(questions) < question_count:
            free_qs: list = list(spare_candidates)
            # Embedding listesi soru listesiyle HİZALI olmalı: `_apply_post_filters`
            # elemeyi index'e göre yapıyor. Semantic dedup kapalıysa embedding
            # listesi boş gelir → boş yer tutucularla hizala.
            free_embs: list = (
                list(spare_embeddings)
                if len(spare_embeddings) == len(spare_candidates)
                else [[] for _ in spare_candidates]
            )
            if len(free_qs) < (question_count - len(questions)):
                drawn = _pool_take(
                    (question_count - len(questions) - len(free_qs)) * 2
                )
                # Havuzdan gelenler bu batch'te tekrar olmasın.
                for q in drawn:
                    if not dedup.is_duplicate(q.question):
                        dedup.add(q.question)
                        free_qs.append(q)
                        free_embs.append([])
            if free_qs:
                kept, kept_embs, m_rej, c_rej = _apply_post_filters(free_qs, free_embs)
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
                        filled, len(free_qs), question_count - len(questions),
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
            len(questions) < question_count
            and post_filter_rounds < POST_FILTER_MAX_RETRIES
        ):
            missing = question_count - len(questions)
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
            )
            new_questions, new_embs = self._apply_semantic_dedup(
                new_candidates, embedder, semantic_dedup
            )
            if not new_questions:
                post_filter_rounds += 1
                continue

            new_questions, new_embs, _m, _c = _apply_post_filters(new_questions, new_embs)
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

        # Trace bilgilerini sakla.
        self._last_dedup_rejected_string = dedup.rejected_count
        self._last_dedup_rejected_semantic = (
            semantic_dedup.rejected_count if semantic_dedup else 0
        )
        self._last_math_verifier_rejected = math_rejected
        self._last_critic_rejected = critic_rejected
        self._last_retry_rounds = retry_round
        self._last_temperature = temperature  # initial (jitter sonrası)
        self._last_final_temperature = retry_temperature if retry_round > 0 else temperature
        self._last_seed = seed
        self._last_requested_count = question_count
        self._last_delivered_count = len(questions)
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
        )

    @staticmethod
    def _process_batch(
        batch: GeneratedBatch,
        dedup: BatchDeduplicator,
        valid_kazanim_codes: set[str],
        fallback_kazanim: str,
        starting_number: int = 1,
    ) -> list[Question]:
        """Ham batch'i numaralanmış Question listesine çevirir; dedup paylaşımlı."""
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
            q_text = process_geo_directives(
                process_table_directives(
                    process_pattern_directives(
                        process_chart_directives(
                            repair_latex_control_chars(raw.question).strip()
                        )
                    )
                )
            )
            if raw.question_type in _figure_types and "<svg" not in q_text:
                logger.info(
                    "Şekilsiz görsel-tip sorusu atıldı (%s): %s",
                    raw.question_type.value, raw.question[:70],
                )
                continue
            # SVG geçerlilik: şekilli tipte gömülü SVG bloğu/bloklarının HER BİRİ geçerli
            # olmalı. q_text "metin + <svg>" biçiminde olduğundan TÜM metni DEĞİL, ÇIKARILAN
            # <svg> bloğunu doğrula (is_valid_svg girdinin <svg ile başlamasını şart koşar →
            # tüm metin verilirse geçerli figür de yanlışlıkla elenirdi). {{geo}}/{{chart}}/
            # {{pattern}} direktifleri bu aşamada zaten deterministik SVG'ye dönüşmüş olur.
            if raw.question_type in _figure_types and "<svg" in q_text:
                _blocks = extract_svg_blocks(q_text)
                _bad = next(
                    (is_valid_svg(s)[1] for _, _, s in _blocks if not is_valid_svg(s)[0]),
                    None,
                )
                if not _blocks or _bad:
                    logger.info(
                        "Bozuk SVG atıldı (%s, %s): %s",
                        raw.question_type.value, _bad or "svg bloğu yok", raw.question[:70],
                    )
                    continue
            # Çoktan seçmeli — YAPISAL şıklar (D1). Model `options` alanına 4 şık yazar
            # (structured output → şıksız drop biter); backend cevap harfini doğrular,
            # correct_index'i türetir ve şıkları metne DETERMİNİSTİK gömer (eski render'lar
            # geriye-uyumlu). Alan boşsa (eski-format model) gömülü metinden parse edilir.
            mc_options: list[str] | None = None
            mc_correct_index: int | None = None
            if raw.question_type in _MC_TYPES:
                opts = [o.strip() for o in (raw.options or []) if o and o.strip()]
                if len(opts) < 4:
                    parsed, _ = _parse_mcq(q_text, raw.answer)  # geriye-uyum: gömülü metin
                    if parsed and len(parsed) >= 4:
                        opts = [o.strip() for o in parsed[:4] if o.strip()]
                if len(opts) != 4:
                    logger.info("Yapısal şıksız/eksik MC atıldı (%s, %d şık): %s",
                                raw.question_type.value, len(opts), raw.question[:70])
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
            content_issue = structured_content_issue(raw.question_type, q_text)
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
                    question_type=raw.question_type,
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
