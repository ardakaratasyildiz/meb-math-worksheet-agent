"""Atıf bütünlüğü eval seti (WS-5.27) — reference_integrity_issue().

Soru "öncüller/görsel/tabloya göre" deyip o öğeyi İÇERMİYORSA cevaplanamaz →
üretimde elenmeli (FLAG). Öğe varsa ya da atıf yoksa geçmeli (KEEP). Deterministik;
pytest ile koşar. Yeni yanlış-eleme/kaçak vakası çıktıkça buraya ekle.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.structured import reference_integrity_issue  # noqa: E402

# ── FLAG: elenmeli (öğeye atıf var ama öğe yok) ──────────────────────────────
FLAG_CASES = [
    # Öncül atfı, öncül listesi yok
    "Aşağıdaki öncüllerden hangileri doğrudur? A) Yalnız I B) I ve II C) II ve III D) I, II ve III",
    "Verilen öncüllere göre aşağıdakilerden hangisi söylenebilir? A) Kar yağar B) Yağmur yağar C) Hava açık D) Rüzgâr eser",
    # Roman-set cevap kalıbı, liste yok
    "Aşağıdakilerden hangileri hücre için doğrudur? A) Yalnız II B) I ve III C) II ve III D) I, II ve III",
    # Grafik atfı, grafik yok
    "Yukarıdaki grafiğe göre en sıcak ay hangisidir? A) Ocak B) Mart C) Temmuz D) Aralık",
    # Görsel atfı, svg yok
    "Görsele göre kuvvetin yönü hangisidir? A) Sağa B) Sola C) Yukarı D) Aşağı",
    # Şema/şekil atfı (çekimli), svg yok
    "Şekildeki basit elektrik devresine göre ampul yanar mı? A) Yanar B) Yanmaz C) Kısmen D) Belirsiz",
    "Yukarıdaki şemaya göre besin zincirinde ilk halka hangisidir? A) Ot B) Tavşan C) Tilki D) Güneş",
    # Harita atfı, görsel yok
    "Haritaya göre en kalabalık bölge hangisidir? A) Marmara B) Ege C) Akdeniz D) Doğu Anadolu",
    # Tablo atfı, tablo yok
    "Yukarıdaki tabloya göre en çok satan ürün hangisidir? A) Kalem B) Silgi C) Defter D) Cetvel",
]

# ── KEEP: geçmeli (öğe var, ya da atıf yok, ya da bilinen kavram) ─────────────
KEEP_CASES = [
    # Öncüller GERÇEKTEN listelenmiş
    "Sıcaklık ölçümleri: I. Ocak 5°C II. Mart 12°C III. Temmuz 30°C\nYukarıdaki öncüllerden hangileri doğrudur? A) Yalnız I B) I ve II C) II ve III D) I, II ve III",
    "Aşağıdaki öncülleri inceleyiniz:\n1. Su 100°C'de kaynar\n2. Buz 0°C'de erir\n3. Su donunca genleşir\nHangileri doğrudur? A) 1 ve 2 B) 2 ve 3 C) 1 ve 3 D) 1, 2 ve 3",
    # Görsel GERÇEKTEN var (svg)
    'Aşağıdaki şekle göre üçgenin alanı kaçtır? <svg width="100" height="80"><polygon points="0,80 100,80 50,0"/></svg> A) 40 B) 4000 C) 400 D) 8000',
    # Chart direktifi var
    "Aşağıdaki grafiğe göre en yüksek değer hangisidir? {{chart:bar|Ocak=5|Mart=12|Temmuz=30}} A) Ocak B) Mart C) Temmuz D) Eşit",
    # Markdown tablo var
    "Yukarıdaki tabloya göre en çok satan ürün hangisidir?\n| Ürün | Adet |\n|---|---|\n| Kalem | 40 |\n| Silgi | 12 |\nA) Kalem B) Silgi C) Defter D) Cetvel",
    # Bilinen KAVRAM: periyodik tablo (render tablo değil)
    "Periyodik tabloda 1. grupta yer alan elementlerin ortak özelliği nedir? A) Soy gaz B) Alkali metal C) Ametal D) Yarı metal",
    # Bilinen KAVRAM: çarpım tablosu
    "Çarpım tablosunu kullanarak 7 × 8 işleminin sonucu kaçtır? A) 54 B) 56 C) 63 D) 48",
    # "bu şekilde / aşağıdaki şekilde" ZARFI — görsel atfı değil
    "Bir sayının 2 katının 6 fazlası 20'dir. Bu şekilde ifade edilen sayı kaçtır? A) 5 B) 7 C) 9 D) 11",
    "Aşağıdaki şekilde hesaplama yapınız: 12 + 8 × 2 işleminin sonucu kaçtır? A) 28 B) 40 C) 20 D) 32",
    # Sosyal: "I. Dünya Savaşı ve II. Meşrutiyet" — araya isim giren Roman'lar (atıf değil)
    "I. Dünya Savaşı'ndan sonra imzalanan ilk ateşkes hangisidir? A) Mondros B) Sevr C) Lozan D) Mudanya",
    # Şıklı ama hiçbir öğeye atıf yok
    "Aşağıdaki cümlelerin hangisinde yazım yanlışı vardır? A) Herşey B) Her şey olur C) Bir şey D) Hiçbir şey",
    # Matematik: "1 ve 2. dereceden" (Arabic, Roman değil) — atıf değil
    "1 ve 2. dereceden denklemler arasındaki fark nedir? A) Üs B) Katsayı C) Değişken D) Sabit",
]


def test_flag_cases() -> None:
    for q in FLAG_CASES:
        issue = reference_integrity_issue(q)
        assert issue is not None, f"FLAG bekleniyordu (elenmeli): {q[:70]!r}"


def test_keep_cases() -> None:
    for q in KEEP_CASES:
        issue = reference_integrity_issue(q)
        assert issue is None, f"KEEP bekleniyordu ama flag'lendi ({issue}): {q[:70]!r}"


if __name__ == "__main__":
    test_flag_cases()
    test_keep_cases()
    print(f"OK — {len(FLAG_CASES)} FLAG + {len(KEEP_CASES)} KEEP vakası geçti.")
