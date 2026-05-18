"""Görsel/yapısal soru tipleri için sentetik üretim.

generate_synthetic_corpus.py system prompt'unda "Görsel/şekil/resim gerektiren
sorular ÜRETMEYİN" yazıyor → bu tipler için ChromaDB ve sentetik corpus'ta hiç
örnek yok. Bu script o boşluğu doldurmak için ayrı bir prompt ile sadece
salt_islem / tablo_sorusu / gorsel_geometri / grafik_okuma / oruntu_sekil
tiplerinde örnek üretir.

Çıktı: knowledge_base/processed/visual_examples.json — ingest_to_chroma.py
bunu da picker'larsa otomatik dahil eder (aynı şema).

Kullanım:
    python scripts/generate_visual_examples.py
    python scripts/generate_visual_examples.py --per-pair 3
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


OUTPUT_PATH = ROOT / "knowledge_base" / "processed" / "visual_examples.json"
MODELS_TO_TRY = [settings.gemini_model, *settings.fallback_model_list]
MAX_ATTEMPTS_PER_MODEL = 3
BASE_DELAY = 1.5

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("gen_visual")


# Hangi görsel tip hangi sınıftan itibaren anlamlı (alt sınıflarda Markdown
# tablo/grafik henüz çocukların okuma seviyesine uygun değil).
VISUAL_TYPE_BY_GRADE: dict[int, list[QuestionType]] = {
    1: [QuestionType.GORSEL_GEOMETRI, QuestionType.ORUNTU_SEKIL],
    2: [QuestionType.GORSEL_GEOMETRI, QuestionType.ORUNTU_SEKIL, QuestionType.TABLO_SORUSU],
    3: [
        QuestionType.GORSEL_GEOMETRI, QuestionType.ORUNTU_SEKIL,
        QuestionType.TABLO_SORUSU, QuestionType.GRAFIK_OKUMA,
        QuestionType.SALT_ISLEM,
    ],
    4: [
        QuestionType.GORSEL_GEOMETRI, QuestionType.ORUNTU_SEKIL,
        QuestionType.TABLO_SORUSU, QuestionType.GRAFIK_OKUMA,
        QuestionType.SALT_ISLEM,
    ],
    5: [
        QuestionType.GORSEL_GEOMETRI, QuestionType.TABLO_SORUSU,
        QuestionType.GRAFIK_OKUMA, QuestionType.SALT_ISLEM,
        QuestionType.ORUNTU_SEKIL,
    ],
    6: [
        QuestionType.GORSEL_GEOMETRI, QuestionType.TABLO_SORUSU,
        QuestionType.GRAFIK_OKUMA, QuestionType.SALT_ISLEM,
    ],
    7: [
        QuestionType.GORSEL_GEOMETRI, QuestionType.TABLO_SORUSU,
        QuestionType.GRAFIK_OKUMA, QuestionType.SALT_ISLEM,
    ],
}

# Her görsel tip için: hangi konu(lar) doğal yatağı?
TYPE_PREFERRED_TOPICS: dict[QuestionType, list[str]] = {
    QuestionType.GORSEL_GEOMETRI: ["geometri", "olcme"],
    QuestionType.ORUNTU_SEKIL: ["dogal_sayilar", "geometri", "cebir"],
    QuestionType.TABLO_SORUSU: ["veri_isleme", "dogal_sayilar", "olcme"],
    QuestionType.GRAFIK_OKUMA: ["veri_isleme"],
    QuestionType.SALT_ISLEM: ["dogal_sayilar", "kesirler", "cebir"],
}


VISUAL_SYSTEM_PROMPT = """Sen MEB matematik müfredatına uygun, GÖRSEL/YAPISAL içerikli soru üreten bir öğretmen asistanısın.

Yalnızca Markdown ve Unicode karakterler kullan; resim/SVG ÜRETME. Her soru \"question\" alanı içine Markdown blokları gömülmüş olmalı.

Soru tipi spesifik formatlar — TAM olarak şu kalıpları kullan:

1. SALT_ISLEM:
   Sadece matematiksel ifade ve sonunda \"= ?\". Türkçe açıklama olmasın.
   Örnek: \"(12 + 8) × 3 ÷ 5 = ?\"  veya  \"3/4 + 1/6 = ?\"

2. TABLO_SORUSU:
   Soru cümlesi + boş satır + GFM tablo + boş satır + tabloya dayalı hesap sorusu.
   Tablo formatı:
   ```
   | Başlık | ... |
   |---|---|
   | satır1 | ... |
   ```

3. GORSEL_GEOMETRI:
   Soru cümlesi + boş satır + ```kod bloğu``` içinde Unicode geometri şekli (△ □ ○ ◇ ▲ ● ▢ ▭) + ölçü etiketleri (kenar uzunluğu/açı) + boş satır + hesap sorusu.
   Örnek:
   ```
       △
      / \\
     /   \\
    /__a__\\
       a = 6 cm
   ```

4. GRAFIK_OKUMA:
   Soru cümlesi + boş satır + ```kod bloğu``` içinde ASCII sütun grafiği (█ veya ▇ karakterleriyle) + her sütuna etiket + değer + boş satır + grafiğe dayalı soru.
   Örnek:
   ```
   Ocak  █████ 50
   Şubat ████████ 80
   Mart  ███ 30
   ```

5. ORUNTU_SEKIL:
   Soru cümlesi + Unicode sembol veya emoji dizisi (♥ ♦ ♠ ★ ▲ ● 🔴 🔵 🟢) DÜZENLİ aralıklı + en sonda \"?\" ile devam eden örüntü.
   Örnek: ♥ ♥ ♦ ♥ ♥ ♦ ♥ ?

Mutlak kurallar:
- Her soru istenen kazanım metninin kapsamı DAHİLİNDE olmalı, üst sınıf bilgisi GEREKTİRMESİN.
- Şekil/tablo/grafik içindeki sayısal değerler ile soru/cevap TUTARLI olmalı.
- Cevap kesin ve doğru olmalı; çözüm adımları açık.
- Türkçe MEB ders kitabı tonunda yaz.
- Çıktıyı sadece istenen JSON formatında üret; ek açıklama yazma."""


class _VisualExample(BaseModel):
    question: str
    answer: str
    solution: str
    kazanim_kod: str


class _VisualBatch(BaseModel):
    examples: list[_VisualExample]


def _build_prompt(
    grade: int,
    topic_name: str,
    topic_id: str,
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
        "Kazanım seçenekleri (her sorunda biriyle etiketlemen gerekiyor):",
    ]
    for k in kazanimlar:
        hint = k.get("difficulty_hints", {}).get(difficulty.value, "")
        lines.append(f"  - {k['kod']}: {k['metin']}")
        if hint:
            lines.append(f"      Zorluk: {hint}")
    lines.extend([
        "",
        f"Yukarıdaki kazanımlardan FARKLI olanları seçerek {count} adet "
        f"{qtype.value} tipinde soru üret. Her soru farklı bir bağlam ve "
        f"farklı sayısal değer kullansın.",
        "",
        'JSON formatı: {"examples": [{"question": "...", "answer": "...", '
        '"solution": "...", "kazanim_kod": "..."}, ...]}',
    ])
    return "\n".join(lines)


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
                    logger.warning("[%s] %s deneme sonrası hata, fallback'e geçiliyor.", model_name, attempt)
                    break
                delay = BASE_DELAY * (2 ** (attempt - 1)) + random.uniform(0, 0.4)
                logger.warning("[%s] retry %.1fs (%s/%s)", model_name, delay, attempt, MAX_ATTEMPTS_PER_MODEL)
                time.sleep(delay)
    raise RuntimeError(f"Tüm modeller tükendi: {last_exc}")


def _parse(resp: types.GenerateContentResponse) -> _VisualBatch:
    parsed = getattr(resp, "parsed", None)
    if isinstance(parsed, _VisualBatch):
        return parsed
    return _VisualBatch.model_validate_json(resp.text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-pair", type=int, default=3,
                        help="Her (grade, type, difficulty) için örnek sayısı")
    parser.add_argument("--difficulties", type=str, default="orta",
                        help="Virgüllü difficulty listesi (orta|kolay|zor). "
                        "Hedef: tip kapsamını doldurmak; varsayılan sadece orta.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Toplam (grade,type,diff) üçlü sayısını sınırla (debug)")
    args = parser.parse_args()

    if not settings.gemini_api_key:
        raise SystemExit("GEMINI_API_KEY .env'de yok.")

    difficulties = [Difficulty(d.strip()) for d in args.difficulties.split(",")]

    examples = _load_existing()
    logger.info("Mevcut görsel örnek sayısı: %s", len(examples))
    done = _completed_triples(examples, args.per_pair)
    logger.info("Tamamlanmış üçlü: %s", len(done))

    work: list[tuple[int, str, str, list[Kazanim], QuestionType, Difficulty]] = []
    for grade in sorted(VISUAL_TYPE_BY_GRADE.keys()):
        if grade not in CURRICULUM:
            continue
        for qtype in VISUAL_TYPE_BY_GRADE[grade]:
            preferred_topics = TYPE_PREFERRED_TOPICS.get(qtype, [])
            # Kazanım pool'unu kur
            kazanimlar: list[Kazanim] = []
            topic_id_for_record = ""
            for topic_id, topic in CURRICULUM[grade].items():
                if preferred_topics and topic_id not in preferred_topics:
                    continue
                kazanimlar.extend(topic["kazanimlar"])
                if not topic_id_for_record:
                    topic_id_for_record = topic_id
            if not kazanimlar:
                # Fallback: sınıf-konu hiyerarşisinde preferred yoksa hepsini al
                for topic_id, topic in CURRICULUM[grade].items():
                    kazanimlar.extend(topic["kazanimlar"])
                    if not topic_id_for_record:
                        topic_id_for_record = topic_id
            for diff in difficulties:
                key = (grade, qtype.value, diff.value)
                if key in done:
                    continue
                work.append((grade, topic_id_for_record, "auto", kazanimlar, qtype, diff))

    if args.limit:
        work = work[: args.limit]

    logger.info("Yapılacak üçlü sayısı: %s (per_pair=%s)", len(work), args.per_pair)
    if not work:
        logger.info("Zaten tamamlanmış.")
        return

    client = genai.Client(api_key=settings.gemini_api_key)
    config = types.GenerateContentConfig(
        system_instruction=VISUAL_SYSTEM_PROMPT,
        temperature=0.9,
        response_mime_type="application/json",
        response_schema=_VisualBatch,
    )

    valid_kazanim_codes = {
        k["kod"]
        for grade in CURRICULUM.values()
        for topic in grade.values()
        for k in topic["kazanimlar"]
    }

    for i, (grade, topic_id_record, _, kazanimlar, qtype, diff) in enumerate(work, 1):
        # CURRICULUM topic listesini sınıf bazında al (prompt için)
        topic_name = next(iter(CURRICULUM[grade].values()))["name"]
        user_prompt = _build_prompt(
            grade=grade,
            topic_name=topic_name,
            topic_id=topic_id_record,
            kazanimlar=kazanimlar,
            qtype=qtype,
            difficulty=diff,
            count=args.per_pair,
        )
        try:
            resp, model_used = _call_with_fallback(client, user_prompt, config)
            batch = _parse(resp)
        except Exception as exc:
            logger.error("[%s/%s] grade=%s type=%s diff=%s başarısız: %s",
                         i, len(work), grade, qtype.value, diff.value, exc)
            continue

        # Kazanım kodunu doğrula; topic_id'yi kazanım üzerinden bul
        topic_id_by_kod = {
            k["kod"]: tid
            for tid, t in CURRICULUM[grade].items()
            for k in t["kazanimlar"]
        }

        added = 0
        for ex in batch.examples[: args.per_pair]:
            kod = ex.kazanim_kod if ex.kazanim_kod in valid_kazanim_codes else kazanimlar[0]["kod"]
            examples.append({
                "grade": grade,
                "topic_id": topic_id_by_kod.get(kod, topic_id_record),
                "kazanim_kod": kod,
                "difficulty": diff.value,
                "question_type": qtype.value,
                "question": ex.question.strip(),
                "answer": ex.answer.strip(),
                "solution": ex.solution.strip(),
                "source": f"synthetic_visual/{model_used}",
            })
            added += 1

        if i % 3 == 0 or i == len(work):
            _save(examples)

        logger.info("[%s/%s] grade=%s type=%s diff=%s → +%s (toplam %s) [%s]",
                    i, len(work), grade, qtype.value, diff.value, added, len(examples), model_used)

    _save(examples)
    logger.info("Tamamlandı. Toplam görsel örnek: %s → %s", len(examples), OUTPUT_PATH)


if __name__ == "__main__":
    main()
