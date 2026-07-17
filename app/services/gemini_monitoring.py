"""Cloud Monitoring maliyet mutabakatı — Google'ın KENDİ token sayaçları.

usage_ledger bir TAHMİN'dir (yalnız worksheet+quiz üretimi, token×bizim-fiyat) ve
faturanın altında kalır: offline embedding (RAG/ingest), başarısız çağrı token'ları
ve fiyat farkı defterde yoktur. Bu modül, `generativelanguage.googleapis.com` metrik-
lerini SA (roles/monitoring.viewer) ile okuyarak GERÇEK kullanımı verir → panelde
"defter (tahmin)" vs "Google gerçek" mutabakatı.

Best-effort: SA yapılandırılmadıysa/çağrı hata verirse {"available": False, ...} döner
(panel yalnız defteri gösterir). Sonuç 10 dk cache'lenir (Monitoring çağrısı ~1-2s +
kota). Kaynak: PR ile eklendi (2026-07).
"""
from __future__ import annotations

import json
import logging
import threading
import time
from datetime import datetime, timedelta, timezone

from app.config import settings
from app.services.llm_providers import PRICING_USD_PER_1M_TOKENS

logger = logging.getLogger(__name__)

_SCOPE = "https://www.googleapis.com/auth/monitoring.read"
_BASE = "generativelanguage.googleapis.com"
_EMBED_PRICE_PER_1M = 0.15  # gemini-embedding girdi; çıktı yok
_CACHE_TTL = 600  # 10 dk
_cache: dict[int, tuple[float, dict]] = {}
_lock = threading.Lock()


def _load_sa() -> tuple[object, str] | None:
    """SA credentials + project_id. Config'ten (JSON env veya dosya). Yoksa None."""
    raw = (settings.gemini_monitoring_sa_json or "").strip()
    info: dict | None = None
    if raw:
        info = json.loads(raw)
    else:
        path = (settings.gemini_monitoring_sa_file or "").strip()
        if path:
            with open(path, encoding="utf-8") as f:
                info = json.load(f)
    if not info:
        return None
    from google.oauth2 import service_account

    creds = service_account.Credentials.from_service_account_info(info, scopes=[_SCOPE])
    return creds, info.get("project_id", "")


def _access_token(creds) -> str:
    import google.auth.transport.requests

    creds.refresh(google.auth.transport.requests.Request())
    return creds.token


def _query(project: str, token: str, metric: str, group_fields: list[str], days: int) -> list[dict]:
    import requests

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    params: list[tuple[str, str]] = [
        ("filter", f'metric.type="{_BASE}/{metric}"'),
        ("interval.startTime", start.strftime("%Y-%m-%dT%H:%M:%SZ")),
        ("interval.endTime", end.strftime("%Y-%m-%dT%H:%M:%SZ")),
        ("aggregation.alignmentPeriod", f"{days * 86400}s"),
        ("aggregation.perSeriesAligner", "ALIGN_SUM"),
    ]
    for g in group_fields:
        params.append(("aggregation.groupByFields", g))
    if group_fields:
        params.append(("aggregation.crossSeriesReducer", "REDUCE_SUM"))
    resp = requests.get(
        f"https://monitoring.googleapis.com/v3/projects/{project}/timeSeries",
        params=params,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("timeSeries", [])


def _sum_by_model(series: list[dict]) -> dict[str, int]:
    out: dict[str, int] = {}
    for s in series:
        model = s.get("metric", {}).get("labels", {}).get("model", "?")
        tot = 0
        for p in s.get("points", []):
            v = p.get("value", {})
            tot += int(v.get("int64Value") or v.get("doubleValue") or 0)
        out[model] = out.get(model, 0) + tot
    return out


def _sum_all(series: list[dict]) -> int:
    tot = 0
    for s in series:
        for p in s.get("points", []):
            v = p.get("value", {})
            tot += int(v.get("int64Value") or v.get("doubleValue") or 0)
    return tot


def _compute(days: int) -> dict:
    loaded = _load_sa()
    if loaded is None:
        return {"available": False, "reason": "Monitoring SA yapılandırılmadı."}
    creds, project = loaded
    if not project:
        return {"available": False, "reason": "SA project_id yok."}
    token = _access_token(creds)

    out_tok = _sum_by_model(
        _query(project, token, "generate_content_usage_output_token_count", ["metric.label.model"], days)
    )
    in_tok = _sum_by_model(
        _query(project, token, "quota/generate_content_paid_tier_input_token_count/usage", ["metric.label.model"], days)
    )
    embed_tok = _sum_all(
        _query(project, token, "quota/embed_content_paid_tier_tokens/usage", [], days)
    )

    by_model = []
    gen_cost = 0.0
    for model in sorted(set(out_tok) | set(in_tok)):
        i, o = in_tok.get(model, 0), out_tok.get(model, 0)
        price = PRICING_USD_PER_1M_TOKENS.get(model)
        cost = ((i * price[0] + o * price[1]) / 1_000_000) if price else 0.0
        gen_cost += cost
        by_model.append(
            {"model": model, "prompt_tokens": i, "completion_tokens": o, "cost_usd": round(cost, 6)}
        )
    embed_cost = embed_tok * _EMBED_PRICE_PER_1M / 1_000_000
    total = gen_cost + embed_cost
    return {
        "available": True,
        "source": "cloud_monitoring",
        "window_days": days,
        "project_id": project,
        "by_model": by_model,
        "embedding": {"tokens": embed_tok, "cost_usd": round(embed_cost, 6)},
        "generation_cost_usd": round(gen_cost, 6),
        "total_cost_usd": round(total, 6),
    }


def get_cost_summary(days: int = 7) -> dict:
    """Google gerçek kullanım maliyeti (Monitoring). 10 dk cache'li, best-effort."""
    days = max(1, min(30, days))
    with _lock:
        hit = _cache.get(days)
        if hit and time.time() - hit[0] < _CACHE_TTL:
            return hit[1]
    try:
        data = _compute(days)
    except Exception as exc:  # noqa: BLE001 — mutabakat paneli üretimi/analizi bozmasın
        logger.warning("gemini_monitoring başarısız: %s", exc)
        return {"available": False, "reason": f"Monitoring hatası: {type(exc).__name__}"}
    with _lock:
        _cache[days] = (time.time(), data)
    return data
