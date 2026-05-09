"""SQLite veya Turso (libSQL) bağlantı fabrikası.

Env-var driven:
    TURSO_DATABASE_URL set → Turso embedded replica modu (lokal SQLite cache +
        her commit'te otomatik remote sync). Restart'a dayanıklı.
    Değilse → klasik sqlite3 bağlantısı (lokal dev).

Kullanım: `from app.services.db_connection import connect`
yerine `sqlite3.connect(path, check_same_thread=False)` koyulur.
Cevap olarak gelen connection object sqlite3.Connection ile API-uyumlu —
mevcut execute/commit/fetchall çağrıları aynen çalışır.
"""
from __future__ import annotations

import logging
import os
import sqlite3

logger = logging.getLogger(__name__)


def is_turso_enabled() -> bool:
    return bool(os.environ.get("TURSO_DATABASE_URL", "").strip())


class _SyncOnCommit:
    """libsql Connection wrapper — commit() sonrası otomatik sync.

    Reads lokal replica'dan (hızlı). Writes önce lokale, commit sonrası
    Turso'ya push edilir. Sync hatası uygulamayı durdurmaz, log yazar.
    """

    def __init__(self, conn) -> None:
        self._conn = conn

    def __getattr__(self, name):
        return getattr(self._conn, name)

    def execute(self, *args, **kwargs):
        return self._conn.execute(*args, **kwargs)

    def commit(self) -> None:
        self._conn.commit()
        try:
            self._conn.sync()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Turso sync başarısız (commit sonrası): %s", exc)

    def close(self) -> None:
        try:
            self._conn.sync()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Turso final sync başarısız (close): %s", exc)
        self._conn.close()


def connect(local_path: str):
    """Lokal SQLite path'i alır, ortama göre uygun connection döner."""
    if is_turso_enabled():
        url = os.environ["TURSO_DATABASE_URL"].strip()
        token = os.environ.get("TURSO_AUTH_TOKEN", "").strip()
        try:
            import libsql_experimental as libsql  # type: ignore

            conn = libsql.connect(local_path, sync_url=url, auth_token=token)
            # İlk açılışta remote'tan local replica'ya çek — restart sonrası
            # cache verisi geri gelmiş olur.
            try:
                conn.sync()
                logger.info(
                    "Turso bağlantısı kuruldu, initial sync OK (local=%s)",
                    local_path,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Initial sync başarısız (replica boş başlar): %s", exc)
            return _SyncOnCommit(conn)
        except ImportError:
            logger.warning(
                "libsql-experimental kurulu değil — TURSO_* env'leri set ama "
                "paket yok. Lokal SQLite'a düşülüyor."
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Turso bağlantısı kurulamadı, lokal SQLite fallback: %s", exc
            )

    return sqlite3.connect(local_path, check_same_thread=False)
