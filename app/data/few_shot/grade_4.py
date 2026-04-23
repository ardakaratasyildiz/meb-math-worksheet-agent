"""4. sınıf few-shot örnek havuzu."""
from app.models.enums import QuestionType

EXAMPLES: dict[str, list[dict]] = {
    "M.4.1.1": [
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "orta",
            "question": "245.318 sayısının okunuşunu yazınız.",
            "answer": "İki yüz kırk beş bin üç yüz on sekiz",
            "solution": "Sınıflara ayırarak okunur: 245 bin, 318.",
        },
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "orta",
            "question": "508.273 sayısında 8 rakamının basamak değeri kaçtır?",
            "answer": "8.000",
            "solution": "8 binler basamağındadır: 8 × 1000 = 8.000.",
        },
    ],
    "M.4.1.2": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "45.123 ; 45.213 ; 45.312 sayılarını küçükten büyüğe sıralayınız.",
            "answer": "45.123 < 45.213 < 45.312",
            "solution": "Yüzler basamağı karşılaştırılır.",
        },
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "zor",
            "question": "On binler basamağı 7, diğer basamakları sıfır olan sayı kaçtır?",
            "answer": "70.000",
            "solution": "7 × 10.000 = 70.000.",
        },
    ],
    "M.4.1.3": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "8.456 + 2.789 işleminin sonucu kaçtır?",
            "answer": "11.245",
            "solution": "8.456 + 2.789 = 11.245.",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Bir markete pazartesi 3.450, salı 4.620 müşteri geldi. İki günde toplam kaç müşteri gelmiştir?",
            "answer": "8.070 müşteri",
            "solution": "3.450 + 4.620 = 8.070.",
        },
    ],
    "M.4.1.4": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "zor",
            "question": "234 × 56 işleminin sonucu kaçtır?",
            "answer": "13.104",
            "solution": "234 × 50 = 11.700; 234 × 6 = 1.404. Toplam: 13.104.",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Bir koltukta 28 kişi oturabiliyor. 35 koltukta toplam kaç kişi oturabilir?",
            "answer": "980 kişi",
            "solution": "28 × 35 = 980.",
        },
    ],
    "M.4.1.5": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "672 ÷ 24 işleminin sonucu kaçtır?",
            "answer": "28",
            "solution": "672 ÷ 24 = 28.",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "576 öğrenci 24 sınıfa eşit dağıtılırsa her sınıfta kaç öğrenci olur?",
            "answer": "24 öğrenci",
            "solution": "576 ÷ 24 = 24.",
        },
    ],
    "M.4.2.1": [
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "orta",
            "question": "5/8, 9/4 ve 2 tam 1/3 kesirlerini sırasıyla basit/bileşik/tam sayılı olarak sınıflandırınız.",
            "answer": "5/8 basit, 9/4 bileşik, 2 tam 1/3 tam sayılı kesir.",
            "solution": "Pay paydadan küçükse basit, büyükse bileşik; tam sayı içeriyorsa tam sayılı kesirdir.",
        },
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "kolay",
            "question": "11/3 kesri hangi kesir türüdür?",
            "answer": "Bileşik kesir",
            "solution": "Pay (11) paydadan (3) büyük olduğu için bileşik kesirdir.",
        },
    ],
    "M.4.2.2": [
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "orta",
            "question": "1/2 kesrine eşit olan iki kesir yazınız.",
            "answer": "2/4 ve 3/6",
            "solution": "Pay ve payda aynı sayı ile çarpılırsa eşit kesirler oluşur.",
        },
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "orta",
            "question": "2/3 kesri ile eşit olan kesri seçiniz: 4/9, 4/6, 6/8.",
            "answer": "4/6",
            "solution": "2/3'ün hem payı hem paydası 2 ile çarpılırsa 4/6 elde edilir.",
        },
    ],
    "M.4.2.3": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "2/7 ; 5/7 ; 4/7 kesirlerini küçükten büyüğe sıralayınız.",
            "answer": "2/7 < 4/7 < 5/7",
            "solution": "Paydaları eşit kesirlerde pay büyüdükçe kesir büyür.",
        },
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "orta",
            "question": "1/4 ; 1/2 ; 1/8 birim kesirlerini büyükten küçüğe sıralayınız.",
            "answer": "1/2 > 1/4 > 1/8",
            "solution": "Birim kesirlerde payda küçüldükçe kesir büyür.",
        },
    ],
    "M.4.2.4": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "3/10 kesrinin ondalık gösterimi nedir?",
            "answer": "0,3",
            "solution": "Paydası 10 olan kesirde pay virgülden sonraya yazılır: 0,3.",
        },
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "0,75 ondalık sayısının kesir gösterimi nedir? (sadeleştirilmiş)",
            "answer": "3/4",
            "solution": "0,75 = 75/100 = 3/4.",
        },
    ],
    "M.4.3.1": [
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "kolay",
            "question": "75°'lik bir açı dar mıdır, dik midir, geniş midir?",
            "answer": "Dar açı",
            "solution": "90°'den küçük açılar dardır.",
        },
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "kolay",
            "question": "120°'lik bir açının türü nedir?",
            "answer": "Geniş açı",
            "solution": "90° ile 180° arasındaki açılar geniş açıdır.",
        },
    ],
    "M.4.3.2": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "Kenar uzunlukları 8 cm, 11 cm ve 14 cm olan üçgenin çevresi kaç cm'dir?",
            "answer": "33 cm",
            "solution": "8 + 11 + 14 = 33 cm.",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Eni 12 cm, boyu 18 cm olan dikdörtgenin çevresi kaç cm'dir?",
            "answer": "60 cm",
            "solution": "Çevre = 2 × (12 + 18) = 60 cm.",
        },
    ],
    "M.4.3.3": [
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "kolay",
            "question": "Eni 4, boyu 7 birim olan dikdörtgenin alanı kaç birim karedir?",
            "answer": "28 birim kare",
            "solution": "Alan = en × boy = 4 × 7 = 28.",
        },
        {
            "type": QuestionType.MODELLEME,
            "difficulty": "kolay",
            "question": "Bir kenarı 5 birim olan karenin alanı kaç birim karedir?",
            "answer": "25 birim kare",
            "solution": "Alan = 5 × 5 = 25.",
        },
    ],
    "M.4.4.1": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "4 km 350 m kaç metredir?",
            "answer": "4.350 m",
            "solution": "4 × 1000 + 350 = 4.350.",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Sabah 1.200 m, akşam 2 km 800 m yürüyen biri toplam kaç metre yürümüştür?",
            "answer": "4.000 m",
            "solution": "1.200 + 2.800 = 4.000 m = 4 km.",
        },
    ],
    "M.4.4.2": [
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "orta",
            "question": "1 m² kaç cm²'dir?",
            "answer": "10.000 cm²",
            "solution": "1 m = 100 cm; 1 m² = 100 × 100 = 10.000 cm².",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Bir odanın alanı 24 m²'dir. Bu alan kaç cm²'dir?",
            "answer": "240.000 cm²",
            "solution": "24 × 10.000 = 240.000 cm².",
        },
    ],
    "M.4.5.1": [
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "orta",
            "question": "Örüntü kuralı '3'ten başla, her adımda 4 ekle.' 6. terim kaçtır?",
            "answer": "23",
            "solution": "Terimler: 3, 7, 11, 15, 19, 23.",
        },
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "zor",
            "question": "5, 11, 17, 23, ... örüntüsünde 7. terim kaçtır?",
            "answer": "41",
            "solution": "Altışar artıyor: 5+6=11, 11+6=17,... 7. terim = 5 + 6×6 = 41.",
        },
    ],
    "M.4.5.2": [
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "kolay",
            "question": "8 + ? = 15 eşitliğinde '?' yerine yazılması gereken sayı kaçtır?",
            "answer": "7",
            "solution": "15 − 8 = 7.",
        },
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "orta",
            "question": "12 = ? − 5 eşitliğinde '?' yerine kaç yazılmalıdır?",
            "answer": "17",
            "solution": "? = 12 + 5 = 17.",
        },
    ],
}
