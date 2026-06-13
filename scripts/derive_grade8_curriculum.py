"""8. sınıf MEB kazanım listesini PDF'lerden türetir ve CURRICULUM[8] bloğu üretir.

Strateji:
  1. Kazanım kodları içeren PDF'leri (yazili*, c1_matematik_8) tara → M.8.x.x kodlarını
     ve çevrelerindeki metni (kazanım metni tahmini için) çıkar.
  2. Ders kitabı ilk 60 sayfasından ünite başlıklarını çıkar (öğrenme alanı tespiti).
  3. Tüm bağlamı Gemini'ye ver → her kazanım için {kod, metin, difficulty_hints} üret.
  4. Sonucu difficulty_hints'li Python dict olarak yazar → curriculum.py'ye elle yapıştırılır.

Kullanım:
    python scripts/derive_grade8_curriculum.py
    python scripts/derive_grade8_curriculum.py --output knowledge_base/processed/grade8_curriculum_draft.json

Çıktı:
  - knowledge_base/processed/grade8_curriculum_draft.json  (JSON — makine okunabilir)
  - knowledge_base/processed/grade8_curriculum_snippet.py  (Python kod parçası — curriculum.py'ye yapıştır)
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

import pymupdf
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import settings  # noqa: E402

PROCESSED_DIR = ROOT / "knowledge_base" / "processed"
GRADE8_DIR = ROOT / "knowledge_base" / "8.Sınıf"

# Kaynak PDF'ler — kazanım kodu içerenler (analiz ile doğrulandı)
KAZANIM_SOURCE_FILES = [
    "yazili1.pdf",
    "yazili2.pdf",
    "yazili3.pdf",
    "yazili4.pdf",
    "c1_matematik_8.pdf",
]
TEXTBOOK_FILE = "8 - Matematik Ders Kitabı - MEB.pdf"

KAZ_RE = re.compile(r"M\.8\.(\d+)\.(\d+)")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("derive_g8")


# --- Pydantic şemaları ---

class KazanimDraft(BaseModel):
    kod: str = Field(description="MEB kazanım kodu, örn 'M.8.1.1'")
    metin: str = Field(description="Kazanımın tam metni (MEB 2024 dili)")
    alan_no: int = Field(description="Öğrenme alanı numarası (1-7)")
    alan_adi: str = Field(description="Öğrenme alanı adı, örn 'Çarpanlar ve Katlar'")
    difficulty_kolay: str = Field(description="Kolay soru için kısa talimat (1 cümle)")
    difficulty_orta: str = Field(description="Orta soru için kısa talimat (1 cümle)")
    difficulty_zor: str = Field(description="Zor soru için kısa talimat (1 cümle)")


class CurriculumDraft(BaseModel):
    kazanimlar: list[KazanimDraft]


def _extract_context_from_pdf(pdf_path: Path, max_chars: int = 8000) -> str:
    """PDF'den maksimum metin çıkar (kazanım kodu ve bağlamı için)."""
    if not pdf_path.exists():
        return ""
    doc = pymupdf.open(str(pdf_path))
    pages_text = []
    total = 0
    for i in range(len(doc)):
        t = doc[i].get_text().strip()
        if t:
            pages_text.append(f"[Sayfa {i+1}]\n{t}")
            total += len(t)
        if total > max_chars:
            break
    doc.close()
    return "\n\n".join(pages_text)[:max_chars]


def _extract_textbook_structure(max_pages: int = 60) -> str:
    """Ders kitabı ilk sayfalarından ünite/öğrenme alanı başlıklarını çıkar."""
    p = GRADE8_DIR / TEXTBOOK_FILE
    if not p.exists():
        return ""
    doc = pymupdf.open(str(p))
    pages_text = []
    for i in range(min(max_pages, len(doc))):
        t = doc[i].get_text().strip()
        if t:
            pages_text.append(t)
    doc.close()
    return "\n\n".join(pages_text)[:10000]


def _collect_known_codes(context_texts: list[str]) -> set[str]:
    """Tüm bağlamlardaki M.8.x.y kodlarını topla."""
    codes: set[str] = set()
    for text in context_texts:
        for m in KAZ_RE.finditer(text):
            codes.add(m.group(0))
    return codes


SYSTEM_PROMPT = """Sen MEB 2024 matematik müfredatı uzmanısın. 8. sınıf öğrenme alanları:
1. Sayılar ve İşlemler (Çarpanlar ve Katlar, Üslü İfadeler, Kareköklü İfadeler)
2. Cebir (Cebirsel İfadeler, Özdeşlikler)
3. Doğrusal Denklemler ve Eşitsizlikler
4. Geometri ve Ölçme (Üçgenler, Dönüşüm Geometrisi, Geometrik Cisimler)
5. Veri İşleme ve İstatistik
6. Olasılık

Kazanım kodu formatı: M.8.{alan_no}.{kazanim_no}
Difficulty hints — her biri KISA (maksimum 15 kelime), somut, tek soru tipini niteler:
  kolay: temel tanım/hesap, tek adım
  orta: iki adımlı, birleşik veya bağlamlı
  zor: muhakeme, ters işlem, LGS tarzı çok adım"""


def _call_gemini(client: genai.Client, prompt: str) -> CurriculumDraft:
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0.1,
        response_mime_type="application/json",
        response_schema=CurriculumDraft,
    )
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
        config=config,
    )
    parsed = getattr(response, "parsed", None)
    if isinstance(parsed, CurriculumDraft):
        return parsed
    return CurriculumDraft.model_validate_json(response.text)


def _build_prompt(
    known_codes: set[str],
    context_snippets: dict[str, str],
    textbook_structure: str,
) -> str:
    sorted_codes = sorted(known_codes)
    code_list = "\n".join(f"  - {c}" for c in sorted_codes)

    ctx_parts = []
    for fname, text in context_snippets.items():
        ctx_parts.append(f"=== {fname} ===\n{text[:2500]}")
    context_block = "\n\n".join(ctx_parts)

    textbook_block = textbook_structure[:3000] if textbook_structure else "(mevcut değil)"

    return f"""Aşağıdaki 8. sınıf kaynaklarından toplanan bilgilere dayanarak, tüm 8. sınıf MEB matematik kazanımlarını (M.8.x.y formatında) tam ve eksiksiz listele.

KAYNAKLARDA BULUNAN KAZANIM KODLARI:
{code_list}

DERS KİTABI ÜNİTE YAPISI (ilk 60 sayfa):
{textbook_block}

KAYNAK METİNLERİ (kazanım bağlamı):
{context_block}

GÖREV:
1. Yukarıdaki kaynaklardaki tüm kodları dahil et.
2. MEB 2024 8. sınıf müfredatına göre eksik kalan kazanımları da ekle (kaynakta görünmese bile).
3. Her kazanım için gerçek MEB metnini yaz (özet değil, tam cümle).
4. difficulty_hints: kolay/orta/zor için somut, kısa (max 15 kelime) talimat.
5. alan_no ve alan_adi'ni doğru eşleştir.
6. Tüm kazanımları döndür — eksik bırakma."""


def _to_python_snippet(kazanimlar: list[KazanimDraft]) -> str:
    """CURRICULUM[8] için Python kod parçası üretir."""
    from app.models.enums import TopicId

    ALAN_TO_TOPIC: dict[int, str] = {
        1: TopicId.DOGAL_SAYILAR.value,
        2: TopicId.CEBIR.value,
        3: TopicId.CEBIR.value,
        4: TopicId.GEOMETRI.value,
        5: TopicId.VERI_ISLEME.value,
        6: TopicId.OLASILIK.value,
    }

    # Öğrenme alanı → kazanım listesi
    by_alan: dict[tuple[int, str], list[KazanimDraft]] = {}
    for k in kazanimlar:
        key = (k.alan_no, k.alan_adi)
        by_alan.setdefault(key, []).append(k)

    lines = ["    8: {"]
    for (alan_no, alan_adi), kzs in sorted(by_alan.items()):
        topic_id = ALAN_TO_TOPIC.get(alan_no, TopicId.DOGAL_SAYILAR.value)
        kzs_sorted = sorted(kzs, key=lambda x: x.kod)
        kaz_lines = []
        for k in kzs_sorted:
            kaz_lines.append(
                f"                {{\n"
                f'                    "kod": "{k.kod}",\n'
                f'                    "metin": "{k.metin}",\n'
                f"                    \"difficulty_hints\": _hints(\n"
                f'                        "{k.difficulty_kolay}",\n'
                f'                        "{k.difficulty_orta}",\n'
                f'                        "{k.difficulty_zor}",\n'
                f"                    ),\n"
                f"                }},"
            )
        kaz_block = "\n".join(kaz_lines)
        lines.append(
            f'        TopicId.{_topic_const(topic_id)}.value: {{\n'
            f'            "topic_id": TopicId.{_topic_const(topic_id)}.value,\n'
            f'            "name": "{alan_adi}",\n'
            f'            "description": "{alan_adi} — 8. sınıf",\n'
            f'            "kazanimlar": [\n'
            f"{kaz_block}\n"
            f"            ],\n"
            f"        }},"
        )
    lines.append("    },")
    return "\n".join(lines)


def _topic_const(value: str) -> str:
    from app.models.enums import TopicId
    for member in TopicId:
        if member.value == value:
            return member.name
    return "DOGAL_SAYILAR"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=str,
        default=str(PROCESSED_DIR / "grade8_curriculum_draft.json"),
    )
    args = parser.parse_args()

    if not settings.gemini_api_key:
        raise SystemExit("GEMINI_API_KEY .env'de yok.")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Kaynak PDF'lerden bağlam çıkar
    logger.info("Kaynak PDF'ler okunuyor...")
    context_snippets: dict[str, str] = {}
    context_texts: list[str] = []
    for fname in KAZANIM_SOURCE_FILES:
        p = GRADE8_DIR / fname
        text = _extract_context_from_pdf(p, max_chars=6000)
        if text:
            context_snippets[fname] = text
            context_texts.append(text)
            logger.info("  %s: %s karakter", fname, len(text))

    # 2. Bilinen kazanım kodlarını topla
    known_codes = _collect_known_codes(context_texts)
    logger.info("Toplanan M.8.x.y kodları: %s → %s", len(known_codes), sorted(known_codes))

    # 3. Ders kitabı yapısını çıkar
    logger.info("Ders kitabı yapısı okunuyor...")
    textbook_structure = _extract_textbook_structure()
    logger.info("  %s karakter", len(textbook_structure))

    # 4. Gemini çağrısı
    logger.info("Gemini ile müfredat türetiliyor (%s)...", settings.gemini_model)
    client = genai.Client(api_key=settings.gemini_api_key)
    prompt = _build_prompt(known_codes, context_snippets, textbook_structure)
    result = _call_gemini(client, prompt)

    kazanimlar = result.kazanimlar
    logger.info("Türetilen kazanım sayısı: %s", len(kazanimlar))

    # 5. JSON çıktı
    out_json = Path(args.output)
    payload = {
        "grade": 8,
        "kazanim_count": len(kazanimlar),
        "source_codes_found": sorted(known_codes),
        "kazanimlar": [k.model_dump() for k in kazanimlar],
    }
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("JSON yazıldı: %s", out_json)

    # 6. Python snippet çıktı
    snippet_path = PROCESSED_DIR / "grade8_curriculum_snippet.py"
    snippet = _to_python_snippet(kazanimlar)
    snippet_path.write_text(snippet, encoding="utf-8")
    logger.info("Python snippet yazıldı: %s", snippet_path)

    # 7. Özet
    print("\n=== ÖZET ===")
    by_alan: dict[str, int] = {}
    for k in kazanimlar:
        key = f"Alan {k.alan_no}: {k.alan_adi}"
        by_alan[key] = by_alan.get(key, 0) + 1
    for alan, n in sorted(by_alan.items()):
        print(f"  {alan}: {n} kazanım")
    print(f"\nToplam: {len(kazanimlar)} kazanım")
    print(f"\nSonraki adım: {snippet_path} dosyasını gözden geçirip")
    print("app/data/curriculum.py'deki CURRICULUM sözlüğüne yapıştır.")


if __name__ == "__main__":
    main()
