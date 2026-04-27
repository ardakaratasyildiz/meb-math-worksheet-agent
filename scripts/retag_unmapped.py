"""Yeni curriculum.py kazanımlarıyla mevcut unmapped chunk'ları yeniden etiketler.

Hedef: Aşama D'de eklenen yeni kazanımlara textbook chunk'larını bağla.

Akış:
    1. Her sınıf için textbook_chunks_grade{N}_tagged.json'ı yükle.
    2. kazanim_kod_llm=null + confidence in (high, medium) olan chunk'ları seç.
    3. Yeni (genişletilmiş) curriculum ile Gemini'ye yeniden sor.
    4. Sonuçları aynı JSON'a yaz: kazanim_kod_llm güncellenir, retagged=True flag eklenir.

Kullanım:
    python scripts/retag_unmapped.py --grade 5
    python scripts/retag_unmapped.py --grade 6 --batch 4

Resumable: retagged=True olanlar atlanır.
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
logger = logging.getLogger("retag")


class RetagResult(BaseModel):
    chunk_id: str
    kazanim_kod: str | None = Field(
        description="Yeni curriculum'dan eşleşen kazanım kodu. Hâlâ eşleşmiyorsa null."
    )
    confidence: str = Field(description="'high' | 'medium' | 'low'")
    notes: str | None = Field(default=None, description="LLM'in kısa açıklaması")


class RetagBatch(BaseModel):
    results: list[RetagResult]


def _kazanim_listesi_text(grade: int) -> str:
    lines = [f"MEB {grade}. SINIF KAZANIMLARI (GENİŞLETİLMİŞ):"]
    for tid, t in CURRICULUM[grade].items():
        lines.append(f"\n[{t['name']}]")
        for k in t["kazanimlar"]:
            lines.append(f"  {k['kod']}: {k['metin']}")
    return "\n".join(lines)


def _system_instruction(grade: int) -> str:
    return f"""Sen MEB matematik müfredatı uzmanısın. Görevin: {grade}. sınıf matematik ders kitabından alınmış metin parçalarını, GENİŞLETİLMİŞ kazanım listesinden uygun bir kazanıma eşlemek.

Kurallar:
1. Bu chunk'lar daha önce eski (dar) curriculum ile etiketlenmiş ve eşleşmemişti. Şimdi LISTEDE YENİ KAZANIMLAR var (Veri İşleme, Olasılık, Çarpanlar/Asal, Yüzde, Algoritma, Açılar vb).
2. Eğer chunk yeni bir kazanıma uyuyorsa kazanim_kod=M.{grade}.x.x döndür.
3. Hâlâ hiçbiri uymuyorsa kazanim_kod=null bırak (gerçekten müfredat dışı).
4. Confidence:
   - high: kazanım metniyle birebir
   - medium: konu uyuyor ama farklı alt başlık
   - low: zorlama eşleşme (kullanılmayabilir)
5. ASLA tahmin etme. Emin değilsen low + notes ile açıklama yaz."""


def _build_user_prompt(batch: list[dict], kazanim_text: str) -> str:
    lines = [
        kazanim_text,
        "",
        "=" * 60,
        "Aşağıdaki ders kitabı metin parçalarını yukarıdaki GENİŞLETİLMİŞ kazanım listesinden biriyle eşle.",
        "Her parça için chunk_id'yi koruyarak RetagResult döndür.",
        "",
    ]
    for i, ch in enumerate(batch, 1):
        header_info = f" | Başlık: {ch['header']}" if ch.get("header") else ""
        hint = ch.get("mapped_topic_hint") or ""
        lines.append(
            f"--- CHUNK {i} | id={ch['chunk_id']} | tip={ch['content_type']}"
            f" | sayfa {ch['page_start']}{header_info} | önceki konu ipucu: {hint} ---"
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
) -> RetagBatch:
    config = types.GenerateContentConfig(
        system_instruction=_system_instruction(grade),
        temperature=0.0,
        response_mime_type="application/json",
        response_schema=RetagBatch,
    )
    last_exc: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = client.models.generate_content(
                model=model, contents=prompt, config=config,
            )
            parsed = getattr(response, "parsed", None)
            if isinstance(parsed, RetagBatch):
                return parsed
            text = getattr(response, "text", None) or ""
            return RetagBatch.model_validate_json(text)
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
    parser.add_argument("--grade", type=int, required=True)
    parser.add_argument("--batch", type=int, default=4)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--model", type=str, default=settings.gemini_model)
    args = parser.parse_args()

    if not settings.gemini_api_key:
        raise SystemExit("GEMINI_API_KEY .env'de yok.")

    grade = args.grade
    path = PROCESSED_DIR / f"textbook_chunks_grade{grade}_tagged.json"
    if not path.exists():
        raise SystemExit(f"Tagged dosya yok: {path}")

    data = json.load(path.open(encoding="utf-8"))
    all_chunks = data["chunks"]

    # Re-tag adayları: previously unmapped + high/medium confidence + retagged değil
    candidates = [
        c for c in all_chunks
        if c.get("tagged")
        and not c.get("kazanim_kod_llm")
        and c.get("confidence") in ("high", "medium")
        and not c.get("retagged")
    ]
    logger.info(
        "Toplam: %s | retag adayı (unmapped + h/m confidence): %s",
        len(all_chunks), len(candidates),
    )

    if args.limit:
        candidates = candidates[: args.limit]

    if not candidates:
        logger.info("Retag edilecek chunk yok.")
        return

    client = genai.Client(api_key=settings.gemini_api_key)
    kazanim_text = _kazanim_listesi_text(grade)
    by_id = {c["chunk_id"]: c for c in all_chunks}

    save_every = max(1, 10 // args.batch)
    batches_done = 0
    newly_mapped = 0

    for start in range(0, len(candidates), args.batch):
        batch = candidates[start : start + args.batch]
        prompt = _build_user_prompt(batch, kazanim_text)
        logger.info("Batch %s-%s / %s ...", start, start + len(batch), len(candidates))
        try:
            result = _call_gemini_with_backoff(client, args.model, prompt, grade)
        except Exception as exc:
            logger.exception("Batch başarısız: %s", exc)
            continue

        result_by_id = {r.chunk_id: r for r in result.results}
        for ch in batch:
            r = result_by_id.get(ch["chunk_id"])
            if r is None:
                logger.warning("LLM yanıt vermedi: %s", ch["chunk_id"])
                continue
            target = by_id[ch["chunk_id"]]
            target["retagged"] = True
            target["retag_kazanim_kod"] = r.kazanim_kod
            target["retag_confidence"] = r.confidence
            target["retag_notes"] = r.notes
            # Eğer eşleşme bulunduysa orijinal alanı da güncelle ki ingest doğru çalışsın
            if r.kazanim_kod:
                target["kazanim_kod_llm"] = r.kazanim_kod
                target["confidence"] = r.confidence
                newly_mapped += 1

        batches_done += 1
        if batches_done % save_every == 0:
            with path.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("  → ara kayıt yapıldı")

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("Tamamlandı. Yeni eşleşen chunk: %s / %s", newly_mapped, len(candidates))

    # Özet
    print("\n=== RETAG ÖZETİ ===")
    by_kazanim: dict[str, int] = {}
    for c in all_chunks:
        if c.get("retagged"):
            kod = c.get("retag_kazanim_kod") or "__STILL_UNMAPPED__"
            by_kazanim[kod] = by_kazanim.get(kod, 0) + 1
    for kod, n in sorted(by_kazanim.items()):
        print(f"  {kod}: {n}")


if __name__ == "__main__":
    main()
