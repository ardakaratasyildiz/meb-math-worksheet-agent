r"""Sözel ders (türkçe/sosyal/ingilizce) ders kitaplarını ChromaDB'ye ingest eder.

`ingest_fen_textbook.py`'nin subject-parametreli genellemesi (aynı deterministik,
LLM'siz Seçenek A mantığı): her chunk `subject` + `grade` + `tema` (curriculum ünite
adından anahtar-kelime eşleşmesi) + `content_type="textbook_concept"` ile etiketlenir.
Kazanım-seviyesi tagging YOK; olgusal/bağlamsal kritik için grade+tema+embedding yeterli.

Kaynak seçimi (bkz. knowledge_base/<Subject>/SOURCES.md):
  - Track A (BURASI): `{grade}.sinif/` altındaki İSİM DESENLİ ders kitapları
    (turkce_5_1.pdf, c1_turkce_7.pdf, sosyal_bilgiler_5_1.pdf, ingilizce_5_ders_kitabi.pdf …).
  - Track B (HARİÇ): ornek_sorular/ + sorular/ soru kitapçıkları → few_shot.py (Kanal B).
  - Hex-id dosyalar (`^[0-9a-f]{10}( \(\d\))?\.pdf`) ek/tarama → bilinçli HARİÇ.

Kullanım (PYTHONUTF8=1 önerilir — Türkçe log):
    python scripts/ingest_subject_textbook.py --subject turkce --grades 5,6 --dry-run
    python scripts/ingest_subject_textbook.py --subject turkce --grades 1,2,3,4,5,6,7,8
    python scripts/ingest_subject_textbook.py --subject sosyal --grades 5,6,7,8
    python scripts/ingest_subject_textbook.py --subject ingilizce --grades 2,5,6,7,8
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import logging
import re
import sys
from pathlib import Path

import chromadb
import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import settings  # noqa: E402
from app.services.embedder import GeminiEmbedder  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S"
)
logger = logging.getLogger("ingest_subject")

# subject → (klasör adı, curriculum modülü). fen ayrı script'te kalır (geriye-uyum).
SUBJECTS: dict[str, str] = {
    "turkce": "Turkce",
    "sosyal": "Sosyal",
    "ingilizce": "Ingilizce",
}

_WS_RE = re.compile(r"\s+")
_ANSWER_KEY_RE = re.compile(r"\b\d{1,2}\s+[A-Ea-e]\b")
# Hex-id dosya (ek/tarama; ders kitabı değil): "0049952a0f.pdf", "0049952a0f (1).pdf".
_HEX_ID_RE = re.compile(r"^[0-9a-f]{8,}( \(\d+\))?$", re.IGNORECASE)
_MAX_CHARS = 1600
_MIN_CHARS = 200


def _clean(t: str) -> str:
    return _WS_RE.sub(" ", t).strip()


def _is_noise(text: str) -> bool:
    """Cevap-anahtarı / içindekiler (nokta-dizili) / çok kısa sayfa mı?"""
    if len(text) < _MIN_CHARS:
        return True
    ak = len(_ANSWER_KEY_RE.findall(text))
    if ak >= 8 and ak * 4 > len(text.split()) // 2:
        return True
    if text.count(".") > len(text) * 0.15 or len(re.findall(r"\.{4,}", text)) >= 3:
        return True
    return False


def _split_chunk(text: str) -> list[str]:
    if len(text) <= _MAX_CHARS:
        return [text]
    parts: list[str] = []
    buf = ""
    for sent in re.split(r"(?<=[.!?])\s+", text):
        if len(buf) + len(sent) + 1 > _MAX_CHARS and buf:
            parts.append(buf.strip())
            buf = sent
        else:
            buf = f"{buf} {sent}".strip()
    if buf.strip():
        parts.append(buf.strip())
    return parts


def _discover_textbooks(subject_dir: Path, grade: int) -> list[str]:
    """`{grade}.sinif/` altındaki isim-desenli ders kitaplarını bulur (hex-id hariç)."""
    gdir = subject_dir / f"{grade}.sinif"
    if not gdir.is_dir():
        return []
    out: list[str] = []
    for p in sorted(gdir.glob("*.pdf")):
        if _HEX_ID_RE.match(p.stem):
            continue  # ek/tarama dosyası → Track A değil
        out.append(f"{grade}.sinif/{p.name}")
    return out


def _tema_matchers(curr, grade: int) -> list[tuple[str, str, set[str]]]:
    out: list[tuple[str, str, set[str]]] = []
    for u in curr.get_units_for_grade(grade):
        name = u.get("name", "")
        kws = {w.lower() for w in re.findall(r"\w+", name) if len(w) >= 4}
        out.append((u.get("unit_id", ""), name, kws))
    return out


def _match_tema(text: str, matchers: list[tuple[str, str, set[str]]]) -> str:
    low = text.lower()
    best_id, best_score = "genel", 0
    for uid, _name, kws in matchers:
        score = sum(1 for kw in kws if kw in low)
        if score > best_score:
            best_id, best_score = uid, score
    return best_id if best_score > 0 else "genel"


def _stable_id(subject: str, grade: int, source: str, idx: int, text: str) -> str:
    h = hashlib.sha1(f"{subject}|{grade}|{source}|{idx}|{text[:120]}".encode("utf-8"))
    return f"{subject}_" + h.hexdigest()[:16]


def extract_grade(subject: str, subject_dir: Path, curr, grade: int) -> list[dict]:
    matchers = _tema_matchers(curr, grade)
    chunks: list[dict] = []
    for rel in _discover_textbooks(subject_dir, grade):
        pdf = subject_dir / rel
        doc = fitz.open(pdf)
        source = f"{subject}/{rel}"
        kept = skipped = 0
        for pno in range(doc.page_count):
            raw = _clean(doc[pno].get_text("text"))
            if _is_noise(raw):
                skipped += 1
                continue
            for piece in _split_chunk(raw):
                if len(piece) < _MIN_CHARS:
                    continue
                tema = _match_tema(piece, matchers)
                chunks.append({
                    "grade": grade,
                    "topic_id": tema,
                    "kazanim_kod": "",
                    "difficulty": "orta",
                    "question_type": "textbook_concept",
                    "question": piece,
                    "answer": "",
                    "solution": "",
                    "source": source,
                    "subject": subject,
                })
                kept += 1
        logger.info("%s: %s chunk (atlanan sayfa: %s)", rel, kept, skipped)
    return chunks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", required=True, choices=sorted(SUBJECTS))
    parser.add_argument("--grades", default="1,2,3,4,5,6,7,8")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch", type=int, default=50)
    args = parser.parse_args()

    subject = args.subject
    subject_dir = ROOT / "knowledge_base" / SUBJECTS[subject]
    curr = importlib.import_module(f"app.subjects.{subject}.curriculum")
    grades = [int(g) for g in args.grades.split(",") if g.strip()]

    all_chunks: list[dict] = []
    for g in grades:
        all_chunks.extend(extract_grade(subject, subject_dir, curr, g))
    logger.info("Toplam %s chunk: %s", subject, len(all_chunks))
    dist: dict[str, int] = {}
    for c in all_chunks:
        key = f"g{c['grade']}/{c['topic_id']}"
        dist[key] = dist.get(key, 0) + 1
    logger.info("Dağılım: %s", dict(sorted(dist.items())))

    if args.dry_run:
        logger.info("--dry-run: embed/yazma yok.")
        return
    if not all_chunks:
        return

    client = chromadb.PersistentClient(path=settings.chroma_db_path)
    col = client.get_or_create_collection(
        name=settings.chroma_collection, metadata={"hnsw:space": "cosine"}
    )
    existing = set(col.get(include=[], limit=None).get("ids", []))

    new_items: list[dict] = []
    seen: set[str] = set()
    for i, c in enumerate(all_chunks):
        cid = _stable_id(subject, c["grade"], c["source"], i, c["question"])
        if cid in existing or cid in seen:
            continue
        seen.add(cid)
        c["_id"] = cid
        new_items.append(c)
    logger.info("Yeni eklenecek: %s", len(new_items))
    if not new_items:
        return

    embedder = GeminiEmbedder()
    added = 0
    for s in range(0, len(new_items), args.batch):
        chunk = new_items[s : s + args.batch]
        texts = [c["question"] for c in chunk]
        try:
            embs = embedder.embed_many(texts)
        except Exception as exc:  # noqa: BLE001
            logger.error("Embedding hatası (batch %s): %s — atlandı.", s, exc)
            continue
        col.add(
            ids=[c["_id"] for c in chunk],
            embeddings=embs,
            documents=texts,
            metadatas=[
                {
                    "grade": c["grade"],
                    "topic_id": c["topic_id"],
                    "kazanim_kod": c["kazanim_kod"],
                    "difficulty": c["difficulty"],
                    "question_type": c["question_type"],
                    "answer": c["answer"],
                    "solution": c["solution"],
                    "source": c["source"],
                    "subject": c["subject"],
                }
                for c in chunk
            ],
        )
        added += len(chunk)
        logger.info("  eklenen: %s / %s", added, len(new_items))
    logger.info("Tamamlandı. Koleksiyon toplam: %s", col.count())


if __name__ == "__main__":
    main()
