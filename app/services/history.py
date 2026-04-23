"""Üretim geçmişi cache'i — aynı isteği tekrarladığında varyasyon için.

(grade, topic_id, kazanim_kod, difficulty) anahtarıyla son N üretilmiş
sorunun normalize hali + bağlam kelimeleri tutulur.

Kalıcı değil — servis yeniden başlatılınca sıfırlanır. RAG iterasyonunda
embedding tabanlı semantik cache ile değiştirilebilir.
"""
import threading
from collections import deque
from typing import Iterable


HistoryKey = tuple[int, str, str, str]


class _Entry:
    __slots__ = ("normalized_question", "contexts")

    def __init__(self, normalized_question: str, contexts: Iterable[str]) -> None:
        self.normalized_question = normalized_question
        self.contexts = tuple(contexts)


class GenerationHistory:
    def __init__(self, capacity_per_key: int = 30) -> None:
        self._capacity = capacity_per_key
        self._cache: dict[HistoryKey, deque[_Entry]] = {}
        self._lock = threading.Lock()

    def record(
        self,
        key: HistoryKey,
        normalized_question: str,
        contexts: Iterable[str],
    ) -> None:
        with self._lock:
            bucket = self._cache.get(key)
            if bucket is None:
                bucket = deque(maxlen=self._capacity)
                self._cache[key] = bucket
            bucket.append(_Entry(normalized_question, contexts))

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
        # En son üretilenlerin bağlamlarına öncelik ver.
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


GENERATION_HISTORY = GenerationHistory()
