"""MEB TYMM (Türkiye Yüzyılı Maarif Modeli) matematik müfredatını ünite (TEMA)
yapısına dönüştürür + eski konulara (topic_id) köprüler.

Girdi:  tymm.meb.gov.tr'den kazınan ham JSON (bkz. scripts/scrape agent çıktısı)
          {"grades": {"1": [{"unite_id", "tema_adi", "kazanimlar":[{"kod","metin"}]}]}}
Çıktı:  app/data/units.json      → backend UNITS kaynağı (units.py yükler)
        frontend/lib/units.json  → frontend snapshot (form dropdown + kazanım indeksi)

Köprü (crosswalk): her kazanım bir eski topic_id'ye eşlenir → ChromaDB + few-shot
havuzu YENİDEN ETİKETLENMEDEN çalışır (RAG grade + topic_id ile filtreler, semantik
sorgu ince ayarı yapar). Eşleme kazanım METNİNE göre kelime-bazlı; bulunamazsa tema
adından türetilen varsayılan konu kullanılır.

Kullanım:
  PYTHONIOENCODING=utf-8 python scripts/build_units.py [--src <json>]

LLM/ağ gerektirmez; deterministik; idempotent.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DEFAULT_SRC = Path(
    r"C:\Users\ARDA~1.KAR\AppData\Local\Temp\claude"
    r"\C--Users-arda-karatas-Desktop-Projects-Claude-GenAgent"
    r"\61e6761b-3473-491a-a805-9d36162d7c5f\scratchpad\meb_tymm_math_curriculum.json"
)
APP_OUT = ROOT / "app" / "data" / "units.json"
FRONTEND_OUT = ROOT / "frontend" / "lib" / "units.json"

# ── Legacy topic_id köprüsü ────────────────────────────────────────────────
# Eski TopicId enum değerleri (app/models/enums.py):
#   dogal_sayilar, kesirler, geometri, olcme, cebir, veri_isleme, olasilik
#
# Strateji: köprü TEMA ADINA göre kurulur (temiz, birebir). Kazanım metnine göre
# kelime-substring eşleşmesi Türkçe'de güvenilmez (ör. "açı" → "açıklar", "eş" →
# "eşit/eşleştirme") — yalnız "SAYILAR VE NİCELİKLER" temasını doğal-sayı vs kesir
# olarak ayırmak için sınırlı kullanılır.
# Sıra ÖNEMLİ: daha spesifik başlıklar önce (VERİDEN OLASILIĞA, İSTATİSTİK...).
TEMA_DEFAULT: list[tuple[str, str]] = [
    ("VERİDEN OLASILIĞA", "olasilik"),
    ("OLASILIĞI", "olasilik"),
    ("OLASILIK", "olasilik"),
    ("İSTATİSTİK", "veri_isleme"),
    ("VERİYE DAYALI", "veri_isleme"),
    ("VERİDEN", "veri_isleme"),
    ("DÖNÜŞÜM", "geometri"),
    ("GEOMETRİK ŞEKİL", "geometri"),
    ("NESNELERİN GEOMETRİSİ", "geometri"),
    ("GEOMETRİK NİCELİK", "olcme"),
    ("CEBİRSEL", "cebir"),
    ("SAYILAR VE NİCELİKLER", "dogal_sayilar"),
]

# "SAYILAR VE NİCELİKLER" teması altında kesir/rasyonel/ondalık geçen kazanımlar
# kesirler konusuna ayrılır (legacy'de o sınıfta kesirler varsa).
_KESIR_KWS = ["kesir", "rasyonel", "ondalık", "ondalik", "payda"]


def _norm(s: str) -> str:
    return s.strip().lower()


def _tema_default_topic(tema_adi: str) -> str:
    up = tema_adi.upper()
    for needle, topic in TEMA_DEFAULT:
        if needle in up:
            return topic
    return "dogal_sayilar"


def _topic_for_kazanim(metin: str, tema_adi: str, grade: int) -> str:
    """Köprü: TEMA adı birincil; SAYILAR teması için metne göre doğal/kesir ayrımı.

    Sonuç legacy CURRICULUM[grade]'de yoksa (ör. grade 4'te veri/olasılık konusu yok)
    o sınıfta mevcut bir konuya düşülür → RAG boş topic'e filtrelemez.
    """
    base = _tema_default_topic(tema_adi)
    if "SAYILAR VE NİCELİKLER" in tema_adi.upper():
        low = _norm(metin)
        if any(kw in low for kw in _KESIR_KWS):
            base = "kesirler"
        else:
            base = "dogal_sayilar"
    return _guard_legacy(base, grade)


# Konu ailesi fallback zincirleri — hedef konu o sınıfta yoksa en yakın komşuya düş.
_FALLBACK_CHAINS: dict[str, list[str]] = {
    "olasilik": ["olasilik", "veri_isleme", "dogal_sayilar"],
    "veri_isleme": ["veri_isleme", "olasilik", "dogal_sayilar"],
    "kesirler": ["kesirler", "dogal_sayilar"],
    "olcme": ["olcme", "geometri", "dogal_sayilar"],
    "geometri": ["geometri", "olcme", "dogal_sayilar"],
    "cebir": ["cebir", "dogal_sayilar"],
    "dogal_sayilar": ["dogal_sayilar", "kesirler"],
}


def _guard_legacy(topic: str, grade: int) -> str:
    """topic legacy'de o sınıfta yoksa aile-duyarlı en yakın konuya düş."""
    from app.data.curriculum import CURRICULUM  # script; ağır değil
    available = set(CURRICULUM.get(grade, {}).keys())
    chain = _FALLBACK_CHAINS.get(topic, [topic])
    for cand in chain:
        if cand in available:
            return cand
    # Son çare: sınıfta mevcut herhangi bir konu.
    for cand in ("dogal_sayilar", "kesirler", "geometri", "olcme", "cebir",
                 "veri_isleme", "olasilik"):
        if cand in available:
            return cand
    return topic


_TR_SMALL_WORDS = {"ve", "ile", "de", "da", "ya", "veya"}


def _tr_lower(s: str) -> str:
    return s.replace("İ", "i").replace("I", "ı").lower()


def _tr_cap_first(w: str) -> str:
    if not w:
        return w
    first = {"i": "İ", "ı": "I"}.get(w[0], w[0].upper())
    return first + w[1:]


def _tr_title(s: str) -> str:
    """Türkçe-duyarlı başlık-case: 'SAYILAR VE NİCELİKLER (1)' → 'Sayılar ve Nicelikler (1)'.

    (str.title/.lower İ/ı'yı bozar — İ→i̇ combining dot, I→i ile ı kaybı.)
    """
    words = _tr_lower(s).split(" ")
    out = [w if w in _TR_SMALL_WORDS else _tr_cap_first(w) for w in words]
    return " ".join(out)


def _clean_name(tema_adi: str) -> tuple[int | None, str]:
    """"1.TEMA: SAYILAR VE NİCELİKLER (1)" → (1, "Sayılar ve Nicelikler (1)")."""
    s = tema_adi.strip()
    no: int | None = None
    m = re.match(r"^\s*(\d+)\s*[.\-]?\s*TEMA\s*[:\-]?\s*(.*)$", s, re.IGNORECASE)
    if m:
        no = int(m.group(1))
        s = m.group(2).strip()
    else:
        m2 = re.match(r"^\s*(\d+)\s*[.\-]\s*(.*)$", s)
        if m2:
            no = int(m2.group(1))
            s = m2.group(2).strip()
    if s.isupper():
        s = _tr_title(s)
    return no, s


def _slugify(s: str) -> str:
    # Türkçe karakterleri sadeleştir
    tr = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    s = s.translate(tr)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s


def build() -> tuple[list[dict], dict]:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(DEFAULT_SRC))
    args = ap.parse_args()

    src = Path(args.src)
    raw = json.loads(src.read_text(encoding="utf-8"))
    grades_raw = raw["grades"]

    units: list[dict] = []
    stats: dict = {"per_grade": {}, "topic_counts": {}, "total_kazanim": 0}

    for grade_str in sorted(grades_raw, key=lambda g: int(g)):
        grade = int(grade_str)
        temalar = grades_raw[grade_str]
        stats["per_grade"][grade] = {"units": len(temalar), "kazanim": 0}
        for idx, tema in enumerate(temalar):
            # _clean_name yalnız adı temizlemek için; `no` = MEB liste sırası (idx+1).
            # (Kaynakta bölünmüş üniteler aynı tema no'sunu tekrar edebiliyor — ör. 5/6.
            # sınıfta "(2)" hâlâ "1.TEMA" etiketli; sıra-bazlı no benzersiz + tutarlı.)
            tema_adi = tema.get("tema_adi", "")
            _, name = _clean_name(tema_adi)
            no = idx + 1
            unit_id = f"mat-{grade}-tema-{no}-{_slugify(name)}"
            kazanimlar = []
            for k in tema.get("kazanimlar", []):
                topic = _topic_for_kazanim(k.get("metin", ""), tema_adi, grade)
                kazanimlar.append({
                    "kod": k["kod"].strip(),
                    "metin": k["metin"].strip(),
                    "legacy_topic_id": topic,
                })
                stats["topic_counts"][topic] = stats["topic_counts"].get(topic, 0) + 1
                stats["total_kazanim"] += 1
                stats["per_grade"][grade]["kazanim"] += 1
            # Ünite düzeyi legacy_topic_id = kazanımlarının en sık konusu
            if kazanimlar:
                freq: dict[str, int] = {}
                for kk in kazanimlar:
                    freq[kk["legacy_topic_id"]] = freq.get(kk["legacy_topic_id"], 0) + 1
                unit_topic = max(freq, key=freq.get)
            else:
                unit_topic = _guard_legacy(_tema_default_topic(tema_adi), grade)
            units.append({
                "unit_id": unit_id,
                "unite_id": tema.get("unite_id"),
                "grade": grade,
                "no": no,
                "name": name,
                "legacy_topic_id": unit_topic,
                "kazanimlar": kazanimlar,
            })
    return units, stats


def main() -> None:
    units, stats = build()

    # Backend kaynağı: grade → [unit]
    app_data: dict[str, list[dict]] = {}
    for u in units:
        app_data.setdefault(str(u["grade"]), []).append(u)

    APP_OUT.write_text(
        json.dumps(app_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    # Frontend snapshot: düz ünite listesi (form dropdown filtreler)
    FRONTEND_OUT.write_text(
        json.dumps(units, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"OK: {len(units)} unite -> {APP_OUT.relative_to(ROOT)}")
    print(f"OK: {len(units)} unite -> {FRONTEND_OUT.relative_to(ROOT)}")
    print(f"Toplam kazanim: {stats['total_kazanim']}")
    print(f"Sinif basi: {stats['per_grade']}")
    print(f"Topic kopru dagilimi: {stats['topic_counts']}")


if __name__ == "__main__":
    main()
