"""Sprint 12-B / Phase C — salt_islem için LaTeX-tabanlı sentetik üretim.

`3/4 + 1/6 = ?` gibi düz metin yerine `$$\\frac{3}{4} + \\frac{1}{6} = ?$$`
LaTeX matematik notasyonu üretir. Frontend rehype-katex ile gerçek
matematik sembollerine, PDF matplotlib mathtext ile PNG'ye dönüştürür.

Validator: question alanı en az 1 $...$ veya $$...$$ bloğu içermeli;
matplotlib mathtext ile parse edilebilir olmalı (render edilebiliyorsa OK).

Çıktı: knowledge_base/processed/salt_islem_latex_examples.json
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
from app.services.math_renderer import extract_latex_blocks, render_latex_to_png  # noqa: E402


OUTPUT_PATH = ROOT / "knowledge_base" / "processed" / "salt_islem_latex_examples.json"
MODELS_TO_TRY = [settings.gemini_model, *settings.fallback_model_list]
MAX_ATTEMPTS_PER_MODEL = 3
BASE_DELAY = 1.5

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("gen_salt_islem")


# salt_islem doğal yatağı: işlem konuları
TYPE_PREFERRED_TOPICS = ["dogal_sayilar", "kesirler", "cebir", "olcme"]


LATEX_SYSTEM_PROMPT = """Sen MEB matematik müfredatına uygun, SADECE MATEMATİKSEL İFADE içeren salt_islem soruları üreten bir asistansın.

Kurallar:

1. Format:
   - "question" alanı SADECE matematik ifadesi olsun, Türkçe açıklama YASAK.
   - İfadeyi `$$...$$` (display mode, tercih edilen) veya `$...$` (inline) sınırlayıcılarıyla yaz.
   - İfade sonunda " = ?" ya da "= ?$$" olmalı.

2. LaTeX subset (matplotlib mathtext desteği — BUNUN DIŞINI KULLANMA):
   - Kesir: `\\frac{a}{b}`
   - Kök: `\\sqrt{x}` veya `\\sqrt[n]{x}`
   - Üs: `^{n}` veya `^2` (tek karakter parantezsiz)
   - Alt indis: `_{n}`
   - Operatörler: `+`, `-`, `\\times`, `\\div`, `\\cdot`, `\\pm`
   - Eşitsizlik: `\\leq`, `\\geq`, `\\neq`, `<`, `>`, `=`
   - Parantezler: `()`, `[]`, `\\{`, `\\}` (literal süslü için)
   - Yunan harfleri: `\\alpha`, `\\beta`, `\\pi`, `\\theta` vs.
   - Trigonometri: `\\sin`, `\\cos`, `\\tan`
   - Toplama: `\\sum`, integral: `\\int`

3. YASAK (mathtext desteklemiyor):
   - `\\begin{cases}`, `\\begin{matrix}` gibi environment'lar
   - `\\text{...}` (Türkçe yazma)
   - Karmaşık paket komutları

4. Cevap:
   - "answer" SADECE sayısal sonuç + (gerekirse) birim (örn. "11/12", "144", "x = 4").
   - LaTeX kullanma cevapta — düz metin yeter.

5. Çözüm:
   - "solution" adım adım Türkçe açıklama. İçinde inline `$...$` LaTeX kullanılabilir.

ÖRNEK ÇIKTI 1 (kesir):
{
  "question": "$$\\\\frac{3}{4} + \\\\frac{1}{6} = ?$$",
  "answer": "11/12",
  "solution": "Paydalar 12 ile eşitle: $\\\\frac{9}{12} + \\\\frac{2}{12} = \\\\frac{11}{12}$.",
  "kazanim_kod": "M.5.1.6"
}

ÖRNEK ÇIKTI 2 (üs + kök):
{
  "question": "$$\\\\sqrt{144} + 5^2 = ?$$",
  "answer": "37",
  "solution": "$\\\\sqrt{144} = 12$ ve $5^2 = 25$. Toplamı $12 + 25 = 37$.",
  "kazanim_kod": "M.6.1.4"
}

ÖRNEK ÇIKTI 3 (denklem):
{
  "question": "$$2x + 7 = 15 \\\\Rightarrow x = ?$$",
  "answer": "4",
  "solution": "Her iki taraftan 7 çıkar: $2x = 8$. İki tarafı 2'ye böl: $x = 4$.",
  "kazanim_kod": "M.6.2.2"
}

Çıktıyı SADECE JSON formatında üret, ek açıklama yazma."""


class _LatexExample(BaseModel):
    question: str
    answer: str
    solution: str
    kazanim_kod: str


class _LatexBatch(BaseModel):
    examples: list[_LatexExample]


def _build_prompt(
    grade: int,
    kazanimlar: list[Kazanim],
    difficulty: Difficulty,
    count: int,
) -> str:
    lines = [
        f"Sınıf: {grade}. sınıf",
        f"Konu: Doğal sayılar / Kesirler / Cebir",
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
        f"salt_islem tipinde, birbirinden FARKLI matematik ifadeleri kullanarak "
        f"{count} adet LaTeX-formatlı soru üret. mathtext subset'in dışına "
        f"ÇIKMA. Her ifade `$...$` veya `$$...$$` ile sarılı olmalı.",
        "",
        'JSON: {"examples": [{"question": "$$...$$", "answer": "...", '
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


def _call_with_fallback(client, user_prompt, config):
    last_exc = None
    for model_name in MODELS_TO_TRY:
        for attempt in range(1, MAX_ATTEMPTS_PER_MODEL + 1):
            try:
                return client.models.generate_content(
                    model=model_name, contents=user_prompt, config=config,
                ), model_name
            except genai_errors.ServerError as exc:
                last_exc = exc
                code = getattr(exc, "code", None)
                if code not in (500, 502, 503, 504):
                    raise
                if attempt == MAX_ATTEMPTS_PER_MODEL:
                    break
                delay = BASE_DELAY * (2 ** (attempt - 1)) + random.uniform(0, 0.4)
                logger.warning("[%s] retry %.1fs", model_name, delay)
                time.sleep(delay)
    raise RuntimeError(f"Tüm modeller tükendi: {last_exc}")


def _parse(resp) -> _LatexBatch:
    parsed = getattr(resp, "parsed", None)
    if isinstance(parsed, _LatexBatch):
        return parsed
    return _LatexBatch.model_validate_json(resp.text)


def _validate(question: str) -> tuple[bool, str]:
    """En az 1 LaTeX bloğu olmalı + matplotlib parse edebilmeli."""
    blocks = extract_latex_blocks(question)
    if not blocks:
        return False, "LaTeX bloğu bulunamadı ($...$ veya $$...$$)"
    # En az birinin render edilebilir olması yeterli (mathtext parse-check)
    for _, _, content, _ in blocks:
        png = render_latex_to_png(content)
        if png:
            return True, ""
    return False, "Tüm LaTeX blokları mathtext ile render edilemedi"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--per-pair", type=int, default=4)
    p.add_argument("--grades", type=str, default="3,4,5,6,7",
                   help="Virgüllü sınıf — varsayılan 3-7 (salt_islem üst sınıflar için)")
    p.add_argument("--difficulties", type=str, default="orta,zor")
    p.add_argument("--limit", type=int, default=None)
    args = p.parse_args()

    if not settings.gemini_api_key:
        raise SystemExit("GEMINI_API_KEY yok.")

    allowed_grades = {int(x.strip()) for x in args.grades.split(",")}
    difficulties = [Difficulty(d.strip()) for d in args.difficulties.split(",")]

    examples = _load_existing()
    logger.info("Mevcut: %s", len(examples))
    done = _completed_pairs(examples, args.per_pair)

    work = []
    for grade in sorted(allowed_grades):
        if grade not in CURRICULUM:
            continue
        kazanimlar: list[Kazanim] = []
        for topic_id, topic in CURRICULUM[grade].items():
            if topic_id in TYPE_PREFERRED_TOPICS:
                kazanimlar.extend(topic["kazanimlar"])
        if not kazanimlar:
            for topic in CURRICULUM[grade].values():
                kazanimlar.extend(topic["kazanimlar"])
        for diff in difficulties:
            if (grade, diff.value) in done:
                continue
            work.append((grade, kazanimlar, diff))

    if args.limit:
        work = work[: args.limit]

    logger.info("Yapılacak: %s (per_pair=%s, beklenen ~%s)",
                len(work), args.per_pair, len(work) * args.per_pair)
    if not work:
        return

    client = genai.Client(api_key=settings.gemini_api_key)
    config = types.GenerateContentConfig(
        system_instruction=LATEX_SYSTEM_PROMPT,
        temperature=0.85,
        response_mime_type="application/json",
        response_schema=_LatexBatch,
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
            logger.error("[%s/%s] g=%s d=%s fail: %s", i, len(work), grade, diff.value, exc)
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
                logger.warning("  fail: %s | q=%r", reason, ex.question[:80])
                skipped += 1
                continue
            kod = ex.kazanim_kod if ex.kazanim_kod in valid_codes else kazanimlar[0]["kod"]
            examples.append({
                "grade": grade,
                "topic_id": topic_id_by_kod.get(kod, "dogal_sayilar"),
                "kazanim_kod": kod,
                "difficulty": diff.value,
                "question_type": "salt_islem",
                "question": ex.question.strip(),
                "answer": ex.answer.strip(),
                "solution": ex.solution.strip(),
                "source": f"synthetic_salt_islem_latex/{model_used}",
            })
            added += 1

        if i % 3 == 0 or i == len(work):
            _save(examples)

        logger.info("[%s/%s] g=%s d=%s → +%s (skip=%s, toplam %s) [%s]",
                    i, len(work), grade, diff.value, added, skipped, len(examples), model_used)

    _save(examples)
    logger.info("Tamamlandı. Toplam: %s → %s", len(examples), OUTPUT_PATH)


if __name__ == "__main__":
    main()
