from enum import Enum


class SubjectId(str, Enum):
    """Ders (subject) ekseni. Varsayılan matematik; sistem tek-ders iken davranış
    değişmez. Fen içeriği kalite kapısını (docs/FEN_BILIMLERI_PLAN.md Faz 6) geçene
    kadar feature-flag arkasında (bkz. Settings.fen_enabled)."""

    MATEMATIK = "matematik"
    FEN = "fen"


class Difficulty(str, Enum):
    KOLAY = "kolay"
    ORTA = "orta"
    ZOR = "zor"


class QuestionType(str, Enum):
    ISLEM = "islem"
    SOZEL_PROBLEM = "sozel_problem"
    KAVRAM_SORUSU = "kavram_sorusu"
    AKIL_YURUTME = "akil_yurutme"
    MODELLEME = "modelleme"
    GUNLUK_HAYAT = "gunluk_hayat"
    # Görsel/yapısal tipler (Faz 1: Markdown/Unicode tabanlı, görsel render gerektirmez)
    SALT_ISLEM = "salt_islem"           # Sözel olmayan saf matematiksel ifade: "3/4 + 1/6 = ?"
    TABLO_SORUSU = "tablo_sorusu"       # Markdown tablodan veri okuyup soru cevaplama
    GORSEL_GEOMETRI = "gorsel_geometri" # Unicode/ASCII şekil + ölçü etiketleriyle geometri sorusu
    GRAFIK_OKUMA = "grafik_okuma"       # ASCII/Markdown sütun grafiği okuma sorusu
    ORUNTU_SEKIL = "oruntu_sekil"       # Görsel sembollü örüntü/dizi (♥ ♥ ♦ ♥ ♥ ♦ ?)
    # Faz 2: Format çeşitliliği (Sprint 12-A) — Bloom alt seviyelerine ve LGS hazırlığa hizmet eder.
    COKTAN_SECMELI = "coktan_secmeli"   # 4 şıklı (A/B/C/D), tek doğru cevap
    BOSLUK_DOLDURMA = "bosluk_doldurma" # Soru içinde "_____" ile bir/birkaç boşluk
    DOGRU_YANLIS = "dogru_yanlis"       # Tek önerme, cevap "Doğru" veya "Yanlış"
    ESLESTIRME = "eslestirme"           # Sol kolon ↔ sağ kolon, GFM tablo + cevap çiftleri
    SIRALAMA = "siralama"               # Verilen öğeleri belirli kritere göre sırala


class EducationLevel(str, Enum):
    ILKOKUL = "İlkokul"
    ORTAOKUL = "Ortaokul"


class TopicId(str, Enum):
    DOGAL_SAYILAR = "dogal_sayilar"
    KESIRLER = "kesirler"
    GEOMETRI = "geometri"
    OLCME = "olcme"
    CEBIR = "cebir"
    VERI_ISLEME = "veri_isleme"
    OLASILIK = "olasilik"
