"""Gemini tabanlı soru üretim servisi."""
import logging
import random
import time

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel, ValidationError

from app.config import settings
from app.data.curriculum import Kazanim, get_topic
from app.models.enums import Difficulty, QuestionType
from app.models.schemas import Question
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
from app.services.history import DEFAULT_TENANT, GENERATION_HISTORY, HistoryKey
from app.services.retriever import ExampleRetriever, get_retriever

logger = logging.getLogger(__name__)


class GeneratedQuestion(BaseModel):
    question: str
    answer: str
    solution_steps: str
    kazanim_kod: str
    question_type: QuestionType


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
        retrieved = retriever.retrieve(
            query_text=query,
            grade=grade,
            kazanim_kod=k["kod"],
            topic_id=topic_id,
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
    """RAG veya statik havuzdan few-shot toplar. İkinci değer kaynak ('rag' / 'static')."""
    if settings.use_rag:
        retriever = get_retriever()
        if retriever is not None and retriever.count() > 0:
            rag_pool = _collect_few_shot_rag(
                retriever, grade, topic_id, kazanimlar, target_difficulty, max_total, rng
            )
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
        try:
            chunks = retriever.retrieve_textbook(
                query_text=query,
                grade=grade,
                kazanim_kod=k["kod"],
                topic_id=topic_id,
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


class GeminiAgent:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        fallback_models: list[str] | None = None,
    ) -> None:
        key = api_key or settings.gemini_api_key
        if not key:
            raise AgentError("GEMINI_API_KEY ayarı boş. .env dosyanızı kontrol edin.")
        self.client = genai.Client(api_key=key)
        self.model = model or settings.gemini_model
        self.fallback_models = (
            fallback_models if fallback_models is not None else settings.fallback_model_list
        )
        self._embedder: GeminiEmbedder | None = None
        self._critic: GeminiCritic | None = None

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

    def _get_critic(self) -> GeminiCritic | None:
        if self._critic is not None:
            return self._critic
        try:
            self._critic = GeminiCritic()
            return self._critic
        except CriticError as exc:
            logger.warning("Critic başlatılamadı, doğrulama devre dışı: %s", exc)
            return None

    def generate(
        self,
        grade: int,
        topic_id: str,
        kazanim_kod: str | None,
        difficulty: Difficulty,
        question_count: int,
        seed: int | None = None,
        temperature: float | None = None,
        max_retry_rounds: int = 1,
        include_textbook: bool = True,
        tenant_id: str | None = None,
    ) -> list[Question]:
        # Seed jitter: aynı parametrelerle yapılan art arda çağrılar farklı sonuç versin.
        if seed is None:
            seed = time.time_ns() % (2**31)
        rng = random.Random(seed)
        if temperature is None:
            base_temp = DIFFICULTY_TEMPERATURES[difficulty]
            jitter = rng.uniform(-TEMPERATURE_JITTER, TEMPERATURE_JITTER)
            temperature = _clamp_temp(base_temp + jitter)

        kazanimlar = _select_kazanimlar(grade, topic_id, kazanim_kod)
        distribution = distribute_question_types(question_count, difficulty, topic_id=topic_id)
        few_shot, few_shot_source = _collect_few_shot(
            grade,
            topic_id,
            kazanimlar,
            distribution,
            target_difficulty=difficulty.value,
            max_total=6,
            rng=rng,
        )
        self._last_few_shot_source = few_shot_source
        self._last_few_shot_count = len(few_shot)
        textbook_chunks: list[dict] = []
        if include_textbook:
            textbook_chunks = _collect_textbook_context(
                grade=grade,
                topic_id=topic_id,
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
        topic = get_topic(grade, topic_id)
        assert topic is not None

        history_key: HistoryKey = (
            tenant_id or DEFAULT_TENANT,
            grade,
            topic_id,
            kazanim_kod or "__AUTO__",
            difficulty.value,
        )
        history_seen = GENERATION_HISTORY.seen_questions(history_key)
        history_contexts = GENERATION_HISTORY.context_exclusions(history_key)
        history_embeddings = GENERATION_HISTORY.seen_embeddings(history_key)

        user_prompt = build_user_prompt(
            grade=grade,
            topic_name=topic["name"],
            kazanimlar=kazanimlar,
            difficulty=difficulty,
            question_count=question_count,
            distribution=distribution,
            few_shot_examples=few_shot,
            context_exclusions=history_contexts,
            few_shot_source=few_shot_source,
            textbook_chunks=textbook_chunks,
        )

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=GeneratedBatch,
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

        # İlk üretim.
        response, model_used = self._call_with_backoff(user_prompt, config)
        self._last_model_used = model_used
        batch = self._parse_response(response)
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
            retry_config = types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=retry_temperature,
                response_mime_type="application/json",
                response_schema=GeneratedBatch,
            )
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
                response2, model_used2 = self._call_with_backoff(retry_prompt, retry_config)
                self._last_model_used = model_used2
                batch2 = self._parse_response(response2)
            except AgentError as exc:
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

        # Hedef sayıyı aşmasın.
        questions = questions[:question_count]
        accepted_embeddings = accepted_embeddings[: len(questions)]

        # Critic geçişi: matematik doğruluğu + kazanım/zorluk uyumu kontrolü.
        critic_rejected = 0
        if settings.enable_critic and questions:
            critic = self._get_critic()
            if critic is not None:
                verdicts = critic.evaluate(questions, kazanimlar, difficulty)
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

        # Trace bilgilerini sakla.
        self._last_dedup_rejected_string = dedup.rejected_count
        self._last_dedup_rejected_semantic = (
            semantic_dedup.rejected_count if semantic_dedup else 0
        )
        self._last_critic_rejected = critic_rejected
        self._last_retry_rounds = retry_round
        self._last_temperature = temperature  # initial (jitter sonrası)
        self._last_final_temperature = retry_temperature if retry_round > 0 else temperature
        self._last_seed = seed
        self._last_requested_count = question_count
        self._last_delivered_count = len(questions)

        # History'e kayıt: üretilen her soruyu normalize + bağlamlarıyla + embedding'iyle sakla.
        for idx, q in enumerate(questions):
            emb = accepted_embeddings[idx] if idx < len(accepted_embeddings) else None
            GENERATION_HISTORY.record(
                history_key,
                normalize_question(q.question),
                extract_context_tokens(q.question),
                embedding=emb,
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
            temperature=getattr(self, "_last_temperature", 0.0),
            final_temperature=getattr(self, "_last_final_temperature", None),
            seed=getattr(self, "_last_seed", 0),
            retry_rounds=getattr(self, "_last_retry_rounds", 0),
            dedup_rejected_string=getattr(self, "_last_dedup_rejected_string", 0),
            dedup_rejected_semantic=getattr(self, "_last_dedup_rejected_semantic", 0),
            critic_rejected=getattr(self, "_last_critic_rejected", 0),
            requested_count=getattr(self, "_last_requested_count", 0),
            delivered_count=getattr(self, "_last_delivered_count", 0),
        )

    def _call_with_backoff(
        self,
        user_prompt: str,
        config: types.GenerateContentConfig,
        max_attempts_per_model: int = 3,
        base_delay: float = 1.5,
    ) -> tuple[types.GenerateContentResponse, str]:
        """Her model için exponential backoff + jitter; tükenirse bir sonraki fallback modele geçer.

        Returns:
            (response, başarılı olan model adı)
        """
        models_to_try = [self.model, *self.fallback_models]
        last_exc: Exception | None = None
        for model_name in models_to_try:
            for attempt in range(1, max_attempts_per_model + 1):
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=user_prompt,
                        config=config,
                    )
                    return response, model_name
                except genai_errors.ServerError as exc:
                    last_exc = exc
                    status = getattr(exc, "code", None)
                    if status not in (500, 502, 503, 504):
                        logger.error("Gemini sunucu hatası (kalıcı): %s", exc)
                        raise AgentError(f"Gemini çağrısı başarısız: {exc}") from exc
                    if attempt == max_attempts_per_model:
                        logger.warning(
                            "%s modelinde %s denemede 503; sonraki modele geçiliyor.",
                            model_name,
                            max_attempts_per_model,
                        )
                        break  # Sonraki modele geç
                    delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
                    logger.warning(
                        "%s modelinde geçici hata (%s); %.1fs sonra tekrar denenecek (%s/%s)",
                        model_name, status, delay, attempt, max_attempts_per_model,
                    )
                    time.sleep(delay)
                except genai_errors.ClientError as exc:
                    logger.error("Gemini istemci hatası: %s", exc)
                    raise AgentError(f"Gemini çağrısı başarısız: {exc}") from exc
                except Exception as exc:
                    logger.exception("Beklenmeyen Gemini hatası")
                    raise AgentError(f"Gemini çağrısı başarısız: {exc}") from exc
        raise AgentError(
            "Gemini tüm modellerde (primary + fallback) kapasite darlığı yaşıyor. "
            f"Son hata: {last_exc}"
        )

    @staticmethod
    def _parse_response(response: types.GenerateContentResponse) -> GeneratedBatch:
        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, GeneratedBatch):
            return parsed
        text = getattr(response, "text", None)
        if not text:
            raise AgentError("Gemini boş yanıt döndü.")
        try:
            return GeneratedBatch.model_validate_json(text)
        except ValidationError as exc:
            logger.error("Gemini çıktısı şemaya uymadı: %s", text[:500])
            raise AgentError("Gemini çıktısı beklenen JSON şemasına uymadı.") from exc

    @staticmethod
    def _process_batch(
        batch: GeneratedBatch,
        dedup: BatchDeduplicator,
        valid_kazanim_codes: set[str],
        fallback_kazanim: str,
        starting_number: int = 1,
    ) -> list[Question]:
        """Ham batch'i numaralanmış Question listesine çevirir; dedup paylaşımlı."""
        questions: list[Question] = []
        for raw in batch.questions:
            if dedup.is_duplicate(raw.question):
                continue
            kod = raw.kazanim_kod if raw.kazanim_kod in valid_kazanim_codes else fallback_kazanim
            dedup.add(raw.question)
            questions.append(
                Question(
                    number=starting_number + len(questions),
                    question=raw.question.strip(),
                    answer=raw.answer.strip(),
                    solution_steps=raw.solution_steps.strip(),
                    kazanim_kod=kod,
                    question_type=raw.question_type,
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
