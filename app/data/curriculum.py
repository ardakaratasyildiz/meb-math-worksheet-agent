"""MEB matematik müfredatı: 1-7. sınıf, 5 öğrenme alanı, kazanım kodları + zorluk kalibrasyonu.

Kazanım kod formatı: M.{sınıf}.{öğrenme_alanı}.{kazanım_no}
Öğrenme alanı numaralandırması:
    1 = Doğal Sayılar / Tam Sayılar (Sayılar ve İşlemler)
    2 = Kesirler / Rasyonel Sayılar
    3 = Geometri
    4 = Ölçme
    5 = Cebir / Örüntüler

Her kazanıma `difficulty_hints` eklenir: "kolay"/"orta"/"zor" için
Gemini'ye somut sınırlar çizen kısa talimatlar.
"""
from typing import TypedDict

from app.models.enums import EducationLevel, TopicId


class Kazanim(TypedDict):
    kod: str
    metin: str
    difficulty_hints: dict[str, str]


class Topic(TypedDict):
    topic_id: str
    name: str
    description: str
    kazanimlar: list[Kazanim]


def _hints(kolay: str, orta: str, zor: str) -> dict[str, str]:
    return {"kolay": kolay, "orta": orta, "zor": zor}


GRADE_LEVELS: dict[int, EducationLevel] = {
    1: EducationLevel.ILKOKUL,
    2: EducationLevel.ILKOKUL,
    3: EducationLevel.ILKOKUL,
    4: EducationLevel.ILKOKUL,
    5: EducationLevel.ORTAOKUL,
    6: EducationLevel.ORTAOKUL,
    7: EducationLevel.ORTAOKUL,
}

TOPIC_NAMES: dict[str, str] = {
    TopicId.DOGAL_SAYILAR.value: "Doğal Sayılar ve İşlemler",
    TopicId.KESIRLER.value: "Kesirler ve Ondalık Sayılar",
    TopicId.GEOMETRI.value: "Geometri",
    TopicId.OLCME.value: "Ölçme",
    TopicId.CEBIR.value: "Cebir ve Denklemler",
}


CURRICULUM: dict[int, dict[str, Topic]] = {
    1: {
        TopicId.DOGAL_SAYILAR.value: {
            "topic_id": TopicId.DOGAL_SAYILAR.value,
            "name": TOPIC_NAMES[TopicId.DOGAL_SAYILAR.value],
            "description": "100'e kadar sayılar, toplama-çıkarma",
            "kazanimlar": [
                {
                    "kod": "M.1.1.1",
                    "metin": "100'e kadar olan nesneleri birer, ikişer, beşer ve onar gruplayarak sayar.",
                    "difficulty_hints": _hints(
                        "20'ye kadar birer birer sayma; tek adım.",
                        "50'ye kadar ikişer veya beşer ritmik sayma; verilen sayıdan başlayıp devam.",
                        "100'e kadar onar sayma veya iki farklı ritmi karşılaştırma; muhakeme gerekir.",
                    ),
                },
                {
                    "kod": "M.1.1.2",
                    "metin": "100'e kadar olan doğal sayıları okur ve yazar.",
                    "difficulty_hints": _hints(
                        "20'ye kadar sayıların okunuşu veya yazılışı; tek adım.",
                        "50'ye kadar sayıların yazılışı; okunuştan rakama geçiş.",
                        "100'e kadar sayılarda basamak bilgisiyle yazma.",
                    ),
                },
                {
                    "kod": "M.1.1.3",
                    "metin": "Onluk ve birlik kavramlarını kullanarak iki basamaklı sayıları çözümler.",
                    "difficulty_hints": _hints(
                        "Verilen sayıyı onluk ve birliklerine ayırma (örn. 47 = 4 onluk 7 birlik).",
                        "Onluk-birlik verilip sayıyı bulma; küçük toplama ile birleşik.",
                        "Onluk/birlik sayılarının karşılaştırılması veya eksik bilgi içeren ayrıştırma.",
                    ),
                },
                {
                    "kod": "M.1.1.4",
                    "metin": "Toplamları en çok 20 olan iki doğal sayıyı zihinden veya yazılı olarak toplar.",
                    "difficulty_hints": _hints(
                        "Tek basamaklı + tek basamaklı, sonuç 10'u geçmez.",
                        "Sonuç 10-15 arası; kısa bir günlük hayat bağlamı olabilir.",
                        "Sonuç 15-20 arası; sözel problem, muhtemelen iki adımlı çıkarım.",
                    ),
                },
                {
                    "kod": "M.1.1.5",
                    "metin": "10'dan küçük doğal sayılarla çıkarma işlemi yapar.",
                    "difficulty_hints": _hints(
                        "Tek basamaklı doğrudan çıkarma, sonuç 3+.",
                        "Sözel problem, tek adımlı çıkarma.",
                        "Verilenden hareketle hangi sayının çıkarıldığını bulma.",
                    ),
                },
            ],
        },
        TopicId.GEOMETRI.value: {
            "topic_id": TopicId.GEOMETRI.value,
            "name": TOPIC_NAMES[TopicId.GEOMETRI.value],
            "description": "Temel geometrik şekilleri tanıma (kare, üçgen, daire)",
            "kazanimlar": [
                {
                    "kod": "M.1.3.1",
                    "metin": "Kare, üçgen, daire ve dikdörtgen şekillerini tanır ve adlandırır.",
                    "difficulty_hints": _hints(
                        "Şekil verilince adını söyleme.",
                        "Kenar-köşe özelliği verilip şekli belirleme.",
                        "Birden fazla özelliği birleştirerek hangi şekil olduğunu bulma.",
                    ),
                },
                {
                    "kod": "M.1.3.2",
                    "metin": "Çevresindeki nesneleri geometrik şekillerle eşleştirir.",
                    "difficulty_hints": _hints(
                        "Tek nesneyi tek şekle eşleme (tekerlek → daire).",
                        "Nesnenin ana yüzeyinin hangi şekle benzediği.",
                        "Birden fazla şekil içeren nesnelerin baskın şeklini tespit.",
                    ),
                },
            ],
        },
        TopicId.OLCME.value: {
            "topic_id": TopicId.OLCME.value,
            "name": TOPIC_NAMES[TopicId.OLCME.value],
            "description": "Uzunluk karşılaştırma, standart olmayan birimler",
            "kazanimlar": [
                {
                    "kod": "M.1.4.1",
                    "metin": "İki nesnenin uzunluklarını kısa-uzun, ince-kalın olarak karşılaştırır.",
                    "difficulty_hints": _hints(
                        "İki nesnenin basit karşılaştırması.",
                        "Üç nesne arasında sıralama.",
                        "Dolaylı karşılaştırma (A>B, B>C → A, B, C sıralaması).",
                    ),
                },
                {
                    "kod": "M.1.4.2",
                    "metin": "Standart olmayan uzunluk birimleri (karış, adım) ile ölçme yapar.",
                    "difficulty_hints": _hints(
                        "Tek birimle tek nesnenin ölçümü.",
                        "Aynı nesne için iki farklı birim arasındaki fark.",
                        "Birim sayılarıyla dolaylı nesne karşılaştırması.",
                    ),
                },
                {
                    "kod": "M.1.4.3",
                    "metin": "Saatleri tam olarak okur.",
                    "difficulty_hints": _hints(
                        "Verilen akrep-yelkovan konumunda tam saati okuma.",
                        "İki tam saat arasındaki fark.",
                        "Verilen tam saatin akrep-yelkovan konumunu tanımlama.",
                    ),
                },
            ],
        },
        TopicId.CEBIR.value: {
            "topic_id": TopicId.CEBIR.value,
            "name": TOPIC_NAMES[TopicId.CEBIR.value],
            "description": "Basit sayı örüntüleri",
            "kazanimlar": [
                {
                    "kod": "M.1.5.1",
                    "metin": "Birer ve ikişer ritmik sayarak basit sayı örüntülerini tanır.",
                    "difficulty_hints": _hints(
                        "Birer artan örüntünün bir sonraki terimi.",
                        "İkişer veya beşer artan örüntüde sıradaki terim.",
                        "Onar örüntü veya farklı adımla başlayan ritmik sayma.",
                    ),
                },
                {
                    "kod": "M.1.5.2",
                    "metin": "Basit bir örüntüde eksik bırakılan sayıyı veya şekli belirler.",
                    "difficulty_hints": _hints(
                        "Sonda tek eksik terim.",
                        "Ortada tek eksik terim.",
                        "İki eksik terim veya örüntü kuralının tersten uygulanması.",
                    ),
                },
            ],
        },
    },
    2: {
        TopicId.DOGAL_SAYILAR.value: {
            "topic_id": TopicId.DOGAL_SAYILAR.value,
            "name": TOPIC_NAMES[TopicId.DOGAL_SAYILAR.value],
            "description": "1000'e kadar sayılar, toplama-çıkarma, çarpmaya giriş",
            "kazanimlar": [
                {
                    "kod": "M.2.1.1",
                    "metin": "1000'e kadar olan doğal sayıları okur ve yazar.",
                    "difficulty_hints": _hints(
                        "100-500 arası sayıların okunuşu/yazılışı.",
                        "500-1000 arası; rakamla/yazıyla dönüşüm.",
                        "Verilen basamak bilgisinden sayı oluşturma.",
                    ),
                },
                {
                    "kod": "M.2.1.2",
                    "metin": "Üç basamaklı doğal sayıları basamak değerlerine göre çözümler.",
                    "difficulty_hints": _hints(
                        "Verilen sayının basamak değerlerini yazma.",
                        "Basamak değeri verilip sayıyı bulma.",
                        "Sayıyı tersten oluşturma veya basamak değerlerini karşılaştırma.",
                    ),
                },
                {
                    "kod": "M.2.1.3",
                    "metin": "Toplamları en çok 100 olan iki doğal sayıyı toplar.",
                    "difficulty_hints": _hints(
                        "İki basamaklı + tek basamaklı, eldesiz.",
                        "Eldeli toplama; sonuç 50-100 arası.",
                        "İki adımlı sözel problemde toplama.",
                    ),
                },
                {
                    "kod": "M.2.1.4",
                    "metin": "İki basamaklı doğal sayılarla çıkarma işlemi yapar.",
                    "difficulty_hints": _hints(
                        "Onluk bozmadan çıkarma.",
                        "Onluk bozma gerektiren çıkarma.",
                        "Çok adımlı sözel problemde çıkarma.",
                    ),
                },
                {
                    "kod": "M.2.1.5",
                    "metin": "Çarpma işlemini tekrarlı toplama olarak açıklar ve 5'e kadar olan sayılarla çarpar.",
                    "difficulty_hints": _hints(
                        "2 veya 3 ile tek basamaklı çarpma.",
                        "4 veya 5 ile tek basamaklı çarpma; kısa bağlam.",
                        "Çarpmayı tekrarlı toplamaya çevirerek ters yönde çözme.",
                    ),
                },
            ],
        },
        TopicId.GEOMETRI.value: {
            "topic_id": TopicId.GEOMETRI.value,
            "name": TOPIC_NAMES[TopicId.GEOMETRI.value],
            "description": "Kenar ve köşe kavramı, şekil özellikleri",
            "kazanimlar": [
                {
                    "kod": "M.2.3.1",
                    "metin": "Geometrik şekillerin kenar ve köşe sayılarını belirler.",
                    "difficulty_hints": _hints(
                        "Tanınan şeklin kenar/köşe sayısı.",
                        "Verilen kenar/köşe sayısından şekli bulma.",
                        "Farklı şekilleri kenar-köşe özellikleriyle ayırt etme.",
                    ),
                },
                {
                    "kod": "M.2.3.2",
                    "metin": "Karenin tüm kenarlarının eşit, dikdörtgenin karşılıklı kenarlarının eşit olduğunu fark eder.",
                    "difficulty_hints": _hints(
                        "Kare/dikdörtgen için tek özellik ifade etme.",
                        "Bir kenar verilip diğer kenarların uzunluğunu bulma.",
                        "Kare ve dikdörtgeni kenar özelliklerine göre karşılaştırma.",
                    ),
                },
            ],
        },
        TopicId.OLCME.value: {
            "topic_id": TopicId.OLCME.value,
            "name": TOPIC_NAMES[TopicId.OLCME.value],
            "description": "cm-m, saat okuma, tartma",
            "kazanimlar": [
                {
                    "kod": "M.2.4.1",
                    "metin": "Metre ve santimetreyi tanır, uzunlukları bu birimlerle ölçer.",
                    "difficulty_hints": _hints(
                        "Metre veya santimetre ile tek adım ölçüm.",
                        "m'yi cm'ye (veya tersine) dönüştürme.",
                        "Karışık birim (2 m 30 cm) problemi.",
                    ),
                },
                {
                    "kod": "M.2.4.2",
                    "metin": "Saat ve dakika kavramlarını kullanarak yarım ve çeyrek saatleri okur.",
                    "difficulty_hints": _hints(
                        "Yarım saati okuma.",
                        "Çeyrek saatleri okuma (3'ü çeyrek geçiyor).",
                        "Verilen iki saat arasındaki fark (yarım-çeyrek dahil).",
                    ),
                },
                {
                    "kod": "M.2.4.3",
                    "metin": "Kilogram birimi ile cisimlerin kütlesini ölçer ve karşılaştırır.",
                    "difficulty_hints": _hints(
                        "İki nesnenin kg bazında toplamı.",
                        "İki nesnenin kütle farkı.",
                        "Üç veya daha fazla nesne arasında kütle karşılaştırması.",
                    ),
                },
            ],
        },
        TopicId.CEBIR.value: {
            "topic_id": TopicId.CEBIR.value,
            "name": TOPIC_NAMES[TopicId.CEBIR.value],
            "description": "Sayı ve şekil örüntüleri",
            "kazanimlar": [
                {
                    "kod": "M.2.5.1",
                    "metin": "Bir örüntüdeki ilişkiyi belirler ve örüntüyü genişletir.",
                    "difficulty_hints": _hints(
                        "Sonraki terimi tahmin etme.",
                        "Kuralı sözel ifade ederek genişletme.",
                        "Azalan veya farklı sabit artışlı örüntüyü sürdürme.",
                    ),
                },
                {
                    "kod": "M.2.5.2",
                    "metin": "Sayı ve şekil örüntülerinde kuralı belirleyip eksik öğeleri tamamlar.",
                    "difficulty_hints": _hints(
                        "Tek eksik terim.",
                        "İki eksik terim; kural sözel.",
                        "Şekilsel örüntüde kural bulma.",
                    ),
                },
            ],
        },
    },
    3: {
        TopicId.DOGAL_SAYILAR.value: {
            "topic_id": TopicId.DOGAL_SAYILAR.value,
            "name": TOPIC_NAMES[TopicId.DOGAL_SAYILAR.value],
            "description": "10.000'e kadar sayılar, dört işlem",
            "kazanimlar": [
                {
                    "kod": "M.3.1.1",
                    "metin": "10.000'e kadar olan doğal sayıları okur, yazar ve basamaklarına göre çözümler.",
                    "difficulty_hints": _hints(
                        "Dört basamaklı sayı yazma/okuma.",
                        "Basamak değerlerini bulma ya da oluşturma.",
                        "Sayıyı farklı basamak değerlerinin toplamı olarak ifade etme.",
                    ),
                },
                {
                    "kod": "M.3.1.2",
                    "metin": "En çok dört basamaklı iki doğal sayıyı toplar.",
                    "difficulty_hints": _hints(
                        "Eldesiz veya tek eldeli toplama.",
                        "İki-üç eldeli toplama; kısa problem.",
                        "Çok adımlı problem; birden fazla toplama.",
                    ),
                },
                {
                    "kod": "M.3.1.3",
                    "metin": "En çok dört basamaklı doğal sayılarla çıkarma işlemi yapar.",
                    "difficulty_hints": _hints(
                        "Onluk bozmadan üç-dört basamaklı çıkarma.",
                        "Onluk bozmalı çıkarma.",
                        "Toplama ve çıkarmayı birleştiren sözel problem.",
                    ),
                },
                {
                    "kod": "M.3.1.4",
                    "metin": "İki basamaklı doğal sayılarla çarpma işlemi yapar.",
                    "difficulty_hints": _hints(
                        "İki basamaklı × tek basamaklı, eldesiz.",
                        "İki basamaklı × iki basamaklı.",
                        "Çarpma sonucunu kullanarak karşılaştırma yapma.",
                    ),
                },
                {
                    "kod": "M.3.1.5",
                    "metin": "İki basamaklı bir doğal sayıyı bir basamaklı sayıya böler.",
                    "difficulty_hints": _hints(
                        "Kalansız tam bölme.",
                        "Kalanlı bölme; kalan tek basamaklı.",
                        "Bölme sonucunu yorumlayarak günlük hayat problemi çözme.",
                    ),
                },
            ],
        },
        TopicId.KESIRLER.value: {
            "topic_id": TopicId.KESIRLER.value,
            "name": TOPIC_NAMES[TopicId.KESIRLER.value],
            "description": "Kesirlere giriş: yarım, çeyrek, bütün-parça",
            "kazanimlar": [
                {
                    "kod": "M.3.2.1",
                    "metin": "Bütün, yarım ve çeyrek kavramlarını model üzerinde gösterir.",
                    "difficulty_hints": _hints(
                        "Yarım veya çeyreği 1/2, 1/4 olarak yazma.",
                        "Model verilip kesri belirleme.",
                        "Bir bütünün kaç çeyrekten oluştuğu ve yarım ile ilişkisi.",
                    ),
                },
                {
                    "kod": "M.3.2.2",
                    "metin": "Bir bütünü eşit parçalara ayırarak parça-bütün ilişkisini açıklar.",
                    "difficulty_hints": _hints(
                        "Eşit parçalardan birini kesir olarak yazma.",
                        "Bir kısmın toplam kesrini ifade etme.",
                        "Verilen kesre karşılık gelen parça sayısını bulma (ters yönde).",
                    ),
                },
                {
                    "kod": "M.3.2.3",
                    "metin": "Pay ve payda kavramlarını kullanarak basit kesirleri yazar.",
                    "difficulty_hints": _hints(
                        "Pay ve payda verilip kesri yazma.",
                        "Kesri okuyup pay ve paydasını ayırt etme.",
                        "Verilen ipuçlarından (taranan parça sayısı, toplam parça) kesir oluşturma.",
                    ),
                },
            ],
        },
        TopicId.GEOMETRI.value: {
            "topic_id": TopicId.GEOMETRI.value,
            "name": TOPIC_NAMES[TopicId.GEOMETRI.value],
            "description": "Çevre hesaplama, simetri",
            "kazanimlar": [
                {
                    "kod": "M.3.3.1",
                    "metin": "Düzgün çokgenlerin çevre uzunluklarını hesaplar.",
                    "difficulty_hints": _hints(
                        "Kare veya eşkenar üçgenin çevresi (tek kenar verili).",
                        "Dikdörtgenin çevresi.",
                        "Çevresi verilip bir kenar uzunluğunu bulma.",
                    ),
                },
                {
                    "kod": "M.3.3.2",
                    "metin": "Bir şeklin simetri eksenini belirler ve simetrik şekiller oluşturur.",
                    "difficulty_hints": _hints(
                        "Kare, üçgen için simetri ekseni sayısı.",
                        "Verilen şekil için simetri ekseninin konumunu belirtme.",
                        "Birden fazla simetri ekseni olan şekillerin karşılaştırılması.",
                    ),
                },
            ],
        },
        TopicId.OLCME.value: {
            "topic_id": TopicId.OLCME.value,
            "name": TOPIC_NAMES[TopicId.OLCME.value],
            "description": "Birim dönüşümleri (km-m-cm-mm), zaman",
            "kazanimlar": [
                {
                    "kod": "M.3.4.1",
                    "metin": "Kilometre, metre, santimetre ve milimetre arasındaki dönüşümleri yapar.",
                    "difficulty_hints": _hints(
                        "Tek adım birim dönüşümü (m → cm veya km → m).",
                        "Karışık birim (2 km 300 m) toplamı metreye çevirme.",
                        "İki farklı birim arasında karşılaştırma gerektiren problem.",
                    ),
                },
                {
                    "kod": "M.3.4.2",
                    "metin": "Saat, dakika ve saniye arasındaki ilişkiyi kullanarak zaman ölçme problemleri çözer.",
                    "difficulty_hints": _hints(
                        "Dakikayı saniyeye veya saatleri dakikaya çevirme.",
                        "Belirli bir süreyi saatlere ve dakikalara ayırma.",
                        "Başlangıç ve bitiş zamanından toplam süre hesaplama.",
                    ),
                },
            ],
        },
        TopicId.CEBIR.value: {
            "topic_id": TopicId.CEBIR.value,
            "name": TOPIC_NAMES[TopicId.CEBIR.value],
            "description": "Örüntülerde kural bulma",
            "kazanimlar": [
                {
                    "kod": "M.3.5.1",
                    "metin": "Sayı ve şekil örüntülerindeki kuralı belirler.",
                    "difficulty_hints": _hints(
                        "Sabit artışlı örüntünün kuralı.",
                        "Sabit azalışlı örüntü veya kural sözel ifade.",
                        "Sabit çarpanlı örüntü (2, 4, 8, 16...) kuralını bulma.",
                    ),
                },
                {
                    "kod": "M.3.5.2",
                    "metin": "Verilen kurala göre sayı ve şekil örüntüsü oluşturur.",
                    "difficulty_hints": _hints(
                        "Başlangıç ve kural verilip ilk 4 terim.",
                        "İlk ve son terim verilip aradaki terimleri bulma.",
                        "Kural karmaşık (örn. her adımda önce ekle sonra çıkar).",
                    ),
                },
            ],
        },
    },
    4: {
        TopicId.DOGAL_SAYILAR.value: {
            "topic_id": TopicId.DOGAL_SAYILAR.value,
            "name": TOPIC_NAMES[TopicId.DOGAL_SAYILAR.value],
            "description": "Büyük doğal sayılar, dört işlem, bölme",
            "kazanimlar": [
                {
                    "kod": "M.4.1.1",
                    "metin": "En çok altı basamaklı doğal sayıları okur, yazar ve basamak değerlerini belirtir.",
                    "difficulty_hints": _hints(
                        "Beş basamaklı sayıların okunuşu/yazılışı.",
                        "Altı basamaklı sayılarda basamak değeri hesaplama.",
                        "Basamak değerlerinin toplamı verilip sayıyı oluşturma.",
                    ),
                },
                {
                    "kod": "M.4.1.2",
                    "metin": "Doğal sayıları sıralar ve karşılaştırır.",
                    "difficulty_hints": _hints(
                        "İki sayıyı >, <, = ile karşılaştırma.",
                        "Üç-dört sayıyı küçükten büyüğe sıralama.",
                        "Eksik rakamlı sayılarda sıralama koşulu.",
                    ),
                },
                {
                    "kod": "M.4.1.3",
                    "metin": "En çok dört basamaklı doğal sayılarla toplama ve çıkarma işlemi yapar.",
                    "difficulty_hints": _hints(
                        "Tek eldeli toplama veya basit çıkarma.",
                        "İki-üç eldeli toplama veya onluk bozmalı çıkarma.",
                        "Çok adımlı sözel problem (toplama + çıkarma).",
                    ),
                },
                {
                    "kod": "M.4.1.4",
                    "metin": "Üç basamaklı bir doğal sayıyı iki basamaklı bir doğal sayı ile çarpar.",
                    "difficulty_hints": _hints(
                        "Üç basamaklı × tek basamaklı.",
                        "Üç basamaklı × iki basamaklı.",
                        "Çarpma sonucunu sözel problemin iki adımından birinde kullanma.",
                    ),
                },
                {
                    "kod": "M.4.1.5",
                    "metin": "Üç basamaklı bir doğal sayıyı iki basamaklı bir doğal sayıya böler.",
                    "difficulty_hints": _hints(
                        "Kalansız tam bölme.",
                        "Kalanlı bölme.",
                        "Bölme işleminin kalanını yorumlayan problem.",
                    ),
                },
            ],
        },
        TopicId.KESIRLER.value: {
            "topic_id": TopicId.KESIRLER.value,
            "name": TOPIC_NAMES[TopicId.KESIRLER.value],
            "description": "Kesir türleri, ondalık gösterim, sıralama",
            "kazanimlar": [
                {
                    "kod": "M.4.2.1",
                    "metin": "Basit, bileşik ve tam sayılı kesirleri tanır.",
                    "difficulty_hints": _hints(
                        "Verilen kesrin türünü söyleme.",
                        "Kesir türünden örnek üretme.",
                        "Farklı türlerdeki kesirleri kıyaslama.",
                    ),
                },
                {
                    "kod": "M.4.2.2",
                    "metin": "Eşit kesirleri model üzerinde gösterir ve örnekler verir.",
                    "difficulty_hints": _hints(
                        "Verilen kesre eşit başka bir kesir yazma.",
                        "Üç kesir arasından ikisinin eşit olduğunu bulma.",
                        "Pay ya da payda kısmen gizlenmiş eşit kesir problemi.",
                    ),
                },
                {
                    "kod": "M.4.2.3",
                    "metin": "Paydaları eşit veya pay/paydası eşit kesirleri sıralar.",
                    "difficulty_hints": _hints(
                        "Paydaları eşit kesirleri sıralama.",
                        "Birim kesirleri sıralama.",
                        "Hem basit hem bileşik kesir bulunan bir grubun sıralanması.",
                    ),
                },
                {
                    "kod": "M.4.2.4",
                    "metin": "Kesirleri ondalık gösterimle ifade eder (ör. 1/2 = 0,5).",
                    "difficulty_hints": _hints(
                        "Paydası 10 olan kesri ondalığa çevirme.",
                        "Paydası 2, 4, 5 olan kesri ondalığa çevirme.",
                        "Ondalıktan kesre dönüşüm ve sadeleştirme.",
                    ),
                },
            ],
        },
        TopicId.GEOMETRI.value: {
            "topic_id": TopicId.GEOMETRI.value,
            "name": TOPIC_NAMES[TopicId.GEOMETRI.value],
            "description": "Açılar (dar, dik, geniş), çevre-alan",
            "kazanimlar": [
                {
                    "kod": "M.4.3.1",
                    "metin": "Açıları dar, dik, geniş ve doğru açı olarak sınıflandırır.",
                    "difficulty_hints": _hints(
                        "Verilen ölçüye göre açı türünü söyleme.",
                        "Açı türü verilip olası bir ölçü örneği vermesi.",
                        "Bir üçgenin açıları verilip her birinin türünü belirleme.",
                    ),
                },
                {
                    "kod": "M.4.3.2",
                    "metin": "Üçgen ve dörtgenlerin çevrelerini hesaplar.",
                    "difficulty_hints": _hints(
                        "Kenar uzunlukları verilen üçgen/dörtgenin çevresi.",
                        "Eşit kenarlı şekilde verilen çevreden kenarı bulma.",
                        "Farklı kenarlı bir şeklin çevresinden bir kenarı hesaplama.",
                    ),
                },
                {
                    "kod": "M.4.3.3",
                    "metin": "Birim kareler kullanarak şekillerin alanını belirler.",
                    "difficulty_hints": _hints(
                        "Karelajla gösterilmiş dikdörtgenin alanı.",
                        "Verilen kenar uzunluklarıyla alan hesaplama.",
                        "Birleşik şekil alanı (iki dikdörtgenin toplamı).",
                    ),
                },
            ],
        },
        TopicId.OLCME.value: {
            "topic_id": TopicId.OLCME.value,
            "name": TOPIC_NAMES[TopicId.OLCME.value],
            "description": "Birim dönüşümleri, alan-çevre birimleri",
            "kazanimlar": [
                {
                    "kod": "M.4.4.1",
                    "metin": "Uzunluk birimleri arasında dönüşüm yapar ve problem çözer.",
                    "difficulty_hints": _hints(
                        "Tek adım birim dönüşümü.",
                        "İki dönüşüm gerektiren problem.",
                        "Farklı birimlerden gelen uzunluklar üzerinde toplama/çıkarma.",
                    ),
                },
                {
                    "kod": "M.4.4.2",
                    "metin": "Alan ölçü birimi olarak metrekare ve santimetrekareyi tanır.",
                    "difficulty_hints": _hints(
                        "m²'yi cm²'ye çevirmenin tanımı.",
                        "Verilen m² değerini cm²'ye çevirme (veya tersi).",
                        "Alan karşılaştırması için birim dönüşümü gerekli problem.",
                    ),
                },
            ],
        },
        TopicId.CEBIR.value: {
            "topic_id": TopicId.CEBIR.value,
            "name": TOPIC_NAMES[TopicId.CEBIR.value],
            "description": "Örüntü ve ilişkilerde genelleme",
            "kazanimlar": [
                {
                    "kod": "M.4.5.1",
                    "metin": "Sayı örüntülerindeki kuralı bulur ve örüntünün herhangi bir adımını belirler.",
                    "difficulty_hints": _hints(
                        "Bir sonraki terimi bulma.",
                        "n. terimi kuralla hesaplama.",
                        "Verilen terimlerden kuralı çıkarıp farklı bir n. terim bulma.",
                    ),
                },
                {
                    "kod": "M.4.5.2",
                    "metin": "Eşitlik kavramını kullanarak basit denklikler oluşturur.",
                    "difficulty_hints": _hints(
                        "a + ? = b biçiminde tek bilinmeyenli denklik.",
                        "Eşitliğin bir tarafında iki işlem (örn. a + b = c − d).",
                        "Denkliği bozan/koruyan işlemleri belirleme.",
                    ),
                },
            ],
        },
    },
    5: {
        TopicId.DOGAL_SAYILAR.value: {
            "topic_id": TopicId.DOGAL_SAYILAR.value,
            "name": TOPIC_NAMES[TopicId.DOGAL_SAYILAR.value],
            "description": "Doğal sayılarla işlemler, işlem önceliği",
            "kazanimlar": [
                {
                    "kod": "M.5.1.1",
                    "metin": "En çok dokuz basamaklı doğal sayıları okur, yazar ve çözümler.",
                    "difficulty_hints": _hints(
                        "6-7 basamaklı sayıların okunuşu.",
                        "8-9 basamaklı sayıların çözümü.",
                        "Basamak değerlerinin farkı/toplamı üzerinden problem.",
                    ),
                },
                {
                    "kod": "M.5.1.2",
                    "metin": "Doğal sayılarla toplama ve çıkarma işlemlerini yapar.",
                    "difficulty_hints": _hints(
                        "Dört basamaklı tek eldeli toplama/çıkarma.",
                        "Beş-altı basamaklı eldeli/bozmalı işlem.",
                        "İki bilgiden hareketle üçüncüyü bulma (zincir problem).",
                    ),
                },
                {
                    "kod": "M.5.1.3",
                    "metin": "En çok üç basamaklı iki doğal sayının çarpma ve bölme işlemlerini yapar.",
                    "difficulty_hints": _hints(
                        "İki basamaklı × iki basamaklı çarpma veya kalansız bölme.",
                        "Üç basamaklı × iki basamaklı veya üç basamaklı ÷ iki basamaklı.",
                        "Çarpma ve bölmeyi birleştiren iki adımlı problem.",
                    ),
                },
                {
                    "kod": "M.5.1.4",
                    "metin": "Doğal sayılarla yapılan işlemlerde işlem önceliğini dikkate alır.",
                    "difficulty_hints": _hints(
                        "Parantezsiz 3 işlemli hesap.",
                        "Parantezli ve 4 işlemli hesap.",
                        "Parantez + üssüz çarpan + işlem önceliği birleşik ifade.",
                    ),
                },
                {
                    "kod": "M.5.1.5",
                    "metin": "Bölme işleminde kalanı yorumlar ve günlük hayat problemleri çözer.",
                    "difficulty_hints": _hints(
                        "Bölme sonucunu + kalan bulma.",
                        "Kalanı yorumlayarak 'kaç tam' sorusuna cevap verme.",
                        "Kalan kullanılarak ek kaynak/araç hesaplaması.",
                    ),
                },
            ],
        },
        TopicId.KESIRLER.value: {
            "topic_id": TopicId.KESIRLER.value,
            "name": TOPIC_NAMES[TopicId.KESIRLER.value],
            "description": "Kesirlerle toplama-çıkarma",
            "kazanimlar": [
                {
                    "kod": "M.5.2.1",
                    "metin": "Birim kesirleri sayı doğrusunda gösterir ve sıralar.",
                    "difficulty_hints": _hints(
                        "Birim kesri sayı doğrusunda belirtme.",
                        "Üç birim kesri sıralama.",
                        "Sayı doğrusundaki gösterimden kesri yazma.",
                    ),
                },
                {
                    "kod": "M.5.2.2",
                    "metin": "Tam sayılı kesri bileşik kesre, bileşik kesri tam sayılı kesre dönüştürür.",
                    "difficulty_hints": _hints(
                        "Tek yönlü basit dönüşüm.",
                        "İki yönlü dönüşüm.",
                        "Dönüşümün ara adımını kullanarak sıralama.",
                    ),
                },
                {
                    "kod": "M.5.2.3",
                    "metin": "Paydaları eşit kesirlerle toplama ve çıkarma işlemleri yapar.",
                    "difficulty_hints": _hints(
                        "Paydaları eşit iki kesir toplama veya çıkarma.",
                        "Üç kesri art arda toplama/çıkarma.",
                        "Bileşik kesir sonucunu sadeleştirerek yorumlama.",
                    ),
                },
                {
                    "kod": "M.5.2.4",
                    "metin": "Paydaları eşit olmayan en çok iki kesrin toplama ve çıkarma işlemini yapar.",
                    "difficulty_hints": _hints(
                        "Paydalardan biri diğerinin katı olan toplama.",
                        "Farklı paydalı kesirlerde ortak payda bulma ve işlem.",
                        "Toplama + çıkarmanın birleşik olduğu problem.",
                    ),
                },
            ],
        },
        TopicId.GEOMETRI.value: {
            "topic_id": TopicId.GEOMETRI.value,
            "name": TOPIC_NAMES[TopicId.GEOMETRI.value],
            "description": "Üçgen ve dörtgenlerin çevre-alan hesabı",
            "kazanimlar": [
                {
                    "kod": "M.5.3.1",
                    "metin": "Üçgenleri kenar ve açı özelliklerine göre sınıflandırır.",
                    "difficulty_hints": _hints(
                        "Kenar özelliğine göre üçgen türünü söyleme.",
                        "Verilen iki açıyla üçüncüyü bulup türü belirleme.",
                        "Kenar ve açı bilgisini birleştirerek tür belirleme.",
                    ),
                },
                {
                    "kod": "M.5.3.2",
                    "metin": "Dörtgen türlerini (kare, dikdörtgen, paralelkenar, eşkenar dörtgen, yamuk) tanır.",
                    "difficulty_hints": _hints(
                        "Verilen bir özelliğe uyan dörtgeni bulma.",
                        "Dörtgen türlerini birbirinden ayıran özellikleri listeleme.",
                        "Verilen özelliklerin birden fazla dörtgen türüne uyup uymadığını muhakeme.",
                    ),
                },
                {
                    "kod": "M.5.3.3",
                    "metin": "Üçgen ve dörtgenlerin çevre uzunluklarını hesaplar.",
                    "difficulty_hints": _hints(
                        "Kenarları verilen şeklin çevresi.",
                        "Çevre verilip bir kenarı bulma.",
                        "Karmaşık şeklin çevresini parçalarla hesaplama.",
                    ),
                },
                {
                    "kod": "M.5.3.4",
                    "metin": "Dikdörtgen ve karenin alanını birim kare cinsinden hesaplar.",
                    "difficulty_hints": _hints(
                        "Kenarları verilen dikdörtgen/karenin alanı.",
                        "Alan verilip bir kenarı bulma.",
                        "Birleşik şeklin alanını iki dikdörtgen olarak hesaplama.",
                    ),
                },
            ],
        },
        TopicId.OLCME.value: {
            "topic_id": TopicId.OLCME.value,
            "name": TOPIC_NAMES[TopicId.OLCME.value],
            "description": "Hacim ölçme, litre-mililitre",
            "kazanimlar": [
                {
                    "kod": "M.5.4.1",
                    "metin": "Uzunluk birimleri arasındaki dönüşümleri yapar ve problem çözer.",
                    "difficulty_hints": _hints(
                        "Tek adım birim dönüşümü.",
                        "Karışık birim içeren toplam/farktan metre bulma.",
                        "Üç farklı birimdeki uzunlukları kıyaslama.",
                    ),
                },
                {
                    "kod": "M.5.4.2",
                    "metin": "Litre ve mililitreyi tanır, sıvı miktarlarını ölçer ve dönüştürür.",
                    "difficulty_hints": _hints(
                        "L'yi mL'ye veya tersine çevirme.",
                        "Karışık birimde (2 L 500 mL) toplam hesabı.",
                        "Oransal kullanım problemi (örn. 4 kutunun toplam hacmi).",
                    ),
                },
                {
                    "kod": "M.5.4.3",
                    "metin": "Sıvı ölçme birimlerini kullanarak günlük hayat problemleri çözer.",
                    "difficulty_hints": _hints(
                        "Tek adımlı günlük hayat problemi.",
                        "İki adımlı (dolum + kullanım) problem.",
                        "Oran gerektiren ölçekleme problemi (tarif miktarını artırma).",
                    ),
                },
            ],
        },
        TopicId.CEBIR.value: {
            "topic_id": TopicId.CEBIR.value,
            "name": TOPIC_NAMES[TopicId.CEBIR.value],
            "description": "Basit denklemler (x + 3 = 7)",
            "kazanimlar": [
                {
                    "kod": "M.5.5.1",
                    "metin": "Bir bilinmeyen içeren basit denklemleri (x + a = b, x − a = b biçiminde) çözer.",
                    "difficulty_hints": _hints(
                        "x + a = b biçiminde doğrudan çözüm.",
                        "x − a = b veya a − x = b çözümü.",
                        "Bilinmeyeni bulduktan sonra ek bir küçük hesap yapma.",
                    ),
                },
                {
                    "kod": "M.5.5.2",
                    "metin": "Sözel olarak ifade edilen durumu cebirsel denklem olarak yazar.",
                    "difficulty_hints": _hints(
                        "Tek adımlı sözel ifadenin denkleme çevrilmesi.",
                        "Denklemi kurup çözüme ulaşma.",
                        "Ters yönde: denklem verilip uygun bir sözel bağlam üretme.",
                    ),
                },
            ],
        },
    },
    6: {
        TopicId.DOGAL_SAYILAR.value: {
            "topic_id": TopicId.DOGAL_SAYILAR.value,
            "name": TOPIC_NAMES[TopicId.DOGAL_SAYILAR.value],
            "description": "Tam sayılar, mutlak değer, toplama-çıkarma",
            "kazanimlar": [
                {
                    "kod": "M.6.1.1",
                    "metin": "Tam sayıları tanır ve sayı doğrusunda gösterir.",
                    "difficulty_hints": _hints(
                        "Verilen tam sayıyı sayı doğrusunda konumlandırma.",
                        "Üç-dört tam sayıyı sıralayarak gösterme.",
                        "İki tam sayı arasındaki tam sayıları sözel tarif etme.",
                    ),
                },
                {
                    "kod": "M.6.1.2",
                    "metin": "Bir tam sayının mutlak değerini belirler ve yorumlar.",
                    "difficulty_hints": _hints(
                        "Basit mutlak değer hesabı |−a|.",
                        "|x| = a tipinde iki çözüm bulma.",
                        "Mutlak değer içeren karşılaştırma problemi.",
                    ),
                },
                {
                    "kod": "M.6.1.3",
                    "metin": "Tam sayılarla toplama ve çıkarma işlemleri yapar.",
                    "difficulty_hints": _hints(
                        "Aynı işaretli tam sayıların toplamı.",
                        "Farklı işaretli toplama veya çıkarma.",
                        "Üç veya daha fazla tam sayılı ifadede işlem sonucu.",
                    ),
                },
                {
                    "kod": "M.6.1.4",
                    "metin": "Tam sayıları büyüklük açısından karşılaştırır ve sıralar.",
                    "difficulty_hints": _hints(
                        "İki tam sayı karşılaştırması.",
                        "Karışık (negatif + pozitif) tam sayıları sıralama.",
                        "Sıralamadan eşitsizlik koşulu oluşturma.",
                    ),
                },
            ],
        },
        TopicId.KESIRLER.value: {
            "topic_id": TopicId.KESIRLER.value,
            "name": TOPIC_NAMES[TopicId.KESIRLER.value],
            "description": "Kesirlerle dört işlem",
            "kazanimlar": [
                {
                    "kod": "M.6.2.1",
                    "metin": "Paydaları farklı kesirlerle toplama ve çıkarma işlemi yapar.",
                    "difficulty_hints": _hints(
                        "Paydalardan biri diğerinin katı.",
                        "Ortak paydayı bulmayı gerektiren iki kesirli işlem.",
                        "Üç kesirli veya tam sayılı kesirli karışık işlem.",
                    ),
                },
                {
                    "kod": "M.6.2.2",
                    "metin": "Kesirlerle çarpma işlemini açıklar ve yapar.",
                    "difficulty_hints": _hints(
                        "İki basit kesrin çarpımı.",
                        "Tam sayılı kesirin başka bir kesirle çarpımı.",
                        "Sonucu sadeleştirme ve tam sayılı kesre çevirme.",
                    ),
                },
                {
                    "kod": "M.6.2.3",
                    "metin": "Kesirlerle bölme işlemini açıklar ve yapar.",
                    "difficulty_hints": _hints(
                        "Bir tam sayının bir birim kesre bölümü.",
                        "İki kesrin bölümü.",
                        "Çok adımlı problemde kesirli bölme kullanımı.",
                    ),
                },
                {
                    "kod": "M.6.2.4",
                    "metin": "Ondalık gösterimlerle dört işlem yapar.",
                    "difficulty_hints": _hints(
                        "Ondalık toplama veya çıkarma (tek basamak).",
                        "Ondalıklı çarpma veya bölme.",
                        "İki adımlı problem ile dört işlemin birleşimi.",
                    ),
                },
            ],
        },
        TopicId.GEOMETRI.value: {
            "topic_id": TopicId.GEOMETRI.value,
            "name": TOPIC_NAMES[TopicId.GEOMETRI.value],
            "description": "Alan hesaplamaları (paralelkenar, üçgen, yamuk)",
            "kazanimlar": [
                {
                    "kod": "M.6.3.1",
                    "metin": "Paralelkenarın alanını hesaplar.",
                    "difficulty_hints": _hints(
                        "Taban ve yükseklik verilip alan.",
                        "Alan verilip taban veya yüksekliği bulma.",
                        "İki paralelkenar arasındaki alan farkı problemi.",
                    ),
                },
                {
                    "kod": "M.6.3.2",
                    "metin": "Üçgenin alanını hesaplar.",
                    "difficulty_hints": _hints(
                        "Taban ve yükseklikten alan bulma.",
                        "Alan verilip bilinmeyen kenarı bulma.",
                        "Dikdörtgenden oluşturulan iki üçgenin alanlarını kıyaslama.",
                    ),
                },
                {
                    "kod": "M.6.3.3",
                    "metin": "Yamuk şeklin alanını hesaplar.",
                    "difficulty_hints": _hints(
                        "Paralel kenarlar ve yükseklikten yamuk alanı.",
                        "Yamuğun alanı verilip bir paralel kenarı bulma.",
                        "Birleşik alanı (yamuk + dikdörtgen) bulma.",
                    ),
                },
            ],
        },
        TopicId.OLCME.value: {
            "topic_id": TopicId.OLCME.value,
            "name": TOPIC_NAMES[TopicId.OLCME.value],
            "description": "Sıvı ölçüleri, hacim hesaplama",
            "kazanimlar": [
                {
                    "kod": "M.6.4.1",
                    "metin": "Sıvı ölçme birimleri arasındaki dönüşümleri yapar.",
                    "difficulty_hints": _hints(
                        "L↔mL basit dönüşüm.",
                        "İki birim arasında toplama/çıkarma.",
                        "Ölçekli problem (kaç tane 250 mL 1 L eder).",
                    ),
                },
                {
                    "kod": "M.6.4.2",
                    "metin": "Dikdörtgenler prizmasının hacmini birim küp cinsinden hesaplar.",
                    "difficulty_hints": _hints(
                        "Üç boyut verilip hacim bulma.",
                        "Hacim verilip bir boyutu bulma.",
                        "Hacim değişimi problemi (su eklenmesi/çıkarılması).",
                    ),
                },
            ],
        },
        TopicId.CEBIR.value: {
            "topic_id": TopicId.CEBIR.value,
            "name": TOPIC_NAMES[TopicId.CEBIR.value],
            "description": "Cebirsel ifadeler, birinci dereceden denklemler",
            "kazanimlar": [
                {
                    "kod": "M.6.5.1",
                    "metin": "Bir değişken içeren cebirsel ifadeleri yazar ve değerini hesaplar.",
                    "difficulty_hints": _hints(
                        "x değeri verilip 2x + 3 hesaplama.",
                        "Sözel durumu cebirsel ifadeye çevirme.",
                        "Değişken yerine farklı iki değer koyup sonuçları karşılaştırma.",
                    ),
                },
                {
                    "kod": "M.6.5.2",
                    "metin": "Birinci dereceden bir bilinmeyenli denklemleri kurar.",
                    "difficulty_hints": _hints(
                        "Tek adımlı sözel ifadeden denklem kurma.",
                        "İki adımlı problem için denklem (ax + b = c).",
                        "İki bilinmeyenin birbirine bağlı tanımlandığı denklem kurma.",
                    ),
                },
                {
                    "kod": "M.6.5.3",
                    "metin": "Birinci dereceden bir bilinmeyenli denklemleri çözer.",
                    "difficulty_hints": _hints(
                        "ax = b veya x + a = b türü çözüm.",
                        "ax + b = c çözümü.",
                        "Her iki tarafta değişken içeren denklem çözümü.",
                    ),
                },
            ],
        },
    },
    7: {
        TopicId.DOGAL_SAYILAR.value: {
            "topic_id": TopicId.DOGAL_SAYILAR.value,
            "name": TOPIC_NAMES[TopicId.DOGAL_SAYILAR.value],
            "description": "Tam sayılarla çarpma-bölme, işlem önceliği",
            "kazanimlar": [
                {
                    "kod": "M.7.1.1",
                    "metin": "Tam sayılarla çarpma işlemini yapar.",
                    "difficulty_hints": _hints(
                        "Aynı işaretli iki tam sayının çarpımı.",
                        "Farklı işaretli tam sayılarla çarpma.",
                        "Üçlü çarpım veya işaret kuralını muhakeme gerektiren problem.",
                    ),
                },
                {
                    "kod": "M.7.1.2",
                    "metin": "Tam sayılarla bölme işlemini yapar.",
                    "difficulty_hints": _hints(
                        "Aynı işaretli iki tam sayıda kalansız bölme.",
                        "Farklı işaretli bölme.",
                        "Çarpma + bölmeyi birleştiren sözel problem.",
                    ),
                },
                {
                    "kod": "M.7.1.3",
                    "metin": "Tam sayılarla yapılan işlemlerde işlem önceliğini uygular.",
                    "difficulty_hints": _hints(
                        "Üç işlemli parantezsiz ifade.",
                        "Parantezli ve 4 işlemli ifade.",
                        "Negatif üslü veya parantez içinde parantez bulunan ifade.",
                    ),
                },
                {
                    "kod": "M.7.1.4",
                    "metin": "Tam sayıların kuvvetlerini hesaplar.",
                    "difficulty_hints": _hints(
                        "(+a)² veya (+a)³ basit hesap.",
                        "(−a)² veya (−a)³ işaret kuralıyla.",
                        "Üslü ifadelerin toplamı/çarpımı.",
                    ),
                },
            ],
        },
        TopicId.KESIRLER.value: {
            "topic_id": TopicId.KESIRLER.value,
            "name": TOPIC_NAMES[TopicId.KESIRLER.value],
            "description": "Rasyonel sayılar, rasyonel sayılarla işlemler",
            "kazanimlar": [
                {
                    "kod": "M.7.2.1",
                    "metin": "Rasyonel sayıyı tanır ve sayı doğrusunda gösterir.",
                    "difficulty_hints": _hints(
                        "Verilen kesir/ondalığın sayı doğrusundaki yeri.",
                        "Negatif rasyonel sayıları sıralama.",
                        "Verilen iki rasyonel sayı arasında üçüncüyü bulma.",
                    ),
                },
                {
                    "kod": "M.7.2.2",
                    "metin": "Rasyonel sayıları farklı biçimlerde (kesir, ondalık) ifade eder.",
                    "difficulty_hints": _hints(
                        "Paydası 10/100 olan kesri ondalığa çevirme.",
                        "Rasyonel sayıyı sadeleştirilmiş kesre çevirme.",
                        "Devirli ondalık ↔ kesir dönüşümü.",
                    ),
                },
                {
                    "kod": "M.7.2.3",
                    "metin": "Rasyonel sayılarla toplama ve çıkarma işlemi yapar.",
                    "difficulty_hints": _hints(
                        "Aynı paydalı iki rasyonel sayıda işlem.",
                        "Farklı paydalı ve işaretli rasyonel sayılar.",
                        "Üç rasyonel sayılı karışık işlem.",
                    ),
                },
                {
                    "kod": "M.7.2.4",
                    "metin": "Rasyonel sayılarla çarpma ve bölme işlemi yapar.",
                    "difficulty_hints": _hints(
                        "İki basit rasyonel sayının çarpımı.",
                        "Bölmeyi çarpmaya çevirerek hesap.",
                        "İşlem önceliği + rasyonel dört işlem karma.",
                    ),
                },
            ],
        },
        TopicId.GEOMETRI.value: {
            "topic_id": TopicId.GEOMETRI.value,
            "name": TOPIC_NAMES[TopicId.GEOMETRI.value],
            "description": "Çember ve dairede uzunluk-alan, merkez açı",
            "kazanimlar": [
                {
                    "kod": "M.7.3.1",
                    "metin": "Çemberin temel elemanlarını (yarıçap, çap, kiriş) tanır.",
                    "difficulty_hints": _hints(
                        "Temel elemanı tanımlama.",
                        "Yarıçap ↔ çap ilişkisi kullanarak hesap.",
                        "Kiriş ile yarıçap arasındaki eşitsizlikleri muhakeme.",
                    ),
                },
                {
                    "kod": "M.7.3.2",
                    "metin": "Çember ve daire arasındaki farkı açıklar.",
                    "difficulty_hints": _hints(
                        "Çember ve daire tanımlarını ayırt etme.",
                        "Günlük hayattan çember/daire örnekleri.",
                        "Çember uzunluğu ile daire alanı arasındaki kavramsal fark.",
                    ),
                },
                {
                    "kod": "M.7.3.3",
                    "metin": "Çemberin uzunluğunu π sayısını kullanarak hesaplar.",
                    "difficulty_hints": _hints(
                        "Yarıçap verilip çember uzunluğu (π = 22/7 veya 3).",
                        "Çap verilip uzunluk, veya uzunluktan yarıçap.",
                        "Çember uzunluğu verilip farklı bir nicelik (döngü sayısı) bulma.",
                    ),
                },
                {
                    "kod": "M.7.3.4",
                    "metin": "Dairenin alanını hesaplar.",
                    "difficulty_hints": _hints(
                        "Yarıçap verilip daire alanı (π = 3).",
                        "Çap verilip alan veya alan verilip yarıçap.",
                        "Daire alanı ile kare alanı karşılaştırması.",
                    ),
                },
                {
                    "kod": "M.7.3.5",
                    "metin": "Merkez açı ile gördüğü daire diliminin alanı arasındaki ilişkiyi kullanır.",
                    "difficulty_hints": _hints(
                        "Basit oran (90° = 1/4 daire).",
                        "Merkez açı verilip dilim alanı.",
                        "Dilim alanı verilip merkez açıyı bulma.",
                    ),
                },
            ],
        },
        TopicId.OLCME.value: {
            "topic_id": TopicId.OLCME.value,
            "name": TOPIC_NAMES[TopicId.OLCME.value],
            "description": "Prizmaların hacmi ve yüzey alanı",
            "kazanimlar": [
                {
                    "kod": "M.7.4.1",
                    "metin": "Dikdörtgenler prizması, kare prizma ve küpün hacmini hesaplar.",
                    "difficulty_hints": _hints(
                        "Verilen boyutlarla hacim.",
                        "Hacim verilip bilinmeyen bir boyutu bulma.",
                        "Farklı prizmaların hacimlerini kıyaslama.",
                    ),
                },
                {
                    "kod": "M.7.4.2",
                    "metin": "Prizmaların yüzey alanını hesaplar.",
                    "difficulty_hints": _hints(
                        "Küpün yüzey alanı.",
                        "Dikdörtgenler prizmasının yüzey alanı.",
                        "Yüzey alanı verilip bir boyutu bulma.",
                    ),
                },
            ],
        },
        TopicId.CEBIR.value: {
            "topic_id": TopicId.CEBIR.value,
            "name": TOPIC_NAMES[TopicId.CEBIR.value],
            "description": "Eşitsizlikler, doğrusal denklemler, oran-orantı",
            "kazanimlar": [
                {
                    "kod": "M.7.5.1",
                    "metin": "Eşitliğin korunumunu kullanarak denklem çözmeye temel oluşturur.",
                    "difficulty_hints": _hints(
                        "Her iki tarafa aynı sayıyı ekleme/çıkarma örneği.",
                        "Her iki tarafı aynı sayıyla çarpma/bölme uygulaması.",
                        "Koruma ilkesini karşılaştırarak hangi işlemin doğru olduğunu seçme.",
                    ),
                },
                {
                    "kod": "M.7.5.2",
                    "metin": "Birinci dereceden bir bilinmeyenli denklemleri çözer.",
                    "difficulty_hints": _hints(
                        "ax + b = c biçiminde çözüm.",
                        "Her iki tarafta x bulunan denklem.",
                        "Kesirli katsayılı veya parantezli denklem.",
                    ),
                },
                {
                    "kod": "M.7.5.3",
                    "metin": "Birinci dereceden bir bilinmeyenli eşitsizlikleri çözer ve sayı doğrusunda gösterir.",
                    "difficulty_hints": _hints(
                        "x + a < b türü tek adımlı eşitsizlik.",
                        "ax + b ≥ c çözümü.",
                        "Katsayının negatif olması nedeniyle yönün değişmesi.",
                    ),
                },
                {
                    "kod": "M.7.5.4",
                    "metin": "Oran ve orantı kavramlarını kullanarak günlük hayat problemleri çözer.",
                    "difficulty_hints": _hints(
                        "Doğru orantı tek adım (ikili oran).",
                        "Doğru veya ters orantı problemi.",
                        "Birden fazla oranı birleştiren problem (dört terimli orantı).",
                    ),
                },
            ],
        },
    },
}


def get_grades() -> list[dict]:
    return [
        {
            "id": grade,
            "name": f"{grade}. Sınıf",
            "level": GRADE_LEVELS[grade].value,
        }
        for grade in sorted(CURRICULUM.keys())
    ]


def get_topics_for_grade(grade: int) -> list[Topic]:
    if grade not in CURRICULUM:
        return []
    return list(CURRICULUM[grade].values())


def get_topic(grade: int, topic_id: str) -> Topic | None:
    return CURRICULUM.get(grade, {}).get(topic_id)


def get_kazanim(grade: int, topic_id: str, kazanim_kod: str) -> Kazanim | None:
    topic = get_topic(grade, topic_id)
    if topic is None:
        return None
    for k in topic["kazanimlar"]:
        if k["kod"] == kazanim_kod:
            return k
    return None


def is_topic_available(grade: int, topic_id: str) -> bool:
    return get_topic(grade, topic_id) is not None
