"""Üretim sonucu önbelleği — aynı (grade, topic, kazanım, difficulty, count)
istekleri için cached soru seti döndürür, LLM çağrısını atlar.

Tasarım:
    - SQLite tablosu (`generation_cache`), aynı history.sqlite3 dosyasında.
    - Key: cache_key = "g{grade}|{topic_id}|{kazanim_kod}|{difficulty}|q{count}"
    - Her key için en fazla `max_per_key` cached set saklanır (FIFO).
    - get() önce key ile filter, sonra exclude_questions overlap'i 0 olan ilk
      set'i döndürür (kullanıcının history'sinde olan sorular tekrar gelmesin).
    - put() yeni set ekler, max aşılırsa en eski silinir.

Semantic fallback (yakın kazanım/zorluk için cache hit) Sprint 7+'da değerlendirilecek;
şu anki sürüm exact-match — basit, deterministik, embedding gerekmez.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path
from typing import Iterable

from app.config import settings
from app.models.schemas import Question
from app.services.db_connection import connect as db_connect

logger = logging.getLogger(__name__)


def _cache_key(
    grade: int,
    topic_id: str,
    kazanim_kod: str | None,
    difficulty: str,
    question_count: int,
    allowed_types=None,
    yeni_nesil: bool = False,
) -> str:
    # allowed_types (kullanıcının seçtiği soru tipi filtresi) anahtara dahil
    # edilir — aksi halde filtre seçen kullanıcıya filtresiz bir cached set
    # (veya tersi) dönebilirdi. None/boş → "all".
    if allowed_types:
        types = "+".join(sorted(getattr(t, "value", str(t)) for t in allowed_types))
    else:
        types = "all"
    # yeni_nesil (premium: farklı model + prompt + görsel-ağırlıklı dağılım)
    # anahtara dahildir — premium ve normal setler farklı karakterde olduğundan
    # ayrı havuzlarda tutulur; premium isteyen kullanıcıya normal set (veya tersi)
    # dönmesin. Normal mod SONEK EKLEMEZ → eski cache kayıtları geçerli kalır.
    suffix = "|premium" if yeni_nesil else ""
    return (
        f"g{grade}|{topic_id}|{kazanim_kod or '__AUTO__'}|{difficulty}"
        f"|q{question_count}|t{types}{suffix}"
    )


class GenerationCache:
    """Thread-safe SQLite tabanlı cache. Singleton kullanım önerilir (`GENERATION_CACHE`)."""

    def __init__(
        self,
        db_path: str | None = None,
        max_per_key: int = 10,
    ) -> None:
        self._db_path = db_path or settings.history_db_path
        self._max_per_key = max_per_key
        self._lock = threading.Lock()
        self._db = None
        self._hits = 0
        self._misses = 0
        self._init_db()

    def _init_db(self) -> None:
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._db = db_connect(self._db_path)
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS generation_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cache_key TEXT NOT NULL,
                questions_json TEXT NOT NULL,
                created_at REAL NOT NULL
            )
            """
        )
        self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_cache_key_created "
            "ON generation_cache(cache_key, created_at DESC)"
        )
        self._db.commit()

    def get(
        self,
        grade: int,
        topic_id: str,
        kazanim_kod: str | None,
        difficulty: str,
        question_count: int,
        exclude_questions: Iterable[str] = (),
        allowed_types=None,
        yeni_nesil: bool = False,
    ) -> list[Question] | None:
        """Cached set döndürür ya da None.

        exclude_questions: kullanıcının history'sinde olan normalize edilmiş sorular.
        Bir cached set'in herhangi bir sorusu bu kümede ise o set atlanır;
        kalan set yoksa miss.

        allowed_types: kullanıcının soru tipi filtresi — cache anahtarına dahildir.
        yeni_nesil: premium mod — cache anahtarına dahildir (ayrı havuz).
        """
        from app.services.diversity import normalize_question

        excl = set(exclude_questions)
        key = _cache_key(
            grade, topic_id, kazanim_kod, difficulty, question_count,
            allowed_types, yeni_nesil,
        )
        with self._lock:
            assert self._db is not None
            rows = self._db.execute(
                "SELECT questions_json FROM generation_cache WHERE cache_key = ? "
                "ORDER BY created_at DESC LIMIT ?",
                (key, self._max_per_key),
            ).fetchall()

        if not rows:
            self._misses += 1
            return None

        # Rastgele bir set seç ki çeşitlilik korunsun (zaman damgasıyla sıralı geldiler)
        import random
        random.shuffle(rows)

        for (questions_json,) in rows:
            try:
                data = json.loads(questions_json)
                questions = [Question.model_validate(q) for q in data]
            except (json.JSONDecodeError, ValueError) as exc:
                logger.warning("Cache satırı parse edilemedi (%s): %s", key, exc)
                continue
            if excl:
                has_overlap = any(
                    normalize_question(q.question) in excl for q in questions
                )
                if has_overlap:
                    continue
            self._hits += 1
            logger.info("Cache HIT: %s (%d soru)", key, len(questions))
            return questions

        # Tüm cached set'ler history'de var
        self._misses += 1
        logger.info("Cache MISS (history overlap): %s", key)
        return None

    def put(
        self,
        grade: int,
        topic_id: str,
        kazanim_kod: str | None,
        difficulty: str,
        question_count: int,
        questions: list[Question],
        allowed_types=None,
        yeni_nesil: bool = False,
    ) -> None:
        """Yeni set ekler. Aynı key için max_per_key aşıldıysa en eski silinir."""
        if not questions:
            return
        key = _cache_key(
            grade, topic_id, kazanim_kod, difficulty, question_count,
            allowed_types, yeni_nesil,
        )
        # Pydantic mode="json" → datetime/enum'ları string'e çevirir.
        payload = json.dumps(
            [q.model_dump(mode="json") for q in questions],
            ensure_ascii=False,
        )
        now = time.time()
        with self._lock:
            assert self._db is not None
            self._db.execute(
                "INSERT INTO generation_cache (cache_key, questions_json, created_at) "
                "VALUES (?, ?, ?)",
                (key, payload, now),
            )
            # Trim: bu key için fazla satırları sil.
            self._db.execute(
                """
                DELETE FROM generation_cache
                WHERE cache_key = ?
                  AND id NOT IN (
                    SELECT id FROM generation_cache
                    WHERE cache_key = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                  )
                """,
                (key, key, self._max_per_key),
            )
            self._db.commit()
        logger.info("Cache PUT: %s (%d soru)", key, len(questions))

    def stats(self) -> dict[str, int]:
        with self._lock:
            assert self._db is not None
            total = self._db.execute(
                "SELECT COUNT(*) FROM generation_cache"
            ).fetchone()[0]
            distinct = self._db.execute(
                "SELECT COUNT(DISTINCT cache_key) FROM generation_cache"
            ).fetchone()[0]
        return {
            "hits": self._hits,
            "misses": self._misses,
            "total_entries": int(total),
            "distinct_keys": int(distinct),
        }

    def clear(self) -> None:
        """Test ve admin amaçlı toplu temizlik."""
        with self._lock:
            assert self._db is not None
            self._db.execute("DELETE FROM generation_cache")
            self._db.commit()
            self._hits = 0
            self._misses = 0


GENERATION_CACHE = GenerationCache(max_per_key=settings.generation_cache_max_per_key)
