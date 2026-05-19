"""Sprint 12-B / Phase B — grafik_okuma + oruntu_sekil için SVG sentetik üretim.

Phase A altyapısını (svg_utils, SafeSvg, pdf_renderer SVG embed) ve aynı
prompt patternini takip eder; bu sefer hedef tipler bar/pie chart ve renkli
şekil örüntüsü.

Çıktı: knowledge_base/processed/chart_pattern_svg_examples.json
ingest_to_chroma.py'ye eklenecek (bir sonraki commit).

Kullanım:
    python scripts/generate_chart_pattern_svg.py
    python scripts/generate_chart_pattern_svg.py --types grafik_okuma --per-pair 3
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import random
import sys
import time
from pathlib import Path

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import settings  # noqa: E402
from app.data.curriculum import CURRICULUM, Kazanim  # noqa: E402
from app.models.enums import Difficulty, QuestionType  # noqa: E402
from app.services.svg_utils import extract_svg_blocks, is_valid_svg  # noqa: E402


OUTPUT_PATH = ROOT / "knowledge_base" / "processed" / "chart_pattern_svg_examples.json"
MODELS_TO_TRY = [settings.gemini_model, *settings.fallback_model_list]
MAX_ATTEMPTS_PER_MODEL = 3
BASE_DELAY = 1.5

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("gen_chart_pattern")


# Hangi tip hangi sınıftan itibaren anlamlı
TYPE_BY_GRADE: dict[QuestionType, list[int]] = {
    QuestionType.GRAFIK_OKUMA: [3, 4, 5, 6, 7],  # ilkokul 3+ veri okuma
    QuestionType.ORUNTU_SEKIL: [1, 2, 3, 4, 5],  # erken çocukluk için zengin
}

# Tip-spesifik topic önceliği
TYPE_PREFERRED_TOPICS: dict[QuestionType, list[str]] = {
    QuestionType.GRAFIK_OKUMA: ["veri_isleme"],
    QuestionType.ORUNTU_SEKIL: ["dogal_sayilar", "geometri", "cebir"],
}


SVG_SYSTEM_PROMPT_CHART = """Sen MEB matematik müfredatına uygun, INLINE SVG ile sütun/pasta grafiği veya geometrik şekil örüntüsü sorusu üreten bir öğretmen asistanısın.

KRİTİK FORMAT KURALLARI:

A) grafik_okuma (sütun/pasta grafiği):
   - "question" alanı: soru cümlesi + boş satır + SVG bloğu + boş satır + grafiğe dayalı hesap/yorum sorusu.
   - <svg viewBox="0 0 W H" xmlns="http://www.w3.org/2000/svg">...</svg>, W ≤ 300, H ≤ 200.
   - Sütun: her bar `<rect>`. Yükseklik VERİ DEĞERİYLE ORANTILI olmalı (örn. 10 ve 20 değer → ikinci bar birincinin tam 2 katı).
   - X-axis çizgisi: `<line x1=20 y1=H-30 x2=W-20 y2=H-30 stroke="black"/>`
   - Her sütun altına `<text>` etiket (Ocak, Şubat, ...), üstüne `<text>` sayısal değer.
   - Pasta grafiği için `<path>` arc'lar + dilim etiketleri.
   - Renkler: #3b82f6, #10b981, #f59e0b, #ef4444, #8b5cf6 arasından seç.
   - "answer" alanı: sayısal sonuç (örn. "32", "10 fazla", "Şubat").
   - "solution" grafiği yorumlama adımlarını anlatır.

B) oruntu_sekil (geometrik şekil örüntüsü):
   - "question" alanı: yönerge cümlesi (örn. "Aşağıdaki örüntüde ? yerine hangi şekil gelmelidir?") + boş satır + SVG bloğu.
   - <svg viewBox="0 0 W H" xmlns="http://www.w3.org/2000/svg">...</svg>, W ≤ 360, H ≤ 80.
   - 4-7 şekil yan yana, eşit aralıkla (cx: 30, 80, 130, 180, 230, 280).
   - Şekiller: <circle r="20">, <rect width="40" height="40">, <polygon> (üçgen).
   - Renkler: #ef4444, #3b82f6, #10b981, #f59e0b.
   - Eksik konuma <text font-size="32" text-anchor="middle">?</text> (cy=30 civarı).
   - Örüntü kuralı (renk/şekil sırası/sayı artışı) MATEMATİKSEL OLARAK tutarlı.
   - "answer" alanı: eksik konumdaki şekil tanımı (örn. "Kırmızı daire", "Yeşil üçgen").
   - "solution": örüntü kuralını açıkla + adım adım uygula.

Mutlak kurallar (her iki tip için):
- Yalnızca line, polyline, polygon, rect, circle, ellipse, path, text, g elementleri.
- YASAK: script, foreignObject, image, use href="http..."
- Stroke siyah (`black` veya `#1f2937`), stroke-width 1-2.
- Sayısal değerler ile grafik/örüntü GEOMETRİSİ tutarlı (anti-yanıltıcı).
- Kazanım sınırı: üst sınıf bilgisi gerektirme.
- Çıktıyı SADECE JSON formatında üret."""


class _SvgExample(BaseModel):
    question: str
    answer: str
    solution: str
    kazanim_kod: str


class _SvgBatch(BaseModel):
    examples: list[_SvgExample]


def _build_prompt(
    grade: int,
    topic_name: str,
    kazanimlar: list[Kazanim],
    qtype: QuestionType,
    difficulty: Difficulty,
    count: int,
) -> str:
    lines = [
        f"Sınıf: {grade}. sınıf",
        f"Konu: {topic_name}",
        f"Hedef Soru Tipi: {qtype.value}",
        f"Zorluk: {difficulty.value}",
        "",
        "Kazanım seçenekleri (her sorunda biriyle etiketle):",
    ]
    for k in kazanimlar:
        hint = k.get("difficulty_hints", {}).get(difficulty.value, "")
        lines.append(f"  - {k['kod']}: {k['metin']}")
        if hint:
            lines.append(f"      Zorluk: {hint}")
    lines.extend([
        "",
        f"{qtype.value} tipinde SVG'li, birbirinden FARKLI bağlam ve farklı "
        f"sayısal değerler kullanarak {count} adet soru üret. Yukarıdaki SVG "
        f"kurallarına TAM uy.",
        "",
        'JSON: {"examples": [{"question": "...<svg>...</svg>...", "answer": "...", '
        '"solution": "...", "kazanim_kod": "..."}, ...]}',
    ])
    return "\n".join(lines)


def _load_existing() -> list[dict]:
    if OUTPUT_PATH.exists():
        with OUTPUT_PATH.open("r", encoding="utf-8") as f:
            return json.load(f).get("examples", [])
    return []


def _save(examples: list[dict]) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUTPUT_PATH.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump({"examples": examples}, f, ensure_ascii=False, indent=2)
    os.replace(tmp, OUTPUT_PATH)


def _completed_triples(examples: list[dict], per_pair: int) -> set[tuple[int, str, str]]:
    counts: dict[tuple[int, str, str], int] = {}
    for e in examples:
        k = (e["grade"], e["question_type"], e["difficulty"])
        counts[k] = counts.get(k, 0) + 1
    return {k for k, v in counts.items() if v >= per_pair}


def _call_with_fallback(
    client: genai.Client,
    user_prompt: str,
    config: types.GenerateContentConfig,
) -> tuple[types.GenerateContentResponse, str]:
    last_exc: Exception | None = None
    for model_name in MODELS_TO_TRY:
        for attempt in range(1, MAX_ATTEMPTS_PER_MODEL + 1):
            try:
                resp = client.models.generate_content(
                    model=model_name, contents=user_prompt, config=config,
                )
                return resp, model_name
            except genai_errors.ServerError as exc:
                last_exc = exc
                code = getattr(exc, "code", None)
                if code not in (500, 502, 503, 504):
                    raise
                if attempt == MAX_ATTEMPTS_PER_MODEL:
                    break
                delay = BASE_DELAY * (2 ** (attempt - 1)) + random.uniform(0, 0.4)
                logger.warning("[%s] retry %.1fs (%s/%s)", model_name, delay, attempt, MAX_ATTEMPTS_PER_MODEL)
                time.sleep(delay)
    raise RuntimeError(f"Tüm modeller tükendi: {last_exc}")


def _parse(resp: types.GenerateContentResponse) -> _SvgBatch:
    parsed = getattr(resp, "parsed", None)
    if isinstance(parsed, _SvgBatch):
        return parsed
    return _SvgBatch.model_validate_json(resp.text)


def _validate(question: str) -> tuple[bool, str]:
    blocks = extract_svg_blocks(question)
    if not blocks:
        return False, "SVG bloğu yok"
    for _, _, svg in blocks:
        ok, _ = is_valid_svg(svg)
        if ok:
            return True, ""
    return False, "Tüm SVG blokları geçersiz"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--per-pair", type=int, default=3)
    p.add_argument("--types", type=str, default="grafik_okuma,oruntu_sekil",
                   help="Virgüllü tip listesi")
    p.add_argument("--difficulties", type=str, default="orta",
                   help="Virgüllü difficulty (default: orta)")
    p.add_argument("--limit", type=int, default=None)
    args = p.parse_args()

    if not settings.gemini_api_key:
        raise SystemExit("GEMINI_API_KEY yok.")

    selected_types = [QuestionType(t.strip()) for t in args.types.split(",")]
    difficulties = [Difficulty(d.strip()) for d in args.difficulties.split(",")]

    examples = _load_existing()
    logger.info("Mevcut: %s", len(examples))
    done = _completed_triples(examples, args.per_pair)

    work: list[tuple[int, list[Kazanim], QuestionType, Difficulty]] = []
    for grade in sorted(CURRICULUM.keys()):
        for qtype in selected_types:
            valid_grades = TYPE_BY_GRADE.get(qtype, list(CURRICULUM.keys()))
            if grade not in valid_grades:
                continue
            preferred = TYPE_PREFERRED_TOPICS.get(qtype, [])
            kazanimlar: list[Kazanim] = []
            for topic_id, topic in CURRICULUM[grade].items():
                if preferred and topic_id not in preferred:
                    continue
                kazanimlar.extend(topic["kazanimlar"])
            if not kazanimlar:
                # Fallback: o sınıfta preferred topic yok → tüm topic
                for topic in CURRICULUM[grade].values():
                    kazanimlar.extend(topic["kazanimlar"])
            if not kazanimlar:
                continue
            for diff in difficulties:
                key = (grade, qtype.value, diff.value)
                if key in done:
                    continue
                work.append((grade, kazanimlar, qtype, diff))

    if args.limit:
        work = work[: args.limit]

    logger.info("Yapılacak üçlü: %s (per_pair=%s, beklenen ~%s örnek)",
                len(work), args.per_pair, len(work) * args.per_pair)
    if not work:
        logger.info("Tamamlanmış.")
        return

    client = genai.Client(api_key=settings.gemini_api_key)
    config = types.GenerateContentConfig(
        system_instruction=SVG_SYSTEM_PROMPT_CHART,
        temperature=0.85,
        response_mime_type="application/json",
        response_schema=_SvgBatch,
    )

    valid_codes = {
        k["kod"]
        for g in CURRICULUM.values()
        for t in g.values()
        for k in t["kazanimlar"]
    }

    for i, (grade, kazanimlar, qtype, diff) in enumerate(work, 1):
        topic_name = next(iter(CURRICULUM[grade].values()))["name"]
        user_prompt = _build_prompt(grade, topic_name, kazanimlar, qtype, diff, args.per_pair)
        try:
            resp, model_used = _call_with_fallback(client, user_prompt, config)
            batch = _parse(resp)
        except Exception as exc:
            logger.error("[%s/%s] g=%s t=%s d=%s fail: %s",
                         i, len(work), grade, qtype.value, diff.value, exc)
            continue

        topic_id_by_kod = {
            k["kod"]: tid
            for tid, t in CURRICULUM[grade].items()
            for k in t["kazanimlar"]
        }

        added = 0
        skipped = 0
        for ex in batch.examples[: args.per_pair]:
            ok, reason = _validate(ex.question)
            if not ok:
                logger.warning("  format-fail (%s): %s | q=%r", qtype.value, reason, ex.question[:80])
                skipped += 1
                continue
            kod = ex.kazanim_kod if ex.kazanim_kod in valid_codes else kazanimlar[0]["kod"]
            # Topic — preferred listesinden seç, yoksa kazanım'dan resolve et.
            topic_id = topic_id_by_kod.get(kod, "")
            if not topic_id:
                topic_id = TYPE_PREFERRED_TOPICS.get(qtype, [""])[0]
            examples.append({
                "grade": grade,
                "topic_id": topic_id,
                "kazanim_kod": kod,
                "difficulty": diff.value,
                "question_type": qtype.value,
                "question": ex.question.strip(),
                "answer": ex.answer.strip(),
                "solution": ex.solution.strip(),
                "source": f"synthetic_chart_pattern_svg/{model_used}",
            })
            added += 1

        if i % 3 == 0 or i == len(work):
            _save(examples)

        logger.info("[%s/%s] g=%s t=%s d=%s → +%s (skip=%s, toplam %s) [%s]",
                    i, len(work), grade, qtype.value, diff.value, added, skipped, len(examples), model_used)

    _save(examples)
    logger.info("Tamamlandı. Toplam: %s → %s", len(examples), OUTPUT_PATH)


if __name__ == "__main__":
    main()
