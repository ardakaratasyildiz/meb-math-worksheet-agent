"""Sprint 12-B / Phase A — gorsel_geometri için SVG-tabanlı sentetik üretim.

Mevcut visual_examples.json'daki Unicode-tabanlı gorsel_geometri örnekleri
yerine LLM-SVG çıktısı üretir. Üretilen SVG, app/services/svg_utils.is_valid_svg
ile parse + tehlikeli pattern kontrolünden geçer; geçmeyenler skip edilir.

Çıktı: knowledge_base/processed/geometry_svg_examples.json (yeni dosya).
ingest_to_chroma.py bu dosyayı da ingest pool'una alacak.

Kullanım:
    python scripts/generate_geometry_svg.py
    python scripts/generate_geometry_svg.py --per-pair 3 --grades 5,6,7
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
from app.models.enums import Difficulty  # noqa: E402
from app.services.svg_utils import extract_svg_blocks, is_valid_svg  # noqa: E402


OUTPUT_PATH = ROOT / "knowledge_base" / "processed" / "geometry_svg_examples.json"
MODELS_TO_TRY = [settings.gemini_model, *settings.fallback_model_list]
MAX_ATTEMPTS_PER_MODEL = 3
BASE_DELAY = 1.5

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("gen_geo_svg")


SVG_SYSTEM_PROMPT = """Sen MEB matematik müfredatına uygun GEOMETRİ soruları üreten bir öğretmen asistanısın. Her soru question alanı içinde inline SVG ile geometri şekli ve ölçü etiketleri taşır.

KRİTİK FORMAT KURALLARI — `gorsel_geometri` tipi için:

1. SVG formatı:
   <svg viewBox="0 0 W H" xmlns="http://www.w3.org/2000/svg">
     <!-- şekiller burada -->
   </svg>
   - W ≤ 250, H ≤ 200 (görsel sayfada makul boyut)
   - viewBox ZORUNLU (responsive scale için)

2. İzin verilen elementler:
   line, polyline, polygon, rect, circle, ellipse, path, text, g
   YASAK: script, foreignObject, image, use href="http://..."

3. Stil:
   - Kontur: stroke="black" veya stroke="#1f2937", stroke-width="1.5" veya "2"
   - Dolgu: fill="none" (sadece kontur) ya da çok açık ton (#fef3c7 gibi)

4. Ölçü etiketleri:
   - <text x="..." y="..." font-size="13">6 cm</text> formatında
   - Şekil kenarına/açısına yakın konumlandır
   - "Birim BURAYA" değil; somut sayı + birim (6 cm, 60°, 12 m vb.)

5. Tutarlılık MUTLAK:
   - SVG'de gösterilen değer ile soru/cevap aynı olmalı
   - Eşkenar üçgen için 3 kenar da aynı uzunlukta gösterilmeli (point koordinatları ona göre)
   - Dik açı varsa köşeye küçük kare çizilebilir (≈ 8x8)

6. Soru/cevap:
   - "question" alanı: soru cümlesi + boş satır + SVG bloğu + (opsiyonel) ek açıklama cümlesi
   - "answer": sayısal sonuç + birim (örn. "42 cm²", "60°", "24")
   - "solution": adım adım çözüm — formül + değer yerleştirme + sonuç

7. Kazanım uyumu:
   - Üst sınıf bilgisi gerektirme
   - Sayılar zorluğa uygun (kolay: küçük tam sayılar; orta: orta; zor: kesirli/oranlı olabilir)

ÖRNEK ÇIKTI:
{
  "question": "Aşağıdaki üçgenin çevresi kaç cm'dir?\\n\\n<svg viewBox=\\"0 0 200 160\\" xmlns=\\"http://www.w3.org/2000/svg\\"><polygon points=\\"100,20 30,140 170,140\\" fill=\\"none\\" stroke=\\"black\\" stroke-width=\\"2\\"/><text x=\\"45\\" y=\\"90\\" font-size=\\"13\\">10 cm</text><text x=\\"145\\" y=\\"90\\" font-size=\\"13\\">10 cm</text><text x=\\"85\\" y=\\"155\\" font-size=\\"13\\">12 cm</text></svg>",
  "answer": "32 cm",
  "solution": "Üçgenin çevresi = 10 + 10 + 12 = 32 cm.",
  "kazanim_kod": "M.4.3.2"
}

Çıktıyı SADECE JSON formatında üret, ek açıklama yazma."""


class _SvgExample(BaseModel):
    question: str
    answer: str
    solution: str
    kazanim_kod: str


class _SvgBatch(BaseModel):
    examples: list[_SvgExample]


def _build_prompt(
    grade: int,
    kazanimlar: list[Kazanim],
    difficulty: Difficulty,
    count: int,
) -> str:
    # Yalnızca geometri/ölçme kazanımlarını ön plana al — SVG en çok orada işe yarar.
    lines = [
        f"Sınıf: {grade}. sınıf",
        "Konu: Geometri / Ölçme",
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
        f"gorsel_geometri tipinde, birbirinden FARKLI bağlam ve farklı şekiller "
        f"(üçgen / dörtgen / daire / yamuk / paralelkenar / koordinat düzlemi vb.) "
        f"kullanarak {count} adet SVG'li geometri sorusu üret. "
        f"Yukarıdaki SVG kurallarına TAM uy.",
        "",
        'JSON formatı: {"examples": [{"question": "...<svg>...</svg>...", "answer": "...", '
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


def _completed_pairs(examples: list[dict], per_pair: int) -> set[tuple[int, str]]:
    counts: dict[tuple[int, str], int] = {}
    for e in examples:
        k = (e["grade"], e["difficulty"])
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


def _validate_svg_in_question(question: str) -> tuple[bool, str]:
    """question metni en az 1 valid SVG içermeli."""
    blocks = extract_svg_blocks(question)
    if not blocks:
        return False, "SVG bloğu bulunamadı"
    # En az birinin valid olması yeter
    for _, _, svg in blocks:
        ok, _reason = is_valid_svg(svg)
        if ok:
            return True, ""
    return False, "Tüm SVG blokları geçersiz"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--per-pair", type=int, default=3,
                   help="(grade, difficulty) başına örnek sayısı")
    p.add_argument("--grades", type=str, default=None,
                   help="Virgüllü sınıf listesi (örn. 5,6,7). Default: 1-7.")
    p.add_argument("--difficulties", type=str, default="orta",
                   help="Virgüllü difficulty (örn. orta,zor). Default: orta.")
    p.add_argument("--limit", type=int, default=None)
    args = p.parse_args()

    if not settings.gemini_api_key:
        raise SystemExit("GEMINI_API_KEY yok.")

    allowed_grades: set[int] | None = None
    if args.grades:
        allowed_grades = {int(x.strip()) for x in args.grades.split(",")}

    difficulties = [Difficulty(d.strip()) for d in args.difficulties.split(",")]

    examples = _load_existing()
    logger.info("Mevcut: %s", len(examples))
    done = _completed_pairs(examples, args.per_pair)

    # Geometri/ölçme kazanımlarını topla
    work: list[tuple[int, list[Kazanim], Difficulty]] = []
    for grade in sorted(CURRICULUM.keys()):
        if allowed_grades and grade not in allowed_grades:
            continue
        geo_kazanim: list[Kazanim] = []
        for topic_id, topic in CURRICULUM[grade].items():
            if topic_id in ("geometri", "olcme"):
                geo_kazanim.extend(topic["kazanimlar"])
        if not geo_kazanim:
            continue
        for diff in difficulties:
            if (grade, diff.value) in done:
                continue
            work.append((grade, geo_kazanim, diff))

    if args.limit:
        work = work[: args.limit]

    logger.info("Yapılacak ikili: %s (per_pair=%s, beklenen ~%s örnek)",
                len(work), args.per_pair, len(work) * args.per_pair)
    if not work:
        logger.info("Tamamlanmış.")
        return

    client = genai.Client(api_key=settings.gemini_api_key)
    config = types.GenerateContentConfig(
        system_instruction=SVG_SYSTEM_PROMPT,
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

    for i, (grade, kazanimlar, diff) in enumerate(work, 1):
        user_prompt = _build_prompt(grade, kazanimlar, diff, args.per_pair)
        try:
            resp, model_used = _call_with_fallback(client, user_prompt, config)
            batch = _parse(resp)
        except Exception as exc:
            logger.error("[%s/%s] grade=%s diff=%s fail: %s",
                         i, len(work), grade, diff.value, exc)
            continue

        topic_id_by_kod = {
            k["kod"]: tid
            for tid, t in CURRICULUM[grade].items()
            for k in t["kazanimlar"]
        }

        added = 0
        skipped = 0
        for ex in batch.examples[: args.per_pair]:
            ok, reason = _validate_svg_in_question(ex.question)
            if not ok:
                logger.warning("  format-fail: %s | q=%r", reason, ex.question[:80])
                skipped += 1
                continue
            kod = ex.kazanim_kod if ex.kazanim_kod in valid_codes else kazanimlar[0]["kod"]
            examples.append({
                "grade": grade,
                "topic_id": topic_id_by_kod.get(kod, "geometri"),
                "kazanim_kod": kod,
                "difficulty": diff.value,
                "question_type": "gorsel_geometri",
                "question": ex.question.strip(),
                "answer": ex.answer.strip(),
                "solution": ex.solution.strip(),
                "source": f"synthetic_geometry_svg/{model_used}",
            })
            added += 1

        if i % 3 == 0 or i == len(work):
            _save(examples)

        logger.info("[%s/%s] grade=%s diff=%s → +%s (skip=%s, toplam %s) [%s]",
                    i, len(work), grade, diff.value, added, skipped, len(examples), model_used)

    _save(examples)
    logger.info("Tamamlandı. Toplam: %s → %s", len(examples), OUTPUT_PATH)


if __name__ == "__main__":
    main()
