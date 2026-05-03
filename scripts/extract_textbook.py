"""MEB matematik PDF'lerinden Örnek/Etkinlik/Konu chunk'ları çıkar.

Strateji:
    1. Her sayfayı PyMuPDF ile metin olarak çıkar; sayfa offset haritası tut.
    2. Tüm metni birleştirip yapısal başlıkları regex ile bul.
    3. Her başlıktan bir sonraki başlığa (veya max lookahead) kadar olan metni
       chunk olarak çıkar.
    4. Başlıklar arası kalan paragraflar uzunsa 'textbook_concept' chunk olur.
    5. Çok kısa (<120 char) chunk'lar elenir.

Kullanım:
    python scripts/extract_textbook.py --grade 5
    python scripts/extract_textbook.py --grade 6

Çıktı: knowledge_base/processed/textbook_chunks_grade{N}.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PDFS_BY_GRADE: dict[int, list[str]] = {
    1: ["matematik_1_1.pdf", "matematik_1_2.pdf"],
    2: ["matematik_2_1.pdf", "matematik_2_2.pdf"],
    5: ["matematik_5_1.pdf", "matematik_5_2.pdf"],
    6: ["matematik_6_1.pdf", "matematik_6_2.pdf"],
    7: ["Matematik Ders Kitabı-MEB.pdf"],
}

# Sprint 5 yeni kaynak deseni — knowledge_base/ kökünden glob ile bulunur.
# Hardcoded mapping'e ekleme yapmadan, dosya adından sınıf çıkarımı.
GRADE_PATTERN_RE = re.compile(
    r"^(?P<grade>\d)\.s[ıi]n[ıi]f(?:_\d+)?\.pdf$",
    re.IGNORECASE,
)


def _discover_grade_pdfs(grade: int, base_dir: Path) -> list[Path]:
    """Sınıf için tüm PDF'leri bul: hardcoded liste + regex deseni.
    md5 hash ile duplicate'leri eler (aynı içerik farklı isimle eklenmiş olabilir)."""
    paths: list[Path] = []
    seen_hashes: set[str] = set()

    # Önce hardcoded liste — eski isimler öncelikli (ChromaDB'de zaten var)
    for fname in PDFS_BY_GRADE.get(grade, []):
        p = base_dir / fname
        if p.exists():
            h = _file_quick_hash(p)
            if h not in seen_hashes:
                seen_hashes.add(h)
                paths.append(p)

    # Sonra regex desenli yeni dosyalar
    for p in sorted(base_dir.glob("*.pdf")):
        m = GRADE_PATTERN_RE.match(p.name)
        if not m:
            continue
        try:
            if int(m.group("grade")) != grade:
                continue
        except ValueError:
            continue
        h = _file_quick_hash(p)
        if h in seen_hashes:
            logger.info("Duplicate atlandı (md5 eşleşti): %s", p.name)
            continue
        seen_hashes.add(h)
        paths.append(p)

    return paths


def _file_quick_hash(path: Path) -> str:
    """İlk 1MB md5 — duplicate dedektörü olarak yeterli, tam hash'ten 100x hızlı."""
    h = hashlib.md5()
    with path.open("rb") as f:
        h.update(f.read(1024 * 1024))
    return h.hexdigest()

MIN_CHUNK_CHARS = 120
MAX_CHUNK_CHARS = 2200
MAX_LOOKAHEAD_CHARS = 1800  # Bir Örnek/Etkinlik bloğunun üst sınırı

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("extract")


# Başlık pattern'leri — satır başında olmalı, çevresinde whitespace toleransı.
# 6/7. sınıf için BİRLİKTE YAPALIM, ÇÖZÜM, ÖĞRENELİM, YAPALIM da dahil edildi.
HEADER_RE = re.compile(
    r"^\s*(?P<kind>"
    r"Örnek|Etkinlik|Alıştırma|Problem|Uygulama|"
    r"BİRLİKTE YAPALIM|ÇÖZÜM|ÖĞRENELİM|YAPALIM|"
    r"Örnek Soru|Soru Çözümü"
    r")"
    r"(?:\s*[-–]\s*(?P<num1>\d+)|\s+(?P<num2>\d+))?"
    r"\s*[:.]?\s*$",
    re.MULTILINE,
)

TEMA_RE = re.compile(r"^\s*(\d+)\s*\.\s*TEMA\s*$", re.MULTILINE)

# Sayfa numarası gibi gözüken küçük artık metinler — temizlenecek
PAGE_NOISE_RE = re.compile(r"^\s*\d{1,3}\s*$", re.MULTILINE)


@dataclass
class Chunk:
    chunk_id: str
    grade: int
    source: str
    page_start: int
    page_end: int
    content_type: str  # textbook_example | textbook_activity | textbook_concept
    header: str | None
    text: str
    char_count: int = 0
    tema: str | None = None

    def __post_init__(self):
        self.char_count = len(self.text)


def _normalize_text(text: str) -> str:
    """Hafif temizlik — gereksiz boşlukları kırp, sayfa numarası satırlarını sil."""
    # Bazı OCR/extraction'da Türkçe karakter sapmaları (ඈ → İ) — sık görülenleri düzelt
    repl = {
        "ඈ": "i",  # bazı PDF'lerde i yerine düşüyor
        "­": "",  # soft hyphen
        "‐": "-",
    }
    for k, v in repl.items():
        text = text.replace(k, v)
    text = PAGE_NOISE_RE.sub("", text)
    # Birden fazla boş satırı tek satıra
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _build_page_map(doc: pymupdf.Document) -> tuple[str, list[tuple[int, int]]]:
    """Tüm sayfa metinlerini birleştirir; her sayfanın (start_offset, end_offset)
    bilgisini döner. Böylece bir text offset'inden hangi sayfada olduğunu çözebiliriz."""
    full = []
    page_offsets: list[tuple[int, int]] = []
    cursor = 0
    for i in range(len(doc)):
        raw = doc[i].get_text()
        cleaned = _normalize_text(raw)
        marker = f"\n[[PAGE_{i}]]\n"  # debug için, ama hesaplamada offset düzeltmesi gerekecek
        # Marker eklemiyoruz; offset hesaplamada saf metin tutacağız
        full.append(cleaned)
        start = cursor
        end = cursor + len(cleaned) + 1  # +1 = aralarına eklenecek "\n"
        page_offsets.append((start, end))
        cursor = end
    full_text = "\n".join(full)
    return full_text, page_offsets


def _offset_to_page(offset: int, page_offsets: list[tuple[int, int]]) -> int:
    for i, (s, e) in enumerate(page_offsets):
        if s <= offset < e:
            return i
    return len(page_offsets) - 1


def _detect_temas(full_text: str) -> list[tuple[int, str]]:
    """Tema başlıklarının (offset, label) listesini döner."""
    return [(m.start(), m.group(0).strip()) for m in TEMA_RE.finditer(full_text)]


def _tema_at(offset: int, temas: list[tuple[int, str]]) -> str | None:
    current = None
    for off, label in temas:
        if off <= offset:
            current = label
        else:
            break
    return current


def _stable_id(grade: int, source: str, page: int, text: str) -> str:
    h = hashlib.sha1(f"{grade}|{source}|{page}|{text[:120]}".encode("utf-8")).hexdigest()
    return f"tb_{h[:14]}"


def _slice_chunk(full_text: str, start: int, end: int) -> str:
    chunk = full_text[start:end]
    chunk = re.sub(r"\s+", " ", chunk).strip()
    return chunk


def _extract_header_chunks(
    full_text: str,
    page_offsets: list[tuple[int, int]],
    temas: list[tuple[int, str]],
    grade: int,
    source: str,
) -> tuple[list[Chunk], list[tuple[int, int]]]:
    """Örnek/Etkinlik vb. başlıklı blokları çıkarır; ayrıca işgal ettikleri
    (start, end) aralıklarını döner — concept chunking bunları atlamak için."""
    header_matches = list(HEADER_RE.finditer(full_text))
    chunks: list[Chunk] = []
    occupied: list[tuple[int, int]] = []

    for i, m in enumerate(header_matches):
        kind = m.group("kind")
        num = m.group("num1") or m.group("num2")
        header_label = f"{kind}{(' ' + num) if num else ''}"
        body_start = m.end()
        # Bir sonraki başlığa veya max lookahead'a kadar
        if i + 1 < len(header_matches):
            body_end = min(header_matches[i + 1].start(), body_start + MAX_LOOKAHEAD_CHARS)
        else:
            body_end = min(len(full_text), body_start + MAX_LOOKAHEAD_CHARS)
        text = _slice_chunk(full_text, body_start, body_end)
        if len(text) < MIN_CHUNK_CHARS:
            continue
        if len(text) > MAX_CHUNK_CHARS:
            text = text[:MAX_CHUNK_CHARS].rsplit(" ", 1)[0]
        page_start = _offset_to_page(m.start(), page_offsets)
        page_end = _offset_to_page(body_end - 1, page_offsets)
        content_type = {
            "Örnek": "textbook_example",
            "Örnek Soru": "textbook_example",
            "Soru Çözümü": "textbook_example",
            "ÇÖZÜM": "textbook_example",
            "Etkinlik": "textbook_activity",
            "BİRLİKTE YAPALIM": "textbook_activity",
            "YAPALIM": "textbook_activity",
            "ÖĞRENELİM": "textbook_concept",
            "Alıştırma": "textbook_exercise",
            "Problem": "textbook_problem",
            "Uygulama": "textbook_activity",
        }.get(kind, "textbook_example")

        chunk = Chunk(
            chunk_id=_stable_id(grade, source, page_start, text),
            grade=grade,
            source=source,
            page_start=page_start,
            page_end=page_end,
            content_type=content_type,
            header=header_label,
            text=text,
            tema=_tema_at(m.start(), temas),
        )
        chunks.append(chunk)
        occupied.append((m.start(), body_end))
    return chunks, occupied


def _extract_concept_chunks(
    full_text: str,
    occupied: list[tuple[int, int]],
    page_offsets: list[tuple[int, int]],
    temas: list[tuple[int, str]],
    grade: int,
    source: str,
) -> list[Chunk]:
    """Örnek/Etkinlik başlıklarının dışında kalan kavram/anlatım metinleri."""
    occupied = sorted(occupied)
    free_ranges: list[tuple[int, int]] = []
    cursor = 0
    for s, e in occupied:
        if s > cursor:
            free_ranges.append((cursor, s))
        cursor = max(cursor, e)
    if cursor < len(full_text):
        free_ranges.append((cursor, len(full_text)))

    chunks: list[Chunk] = []
    for s, e in free_ranges:
        segment = full_text[s:e]
        # Paragraf bazlı böl
        paragraphs = re.split(r"\n\s*\n+", segment)
        for para in paragraphs:
            text = re.sub(r"\s+", " ", para).strip()
            if len(text) < MIN_CHUNK_CHARS:
                continue
            if len(text) > MAX_CHUNK_CHARS:
                # Cümle bazlı parçala
                pieces = re.split(r"(?<=[.!?])\s+", text)
                buffer = ""
                for piece in pieces:
                    if len(buffer) + len(piece) + 1 > MAX_CHUNK_CHARS and buffer:
                        chunks.append(_make_concept_chunk(buffer, full_text, segment, s, page_offsets, temas, grade, source))
                        buffer = piece
                    else:
                        buffer = (buffer + " " + piece).strip()
                if len(buffer) >= MIN_CHUNK_CHARS:
                    chunks.append(_make_concept_chunk(buffer, full_text, segment, s, page_offsets, temas, grade, source))
            else:
                chunks.append(_make_concept_chunk(text, full_text, segment, s, page_offsets, temas, grade, source))
    return chunks


def _make_concept_chunk(
    text: str,
    full_text: str,
    segment: str,
    seg_start: int,
    page_offsets: list[tuple[int, int]],
    temas: list[tuple[int, str]],
    grade: int,
    source: str,
) -> Chunk:
    # Yaklaşık offset — segment içinde aratıp başlangıcını bul
    rel = segment.find(text[:60]) if text else 0
    abs_off = seg_start + (rel if rel >= 0 else 0)
    page_start = _offset_to_page(abs_off, page_offsets)
    page_end = page_start
    return Chunk(
        chunk_id=_stable_id(grade, source, page_start, text),
        grade=grade,
        source=source,
        page_start=page_start,
        page_end=page_end,
        content_type="textbook_concept",
        header=None,
        text=text,
        tema=_tema_at(abs_off, temas),
    )


def process_pdf(pdf_path: Path, grade: int) -> list[Chunk]:
    logger.info("Açılıyor: %s (sınıf %s)", pdf_path.name, grade)
    doc = pymupdf.open(str(pdf_path))
    full_text, page_offsets = _build_page_map(doc)
    temas = _detect_temas(full_text)
    logger.info("  → %s sayfa, %s tema, %s karakter", len(doc), len(temas), len(full_text))

    header_chunks, occupied = _extract_header_chunks(full_text, page_offsets, temas, grade, pdf_path.name)
    concept_chunks = _extract_concept_chunks(full_text, occupied, page_offsets, temas, grade, pdf_path.name)
    doc.close()

    # ID çakışması olabilir → benzersizleştir
    seen: set[str] = set()
    unique: list[Chunk] = []
    for c in header_chunks + concept_chunks:
        if c.chunk_id in seen:
            continue
        seen.add(c.chunk_id)
        unique.append(c)

    by_type: dict[str, int] = {}
    for c in unique:
        by_type[c.content_type] = by_type.get(c.content_type, 0) + 1
    logger.info("  → toplam chunk: %s | tip dağılımı: %s", len(unique), by_type)
    return unique


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--grade", type=int, required=True, choices=range(1, 8))
    args = parser.parse_args()
    grade = args.grade
    output = ROOT / "knowledge_base" / "processed" / f"textbook_chunks_grade{grade}.json"

    base_dir = ROOT / "knowledge_base"
    pdfs = _discover_grade_pdfs(grade, base_dir)
    if not pdfs:
        logger.error("Sınıf %s için PDF bulunamadı.", grade)
        return
    logger.info("Sınıf %s için %s benzersiz PDF işlenecek:", grade, len(pdfs))
    for p in pdfs:
        logger.info("  - %s", p.name)

    all_chunks: list[Chunk] = []
    for path in pdfs:
        all_chunks.extend(process_pdf(path, grade))

    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "grade": grade,
        "total_chunks": len(all_chunks),
        "chunks": [asdict(c) for c in all_chunks],
    }
    with output.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    logger.info("Yazıldı: %s (%s chunk)", output, len(all_chunks))

    # Özet
    print("\n=== ÖZET ===")
    by_type: dict[str, int] = {}
    for c in all_chunks:
        by_type[c.content_type] = by_type.get(c.content_type, 0) + 1
    for t, n in sorted(by_type.items()):
        print(f"  {t}: {n}")
    print(f"  TOPLAM: {len(all_chunks)}")


if __name__ == "__main__":
    main()
