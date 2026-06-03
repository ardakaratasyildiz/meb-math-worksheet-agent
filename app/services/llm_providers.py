"""LLM provider abstraction — Gemini ve Anthropic için ortak arayüz.

Pipeline'ın provider-agnostic olması için yazılan ince katman:
- Her provider `generate(system, prompt, schema, temperature)` ile çağrılır.
- Ortak dönüş: ProviderResponse(parsed_obj, model_name, raw_text, retryable_error?)
- Pydantic schema'yı her iki SDK için adapt eder:
    * Gemini: response_schema kullanır (native Pydantic).
    * Anthropic: tool_use ile structured output (input_schema=JSON Schema dump).
"""
from __future__ import annotations

import json
import logging
import random
import time
from dataclasses import dataclass
from typing import Type, TypeVar

from pydantic import BaseModel, ValidationError

from app.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


# Fiyatlar (USD per 1M token, input/output). Cost metering loglaması için —
# kesin fatura değil; provider faturalarıyla periyodik karşılaştırılmalı.
# Gemini fiyatları ai.google.dev/gemini-api/docs/pricing (2026-06, ücretli tier,
# <=200k prompt) ile güncellendi. ÖNCEKİ değerler eskiydi (ör. 2.5-flash
# 0.075/0.30) → cost-meter ~8× DÜŞÜK raporluyordu.
PRICING_USD_PER_1M_TOKENS: dict[str, tuple[float, float]] = {
    "gemini-2.5-flash": (0.30, 2.50),
    "gemini-2.5-flash-lite": (0.10, 0.40),
    "gemini-2.5-pro": (1.25, 10.00),
    "gemini-3.5-flash": (1.50, 9.00),
    "gemini-3.1-pro-preview": (2.00, 12.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-opus-4-7": (15.00, 75.00),
    "claude-haiku-4-5-20251001": (0.80, 4.00),
}


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    model_name: str = ""

    @property
    def estimated_cost_usd(self) -> float:
        prices = PRICING_USD_PER_1M_TOKENS.get(self.model_name)
        if not prices:
            return 0.0
        in_p, out_p = prices
        return (self.input_tokens * in_p + self.output_tokens * out_p) / 1_000_000


@dataclass
class ProviderResponse:
    parsed: BaseModel | None
    model_name: str
    provider: str  # "gemini" | "anthropic"
    raw_text: str | None = None
    usage: TokenUsage | None = None


class ProviderError(Exception):
    """Provider'a özgü kalıcı hata — retry'a değmez."""


class ProviderTransientError(Exception):
    """Geçici hata (5xx, rate limit) — başka model/provider'a düş."""


# ---- Gemini ----


class GeminiProvider:
    def __init__(
        self,
        primary_model: str | None = None,
        fallback_models: list[str] | None = None,
    ) -> None:
        from google import genai
        if not settings.gemini_api_key:
            raise ProviderError("GEMINI_API_KEY boş.")
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.primary = primary_model or settings.gemini_model
        self.fallbacks = (
            fallback_models if fallback_models is not None
            else settings.fallback_model_list
        )

    @property
    def models(self) -> list[str]:
        return [self.primary, *self.fallbacks]

    def generate(
        self,
        system: str,
        prompt: str,
        schema: Type[T],
        temperature: float,
        model: str | None = None,
    ) -> ProviderResponse:
        from google import genai
        from google.genai import errors as genai_errors
        from google.genai import types

        model_name = model or self.primary
        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=schema,
        )
        try:
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,
            )
        except genai_errors.ServerError as exc:
            status = getattr(exc, "code", None)
            if status in (500, 502, 503, 504):
                raise ProviderTransientError(f"Gemini {status}: {exc}") from exc
            raise ProviderError(f"Gemini sunucu hatası: {exc}") from exc
        except genai_errors.ClientError as exc:
            # 429 = RESOURCE_EXHAUSTED (rate limit / kota). HTTP 4xx olduğu için
            # SDK bunu ClientError olarak fırlatır, ama KALICI değildir: kotanın
            # dakikalık penceresi sıfırlanınca tekrar denenince geçer. Yüksek
            # trafikte free-tier'ın baskın hatası budur; kalıcı sayılırsa tüm
            # (aynı kotayı paylaşan) Gemini fallback zinciri backoff'suz anında
            # tükenir → kullanıcıya gereksiz 502. Transient'a çevir ki
            # call_with_chain exponential backoff ile yeniden denesin.
            status = getattr(exc, "code", None)
            if status == 429:
                raise ProviderTransientError(f"Gemini 429 (rate limit): {exc}") from exc
            raise ProviderError(f"Gemini istemci hatası: {exc}") from exc

        usage_meta = getattr(response, "usage_metadata", None)
        usage = TokenUsage(
            input_tokens=getattr(usage_meta, "prompt_token_count", 0) or 0,
            output_tokens=getattr(usage_meta, "candidates_token_count", 0) or 0,
            model_name=model_name,
        )

        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, schema):
            return ProviderResponse(
                parsed=parsed, model_name=model_name, provider="gemini", usage=usage,
            )
        text = getattr(response, "text", None)
        if not text:
            raise ProviderError("Gemini boş yanıt döndü.")
        try:
            return ProviderResponse(
                parsed=schema.model_validate_json(text),
                model_name=model_name,
                provider="gemini",
                raw_text=text,
                usage=usage,
            )
        except ValidationError as exc:
            raise ProviderError("Gemini çıktısı şemaya uymadı.") from exc


# ---- Anthropic ----


class AnthropicProvider:
    """Claude tool_use ile structured output. Gemini'nin response_schema'sının karşılığı."""

    def __init__(self, model: str | None = None) -> None:
        import anthropic
        if not settings.anthropic_api_key:
            raise ProviderError("ANTHROPIC_API_KEY boş.")
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = model or settings.anthropic_fallback_model

    @property
    def models(self) -> list[str]:
        return [self.model]

    def generate(
        self,
        system: str,
        prompt: str,
        schema: Type[T],
        temperature: float,
        model: str | None = None,
    ) -> ProviderResponse:
        import anthropic
        model_name = model or self.model

        # Pydantic schema → JSON Schema for tool_use
        json_schema = schema.model_json_schema()
        tool_def = {
            "name": "submit_response",
            "description": (
                "Üretilen sorular bu araç üzerinden teslim edilir. Tool çağrısının "
                "input'u doğrudan istenen JSON şemasıdır."
            ),
            "input_schema": json_schema,
        }

        try:
            response = self.client.messages.create(
                model=model_name,
                max_tokens=8192,
                system=system,
                temperature=temperature,
                tools=[tool_def],
                tool_choice={"type": "tool", "name": "submit_response"},
                messages=[{"role": "user", "content": prompt}],
            )
        except anthropic.APIStatusError as exc:
            status = getattr(exc, "status_code", None)
            if status in (500, 502, 503, 504, 529):  # 529 = overloaded
                raise ProviderTransientError(f"Anthropic {status}: {exc}") from exc
            if status == 429:
                raise ProviderTransientError(f"Anthropic rate limit: {exc}") from exc
            raise ProviderError(f"Anthropic API hatası: {exc}") from exc
        except anthropic.APIConnectionError as exc:
            raise ProviderTransientError(f"Anthropic bağlantı: {exc}") from exc

        # Tool use bloğunu bul
        tool_input = None
        for block in response.content:
            if getattr(block, "type", None) == "tool_use":
                tool_input = block.input
                break
        if tool_input is None:
            raise ProviderError("Anthropic tool_use bloğu döndürmedi.")

        usage_obj = getattr(response, "usage", None)
        usage = TokenUsage(
            input_tokens=getattr(usage_obj, "input_tokens", 0) or 0,
            output_tokens=getattr(usage_obj, "output_tokens", 0) or 0,
            model_name=model_name,
        )

        try:
            return ProviderResponse(
                parsed=schema.model_validate(tool_input),
                model_name=model_name,
                provider="anthropic",
                raw_text=json.dumps(tool_input, ensure_ascii=False),
                usage=usage,
            )
        except ValidationError as exc:
            raise ProviderError(f"Anthropic çıktısı şemaya uymadı: {exc}") from exc


# ---- Orchestrator ----


def call_with_chain(
    system: str,
    prompt: str,
    schema: Type[T],
    temperature: float,
    gemini: GeminiProvider | None,
    anthropic: AnthropicProvider | None,
    max_attempts_per_model: int = 3,
    base_delay: float = 1.5,
) -> ProviderResponse:
    """Provider chain ile çağrı: Gemini fallback chain → Anthropic.

    Her model için exponential backoff. Tüm Gemini modelleri tükendiğinde
    Anthropic'e geçer (varsa). Hiçbir provider çalışmazsa son hata fırlatılır.
    """
    last_error: Exception | None = None

    chain: list[tuple[str, str]] = []  # (provider_name, model_name)
    if gemini is not None:
        chain.extend(("gemini", m) for m in gemini.models)
    if anthropic is not None:
        chain.extend(("anthropic", m) for m in anthropic.models)
    if not chain:
        raise ProviderError("Hiçbir LLM provider yapılandırılmamış.")

    for provider_name, model_name in chain:
        for attempt in range(1, max_attempts_per_model + 1):
            try:
                if provider_name == "gemini" and gemini is not None:
                    return gemini.generate(system, prompt, schema, temperature, model=model_name)
                if provider_name == "anthropic" and anthropic is not None:
                    return anthropic.generate(system, prompt, schema, temperature, model=model_name)
            except ProviderTransientError as exc:
                last_error = exc
                if attempt == max_attempts_per_model:
                    logger.warning(
                        "%s/%s: %s deneme sonrası başarısız, bir sonraki modele geçiliyor.",
                        provider_name, model_name, max_attempts_per_model,
                    )
                    break
                delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
                logger.warning(
                    "%s/%s geçici hata: %s — %.1fs sonra tekrar (%s/%s)",
                    provider_name, model_name, exc, delay, attempt, max_attempts_per_model,
                )
                time.sleep(delay)
            except ProviderError as exc:
                # Kalıcı hata: bu modeli atla, sonrakine geç (tüm chain'i öldürme).
                last_error = exc
                logger.warning(
                    "%s/%s kalıcı hata, sonraki modele geçiliyor: %s",
                    provider_name, model_name, exc,
                )
                break
    raise ProviderError(f"Tüm provider chain tükendi. Son hata: {last_error}")
