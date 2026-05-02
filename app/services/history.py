"""Üretim geçmişi cache'i — aynı isteği tekrarladığında varyasyon için.

(tenant_id, grade, topic_id, kazanim_kod, difficulty) anahtarıyla son N üretilmiş
sorunun normalize hali + bağlam kelimeleri + opsiyonel embedding'i tutulur.

Persistence (settings.enable_history_persist):
    True  → SQLite'a yazar, başlangıçta yükler. Restart sonrası kayıp olmaz.
    False → Sadece bellek; eski davranış.

Tenant izolasyonu HistoryKey'in ilk elemanı (str). Default "__shared__"
geriye uyumluluk için; istemci farklı tenant_id verirse cache ayrılır.
"""
from __future__ import annotations

import logging
import sqlite3
import struct
import threading
from collections import deque
from pathlib import Path
from typing import Iterable, Sequence

from app.config import settings

logger = logging.getLogger(__name__)


HistoryKey = tuple[str, int, str, str, str]
"""(tenant_id, grade, topic_id, kazanim_kod, difficulty)"""

DEFAULT_TENANT = "__shared__"


def _key_to_str(key: HistoryKey) -> str:
    return "|".join(str(p) for p in key)


def _pack_embedding(emb: Sequence[float] | None) -> bytes | None:
    if not emb:
        return None
    return struct.pack(f"{len(emb)}f", *emb)


def _unpack_embedding(blob: bytes | None) -> list[float] | None:
    if not blob:
        return None
    n = len(blob) // 4
    return list(struct.unpack(f"{n}f", blob))


class _Entry:
    __slots__ = ("normalized_question", "contexts", "embedding")

    def __init__(
        self,
        normalized_question: str,
        contexts: Iterable[str],
        embedding: Sequence[float] | None = None,
    ) -> None:
        self.normalized_question = normalized_question
        self.contexts = tuple(contexts)
        self.embedding = list(embedding) if embedding else None


class GenerationHistory:
    def __init__(
        self,
        capacity_per_key: int = 30,
        persist: bool | None = None,
        db_path: str | None = None,
    ) -> None:
        self._capacity = capacity_per_key
        self._cache: dict[HistoryKey, deque[_Entry]] = {}
        self._lock = threading.Lock()
        self._persist = settings.enable_history_persist if persist is None else persist
        self._db_path = db_path or settings.history_db_path
        self._db: sqlite3.Connection | None = None
        if self._persist:
            self._init_db()
            self._load_from_db()

    def _init_db(self) -> None:
        try:
            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
            self._db = sqlite3.connect(self._db_path, check_same_thread=False)
            self._db.execute(
                """
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL,
                    normalized_question TEXT NOT NULL,
                    contexts TEXT NOT NULL,
                    embedding BLOB,
                    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
                )
                """
            )
            self._db.execute(
                "CREATE INDEX IF NOT EXISTS idx_history_key ON history(key, id)"
            )
            self._db.commit()
        except sqlite3.Error as exc:
            logger.warning("History DB init başarısız, persistence devre dışı: %s", exc)
            self._persist = False
            self._db = None

    def _load_from_db(self) -> None:
        if self._db is None:
            return
        try:
            cur = self._db.execute(
                "SELECT key, normalized_question, contexts, embedding FROM history "
                "ORDER BY id ASC"
            )
            for row in cur:
                key_str, nq, ctx_str, emb_blob = row
                key = self._parse_key(key_str)
                if key is None:
                    continue
                contexts = ctx_str.split("\x1f") if ctx_str else []
                emb = _unpack_embedding(emb_blob)
                bucket = self._cache.get(key)
                if bucket is None:
                    bucket = deque(maxlen=self._capacity)
                    self._cache[key] = bucket
                bucket.append(_Entry(nq, contexts, emb))
        except sqlite3.Error as exc:
            logger.warning("History DB load başarısız: %s", exc)

    @staticmethod
    def _parse_key(key_str: str) -> HistoryKey | None:
        parts = key_str.split("|")
        if len(parts) != 5:
            return None
        try:
            return (parts[0], int(parts[1]), parts[2], parts[3], parts[4])
        except ValueError:
            return None

    def record(
        self,
        key: HistoryKey,
        normalized_question: str,
        contexts: Iterable[str],
        embedding: Sequence[float] | None = None,
    ) -> None:
        contexts_list = list(contexts)
        entry = _Entry(normalized_question, contexts_list, embedding)
        with self._lock:
            bucket = self._cache.get(key)
            if bucket is None:
                bucket = deque(maxlen=self._capacity)
                self._cache[key] = bucket
            bucket.append(entry)
        if self._persist and self._db is not None:
            try:
                key_str = _key_to_str(key)
                self._db.execute(
                    "INSERT INTO history (key, normalized_question, contexts, embedding) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        key_str,
                        normalized_question,
                        "\x1f".join(contexts_list),
                        _pack_embedding(embedding),
                    ),
                )
                # Capacity-aşımı: en eski kayıtları sil.
                self._db.execute(
                    "DELETE FROM history WHERE key = ? AND id NOT IN ("
                    "SELECT id FROM history WHERE key = ? ORDER BY id DESC LIMIT ?"
                    ")",
                    (key_str, key_str, self._capacity),
                )
                self._db.commit()
            except sqlite3.Error as exc:
                logger.warning("History DB write başarısız (kayıp olmayacak, RAM güncellendi): %s", exc)

    def seen_embeddings(self, key: HistoryKey) -> list[list[float]]:
        with self._lock:
            bucket = self._cache.get(key)
            if bucket is None:
                return []
            return [e.embedding for e in bucket if e.embedding]

    def seen_questions(self, key: HistoryKey) -> set[str]:
        with self._lock:
            bucket = self._cache.get(key)
            if bucket is None:
                return set()
            return {e.normalized_question for e in bucket}

    def context_exclusions(self, key: HistoryKey, max_contexts: int = 15) -> list[str]:
        with self._lock:
            bucket = self._cache.get(key)
            if bucket is None:
                return []
            entries = list(bucket)
        all_ctx: set[str] = set()
        for e in reversed(entries):
            all_ctx.update(e.contexts)
            if len(all_ctx) >= max_contexts:
                break
        return sorted(all_ctx)[:max_contexts]

    def size(self, key: HistoryKey) -> int:
        with self._lock:
            bucket = self._cache.get(key)
            return len(bucket) if bucket else 0

    def clear(self, key: HistoryKey | None = None) -> None:
        """key None ise tüm cache'i temizler."""
        with self._lock:
            if key is None:
                self._cache.clear()
            else:
                self._cache.pop(key, None)
        if self._persist and self._db is not None:
            try:
                if key is None:
                    self._db.execute("DELETE FROM history")
                else:
                    self._db.execute("DELETE FROM history WHERE key = ?", (_key_to_str(key),))
                self._db.commit()
            except sqlite3.Error as exc:
                logger.warning("History DB clear başarısız: %s", exc)


GENERATION_HISTORY = GenerationHistory()
