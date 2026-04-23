"""3. sınıf few-shot örnek havuzu."""
from app.models.enums import QuestionType

EXAMPLES: dict[str, list[dict]] = {
    "M.3.1.1": [
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "orta",
            "question": "4.587 sayısında 5 rakamının basamak değeri kaçtır?",
            "answer": "500",
            "solution": "5 yüzler basamağında: 5 × 100 = 500.",
        },
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "'Üç bin yüz yirmi' sayısını rakamla yazınız.",
            "answer": "3.120",
            "solution": "3.000 + 100 + 20 = 3.120.",
        },
    ],
    "M.3.1.2": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "1.456 + 2.378 işleminin sonucu kaçtır?",
            "answer": "3.834",
            "solution": "1.456 + 2.378 = 3.834",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Bir okulda 1.245 erkek ve 1.378 kız öğrenci vardır. Toplam öğrenci sayısı kaçtır?",
            "answer": "2.623 öğrenci",
            "solution": "1.245 + 1.378 = 2.623",
        },
    ],
    "M.3.1.3": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "5.812 − 2.479 işleminin sonucu kaçtır?",
            "answer": "3.333",
            "solution": "5.812 − 2.479 = 3.333",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Bir bahçede 4.500 ağaç vardı. 1.250 ağaç söküldü. Geriye kaç ağaç kaldı?",
            "answer": "3.250 ağaç",
            "solution": "4.500 − 1.250 = 3.250",
        },
    ],
    "M.3.1.4": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "23 × 12 işleminin sonucu kaçtır?",
            "answer": "276",
            "solution": "23 × 12 = 23 × 10 + 23 × 2 = 230 + 46 = 276.",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Bir kutuda 24 boya kalemi var. 15 kutuda toplam kaç kalem vardır?",
            "answer": "360 kalem",
            "solution": "24 × 15 = 360",
        },
    ],
    "M.3.1.5": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "84 ÷ 4 işleminin sonucu kaçtır?",
            "answer": "21",
            "solution": "84 ÷ 4 = 21.",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "kolay",
            "question": "96 cevizi 8 çocuğa eşit paylaştırırsak her çocuğa kaç ceviz düşer?",
            "answer": "12 ceviz",
            "solution": "96 ÷ 8 = 12.",
        },
    ],
    "M.3.2.1": [
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "kolay",
            "question": "Bir bütünün yarısı hangi kesirle gösterilir?",
            "answer": "1/2",
            "solution": "Bütün iki eşit parçaya bölünürse her parça 1/2'dir.",
        },
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "kolay",
            "question": "Bir bütünün çeyreği hangi kesirle gösterilir?",
            "answer": "1/4",
            "solution": "Bütün dört eşit parçaya bölünürse her parça 1/4'tür.",
        },
    ],
    "M.3.2.2": [
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Bir pizza 8 eşit dilime bölündü. 3 dilim yenildiyse pizzanın kaçta kaçı yenmiştir?",
            "answer": "3/8",
            "solution": "Bütün 8 parça, yenen 3 parça → 3/8.",
        },
        {
            "type": QuestionType.MODELLEME,
            "difficulty": "kolay",
            "question": "Bir çikolatayı 6 eşit parçaya ayırırsak her parça kaçta kaçtır?",
            "answer": "1/6",
            "solution": "Bütün 6 eşit parçaya bölünürse her parça 1/6'dır.",
        },
    ],
    "M.3.2.3": [
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "kolay",
            "question": "5/9 kesrinde pay ve payda hangileridir?",
            "answer": "Pay: 5, Payda: 9",
            "solution": "Üstteki sayı pay, alttaki sayı paydadır.",
        },
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "Payı 3, paydası 7 olan kesri yazınız.",
            "answer": "3/7",
            "solution": "Pay üste, payda alta yazılır: 3/7.",
        },
    ],
    "M.3.3.1": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "Bir kenarı 6 cm olan karenin çevresi kaç cm'dir?",
            "answer": "24 cm",
            "solution": "Çevre = 4 × 6 = 24 cm.",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Eni 5 cm, boyu 9 cm olan dikdörtgenin çevresi kaç cm'dir?",
            "answer": "28 cm",
            "solution": "Çevre = 2 × (5 + 9) = 28 cm.",
        },
    ],
    "M.3.3.2": [
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "orta",
            "question": "Karenin kaç simetri ekseni vardır?",
            "answer": "4",
            "solution": "Karenin iki köşegen ve iki kenar orta dikme olmak üzere 4 simetri ekseni vardır.",
        },
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "orta",
            "question": "Eşkenar üçgenin kaç simetri ekseni vardır?",
            "answer": "3",
            "solution": "Her köşeden karşı kenara çizilen üç doğru eşkenar üçgenin simetri eksenleridir.",
        },
    ],
    "M.3.4.1": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "5 km kaç metredir?",
            "answer": "5.000 m",
            "solution": "1 km = 1000 m. 5 × 1000 = 5.000 m.",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Bir koşucu 2 km 350 m koşmuştur. Bu mesafe kaç metredir?",
            "answer": "2.350 m",
            "solution": "2 × 1000 + 350 = 2.350 m.",
        },
    ],
    "M.3.4.2": [
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Bir ders 40 dakika sürmektedir. 3 ders toplam kaç dakika eder?",
            "answer": "120 dakika (2 saat)",
            "solution": "3 × 40 = 120 dakika = 2 saat.",
        },
        {
            "type": QuestionType.GUNLUK_HAYAT,
            "difficulty": "zor",
            "question": "Saat 14:25'te başlayan bir film 1 saat 30 dakika sürerse saat kaçta biter?",
            "answer": "15:55",
            "solution": "14:25 + 1:30 = 15:55.",
        },
    ],
    "M.3.5.1": [
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "orta",
            "question": "3, 6, 9, 12, ? Örüntüsünde kural nedir ve sıradaki sayı kaçtır?",
            "answer": "Kural: üçer artar; sıradaki sayı 15.",
            "solution": "Her sayı bir öncekinden 3 fazla. 12 + 3 = 15.",
        },
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "kolay",
            "question": "100, 90, 80, 70, ? Örüntüsünde sıradaki sayı kaçtır?",
            "answer": "60",
            "solution": "Onar azalan örüntü: 70 − 10 = 60.",
        },
    ],
    "M.3.5.2": [
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "orta",
            "question": "Kural 'her seferinde 4 ekle' olan, 7'den başlayan örüntünün ilk 5 terimini yazınız.",
            "answer": "7, 11, 15, 19, 23",
            "solution": "7'ye 4 eklenerek devam edilir.",
        },
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "kolay",
            "question": "Kural 'ikişer azalt' olan, 20'den başlayan örüntünün ilk 4 terimini yazınız.",
            "answer": "20, 18, 16, 14",
            "solution": "20'den başlayıp her seferinde 2 azaltılır.",
        },
    ],
}
