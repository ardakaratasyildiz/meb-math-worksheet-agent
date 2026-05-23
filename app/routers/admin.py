"""Admin endpoint'leri — cache içeriğini, üretim geçmişini, kullanıcı bazlı
gördüğü soruları görüntüleme. ADMIN_API_KEY env'i ile korunur (boşsa devre dışı).

İki tür çağrı şekli destekler:
1. Doğrudan curl (incident debug): `-H "X-Admin-Key: <key>"`. Actor=None
   (anonymous admin), audit kaydında sadece IP görünür.
2. Next.js server proxy (UI): aynı X-Admin-Key + ek `X-Admin-Actor: <clerk_user_id>`
   header'ı. Audit'te kim baktığı net.

Kullanım (curl):
    H="X-Admin-Key: <senin admin key>"
    curl -H "$H" https://<host>/admin/cache/stats
    curl -H "$H" https://<host>/admin/cache/recent
    curl -H "$H" https://<host>/admin/history/<tenant_id>
"""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.config import settings
from app.services.admin_audit import ADMIN_AUDIT
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


def get_admin_actor(
    request: Request,
    x_admin_actor: str | None = Header(default=None, alias="X-Admin-Actor"),
) -> dict[str, str | None]:
    """Audit için aktör + IP bilgisi.

    Next.js server proxy `X-Admin-Actor` header'ında Clerk user ID gönderir.
    Doğrudan curl kullanıldıysa actor=None (anonymous admin via key).
    IP, Render proxy arkasında olduğu için önce X-Forwarded-For'dan alınır.
    """
    ip: str | None = None
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # İlk IP gerçek client; sonrakiler proxy zincirinden gelir.
        ip = forwarded.split(",")[0].strip()
    elif request.client:
        ip = request.client.host
    return {"actor": x_admin_actor, "ip": ip}


@router.get("/cache/stats", dependencies=[Depends(require_admin_key)])
def cache_stats(actor: dict = Depends(get_admin_actor)) -> dict[str, Any]:
    """Cache özet istatistiği: toplam set, distinct key, runtime hit/miss sayacı."""
    ADMIN_AUDIT.record(action="cache_stats", clerk_user_id=actor["actor"], ip=actor["ip"])
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
def cache_recent(limit: int = 20, actor: dict = Depends(get_admin_actor)) -> dict[str, Any]:
    """Son N üretim seti — key + ilk sorunun başlangıcı + soru sayısı + zamanı."""
    ADMIN_AUDIT.record(
        action="cache_recent", clerk_user_id=actor["actor"], target=str(limit), ip=actor["ip"]
    )
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


@router.get("/history/_summary", dependencies=[Depends(require_admin_key)])
def history_summary(actor: dict = Depends(get_admin_actor)) -> dict[str, Any]:
    """Tüm tenant'ların özet — kim ne kadar soru görmüş.

    Not: /history/{tenant_id} route'undan önce tanımlanmalı, yoksa FastAPI
    "_summary" stringini tenant_id olarak yakalar.
    """
    ADMIN_AUDIT.record(action="history_summary", clerk_user_id=actor["actor"], ip=actor["ip"])
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


@router.get("/history/{tenant_id}", dependencies=[Depends(require_admin_key)])
def tenant_history(
    tenant_id: str,
    limit: int = 100,
    actor: dict = Depends(get_admin_actor),
) -> dict[str, Any]:
    """Belirli bir tenant_id'nin gördüğü tüm soruları listeler — kullanıcı bazlı izleme.

    Bu endpoint başkasının verisini gösterir → audit log'da target=tenant_id
    yazılır. KVKK incelemesinde kanıt: hangi admin kimi izlemiş.
    """
    ADMIN_AUDIT.record(
        action="view_tenant_history",
        clerk_user_id=actor["actor"],
        target=tenant_id,
        ip=actor["ip"],
    )
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


@router.get("/worksheet-history/_summary", dependencies=[Depends(require_admin_key)])
def worksheet_history_summary(actor: dict = Depends(get_admin_actor)) -> dict[str, Any]:
    """Sprint 13: Tenant bazlı üretilmiş PDF sayımı + son üretim zamanı.

    /admin/history/_summary "soru gördü" sayar (her PDF'te 5–10 soru);
    bu ise "PDF/kağıt" sayar — farklı metrik. UI'da ikisi yan yana durur.
    """
    ADMIN_AUDIT.record(
        action="worksheet_summary", clerk_user_id=actor["actor"], ip=actor["ip"]
    )
    conn = db_connect(settings.history_db_path)
    try:
        rows = conn.execute(
            "SELECT tenant_id, COUNT(*) as n, MAX(created_at) as last_at "
            "FROM worksheet_history GROUP BY tenant_id ORDER BY n DESC"
        ).fetchall()
    finally:
        conn.close()
    return {
        "tenant_count": len(rows),
        "tenants": [
            {"tenant_id": t, "worksheet_count": n, "last_at": last_at}
            for t, n, last_at in rows
        ],
    }


@router.get("/audit", dependencies=[Depends(require_admin_key)])
def audit_log(
    limit: int = 100,
    actor: dict = Depends(get_admin_actor),
) -> dict[str, Any]:
    """Son N admin erişim kaydı — meta-audit (audit'i görüntülemek de audit'lenir)."""
    ADMIN_AUDIT.record(
        action="audit_view",
        clerk_user_id=actor["actor"],
        target=str(limit),
        ip=actor["ip"],
    )
    items = ADMIN_AUDIT.recent(limit=limit)
    return {"count": len(items), "items": items}
