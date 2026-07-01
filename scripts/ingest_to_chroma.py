"""synthetic_examples.json + manuel few-shot örneklerini ChromaDB'ye yükler.

Her örnek embed edilir (gemini-embedding-001) ve metadata ile saklanır.
Mevcut koleksiyon varsa --rebuild bayrağıyla yeniden oluşturulur.

Kullanım:
    python scripts/ingest_to_chroma.py
    python scripts/ingest_to_chroma.py --rebuild
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from pathlib import Path

import chromadb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import settings  # noqa: E402
from app.data.curriculum import CURRICULUM  # noqa: E402
from app.data.few_shot import EXAMPLES_BY_GRADE  # noqa: E402
from app.services.embedder import GeminiEmbedder  # noqa: E402


SYNTH_JSON_PATH = ROOT / "knowledge_base" / "processed" / "synthetic_examples.json"
LGS_JSON_PATH = ROOT / "knowledge_base" / "processed" / "lgs_examples.json"
VISUAL_JSON_PATH = ROOT / "knowledge_base" / "processed" / "visual_examples.json"
FORMAT_JSON_PATH = ROOT / "knowledge_base" / "processed" / "format_examples.json"
GEOMETRY_SVG_JSON_PATH = ROOT / "knowledge_base" / "processed" / "geometry_svg_examples.json"
CHART_PATTERN_SVG_JSON_PATH = ROOT / "knowledge_base" / "processed" / "chart_pattern_svg_examples.json"
SALT_ISLEM_LATEX_JSON_PATH = ROOT / "knowledge_base" / "processed" / "salt_islem_latex_examples.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("ingest")


def _stable_id(payload: dict) -> str:
    """Aynı sorunun tekrar eklenmesini engelleyen deterministik id."""
    key = f"{payload['grade']}|{payload['kazanim_kod']}|{payload['question_type']}|{payload['question']}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def _load_synthetic() -> list[dict]:
    if not SYNTH_JSON_PATH.exists():
        logger.warning("Sentetik JSON yok: %s", SYNTH_JSON_PATH)
        return []
    with SYNTH_JSON_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("examples", [])
    logger.info("Sentetik örnek: %s", len(items))
    return items


def _load_visual() -> list[dict]:
    """Görsel/yapısal sentetik örnekleri yükler (generate_visual_examples.py çıktısı)."""
    if not VISUAL_JSON_PATH.exists():
        logger.info("Görsel sentetik JSON yok (atlanıyor): %s", VISUAL_JSON_PATH)
        return []
    with VISUAL_JSON_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("examples", [])
    logger.info("Görsel sentetik örnek: %s", len(items))
    return items


def _load_format() -> list[dict]:
    """Sprint 12-A format tipleri (çoktan seçmeli, boşluk doldurma, doğru/yanlış,
    eşleştirme, sıralama) sentetik örnekleri."""
    if not FORMAT_JSON_PATH.exists():
        logger.info("Format sentetik JSON yok (atlanıyor): %s", FORMAT_JSON_PATH)
        return []
    with FORMAT_JSON_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("examples", [])
    logger.info("Format sentetik örnek: %s", len(items))
    return items


def _load_geometry_svg() -> list[dict]:
    """Sprint 12-B Phase A — SVG'li gorsel_geometri örnekleri."""
    if not GEOMETRY_SVG_JSON_PATH.exists():
        logger.info("Geometry SVG JSON yok (atlanıyor): %s", GEOMETRY_SVG_JSON_PATH)
        return []
    with GEOMETRY_SVG_JSON_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("examples", [])
    logger.info("Geometry SVG örnek: %s", len(items))
    return items


def _load_chart_pattern_svg() -> list[dict]:
    """Sprint 12-B Phase B — SVG'li grafik_okuma + oruntu_sekil örnekleri."""
    if not CHART_PATTERN_SVG_JSON_PATH.exists():
        logger.info("Chart/Pattern SVG JSON yok (atlanıyor): %s", CHART_PATTERN_SVG_JSON_PATH)
        return []
    with CHART_PATTERN_SVG_JSON_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("examples", [])
    logger.info("Chart/Pattern SVG örnek: %s", len(items))
    return items


def _load_salt_islem_latex() -> list[dict]:
    """Sprint 12-B Phase C — LaTeX'li salt_islem örnekleri."""
    if not SALT_ISLEM_LATEX_JSON_PATH.exists():
        logger.info("salt_islem LaTeX JSON yok (atlanıyor): %s", SALT_ISLEM_LATEX_JSON_PATH)
        return []
    with SALT_ISLEM_LATEX_JSON_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("examples", [])
    logger.info("salt_islem LaTeX örnek: %s", len(items))
    return items


def _load_lgs() -> list[dict]:
    """LGS PDF'lerinden çıkarılan gerçek sınav sorularını yükler (grade=8 few-shot)."""
    if not LGS_JSON_PATH.exists():
        logger.info("LGS JSON yok (atlanıyor): %s", LGS_JSON_PATH)
        return []
    with LGS_JSON_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("examples", [])
    logger.info("LGS örnek: %s", len(items))
    return items


_QUESTIONS_GRADES = (5, 6, 7)
_QTYPE_INGEST_MAP = {"acik_uclu": "sozel_problem", "siralanan": "siralama"}


def _load_questions() -> list[dict]:
    """5/6/7. sınıf PDF'lerinden çıkarılıp DOĞRULANMIŞ gerçek soruları yükler.

    `validate_questions.py` çıktısı (questions_grade{N}_validated.json) tercih edilir;
    yoksa ham questions_grade{N}.json (doğrulama yapılmamış — uyarı loglar).
    topic_id kazanım kodundan doldurulur (retriever fallback'i için), tip eşlenir.
    content_type SET EDİLMEZ → retriever bunları few-shot Q&A olarak görür.
    """
    out: list[dict] = []
    for grade in _QUESTIONS_GRADES:
        validated = ROOT / "knowledge_base" / "processed" / f"questions_grade{grade}_validated.json"
        raw = ROOT / "knowledge_base" / "processed" / f"questions_grade{grade}.json"
        path = validated if validated.exists() else raw
        if not path.exists():
            continue
        if path is raw:
            logger.warning("Sınıf %s: DOĞRULANMAMIŞ ham dosya kullanılıyor (%s) — önce validate_questions.py önerilir.",
                           grade, raw.name)
        topics = CURRICULUM.get(grade, {})
        kod_to_topic = {k["kod"]: tid for tid, t in topics.items() for k in t["kazanimlar"]}
        items = json.loads(path.read_text(encoding="utf-8")).get("examples", [])
        for ex in items:
            kod = ex.get("kazanim_kod") or ""
            qt = ex.get("question_type", "coktan_secmeli")
            out.append({
                "grade": ex.get("grade", grade),
                "topic_id": ex.get("topic_id") or kod_to_topic.get(kod, ""),
                "kazanim_kod": kod,
                "difficulty": ex.get("difficulty", "orta"),
                "question_type": _QTYPE_INGEST_MAP.get(qt, qt),
                "question": ex["question"],
                "answer": ex["answer"],
                "solution": ex.get("solution", ""),
                "source": ex.get("source", f"questions/grade{grade}"),
            })
        logger.info("Sınıf %s soru örneği (%s): %s", grade, path.name, len(items))
    return out


def _load_manual_few_shot() -> list[dict]:
    """Mevcut elle yazılmış few-shot örneklerini topla."""
    out: list[dict] = []
    for grade, pool in EXAMPLES_BY_GRADE.items():
        topics = CURRICULUM.get(grade, {})
        kod_to_topic = {k["kod"]: tid for tid, t in topics.items() for k in t["kazanimlar"]}
        for kod, examples in pool.items():
            topic_id = kod_to_topic.get(kod, "")
            for ex in examples:
                qt = ex["type"]
                qt_value = qt.value if hasattr(qt, "value") else str(qt)
                out.append({
                    "grade": grade,
                    "topic_id": topic_id,
                    "kazanim_kod": kod,
                    "difficulty": ex.get("difficulty", "orta"),
                    "question_type": qt_value,
                    "question": ex["question"],
                    "answer": ex["answer"],
                    "solution": ex["solution"],
                    "source": "manual/few_shot",
                })
    logger.info("Manuel few-shot örnek: %s", len(out))
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild", action="store_true", help="Koleksiyonu sıfırdan oluştur")
    parser.add_argument("--batch", type=int, default=50, help="Embedding batch boyutu")
    args = parser.parse_args()

    client = chromadb.PersistentClient(path=settings.chroma_db_path)

    if args.rebuild:
        try:
            client.delete_collection(name=settings.chroma_collection)
            logger.info("Mevcut koleksiyon silindi: %s", settings.chroma_collection)
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=settings.chroma_collection,
        metadata={"hnsw:space": "cosine"},
    )
    existing_ids: set[str] = set()
    try:
        dump = collection.get(include=[], limit=None)
        existing_ids = set(dump.get("ids", []))
    except Exception:
        pass
    logger.info("Koleksiyonda mevcut: %s kayıt", len(existing_ids))

    all_items = (
        _load_synthetic()
        + _load_visual()
        + _load_format()
        + _load_geometry_svg()
        + _load_chart_pattern_svg()
        + _load_salt_islem_latex()
        + _load_lgs()
        + _load_questions()
        + _load_manual_few_shot()
    )
    logger.info("Toplam aday örnek: %s", len(all_items))

    # id belirle + zaten var olanları VE bu koşu içindeki mükerrerleri atla
    new_items: list[tuple[str, dict]] = []
    seen_ids: set[str] = set()
    dup_in_run = 0
    for item in all_items:
        item_id = _stable_id(item)
        if item_id in existing_ids or item_id in seen_ids:
            if item_id in seen_ids:
                dup_in_run += 1
            continue
        seen_ids.add(item_id)
        new_items.append((item_id, item))
    logger.info("Yeni eklenecek örnek: %s (koşu-içi mükerrer atlandı: %s)", len(new_items), dup_in_run)
    if not new_items:
        logger.info("Eklenecek yeni örnek yok.")
        return

    embedder = GeminiEmbedder()
    total = len(new_items)
    added = 0

    for start in range(0, total, args.batch):
        chunk = new_items[start : start + args.batch]
        texts_to_embed = [item["question"] for _, item in chunk]
        logger.info("Embedding batch %s-%s / %s ...", start, start + len(chunk), total)
        try:
            embeddings = embedder.embed_many(texts_to_embed)
        except Exception as exc:
            logger.error("Embedding başarısız: %s — bu batch atlandı.", exc)
            continue

        ids = [cid for cid, _ in chunk]
        documents = [item["question"] for _, item in chunk]
        metadatas = [
            {
                "grade": item["grade"],
                "topic_id": item["topic_id"],
                "kazanim_kod": item["kazanim_kod"],
                "difficulty": item["difficulty"],
                "question_type": item["question_type"],
                "answer": item["answer"],
                "solution": item["solution"],
                "source": item["source"],
            }
            for _, item in chunk
        ]
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        added += len(chunk)
        logger.info("  → eklenen kümülatif: %s / %s", added, total)

    logger.info("Tamamlandı. Koleksiyonda toplam kayıt: %s", collection.count())


if __name__ == "__main__":
    main()
