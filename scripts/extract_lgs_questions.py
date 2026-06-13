"""LGS ve yazılı sınav PDF'lerinden yapısal MCQ Soru+Cevap çıkarır.

Strateji:
  1. Manifest'ten `track="lgs"` ve `skip` olmayan PDF'leri seç.
  2. Her PDF'i iki geçişte işle:
       a) Cevap anahtarı (answer key) sayfalarını tespit et (scan).
       b) Soru sayfalarını görüntüye çevirip cevap anahtarıyla birlikte
          Gemini Flash'a ver → Pydantic MCQQuestion listesi döndür.
  3. Görsel sorular (has_visual=True) için ikinci bir Gemini çağrısı:
       Soruyu yeniden üretirken görseli inline <svg> veya Markdown tabloya çevir.
  4. Hata veren / çevrilemeyen görseller → lgs_visual_review.json kuyruğuna.
  5. Başarılı tüm sorular → lgs_examples.json (few-shot şeması ile uyumlu).

Kullanım:
    python scripts/extract_lgs_questions.py
    python scripts/extract_lgs_questions.py --limit 3          # test: ilk 3 PDF
    python scripts/extract_lgs_questions.py --skip-visual      # görsel dönüşümü atla
    python scripts/extract_lgs_questions.py --dry-run          # yazma, sadece say

Çıktılar:
    knowledge_base/processed/lgs_examples.json       (few-shot şeması)
    knowledge_base/processed/lgs_visual_review.json  (elle değerlendirme kuyruğu)

Resumable: lgs_examples.json'daki mevcut kayıtlar stable_id ile atlanır.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import logging
import re
import time
from pathlib import Path

import pymupdf
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel, Field

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import settings  # noqa: E402

PROCESSED_DIR = ROOT / "knowledge_base" / "processed"
GRADE8_DIR = ROOT / "knowledge_base" / "8.Sınıf"
MANIFEST_PATH = GRADE8_DIR / "manifest.json"

LGS_OUTPUT = PROCESSED_DIR / "lgs_examples.json"
REVIEW_OUTPUT = PROCESSED_DIR / "lgs_visual_review.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("extract_lgs")

# ─── Sabitler ───────────────────────────────────────────────────────────────
RENDER_DPI = 150  # görüntü kalitesi — yeterli + hızlı
MAX_PAGES_PER_CALL = 4  # bir Gemini çağrısına gönderilen sayfa sayısı
BATCH_DELAY = 1.0  # Flash rate-limit için batch arası bekleme (sn)
ANSWER_KEY_MARKERS = re.compile(
    r"(?i)(cevap\s+anahtar|yanıt\s+anahtar|doğru\s+yanıt|cevaplar|CEVAP)",
    re.UNICODE,
)


# ─── Pydantic şemaları ───────────────────────────────────────────────────────

class MCQOption(BaseModel):
    label: str = Field(description="Şık harfi: A, B, C veya D")
    text: str = Field(description="Şık metni")


class MCQQuestion(BaseModel):
    question_no: int | None = Field(default=None, description="PDF'deki soru numarası")
    stem: str = Field(description="Soru kökü (kısa senaryo dahil)")
    options: list[MCQOption] = Field(description="A, B, C, D şıkları")
    correct_answer: str = Field(description="Doğru şık harfi: A, B, C veya D")
    solution: str = Field(description="Kısa açıklama / çözüm yolu (1-2 cümle)")
    kazanim_kod: str | None = Field(
        default=None,
        description="Varsa MEB kazanım kodu (M.8.x.y). Belirsizse null.",
    )
    difficulty: str = Field(
        default="orta",
        description="'kolay' | 'orta' | 'zor' — LGS sorularının büyük çoğunluğu 'orta'",
    )
    has_visual: bool = Field(
        default=False,
        description="True: soruda şekil/grafik/tablo var (görseli ihtiyacı var).",
    )
    visual_type: str | None = Field(
        default=None,
        description="'geometri' | 'grafik' | 'tablo' | 'desen' | null",
    )
    skip_reason: str | None = Field(
        default=None,
        description="Çıkarılamadıysa neden (örn 'görsel anlaşılamadı', 'sayfa okunamadı'). Aksi null.",
    )


class MCQBatch(BaseModel):
    questions: list[MCQQuestion]


class SVGQuestion(BaseModel):
    stem_with_visual: str = Field(
        description=(
            "Soru kökü, ardından görseli temsil eden inline <svg>...</svg> "
            "VEYA Markdown tablosu (tablo soruları için). "
            "SVG: viewBox='0 0 W H' xmlns='http://www.w3.org/2000/svg' ile başlamalı. "
            "Tablo: GFM Markdown | hücre | ... formatında."
        )
    )
    question_type: str = Field(
        description="'gorsel_geometri' | 'grafik_okuma' | 'tablo_sorusu' | 'oruntu_sekil'"
    )
    reproduced: bool = Field(
        description="True: görsel başarıyla yeniden üretildi. False: atlansın."
    )
    skip_reason: str | None = Field(
        default=None,
        description="reproduced=False ise neden (örn 'fotoğraf içeriyor', 'çok karmaşık şekil').",
    )


# ─── Yardımcılar ────────────────────────────────────────────────────────────

def _stable_id(grade: int, source: str, q_no: int | None, stem: str) -> str:
    key = f"{grade}|{source}|{q_no}|{stem[:80]}"
    return "lgs_" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:14]


def _page_to_base64(page: pymupdf.Page, dpi: int = RENDER_DPI) -> str:
    mat = pymupdf.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat, colorspace=pymupdf.csRGB)
    return base64.b64encode(pix.tobytes("png")).decode("utf-8")


def _detect_answer_key_pages(doc: pymupdf.Document) -> set[int]:
    """Cevap anahtarı sayfalarını tespit et."""
    ans_pages: set[int] = set()
    for i in range(len(doc)):
        text = doc[i].get_text()
        if ANSWER_KEY_MARKERS.search(text):
            ans_pages.add(i)
    return ans_pages


def _extract_answer_map(doc: pymupdf.Document, ans_pages: set[int]) -> dict[int, str]:
    """Cevap anahtarı sayfalarından soru_no → doğru_şık haritası çıkar."""
    ans_map: dict[int, str] = {}
    ANS_RE = re.compile(r"(?:(\d{1,2})[\s.)\-]+([A-D]))", re.IGNORECASE)
    for page_idx in sorted(ans_pages):
        text = doc[page_idx].get_text()
        for m in ANS_RE.finditer(text):
            try:
                no = int(m.group(1))
                ans_map[no] = m.group(2).upper()
            except ValueError:
                pass
    return ans_map


def _call_with_backoff(
    fn,
    max_attempts: int = 3,
    base_delay: float = 2.0,
):
    last_exc = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except genai_errors.ServerError as exc:
            last_exc = exc
            code = getattr(exc, "code", None)
            if code not in (429, 500, 502, 503, 504) or attempt == max_attempts:
                raise
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning("API hata %s (deneme %s/%s); %.1fs sonra retry", code, attempt, max_attempts, delay)
            time.sleep(delay)
        except Exception as exc:
            raise
    raise RuntimeError(f"Tüm denemeler başarısız: {last_exc}")


# ─── Gemini çağrıları ────────────────────────────────────────────────────────

EXTRACTION_SYSTEM = """Sen matematik sınav sorusu çıkarma uzmanısın.
PDF sayfalarında gördüğün Türkçe matematik sorularını yapısal MCQ formatına dönüştür.

Kurallar:
1. Her soru için stem (kök), 4 şık (A-D), doğru cevap, kısa çözüm, kazanım kodu (varsa).
2. Doğru cevap: cevap anahtarından al. Anahtarda yoksa en makul şıkkı seç + solution'da belirt.
3. difficulty: LGS soruları çoğunlukla 'orta'. Bilgi gerektiren ise 'kolay', çok adımlı ise 'zor'.
4. has_visual=True: soruda şekil / grafik / tablo var.
   visual_type: 'geometri' | 'grafik' | 'tablo' | 'desen'
5. Okunaksız, yarım kalmış ya da görsel OLMADAN anlaşılmayan sorular: skip_reason doldur.
6. ASLA soru uydurmaca. Sayfada yoksa ekleme."""

SVG_SYSTEM = """Sen matematiksel görsel dönüştürme uzmanısın.
Verilen LGS sorusundaki görseli sisteme uygun inline formata çevir.

Format kuralları:
- Geometri şekli → inline <svg viewBox="0 0 W H" xmlns="http://www.w3.org/2000/svg">...</svg>
  * Şekli, ölçü etiketlerini, açı işaretlerini, harf etiketlerini dahil et.
  * Düz çizgiler için <line>, çokgen için <polygon>, çember için <circle>, metin için <text>.
  * viewBox: içeriği tam sığdıracak boyut. Kenar payı 10px.
- Grafik (sütun/çizgi/pasta) → <svg> ile temsili grafik.
- Tablo → GFM Markdown: | Sütun1 | Sütun2 | ... ile başlayan tablo.
- Desen/örüntü → Unicode semboller veya <svg>.

reproduced=False koşulları:
  - Fotoğraf/gerçek nesne görüntüsü (şekil değil)
  - Çok karmaşık, sayfada 20+ nesne içeren şekil
  - Metinle tam ifade edilebilir (aslında görsele gerek yok)"""


def _extract_questions_from_pages(
    client: genai.Client,
    page_images: list[str],  # base64 PNG listesi
    answer_map: dict[int, str],
    source_name: str,
) -> list[MCQQuestion]:
    """Birden fazla sayfayı Gemini Flash'a gönderip MCQ listesi al."""
    # Cevap anahtarını prompt'a ekle
    ans_text = ""
    if answer_map:
        pairs = ", ".join(f"{n}→{a}" for n, a in sorted(answer_map.items()))
        ans_text = f"\nCEVAP ANAHTARI: {pairs}\n"

    prompt_parts: list = [
        f"Kaynak: {source_name}{ans_text}\nBu sayfadaki tüm matematik sorularını çıkar:"
    ]
    for img_b64 in page_images:
        prompt_parts.append(
            types.Part.from_bytes(
                data=base64.b64decode(img_b64),
                mime_type="image/png",
            )
        )

    config = types.GenerateContentConfig(
        system_instruction=EXTRACTION_SYSTEM,
        temperature=0.1,
        response_mime_type="application/json",
        response_schema=MCQBatch,
    )

    def _call():
        return client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt_parts,
            config=config,
        )

    response = _call_with_backoff(_call)
    parsed = getattr(response, "parsed", None)
    if isinstance(parsed, MCQBatch):
        return parsed.questions
    return MCQBatch.model_validate_json(response.text).questions


def _reproduce_visual(
    client: genai.Client,
    question: MCQQuestion,
    page_image: str,  # base64 PNG — sorunun bulunduğu sayfa
) -> SVGQuestion | None:
    """Görsel sorunun görselini inline SVG/Markdown'a çevir."""
    prompt_parts = [
        f"Soru: {question.stem}\n\nBu sorudaki görseli (şekil/grafik/tablo) inline formata çevir:",
        types.Part.from_bytes(
            data=base64.b64decode(page_image),
            mime_type="image/png",
        ),
    ]
    config = types.GenerateContentConfig(
        system_instruction=SVG_SYSTEM,
        temperature=0.2,
        response_mime_type="application/json",
        response_schema=SVGQuestion,
    )

    def _call():
        return client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt_parts,
            config=config,
        )

    try:
        response = _call_with_backoff(_call)
        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, SVGQuestion):
            return parsed
        return SVGQuestion.model_validate_json(response.text)
    except Exception as exc:
        logger.warning("SVG dönüşüm hatası: %s", exc)
        return None


# ─── Ana işleme ──────────────────────────────────────────────────────────────

def _load_existing_ids(output_path: Path) -> set[str]:
    if not output_path.exists():
        return set()
    data = json.loads(output_path.read_text(encoding="utf-8"))
    return {e["id"] for e in data.get("examples", [])}


def _save_examples(examples: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps({"examples": examples}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _save_review(review_items: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps({"review_queue": review_items}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def process_pdf(
    pdf_path: Path,
    client: genai.Client,
    existing_ids: set[str],
    skip_visual: bool = False,
) -> tuple[list[dict], list[dict]]:
    """Tek bir LGS/yazılı PDF'i işle. (examples, review_items) döndür."""
    logger.info("İşleniyor: %s", pdf_path.name)
    doc = pymupdf.open(str(pdf_path))
    n_pages = len(doc)

    # Cevap anahtarı sayfaları
    ans_pages = _detect_answer_key_pages(doc)
    answer_map = _extract_answer_map(doc, ans_pages)
    logger.info("  %d sayfa | %d cevap anahtarı sayfası | %d cevap eşleşti",
                n_pages, len(ans_pages), len(answer_map))

    # Soru sayfaları = cevap anahtarı olmayan sayfalar
    question_pages = [i for i in range(n_pages) if i not in ans_pages]

    examples: list[dict] = []
    review_items: list[dict] = []

    # Batch'lere böl
    batches = [
        question_pages[i: i + MAX_PAGES_PER_CALL]
        for i in range(0, len(question_pages), MAX_PAGES_PER_CALL)
    ]

    # Sayfa → base64 cache (birden fazla batch aynı sayfayı kullanabilir)
    page_cache: dict[int, str] = {}

    for b_idx, batch_pages in enumerate(batches):
        logger.info("  Batch %d/%d (sayfa %s)...", b_idx + 1, len(batches),
                    [p + 1 for p in batch_pages])

        # Sayfaları render et
        page_images: list[str] = []
        for pidx in batch_pages:
            if pidx not in page_cache:
                page_cache[pidx] = _page_to_base64(doc[pidx])
            page_images.append(page_cache[pidx])

        try:
            questions = _extract_questions_from_pages(
                client, page_images, answer_map, pdf_path.name
            )
        except Exception as exc:
            logger.error("  Batch %d başarısız: %s", b_idx + 1, exc)
            time.sleep(BATCH_DELAY * 2)
            continue

        logger.info("  → %d soru çıkarıldı", len(questions))

        for q in questions:
            # Atlama kararı
            if q.skip_reason:
                review_items.append({
                    "source": pdf_path.name,
                    "question_no": q.question_no,
                    "stem_preview": q.stem[:120],
                    "skip_reason": q.skip_reason,
                })
                continue

            if not q.stem or not q.options or not q.correct_answer:
                continue  # eksik veri

            # Stable ID
            stable_id = _stable_id(8, pdf_path.name, q.question_no, q.stem)
            if stable_id in existing_ids:
                continue  # zaten var

            # Görsel işleme
            stem_final = q.stem
            question_type = "coktan_secmeli"

            if q.has_visual and not skip_visual and q.visual_type:
                # Görsel hangi sayfada? batch içindeki ilk sayfayı kullan (yeterince doğru)
                page_img = page_images[0]
                svg_result = _reproduce_visual(client, q, page_img)

                if svg_result and svg_result.reproduced:
                    stem_final = svg_result.stem_with_visual
                    question_type = svg_result.question_type
                    logger.info("    ✓ Görsel dönüştürüldü: %s (tip: %s)",
                                q.question_no, svg_result.question_type)
                else:
                    reason = (svg_result.skip_reason if svg_result else "SVG çağrısı başarısız")
                    logger.info("    ✗ Görsel atlandı (#%s): %s", q.question_no, reason)
                    review_items.append({
                        "source": pdf_path.name,
                        "question_no": q.question_no,
                        "stem_preview": q.stem[:120],
                        "visual_type": q.visual_type,
                        "skip_reason": reason or "görsel yeniden üretilemedi",
                    })
                    # Görselsiz metni koru — konu bağlamı olarak işe yarar
                    stem_final = q.stem

            # few-shot format
            answer_text = q.correct_answer
            # Şıktan tam metni bul
            opt_map = {o.label.upper(): o.text for o in q.options}
            answer_full = f"{q.correct_answer}) {opt_map.get(q.correct_answer.upper(), '')}"

            example = {
                "id": stable_id,
                "grade": 8,
                "topic_id": "",  # ingest sırasında kazanım_kodu → topic_id haritasından doldurulacak
                "kazanim_kod": q.kazanim_kod or "",
                "difficulty": q.difficulty,
                "question_type": question_type,
                "question": stem_final + "\n\n" + "\n".join(
                    f"{o.label}) {o.text}" for o in q.options
                ),
                "answer": answer_full,
                "solution": q.solution,
                "source": f"lgs/{pdf_path.name}",
            }
            examples.append(example)
            existing_ids.add(stable_id)

        time.sleep(BATCH_DELAY)

    doc.close()
    logger.info("  → %d örnek eklendi | %d review kuyruğuna alındı",
                len(examples), len(review_items))
    return examples, review_items


# ─── main ────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Test: işlenecek max PDF sayısı")
    parser.add_argument("--skip-visual", action="store_true", help="Görsel dönüşümünü atla")
    parser.add_argument("--dry-run", action="store_true", help="Dosyaya yazma, sadece say")
    parser.add_argument(
        "--pdf", type=str, default=None,
        help="Tek bir PDF işle (manifest'teki dosya adı)"
    )
    args = parser.parse_args()

    if not settings.gemini_api_key:
        raise SystemExit("GEMINI_API_KEY .env'de yok.")

    # Manifest'ten LGS PDF'lerini al
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    lgs_files = [
        e["file"] for e in manifest.get("files", [])
        if e.get("track") == "lgs" and not e.get("skip")
    ]

    if args.pdf:
        lgs_files = [f for f in lgs_files if f == args.pdf]
        if not lgs_files:
            raise SystemExit(f"'{args.pdf}' manifest'te lgs track'inde bulunamadı.")
    elif args.limit:
        lgs_files = lgs_files[: args.limit]

    logger.info("İşlenecek LGS PDF sayısı: %d", len(lgs_files))
    for f in lgs_files:
        logger.info("  - %s", f)

    # Mevcut kayıtları yükle (resumable)
    existing_ids = _load_existing_ids(LGS_OUTPUT)
    logger.info("Mevcut lgs_examples kayıt: %d", len(existing_ids))

    existing_examples: list[dict] = []
    if LGS_OUTPUT.exists():
        existing_examples = json.loads(LGS_OUTPUT.read_text(encoding="utf-8")).get("examples", [])

    existing_review: list[dict] = []
    if REVIEW_OUTPUT.exists():
        existing_review = json.loads(REVIEW_OUTPUT.read_text(encoding="utf-8")).get("review_queue", [])

    client = genai.Client(api_key=settings.gemini_api_key)

    all_new_examples: list[dict] = []
    all_review: list[dict] = list(existing_review)

    for fname in lgs_files:
        pdf_path = GRADE8_DIR / fname
        if not pdf_path.exists():
            logger.warning("PDF bulunamadı: %s", pdf_path)
            continue

        new_examples, review_items = process_pdf(
            pdf_path,
            client,
            existing_ids=existing_ids,
            skip_visual=args.skip_visual,
        )
        all_new_examples.extend(new_examples)
        all_review.extend(review_items)

        # Her PDF sonrası ara kaydet
        if not args.dry_run:
            _save_examples(existing_examples + all_new_examples, LGS_OUTPUT)
            _save_review(all_review, REVIEW_OUTPUT)
            logger.info("Ara kayıt: %d örnek", len(existing_examples) + len(all_new_examples))

    # Özet
    total = len(existing_examples) + len(all_new_examples)
    print("\n=== ÖZET ===")
    print(f"Yeni eklenen örnek : {len(all_new_examples)}")
    print(f"Toplam örnek       : {total}")
    print(f"Review kuyruğu     : {len(all_review)} (elle değerlendirme)")

    if args.dry_run:
        print("(dry-run: dosyaya yazılmadı)")
        return

    # Tip dağılımı
    by_type: dict[str, int] = {}
    by_kaz: dict[str, int] = {}
    for e in all_new_examples:
        t = e.get("question_type", "?")
        by_type[t] = by_type.get(t, 0) + 1
        k = e.get("kazanim_kod") or "__UNMAPPED__"
        by_kaz[k] = by_kaz.get(k, 0) + 1

    print("\nYeni örnek tip dağılımı:")
    for t, n in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {t}: {n}")
    print("\nKazanım dağılımı (top-10):")
    for k, n in sorted(by_kaz.items(), key=lambda x: -x[1])[:10]:
        print(f"  {k}: {n}")

    print(f"\nÇıktılar:\n  {LGS_OUTPUT}\n  {REVIEW_OUTPUT}")
    print("\nSonraki adım: python scripts/ingest_to_chroma.py")


if __name__ == "__main__":
    main()
