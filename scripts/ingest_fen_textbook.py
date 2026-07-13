"""Fen ders/çalışma kitaplarını ChromaDB'ye ingest eder (subject-aware RAG — Fen).

DETERMİNİSTİK (LLM YOK — Seçenek A): her chunk `subject="fen"` + `grade` + `tema`
(Fen curriculum ünite adından anahtar-kelime eşleşmesi) ile etiketlenir. Kazanım-
seviyesi LLM tagging yapılmaz; olgusal kritik için grade+tema+embedding yeterli.

Gürültü elenir: cevap-anahtarı sayfaları ("1 B 11 C ..."), çok kısa/kapak sayfaları.
content_type="textbook_concept" → retriever.retrieve_textbook() bunları çeker.

Kullanım:
    python scripts/ingest_fen_textbook.py --grades 5,6 --dry-run
    python scripts/ingest_fen_textbook.py --grades 3,4,5,6,7,8
"""
from __future__ import annotations

import argparse
import hashlib
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
from app.subjects.fen import curriculum as fen_curr  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("ingest_fen")

FEN_DIR = ROOT / "knowledge_base" / "Fen"

# Sınıf → ingest edilecek İÇERİK dosyaları (kavram-taşıyan; hex/cevap-anahtarı/
# tarama-testi gürültü dosyaları BİLİNÇLİ dışarıda). lgs_fen (soru bankası) şimdilik
# hariç — olgusal kritik kavram metni ister, soru derlemesi değil.
FILES_BY_GRADE: dict[int, list[str]] = {
    3: ["3.sinif/3fen_calisma_kitabi_odsgm.pdf"],
    4: ["4.sinif/4fen_calisma_kitabi_odsgm.pdf"],
    5: ["5.sinif/fen_bilimleri_5_1.pdf", "5.sinif/fen_bilimleri_5_2.pdf"],
    6: ["6.sinif/fen_bilimleri_6_1.pdf", "6.sinif/fen_bilimleri_6_2.pdf"],
    7: ["7.sinif/c1_fen-bilimleri-7.pdf"],
    8: ["8.sinif/8fen_calisma_kitabi_odsgm.pdf", "8.sinif/c1_fen-bilimleri-8.pdf"],
}

_WS_RE = re.compile(r"\s+")
# Cevap anahtarı satırı: "1 B 11 C 21 D" gibi sayı-harf tekrarları.
_ANSWER_KEY_RE = re.compile(r"\b\d{1,2}\s+[A-Ea-e]\b")
_MAX_CHARS = 1600  # chunk üst sınırı (uzun sayfaları böl)
_MIN_CHARS = 200   # bundan kısa sayfa atlanır (kapak/boş)


def _clean(t: str) -> str:
    return _WS_RE.sub(" ", t).strip()


def _is_noise(text: str) -> bool:
    """Cevap-anahtarı / içindekiler (nokta-dizili) / çok kısa sayfa mı?"""
    if len(text) < _MIN_CHARS:
        return True
    ak = len(_ANSWER_KEY_RE.findall(text))
    # Yoğun "sayı-harf" örüntüsü → cevap anahtarı tablosu.
    if ak >= 8 and ak * 4 > len(text.split()) // 2:
        return True
    # İçindekiler / nokta-liderli sayfa: nokta oranı yüksek ya da çok "...." dizisi.
    if text.count(".") > len(text) * 0.15 or len(re.findall(r"\.{4,}", text)) >= 3:
        return True
    return False


def _split_chunk(text: str) -> list[str]:
    """Uzun metni cümle sınırında ~_MAX_CHARS parçalara böler."""
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


def _tema_matchers(grade: int) -> list[tuple[str, str, set[str]]]:
    """(unit_id, unit_name, anahtar-kelime seti) — chunk'ı temaya eşlemek için."""
    out: list[tuple[str, str, set[str]]] = []
    for u in fen_curr.get_units_for_grade(grade):
        name = u.get("name", "")
        kws = {w.lower() for w in re.findall(r"\w+", name) if len(w) >= 4}
        out.append((u.get("unit_id", ""), name, kws))
    return out


def _match_tema(text: str, matchers: list[tuple[str, str, set[str]]]) -> str:
    """Chunk'a en çok anahtar-kelime örtüşen temanın unit_id'si; yoksa 'genel'."""
    low = text.lower()
    best_id, best_score = "genel", 0
    for uid, _name, kws in matchers:
        score = sum(1 for kw in kws if kw in low)
        if score > best_score:
            best_id, best_score = uid, score
    return best_id if best_score > 0 else "genel"


def _stable_id(grade: int, source: str, idx: int, text: str) -> str:
    h = hashlib.sha1(f"fen|{grade}|{source}|{idx}|{text[:120]}".encode("utf-8"))
    return "fen_" + h.hexdigest()[:16]


def extract_grade(grade: int) -> list[dict]:
    matchers = _tema_matchers(grade)
    chunks: list[dict] = []
    for rel in FILES_BY_GRADE.get(grade, []):
        pdf = FEN_DIR / rel
        if not pdf.exists():
            logger.warning("Yok, atlanıyor: %s", rel)
            continue
        doc = fitz.open(pdf)
        source = f"fen/{rel}"
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
                    "kazanim_kod": "",  # Seçenek A: kazanım-seviyesi tagging yok
                    "difficulty": "orta",
                    "question_type": "textbook_concept",
                    "question": piece,
                    "answer": "",
                    "solution": "",
                    "source": source,
                    "subject": "fen",
                })
                kept += 1
        logger.info("%s: %s chunk (atlanan sayfa: %s)", rel, kept, skipped)
    return chunks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--grades", default="3,4,5,6,7,8")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch", type=int, default=50)
    args = parser.parse_args()
    grades = [int(g) for g in args.grades.split(",") if g.strip()]

    all_chunks: list[dict] = []
    for g in grades:
        all_chunks.extend(extract_grade(g))
    logger.info("Toplam Fen chunk: %s", len(all_chunks))
    # tema dağılımı
    dist: dict[str, int] = {}
    for c in all_chunks:
        key = f"g{c['grade']}/{c['topic_id']}"
        dist[key] = dist.get(key, 0) + 1
    logger.info("Dağılım (örnek): %s", dict(list(sorted(dist.items()))[:20]))

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
        cid = _stable_id(c["grade"], c["source"], i, c["question"])
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
        except Exception as exc:
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
