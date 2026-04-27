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
from app.services.diversity import (
    BatchDeduplicator,
    distribute_question_types,
    extract_context_tokens,
    normalize_question,
)
from app.services.examples import get_examples_for_kazanim
from app.services.history import GENERATION_HISTORY, HistoryKey
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
    """Statik (manuel) few-shot havuzundan örnek toplar — RAG kapalıysa veya fallback."""
    preferred = list(distribution.keys())
    pool: list[dict] = []
    for k in kazanimlar:
        examples = get_examples_for_kazanim(
            grade,
            k["kod"],
            max_count=2,
            preferred_types=preferred,
            target_difficulty=target_difficulty,
            rng=rng,
        )
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
        )
        pool.extend(retrieved)

    # Rastgele jitter + tercihe göre sıralama (hedef zorluk önde).
    rng.shuffle(pool)
    pool.sort(
        key=lambda e: (0 if e.get("difficulty") == target_difficulty else 1,)
    )
    return pool[:max_total]


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
    ) -> list[Question]:
        # Seed jitter: aynı parametrelerle yapılan art arda çağrılar farklı sonuç versin.
        if seed is None:
            seed = time.time_ns() % (2**31)
        rng = random.Random(seed)
        if temperature is None:
            temperature = DIFFICULTY_TEMPERATURES[difficulty]

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
        textbook_chunks: list[dict] = []
        if include_textbook:
            textbook_chunks = _collect_textbook_context(
                grade=grade,
                topic_id=topic_id,
                kazanimlar=kazanimlar,
                target_difficulty=difficulty.value,
                max_total=3,
            )
        self._last_textbook_count = len(textbook_chunks)
        logger.info(
            "Few-shot kaynağı: %s (%s örnek) | textbook chunks: %s",
            few_shot_source, len(few_shot), len(textbook_chunks),
        )
        topic = get_topic(grade, topic_id)
        assert topic is not None

        history_key: HistoryKey = (
            grade,
            topic_id,
            kazanim_kod or "__AUTO__",
            difficulty.value,
        )
        history_seen = GENERATION_HISTORY.seen_questions(history_key)
        history_contexts = GENERATION_HISTORY.context_exclusions(history_key)

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

        valid_kazanim_codes = {k["kod"] for k in kazanimlar}
        fallback_kazanim = kazanimlar[0]["kod"]

        # İlk üretim.
        response, model_used = self._call_with_backoff(user_prompt, config)
        self._last_model_used = model_used
        batch = self._parse_response(response)
        questions = self._process_batch(
            batch, dedup, valid_kazanim_codes, fallback_kazanim, starting_number=1
        )

        # Eksik kaldıysa yeniden üretim.
        retry_round = 0
        while (
            len(questions) < question_count
            and retry_round < max_retry_rounds
            and batch.questions  # ilk çağrı tamamen boşsa retry etme
        ):
            missing = question_count - len(questions)
            retry_prompt = build_retry_prompt(
                original_user_prompt=user_prompt,
                already_generated_questions=[q.question for q in questions],
                missing_count=missing,
            )
            logger.info(
                "Eksik %s soru için yeniden üretim (round %s)",
                missing,
                retry_round + 1,
            )
            try:
                response2, model_used2 = self._call_with_backoff(retry_prompt, config)
                self._last_model_used = model_used2
                batch2 = self._parse_response(response2)
            except AgentError as exc:
                logger.warning("Retry başarısız, mevcut sorularla devam ediliyor: %s", exc)
                break
            more = self._process_batch(
                batch2,
                dedup,
                valid_kazanim_codes,
                fallback_kazanim,
                starting_number=len(questions) + 1,
            )
            if not more:
                break
            questions.extend(more[:missing])
            retry_round += 1

        # Hedef sayıyı aşmasın.
        questions = questions[:question_count]

        # History'e kayıt: üretilen her soruyu normalize + bağlamlarıyla sakla.
        for q in questions:
            GENERATION_HISTORY.record(
                history_key,
                normalize_question(q.question),
                extract_context_tokens(q.question),
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
