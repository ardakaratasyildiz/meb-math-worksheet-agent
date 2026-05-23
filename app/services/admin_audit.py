"""Admin panel erişim audit log'u.

Her admin endpoint çağrısını kaydeder: kim (Clerk user ID), ne yaptı, hangi
tenant'a baktı, ne zaman, hangi IP'den. KVKK ve güvenlik incelemesi için
kanıt kayıt — kullanıcı verisinin kimin tarafından görüntülendiğini sonradan
sorgulayabilmemiz şart.

Tablo `history.sqlite3` ile aynı dosyayı paylaşır (worksheet_history,
generation_cache vb. ile birlikte). Turso etkinse otomatik replicate olur.

Kullanım:
    ADMIN_AUDIT.record(clerk_user_id="user_xxx", action="view_tenant_history",
                       target="tenant_yyy", ip="1.2.3.4")
"""
from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Any

from app.config import settings
from app.services.db_connection import connect as db_connect

logger = logging.getLogger(__name__)


class AdminAudit:
    """Thread-safe, SQLite/Turso tabanlı admin erişim kayıtçısı. Singleton: ADMIN_AUDIT."""

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
            CREATE TABLE IF NOT EXISTS admin_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clerk_user_id TEXT,
                action TEXT NOT NULL,
                target TEXT,
                ip TEXT,
                created_at REAL NOT NULL
            )
            """
        )
        self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_created "
            "ON admin_audit(created_at DESC)"
        )
        self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_user "
            "ON admin_audit(clerk_user_id, created_at DESC)"
        )
        self._db.commit()

    def record(
        self,
        action: str,
        clerk_user_id: str | None = None,
        target: str | None = None,
        ip: str | None = None,
    ) -> None:
        """Audit kaydı yaz. Hata durumunda uygulamayı kırmaz — log + devam."""
        try:
            with self._lock:
                assert self._db is not None
                self._db.execute(
                    "INSERT INTO admin_audit (clerk_user_id, action, target, ip, created_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (clerk_user_id, action, target, ip, time.time()),
                )
                self._db.commit()
        except Exception as exc:  # noqa: BLE001
            # Audit yazımı başarısız olursa admin endpoint'i yine çalışsın —
            # gözlemlenebilirlik nice-to-have, hard dependency değil.
            logger.warning("Admin audit yazımı başarısız: %s", exc)

    def recent(self, limit: int = 100) -> list[dict[str, Any]]:
        """Son N audit kaydı — en yeni önce. /admin/audit endpoint'i için."""
        lim = max(1, min(500, limit))
        with self._lock:
            assert self._db is not None
            rows = self._db.execute(
                "SELECT id, clerk_user_id, action, target, ip, created_at "
                "FROM admin_audit ORDER BY created_at DESC LIMIT ?",
                (lim,),
            ).fetchall()
        return [
            {
                "id": rid,
                "clerk_user_id": uid,
                "action": action,
                "target": target,
                "ip": ip,
                "created_at": created_at,
            }
            for rid, uid, action, target, ip, created_at in rows
        ]

    def total_count(self) -> int:
        """Toplam audit kayıt sayısı — /readyz teşhisi için."""
        with self._lock:
            assert self._db is not None
            row = self._db.execute("SELECT COUNT(*) FROM admin_audit").fetchone()
        return int(row[0]) if row else 0


ADMIN_AUDIT = AdminAudit()
