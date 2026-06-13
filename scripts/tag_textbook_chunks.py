"""Ders kitabı chunk'larını Gemini ile MEB kazanımlarına etiketler.

Kullanım:
    python scripts/tag_textbook_chunks.py --grade 5
    python scripts/tag_textbook_chunks.py --grade 6 --batch 4

Çıktı: knowledge_base/processed/textbook_chunks_grade{N}_tagged.json
Resumable: var olan dosyada `tagged: true` olan chunk'lar atlanır.

Karar matrisi (LLM tarafından doldurulur):
    - kazanim_kod: M.{grade}.x.x  → eşleşme bulundu
    - kazanim_kod: null           → mevcut müfredatta karşılığı yok (curriculum_expansion)
    - confidence: high/medium/low
    - mapped_topic_hint: kullanıcıya yardımcı, eşleşmediğinde "Çarpanlar" gibi konu ipucu
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import settings  # noqa: E402
from app.data.curriculum import CURRICULUM  # noqa: E402

PROCESSED_DIR = ROOT / "knowledge_base" / "processed"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("tag")


class TagResult(BaseModel):
    chunk_id: str = Field(description="Etiketlenen chunk'ın id'si")
    kazanim_kod: str | None = Field(
        description="Eşleşen MEB kazanım kodu (örn 'M.5.1.3'). Mevcut müfredatta karşılık yoksa null."
    )
    confidence: str = Field(
        description="'high' | 'medium' | 'low'. Eşleşme güveni."
    )
    mapped_topic_hint: str | None = Field(
        default=None,
        description="kazanim_kod=null ise konu adı tahmini (örn 'Çarpanlar', 'Olasılık'). Aksi halde null.",
    )
    content_quality: str = Field(
        description="'usable' | 'noisy' | 'unusable'. Metnin RAG için kullanılabilirliği."
    )


class TagBatch(BaseModel):
    results: list[TagResult]


def _kazanim_listesi_text(grade: int) -> str:
    lines = [f"MEB {grade}. SINIF KAZANIMLARI:"]
    for tid, t in CURRICULUM[grade].items():
        lines.append(f"\n[{t['name']}]")
        for k in t["kazanimlar"]:
            lines.append(f"  {k['kod']}: {k['metin']}")
    return "\n".join(lines)


def _system_instruction(grade: int) -> str:
    return f"""Sen MEB matematik müfredatı uzmanısın. Görevin: {grade}. sınıf matematik ders kitabından alınmış metin parçalarını uygun MEB kazanım koduyla eşlemek.

Kurallar:
1. Her chunk için EN UYGUN tek bir kazanım kodu seç. Birden fazla kazanım uyuyorsa en spesifik olanı seç.
2. Chunk içeriği aşağıdaki kazanımların HİÇBİRİYLE örtüşmüyorsa kazanim_kod=null döndür ve mapped_topic_hint'e "Çarpanlar / Asal sayılar / Olasılık / İstatistik / Algoritma / Diğer" gibi YENİ MEB 2024 müfredatından bir konu adı yaz.
3. Confidence:
   - high: kazanım metniyle birebir veya çok yakın
   - medium: konu uyuyor ama farklı alt başlık
   - low: zorlama eşleşme, kullanılmayabilir
4. content_quality:
   - usable: metin akıcı, tek başına anlamlı, soru/etkinlik/kavram net
   - noisy: bazı OCR/extraction artıkları var ama içerik anlaşılır
   - unusable: çoğunlukla kopuk harfler, koordinat işaretleri, anlamsız parça
5. ASLA tahmin etme. Emin değilsen confidence=low + mapped_topic_hint kullan."""


def _load_input_chunks(input_path: Path) -> list[dict]:
    data = json.load(input_path.open(encoding="utf-8"))
    return data["chunks"]


def _load_existing_tags(output_path: Path) -> dict[str, dict]:
    if not output_path.exists():
        return {}
    data = json.load(output_path.open(encoding="utf-8"))
    return {c["chunk_id"]: c for c in data.get("chunks", []) if c.get("tagged")}


def _save_tags(all_chunks: list[dict], output_path: Path, grade: int) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "grade": grade,
        "total": len(all_chunks),
        "tagged_count": sum(1 for c in all_chunks if c.get("tagged")),
        "chunks": all_chunks,
    }
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _build_user_prompt(batch: list[dict], kazanim_text: str) -> str:
    lines = [
        kazanim_text,
        "",
        "=" * 60,
        "Aşağıdaki ders kitabı metin parçalarını yukarıdaki kazanımlardan biriyle eşle.",
        "Her parça için chunk_id'yi koruyarak TagResult döndür.",
        "Eşleşme yoksa kazanim_kod=null ve mapped_topic_hint doldur.",
        "",
    ]
    for i, ch in enumerate(batch, 1):
        header_info = f" | Başlık: {ch['header']}" if ch.get("header") else ""
        lines.append(
            f"--- CHUNK {i} | id={ch['chunk_id']} | tip={ch['content_type']}"
            f" | sayfa {ch['page_start']}{header_info} ---"
        )
        lines.append(ch["text"][:1800])
        lines.append("")
    return "\n".join(lines)


def _call_gemini_with_backoff(
    client: genai.Client,
    model: str,
    prompt: str,
    grade: int,
    max_attempts: int = 3,
    base_delay: float = 1.5,
) -> TagBatch:
    config = types.GenerateContentConfig(
        system_instruction=_system_instruction(grade),
        temperature=0.0,
        response_mime_type="application/json",
        response_schema=TagBatch,
    )
    last_exc: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=config,
            )
            parsed = getattr(response, "parsed", None)
            if isinstance(parsed, TagBatch):
                return parsed
            text = getattr(response, "text", None) or ""
            return TagBatch.model_validate_json(text)
        except genai_errors.ServerError as exc:
            last_exc = exc
            status = getattr(exc, "code", None)
            if status not in (500, 502, 503, 504) or attempt == max_attempts:
                raise
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning("503 (deneme %s/%s); %.1fs sonra retry", attempt, max_attempts, delay)
            time.sleep(delay)
        except Exception as exc:
            last_exc = exc
            raise
    raise RuntimeError(f"Tüm denemeler başarısız: {last_exc}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--grade", type=int, required=True, help="Sınıf (1-8)")
    parser.add_argument("--batch", type=int, default=4, help="Bir Gemini çağrısındaki chunk sayısı")
    parser.add_argument("--limit", type=int, default=None, help="Test için maksimum chunk sayısı")
    parser.add_argument(
        "--model",
        type=str,
        default=settings.gemini_model,
        help="Tagging için kullanılacak Gemini modeli",
    )
    args = parser.parse_args()

    if not settings.gemini_api_key:
        raise SystemExit("GEMINI_API_KEY .env'de yok.")

    grade = args.grade
    input_path = PROCESSED_DIR / f"textbook_chunks_grade{grade}.json"
    output_path = PROCESSED_DIR / f"textbook_chunks_grade{grade}_tagged.json"
    if grade not in CURRICULUM:
        raise SystemExit(f"Curriculum'da {grade}. sınıf tanımlı değil.")
    if not input_path.exists():
        raise SystemExit(f"Input yok: {input_path} — önce extract_textbook.py çalıştırın.")

    src_chunks = _load_input_chunks(input_path)
    existing = _load_existing_tags(output_path)
    logger.info("Toplam input: %s | mevcut etiketli: %s", len(src_chunks), len(existing))

    # Etiketlenmiş ve etiketlenmemiş listeyi hazırla
    merged: list[dict] = []
    pending: list[dict] = []
    for ch in src_chunks:
        if ch["chunk_id"] in existing:
            merged.append(existing[ch["chunk_id"]])
        else:
            base = dict(ch)
            base["tagged"] = False
            base["kazanim_kod_llm"] = None
            base["confidence"] = None
            base["mapped_topic_hint"] = None
            base["content_quality"] = None
            merged.append(base)
            pending.append(base)

    if args.limit:
        pending = pending[: args.limit]

    if not pending:
        logger.info("Etiketlenecek chunk yok.")
        return

    logger.info(
        "Etiketlenecek: %s chunk | grade=%s | model=%s | batch=%s",
        len(pending), grade, args.model, args.batch,
    )

    client = genai.Client(api_key=settings.gemini_api_key)
    kazanim_text = _kazanim_listesi_text(grade)

    by_id: dict[str, dict] = {c["chunk_id"]: c for c in merged}

    save_every = max(1, 10 // args.batch)
    batches_done = 0

    for start in range(0, len(pending), args.batch):
        batch = pending[start : start + args.batch]
        prompt = _build_user_prompt(batch, kazanim_text)
        logger.info(
            "Batch %s-%s / %s ...",
            start, start + len(batch), len(pending),
        )
        try:
            result = _call_gemini_with_backoff(client, args.model, prompt, grade)
        except Exception as exc:
            logger.exception("Batch başarısız (%s-%s): %s", start, start + len(batch), exc)
            continue

        result_by_id = {r.chunk_id: r for r in result.results}
        for ch in batch:
            r = result_by_id.get(ch["chunk_id"])
            if r is None:
                logger.warning("LLM bu chunk'a yanıt vermedi: %s", ch["chunk_id"])
                continue
            target = by_id[ch["chunk_id"]]
            target["tagged"] = True
            target["kazanim_kod_llm"] = r.kazanim_kod
            target["confidence"] = r.confidence
            target["mapped_topic_hint"] = r.mapped_topic_hint
            target["content_quality"] = r.content_quality
        batches_done += 1
        if batches_done % save_every == 0:
            _save_tags(merged, output_path, grade)
            logger.info("  → ara kayıt yapıldı")

    _save_tags(merged, output_path, grade)
    logger.info("Tamamlandı: %s", output_path)

    # Özet
    print("\n=== ÖZET ===")
    by_kazanim: dict[str, int] = {}
    by_quality: dict[str, int] = {}
    by_confidence: dict[str, int] = {}
    unmapped_topics: dict[str, int] = {}
    for c in merged:
        if not c.get("tagged"):
            continue
        kod = c.get("kazanim_kod_llm") or "__UNMAPPED__"
        by_kazanim[kod] = by_kazanim.get(kod, 0) + 1
        if c.get("content_quality"):
            by_quality[c["content_quality"]] = by_quality.get(c["content_quality"], 0) + 1
        if c.get("confidence"):
            by_confidence[c["confidence"]] = by_confidence.get(c["confidence"], 0) + 1
        if not c.get("kazanim_kod_llm") and c.get("mapped_topic_hint"):
            unmapped_topics[c["mapped_topic_hint"]] = unmapped_topics.get(c["mapped_topic_hint"], 0) + 1

    print("\nKazanım dağılımı:")
    for kod, n in sorted(by_kazanim.items()):
        print(f"  {kod}: {n}")
    print("\nİçerik kalitesi:")
    for q, n in sorted(by_quality.items()):
        print(f"  {q}: {n}")
    print("\nGüven dağılımı:")
    for c, n in sorted(by_confidence.items()):
        print(f"  {c}: {n}")
    if unmapped_topics:
        print("\nMüfredat dışı konu ipuçları (curriculum_expansion):")
        for t, n in sorted(unmapped_topics.items(), key=lambda x: -x[1]):
            print(f"  {t}: {n}")


if __name__ == "__main__":
    main()
