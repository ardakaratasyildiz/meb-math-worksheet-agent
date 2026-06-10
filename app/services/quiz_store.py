"""Çözülebilir quiz kalıcılığı (öğrenme döngüsü — Adım 1).

WORKSHEET_HISTORY ile aynı SQLite/Turso dosyasını paylaşır ama AYRI tablolar:
    quizzes        → üretilmiş çözülebilir quiz (sorular CEVAPLI saklanır; cevaplar
                     yalnız sunucuda kalır, /attempt puanlamasında kullanılır).
    attempts       → çözüm denemeleri (Adım 2'de yazılır).
    mastery_state  → kullanıcı × kazanım doğru oranı (Adım 2/3'te yazılır).

attempts/mastery_state tabloları bu PR'da OLUŞTURULUR (veri modeli) ama yalnız
quizzes CRUD implemente edilir; puanlama endpoint'leri Adım 2'de gelir.

Thread-safe (threading.Lock + db_connection deseni). Singleton: QUIZ_STORE.
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

# Tenant başına saklanacak azami quiz (FIFO trim). Worksheet geçmişiyle aynı sınır.
_DEFAULT_MAX_PER_TENANT = 200


class QuizStore:
    """SQLite/Turso tabanlı çözülebilir quiz deposu."""

    def __init__(self, db_path: str | None = None, max_per_tenant: int | None = None) -> None:
        self._db_path = db_path or settings.history_db_path
        self._max = max_per_tenant or getattr(
            settings, "quiz_max_per_tenant", _DEFAULT_MAX_PER_TENANT
        )
        self._lock = threading.Lock()
        self._db = None
        self._init_db()

    def _init_db(self) -> None:
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._db = db_connect(self._db_path)
        # quizzes — sorular CEVAPLI (full Question dump) saklanır.
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS quizzes (
                id TEXT PRIMARY KEY,
                owner_tenant_id TEXT NOT NULL,
                title TEXT NOT NULL,
                grade INTEGER NOT NULL,
                topic_id TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                questions_json TEXT NOT NULL,
                created_at REAL NOT NULL
            )
            """
        )
        self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_quizzes_owner_created "
            "ON quizzes(owner_tenant_id, created_at DESC)"
        )
        # attempts / mastery_state — veri modeli şimdi oluşur, kullanım Adım 2.
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS attempts (
                id TEXT PRIMARY KEY,
                quiz_id TEXT NOT NULL,
                solver_tenant_id TEXT NOT NULL,
                answers_json TEXT NOT NULL,
                score INTEGER NOT NULL,
                total INTEGER NOT NULL,
                duration_seconds INTEGER,
                per_kazanim_json TEXT,
                completed_at REAL NOT NULL
            )
            """
        )
        self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_attempts_solver "
            "ON attempts(solver_tenant_id, completed_at DESC)"
        )
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS mastery_state (
                tenant_id TEXT NOT NULL,
                kazanim_kod TEXT NOT NULL,
                correct INTEGER NOT NULL DEFAULT 0,
                total INTEGER NOT NULL DEFAULT 0,
                last_seen_at REAL NOT NULL,
                PRIMARY KEY (tenant_id, kazanim_kod)
            )
            """
        )
        self._db.commit()

    def create(
        self,
        *,
        owner_tenant_id: str,
        title: str,
        grade: int,
        topic_id: str,
        difficulty: str,
        questions: list[dict],
    ) -> dict:
        """Quiz'i kaydeder (sorular cevaplı). {id, created_at} döner.

        questions: her biri Question.model_dump() (answer + yapısal alanlar dahil).
        """
        quiz_id = uuid.uuid4().hex
        now = time.time()
        created_at = datetime.now(tz=timezone.utc).isoformat()
        payload = json.dumps(
            {"created_at": created_at, "questions": questions}, ensure_ascii=False
        )
        with self._lock:
            assert self._db is not None
            self._db.execute(
                "INSERT INTO quizzes (id, owner_tenant_id, title, grade, topic_id, "
                "difficulty, questions_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (quiz_id, owner_tenant_id, title, grade, topic_id, difficulty, payload, now),
            )
            # FIFO trim — tenant başına en fazla _max quiz.
            self._db.execute(
                """
                DELETE FROM quizzes
                WHERE owner_tenant_id = ?
                  AND id NOT IN (
                    SELECT id FROM quizzes
                    WHERE owner_tenant_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                  )
                """,
                (owner_tenant_id, owner_tenant_id, self._max),
            )
            self._db.commit()
        return {"id": quiz_id, "created_at": created_at}

    def get(self, quiz_id: str, owner_tenant_id: str) -> dict | None:
        """Quiz'i sahibine getirir (CEVAPLI tam kayıt). Sahip değilse None.

        Dönüş: {id, owner_tenant_id, title, grade, topic_id, difficulty,
                created_at, questions: [Question.model_dump(), ...]}
        Anti-kopya: cevap soyma çağıran (router) sorumluluğundadır.
        """
        if not quiz_id or not owner_tenant_id:
            return None
        with self._lock:
            assert self._db is not None
            row = self._db.execute(
                "SELECT id, owner_tenant_id, title, grade, topic_id, difficulty, "
                "questions_json FROM quizzes WHERE id = ? AND owner_tenant_id = ?",
                (quiz_id, owner_tenant_id),
            ).fetchone()
        if not row:
            return None
        try:
            body = json.loads(row[6])
        except json.JSONDecodeError:
            logger.error("quizzes kaydı bozuk JSON: id=%s", quiz_id)
            return None
        return {
            "id": row[0],
            "owner_tenant_id": row[1],
            "title": row[2],
            "grade": row[3],
            "topic_id": row[4],
            "difficulty": row[5],
            "created_at": body.get("created_at", ""),
            "questions": body.get("questions", []),
        }

    def close(self) -> None:
        """Bağlantıyı kapatır (test temizliği / graceful shutdown)."""
        with self._lock:
            if self._db is not None:
                try:
                    self._db.close()
                except Exception as exc:  # noqa: BLE001
                    logger.warning("QuizStore close hatası: %s", exc)
                self._db = None

    def list(self, owner_tenant_id: str, limit: int | None = None) -> list[dict]:
        """Sahibinin quiz'leri — en yeni önce, hafif meta (sorular hariç)."""
        if not owner_tenant_id:
            return []
        lim = self._max if limit is None else max(1, min(self._max, limit))
        with self._lock:
            assert self._db is not None
            rows = self._db.execute(
                "SELECT id, title, grade, topic_id, difficulty, created_at "
                "FROM quizzes WHERE owner_tenant_id = ? ORDER BY created_at DESC LIMIT ?",
                (owner_tenant_id, lim),
            ).fetchall()
        return [
            {
                "id": r[0],
                "title": r[1],
                "grade": r[2],
                "topic_id": r[3],
                "difficulty": r[4],
                "created_at": datetime.fromtimestamp(r[5], tz=timezone.utc).isoformat(),
            }
            for r in rows
        ]


QUIZ_STORE = QuizStore()
