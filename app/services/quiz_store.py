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
        # Migration: quiz bağlam snapshot'ı (geçmiş, quiz FIFO-trim'lense bile
        # bozulmasın). Idempotent — sütun yoksa eklenir.
        cols = {
            r[1]
            for r in self._db.execute("PRAGMA table_info(attempts)").fetchall()
        }
        if "quiz_snapshot_json" not in cols:
            self._db.execute(
                "ALTER TABLE attempts ADD COLUMN quiz_snapshot_json TEXT"
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

    # ── Attempts + mastery (Adım 2) ──────────────────────────────────────────

    def record_attempt(
        self,
        *,
        quiz_id: str,
        solver_tenant_id: str,
        answers: list[dict],
        score: int,
        total: int,
        duration_seconds: int | None,
        per_kazanim: list[dict],
        quiz_snapshot: dict | None = None,
    ) -> dict:
        """Çözüm denemesini kaydeder. {id, completed_at} döner.

        quiz_snapshot: {title, grade, topic_id, difficulty, questions:[...]} —
        denemeyi self-contained yapar; quiz FIFO-trim'lense bile geçmiş çalışır.
        """
        attempt_id = uuid.uuid4().hex
        now = time.time()
        completed_at = datetime.now(tz=timezone.utc).isoformat()
        snapshot_json = (
            json.dumps(quiz_snapshot, ensure_ascii=False)
            if quiz_snapshot is not None
            else None
        )
        with self._lock:
            assert self._db is not None
            self._db.execute(
                "INSERT INTO attempts (id, quiz_id, solver_tenant_id, answers_json, "
                "score, total, duration_seconds, per_kazanim_json, completed_at, "
                "quiz_snapshot_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    attempt_id,
                    quiz_id,
                    solver_tenant_id,
                    json.dumps(answers, ensure_ascii=False),
                    score,
                    total,
                    duration_seconds,
                    json.dumps(per_kazanim, ensure_ascii=False),
                    now,
                    snapshot_json,
                ),
            )
            # FIFO trim — snapshot satırları büyüttüğü için attempts de sınırlanır.
            self._db.execute(
                """
                DELETE FROM attempts
                WHERE solver_tenant_id = ?
                  AND id NOT IN (
                    SELECT id FROM attempts
                    WHERE solver_tenant_id = ?
                    ORDER BY completed_at DESC
                    LIMIT ?
                  )
                """,
                (solver_tenant_id, solver_tenant_id, self._max),
            )
            self._db.commit()
        return {"id": attempt_id, "completed_at": completed_at}

    def list_attempts(self, solver_tenant_id: str, limit: int = 50) -> list[dict]:
        """Kullanıcının çözüm denemeleri — en yeni önce (quiz geçmişi listesi).

        Meta snapshot'tan okunur; eski (snapshot'sız) kayıtlar için quizzes'e
        LEFT JOIN ile geri düşülür. has_detail = soru detayı reconstruct edilebilir mi.
        """
        if not solver_tenant_id:
            return []
        lim = max(1, min(self._max, limit))
        with self._lock:
            assert self._db is not None
            rows = self._db.execute(
                """
                SELECT a.id, a.quiz_id, a.score, a.total, a.completed_at,
                       a.quiz_snapshot_json,
                       q.title, q.grade, q.topic_id, q.difficulty
                FROM attempts a
                LEFT JOIN quizzes q
                       ON q.id = a.quiz_id AND q.owner_tenant_id = a.solver_tenant_id
                WHERE a.solver_tenant_id = ?
                ORDER BY a.completed_at DESC
                LIMIT ?
                """,
                (solver_tenant_id, lim),
            ).fetchall()
        out: list[dict] = []
        for r in rows:
            snap = None
            if r[5]:
                try:
                    snap = json.loads(r[5])
                except json.JSONDecodeError:
                    snap = None
            has_quiz = r[6] is not None
            has_detail = snap is not None or has_quiz
            out.append(
                {
                    "attempt_id": r[0],
                    "quiz_id": r[1],
                    "title": (snap or {}).get("title") or r[6] or "Quiz",
                    "grade": (snap or {}).get("grade") if snap else r[7],
                    "topic_id": (snap or {}).get("topic_id") or r[8] or "",
                    "difficulty": (snap or {}).get("difficulty") or r[9] or "orta",
                    "score": r[2],
                    "total": r[3],
                    "completed_at": datetime.fromtimestamp(
                        r[4], tz=timezone.utc
                    ).isoformat(),
                    "has_detail": has_detail,
                }
            )
        return out

    def get_attempt(self, attempt_id: str, solver_tenant_id: str) -> dict | None:
        """Tek denemeyi sahibine getirir (cevaplar + quiz snapshot). Sahip değilse None.

        snapshot None ise (eski kayıt) quizzes'ten best-effort doldurulur.
        """
        if not attempt_id or not solver_tenant_id:
            return None
        with self._lock:
            assert self._db is not None
            row = self._db.execute(
                "SELECT id, quiz_id, score, total, duration_seconds, completed_at, "
                "answers_json, quiz_snapshot_json FROM attempts "
                "WHERE id = ? AND solver_tenant_id = ?",
                (attempt_id, solver_tenant_id),
            ).fetchone()
        if not row:
            return None
        try:
            answers = json.loads(row[6]) if row[6] else []
        except json.JSONDecodeError:
            answers = []
        snapshot = None
        if row[7]:
            try:
                snapshot = json.loads(row[7])
            except json.JSONDecodeError:
                snapshot = None
        if snapshot is None:
            # Eski kayıt: quiz hâlâ duruyorsa oradan reconstruct et.
            quiz = self.get(row[1], solver_tenant_id)
            if quiz is not None:
                snapshot = {
                    "title": quiz["title"],
                    "grade": quiz["grade"],
                    "topic_id": quiz["topic_id"],
                    "difficulty": quiz["difficulty"],
                    "questions": quiz["questions"],
                }
        return {
            "attempt_id": row[0],
            "quiz_id": row[1],
            "score": row[2],
            "total": row[3],
            "duration_seconds": row[4],
            "completed_at": datetime.fromtimestamp(row[5], tz=timezone.utc).isoformat(),
            "answers": answers,
            "snapshot": snapshot,
        }

    def update_mastery(self, tenant_id: str, per_kazanim: list[dict]) -> None:
        """Kazanım-bazlı doğru/toplam sayaçlarını kümülatif günceller (UPSERT)."""
        if not tenant_id or not per_kazanim:
            return
        now = time.time()
        with self._lock:
            assert self._db is not None
            for item in per_kazanim:
                kod = item.get("kazanim_kod")
                if not kod:
                    continue
                self._db.execute(
                    """
                    INSERT INTO mastery_state (tenant_id, kazanim_kod, correct, total, last_seen_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(tenant_id, kazanim_kod) DO UPDATE SET
                        correct = correct + excluded.correct,
                        total   = total   + excluded.total,
                        last_seen_at = excluded.last_seen_at
                    """,
                    (tenant_id, kod, int(item.get("correct", 0)), int(item.get("total", 0)), now),
                )
            self._db.commit()

    def count_attempts(self, tenant_id: str) -> int:
        """Kullanıcının toplam çözüm denemesi sayısı (ilerleme özeti)."""
        if not tenant_id:
            return 0
        with self._lock:
            assert self._db is not None
            row = self._db.execute(
                "SELECT COUNT(*) FROM attempts WHERE solver_tenant_id = ?",
                (tenant_id,),
            ).fetchone()
        return int(row[0]) if row else 0

    def recent_attempts(self, tenant_id: str, limit: int = 10) -> list[dict]:
        """Son N çözüm denemesi — eski→yeni sırada (trend grafiği için)."""
        if not tenant_id:
            return []
        lim = max(1, min(50, limit))
        with self._lock:
            assert self._db is not None
            rows = self._db.execute(
                "SELECT score, total, completed_at FROM attempts "
                "WHERE solver_tenant_id = ? ORDER BY completed_at DESC LIMIT ?",
                (tenant_id, lim),
            ).fetchall()
        # DESC çekildi → eski→yeni için ters çevir.
        out = [
            {
                "score": r[0],
                "total": r[1],
                "completed_at": datetime.fromtimestamp(r[2], tz=timezone.utc).isoformat(),
            }
            for r in rows
        ]
        out.reverse()
        return out

    def attempts_since(self, tenant_id: str, since_epoch: float) -> list[dict]:
        """Belirli epoch'tan sonraki denemeler — eski→yeni (30 günlük trend için)."""
        if not tenant_id:
            return []
        with self._lock:
            assert self._db is not None
            rows = self._db.execute(
                "SELECT score, total, completed_at FROM attempts "
                "WHERE solver_tenant_id = ? AND completed_at >= ? "
                "ORDER BY completed_at ASC",
                (tenant_id, since_epoch),
            ).fetchall()
        return [
            {
                "score": r[0],
                "total": r[1],
                "completed_at": datetime.fromtimestamp(r[2], tz=timezone.utc).isoformat(),
            }
            for r in rows
        ]

    def get_mastery(self, tenant_id: str) -> list[dict]:
        """Kullanıcının kazanım-bazlı ustalık durumu (Adım 3 ilerleme panosu)."""
        if not tenant_id:
            return []
        with self._lock:
            assert self._db is not None
            rows = self._db.execute(
                "SELECT kazanim_kod, correct, total, last_seen_at FROM mastery_state "
                "WHERE tenant_id = ? ORDER BY kazanim_kod",
                (tenant_id,),
            ).fetchall()
        return [
            {
                "kazanim_kod": r[0],
                "correct": r[1],
                "total": r[2],
                "last_seen_at": datetime.fromtimestamp(r[3], tz=timezone.utc).isoformat(),
            }
            for r in rows
        ]

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
