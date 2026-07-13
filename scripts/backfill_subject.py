"""ChromaDB'deki mevcut chunk'lara `subject` metadatası ekler (subject-aware RAG geçişi).

Mevcut koleksiyondaki tüm kayıtlar matematik (subject alanı yok). Retriever
subject-aware olunca (`where` filtresine subject eklendi) subject'siz kayıtlar
eşleşmez → math retrieval bozulurdu.

⚠️ chroma `collection.update(metadatas=...)` metadata-only güncellemede bile HNSW
segment compaction'ı tetikleyip "Failed to apply logs to the hnsw segment writer"
hatası veriyor (bu korpusta). O yüzden backfill DOĞRUDAN sqlite `embedding_metadata`
tablosuna yazılır — HNSW/vektör dizinine HİÇ dokunmaz, yalnız `where` filtresinin
okuduğu metadata satırlarını ekler. Idempotent (subject satırı olan id atlanır).

Subject kazanım kodundan türetilir (M./MAT.→matematik, FB.→fen …); mevcut korpus
tümü math olduğu için pratikte hepsi matematik.

Kullanım:
    python scripts/backfill_subject.py            # uygula
    python scripts/backfill_subject.py --dry-run  # sadece say
"""
from __future__ import annotations

import argparse
import logging
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import settings  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("backfill_subject")

# kazanım kodu prefix → ders. Mevcut kayıtlar M.*/MAT.* (matematik).
_PREFIX = [
    ("MAT.", "matematik"), ("M.", "matematik"),
    ("FB.", "fen"), ("F.", "fen"),
    ("TR.", "turkce"), ("T.", "turkce"),
    ("İTA.", "sosyal"), ("ITA.", "sosyal"), ("SOS.", "sosyal"), ("SB.", "sosyal"),
    ("ENG.", "ingilizce"),
]


def _subject_from_kod(kod: str) -> str:
    up = (kod or "").upper()
    for pfx, subj in _PREFIX:
        if up.startswith(pfx):
            return subj
    if len(up) > 1 and up[0] == "E" and up[1].isdigit():
        return "ingilizce"
    return "matematik"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    db = str(Path(settings.chroma_db_path) / "chroma.sqlite3")
    con = sqlite3.connect(db)
    cur = con.cursor()

    # subject'i olmayan embedding id'leri + kazanım koduna göre ders dağılımı
    rows = cur.execute(
        """
        SELECT em.id, COALESCE(kk.string_value, '')
        FROM embedding_metadata em
        LEFT JOIN embedding_metadata kk ON kk.id = em.id AND kk.key = 'kazanim_kod'
        WHERE em.id NOT IN (SELECT id FROM embedding_metadata WHERE key = 'subject')
        GROUP BY em.id
        """
    ).fetchall()
    by_subject: dict[str, int] = {}
    payload: list[tuple[int, str, str]] = []
    for eid, kod in rows:
        subj = _subject_from_kod(kod)
        by_subject[subj] = by_subject.get(subj, 0) + 1
        payload.append((eid, "subject", subj))

    logger.info("subject'siz id: %s | dağılım: %s", len(payload), by_subject)
    if args.dry_run:
        logger.info("--dry-run: yazılmadı.")
        con.close()
        return
    if not payload:
        logger.info("Eklenecek yok (hepsinde subject var).")
        con.close()
        return

    cur.executemany(
        "INSERT INTO embedding_metadata (id, key, string_value) VALUES (?, ?, ?)",
        payload,
    )
    con.commit()
    missing = cur.execute(
        "SELECT COUNT(DISTINCT id) FROM embedding_metadata "
        "WHERE id NOT IN (SELECT id FROM embedding_metadata WHERE key='subject')"
    ).fetchone()[0]
    con.close()
    logger.info("Tamamlandı. subject'siz kalan id: %s (0 olmalı)", missing)


if __name__ == "__main__":
    main()
