"""Gemini embedding wrapper (gemini-embedding-001, 3072 boyut)."""
import logging
import math
import random
import time
from typing import Iterable

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.config import settings
from app.services.gemini_client import make_gemini_client

logger = logging.getLogger(__name__)

_MAX_BATCH_SIZE = 100  # Gemini embedContent batch limiti (güvenli tutuldu)


class EmbedderError(Exception):
    pass


class GeminiEmbedder:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        key = api_key or settings.gemini_api_key
        if not key:
            raise EmbedderError("GEMINI_API_KEY ayarı boş.")
        self.client = make_gemini_client(key)
        self.model = model or settings.gemini_embedding_model
        self.dimensions = settings.embedding_dimensions
        # Son embed_many() çağrısının maliyet ölçümü (embedding yalnız girdi ücretli).
        # Token sayısı ~kar/4 ile tahmin edilir (Gemini embed API token döndürmez).
        from app.services.llm_providers import TokenUsage
        self._last_usage = TokenUsage(model_name=self.model)

    @staticmethod
    def _normalize(vec: list[float]) -> list[float]:
        norm = math.sqrt(sum(v * v for v in vec))
        if norm == 0:
            return vec
        return [v / norm for v in vec]

    def embed_one(self, text: str) -> list[float]:
        return self.embed_many([text])[0]

    def embed_many(
        self,
        texts: Iterable[str],
        max_attempts: int = 4,
        base_delay: float = 1.5,
    ) -> list[list[float]]:
        """Çok sayıda metni batch ederek embed eder. 503 için backoff uygular."""
        all_texts = list(texts)
        if not all_texts:
            return []
        # Maliyet ölçümü: embedding girdi token'ı ~toplam karakter/4.
        from app.services.llm_providers import TokenUsage
        _est_tokens = sum(len(t) for t in all_texts) // 4
        self._last_usage = TokenUsage(input_tokens=_est_tokens, model_name=self.model)
        results: list[list[float]] = []
        for start in range(0, len(all_texts), _MAX_BATCH_SIZE):
            chunk = all_texts[start : start + _MAX_BATCH_SIZE]
            embeddings = self._embed_with_backoff(chunk, max_attempts, base_delay)
            results.extend(embeddings)
        return results

    def _embed_with_backoff(
        self,
        chunk: list[str],
        max_attempts: int,
        base_delay: float,
    ) -> list[list[float]]:
        last_exc: Exception | None = None
        for attempt in range(1, max_attempts + 1):
            try:
                r = self.client.models.embed_content(
                    model=self.model,
                    contents=chunk,
                    config=types.EmbedContentConfig(output_dimensionality=self.dimensions),
                )
                # 3072 dışı boyutlarda Gemini normalize garantisi vermez → cosine için normalize et
                return [self._normalize(e.values) for e in r.embeddings]
            except genai_errors.ServerError as exc:
                last_exc = exc
                status = getattr(exc, "code", None)
                if status not in (500, 502, 503, 504) or attempt == max_attempts:
                    raise EmbedderError(f"Embedding başarısız: {exc}") from exc
                delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.4)
                logger.warning(
                    "Embedding geçici hata (%s), %.1fs sonra tekrar (%s/%s)",
                    status, delay, attempt, max_attempts,
                )
                time.sleep(delay)
            except genai_errors.ClientError as exc:
                raise EmbedderError(f"Embedding istemci hatası: {exc}") from exc
            except Exception as exc:
                raise EmbedderError(f"Embedding beklenmeyen hata: {exc}") from exc
        raise EmbedderError(f"Embedding tükendi: {last_exc}")
