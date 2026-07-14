"""Haftalık çalışma programı kalıcılığı (WS-6a).

Öğrencinin oluşturduğu program tenant bazlı SAKLANIR → "Çalışma Programım" sekmesinde
her ziyarette hazır durur (İlerlemem gibi kalıcı). Kullanıcı "Yenile" derse yeni program
üretilip üzerine yazılır (tenant başına TEK, en güncel plan).

Tablo:
    study_plans → tenant_id (PK) × plan_json × created_at

Thread-safe (Lock + db_connection). Singleton: STUDY_PLAN_STORE.
"""
from __future__ import annotations

import logging
import threading
import time
from pathlib import Path

from app.config import settings
from app.services.db_connection import connect as db_connect

logger = logging.getLogger(__name__)


class StudyPlanStore:
    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path or settings.history_db_path
        self._lock = threading.Lock()
        self._db = None
        self._init_db()

    def _init_db(self) -> None:
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._db = db_connect(self._db_path)
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS study_plans (
                tenant_id TEXT PRIMARY KEY,
                plan_json TEXT NOT NULL,
                created_at REAL NOT NULL
            )
            """
        )
        self._db.commit()

    def save(self, tenant_id: str, plan_json: str) -> float:
        """Programı kaydeder/üzerine yazar; created_at (epoch) döner."""
        if not tenant_id:
            raise ValueError("tenant_id boş.")
        now = time.time()
        with self._lock:
            assert self._db is not None
            self._db.execute(
                "INSERT OR REPLACE INTO study_plans (tenant_id, plan_json, created_at) "
                "VALUES (?, ?, ?)",
                (tenant_id, plan_json, now),
            )
            self._db.commit()
        return now

    def get(self, tenant_id: str) -> tuple[str, float] | None:
        """Kayıtlı program (plan_json, created_at) ya da None."""
        if not tenant_id:
            return None
        with self._lock:
            assert self._db is not None
            row = self._db.execute(
                "SELECT plan_json, created_at FROM study_plans WHERE tenant_id = ?",
                (tenant_id,),
            ).fetchone()
        return (row[0], row[1]) if row else None

    def close(self) -> None:
        with self._lock:
            if self._db is not None:
                try:
                    self._db.close()
                except Exception as exc:  # noqa: BLE001
                    logger.warning("StudyPlanStore close hatası: %s", exc)
                self._db = None


STUDY_PLAN_STORE = StudyPlanStore()
