"""5. sınıf few-shot örnek havuzu (MVP demo sınıfı)."""
from app.models.enums import QuestionType

EXAMPLES: dict[str, list[dict]] = {
    "M.5.1.1": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "473.205.610 sayısının okunuşunu yazınız.",
            "answer": "Dört yüz yetmiş üç milyon iki yüz beş bin altı yüz on",
            "solution": "Sınıflara göre okunur: 473 milyon, 205 bin, 610.",
        },
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "orta",
            "question": "85.430.207 sayısında 4 rakamının basamak değeri kaçtır?",
            "answer": "400.000",
            "solution": "4 rakamı yüz binler basamağındadır, basamak değeri 4 × 100.000 = 400.000.",
        },
    ],
    "M.5.1.2": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "12.456 + 8.379 işleminin sonucu kaçtır?",
            "answer": "20.835",
            "solution": "12.456 + 8.379 = 20.835",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Bir kütüphanede 24.350 kitap vardır. 3.785 kitap daha alınınca toplam kitap sayısı kaç olur?",
            "answer": "28.135 kitap",
            "solution": "24.350 + 3.785 = 28.135",
        },
    ],
    "M.5.1.3": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "246 × 35 işleminin sonucu kaçtır?",
            "answer": "8.610",
            "solution": "246 × 35 = 246 × 30 + 246 × 5 = 7.380 + 1.230 = 8.610",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Bir okulda 432 öğrenciye eşit sayıda paylaştırılmak üzere 12.960 defter alınmıştır. Her öğrenciye kaç defter düşer?",
            "answer": "30 defter",
            "solution": "12.960 ÷ 432 = 30",
        },
    ],
    "M.5.1.4": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "12 + 4 × (8 − 5) işleminin sonucu kaçtır?",
            "answer": "24",
            "solution": "Önce parantez: 8−5=3. Sonra çarpma: 4×3=12. En son toplama: 12+12=24.",
        },
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "zor",
            "question": "20 − 6 ÷ 2 + 3 × 4 işleminin sonucu kaçtır?",
            "answer": "29",
            "solution": "Çarpma ve bölme önce: 6÷2=3, 3×4=12. Sonra: 20−3+12 = 29.",
        },
    ],
    "M.5.1.5": [
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Bir manav 250 elmayı 8'erli kasalara yerleştirecektir. Kaç tam kasa olur ve kaç elma kalır?",
            "answer": "31 kasa, 2 elma kalır",
            "solution": "250 ÷ 8 = 31 (kalan 2). 31 × 8 = 248, 250−248 = 2 elma kalır.",
        },
        {
            "type": QuestionType.GUNLUK_HAYAT,
            "difficulty": "zor",
            "question": "47 öğrenci her birine 6 kişi binebilen otomobillere binecektir. En az kaç otomobil gerekir?",
            "answer": "8 otomobil",
            "solution": "47 ÷ 6 = 7 (kalan 5). Kalanlar için bir otomobil daha gerekir: 7+1 = 8.",
        },
    ],
    "M.5.2.1": [
        {
            "type": QuestionType.MODELLEME,
            "difficulty": "orta",
            "question": "Sayı doğrusunda 0 ile 1 arasını 5 eşit parçaya böldüğümüzde 3. çentik hangi kesre karşılık gelir?",
            "answer": "3/5",
            "solution": "0–1 arası 5 eşit parçaya bölünür, her parça 1/5'tir. 3. çentik 3/5'i gösterir.",
        },
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "orta",
            "question": "1/3, 1/6 ve 1/4 birim kesirlerini küçükten büyüğe sıralayınız.",
            "answer": "1/6 < 1/4 < 1/3",
            "solution": "Birim kesirlerde payda büyüdükçe kesir küçülür, dolayısıyla 1/6 en küçük, 1/3 en büyüktür.",
        },
    ],
    "M.5.2.2": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "17/4 bileşik kesrini tam sayılı kesir olarak yazınız.",
            "answer": "4 tam 1/4",
            "solution": "17 ÷ 4 = 4 kalan 1, dolayısıyla 17/4 = 4 tam 1/4.",
        },
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "3 tam 2/5 tam sayılı kesrini bileşik kesre dönüştürünüz.",
            "answer": "17/5",
            "solution": "(3 × 5) + 2 = 17. Sonuç: 17/5.",
        },
    ],
    "M.5.2.3": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "5/8 + 2/8 işleminin sonucu kaçtır?",
            "answer": "7/8",
            "solution": "Paydalar eşit; paylar toplanır: 5+2=7. Sonuç: 7/8.",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Bir karpuzun 3/10'unu Ayşe, 4/10'unu Burak yedi. İkisi birlikte karpuzun kaçta kaçını yemiştir?",
            "answer": "7/10",
            "solution": "3/10 + 4/10 = 7/10",
        },
    ],
    "M.5.2.4": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "1/2 + 1/3 işleminin sonucu kaçtır?",
            "answer": "5/6",
            "solution": "Paydaları eşitlemek için ortak payda 6: 3/6 + 2/6 = 5/6.",
        },
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "zor",
            "question": "3/4 − 2/5 işleminin sonucu kaçtır?",
            "answer": "7/20",
            "solution": "Ortak payda 20: 15/20 − 8/20 = 7/20.",
        },
    ],
    "M.5.2.5": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "200 sayısının %25'i kaçtır?",
            "answer": "50",
            "solution": "200 × 25/100 = 50.",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Bir kazak 480 TL'dir. Mağaza %20 indirim uyguladığında kazağın yeni fiyatı kaç TL olur?",
            "answer": "384 TL",
            "solution": "İndirim miktarı: 480 × 20/100 = 96 TL. Yeni fiyat: 480 − 96 = 384 TL.",
        },
    ],
    "M.5.3.1": [
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "orta",
            "question": "Tüm açıları 60 derece olan bir üçgen hangi tür üçgendir?",
            "answer": "Eşkenar üçgen (aynı zamanda dar açılı üçgendir)",
            "solution": "Açıları eşit olan üçgen eşkenardır. 60° dar açıdır, dolayısıyla dar açılı üçgendir.",
        },
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "orta",
            "question": "Bir üçgenin iki açısı 40° ve 75° ise üçüncü açısı kaç derecedir?",
            "answer": "65°",
            "solution": "Üçgenin iç açıları toplamı 180°. 180 − (40+75) = 180 − 115 = 65°.",
        },
    ],
    "M.5.3.2": [
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "orta",
            "question": "Karşılıklı kenarları paralel ve eşit, tüm açıları dik olan dörtgen nedir?",
            "answer": "Dikdörtgen (kareye özel hâl)",
            "solution": "Tüm açıları dik ve karşılıklı kenarları eşit olan dörtgen dikdörtgendir.",
        },
        {
            "type": QuestionType.MODELLEME,
            "difficulty": "orta",
            "question": "Yamuk şeklini sözel olarak tarif ediniz.",
            "answer": "En az bir çift karşılıklı kenarı paralel olan dörtgendir.",
            "solution": "Yamuğun tanımı: bir çift karşılıklı kenarı paralel olan dörtgen.",
        },
    ],
    "M.5.3.3": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "Kenar uzunlukları 7 cm, 9 cm ve 12 cm olan üçgenin çevresi kaç cm'dir?",
            "answer": "28 cm",
            "solution": "Çevre = 7 + 9 + 12 = 28 cm.",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Eni 8 m, boyu 14 m olan dikdörtgen şeklindeki bir bahçenin etrafına tel çekilecektir. Kaç metre tel gerekir?",
            "answer": "44 m",
            "solution": "Çevre = 2×(8+14) = 2×22 = 44 m.",
        },
    ],
    "M.5.3.4": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "Bir kenarı 6 cm olan karenin alanı kaç cm²'dir?",
            "answer": "36 cm²",
            "solution": "Karenin alanı = kenar × kenar = 6 × 6 = 36 cm².",
        },
        {
            "type": QuestionType.GUNLUK_HAYAT,
            "difficulty": "kolay",
            "question": "Eni 5 m, boyu 8 m olan bir odanın zeminine halı serilecektir. Kaç m² halı gerekir?",
            "answer": "40 m²",
            "solution": "Dikdörtgenin alanı = en × boy = 5 × 8 = 40 m².",
        },
    ],
    "M.5.3.5": [
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "kolay",
            "question": "İki ucu belli olan, sınırlı ve uzunluğu ölçülebilen geometrik şekle ne ad verilir? Sembolünü açıklayınız.",
            "answer": "Doğru parçası; AB doğru parçası [AB] sembolüyle gösterilir.",
            "solution": "Doğru parçası iki ucu belli, sınırlı ve uzunluğu ölçülebilen şekildir. AB doğru parçası, A ve B noktaları arasındadır ve [AB] biçiminde yazılır.",
        },
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "orta",
            "question": "AB ve CD doğruları paralel ve EF doğrusu AB doğrusuna diktir. EF doğrusunun CD doğrusu ile ilişkisi nasıldır? Açıklayınız.",
            "answer": "EF doğrusu CD doğrusuna da diktir.",
            "solution": "AB // CD ve EF ⊥ AB ise, paralel doğrulara çizilen aynı dikme her iki doğruyla da aynı açıyı oluşturur. Bu nedenle EF ⊥ CD olur.",
        },
    ],
    "M.5.4.1": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "3 km 250 m kaç metredir?",
            "answer": "3.250 m",
            "solution": "1 km = 1000 m. 3×1000 + 250 = 3.250 m.",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Bir koşucu sabah 1.500 m, akşam 2 km koştu. Toplam kaç metre koşmuştur?",
            "answer": "3.500 m",
            "solution": "2 km = 2.000 m. 1.500 + 2.000 = 3.500 m.",
        },
    ],
    "M.5.4.2": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "4 L 750 mL kaç mililitredir?",
            "answer": "4.750 mL",
            "solution": "1 L = 1000 mL. 4×1000 + 750 = 4.750 mL.",
        },
        {
            "type": QuestionType.GUNLUK_HAYAT,
            "difficulty": "orta",
            "question": "Bir bidonda 3 L 200 mL süt vardır. 1 L 600 mL süt kullanılırsa kaç mL süt kalır?",
            "answer": "1.600 mL",
            "solution": "3.200 mL − 1.600 mL = 1.600 mL.",
        },
    ],
    "M.5.4.3": [
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Bir su deposu 50 L su almaktadır. Depo yarısına kadar doluysa içinde kaç mL su vardır?",
            "answer": "25.000 mL",
            "solution": "50 L'nin yarısı 25 L = 25.000 mL.",
        },
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "orta",
            "question": "Her biri 250 mL olan 8 adet meyve suyu kutusu kaç litre meyve suyu eder?",
            "answer": "2 L",
            "solution": "8 × 250 = 2.000 mL = 2 L.",
        },
    ],
    "M.5.5.1": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "x + 17 = 42 denkleminde x kaçtır?",
            "answer": "x = 25",
            "solution": "x = 42 − 17 = 25.",
        },
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "y − 9 = 15 denkleminde y kaçtır?",
            "answer": "y = 24",
            "solution": "y = 15 + 9 = 24.",
        },
    ],
    "M.5.5.2": [
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Ali'nin yaşının 7 fazlası 19'dur. Ali kaç yaşındadır? Önce denklem yazıp çözünüz.",
            "answer": "12 yaşında",
            "solution": "x + 7 = 19. Buradan x = 19 − 7 = 12.",
        },
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "zor",
            "question": "Bir sayının 8 eksiği 14 ediyor. Bu sayıyı bulunuz.",
            "answer": "22",
            "solution": "x − 8 = 14. Buradan x = 14 + 8 = 22.",
        },
    ],
    "M.5.6.1": [
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "kolay",
            "question": "Bir sınıftaki 25 öğrencinin en sevdiği meyve sayıları şöyledir: elma 8, muz 6, çilek 7, üzüm 4. Bu veriyi sıklık tablosuna aktardığınızda en yüksek sıklığa sahip meyve hangisidir?",
            "answer": "Elma (8)",
            "solution": "Sıklıklar karşılaştırılır: elma=8, çilek=7, muz=6, üzüm=4. En yüksek sıklık 8 ile elmaya aittir.",
        },
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "orta",
            "question": "Bir sütun grafiğinde 3. sınıf 18 kitap, 4. sınıf 22 kitap, 5. sınıf 30 kitap okumuştur. 5. sınıfın okuduğu kitap sayısı, 3. sınıftan kaç fazladır ve toplam kaç kitap okunmuştur?",
            "answer": "5. sınıf 12 kitap fazla okumuştur; toplam 70 kitap okunmuştur.",
            "solution": "Fark: 30 − 18 = 12. Toplam: 18 + 22 + 30 = 70.",
        },
    ],
}
