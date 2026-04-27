"""Her (kazanım × zorluk) için çeşitli sentetik örnekler üretir.

RAG için vector store'a yüklenecek corpus'un ham JSON formu.

Kullanım:
    python scripts/generate_synthetic_corpus.py

Özellikler:
    - Resumable: önceki çalıştırmanın çıktılarını okur, eksikleri üretir
    - 503 dayanıklı: her çağrı için model fallback + exponential backoff
    - Her (kazanım, zorluk) için 5 çeşitli örnek (toplam ~1600)
"""
from __future__ import annotations

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

# Proje kökünü path'e ekle
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import settings  # noqa: E402
from app.data.curriculum import CURRICULUM, Kazanim  # noqa: E402
from app.models.enums import Difficulty, QuestionType  # noqa: E402


OUTPUT_PATH = ROOT / "knowledge_base" / "processed" / "synthetic_examples.json"
EXAMPLES_PER_PAIR = 5
MODELS_TO_TRY = [settings.gemini_model, *settings.fallback_model_list]
MAX_ATTEMPTS_PER_MODEL = 3
BASE_DELAY = 1.5

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("gen_corpus")


class _SynthExample(BaseModel):
    question: str
    answer: str
    solution: str
    question_type: QuestionType


class _SynthBatch(BaseModel):
    examples: list[_SynthExample]


SYSTEM_PROMPT = """Sen MEB (Milli Eğitim Bakanlığı) müfredatına hakim bir matematik öğretmeni asistanısın.
Çeşitli, müfredata uygun ve birbirinden farklı sorular üretiyorsun.

Mutlak kurallar:
1. Her soru verilen kazanım metninin kapsamı dahilinde olmalı, dışına çıkmamalı.
2. Sorular zorluk kalibrasyonuna UYMALI (belirtilen sayı aralığı, adım sayısı, karmaşıklık).
3. Aynı batch içindeki sorular BİRBİRİNDEN FARKLI olmalı:
   - Farklı BAĞLAM (pasta, bahçe, para, yol, süre, ağırlık, nesne sayma vb.)
   - Farklı SAYISAL ARALIK
   - Farklı SORU TİPİ (işlem, sözel problem, kavram, akıl yürütme, modelleme, günlük hayat)
4. Görsel/şekil/resim gerektiren sorular ÜRETMEYİN; geometri sorularını sözel verin.
5. Çoktan seçmeli soru üretmeyin; açık uçlu olsun.
6. Her sorunun kesin ve doğru bir cevabı olmalı; matematiksel olarak hatalı soru üretmeyin.
7. Türkçe, MEB ders kitabı tonunda yazın.
8. Çözüm adımlarını mutlaka belirtin.
9. Çıktıyı istenen JSON formatında üretin; ek metin eklemeyin."""


def _load_existing() -> list[dict]:
    if OUTPUT_PATH.exists():
        with OUTPUT_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("examples", [])
    return []


def _save(examples: list[dict]) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUTPUT_PATH.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump({"examples": examples}, f, ensure_ascii=False, indent=2)
    os.replace(tmp, OUTPUT_PATH)


def _completed_keys(examples: list[dict]) -> set[tuple[int, str, str]]:
    """Hangi (grade, kazanim_kod, difficulty) tamamlandı?"""
    counts: dict[tuple[int, str, str], int] = {}
    for e in examples:
        k = (e["grade"], e["kazanim_kod"], e["difficulty"])
        counts[k] = counts.get(k, 0) + 1
    return {k for k, v in counts.items() if v >= EXAMPLES_PER_PAIR}


def _build_prompt(
    grade: int,
    topic_id: str,
    topic_name: str,
    kazanim: Kazanim,
    difficulty: Difficulty,
    count: int,
) -> str:
    hint = kazanim.get("difficulty_hints", {}).get(difficulty.value, "")
    types_list = ", ".join(qt.value for qt in QuestionType)
    return f"""Sınıf: {grade}. sınıf
Konu: {topic_name}
Kazanım Kodu: {kazanim["kod"]}
Kazanım Metni: {kazanim["metin"]}
Zorluk: {difficulty.value}
Zorluk Kalibrasyonu: {hint}

Üretilecek Soru Sayısı: {count}
Kullanılabilir Soru Tipleri: {types_list}

Yukarıdaki kazanım ve kalibrasyona uygun, birbirinden farklı {count} soru üret.
Her soruda FARKLI bir bağlam ve FARKLI sayı aralığı kullan. Soru tiplerini çeşitlendir.
Çıktı formatı: {{"examples": [{{"question": "...", "answer": "...", "solution": "...", "question_type": "..."}}, ...]}}"""


def _call_gemini_with_fallback(
    client: genai.Client,
    user_prompt: str,
    config: types.GenerateContentConfig,
) -> tuple[types.GenerateContentResponse, str]:
    last_exc: Exception | None = None
    for model_name in MODELS_TO_TRY:
        for attempt in range(1, MAX_ATTEMPTS_PER_MODEL + 1):
            try:
                resp = client.models.generate_content(
                    model=model_name,
                    contents=user_prompt,
                    config=config,
                )
                return resp, model_name
            except genai_errors.ServerError as exc:
                last_exc = exc
                status = getattr(exc, "code", None)
                if status not in (500, 502, 503, 504):
                    raise
                if attempt == MAX_ATTEMPTS_PER_MODEL:
                    logger.warning("[%s] %s deneme sonrası 503, fallback'e geçiliyor.", model_name, attempt)
                    break
                delay = BASE_DELAY * (2 ** (attempt - 1)) + random.uniform(0, 0.4)
                logger.warning("[%s] 503, %.1fs sonra retry (%s/%s)", model_name, delay, attempt, MAX_ATTEMPTS_PER_MODEL)
                time.sleep(delay)
    raise RuntimeError(f"Tüm modeller tükendi: {last_exc}")


def _parse(resp: types.GenerateContentResponse) -> _SynthBatch:
    parsed = getattr(resp, "parsed", None)
    if isinstance(parsed, _SynthBatch):
        return parsed
    return _SynthBatch.model_validate_json(resp.text)


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=None, help="İşlenecek maksimum (kazanım, zorluk) çifti")
    p.add_argument("--grades", type=str, default=None, help="Virgülle ayrılmış sınıf listesi (örn. '5' veya '5,7')")
    args = p.parse_args()

    if not settings.gemini_api_key:
        raise SystemExit("GEMINI_API_KEY .env'de yok.")

    allowed_grades: set[int] | None = None
    if args.grades:
        allowed_grades = {int(g.strip()) for g in args.grades.split(",")}
        logger.info("Yalnızca şu sınıflar: %s", sorted(allowed_grades))

    examples = _load_existing()
    logger.info("Mevcut örnek sayısı: %s", len(examples))

    done = _completed_keys(examples)
    logger.info("Tamamlanmış (kazanım, zorluk) çifti: %s", len(done))

    client = genai.Client(api_key=settings.gemini_api_key)
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0.95,
        response_mime_type="application/json",
        response_schema=_SynthBatch,
    )

    total_pairs = 0
    work: list[tuple[int, str, str, Kazanim, Difficulty]] = []
    for grade, topics in CURRICULUM.items():
        if allowed_grades is not None and grade not in allowed_grades:
            continue
        for topic_id, topic in topics.items():
            for k in topic["kazanimlar"]:
                for d in Difficulty:
                    total_pairs += 1
                    key = (grade, k["kod"], d.value)
                    if key in done:
                        continue
                    work.append((grade, topic_id, topic["name"], k, d))

    if args.limit is not None:
        work = work[: args.limit]

    logger.info("Yapılacak çift sayısı: %s / %s", len(work), total_pairs)
    if not work:
        logger.info("Zaten tamamlanmış. %s örnek mevcut.", len(examples))
        return

    for i, (grade, topic_id, topic_name, kazanim, difficulty) in enumerate(work, 1):
        user_prompt = _build_prompt(
            grade, topic_id, topic_name, kazanim, difficulty, EXAMPLES_PER_PAIR
        )
        try:
            resp, model_used = _call_gemini_with_fallback(client, user_prompt, config)
            batch = _parse(resp)
        except Exception as exc:
            logger.error("[%s/%s] %s %s %s başarısız: %s", i, len(work), grade, kazanim["kod"], difficulty.value, exc)
            continue

        added = 0
        for ex in batch.examples[:EXAMPLES_PER_PAIR]:
            examples.append({
                "grade": grade,
                "topic_id": topic_id,
                "kazanim_kod": kazanim["kod"],
                "difficulty": difficulty.value,
                "question_type": ex.question_type.value,
                "question": ex.question.strip(),
                "answer": ex.answer.strip(),
                "solution": ex.solution.strip(),
                "source": f"synthetic/{model_used}",
            })
            added += 1

        if i % 5 == 0 or i == len(work):
            _save(examples)

        logger.info("[%s/%s] %s %s %s → +%s örnek (toplam %s) [%s]",
                    i, len(work), grade, kazanim["kod"], difficulty.value, added, len(examples), model_used)

    _save(examples)
    logger.info("Tamamlandı. Toplam örnek: %s → %s", len(examples), OUTPUT_PATH)


if __name__ == "__main__":
    main()
