"""Veli ↔ öğrenci bağı (WS-6b).

Öğrenci bir "veli takip kodu" üretir (kalıcı, tekrar kullanılabilir); veli bu kodu
girerek öğrencinin ilerlemesini SALT-OKUNUR takip eder. Sınıf katılma-kodu deseniyle
aynı (okunabilir alfabe, çakışmasız kod). Tenant-bazlı; Clerk rolünden bağımsız.

Tablolar:
    parent_codes  → öğrenci × kod (öğrenci başına tek kod)
    parent_links  → veli × öğrenci (çözülmüş bağ; salt-okunur erişim yetkisi)

Thread-safe (Lock + db_connection). Singleton: PARENT_LINK_STORE.
"""
from __future__ import annotations

import logging
import secrets
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings
from app.services.db_connection import connect as db_connect

logger = logging.getLogger(__name__)

_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
_CODE_LEN = 6
_MAX_CODE_TRIES = 12


def _iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()


class ParentLinkStore:
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
            CREATE TABLE IF NOT EXISTS parent_codes (
                student_tenant_id TEXT PRIMARY KEY,
                code TEXT NOT NULL UNIQUE,
                created_at REAL NOT NULL
            )
            """
        )
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS parent_links (
                parent_tenant_id TEXT NOT NULL,
                student_tenant_id TEXT NOT NULL,
                child_label TEXT,
                linked_at REAL NOT NULL,
                PRIMARY KEY (parent_tenant_id, student_tenant_id)
            )
            """
        )
        self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_parent_links_parent "
            "ON parent_links(parent_tenant_id, linked_at DESC)"
        )
        # Ters arama (öğrenci → veli): aile paylaşımlı-kota + entitlement mirası için.
        self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_parent_links_student "
            "ON parent_links(student_tenant_id)"
        )
        self._db.commit()

    def _gen_unique_code(self) -> str:
        assert self._db is not None
        for _ in range(_MAX_CODE_TRIES):
            code = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_LEN))
            if not self._db.execute(
                "SELECT 1 FROM parent_codes WHERE code = ?", (code,)
            ).fetchone():
                return code
        raise RuntimeError("Benzersiz veli kodu üretilemedi.")

    def get_or_create_code(self, student_tenant_id: str) -> str:
        """Öğrencinin veli takip kodu (yoksa üretilir, kalıcı)."""
        if not student_tenant_id:
            raise ValueError("student_tenant_id boş.")
        with self._lock:
            assert self._db is not None
            row = self._db.execute(
                "SELECT code FROM parent_codes WHERE student_tenant_id = ?",
                (student_tenant_id,),
            ).fetchone()
            if row:
                return row[0]
            code = self._gen_unique_code()
            self._db.execute(
                "INSERT INTO parent_codes (student_tenant_id, code, created_at) "
                "VALUES (?, ?, ?)",
                (student_tenant_id, code, time.time()),
            )
            self._db.commit()
            return code

    def link(self, parent_tenant_id: str, code: str, child_label: str | None = None) -> str | None:
        """Veli, kodu girerek öğrenciye bağlanır. Öğrenci tenant_id döner; kod geçersiz
        ya da veli kendi kodunu girdiyse None."""
        code = (code or "").strip().upper()
        if not parent_tenant_id or not code:
            return None
        with self._lock:
            assert self._db is not None
            row = self._db.execute(
                "SELECT student_tenant_id FROM parent_codes WHERE code = ?", (code,)
            ).fetchone()
            if not row:
                return None
            student = row[0]
            if student == parent_tenant_id:
                return None  # kendine bağlanamaz
            self._db.execute(
                "INSERT OR REPLACE INTO parent_links "
                "(parent_tenant_id, student_tenant_id, child_label, linked_at) "
                "VALUES (?, ?, ?, ?)",
                (parent_tenant_id, student, (child_label or "").strip() or None, time.time()),
            )
            self._db.commit()
            return student

    def is_linked(self, parent_tenant_id: str, student_tenant_id: str) -> bool:
        """Veli bu öğrenciye bağlı mı (yetki kontrolü)."""
        if not parent_tenant_id or not student_tenant_id:
            return False
        with self._lock:
            assert self._db is not None
            return self._db.execute(
                "SELECT 1 FROM parent_links WHERE parent_tenant_id = ? AND student_tenant_id = ?",
                (parent_tenant_id, student_tenant_id),
            ).fetchone() is not None

    def list_children(self, parent_tenant_id: str) -> list[dict]:
        """Velinin bağlı olduğu öğrenciler (en yeni önce)."""
        if not parent_tenant_id:
            return []
        with self._lock:
            assert self._db is not None
            rows = self._db.execute(
                "SELECT student_tenant_id, child_label, linked_at FROM parent_links "
                "WHERE parent_tenant_id = ? ORDER BY linked_at DESC",
                (parent_tenant_id,),
            ).fetchall()
        return [
            {"student_id": r[0], "label": r[1] or "Öğrenci", "linked_at": _iso(r[2])}
            for r in rows
        ]

    def parents_of(self, student_tenant_id: str) -> list[str]:
        """Bu öğrenciye bağlı veli tenant'ları (en eski bağ önce).

        Aile paylaşımlı-kota havuzu + entitlement mirası (çocuk, premium velisinin
        planını miras alır) için ters arama. Boş/bağsız → []."""
        if not student_tenant_id:
            return []
        with self._lock:
            assert self._db is not None
            rows = self._db.execute(
                "SELECT parent_tenant_id FROM parent_links WHERE student_tenant_id = ? "
                "ORDER BY linked_at ASC",
                (student_tenant_id,),
            ).fetchall()
        return [r[0] for r in rows]

    def unlink(self, parent_tenant_id: str, student_tenant_id: str) -> bool:
        with self._lock:
            assert self._db is not None
            cur = self._db.execute(
                "DELETE FROM parent_links WHERE parent_tenant_id = ? AND student_tenant_id = ?",
                (parent_tenant_id, student_tenant_id),
            )
            self._db.commit()
            return cur.rowcount > 0

    def close(self) -> None:
        with self._lock:
            if self._db is not None:
                try:
                    self._db.close()
                except Exception as exc:  # noqa: BLE001
                    logger.warning("ParentLinkStore close hatası: %s", exc)
                self._db = None


PARENT_LINK_STORE = ParentLinkStore()
