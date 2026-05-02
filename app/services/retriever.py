"""ChromaDB üzerinden kazanım × zorluk filtreli örnek retrieval'ı.

Akış:
    1. Sorgu metni embed edilir.
    2. Önce (grade, kazanim_kod, difficulty) tam eşleşmesiyle aranır.
    3. Yeterli bulunamazsa (grade, kazanim_kod) ile geniş aramaya geçilir.
    4. Hâlâ yetersizse (grade, topic_id) ile son fallback.

Retrieved dokümanlar few-shot benzeri dict formatında döndürülür.
"""
from __future__ import annotations

import logging
import random
from functools import lru_cache
from typing import Any

import chromadb

from app.config import settings
from app.services.embedder import GeminiEmbedder

logger = logging.getLogger(__name__)


class RetrieverError(Exception):
    pass


def _where_and(*clauses: dict[str, Any] | None) -> dict[str, Any] | None:
    """ChromaDB where filtresi oluşturur. None olanları atlar."""
    real = [c for c in clauses if c]
    if not real:
        return None
    if len(real) == 1:
        return real[0]
    return {"$and": real}


def _weighted_sample(
    pool: list[dict],
    k: int,
    rng: random.Random,
) -> list[dict]:
    """Distance ağırlıklı, geri konmasız örnekleme.

    Daha düşük distance (daha yakın) = daha yüksek seçilme şansı, ama her aday
    sıfırdan büyük ağırlığa sahip olduğu için aynı sorgunun farklı çağrıları
    farklı k seçer. Distance None olanlara nötr ağırlık verilir.
    """
    if k >= len(pool):
        return list(pool)

    distances = [c.get("distance") for c in pool]
    valid = [d for d in distances if isinstance(d, (int, float))]
    if not valid:
        # Distance yok — saf rastgele örnekleme.
        return rng.sample(pool, k)

    max_d = max(valid)
    # Ağırlık: yakınlığa göre azalan ama her zaman pozitif.
    # weight = (max_d - d) + small_epsilon → en uzak bile sıfırdan büyük.
    eps = (max_d * 0.1) if max_d > 0 else 0.1
    weights = [
        ((max_d - d) + eps) if isinstance(d, (int, float)) else eps
        for d in distances
    ]

    selected_idx: list[int] = []
    available = list(range(len(pool)))
    cur_weights = list(weights)
    for _ in range(k):
        if not available:
            break
        total = sum(cur_weights[i] for i in available)
        if total <= 0:
            chosen = rng.choice(available)
        else:
            r = rng.random() * total
            running = 0.0
            chosen = available[-1]
            for i in available:
                running += cur_weights[i]
                if running >= r:
                    chosen = i
                    break
        selected_idx.append(chosen)
        available.remove(chosen)
    return [pool[i] for i in selected_idx]


class ExampleRetriever:
    def __init__(
        self,
        db_path: str | None = None,
        collection_name: str | None = None,
    ) -> None:
        self.db_path = db_path or settings.chroma_db_path
        self.collection_name = collection_name or settings.chroma_collection
        self.client = chromadb.PersistentClient(path=self.db_path)
        try:
            self.collection = self.client.get_collection(self.collection_name)
        except Exception as exc:
            raise RetrieverError(
                f"ChromaDB koleksiyonu '{self.collection_name}' bulunamadı. "
                "Önce `python scripts/ingest_to_chroma.py` çalıştırın."
            ) from exc
        self.embedder = GeminiEmbedder()

    def count(self) -> int:
        return self.collection.count()

    # content_type değerlerinden textbook'a ait olanlar — few-shot yolunda hariç tutulur
    _TEXTBOOK_CONTENT_TYPES = {
        "textbook_example",
        "textbook_activity",
        "textbook_concept",
        "textbook_problem",
        "textbook_exercise",
        "curriculum_expansion",
    }

    def retrieve(
        self,
        query_text: str,
        grade: int,
        kazanim_kod: str | None,
        topic_id: str,
        difficulty: str,
        k: int = 5,
        rng: random.Random | None = None,
    ) -> list[dict]:
        """Soru-cevap formatlı few-shot örnekleri döndürür (textbook chunk'ları HARİÇ).

        Katmanlı fallback: dar filtreden geniş filtreye.
        rng verilirse oversample + weighted random sampling — aynı sorguda farklı çağrıların
        farklı k seçmesi için.
        """
        return self._query_with_fallback(
            query_text=query_text,
            grade=grade,
            kazanim_kod=kazanim_kod,
            topic_id=topic_id,
            difficulty=difficulty,
            k=k,
            include_textbook=False,
            rng=rng,
        )

    def retrieve_textbook(
        self,
        query_text: str,
        grade: int,
        kazanim_kod: str | None,
        topic_id: str,
        k: int = 3,
        rng: random.Random | None = None,
    ) -> list[dict]:
        """Sadece MEB ders kitabı chunk'larını döndürür. Difficulty filtresi YOK
        (kitap içeriği zorluk-agnostic). curriculum_expansion da dahildir."""
        return self._query_with_fallback(
            query_text=query_text,
            grade=grade,
            kazanim_kod=kazanim_kod,
            topic_id=topic_id,
            difficulty=None,
            k=k,
            include_textbook=True,
            textbook_only=True,
            rng=rng,
        )

    def _query_with_fallback(
        self,
        query_text: str,
        grade: int,
        kazanim_kod: str | None,
        topic_id: str,
        difficulty: str | None,
        k: int,
        include_textbook: bool,
        textbook_only: bool = False,
        rng: random.Random | None = None,
    ) -> list[dict]:
        query_embedding = self.embedder.embed_one(query_text)

        filters_to_try: list[dict[str, Any] | None] = []
        if kazanim_kod:
            if difficulty:
                filters_to_try.append(
                    _where_and(
                        {"grade": grade},
                        {"kazanim_kod": kazanim_kod},
                        {"difficulty": difficulty},
                    )
                )
            filters_to_try.append(
                _where_and(
                    {"grade": grade},
                    {"kazanim_kod": kazanim_kod},
                )
            )
        if difficulty:
            filters_to_try.append(
                _where_and(
                    {"grade": grade},
                    {"topic_id": topic_id},
                    {"difficulty": difficulty},
                )
            )
        filters_to_try.append(
            _where_and(
                {"grade": grade},
                {"topic_id": topic_id},
            )
        )
        if textbook_only:
            # Ders kitabı için son fallback: sadece sınıf bazlı, kazanım/topic yok
            filters_to_try.append(_where_and({"grade": grade}))

        seen_ids: set[str] = set()
        # Jitter aktifse aday havuzunu biriktir, sonunda örnekle.
        # rng yoksa eski deterministic davranış: ilk k'yı al ve bitir.
        oversample_factor = 4 if rng is not None else 1
        candidate_pool: list[dict] = []
        target = k if rng is not None else k  # collected aynı sayıya hedeflenir

        for where in filters_to_try:
            # rng varsa daha geniş havuz topla; deterministic modda erken çık.
            if rng is None and len(candidate_pool) >= target:
                break
            if rng is not None and len(candidate_pool) >= k * oversample_factor:
                break
            try:
                res = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=max(k * oversample_factor * 2, 30),
                    where=where,
                )
            except Exception as exc:
                logger.warning("Chroma query hata (%s): %s", where, exc)
                continue
            ids = (res.get("ids") or [[]])[0]
            docs = (res.get("documents") or [[]])[0]
            metas = (res.get("metadatas") or [[]])[0]
            distances = (res.get("distances") or [[]])[0]
            for i, cid in enumerate(ids):
                if cid in seen_ids:
                    continue
                meta = metas[i] if i < len(metas) else {}
                meta_ct = meta.get("content_type") or meta.get("question_type") or ""
                is_textbook = meta_ct in self._TEXTBOOK_CONTENT_TYPES
                if textbook_only and not is_textbook:
                    continue
                if not include_textbook and is_textbook:
                    continue
                seen_ids.add(cid)
                distance = distances[i] if i < len(distances) else None
                candidate_pool.append({
                    "type": meta.get("question_type"),
                    "difficulty": meta.get("difficulty"),
                    "question": docs[i] if i < len(docs) else "",
                    "answer": meta.get("answer", ""),
                    "solution": meta.get("solution", ""),
                    "kazanim_kod": meta.get("kazanim_kod", ""),
                    "source": meta.get("source", ""),
                    "content_type": meta_ct,
                    "page_start": meta.get("page_start"),
                    "page_end": meta.get("page_end"),
                    "header": meta.get("header", ""),
                    "tema": meta.get("tema", ""),
                    "distance": distance,
                })
                if rng is None and len(candidate_pool) >= k:
                    break

        if rng is None or len(candidate_pool) <= k:
            return candidate_pool[:k]

        return _weighted_sample(candidate_pool, k, rng)


@lru_cache(maxsize=1)
def get_retriever() -> ExampleRetriever | None:
    """Modül düzeyinde singleton. ChromaDB yoksa None döner (USE_RAG=False davranışı)."""
    try:
        return ExampleRetriever()
    except RetrieverError as exc:
        logger.warning("Retriever başlatılamadı: %s", exc)
        return None
