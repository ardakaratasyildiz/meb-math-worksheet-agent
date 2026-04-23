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


class EducationLevel(str, Enum):
    ILKOKUL = "İlkokul"
    ORTAOKUL = "Ortaokul"


class TopicId(str, Enum):
    DOGAL_SAYILAR = "dogal_sayilar"
    KESIRLER = "kesirler"
    GEOMETRI = "geometri"
    OLCME = "olcme"
    CEBIR = "cebir"
