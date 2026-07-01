"""Herhangi bir sınıfın (1-8) PDF'lerinden yapısal Soru+Cevap çıkarır.

`extract_lgs_questions.py`'nin genelleştirilmiş hâli. Farklar:
  * `--grade N` — sınıf parametrik (8 hardcode değil).
  * Gürbüz klasör çözümü (`_resolve_grade_dir`) — `5.sınıf` / `7.Sınıf` casing + İ/ı.
  * Çok-formatlı şema (`ExtractedQuestion`) — MCQ + açık uçlu + boşluk + D/Y + eşleştirme.
  * Manifest `kazanim_hint` → çıkarım prompt'una "muhtemel konu" ipucu.
  * Görsel sadakat kapısı — üretilen inline <svg> `svg_utils.is_valid_svg`'den geçer;
    geçmeyen few-shot havuzuna GİRMEZ, review kuyruğuna düşer.

Strateji (LGS hattıyla aynı):
  1. Manifest'ten `track in {"questions","lgs"}` ve `skip` olmayan PDF'leri seç.
  2. Her PDF: (a) cevap anahtarı sayfalarını tespit, (b) soru sayfalarını görüntüye
     çevirip cevap anahtarı + kazanım ipucuyla Gemini Flash'a ver → yapısal liste.
  3. Görsel sorular için 2. Gemini çağrısı → inline <svg>/Markdown → is_valid_svg kapısı.
  4. Çıkarılamayan / bozuk görsel → review kuyruğu.
  5. Başarılı sorular → processed/questions_grade{N}.json (few-shot şeması).

Kullanım:
    python scripts/extract_questions.py --grade 5 --limit 1   # pilot: 1 PDF
    python scripts/extract_questions.py --grade 5             # tüm questions track
    python scripts/extract_questions.py --grade 6 --skip-visual
    python scripts/extract_questions.py --grade 7 --dry-run

Resumable: çıktı JSON'daki mevcut kayıtlar stable_id ile atlanır.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import logging
import re
import sys
import time
from pathlib import Path

import pymupdf
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import settings  # noqa: E402
from app.data.curriculum import CURRICULUM  # noqa: E402
from app.services.svg_utils import extract_svg_blocks, is_valid_svg  # noqa: E402

PROCESSED_DIR = ROOT / "knowledge_base" / "processed"
KB_DIR = ROOT / "knowledge_base"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("extract_questions")

# ─── Sabitler ───────────────────────────────────────────────────────────────
RENDER_DPI = 150
MAX_PAGES_PER_CALL = 2  # yoğun çıkmış-soru sayfalarında JSON truncation riskini azalt
VISUAL_MAX_PAGES_PER_CALL = 2  # visual_heavy PDF'lerde daha dikkatli
MAX_OUTPUT_TOKENS = 32768  # uzun yapısal JSON kesilmesin
BATCH_DELAY = 1.0
ANSWER_KEY_MARKERS = re.compile(
    r"(?i)(cevap\s+anahtar|yanıt\s+anahtar|doğru\s+yanıt|cevaplar|CEVAP)",
    re.UNICODE,
)
QUESTION_TRACKS = {"questions", "lgs"}


# ─── Pydantic şemaları (çok-formatlı) ─────────────────────────────────────────

class QOption(BaseModel):
    label: str = Field(description="Şık harfi: A, B, C veya D")
    text: str = Field(description="Şık metni")


class ExtractedQuestion(BaseModel):
    question_no: int | None = Field(default=None, description="PDF'deki soru numarası")
    stem: str = Field(description="Soru kökü (kısa senaryo dahil)")
    question_type: str = Field(
        default="coktan_secmeli",
        description=(
            "'coktan_secmeli' | 'acik_uclu' | 'bosluk_doldurma' | 'dogru_yanlis' | "
            "'eslestirme' | 'siralanan'. Görsel içeriyorsa yine de buradan seç; "
            "görsel tipi visual_type'a yaz."
        ),
    )
    options: list[QOption] = Field(
        default_factory=list,
        description="Çoktan seçmeli ise A-D şıkları. Diğer formatlarda boş bırak.",
    )
    correct_answer: str = Field(
        description="Doğru cevap: MCQ'da şık harfi (A-D); açık uçluda cevap metni/değeri."
    )
    solution: str = Field(description="Kısa çözüm yolu (1-2 cümle). Yoksa üret.")
    kazanim_kod: str | None = Field(
        default=None,
        description="MEB kazanım kodu (M.{grade}.x.y). Belirsizse null.",
    )
    difficulty: str = Field(
        default="orta",
        description="'kolay' | 'orta' | 'zor'.",
    )
    has_visual: bool = Field(
        default=False, description="True: soruda şekil/grafik/tablo var."
    )
    visual_type: str | None = Field(
        default=None,
        description="'geometri' | 'grafik' | 'tablo' | 'desen' | null",
    )
    skip_reason: str | None = Field(
        default=None,
        description="Çıkarılamadıysa neden. Aksi null.",
    )


class QuestionBatch(BaseModel):
    questions: list[ExtractedQuestion]


class SVGQuestion(BaseModel):
    stem_with_visual: str = Field(
        description=(
            "Soru kökü + görseli temsil eden inline <svg>...</svg> VEYA Markdown tablosu. "
            "SVG: viewBox='0 0 W H' xmlns='http://www.w3.org/2000/svg' ile başlamalı."
        )
    )
    question_type: str = Field(
        description="'gorsel_geometri' | 'grafik_okuma' | 'tablo_sorusu' | 'oruntu_sekil'"
    )
    reproduced: bool = Field(description="True: görsel başarıyla üretildi.")
    skip_reason: str | None = Field(default=None)


# ─── Yardımcılar ────────────────────────────────────────────────────────────

def _resolve_grade_dir(grade: int) -> Path:
    """Sınıf klasörünü gürbüz şekilde bul: '5.sınıf' / '7.Sınıf' / İ-ı varyasyonları."""
    target = f"{grade}.s"  # "5.s" / "7.S" → casefold ile eşleşir
    for child in KB_DIR.iterdir():
        if not child.is_dir():
            continue
        name = child.name
        if name.casefold().startswith(target.casefold()) and "ını" in name.casefold().replace("i", "ı"):
            return child
        # Daha gevşek: "5.sınıf" / "5.Sınıf" — nokta sonrası 's' ile başlayan klasör
        if name.casefold().startswith(f"{grade}.".casefold()) and name[len(f"{grade}."):][:1].casefold() == "s":
            return child
    raise SystemExit(f"{grade}. sınıf klasörü bulunamadı (knowledge_base altında).")


def _stable_id(grade: int, prefix: str, source: str, q_no: int | None, stem: str) -> str:
    key = f"{grade}|{source}|{q_no}|{stem[:80]}"
    return prefix + hashlib.sha1(key.encode("utf-8")).hexdigest()[:14]


def _page_to_base64(page: pymupdf.Page, dpi: int = RENDER_DPI) -> str:
    mat = pymupdf.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat, colorspace=pymupdf.csRGB)
    return base64.b64encode(pix.tobytes("png")).decode("utf-8")


def _detect_answer_key_pages(doc: pymupdf.Document) -> set[int]:
    return {i for i in range(len(doc)) if ANSWER_KEY_MARKERS.search(doc[i].get_text())}


def _extract_answer_map(doc: pymupdf.Document, ans_pages: set[int]) -> dict[int, str]:
    ans_map: dict[int, str] = {}
    ANS_RE = re.compile(r"(?:(\d{1,2})[\s.)\-]+([A-D]))", re.IGNORECASE)
    for page_idx in sorted(ans_pages):
        for m in ANS_RE.finditer(doc[page_idx].get_text()):
            try:
                ans_map[int(m.group(1))] = m.group(2).upper()
            except ValueError:
                pass
    return ans_map


def _call_with_backoff(fn, max_attempts: int = 3, base_delay: float = 2.0):
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
            logger.warning("API hata %s (deneme %s/%s); %.1fs sonra retry",
                           code, attempt, max_attempts, delay)
            time.sleep(delay)
    raise RuntimeError(f"Tüm denemeler başarısız: {last_exc}")


def _valid_kazanim_codes(grade: int) -> set[str]:
    codes: set[str] = set()
    for topic in CURRICULUM.get(grade, {}).values():
        for k in topic["kazanimlar"]:
            codes.add(k["kod"])
    return codes


# ─── Gemini çağrıları ─────────────────────────────────────────────────────────

def _extraction_system(grade: int) -> str:
    return f"""Sen matematik sınav sorusu çıkarma uzmanısın.
PDF sayfalarında gördüğün Türkçe {grade}. sınıf matematik sorularını yapısal formata dönüştür.

Kurallar:
1. Her soru: stem (kök), question_type, (MCQ ise A-D şıkları), correct_answer, kısa solution, kazanım kodu (varsa).
2. question_type'ı sayfadaki gerçek formata göre seç:
   'coktan_secmeli' (A-D şıklı) | 'acik_uclu' | 'bosluk_doldurma' | 'dogru_yanlis' | 'eslestirme' | 'siralanan'.
3. Doğru cevap: cevap anahtarından al. Anahtarda yoksa en makul cevabı seç + solution'da belirt.
4. solution HER soruda dolu olmalı: kaynakta yoksa kısa çözüm üret.
5. difficulty: tek adım → 'kolay', 2-3 adım → 'orta', çok adımlı → 'zor'.
6. has_visual=True: soruda şekil/grafik/tablo var. visual_type: 'geometri'|'grafik'|'tablo'|'desen'.
7. kazanim_kod: M.{grade}.x.y biçiminde. Emin değilsen null.
8. Okunaksız/yarım/görselsiz anlaşılmayan sorular: skip_reason doldur.
9. ASLA soru uydurma. Sayfada yoksa ekleme."""


SVG_SYSTEM = """Sen matematiksel görsel dönüştürme uzmanısın.
Verilen sorudaki görseli sisteme uygun inline formata çevir.

Format kuralları:
- Geometri şekli → inline <svg viewBox="0 0 W H" xmlns="http://www.w3.org/2000/svg">...</svg>
  * Şekli, ölçü/açı/harf etiketlerini dahil et. <line>/<polygon>/<circle>/<text> kullan.
  * viewBox içeriği tam sığdırsın, 10px kenar payı.
- Grafik (sütun/çizgi/pasta) → <svg> ile temsili grafik.
- Tablo → GFM Markdown: | Sütun1 | Sütun2 | ...
- Desen/örüntü → Unicode semboller veya <svg>.

reproduced=False koşulları:
  - Fotoğraf/gerçek nesne görüntüsü
  - Çok karmaşık (20+ nesne) şekil
  - Metinle tam ifade edilebilir (görsele gerek yok)"""


def _extract_questions_from_pages(
    client: genai.Client,
    grade: int,
    page_images: list[str],
    answer_map: dict[int, str],
    source_name: str,
    kazanim_hint: str | None,
) -> list[ExtractedQuestion]:
    hint_text = ""
    if kazanim_hint:
        hint_text = f"\nMUHTEMEL KONU/KAZANIM: {kazanim_hint} (kesin değil; soru farklıysa kendin belirle)\n"
    ans_text = ""
    if answer_map:
        pairs = ", ".join(f"{n}→{a}" for n, a in sorted(answer_map.items()))
        ans_text = f"\nCEVAP ANAHTARI: {pairs}\n"

    prompt_parts: list = [
        f"Kaynak: {source_name}{ans_text}{hint_text}\nBu sayfadaki tüm matematik sorularını çıkar:"
    ]
    for img_b64 in page_images:
        prompt_parts.append(
            types.Part.from_bytes(data=base64.b64decode(img_b64), mime_type="image/png")
        )

    config = types.GenerateContentConfig(
        system_instruction=_extraction_system(grade),
        temperature=0.1,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        thinking_config=types.ThinkingConfig(thinking_budget=0),  # çıkarım: thinking gereksiz → hız+maliyet
        response_mime_type="application/json",
        response_schema=QuestionBatch,
    )

    def _call():
        return client.models.generate_content(
            model=settings.gemini_model, contents=prompt_parts, config=config
        )

    response = _call_with_backoff(_call)
    parsed = getattr(response, "parsed", None)
    if isinstance(parsed, QuestionBatch):
        return parsed.questions
    try:
        return QuestionBatch.model_validate_json(response.text).questions
    except Exception:
        # Output token limitine takılıp JSON kesilmiş olabilir → tamamlanmış soruları kurtar
        salvaged = _salvage_questions(response.text)
        if salvaged:
            logger.warning("  JSON kesik; %d tam soru kurtarıldı (partial salvage)", len(salvaged))
        return salvaged


def _salvage_questions(text: str) -> list[ExtractedQuestion]:
    """Kesik JSON dizisinden tamamı kapanmış {..} nesnelerini tek tek parse eder."""
    objs: list[ExtractedQuestion] = []
    start_arr = text.find("[")
    if start_arr == -1:
        return objs
    depth = 0
    obj_start: int | None = None
    in_str = False
    esc = False
    for idx in range(start_arr + 1, len(text)):
        c = text[idx]
        if esc:
            esc = False
            continue
        if c == "\\":
            esc = True
            continue
        if c == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if c == "{":
            if depth == 0:
                obj_start = idx
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0 and obj_start is not None:
                frag = text[obj_start: idx + 1]
                try:
                    objs.append(ExtractedQuestion.model_validate_json(frag))
                except Exception:
                    pass
                obj_start = None
    return objs


def _reproduce_visual(
    client: genai.Client, question: ExtractedQuestion, page_image: str
) -> SVGQuestion | None:
    prompt_parts = [
        f"Soru: {question.stem}\n\nBu sorudaki görseli inline formata çevir:",
        types.Part.from_bytes(data=base64.b64decode(page_image), mime_type="image/png"),
    ]
    config = types.GenerateContentConfig(
        system_instruction=SVG_SYSTEM,
        temperature=0.2,
        response_mime_type="application/json",
        response_schema=SVGQuestion,
    )

    def _call():
        return client.models.generate_content(
            model=settings.gemini_model, contents=prompt_parts, config=config
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


def _svg_gate(stem_with_visual: str) -> tuple[bool, str]:
    """İçindeki tüm <svg> bloklarını is_valid_svg ile doğrula. Markdown tablo → geçer."""
    blocks = extract_svg_blocks(stem_with_visual)
    if not blocks:
        # "<svg" var ama tam blok yok → kapanmamış/bozuk SVG
        if "<svg" in stem_with_visual.lower():
            return False, "kapanmamış/bozuk svg bloğu"
        return True, "svg yok (markdown/tablo)"
    for _start, _end, svg in blocks:
        ok, reason = is_valid_svg(svg)
        if not ok:
            return False, f"geçersiz svg: {reason}"
    return True, "ok"


# ─── IO ────────────────────────────────────────────────────────────────────

def _load_existing_ids(output_path: Path) -> set[str]:
    if not output_path.exists():
        return set()
    data = json.loads(output_path.read_text(encoding="utf-8"))
    return {e["id"] for e in data.get("examples", [])}


def _save_examples(examples: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps({"examples": examples}, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _save_review(review_items: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps({"review_queue": review_items}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ─── PDF işleme ────────────────────────────────────────────────────────────

def process_pdf(
    pdf_path: Path,
    client: genai.Client,
    grade: int,
    id_prefix: str,
    existing_ids: set[str],
    valid_codes: set[str],
    kazanim_hint: str | None,
    visual_heavy: bool,
    skip_visual: bool = False,
) -> tuple[list[dict], list[dict]]:
    logger.info("İşleniyor: %s (hint=%s, visual_heavy=%s)", pdf_path.name, kazanim_hint, visual_heavy)
    doc = pymupdf.open(str(pdf_path))
    n_pages = len(doc)

    ans_pages = _detect_answer_key_pages(doc)
    answer_map = _extract_answer_map(doc, ans_pages)
    logger.info("  %d sayfa | %d cevap anahtarı sayfası | %d cevap eşleşti",
                n_pages, len(ans_pages), len(answer_map))

    question_pages = [i for i in range(n_pages) if i not in ans_pages]
    pages_per_call = VISUAL_MAX_PAGES_PER_CALL if visual_heavy else MAX_PAGES_PER_CALL

    examples: list[dict] = []
    review_items: list[dict] = []
    batches = [
        question_pages[i: i + pages_per_call]
        for i in range(0, len(question_pages), pages_per_call)
    ]
    page_cache: dict[int, str] = {}

    for b_idx, batch_pages in enumerate(batches):
        logger.info("  Batch %d/%d (sayfa %s)...", b_idx + 1, len(batches),
                    [p + 1 for p in batch_pages])
        page_images: list[str] = []
        for pidx in batch_pages:
            if pidx not in page_cache:
                page_cache[pidx] = _page_to_base64(doc[pidx])
            page_images.append(page_cache[pidx])

        try:
            questions = _extract_questions_from_pages(
                client, grade, page_images, answer_map, pdf_path.name, kazanim_hint
            )
        except Exception as exc:
            logger.error("  Batch %d başarısız: %s", b_idx + 1, exc)
            time.sleep(BATCH_DELAY * 2)
            continue

        logger.info("  → %d soru çıkarıldı", len(questions))

        for q in questions:
            if q.skip_reason:
                review_items.append({
                    "source": pdf_path.name, "question_no": q.question_no,
                    "stem_preview": q.stem[:120], "skip_reason": q.skip_reason,
                })
                continue
            if not q.stem or not q.correct_answer:
                continue
            if q.question_type == "coktan_secmeli" and not q.options:
                continue  # MCQ dedi ama şık yok → tutarsız

            stable_id = _stable_id(grade, id_prefix, pdf_path.name, q.question_no, q.stem)
            if stable_id in existing_ids:
                continue

            # Kazanım doğrula: geçersizse null'a indir (gürültü ingest'te elenir)
            kazanim = q.kazanim_kod if q.kazanim_kod in valid_codes else (
                kazanim_hint if kazanim_hint in valid_codes else None
            )

            stem_final = q.stem
            question_type = q.question_type

            if q.has_visual and not skip_visual and q.visual_type:
                page_img = page_images[0]
                svg_result = _reproduce_visual(client, q, page_img)
                if svg_result and svg_result.reproduced:
                    ok, reason = _svg_gate(svg_result.stem_with_visual)
                    if ok:
                        stem_final = svg_result.stem_with_visual
                        question_type = svg_result.question_type
                        logger.info("    ✓ Görsel dönüştürüldü #%s (tip: %s)",
                                    q.question_no, question_type)
                    else:
                        logger.info("    ✗ SVG kapısı reddetti #%s: %s", q.question_no, reason)
                        review_items.append({
                            "source": pdf_path.name, "question_no": q.question_no,
                            "stem_preview": q.stem[:120], "visual_type": q.visual_type,
                            "skip_reason": f"svg_gate: {reason}",
                        })
                        continue  # bozuk görsel few-shot'a girmez
                else:
                    reason = svg_result.skip_reason if svg_result else "SVG çağrısı başarısız"
                    logger.info("    ✗ Görsel atlandı #%s: %s", q.question_no, reason)
                    review_items.append({
                        "source": pdf_path.name, "question_no": q.question_no,
                        "stem_preview": q.stem[:120], "visual_type": q.visual_type,
                        "skip_reason": reason or "görsel yeniden üretilemedi",
                    })
                    continue  # görsel olmadan anlaşılmayan soruyu havuza koyma

            # Cevap metni
            if q.options:
                opt_map = {o.label.upper(): o.text for o in q.options}
                answer_full = f"{q.correct_answer}) {opt_map.get(q.correct_answer.upper(), '')}".strip()
                question_block = stem_final + "\n\n" + "\n".join(
                    f"{o.label}) {o.text}" for o in q.options
                )
            else:
                answer_full = q.correct_answer
                question_block = stem_final

            examples.append({
                "id": stable_id,
                "grade": grade,
                "topic_id": "",  # ingest'te kazanım_kodu → topic_id ile doldurulur
                "kazanim_kod": kazanim or "",
                "difficulty": q.difficulty,
                "question_type": question_type,
                "question": question_block,
                "answer": answer_full,
                "solution": q.solution,
                "source": f"questions/grade{grade}/{pdf_path.name}",
            })
            existing_ids.add(stable_id)

        time.sleep(BATCH_DELAY)

    doc.close()
    logger.info("  → %d örnek eklendi | %d review kuyruğuna", len(examples), len(review_items))
    return examples, review_items


# ─── main ────────────────────────────────────────────────────────────────────

def run(
    grade: int,
    limit: int | None = None,
    only_pdf: str | None = None,
    skip_visual: bool = False,
    lean: bool = False,
    dry_run: bool = False,
    id_prefix: str | None = None,
    output_name: str | None = None,
    review_name: str | None = None,
    grade_dir: Path | None = None,
) -> None:
    if not settings.gemini_api_key:
        raise SystemExit("GEMINI_API_KEY .env'de yok.")

    gdir = grade_dir or _resolve_grade_dir(grade)
    manifest_path = gdir / "manifest.json"
    if not manifest_path.exists():
        raise SystemExit(f"manifest.json yok: {manifest_path}")

    id_prefix = id_prefix or f"q{grade}_"
    output_path = PROCESSED_DIR / (output_name or f"questions_grade{grade}.json")
    review_path = PROCESSED_DIR / (review_name or f"questions_visual_review_grade{grade}.json")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = [
        e for e in manifest.get("files", [])
        if e.get("track") in QUESTION_TRACKS and not e.get("skip")
    ]
    if lean:
        # Yalın koşu: sadece gold (çıkmış sorular) + görsel-yoğun PDF'ler → maliyet ~%60-70 düşer
        entries = [e for e in entries if e.get("gold") or e.get("visual_heavy")]
    if only_pdf:
        entries = [e for e in entries if e["file"] == only_pdf]
        if not entries:
            raise SystemExit(f"'{only_pdf}' manifest'te questions track'inde yok.")
    elif limit:
        entries = entries[:limit]

    logger.info("Sınıf %d | klasör: %s | işlenecek PDF: %d", grade, gdir.name, len(entries))
    for e in entries:
        logger.info("  - %s", e["file"])

    valid_codes = _valid_kazanim_codes(grade)
    existing_ids = _load_existing_ids(output_path)
    logger.info("Mevcut kayıt: %d", len(existing_ids))

    existing_examples: list[dict] = []
    if output_path.exists():
        existing_examples = json.loads(output_path.read_text(encoding="utf-8")).get("examples", [])

    # Resume optimizasyonu: kayıt PDF-başına atomik → çıktıda kaynağı olan PDF TAM bitmiştir.
    # Bu PDF'leri tekrar vision'lama (para tasarrufu). Yarıda kesilen PDF 0 örnek kaydettiği
    # için çıktıda olmaz → yeniden işlenir.
    completed_sources = {e.get("source", "").split("/")[-1] for e in existing_examples}
    if completed_sources:
        before = len(entries)
        entries = [e for e in entries if e["file"] not in completed_sources]
        skipped = before - len(entries)
        if skipped:
            logger.info("Resume: %d tamamlanmış PDF atlanıyor (tekrar vision yok)", skipped)
    existing_review: list[dict] = []
    if review_path.exists():
        existing_review = json.loads(review_path.read_text(encoding="utf-8")).get("review_queue", [])

    client = genai.Client(api_key=settings.gemini_api_key)
    all_new: list[dict] = []
    all_review: list[dict] = list(existing_review)

    for entry in entries:
        pdf_path = gdir / entry["file"]
        if not pdf_path.exists():
            logger.warning("PDF yok: %s", pdf_path)
            continue
        new_examples, review_items = process_pdf(
            pdf_path, client, grade, id_prefix,
            existing_ids=existing_ids, valid_codes=valid_codes,
            kazanim_hint=entry.get("kazanim_hint"),
            visual_heavy=bool(entry.get("visual_heavy")),
            skip_visual=skip_visual,
        )
        all_new.extend(new_examples)
        all_review.extend(review_items)
        if not dry_run:
            _save_examples(existing_examples + all_new, output_path)
            _save_review(all_review, review_path)
            logger.info("Ara kayıt: %d örnek", len(existing_examples) + len(all_new))

    total = len(existing_examples) + len(all_new)
    print("\n=== ÖZET ===")
    print(f"Sınıf              : {grade}")
    print(f"Yeni eklenen örnek : {len(all_new)}")
    print(f"Toplam örnek       : {total}")
    print(f"Review kuyruğu     : {len(all_review)}")

    if dry_run:
        print("(dry-run: dosyaya yazılmadı)")
        return

    by_type: dict[str, int] = {}
    by_kaz: dict[str, int] = {}
    for e in all_new:
        by_type[e["question_type"]] = by_type.get(e["question_type"], 0) + 1
        k = e.get("kazanim_kod") or "__UNMAPPED__"
        by_kaz[k] = by_kaz.get(k, 0) + 1
    print("\nYeni örnek tip dağılımı:")
    for t, n in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {t}: {n}")
    print("\nKazanım dağılımı (top-10):")
    for k, n in sorted(by_kaz.items(), key=lambda x: -x[1])[:10]:
        print(f"  {k}: {n}")
    print(f"\nÇıktılar:\n  {output_path}\n  {review_path}")
    print("\nSonraki adım: python scripts/ingest_to_chroma.py")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--grade", type=int, required=True, help="Sınıf (1-8)")
    parser.add_argument("--limit", type=int, default=None, help="Test: max PDF sayısı")
    parser.add_argument("--pdf", type=str, default=None, help="Tek PDF (manifest dosya adı)")
    parser.add_argument("--skip-visual", action="store_true", help="Görsel dönüşümünü atla")
    parser.add_argument("--lean", action="store_true", help="Sadece gold + görsel-yoğun PDF'ler (maliyet tasarrufu)")
    parser.add_argument("--dry-run", action="store_true", help="Dosyaya yazma")
    args = parser.parse_args()
    run(
        grade=args.grade, limit=args.limit, only_pdf=args.pdf,
        skip_visual=args.skip_visual, lean=args.lean, dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
