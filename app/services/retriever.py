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
    ) -> list[dict]:
        """Soru-cevap formatlı few-shot örnekleri döndürür (textbook chunk'ları HARİÇ).

        Katmanlı fallback: dar filtreden geniş filtreye.
        """
        return self._query_with_fallback(
            query_text=query_text,
            grade=grade,
            kazanim_kod=kazanim_kod,
            topic_id=topic_id,
            difficulty=difficulty,
            k=k,
            include_textbook=False,
        )

    def retrieve_textbook(
        self,
        query_text: str,
        grade: int,
        kazanim_kod: str | None,
        topic_id: str,
        k: int = 3,
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
        collected: list[dict] = []

        for where in filters_to_try:
            if len(collected) >= k:
                break
            try:
                res = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=max(k * 3, 15),  # textbook filtre sonrası elenecek, fazlasını çek
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
                collected.append({
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
                if len(collected) >= k:
                    break

        return collected


@lru_cache(maxsize=1)
def get_retriever() -> ExampleRetriever | None:
    """Modül düzeyinde singleton. ChromaDB yoksa None döner (USE_RAG=False davranışı)."""
    try:
        return ExampleRetriever()
    except RetrieverError as exc:
        logger.warning("Retriever başlatılamadı: %s", exc)
        return None
