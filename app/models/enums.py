from enum import Enum


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
