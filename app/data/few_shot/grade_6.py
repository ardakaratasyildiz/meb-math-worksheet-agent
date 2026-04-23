"""6. sınıf few-shot örnek havuzu."""
from app.models.enums import QuestionType

EXAMPLES: dict[str, list[dict]] = {
    "M.6.1.1": [
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "kolay",
            "question": "−5, 0 ve +3 sayılarını sayı doğrusunda hangi sıraya göre yazarsınız?",
            "answer": "−5, 0, +3",
            "solution": "Negatif sayılar 0'ın solunda, pozitifler sağındadır.",
        },
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "kolay",
            "question": "Sıfırdan küçük tam sayıların ortak adı nedir?",
            "answer": "Negatif tam sayılar",
            "solution": "Sıfırın solundaki tam sayılar negatiftir.",
        },
    ],
    "M.6.1.2": [
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "kolay",
            "question": "|−12| ifadesinin değeri kaçtır?",
            "answer": "12",
            "solution": "Mutlak değer, sayının işaretine bakmaksızın uzaklığıdır.",
        },
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "zor",
            "question": "|x| = 7 ise x'in alabileceği değerler nelerdir?",
            "answer": "x = 7 veya x = −7",
            "solution": "Mutlak değeri 7 olan iki sayı vardır: +7 ve −7.",
        },
    ],
    "M.6.1.3": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "(−8) + (+5) işleminin sonucu kaçtır?",
            "answer": "−3",
            "solution": "Farklı işaretli sayılarda mutlak değerler farkı alınır, büyük olanın işareti yazılır.",
        },
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "(−6) − (−9) işleminin sonucu kaçtır?",
            "answer": "+3",
            "solution": "(−6) − (−9) = (−6) + (+9) = +3.",
        },
    ],
    "M.6.1.4": [
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "orta",
            "question": "−7, +2, −3, 0 sayılarını küçükten büyüğe sıralayınız.",
            "answer": "−7 < −3 < 0 < +2",
            "solution": "Negatiflerde mutlak değer büyüdükçe sayı küçülür.",
        },
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "zor",
            "question": "−5 ile +4 arasında kaç tane tam sayı vardır?",
            "answer": "8",
            "solution": "Aradaki tam sayılar: −4, −3, −2, −1, 0, +1, +2, +3 → 8 adet.",
        },
    ],
    "M.6.2.1": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "2/3 + 1/4 işleminin sonucu kaçtır?",
            "answer": "11/12",
            "solution": "Ortak payda 12: 8/12 + 3/12 = 11/12.",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Bir bahçenin 1/4'ü çiçek, 2/5'i sebzedir. Toplam ne kadarlık bölüm bunlara ayrılmıştır?",
            "answer": "13/20",
            "solution": "Ortak payda 20: 5/20 + 8/20 = 13/20.",
        },
    ],
    "M.6.2.2": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "2/3 × 4/5 işleminin sonucu kaçtır?",
            "answer": "8/15",
            "solution": "Paylar paylarla, paydalar paydalarla çarpılır: 2×4 / 3×5 = 8/15.",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "12 kg unun 3/4'ü kullanıldıysa kaç kg un kullanılmıştır?",
            "answer": "9 kg",
            "solution": "12 × 3/4 = 9 kg.",
        },
    ],
    "M.6.2.3": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "3/4 ÷ 1/2 işleminin sonucu kaçtır?",
            "answer": "3/2 (1 tam 1/2)",
            "solution": "Bölme bölenin tersiyle çarpmaya eşittir: 3/4 × 2/1 = 6/4 = 3/2.",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "5 metre kumaştan her biri 1/2 metre olan kaç parça kesilebilir?",
            "answer": "10 parça",
            "solution": "5 ÷ 1/2 = 5 × 2 = 10.",
        },
    ],
    "M.6.2.4": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "3,45 + 2,8 işleminin sonucu kaçtır?",
            "answer": "6,25",
            "solution": "Virgüller alt alta gelecek şekilde toplanır: 3,45 + 2,80 = 6,25.",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "1 kg portakal 24,50 TL ise 3 kg portakal kaç TL'dir?",
            "answer": "73,50 TL",
            "solution": "24,50 × 3 = 73,50 TL.",
        },
    ],
    "M.6.3.1": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "Tabanı 8 cm, yüksekliği 5 cm olan paralelkenarın alanı kaç cm²'dir?",
            "answer": "40 cm²",
            "solution": "Alan = taban × yükseklik = 8 × 5 = 40.",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Alanı 96 cm² olan paralelkenarın tabanı 12 cm ise yüksekliği kaç cm'dir?",
            "answer": "8 cm",
            "solution": "Yükseklik = Alan / Taban = 96 / 12 = 8.",
        },
    ],
    "M.6.3.2": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "Tabanı 10 cm, yüksekliği 6 cm olan üçgenin alanı kaç cm²'dir?",
            "answer": "30 cm²",
            "solution": "Üçgen alanı = (taban × yükseklik) / 2 = (10 × 6) / 2 = 30.",
        },
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "zor",
            "question": "Alanı 24 cm² olan bir üçgenin yüksekliği 8 cm ise tabanı kaç cm'dir?",
            "answer": "6 cm",
            "solution": "(taban × 8) / 2 = 24 → taban × 8 = 48 → taban = 6.",
        },
    ],
    "M.6.3.3": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "Paralel kenarları 6 cm ve 10 cm, yüksekliği 4 cm olan yamuğun alanı kaç cm²'dir?",
            "answer": "32 cm²",
            "solution": "Yamuk alanı = (a + c) × h / 2 = (6 + 10) × 4 / 2 = 64 / 2 = 32.",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Yamuk şeklinde bir bahçenin paralel kenarları 12 m ve 18 m, yüksekliği 10 m'dir. Alanı kaç m²'dir?",
            "answer": "150 m²",
            "solution": "(12 + 18) × 10 / 2 = 300 / 2 = 150.",
        },
    ],
    "M.6.4.1": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "2,5 L kaç mL'dir?",
            "answer": "2.500 mL",
            "solution": "1 L = 1000 mL. 2,5 × 1000 = 2.500.",
        },
        {
            "type": QuestionType.GUNLUK_HAYAT,
            "difficulty": "orta",
            "question": "750 mL'lik bir şişeden 4 tane içildi. Toplam kaç litre içilmiştir?",
            "answer": "3 L",
            "solution": "750 × 4 = 3.000 mL = 3 L.",
        },
    ],
    "M.6.4.2": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "Eni 4 cm, boyu 5 cm, yüksekliği 3 cm olan dikdörtgenler prizmasının hacmi kaç cm³'tür?",
            "answer": "60 cm³",
            "solution": "Hacim = en × boy × yükseklik = 4 × 5 × 3 = 60.",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Bir akvaryumun tabanı 30 cm × 20 cm, yüksekliği 25 cm. Akvaryum tam dolduğunda kaç cm³ su alır?",
            "answer": "15.000 cm³",
            "solution": "30 × 20 × 25 = 15.000.",
        },
    ],
    "M.6.5.1": [
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "kolay",
            "question": "x = 4 için 3x + 5 ifadesinin değeri kaçtır?",
            "answer": "17",
            "solution": "3 × 4 + 5 = 12 + 5 = 17.",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "kolay",
            "question": "Bir kalemin fiyatı x TL ise 5 kalemin fiyatını cebirsel ifade ile yazınız.",
            "answer": "5x TL",
            "solution": "5 kalem için 5 × x = 5x.",
        },
    ],
    "M.6.5.2": [
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Bir sayının 3 katının 5 fazlası 26'dır. Bu durumu cebirsel denklem olarak yazınız.",
            "answer": "3x + 5 = 26",
            "solution": "Sayıya x deyince: '3 katı' 3x, '5 fazlası' +5, 'eşit 26' = 26.",
        },
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "zor",
            "question": "Bir defter ile bir kitap toplam 60 TL. Kitap defterden 20 TL pahalı. Defter fiyatı d ise denklemi kurunuz.",
            "answer": "d + (d + 20) = 60",
            "solution": "Kitap: d + 20. Toplam: d + (d + 20) = 60.",
        },
    ],
    "M.6.5.3": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "3x + 5 = 26 denkleminin çözümünü yapınız.",
            "answer": "x = 7",
            "solution": "3x = 21 → x = 7.",
        },
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "2x − 9 = 11 denkleminin çözümünü yapınız.",
            "answer": "x = 10",
            "solution": "2x = 20 → x = 10.",
        },
    ],
}
