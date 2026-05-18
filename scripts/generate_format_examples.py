"""Sprint 12-A format tipleri (coktan_secmeli, bosluk_doldurma, dogru_yanlis,
eslestirme, siralama) için sentetik üretim.

generate_synthetic_corpus.py ve generate_visual_examples.py pattern'ini takip
eder; tip-spesifik format kuralları sıkı sistem prompt'unda zorlanır.

Çıktı: knowledge_base/processed/format_examples.json — ingest_to_chroma.py
bunu da picker'larsa otomatik dahil eder.

Kullanım:
    python scripts/generate_format_examples.py
    python scripts/generate_format_examples.py --per-pair 3
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


OUTPUT_PATH = ROOT / "knowledge_base" / "processed" / "format_examples.json"
MODELS_TO_TRY = [settings.gemini_model, *settings.fallback_model_list]
MAX_ATTEMPTS_PER_MODEL = 3
BASE_DELAY = 1.5

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("gen_format")


# Hangi tip hangi zorluk seviyesinde anlamlı:
# - DOGRU_YANLIS: sadece kolay (kavram pekiştirme)
# - BOSLUK_DOLDURMA: kolay + orta
# - COKTAN_SECMELI: hepsi (LGS prep)
# - ESLESTIRME: orta + zor (zihinsel ilişki kurma)
# - SIRALAMA: orta + zor (büyüklük/zaman/öncelik)
FORMAT_BY_DIFFICULTY: dict[QuestionType, list[Difficulty]] = {
    QuestionType.COKTAN_SECMELI: [Difficulty.KOLAY, Difficulty.ORTA, Difficulty.ZOR],
    QuestionType.BOSLUK_DOLDURMA: [Difficulty.KOLAY, Difficulty.ORTA],
    QuestionType.DOGRU_YANLIS: [Difficulty.KOLAY],
    QuestionType.ESLESTIRME: [Difficulty.ORTA, Difficulty.ZOR],
    QuestionType.SIRALAMA: [Difficulty.ORTA, Difficulty.ZOR],
}


FORMAT_SYSTEM_PROMPT = """Sen MEB matematik müfredatına uygun FORMAT-SPESIFIK soru üreten bir öğretmen asistanısın.

Her soru kazanım kapsamında olmalı, Türkçe MEB ders kitabı tonunda yazılmalı. Açık uçlu sözel formattan FARKLI olarak aşağıdaki format kalıplarına TAM uy.

KRİTİK: Soru metnine ait TÜM içerik (şıklar, boşluklar, tablolar, dizi öğeleri)
"question" alanı İÇİNDE olmalı — ASLA "question" alanını sadece soru cümlesiyle
sınırlama, formatın gerektirdiği şıklar/tablo/liste her zaman question içine gömülü.

1. COKTAN_SECMELI:
   - "question" ALANI: soru cümlesi + boş satır + 4 şık her biri ayrı satırda
     "A) ...", "B) ...", "C) ...", "D) ..." formatında. ŞIKLAR question alanı
     İÇİNDE OLMALI, ayrı bir alanda DEĞİL.
   - SADECE BİR doğru şık olmalı.
   - Çeldiriciler (yanlış şıklar) MAKUL olmalı — öğrencinin yapabileceği yaygın hatalardan üretilmiş.
   - `answer` SADECE doğru şıkkın harfi: "A", "B", "C" veya "D".
   - `solution` doğru şıkkın neden doğru olduğunu + en az bir yanlış şıkkın neden çeldirici olduğunu açıklar.

   ÖRNEK ÇIKTI (coktan_secmeli):
   {
     "question": "Bir manavda 24 elma ve 18 armut vardır. Manavda toplam kaç meyve bulunmaktadır?\\n\\nA) 32\\nB) 36\\nC) 42\\nD) 48",
     "answer": "C",
     "solution": "Toplam meyve sayısı 24 + 18 = 42'dir. Doğru cevap C. A şıkkı yanlış toplama (24+8), B şıkkı eksik basamak hatası, D şıkkı çarpma hatasıdır.",
     "kazanim_kod": "M.3.1.5"
   }

2. BOSLUK_DOLDURMA:
   - "question" ALANI: soru cümlesi içinde bir veya daha fazla "_____" (en az 5 alt çizgi) bulunmalı.
   - Boşluk soru cümlesinin doğal akışı içinde olsun, başına/sonuna iliştirilmiş gibi DEĞİL.
   - `answer` boşluğa giren ifadeler — birden fazla boşluk varsa soldan sağa "; " ile ayır.

   ÖRNEK ÇIKTI:
   {
     "question": "Bir düzine yumurta _____ adettir. İki düzine yumurta ise _____ adettir.",
     "answer": "12; 24",
     "solution": "Bir düzine 12 tanedir. İki düzine = 2 × 12 = 24.",
     "kazanim_kod": "M.2.1.3"
   }

3. DOGRU_YANLIS:
   - "question" ALANI: SORU DEĞİL — TEK BİR İDDIA/önerme cümlesi (soru işareti OLMASIN, sonu "." ile bitsin).
   - Kazanımın net bir kavram/kuralını test etsin.
   - `answer` SADECE "Doğru" veya "Yanlış" olsun (Türkçe büyük D/Y harfli).
   - `solution` önermenin neden doğru/yanlış olduğunu kazanım çerçevesinde açıklar.

   ÖRNEK ÇIKTI:
   {
     "question": "Bir karenin tüm kenarları birbirine eşit uzunluktadır.",
     "answer": "Doğru",
     "solution": "Kare tanımı gereği dört kenarı eşit uzunlukta olan dörtgendir.",
     "kazanim_kod": "M.2.3.1"
   }

4. ESLESTIRME:
   - "question" ALANI: yönerge cümlesi + boş satır + GFM tablo (her zaman question İÇİNDE):
     | Numara/Öğe | Harf/Karşılık |
     |---|---|
     | 1. ... | a) ... |
     | 2. ... | b) ... |
     | 3. ... | c) ... |
   - Sol kolonda numaralı öğeler, sağ kolonda karıştırılmış sırada harfli karşılıklar.
   - 3 veya 4 satır olsun.
   - `answer` formatı: "1-c, 2-a, 3-b" (numara-harf, virgülle ayrılmış).
   - `solution` her eşleşmenin neden doğru olduğunu satır satır açıklar.

   ÖRNEK ÇIKTI:
   {
     "question": "Aşağıdaki kesirleri ondalık karşılıklarıyla eşleştiriniz.\\n\\n| Kesir | Ondalık |\\n|---|---|\\n| 1. 1/2 | a) 0,25 |\\n| 2. 1/4 | b) 0,75 |\\n| 3. 3/4 | c) 0,5 |",
     "answer": "1-c, 2-a, 3-b",
     "solution": "1/2 = 0,5 → 1-c; 1/4 = 0,25 → 2-a; 3/4 = 0,75 → 3-b.",
     "kazanim_kod": "M.4.2.6"
   }

5. SIRALAMA:
   - "question" ALANI: yönerge (örn. "Aşağıdaki sayıları küçükten büyüğe sıralayınız.") + boş satır + karıştırılmış öğeler (madde işaretli veya virgüllü).
   - 4 veya 5 öğe.
   - `answer` doğru sıralı öğeler " → " (boşluklu Unicode ok U+2192) ile ayrılmış.
   - `solution` sıralama kriterini ve karşılaştırma adımlarını açıklar.

   ÖRNEK ÇIKTI:
   {
     "question": "Aşağıdaki kesirleri küçükten büyüğe doğru sıralayınız.\\n\\n- 3/4\\n- 1/2\\n- 5/8\\n- 7/8",
     "answer": "1/2 → 5/8 → 3/4 → 7/8",
     "solution": "Paydaları eşitleyerek 8'lik paydaya çevirelim: 1/2=4/8, 5/8=5/8, 3/4=6/8, 7/8=7/8. Buna göre 4/8 < 5/8 < 6/8 < 7/8.",
     "kazanim_kod": "M.4.2.5"
   }

Mutlak kurallar:
- Kazanım metni dışına ÇIKMA, üst sınıf bilgisi GEREKTIRMESIN.
- Resim/SVG ÜRETME; sadece metin/Markdown/Unicode.
- Cevap kesin ve doğru olmalı; çözüm net.
- Çıktıyı SADECE istenen JSON formatında üret, ek açıklama yazma."""


class _FormatExample(BaseModel):
    question: str
    answer: str
    solution: str
    kazanim_kod: str


class _FormatBatch(BaseModel):
    examples: list[_FormatExample]


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
        f"{qtype.value} formatında, birbirinden FARKLI bağlam ve "
        f"farklı kazanımlar kullanarak {count} adet soru üret. "
        f"Format kurallarına TAM uy.",
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


def _parse(resp: types.GenerateContentResponse) -> _FormatBatch:
    parsed = getattr(resp, "parsed", None)
    if isinstance(parsed, _FormatBatch):
        return parsed
    return _FormatBatch.model_validate_json(resp.text)


# Tip-spesifik format kontrolleri — LLM prompt'a uymadığında bozuk örnek
# ingest edilmesin diye eler. Her kontrol True/False döner (True = format uygun).
def _is_valid_format(qtype: QuestionType, ex: _FormatExample) -> tuple[bool, str]:
    q = ex.question
    a = ex.answer.strip()
    if qtype is QuestionType.COKTAN_SECMELI:
        # A) B) C) D) işaretçilerinin hepsi olmalı; cevap tek harf A-D
        markers = sum(1 for m in ("A)", "B)", "C)", "D)") if m in q)
        if markers < 4:
            return False, f"şıklar eksik (4'ten az marker: {markers})"
        if a not in {"A", "B", "C", "D"}:
            return False, f"cevap A/B/C/D değil: {a!r}"
    elif qtype is QuestionType.BOSLUK_DOLDURMA:
        if "_____" not in q:
            return False, "soruda boşluk yok"
    elif qtype is QuestionType.DOGRU_YANLIS:
        if q.rstrip().endswith("?"):
            return False, "önerme yerine soru cümlesi"
        if a not in {"Doğru", "Yanlış"}:
            return False, f"cevap Doğru/Yanlış değil: {a!r}"
    elif qtype is QuestionType.ESLESTIRME:
        if "|---|" not in q.replace(" ", ""):
            # GFM tablo ayırıcı ("|---|---|" gibi). Boşlukları kaldırarak kontrol.
            if "| --- |" not in q and "|---" not in q:
                return False, "GFM tablo yok"
        # answer pattern: "N-l, N-l, ..."
        import re as _re
        if not _re.search(r"\d+\s*-\s*[a-zA-ZçğıöşüÇĞİÖŞÜ]", a):
            return False, f"cevap eşleşme formatında değil: {a!r}"
    elif qtype is QuestionType.SIRALAMA:
        if "→" not in a:
            return False, f"cevap ' → ' içermiyor: {a!r}"
    return True, ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-pair", type=int, default=3,
                        help="Her (grade, type, difficulty) üçlüsü için örnek sayısı")
    parser.add_argument("--limit", type=int, default=None,
                        help="Toplam üçlü sayısını sınırla (debug)")
    args = parser.parse_args()

    if not settings.gemini_api_key:
        raise SystemExit("GEMINI_API_KEY .env'de yok.")

    examples = _load_existing()
    logger.info("Mevcut format örnek sayısı: %s", len(examples))
    done = _completed_triples(examples, args.per_pair)
    logger.info("Tamamlanmış üçlü: %s", len(done))

    work: list[tuple[int, list[Kazanim], QuestionType, Difficulty]] = []
    for grade in sorted(CURRICULUM.keys()):
        # Tüm topic kazanımlarını birleştir — format tipleri tüm konularda işler
        all_kazanim: list[Kazanim] = []
        for topic in CURRICULUM[grade].values():
            all_kazanim.extend(topic["kazanimlar"])
        if not all_kazanim:
            continue
        for qtype, difficulties in FORMAT_BY_DIFFICULTY.items():
            for diff in difficulties:
                key = (grade, qtype.value, diff.value)
                if key in done:
                    continue
                work.append((grade, all_kazanim, qtype, diff))

    if args.limit:
        work = work[: args.limit]

    logger.info("Yapılacak üçlü sayısı: %s (per_pair=%s, beklenen toplam ~%s örnek)",
                len(work), args.per_pair, len(work) * args.per_pair)
    if not work:
        logger.info("Zaten tamamlanmış.")
        return

    client = genai.Client(api_key=settings.gemini_api_key)
    config = types.GenerateContentConfig(
        system_instruction=FORMAT_SYSTEM_PROMPT,
        temperature=0.9,
        response_mime_type="application/json",
        response_schema=_FormatBatch,
    )

    valid_kazanim_codes = {
        k["kod"]
        for grade in CURRICULUM.values()
        for topic in grade.values()
        for k in topic["kazanimlar"]
    }

    for i, (grade, kazanimlar, qtype, diff) in enumerate(work, 1):
        topic_name = next(iter(CURRICULUM[grade].values()))["name"]
        user_prompt = _build_prompt(
            grade=grade,
            topic_name=topic_name,
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

        topic_id_by_kod = {
            k["kod"]: tid
            for tid, t in CURRICULUM[grade].items()
            for k in t["kazanimlar"]
        }

        added = 0
        skipped = 0
        for ex in batch.examples[: args.per_pair]:
            ok, reason = _is_valid_format(qtype, ex)
            if not ok:
                logger.warning("  format-fail (%s): %s | q=%r", qtype.value, reason, ex.question[:80])
                skipped += 1
                continue
            kod = ex.kazanim_kod if ex.kazanim_kod in valid_kazanim_codes else kazanimlar[0]["kod"]
            examples.append({
                "grade": grade,
                "topic_id": topic_id_by_kod.get(kod, ""),
                "kazanim_kod": kod,
                "difficulty": diff.value,
                "question_type": qtype.value,
                "question": ex.question.strip(),
                "answer": ex.answer.strip(),
                "solution": ex.solution.strip(),
                "source": f"synthetic_format/{model_used}",
            })
            added += 1

        if i % 3 == 0 or i == len(work):
            _save(examples)

        logger.info("[%s/%s] grade=%s type=%s diff=%s → +%s (skip=%s, toplam %s) [%s]",
                    i, len(work), grade, qtype.value, diff.value, added, skipped, len(examples), model_used)

    _save(examples)
    logger.info("Tamamlandı. Toplam format örnek: %s → %s", len(examples), OUTPUT_PATH)


if __name__ == "__main__":
    main()
