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
import re
from functools import lru_cache
from typing import Any

import chromadb
from rank_bm25 import BM25Okapi

from app.config import settings
from app.services.embedder import GeminiEmbedder

_TOKEN_RE = re.compile(r"\w+", flags=re.UNICODE)


def _tokenize(text: str) -> list[str]:
    """Küçük harfe indirir, kelime token'larına ayırır. Türkçe ASCII-folding yok —
    'ı/i' veya 'ç/c' gibi farklılıklar BM25'te ayrı sayılır (bu istenir; matematik
    terimlerinin doğru türünü korumak)."""
    return [m.group(0).lower() for m in _TOKEN_RE.finditer(text or "")]

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


def _cap_per_source(pool: list[dict], max_per_source: int = 2) -> list[dict]:
    """Aynı `source` (örn. 'textbook/3.sinif_1.pdf') alanından en fazla
    `max_per_source` chunk'ı tutar; sıralama korunur. Source bilgisi olmayan
    chunk'lar her zaman geçer."""
    counts: dict[str, int] = {}
    out: list[dict] = []
    for c in pool:
        src = c.get("source") or ""
        if not src:
            out.append(c)
            continue
        if counts.get(src, 0) >= max_per_source:
            continue
        counts[src] = counts.get(src, 0) + 1
        out.append(c)
    return out


def _source_priority(c: dict) -> float:
    """Kaynak-önceliği çarpanı: gerçek (çıkmış/LGS) ve GÖRSELLİ örnekler few-shot
    seçiminde öne çıksın → model gerçek görsel örnekleri daha sık görüp o mantığı öğrenir.
    """
    p = 1.0
    src = (c.get("source") or "")
    if src and not src.startswith("synthetic"):
        p *= 1.6  # gerçek kaynak (questions/lgs/cikmis) > sentetik
    q = c.get("question") or ""
    if "<svg" in q or "{{chart" in q or "|---" in q:
        p *= 1.8  # görselli soru (SVG/grafik/tablo) boost
    return p


def _weighted_sample(
    pool: list[dict],
    k: int,
    rng: random.Random,
) -> list[dict]:
    """Distance + kaynak-önceliği ağırlıklı, geri konmasız örnekleme.

    Daha düşük distance (daha yakın) = daha yüksek seçilme şansı; ayrıca gerçek
    ve görselli örnekler _source_priority ile boost alır. Her aday sıfırdan büyük
    ağırlığa sahip olduğu için aynı sorgunun farklı çağrıları farklı k seçer.
    """
    if k >= len(pool):
        return list(pool)

    distances = [c.get("distance") for c in pool]
    valid = [d for d in distances if isinstance(d, (int, float))]
    if valid:
        max_d = max(valid)
        # Ağırlık: yakınlığa göre azalan ama her zaman pozitif.
        eps = (max_d * 0.1) if max_d > 0 else 0.1
        base = [
            ((max_d - d) + eps) if isinstance(d, (int, float)) else eps
            for d in distances
        ]
    else:
        # Distance yok — nötr taban (kaynak-önceliği yine uygulanır).
        base = [1.0] * len(pool)
    weights = [b * _source_priority(pool[i]) for i, b in enumerate(base)]

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
        # BM25 indeksi — filter scope'una göre lazy & cached
        self._bm25_cache: dict[str, tuple[BM25Okapi, list[str], list[str], list[dict]]] = {}

    def count(self) -> int:
        return self.collection.count()

    def _bm25_for_filter(
        self,
        where: dict[str, Any] | None,
    ) -> tuple[BM25Okapi, list[str], list[str], list[dict]] | None:
        """Verilen filter scope'u için BM25 indeksi (id, text, metadata).

        Aynı filter daha önce sorgulanmışsa cache'ten döner. Build maliyeti
        ~100ms/2000 doc; tek seferlik."""
        cache_key = repr(where)
        cached = self._bm25_cache.get(cache_key)
        if cached is not None:
            return cached
        try:
            res = self.collection.get(where=where, include=["documents", "metadatas"])
        except Exception as exc:
            logger.warning("BM25 corpus alınamadı (%s): %s", where, exc)
            return None
        ids: list[str] = res.get("ids") or []
        docs: list[str] = res.get("documents") or []
        metas: list[dict] = res.get("metadatas") or []
        if not ids:
            return None
        tokenized = [_tokenize(d) for d in docs]
        if not any(tokenized):
            return None
        bm25 = BM25Okapi(tokenized)
        out = (bm25, ids, docs, metas)
        self._bm25_cache[cache_key] = out
        return out

    @staticmethod
    def _rrf_fuse(
        rankings: list[list[str]],
        k: int,
        rrf_k: int = 60,
    ) -> list[str]:
        """Reciprocal Rank Fusion: birden çok sıralı id listesinden tek sıralama.
        Score = sum(1 / (rrf_k + rank_in_list))"""
        scores: dict[str, float] = {}
        for rank_list in rankings:
            for rank, cid in enumerate(rank_list):
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank + 1)
        sorted_ids = sorted(scores.keys(), key=lambda c: -scores[c])
        return sorted_ids[:k]

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

        # Fallback sırası — sıkı difficulty filtresi mümkün olduğu kadar uzun korunur:
        #   1. (grade, kazanım, difficulty)  — en dar, en hedefli
        #   2. (grade, topic, difficulty)    — topic genişler ama difficulty SIKI
        #   3. (grade, kazanım)              — difficulty gevşer
        #   4. (grade, topic)                — en gevşek
        # Sprint 5 regresyonu (kolay/zor talep edildiğinde orta'ya kayma) bu
        # sıralamayla azaltılır: synthetic kolay/zor pool boyutu kazanım başına
        # 5; (1)'de yeterli bulunmazsa (3)'e atlamak yerine (2) ile topic genişler
        # ama kolay/zor kalır.
        filters_to_try: list[dict[str, Any] | None] = []
        if kazanim_kod and difficulty:
            filters_to_try.append(
                _where_and(
                    {"grade": grade},
                    {"kazanim_kod": kazanim_kod},
                    {"difficulty": difficulty},
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
        if kazanim_kod:
            filters_to_try.append(
                _where_and(
                    {"grade": grade},
                    {"kazanim_kod": kazanim_kod},
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

        use_hybrid = settings.enable_hybrid_retrieval

        for where in filters_to_try:
            # rng varsa daha geniş havuz topla; deterministic modda erken çık.
            if rng is None and len(candidate_pool) >= target:
                break
            if rng is not None and len(candidate_pool) >= k * oversample_factor:
                break
            n_dense = max(k * oversample_factor * 2, 30)
            try:
                res = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_dense,
                    where=where,
                )
            except Exception as exc:
                logger.warning("Chroma query hata (%s): %s", where, exc)
                continue
            dense_ids: list[str] = (res.get("ids") or [[]])[0]
            dense_docs: list[str] = (res.get("documents") or [[]])[0]
            dense_metas: list[dict] = (res.get("metadatas") or [[]])[0]
            dense_distances: list[float] = (res.get("distances") or [[]])[0]

            if use_hybrid:
                # BM25 sıralaması; aynı filter scope'unda
                bm25_data = self._bm25_for_filter(where)
                if bm25_data is not None:
                    bm25, all_ids, all_docs, all_metas = bm25_data
                    bm25_scores = bm25.get_scores(_tokenize(query_text))
                    # En yüksek BM25 skorlu top-N (n_dense kadar)
                    top_n_idx = sorted(
                        range(len(all_ids)),
                        key=lambda i: -bm25_scores[i],
                    )[:n_dense]
                    bm25_ids = [all_ids[i] for i in top_n_idx]
                    # RRF füzyonu
                    fused_ids = self._rrf_fuse(
                        [dense_ids, bm25_ids],
                        k=n_dense,
                        rrf_k=settings.hybrid_rrf_k,
                    )
                    # Doc/meta/distance'ları ID'den haritala
                    id_to_doc = {cid: all_docs[i] for i, cid in enumerate(all_ids)}
                    id_to_meta = {cid: all_metas[i] for i, cid in enumerate(all_ids)}
                    id_to_dist = {
                        cid: dense_distances[i] if i < len(dense_distances) else None
                        for i, cid in enumerate(dense_ids)
                    }
                    ids = fused_ids
                    docs = [id_to_doc.get(cid, "") for cid in fused_ids]
                    metas = [id_to_meta.get(cid, {}) for cid in fused_ids]
                    distances = [id_to_dist.get(cid) for cid in fused_ids]
                else:
                    ids, docs, metas, distances = dense_ids, dense_docs, dense_metas, dense_distances
            else:
                ids, docs, metas, distances = dense_ids, dense_docs, dense_metas, dense_distances
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

        # Source-aware diversity: textbook retrieval'da aynı PDF kaynağından
        # max_per_source kadar al. Bir kazanım için tüm chunk'lar tek bir
        # ders kitabı dosyasından gelirse model aynı bağlamı tekrar üretmeye
        # eğilimli — çeşitliliği bozar. Few-shot pool'unda source'lar zaten
        # synthetic+manual ile karışık, bu sınırı uygulamak gerekli değil.
        if textbook_only and candidate_pool:
            candidate_pool = _cap_per_source(candidate_pool, max_per_source=2)

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
