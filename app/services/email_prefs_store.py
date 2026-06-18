"""E-posta tercihleri (KVKK opt-in) kalıcılığı — Track 2 temeli.

Bülten + hatırlatma e-postaları YALNIZ açık onay (opt-in) veren kullanıcılara
gönderilir. Bu store onayı + e-postayı saklar (cron/gönderim Clerk Admin API'ye
gerek kalmadan buradan okur). KVKK: izin açık, geri alınabilir (unsubscribe).

Aynı SQLite/Turso dosyası; ayrı tablo. Thread-safe (db_connection deseni).
Singleton: EMAIL_PREFS.
"""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings
from app.services.db_connection import connect as db_connect

logger = logging.getLogger(__name__)


class EmailPrefsStore:
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
            CREATE TABLE IF NOT EXISTS email_prefs (
                tenant_id TEXT PRIMARY KEY,
                email TEXT,
                newsletter_optin INTEGER NOT NULL DEFAULT 0,
                updated_at REAL NOT NULL
            )
            """
        )
        # Cron (re-engagement/bülten) opt-in olanları hızlı çeksin.
        self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_email_optin "
            "ON email_prefs(newsletter_optin)"
        )
        self._db.commit()

    def get(self, tenant_id: str) -> dict | None:
        """Kullanıcının tercihi. Hiç ayarlanmadıysa None (→ onay kartı gösterilir)."""
        if not tenant_id:
            return None
        with self._lock:
            assert self._db is not None
            row = self._db.execute(
                "SELECT email, newsletter_optin, updated_at FROM email_prefs "
                "WHERE tenant_id = ?",
                (tenant_id,),
            ).fetchone()
        if not row:
            return None
        return {
            "email": row[0],
            "newsletter_optin": bool(row[1]),
            "updated_at": datetime.fromtimestamp(row[2], tz=timezone.utc).isoformat(),
        }

    def set(self, *, tenant_id: str, email: str | None, newsletter_optin: bool) -> None:
        """Tercihi kaydeder/günceller (UPSERT). E-posta sonraki gönderim için saklanır."""
        if not tenant_id:
            return
        now = time.time()
        with self._lock:
            assert self._db is not None
            self._db.execute(
                """
                INSERT INTO email_prefs (tenant_id, email, newsletter_optin, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(tenant_id) DO UPDATE SET
                    email = excluded.email,
                    newsletter_optin = excluded.newsletter_optin,
                    updated_at = excluded.updated_at
                """,
                (tenant_id, (email or "").strip() or None, 1 if newsletter_optin else 0, now),
            )
            self._db.commit()

    def list_opted_in(self) -> list[dict]:
        """Onay veren + e-postası olan kullanıcılar (cron gönderimi için)."""
        with self._lock:
            assert self._db is not None
            rows = self._db.execute(
                "SELECT tenant_id, email FROM email_prefs "
                "WHERE newsletter_optin = 1 AND email IS NOT NULL",
            ).fetchall()
        return [{"tenant_id": r[0], "email": r[1]} for r in rows]

    def close(self) -> None:
        with self._lock:
            if self._db is not None:
                try:
                    self._db.close()
                except Exception as exc:  # noqa: BLE001
                    logger.warning("EmailPrefsStore close hatası: %s", exc)
                self._db = None


EMAIL_PREFS = EmailPrefsStore()
