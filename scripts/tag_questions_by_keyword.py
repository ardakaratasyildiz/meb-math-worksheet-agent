"""Kodsuz (unmapped) çıkarılmış soruları ANAHTAR-KELIME ile kazanıma etiketler.

Maliyetsiz (LLM yok). Mantık: 5-7. sınıf konuları lekzik olarak ayrışık
(kesir / geometri / sayılar / yüzde / ölçme / cebir / veri). Soru metnindeki
anahtar kelimelere göre kazanım atar. Konuyu doğru bilmek `topic_id`'yi doldurur
(retriever'ın asıl kaldıracı). Emin olunmayan → kodsuz bırakılır (yanlış etiket yok).

Kurallar ÖNCELİKLİ: spesifik kelimeler (çevre/alan/üçgen/işlem önceliği) genel
kelimelerden (kesir/sayı) ÖNCE denenir. İlk eşleşen kazanım atanır.

Kullanım:
    python scripts/tag_questions_by_keyword.py --grade 5
    python scripts/tag_questions_by_keyword.py --grade 5 --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PROCESSED_DIR = ROOT / "knowledge_base" / "processed"


def _norm(text: str) -> str:
    """Türkçe-duyarlı küçük harf + SVG/HTML çıkar."""
    t = text.split("<svg")[0]  # görsel kısmı at, sadece metin
    t = t.replace("İ", "i").replace("I", "ı").replace("Ş", "ş").replace("Ç", "ç")
    t = t.replace("Ö", "ö").replace("Ü", "ü").replace("Ğ", "ğ")
    return t.lower()


# (kazanım_kodu, [anahtar kelimeler]) — SIRA ÖNEMLİ: spesifik → genel.
# Her sınıf için ayrı liste; None döndüren = kodsuz bırak.
_RULES: dict[int, list[tuple[str, list[str]]]] = {
    5: [
        # İşlem önceliği (çok spesifik)
        ("M.5.1.4", ["işlem önceliği", "işlem sırası", "önce hangi işlem"]),
        # Yüzde (geometri/kesirden ÖNCE — 'yüzde kaçını' net sinyal)
        ("M.5.2.5", ["yüzde", "indirim", "zam", "kdv"]),
        # Geometri — spesifik
        ("M.5.3.3", ["çevre uzunluğu", "çevresi", "çevresini"]),
        ("M.5.3.4", ["alanı", "alanını", "birim kare"]),
        ("M.5.3.1", ["üçgen", "ikizkenar", "çeşitkenar"]),
        ("M.5.3.2", ["dörtgen", "yamuk", "paralelkenar", "deltoid"]),
        ("M.5.3.5", ["açı", "açının", "açıortay", "derece", "doğru parçası",
                     "kareli zemin", "karesel zemin", "dik açı", "dar açı", "geniş açı"]),
        # Kesir — spesifik
        ("M.5.2.2", ["bileşik kesir", "tam sayılı kesir", "tam sayılı"]),
        ("M.5.2.1", ["birim kesir", "kesri sırala", "sayı doğrusunda"]),
        ("M.5.2.3", ["kesir", "kesrin", "kesirler", "payda"]),
        # Cebir
        ("M.5.5.1", ["denklem", "bilinmeyen"]),
        # Ölçme
        ("M.5.4.2", ["litre", "mililitre", "sıvı"]),
        ("M.5.4.1", ["kaç metre", "kaç santimetre", "kaç kilometre",
                     "kilometre", "santimetre", "milimetre"]),
        # Veri — sadece NET sinyaller ('veri'/'tablo' tek başına değil)
        ("M.5.6.1", ["sıklık tablosu", "sütun grafiği", "grafiğe göre",
                     "anket", "veri grubu"]),
        # Sayılar — okunuş/basamak
        ("M.5.1.1", ["okunuş", "okunuşu", "yazılışı", "basamak", "bölük",
                     "çözümle", "basamak değeri", "sayı değeri"]),
        ("M.5.1.3", ["çarpma işlemi", "bölme işlemi", "çarpımı", "bölümü"]),
        ("M.5.1.2", ["toplama işlemi", "çıkarma işlemi"]),
    ],
    6: [
        ("M.6.1.7", ["bölünebilme", "bölünebilir", " ile tam bölün"]),
        ("M.6.1.6", ["obeb", "okek", "ortak bölen", "ortak kat", "ebob", "ekok"]),
        ("M.6.1.5", ["asal", "çarpan", "asal çarpan", "kat"]),
        ("M.6.3.2", ["üçgenin alan"]),
        ("M.6.3.1", ["paralelkenar", "paralelkenarın alan"]),
        ("M.6.3.3", ["yamuk"]),
        ("M.6.3.4", ["açı", "tümler", "bütünler", "komşu açı", "ters açı", "derece"]),
        ("M.6.3.5", ["çember", "daire", "yarıçap", "çap", "merkez"]),
        ("M.6.2.5", ["yüzde", "%"]),
        ("M.6.2.4", ["ondalık"]),
        ("M.6.2.2", ["kesirlerle çarpma", "kesir çarp"]),
        ("M.6.2.3", ["kesirlerle bölme", "kesir böl"]),
        ("M.6.2.1", ["kesir", "pay", "payda"]),
        ("M.6.5.3", ["denklem çöz", "denklemi çöz"]),
        ("M.6.5.2", ["denklem kur", "denklem"]),
        ("M.6.5.1", ["cebirsel ifade", "değişken", "ifadenin değeri"]),
        ("M.6.1.3", ["tam sayı", "negatif", "mutlak değer"]),
        ("M.6.6.1", ["grafik", "sütun", "çizgi grafiğ"]),
        ("M.6.6.2", ["aritmetik ortalama", "ortanca", "tepe değer", "ortalama"]),
        ("M.6.7.1", ["olası", "kesin", "imkansız", "olasılık"]),
    ],
    7: [
        ("M.7.3.4", ["dairenin alan", "daire alan"]),
        ("M.7.3.3", ["çemberin uzunluğu", "çember uzunluk", "çevre", "pi sayısı", "π"]),
        ("M.7.3.5", ["daire dilimi", "merkez açı"]),
        ("M.7.3.1", ["çember", "yarıçap", "çap", "kiriş"]),
        ("M.7.5.4", ["oran", "orantı", "doğru orantı", "ters orantı", "yüzde", "%"]),
        ("M.7.5.3", ["eşitsizlik"]),
        ("M.7.5.2", ["denklem çöz", "denklemi çöz", "denklem"]),
        ("M.7.5.1", ["eşitlik", "eşitliğin korunum"]),
        ("M.7.1.4", ["kuvvet", "üs", "üslü"]),
        ("M.7.1.1", ["tam sayılarla çarpma", "tam sayı çarp"]),
        ("M.7.1.2", ["tam sayılarla bölme", "tam sayı böl"]),
        ("M.7.1.3", ["tam sayı", "işlem önceliği"]),
        ("M.7.2.4", ["rasyonel", "rasyonel sayı çarp", "rasyonel böl"]),
        ("M.7.2.3", ["rasyonel sayı", "rasyonel"]),
        ("M.7.6.1", ["daire grafiğ", "grafik"]),
        ("M.7.6.2", ["aritmetik ortalama", "ortanca", "tepe değer"]),
        ("M.7.7.1", ["olasılık"]),
    ],
}


@lru_cache(maxsize=2048)
def _kw_pattern(kw: str) -> re.Pattern:
    # Kelime-sınırı eşleşmesi: "veri" -> "verilen" YAKALAMASIN.
    # % gibi sembolleri ve çok-kelimeli kalıpları da güvenli ele al.
    return re.compile(r"(?<!\w)" + re.escape(kw) + r"(?!\w)")


def _classify(text: str, grade: int) -> str | None:
    n = _norm(text)
    for kod, keys in _RULES.get(grade, []):
        for kw in keys:
            if _kw_pattern(kw).search(n):
                return kod
    return None


def run(grade: int, dry_run: bool = False) -> None:
    path = PROCESSED_DIR / f"questions_grade{grade}.json"
    if not path.exists():
        raise SystemExit(f"Girdi yok: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    examples = data["examples"]

    before_unmapped = sum(1 for e in examples if not e.get("kazanim_kod"))
    newly = 0
    assigned = Counter()
    for e in examples:
        if e.get("kazanim_kod"):
            continue
        kod = _classify(e["question"], grade)
        if kod:
            if not dry_run:
                e["kazanim_kod"] = kod
                e["tagged_by"] = "keyword"
            newly += 1
            assigned[kod] += 1

    after_unmapped = before_unmapped - newly
    print("\n=== ANAHTAR-KELIME ETİKETLEME ===")
    print(f"Sınıf               : {grade}")
    print(f"Toplam soru         : {len(examples)}")
    print(f"Önce kodsuz         : {before_unmapped}")
    print(f"Yeni etiketlenen    : {newly}")
    print(f"Hâlâ kodsuz         : {after_unmapped}  (müfredat-dışı/belirsiz → bırakıldı)")
    print(f"Etiketlenme oranı   : {newly/before_unmapped*100:.0f}%" if before_unmapped else "")
    print("\nAtanan kazanım dağılımı:")
    for kod, n in sorted(assigned.items(), key=lambda x: -x[1]):
        print(f"  {kod}: {n}")

    if dry_run:
        print("\n(dry-run: yazılmadı)")
        return
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGüncellendi: {path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--grade", type=int, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(grade=args.grade, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
