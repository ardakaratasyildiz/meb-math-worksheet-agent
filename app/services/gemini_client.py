"""Ortak Gemini (google-genai) Client fabrikası.

Tek amaç: `settings.gemini_base_url` set ise trafiği temiz-IP'li bir proxy
(ör. Cloudflare Worker) üzerinden geçirmek. Render free-tier paylaşımlı çıkış
IP'si Google tarafından 403 ("from this server") ile bloklanınca kullanılır
(2026-07 incident). Boşsa doğrudan Google'a gider (bugünkü davranış).

Generation (llm_providers) ve embedding (embedder) aynı fabrikayı kullanır →
proxy tek env ile ikisini birden kapsar.
"""
from __future__ import annotations

from google import genai
from google.genai import types

from app.config import settings


def make_gemini_client(api_key: str) -> "genai.Client":
    """Yapılandırmaya göre doğrudan ya da proxy'li genai.Client döndürür."""
    base = settings.gemini_base_url.strip()
    if not base:
        return genai.Client(api_key=api_key)

    headers: dict[str, str] = {}
    secret = settings.gemini_proxy_secret.strip()
    if secret:
        headers["x-proxy-secret"] = secret
    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(base_url=base, headers=headers or None),
    )
