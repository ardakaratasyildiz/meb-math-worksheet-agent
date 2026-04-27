"""Retag edilmiş chunk'ların ChromaDB metadata'sını günceller.

Embedding aynı kalır (chunk metni değişmedi); sadece kazanım kodu, topic_id,
content_type ve confidence güncellenir. Böylece daha önce 'curriculum_expansion'
olarak gizlenen chunk'lar yeni kazanımlar üzerinden retrieve edilebilir hale gelir.

Kullanım:
    python scripts/reingest_retagged.py            # tüm sınıflar
    python scripts/reingest_retagged.py --grade 6  # sadece bir sınıf
    python scripts/reingest_retagged.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import chromadb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import settings  # noqa: E402
from app.data.curriculum import CURRICULUM  # noqa: E402

PROCESSED_DIR = ROOT / "knowledge_base" / "processed"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("reingest")


def _kazanim_to_topic_map(grade: int) -> dict[str, str]:
    out: dict[str, str] = {}
    for tid, t in CURRICULUM[grade].items():
        for k in t["kazanimlar"]:
            out[k["kod"]] = tid
    return out


def _load_grade_tagged(grade: int) -> list[dict]:
    p = PROCESSED_DIR / f"textbook_chunks_grade{grade}_tagged.json"
    if not p.exists():
        return []
    return json.load(p.open(encoding="utf-8"))["chunks"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--grade", type=int, default=None, help="Sadece bu sınıf; verilmezse hepsi")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    grades = [args.grade] if args.grade else [1, 2, 5, 6, 7]
    client = chromadb.PersistentClient(path=settings.chroma_db_path)
    collection = client.get_or_create_collection(
        name=settings.chroma_collection,
        metadata={"hnsw:space": "cosine"},
    )

    existing_ids: set[str] = set()
    try:
        existing_ids = set(collection.get(include=[], limit=None).get("ids", []))
    except Exception:
        pass
    logger.info("Koleksiyonda mevcut: %s kayıt", len(existing_ids))

    total_updates = 0
    by_grade: dict[int, int] = {}
    by_kazanim: dict[str, int] = {}
    needs_insert: list[dict] = []  # önceden ingest edilmemiş ama şimdi eşleşenler

    for grade in grades:
        chunks = _load_grade_tagged(grade)
        if not chunks:
            logger.warning("Grade %s için tagged dosya yok, atlanıyor.", grade)
            continue
        kod2tid = _kazanim_to_topic_map(grade)

        candidates = [
            c for c in chunks
            if c.get("retagged") and c.get("retag_kazanim_kod")
        ]
        logger.info("Grade %s: retag eşleşmesi olan %s chunk", grade, len(candidates))

        ids_to_update: list[str] = []
        metas_to_update: list[dict] = []
        for c in candidates:
            cid = c["chunk_id"]
            new_kod = c["retag_kazanim_kod"]
            new_tid = kod2tid.get(new_kod, "")
            new_ct = c.get("content_type", "textbook_concept")
            # Eski curriculum_expansion etiketini kaldır
            if new_ct == "curriculum_expansion":
                new_ct = "textbook_concept"

            new_meta = {
                "grade": c["grade"],
                "topic_id": new_tid,
                "kazanim_kod": new_kod,
                "kazanim_kod_present": True,
                "difficulty": "orta",
                "question_type": new_ct,
                "answer": "",
                "solution": "",
                "source": f"textbook/{c['source']}",
                "content_type": new_ct,
                "page_start": c["page_start"],
                "page_end": c["page_end"],
                "header": c.get("header") or "",
                "tema": c.get("tema") or "",
                "confidence": c.get("retag_confidence") or c.get("confidence") or "",
                "content_quality": c.get("content_quality") or "",
                "mapped_topic_hint": "",  # artık eşleşti, hint silinir
                "retagged": True,
            }
            if cid in existing_ids:
                ids_to_update.append(cid)
                metas_to_update.append(new_meta)
            else:
                # ChromaDB'de yok — şu an ingest edilmemiş. Insert listesine ekle.
                needs_insert.append({
                    "id": cid,
                    "text": c["text"],
                    "metadata": new_meta,
                })

            by_kazanim[new_kod] = by_kazanim.get(new_kod, 0) + 1

        by_grade[grade] = len(candidates)

        if ids_to_update:
            logger.info("Grade %s: %s update", grade, len(ids_to_update))
            if not args.dry_run:
                collection.update(ids=ids_to_update, metadatas=metas_to_update)
                total_updates += len(ids_to_update)

    if needs_insert:
        logger.info("Mevcut koleksiyonda olmayan %s chunk için embed+insert gerekiyor", len(needs_insert))
        if not args.dry_run:
            from app.services.embedder import GeminiEmbedder
            embedder = GeminiEmbedder()
            BATCH = 50
            for start in range(0, len(needs_insert), BATCH):
                batch = needs_insert[start : start + BATCH]
                logger.info("Embedding %s-%s / %s", start, start + len(batch), len(needs_insert))
                embeds = embedder.embed_many([b["text"] for b in batch])
                collection.add(
                    ids=[b["id"] for b in batch],
                    embeddings=embeds,
                    documents=[b["text"] for b in batch],
                    metadatas=[b["metadata"] for b in batch],
                )

    logger.info("Bitti. Update edilen: %s | Insert edilen: %s", total_updates, len(needs_insert))

    print("\n=== ÖZET ===")
    for g, n in sorted(by_grade.items()):
        print(f"  Grade {g}: {n} chunk yeniden etiketlendi")
    print("\nKazanım bazlı yeni atamalar:")
    for kod, n in sorted(by_kazanim.items()):
        print(f"  {kod}: {n}")
    print(f"\nToplam koleksiyon: {collection.count()}")


if __name__ == "__main__":
    main()
