"""LLM judge: üretilen soruları matematik doğruluğu, çözüm tutarlılığı, kazanım uyumu
ve zorluk seviyesi açısından değerlendiren ikinci-geçiş doğrulayıcı.

Fail-open: critic erişilemezse veya yanıtı parse edilemezse soruları geçirir
(sessizce reddetmek yerine üretimi sürdürür, hatayı loglar).
"""
from __future__ import annotations

import logging
import random
import time

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel, ValidationError

from app.config import settings
from app.data.curriculum import Kazanim
from app.models.enums import Difficulty
from app.models.schemas import Question

logger = logging.getLogger(__name__)


class CriticVerdict(BaseModel):
    question_index: int
    is_valid: bool
    confidence: float
    issues: list[str] = []


class CriticBatch(BaseModel):
    verdicts: list[CriticVerdict]


CRITIC_SYSTEM_PROMPT = """Sen MEB matematik müfredatı için soru doğrulayıcısısın.
Sana bir soru listesi + kazanım metinleri + hedef zorluk verilir.
Her soru için şunları denetle:

1. **Matematiksel doğruluk** — verilen cevap doğru mu? Çözüm adımları cevabı destekliyor mu?
2. **Çözüm tutarlılığı** — adımlar mantıksal sırada mı, hatalı bir aritmetik var mı?
3. **Kazanım uyumu** — soru, iddia edilen kazanım koduyla örtüşüyor mu?
4. **Zorluk uyumu** — soru, hedef zorluk seviyesine (kolay/orta/zor) uygun mu?
   - kolay = tek adım, küçük sayılar, doğrudan kazanım uygulaması
   - orta = 2-3 adım, sözel bağlam mümkün
   - zor = 3+ adım, akıl yürütme, çoklu kazanım ya da çıkarsama

Her soru için:
- is_valid: yukarıdaki 4 maddeyi geçiyor mu (true/false)
- confidence: 0.0–1.0 arası kararına olan güvenin
- issues: tespit ettiğin somut sorunların kısa listesi (boş bırakabilirsin)

Yalnızca JSON döndür: {"verdicts": [{"question_index": 0, "is_valid": true, "confidence": 0.95, "issues": []}, ...]}
"""


class CriticError(Exception):
    pass


class GeminiCritic:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        key = api_key or settings.gemini_api_key
        if not key:
            raise CriticError("GEMINI_API_KEY ayarı boş.")
        self.client = genai.Client(api_key=key)
        # Critic için flash-lite yeterli; hız önemli, yaratıcılık değil.
        self.model = model or settings.critic_model
        # Son evaluate() çağrısının Gemini token kullanımı — maliyet ölçümü için
        # agent bunu toplam maliyete ekler (critic ayrı bir Gemini çağrısıdır).
        from app.services.llm_providers import TokenUsage
        self._last_usage = TokenUsage(model_name=self.model)

    def evaluate(
        self,
        questions: list[Question],
        kazanimlar: list[Kazanim],
        difficulty: Difficulty,
    ) -> list[CriticVerdict]:
        """Her soru için verdict döner. Critic çağrısı tamamen başarısızsa boş liste — fail-open."""
        from app.services.llm_providers import TokenUsage
        self._last_usage = TokenUsage(model_name=self.model)  # sıfırla
        if not questions:
            return []

        kazanim_block = "\n".join(
            f"- {k['kod']}: {k['metin']}" for k in kazanimlar
        )
        questions_block = "\n\n".join(
            f"[{i}] kazanım: {q.kazanim_kod} | tip: {q.question_type.value}\n"
            f"Soru: {q.question}\n"
            f"Cevap: {q.answer}\n"
            f"Çözüm: {q.solution_steps}"
            for i, q in enumerate(questions)
        )
        prompt = (
            f"Hedef zorluk: {difficulty.value}\n\n"
            f"Geçerli kazanımlar:\n{kazanim_block}\n\n"
            f"Değerlendirilecek sorular:\n{questions_block}"
        )

        config = types.GenerateContentConfig(
            system_instruction=CRITIC_SYSTEM_PROMPT,
            temperature=0.1,  # deterministic, akıl yürütme değil denetim
            response_mime_type="application/json",
            response_schema=CriticBatch,
        )

        try:
            response = self._call_with_backoff(prompt, config)
        except CriticError as exc:
            logger.warning("Critic çağrısı başarısız, sorular geçiriliyor (fail-open): %s", exc)
            return []

        # Token kullanımını ölç (maliyet için).
        um = getattr(response, "usage_metadata", None)
        if um is not None:
            self._last_usage = TokenUsage(
                input_tokens=getattr(um, "prompt_token_count", 0) or 0,
                output_tokens=getattr(um, "candidates_token_count", 0) or 0,
                model_name=self.model,
            )

        try:
            batch = self._parse_response(response)
        except CriticError as exc:
            logger.warning("Critic yanıtı parse edilemedi, sorular geçiriliyor: %s", exc)
            return []

        return batch.verdicts

    def _call_with_backoff(
        self,
        prompt: str,
        config: types.GenerateContentConfig,
        max_attempts: int = 2,
        base_delay: float = 1.5,
    ) -> types.GenerateContentResponse:
        last_exc: Exception | None = None
        for attempt in range(1, max_attempts + 1):
            try:
                return self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=config,
                )
            except genai_errors.ServerError as exc:
                last_exc = exc
                status = getattr(exc, "code", None)
                if status not in (500, 502, 503, 504) or attempt == max_attempts:
                    raise CriticError(f"Critic sunucu hatası: {exc}") from exc
                delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.4)
                logger.warning(
                    "Critic geçici hata (%s), %.1fs sonra tekrar (%s/%s)",
                    status, delay, attempt, max_attempts,
                )
                time.sleep(delay)
            except genai_errors.ClientError as exc:
                raise CriticError(f"Critic istemci hatası: {exc}") from exc
            except Exception as exc:
                raise CriticError(f"Critic beklenmeyen hata: {exc}") from exc
        raise CriticError(f"Critic tükendi: {last_exc}")

    @staticmethod
    def _parse_response(response: types.GenerateContentResponse) -> CriticBatch:
        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, CriticBatch):
            return parsed
        text = getattr(response, "text", None)
        if not text:
            raise CriticError("Critic boş yanıt döndü.")
        try:
            return CriticBatch.model_validate_json(text)
        except ValidationError as exc:
            raise CriticError("Critic JSON şemaya uymadı.") from exc
