"""Etiketlenmiş ders kitabı chunk'larını ChromaDB'ye yükler.

Kullanım:
    python scripts/ingest_textbook.py --grade 5
    python scripts/ingest_textbook.py --grade 6 --dry-run

Kaynak: knowledge_base/processed/textbook_chunks_grade{N}_tagged.json
Hedef koleksiyon: settings.chroma_collection (mevcut sentetik+manuel kayıtların yanına eklenir)

Filtreleme kuralları:
    - tagged=false       → atla
    - content_quality=unusable → atla
    - confidence=low ve kazanim_kod_llm=null → atla (gürültü)

content_type metadata değeri kayıt zamanında karara bağlanır:
    - kazanim_kod_llm var: chunk'ın orijinal content_type'ı korunur (textbook_example/...)
    - kazanim_kod_llm yok ama mapped_topic_hint var: 'curriculum_expansion'

Embedding: GeminiEmbedder (gemini-embedding-001).
Idempotent: stable id (sha1) ile mevcut kayıtlar atlanır.
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
from app.services.embedder import GeminiEmbedder  # noqa: E402

PROCESSED_DIR = ROOT / "knowledge_base" / "processed"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("ingest_tb")


def _kazanim_to_topic_map(grade: int) -> dict[str, str]:
    out: dict[str, str] = {}
    for tid, t in CURRICULUM[grade].items():
        for k in t["kazanimlar"]:
            out[k["kod"]] = tid
    return out


def _should_ingest(chunk: dict) -> bool:
    if not chunk.get("tagged"):
        return False
    quality = chunk.get("content_quality")
    if quality == "unusable":
        return False
    confidence = chunk.get("confidence")
    has_kod = bool(chunk.get("kazanim_kod_llm"))
    if confidence == "low" and not has_kod:
        return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--grade", type=int, required=True, help="Sınıf (1-7)")
    parser.add_argument("--dry-run", action="store_true", help="Sadece istatistik yaz, ChromaDB'ye yazma")
    parser.add_argument("--batch", type=int, default=50, help="Embedding batch boyutu")
    args = parser.parse_args()
    grade = args.grade

    input_path = PROCESSED_DIR / f"textbook_chunks_grade{grade}_tagged.json"
    if not input_path.exists():
        raise SystemExit(f"Tagged dosya yok: {input_path}")

    data = json.load(input_path.open(encoding="utf-8"))
    all_chunks = data["chunks"]
    logger.info("Toplam tagged input: %s", len(all_chunks))

    candidates = [c for c in all_chunks if _should_ingest(c)]
    logger.info(
        "Filtreleme sonrası: %s (atlanan: %s)",
        len(candidates), len(all_chunks) - len(candidates),
    )

    # İstatistik
    stats = {"by_content_type": {}, "by_kazanim": {}, "by_quality": {}, "by_confidence": {}}
    for c in candidates:
        ct = "curriculum_expansion" if not c.get("kazanim_kod_llm") else c["content_type"]
        stats["by_content_type"][ct] = stats["by_content_type"].get(ct, 0) + 1
        kod = c.get("kazanim_kod_llm") or "__UNMAPPED__"
        stats["by_kazanim"][kod] = stats["by_kazanim"].get(kod, 0) + 1
        if c.get("content_quality"):
            stats["by_quality"][c["content_quality"]] = stats["by_quality"].get(c["content_quality"], 0) + 1
        if c.get("confidence"):
            stats["by_confidence"][c["confidence"]] = stats["by_confidence"].get(c["confidence"], 0) + 1

    print("\n=== INGEST PLAN ===")
    for k, d in stats.items():
        print(f"\n{k}:")
        for kk, v in sorted(d.items()):
            print(f"  {kk}: {v}")

    if args.dry_run:
        logger.info("Dry-run: ChromaDB'ye yazılmadı.")
        return

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
    logger.info("Koleksiyonda mevcut kayıt: %s", len(existing_ids))

    new_items: list[dict] = []
    kod2tid = _kazanim_to_topic_map(grade)
    for c in candidates:
        if c["chunk_id"] in existing_ids:
            continue
        kod = c.get("kazanim_kod_llm")
        topic_id = kod2tid.get(kod, "")  # eşleşmeyenlerde boş kalır
        ct = "curriculum_expansion" if not kod else c["content_type"]
        new_items.append({
            "id": c["chunk_id"],
            "text": c["text"],
            "metadata": {
                "grade": c["grade"],
                "topic_id": topic_id,
                "kazanim_kod": kod or "",
                "kazanim_kod_present": bool(kod),
                "difficulty": "orta",  # ders kitabı içerikleri zorluk-agnostic — orta varsayılır
                "question_type": c["content_type"],  # textbook_example/activity/concept/...
                "answer": "",  # ders kitabı chunk'ı, cevap yok
                "solution": "",
                "source": f"textbook/{c['source']}",
                "content_type": ct,
                "page_start": c["page_start"],
                "page_end": c["page_end"],
                "header": c.get("header") or "",
                "tema": c.get("tema") or "",
                "confidence": c.get("confidence") or "",
                "content_quality": c.get("content_quality") or "",
                "mapped_topic_hint": c.get("mapped_topic_hint") or "",
            },
        })

    logger.info("Yeni eklenecek: %s", len(new_items))
    if not new_items:
        return

    embedder = GeminiEmbedder()
    total = len(new_items)
    added = 0
    for start in range(0, total, args.batch):
        chunk_batch = new_items[start : start + args.batch]
        texts = [c["text"] for c in chunk_batch]
        logger.info("Embedding batch %s-%s / %s ...", start, start + len(chunk_batch), total)
        try:
            embeddings = embedder.embed_many(texts)
        except Exception as exc:
            logger.error("Embedding başarısız (atlandı): %s", exc)
            continue
        collection.add(
            ids=[c["id"] for c in chunk_batch],
            embeddings=embeddings,
            documents=texts,
            metadatas=[c["metadata"] for c in chunk_batch],
        )
        added += len(chunk_batch)
        logger.info("  → kümülatif: %s / %s", added, total)

    logger.info("Tamamlandı. Toplam koleksiyon: %s", collection.count())


if __name__ == "__main__":
    main()
