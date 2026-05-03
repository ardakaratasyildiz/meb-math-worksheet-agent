"""Faz 0 keşif — her PDF için metin çıkarılabilirlik, sample metin, TOC ve özellikleri raporla.

Çıktı: knowledge_base/processed/discovery_report.json
"""
from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "knowledge_base"
OUTPUT = ROOT / "knowledge_base" / "processed" / "discovery_report.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("discover")


# Heuristic sınıf tespiti — özel isimli dosyalar için sabit eşleşmeler
GRADE_HINTS: dict[str, int] = {
    "3.Sinif-Matematik-Ders-Kitabi-MEB-pdf.pdf": 3,
    "4.Sinif-Matematik-Ders-Kitabi-MEB-pdf.pdf": 4,
    "matematik_1_1.pdf": 1,
    "matematik_1_2.pdf": 1,
    "matematik_2_1.pdf": 2,
    "matematik_2_2.pdf": 2,
    "matematik_5_1.pdf": 5,
    "matematik_5_2.pdf": 5,
    "matematik_6_1.pdf": 6,
    "matematik_6_2.pdf": 6,
    "Matematik Ders Kitabı-MEB.pdf": 7,  # 7. sınıf test kitabı (TOC incelendi)
}

# Sprint 5 yeni kaynaklar: "X.sinif.pdf" veya "X.sinif_N.pdf" deseni → sınıfı dosyadan çıkar
GRADE_FROM_PATTERN_RE = re.compile(
    r"^(?P<grade>\d)\.s[ıi]n[ıi]f(?:_\d+)?\.pdf$",
    re.IGNORECASE,
)


def detect_grade(filename: str) -> int | None:
    """Önce sabit eşlemeye, sonra regex deseni."""
    if filename in GRADE_HINTS:
        return GRADE_HINTS[filename]
    m = GRADE_FROM_PATTERN_RE.match(filename)
    if m:
        try:
            g = int(m.group("grade"))
            if 1 <= g <= 7:
                return g
        except ValueError:
            return None
    return None


MATH_SYMBOL_RE = re.compile(r"[×÷±≤≥≠≈π√∞°∠∆¬∀∃∑∏∫½⅓⅔¼¾⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞]")
HEADER_PATTERNS = [
    re.compile(r"^\s*(\d+\.\s*ÜNİTE|\d+\.\s*BÖLÜM)", re.M),
    re.compile(r"^\s*Kazanım\s*[:：]", re.M | re.I),
    re.compile(r"^\s*Örnek\s+\d+", re.M),
    re.compile(r"^\s*Etkinlik(\s+\d+)?\s*[:：]?", re.M),
    re.compile(r"^\s*Alıştırma(lar)?", re.M | re.I),
    re.compile(r"^\s*Problem(ler)?\s*[:：]", re.M),
]


def _detect_toc_pages(doc: pymupdf.Document, max_check: int = 25) -> list[int]:
    """İçindekiler tablosu barındıran sayfaları bul."""
    candidates = []
    for p in range(min(max_check, len(doc))):
        txt = doc[p].get_text()
        if "İÇİNDEKİLER" in txt.upper() or re.search(r"\.\.\.{3,}\s*\d+", txt):
            candidates.append(p)
    return candidates


def _sample_pages(doc: pymupdf.Document, n: int = 6) -> list[int]:
    total = len(doc)
    if total <= n:
        return list(range(total))
    # %10, %25, %40, %55, %70, %85 gibi düzenli
    import random
    rng = random.Random(42)
    pages = sorted(rng.sample(range(total), n))
    return pages


def _count_headers(text: str) -> dict[str, int]:
    counts = {}
    for i, pat in enumerate(HEADER_PATTERNS):
        name = ["unite_bolum", "kazanim", "ornek", "etkinlik", "alistirma", "problem"][i]
        counts[name] = len(pat.findall(text))
    return counts


def analyze_pdf(path: Path) -> dict:
    logger.info("İşleniyor: %s", path.name)
    doc = pymupdf.open(str(path))
    total_pages = len(doc)

    # Örneklem bazlı metin + imge sayımı
    sample_idx = _sample_pages(doc, n=10)
    text_chars = 0
    image_count = 0
    math_syms = 0
    header_counts_total: dict[str, int] = {}
    full_sample_text = ""
    for i in sample_idx:
        page = doc[i]
        t = page.get_text().strip()
        text_chars += len(t)
        image_count += len(page.get_images())
        math_syms += len(MATH_SYMBOL_RE.findall(t))
        full_sample_text += "\n" + t
        hc = _count_headers(t)
        for k, v in hc.items():
            header_counts_total[k] = header_counts_total.get(k, 0) + v

    avg_text = text_chars / len(sample_idx)
    avg_images = image_count / len(sample_idx)
    is_scanned = avg_text < 50

    # TOC — hem PyMuPDF outline hem de İçindekiler sayfası
    outline_toc = doc.get_toc()
    toc_pages = _detect_toc_pages(doc)

    # İlk sayfalardan (0-30) Kazanım/Ünite başlıkları — kazanım kodlarını yakalamak
    first_pages_text = ""
    for i in range(min(30, total_pages)):
        first_pages_text += doc[i].get_text() + "\n"

    # MEB kazanım kodu regex (M.X.X.X veya M.X.X)
    kazanim_code_matches = re.findall(r"M\.\d\.\d+(?:\.\d+)?", first_pages_text)

    # İlk sayfa kapak metni
    sample_txt_for_report = ""
    for i in sample_idx[:3]:
        t = doc[i].get_text().strip()
        if t:
            sample_txt_for_report += f"[sayfa {i}] {t[:300]}\n---\n"

    report = {
        "filename": path.name,
        "file_size_mb": round(path.stat().st_size / 1024 / 1024, 1),
        "total_pages": total_pages,
        "assumed_grade": detect_grade(path.name),
        "extraction_status": "scanned_ocr_required" if is_scanned else "text_embedded",
        "avg_text_chars_per_page": round(avg_text, 0),
        "avg_images_per_page": round(avg_images, 1),
        "math_symbols_in_sample": math_syms,
        "kazanim_codes_found_in_first_30_pages": sorted(set(kazanim_code_matches)),
        "header_hint_counts": header_counts_total,
        "pymupdf_outline_entries": len(outline_toc),
        "pymupdf_outline_sample": outline_toc[:5],
        "toc_candidate_pages": toc_pages[:5],
        "sample_text_excerpt": sample_txt_for_report[:800],
    }
    doc.close()
    return report


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--grade", type=int, default=None,
        help="Sadece bu sınıfa ait PDF'leri analiz et (1-7). Boşsa hepsi.",
    )
    parser.add_argument(
        "--pattern", type=str, default=None,
        help="Glob pattern (örn '1.sinif_*.pdf'). --grade ile birlikte kullanılabilir.",
    )
    args = parser.parse_args()

    if args.pattern:
        pdfs = sorted(PDF_DIR.glob(args.pattern))
    else:
        pdfs = sorted(PDF_DIR.glob("*.pdf"))
    if args.grade is not None:
        pdfs = [p for p in pdfs if detect_grade(p.name) == args.grade]
    logger.info("%s PDF bulundu", len(pdfs))

    reports = []
    for pdf in pdfs:
        try:
            reports.append(analyze_pdf(pdf))
        except Exception as exc:
            logger.exception("HATA %s: %s", pdf.name, exc)
            reports.append({"filename": pdf.name, "error": str(exc)})

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8") as f:
        json.dump({"reports": reports}, f, ensure_ascii=False, indent=2)
    logger.info("Rapor: %s", OUTPUT)

    # Kısa özet
    print("\n=== ÖZET ===")
    for r in reports:
        if "error" in r:
            print(f"{r['filename']}: HATA {r['error']}")
            continue
        status = "✓ METİN" if r["extraction_status"] == "text_embedded" else "✗ OCR GEREK"
        print(
            f"[{r['assumed_grade']}.sınıf] {r['filename']:<50} "
            f"{r['total_pages']}s | {status} | "
            f"ort.metin {r['avg_text_chars_per_page']:.0f} | "
            f"outline {r['pymupdf_outline_entries']} | "
            f"toc_sayfa {len(r['toc_candidate_pages'])} | "
            f"örnek/etkinlik/kazanım/alıştırma hint "
            f"O:{r['header_hint_counts'].get('ornek', 0)} "
            f"E:{r['header_hint_counts'].get('etkinlik', 0)} "
            f"K:{r['header_hint_counts'].get('kazanim', 0)} "
            f"A:{r['header_hint_counts'].get('alistirma', 0)}"
        )


if __name__ == "__main__":
    main()
