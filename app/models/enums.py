from enum import Enum


class SubjectId(str, Enum):
    """Ders (subject) ekseni. Varsayılan matematik; sistem tek-ders iken davranış
    değişmez. Fen içeriği kalite kapısını (docs/FEN_BILIMLERI_PLAN.md Faz 6) geçene
    kadar feature-flag arkasında (bkz. Settings.fen_enabled)."""

    MATEMATIK = "matematik"
    FEN = "fen"
    TURKCE = "turkce"
    SOSYAL = "sosyal"
    INGILIZCE = "ingilizce"


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
    SIRALAMA = "siralama"               # Verilen öğeleri belirli kritere göre sırala (kronoloji dahil)
    # Sözel dersler (Türkçe / Sosyal / İngilizce) — ders-nötr adlandırıldı, paylaşılır.
    OKUMA_PASAJI = "okuma_pasaji"       # Özgün pasaj/metin + pasaja dayalı soru (LGS paragraf)
    DIYALOG_TAMAMLAMA = "diyalog_tamamlama"  # Konuşma balonları/diyalogda eksik repliği tamamlama
    KELIME_BILGISI = "kelime_bilgisi"   # Sözcük/kelime anlamı, eş/zıt anlam (vocab)
    HARITA_YORUMLAMA = "harita_yorumlama"    # Harita/kroki/zaman şeridi üzerinden yorum (Sosyal)
    KAYNAK_METIN = "kaynak_metin"       # Tarihî belge/metin/alıntı + yorum (Sosyal/İnkılap)
    DIL_BILGISI = "dil_bilgisi"         # Dil bilgisi kuralı (Türkçe: sözcük türü, ek vb.)
    YAZIM_NOKTALAMA = "yazim_noktalama" # Yazım kuralı / noktalama işareti (Türkçe)
    GORSEL_YORUMLAMA = "gorsel_yorumlama"    # Görsel/afiş/realia yorumlama (İngilizce/Sosyal)


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
