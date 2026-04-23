"""2. sınıf few-shot örnek havuzu."""
from app.models.enums import QuestionType

EXAMPLES: dict[str, list[dict]] = {
    "M.2.1.1": [
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "kolay",
            "question": "385 sayısının okunuşunu yazınız.",
            "answer": "Üç yüz seksen beş",
            "solution": "3 yüzlük, 8 onluk, 5 birlikten oluşur.",
        },
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "'Yedi yüz on iki' sayısını rakamla yazınız.",
            "answer": "712",
            "solution": "Yedi yüz = 700, on iki = 12, toplam 712.",
        },
    ],
    "M.2.1.2": [
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "orta",
            "question": "548 sayısında 5 rakamının basamak değeri kaçtır?",
            "answer": "500",
            "solution": "5 rakamı yüzler basamağındadır: 5 × 100 = 500.",
        },
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "6 yüzlük + 3 onluk + 9 birlik kaç eder?",
            "answer": "639",
            "solution": "600 + 30 + 9 = 639.",
        },
    ],
    "M.2.1.3": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "47 + 35 işleminin sonucu kaçtır?",
            "answer": "82",
            "solution": "47 + 35 = 82",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Bir sınıfta 28 kız ve 24 erkek öğrenci vardır. Toplam kaç öğrenci vardır?",
            "answer": "52 öğrenci",
            "solution": "28 + 24 = 52",
        },
    ],
    "M.2.1.4": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "85 − 47 işleminin sonucu kaçtır?",
            "answer": "38",
            "solution": "85 − 47 = 38",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Bir kütüphanede 95 kitap vardır. 38 tanesi okuyuculara verildi. Geriye kaç kitap kaldı?",
            "answer": "57 kitap",
            "solution": "95 − 38 = 57",
        },
    ],
    "M.2.1.5": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "4 × 5 işleminin sonucu kaçtır?",
            "answer": "20",
            "solution": "4 + 4 + 4 + 4 + 4 = 20 (veya 4 × 5 = 20).",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Bir kutuda 5 kalem var. 3 kutuda toplam kaç kalem vardır?",
            "answer": "15 kalem",
            "solution": "3 × 5 = 15",
        },
    ],
    "M.2.3.1": [
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "kolay",
            "question": "Üçgenin kaç kenarı ve kaç köşesi vardır?",
            "answer": "3 kenar ve 3 köşe",
            "solution": "Üçgenin tanım gereği 3 kenarı ve 3 köşesi vardır.",
        },
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "kolay",
            "question": "Karenin kaç kenarı ve köşesi vardır?",
            "answer": "4 kenar ve 4 köşe",
            "solution": "Karede dört eşit kenar ve dört köşe bulunur.",
        },
    ],
    "M.2.3.2": [
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "kolay",
            "question": "Karenin kenarları için ne söyleyebiliriz?",
            "answer": "Dört kenarı da birbirine eşittir.",
            "solution": "Karenin tanımı: tüm kenarları eşit dörtgen.",
        },
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "kolay",
            "question": "Dikdörtgenin karşılıklı kenarları için ne söylenebilir?",
            "answer": "Karşılıklı kenarları birbirine eşittir.",
            "solution": "Dikdörtgende karşılıklı iki kenar uzunluğu eşittir.",
        },
    ],
    "M.2.4.1": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "3 m kaç cm'dir?",
            "answer": "300 cm",
            "solution": "1 m = 100 cm. 3 × 100 = 300 cm.",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Bir ip 2 m 50 cm uzunluğundadır. Bu ip kaç cm'dir?",
            "answer": "250 cm",
            "solution": "2 × 100 + 50 = 250 cm.",
        },
    ],
    "M.2.4.2": [
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "orta",
            "question": "Akrep 4'te, yelkovan 6'da ise saat kaçtır?",
            "answer": "Saat 4'i 30 geçiyor (yarım)",
            "solution": "Yelkovan 6'ya geldiğinde tam yarım saati gösterir.",
        },
        {
            "type": QuestionType.GUNLUK_HAYAT,
            "difficulty": "zor",
            "question": "Saat 9'a çeyrek kala ne demektir?",
            "answer": "8:45",
            "solution": "9'a 15 dakika kalmış: 9 − 0:15 = 8:45.",
        },
    ],
    "M.2.4.3": [
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "kolay",
            "question": "Ayşe 3 kg elma ve 2 kg portakal aldı. Toplam kaç kg meyve aldı?",
            "answer": "5 kg",
            "solution": "3 + 2 = 5 kg.",
        },
        {
            "type": QuestionType.GUNLUK_HAYAT,
            "difficulty": "orta",
            "question": "Bir karpuz 8 kg, bir kavun 3 kg. Karpuz kavundan kaç kg ağırdır?",
            "answer": "5 kg",
            "solution": "8 − 3 = 5 kg.",
        },
    ],
    "M.2.5.1": [
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "kolay",
            "question": "5, 10, 15, 20, ? Örüntüsünde sıradaki sayı kaçtır?",
            "answer": "25",
            "solution": "Beşer artıyor: 20 + 5 = 25.",
        },
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "orta",
            "question": "1, 4, 7, 10, ? Örüntüsünde sıradaki sayı kaçtır?",
            "answer": "13",
            "solution": "Üçer artıyor: 10 + 3 = 13.",
        },
    ],
    "M.2.5.2": [
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "orta",
            "question": "10, 20, ?, 40, 50 örüntüsündeki eksik sayı kaçtır?",
            "answer": "30",
            "solution": "Onar artan örüntü: 20 + 10 = 30.",
        },
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "orta",
            "question": "△, ○, △, ○, ? örüntüsünde sıradaki şekil hangisidir?",
            "answer": "△",
            "solution": "Üçgen ve daire dönüşümlü; sırada üçgen gelir.",
        },
    ],
}
