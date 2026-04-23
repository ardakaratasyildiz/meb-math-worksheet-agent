"""1. sınıf few-shot örnek havuzu."""
from app.models.enums import QuestionType

EXAMPLES: dict[str, list[dict]] = {
    "M.1.1.1": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "0'dan 20'ye kadar ikişer ritmik sayınız.",
            "answer": "0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20",
            "solution": "Her seferinde 2 ekleyerek sayılır.",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "kolay",
            "question": "Sepette 5 elma vardır. Anne 3 elma daha koyarsa sepette kaç elma olur?",
            "answer": "8 elma",
            "solution": "5 + 3 = 8",
        },
    ],
    "M.1.1.2": [
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "kolay",
            "question": "47 sayısının okunuşunu yazınız.",
            "answer": "Kırk yedi",
            "solution": "4 onluk = kırk, 7 birlik = yedi.",
        },
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "'Otuz altı' sayısını rakamla yazınız.",
            "answer": "36",
            "solution": "Otuz = 30, altı = 6, toplam 36.",
        },
    ],
    "M.1.1.3": [
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "kolay",
            "question": "63 sayısı kaç onluk ve kaç birlikten oluşur?",
            "answer": "6 onluk ve 3 birlik",
            "solution": "Onlar basamağı 6, birler basamağı 3.",
        },
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "4 onluk ve 7 birlik kaç eder?",
            "answer": "47",
            "solution": "4 × 10 + 7 = 47",
        },
    ],
    "M.1.1.4": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "8 + 7 işleminin sonucu kaçtır?",
            "answer": "15",
            "solution": "8 + 7 = 15",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Ahmet'in 9 bilyesi var. Babası 6 bilye daha aldı. Toplam kaç bilyesi olmuştur?",
            "answer": "15 bilye",
            "solution": "9 + 6 = 15",
        },
    ],
    "M.1.1.5": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "9 − 4 işleminin sonucu kaçtır?",
            "answer": "5",
            "solution": "9 − 4 = 5",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Ayşe'nin 8 şekeri vardı. 3 tanesini yedi. Geriye kaç şekeri kaldı?",
            "answer": "5 şeker",
            "solution": "8 − 3 = 5",
        },
    ],
    "M.1.3.1": [
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "kolay",
            "question": "4 kenarı eşit olan dörtgen şekli nasıl adlandırılır?",
            "answer": "Kare",
            "solution": "Tüm kenarları eşit dörtgen kare olarak tanımlanır.",
        },
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "kolay",
            "question": "3 kenarı olan şekil nedir?",
            "answer": "Üçgen",
            "solution": "Üç kenarlı çokgene üçgen denir.",
        },
    ],
    "M.1.3.2": [
        {
            "type": QuestionType.GUNLUK_HAYAT,
            "difficulty": "kolay",
            "question": "Tekerlek hangi geometrik şekle benzer?",
            "answer": "Daire",
            "solution": "Yuvarlak ve sınırı eğri olan şekil dairedir.",
        },
        {
            "type": QuestionType.GUNLUK_HAYAT,
            "difficulty": "kolay",
            "question": "Pencere genelde hangi geometrik şekildedir?",
            "answer": "Dikdörtgen",
            "solution": "Karşılıklı kenarları eşit ve dik olan dörtgen dikdörtgendir.",
        },
    ],
    "M.1.4.1": [
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "kolay",
            "question": "Bir kalem 12 cm, bir silgi 4 cm uzunluğundadır. Hangisi daha uzundur?",
            "answer": "Kalem",
            "solution": "12 > 4 olduğundan kalem daha uzundur.",
        },
        {
            "type": QuestionType.GUNLUK_HAYAT,
            "difficulty": "orta",
            "question": "Boyu 1 metre olan bir çocuk ile 50 cm boyundaki bir bebekten hangisi daha uzundur?",
            "answer": "Çocuk",
            "solution": "1 m = 100 cm olduğundan çocuk daha uzundur.",
        },
    ],
    "M.1.4.2": [
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Bir masanın uzunluğu 5 karış, defterin uzunluğu 2 karış ise masa defterden kaç karış daha uzundur?",
            "answer": "3 karış",
            "solution": "5 − 2 = 3 karış.",
        },
        {
            "type": QuestionType.GUNLUK_HAYAT,
            "difficulty": "orta",
            "question": "Sınıfın bir duvarı 8 adımda yürünüyor. Yarıya kadar gidersek kaç adım atmış oluruz?",
            "answer": "4 adım",
            "solution": "8'in yarısı 4'tür.",
        },
    ],
    "M.1.4.3": [
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "kolay",
            "question": "Akrep 3'te, yelkovan 12'deyse saat kaçtır?",
            "answer": "Saat 3",
            "solution": "Yelkovan 12'de iken akrebin gösterdiği rakam tam saati verir.",
        },
        {
            "type": QuestionType.GUNLUK_HAYAT,
            "difficulty": "orta",
            "question": "Bir film saat 5'te başlayıp 7'de bitiyor. Kaç saat sürmüştür?",
            "answer": "2 saat",
            "solution": "7 − 5 = 2 saat.",
        },
    ],
    "M.1.5.1": [
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "kolay",
            "question": "2, 4, 6, 8, ? Örüntüsünde sıradaki sayı kaçtır?",
            "answer": "10",
            "solution": "Her sayı bir öncekinden 2 fazladır: 8 + 2 = 10.",
        },
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "kolay",
            "question": "1, 3, 5, 7, ? Örüntüsünde sıradaki sayı kaçtır?",
            "answer": "9",
            "solution": "Her sayı 2 artıyor: 7 + 2 = 9.",
        },
    ],
    "M.1.5.2": [
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "orta",
            "question": "5, 10, ?, 20, 25 örüntüsündeki eksik sayı kaçtır?",
            "answer": "15",
            "solution": "Beşer artan örüntü: 10 + 5 = 15.",
        },
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "orta",
            "question": "3, ?, 9, 12, 15 örüntüsündeki eksik sayı kaçtır?",
            "answer": "6",
            "solution": "Üçer artıyor: 3 + 3 = 6.",
        },
    ],
}
