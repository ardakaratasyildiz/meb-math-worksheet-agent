"""Kullanıcı (tenant) bazlı üretilmiş çalışma kağıdı geçmişi.

Bu modül GENERATION_HISTORY ve GENERATION_CACHE'ten farklı bir amaca hizmet eder:
    - GENERATION_HISTORY → tekrar-önleme (yalnızca normalize soru metni tutar).
    - GENERATION_CACHE   → parametre-bazlı paylaşımlı havuz (kullanıcıdan bağımsız).
    - WORKSHEET_HISTORY  → kullanıcının KENDİ ürettiği kağıtları gösterim için
      saklar: başlık, tarih, tam worksheet + metadata, "yeniden üret" parametreleri.

Saklanan kayıt frontend'in `HistoryItem` arayüzüyle birebir aynı şekildedir
(`{id, saved_at, request, response}`) — frontend ek dönüşüm yapmadan kullanır.

SQLite/Turso tablosu (`history.sqlite3` ile aynı dosya). Tenant başına en fazla
`max_per_tenant` kayıt; aşılırsa en eski FIFO ile silinir.
"""
from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings
from app.services.db_connection import connect as db_connect

logger = logging.getLogger(__name__)


class WorksheetHistory:
    """Thread-safe, SQLite/Turso tabanlı kullanıcı kağıt geçmişi. Singleton: `WORKSHEET_HISTORY`."""

    def __init__(self, db_path: str | None = None, max_per_tenant: int | None = None) -> None:
        self._db_path = db_path or settings.history_db_path
        self._max = max_per_tenant or settings.worksheet_history_max_per_tenant
        self._lock = threading.Lock()
        self._db = None
        self._init_db()

    def _init_db(self) -> None:
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._db = db_connect(self._db_path)
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS worksheet_history (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                item_json TEXT NOT NULL,
                created_at REAL NOT NULL
            )
            """
        )
        self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_wh_tenant_created "
            "ON worksheet_history(tenant_id, created_at DESC)"
        )
        self._db.commit()

    def add(self, tenant_id: str, request: dict, response: dict) -> dict | None:
        """Yeni kağıdı kullanıcının geçmişine ekler; saklanan HistoryItem'ı döner.

        tenant_id boşsa (giriş yapmamış kullanıcı) hiçbir şey yapmaz, None döner.
        """
        if not tenant_id:
            return None
        item = {
            "id": uuid.uuid4().hex,
            "saved_at": datetime.now(tz=timezone.utc).isoformat(),
            "request": request,
            "response": response,
        }
        payload = json.dumps(item, ensure_ascii=False)
        now = time.time()
        with self._lock:
            assert self._db is not None
            self._db.execute(
                "INSERT INTO worksheet_history (id, tenant_id, item_json, created_at) "
                "VALUES (?, ?, ?, ?)",
                (item["id"], tenant_id, payload, now),
            )
            # FIFO trim — tenant başına en fazla _max kayıt tut.
            self._db.execute(
                """
                DELETE FROM worksheet_history
                WHERE tenant_id = ?
                  AND id NOT IN (
                    SELECT id FROM worksheet_history
                    WHERE tenant_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                  )
                """,
                (tenant_id, tenant_id, self._max),
            )
            self._db.commit()
        return item

    def list(self, tenant_id: str, limit: int | None = None) -> list[dict]:
        """Kullanıcının kağıtları — en yeni önce. tenant_id boşsa boş liste."""
        if not tenant_id:
            return []
        lim = self._max if limit is None else max(1, min(self._max, limit))
        with self._lock:
            assert self._db is not None
            rows = self._db.execute(
                "SELECT item_json FROM worksheet_history WHERE tenant_id = ? "
                "ORDER BY created_at DESC LIMIT ?",
                (tenant_id, lim),
            ).fetchall()
        items: list[dict] = []
        for (item_json,) in rows:
            try:
                items.append(json.loads(item_json))
            except json.JSONDecodeError:
                continue
        return items

    def delete(self, tenant_id: str, item_id: str) -> None:
        """Tek bir kaydı siler. tenant_id filtresi → başkasının kaydı silinemez."""
        if not tenant_id or not item_id:
            return
        with self._lock:
            assert self._db is not None
            self._db.execute(
                "DELETE FROM worksheet_history WHERE tenant_id = ? AND id = ?",
                (tenant_id, item_id),
            )
            self._db.commit()

    def clear(self, tenant_id: str) -> None:
        """Kullanıcının tüm geçmişini siler."""
        if not tenant_id:
            return
        with self._lock:
            assert self._db is not None
            self._db.execute(
                "DELETE FROM worksheet_history WHERE tenant_id = ?",
                (tenant_id,),
            )
            self._db.commit()


WORKSHEET_HISTORY = WorksheetHistory()
