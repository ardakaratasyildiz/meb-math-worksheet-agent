"""Admin endpoint'leri — cache içeriğini, üretim geçmişini, kullanıcı bazlı
gördüğü soruları görüntüleme. ADMIN_API_KEY env'i ile korunur (boşsa devre dışı).

Kullanım (curl):
    H="X-Admin-Key: <senin admin key>"
    curl -H "$H" https://<host>/admin/cache/stats
    curl -H "$H" https://<host>/admin/cache/recent
    curl -H "$H" https://<host>/admin/history/<tenant_id>
"""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException

from app.config import settings
from app.services.db_connection import connect as db_connect
from app.services.history import GENERATION_HISTORY
from app.services.llm_cache import GENERATION_CACHE

router = APIRouter()


async def require_admin_key(
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> None:
    if not settings.admin_api_key:
        raise HTTPException(status_code=503, detail="Admin endpoints devre dışı (ADMIN_API_KEY set değil).")
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Geçersiz admin key.")


@router.get("/cache/stats", dependencies=[Depends(require_admin_key)])
def cache_stats() -> dict[str, Any]:
    """Cache özet istatistiği: toplam set, distinct key, runtime hit/miss sayacı."""
    base = GENERATION_CACHE.stats()
    # Key bazlı dağılım — en yoğun 20 key'i listele
    conn = db_connect(settings.history_db_path)
    try:
        rows = conn.execute(
            "SELECT cache_key, COUNT(*) as n FROM generation_cache "
            "GROUP BY cache_key ORDER BY n DESC LIMIT 20"
        ).fetchall()
    finally:
        conn.close()
    return {
        **base,
        "top_keys": [{"key": k, "set_count": n} for k, n in rows],
    }


@router.get("/cache/recent", dependencies=[Depends(require_admin_key)])
def cache_recent(limit: int = 20) -> dict[str, Any]:
    """Son N üretim seti — key + ilk sorunun başlangıcı + soru sayısı + zamanı."""
    limit = max(1, min(200, limit))
    conn = db_connect(settings.history_db_path)
    try:
        rows = conn.execute(
            "SELECT cache_key, questions_json, created_at FROM generation_cache "
            "ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    finally:
        conn.close()
    out = []
    for cache_key, questions_json, created_at in rows:
        try:
            qs = json.loads(questions_json)
        except json.JSONDecodeError:
            continue
        first = qs[0] if qs else {}
        out.append({
            "cache_key": cache_key,
            "question_count": len(qs),
            "created_at": created_at,
            "first_question_preview": (first.get("question", "") or "")[:120],
            "first_answer_preview": (first.get("answer", "") or "")[:80],
        })
    return {"count": len(out), "items": out}


@router.get("/history/{tenant_id}", dependencies=[Depends(require_admin_key)])
def tenant_history(tenant_id: str, limit: int = 100) -> dict[str, Any]:
    """Belirli bir tenant_id'nin gördüğü tüm soruları listeler — kullanıcı bazlı izleme."""
    limit = max(1, min(500, limit))
    # GENERATION_HISTORY import'u modül init'ini garantiliyor (tablo create).
    _ = GENERATION_HISTORY
    conn = db_connect(settings.history_db_path)
    try:
        rows = conn.execute(
            "SELECT key, normalized_question, contexts FROM history "
            "WHERE key LIKE ? ORDER BY rowid DESC LIMIT ?",
            (f"{tenant_id}|%", limit),
        ).fetchall()
    finally:
        conn.close()
    items = []
    for key, normalized, contexts in rows:
        items.append({
            "key": key,
            "normalized_question": normalized,
            "contexts": contexts.split(",") if contexts else [],
        })
    return {"tenant_id": tenant_id, "count": len(items), "items": items}


@router.get("/history/_summary", dependencies=[Depends(require_admin_key)])
def history_summary() -> dict[str, Any]:
    """Tüm tenant'ların özet — kim ne kadar soru görmüş."""
    conn = db_connect(settings.history_db_path)
    try:
        rows = conn.execute(
            """
            SELECT
                substr(key, 1, instr(key, '|') - 1) AS tenant_id,
                COUNT(*) AS question_count
            FROM history
            GROUP BY tenant_id
            ORDER BY question_count DESC
            """
        ).fetchall()
    finally:
        conn.close()
    return {
        "tenant_count": len(rows),
        "tenants": [{"tenant_id": t, "question_count": n} for t, n in rows],
    }
