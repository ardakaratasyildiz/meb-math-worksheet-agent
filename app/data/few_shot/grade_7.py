"""7. sınıf few-shot örnek havuzu."""
from app.models.enums import QuestionType

EXAMPLES: dict[str, list[dict]] = {
    "M.7.1.1": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "(−6) × (+4) işleminin sonucu kaçtır?",
            "answer": "−24",
            "solution": "Farklı işaretli iki tam sayının çarpımı negatiftir: 6 × 4 = 24, sonuç −24.",
        },
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "(−5) × (−7) işleminin sonucu kaçtır?",
            "answer": "+35",
            "solution": "Aynı işaretli iki tam sayının çarpımı pozitiftir: 5 × 7 = 35.",
        },
    ],
    "M.7.1.2": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "(−48) ÷ (+6) işleminin sonucu kaçtır?",
            "answer": "−8",
            "solution": "Farklı işaret → sonuç negatif. 48 ÷ 6 = 8.",
        },
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "(−72) ÷ (−9) işleminin sonucu kaçtır?",
            "answer": "+8",
            "solution": "Aynı işaret → sonuç pozitif. 72 ÷ 9 = 8.",
        },
    ],
    "M.7.1.3": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "(−4) × 3 + (−6) ÷ 2 işleminin sonucu kaçtır?",
            "answer": "−15",
            "solution": "Önce çarpma/bölme: −12 ve −3. Sonra toplama: −12 + (−3) = −15.",
        },
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "zor",
            "question": "10 − 2 × (−3) işleminin sonucu kaçtır?",
            "answer": "16",
            "solution": "Önce çarpma: 2 × (−3) = −6. Sonra: 10 − (−6) = 10 + 6 = 16.",
        },
    ],
    "M.7.1.4": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "(−2)⁴ ifadesinin değeri kaçtır?",
            "answer": "16",
            "solution": "Üs çift olduğu için sonuç pozitiftir: 2⁴ = 16.",
        },
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "(−3)³ ifadesinin değeri kaçtır?",
            "answer": "−27",
            "solution": "Üs tek olduğu için sonuç negatiftir: 3³ = 27, sonuç −27.",
        },
    ],
    "M.7.2.1": [
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "kolay",
            "question": "−5/3 sayısı rasyonel sayı mıdır? Açıklayınız.",
            "answer": "Evet",
            "solution": "İki tam sayının (pay = −5, payda = 3) oranı şeklinde yazılabildiği için rasyonel sayıdır.",
        },
        {
            "type": QuestionType.MODELLEME,
            "difficulty": "orta",
            "question": "−1 ile 0 arasında, sayı doğrusunda −1/2'yi gösteriniz.",
            "answer": "−1 ile 0 arasındaki orta nokta",
            "solution": "−1 ile 0 arası ikiye bölünür; orta nokta −1/2'dir.",
        },
    ],
    "M.7.2.2": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "3/4 rasyonel sayısının ondalık gösterimi nedir?",
            "answer": "0,75",
            "solution": "3 ÷ 4 = 0,75.",
        },
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "0,4 ondalık sayısını sadeleştirilmiş kesir olarak yazınız.",
            "answer": "2/5",
            "solution": "0,4 = 4/10 = 2/5.",
        },
    ],
    "M.7.2.3": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "1/2 + (−3/4) işleminin sonucu kaçtır?",
            "answer": "−1/4",
            "solution": "Ortak payda 4: 2/4 + (−3/4) = −1/4.",
        },
        {
            "type": QuestionType.ISLEM,
            "difficulty": "zor",
            "question": "−2/5 − 1/3 işleminin sonucu kaçtır?",
            "answer": "−11/15",
            "solution": "Ortak payda 15: −6/15 − 5/15 = −11/15.",
        },
    ],
    "M.7.2.4": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "(−2/3) × (3/4) işleminin sonucu kaçtır?",
            "answer": "−1/2",
            "solution": "Paylar paylarla, paydalar paydalarla: (−2 × 3) / (3 × 4) = −6/12 = −1/2.",
        },
        {
            "type": QuestionType.ISLEM,
            "difficulty": "zor",
            "question": "(3/5) ÷ (−6/10) işleminin sonucu kaçtır?",
            "answer": "−1",
            "solution": "(3/5) × (10/−6) = 30 / −30 = −1.",
        },
    ],
    "M.7.3.1": [
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "kolay",
            "question": "Çemberin merkezini herhangi bir noktasına bağlayan doğru parçasına ne denir?",
            "answer": "Yarıçap",
            "solution": "Çemberin merkezinden çember üzerindeki bir noktaya çizilen parça yarıçaptır.",
        },
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "kolay",
            "question": "Çemberin merkezinden geçen ve çemberi iki noktada kesen doğru parçasına ne denir?",
            "answer": "Çap",
            "solution": "Merkezden geçen kiriş çaptır ve uzunluğu yarıçapın 2 katıdır.",
        },
    ],
    "M.7.3.2": [
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "kolay",
            "question": "Çember ve daire arasındaki temel fark nedir?",
            "answer": "Çember bir eğri (sınır), daire ise bu eğri ile çevrelenen yüzeydir.",
            "solution": "Çember sadece sınırı, daire sınırı + içini ifade eder.",
        },
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "kolay",
            "question": "Bir pizzanın tamamı çember midir, daire midir?",
            "answer": "Daire",
            "solution": "İçi dolu yüzey daireye karşılık gelir.",
        },
    ],
    "M.7.3.3": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "Yarıçapı 7 cm olan çemberin uzunluğu kaç cm'dir? (π = 22/7 alınız.)",
            "answer": "44 cm",
            "solution": "Çevre = 2πr = 2 × (22/7) × 7 = 44.",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Yarıçapı 10 cm olan dairesel bir tepsinin çevresi kaç cm'dir? (π = 3,14 alınız.)",
            "answer": "62,8 cm",
            "solution": "2 × 3,14 × 10 = 62,8 cm.",
        },
    ],
    "M.7.3.4": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "Yarıçapı 5 cm olan dairenin alanı kaç cm²'dir? (π = 3 alınız.)",
            "answer": "75 cm²",
            "solution": "Alan = πr² = 3 × 25 = 75 cm².",
        },
        {
            "type": QuestionType.GORSEL_GEOMETRI,
            "difficulty": "orta",
            "question": (
                "Aşağıda merkezi O olan ve yarıçapı verilmiş bir daire vardır. "
                "Bu dairenin alanını hesaplayınız. (π = 3 alınız.)\n\n"
                "```\n"
                "       ●───────●\n"
                "      ╱         ╲\n"
                "     ●     O─────● 6 cm\n"
                "      ╲         ╱\n"
                "       ●───────●\n"
                "```"
            ),
            "answer": "108 cm²",
            "solution": "Alan = πr² = 3 × 6² = 3 × 36 = 108 cm².",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Yarıçapı 7 cm olan dairesel bir bölgenin alanı kaç cm²'dir? (π = 22/7 alınız.)",
            "answer": "154 cm²",
            "solution": "(22/7) × 7 × 7 = 22 × 7 = 154.",
        },
    ],
    "M.7.3.5": [
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "orta",
            "question": "Bir dairenin merkez açısı 90° olan dilimi, dairenin kaçta kaçıdır?",
            "answer": "1/4",
            "solution": "Tam açı 360°. 90/360 = 1/4.",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "zor",
            "question": "Alanı 120 cm² olan bir dairenin merkez açısı 60° olan diliminin alanı kaç cm²'dir?",
            "answer": "20 cm²",
            "solution": "60/360 = 1/6. 120 × 1/6 = 20.",
        },
    ],
    "M.7.4.1": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "Bir kenarı 4 cm olan küpün hacmi kaç cm³'tür?",
            "answer": "64 cm³",
            "solution": "Hacim = a³ = 4 × 4 × 4 = 64.",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "kolay",
            "question": "Eni 5 cm, boyu 8 cm, yüksekliği 6 cm olan dikdörtgenler prizmasının hacmi kaç cm³'tür?",
            "answer": "240 cm³",
            "solution": "5 × 8 × 6 = 240.",
        },
    ],
    "M.7.4.2": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "Bir kenarı 3 cm olan küpün yüzey alanı kaç cm²'dir?",
            "answer": "54 cm²",
            "solution": "Yüzey alanı = 6a² = 6 × 9 = 54.",
        },
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "zor",
            "question": "Eni 2 cm, boyu 4 cm, yüksekliği 5 cm olan dikdörtgenler prizmasının yüzey alanı kaç cm²'dir?",
            "answer": "76 cm²",
            "solution": "2(2×4 + 2×5 + 4×5) = 2(8 + 10 + 20) = 2 × 38 = 76.",
        },
    ],
    "M.7.5.1": [
        {
            "type": QuestionType.KAVRAM_SORUSU,
            "difficulty": "kolay",
            "question": "Bir eşitliğin her iki tarafına aynı sayı eklenirse eşitlik bozulur mu?",
            "answer": "Bozulmaz",
            "solution": "Eşitliğin korunumu ilkesine göre her iki tarafa eşit miktar ekleme/çıkarma eşitliği bozmaz.",
        },
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "orta",
            "question": "x + 3 = 8 denkleminde x'i yalnız bırakmak için her iki taraftan kaç çıkarılmalıdır?",
            "answer": "3",
            "solution": "Her iki taraftan 3 çıkarılırsa x = 5 elde edilir.",
        },
    ],
    "M.7.5.2": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "5x − 7 = 18 denkleminin çözümünü yapınız.",
            "answer": "x = 5",
            "solution": "5x = 25 → x = 5.",
        },
        {
            "type": QuestionType.SALT_ISLEM,
            "difficulty": "orta",
            "question": "4x + 9 = 33 → x = ?",
            "answer": "x = 6",
            "solution": "4x = 24 → x = 6.",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Bir sayının 4 katından 6 çıkarıldığında 22 elde edildiğine göre bu sayı kaçtır?",
            "answer": "7",
            "solution": "4x − 6 = 22 → 4x = 28 → x = 7.",
        },
    ],
    "M.7.5.3": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "kolay",
            "question": "x + 4 < 9 eşitsizliğini çözünüz.",
            "answer": "x < 5",
            "solution": "Her iki taraftan 4 çıkarılır: x < 5.",
        },
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "zor",
            "question": "2x − 3 ≥ 7 eşitsizliğini sağlayan en küçük tam sayı kaçtır?",
            "answer": "5",
            "solution": "2x ≥ 10 → x ≥ 5. En küçük tam sayı 5.",
        },
    ],
    "M.7.5.4": [
        {
            "type": QuestionType.GUNLUK_HAYAT,
            "difficulty": "kolay",
            "question": "3 kg elma 60 TL ise 5 kg elma kaç TL'dir?",
            "answer": "100 TL",
            "solution": "3/60 = 5/x → x = (5 × 60)/3 = 100.",
        },
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "Bir araç 4 saatte 320 km yol alıyor. Aynı hızla 7 saatte kaç km yol alır?",
            "answer": "560 km",
            "solution": "Doğru orantı: 4/320 = 7/x → x = (7 × 320)/4 = 560.",
        },
    ],
    "M.7.6.1": [
        {
            "type": QuestionType.SOZEL_PROBLEM,
            "difficulty": "orta",
            "question": "200 kişiyle yapılan bir ankette daire grafiğinde elma %35, armut %25, üzüm %30 olarak gösterilmiştir. Geri kalan kategori 'diğer'dir. Daire grafiğinde 'diğer' kaç kişiye karşılık gelir ve dilim kaç derece olmalıdır?",
            "answer": "20 kişi; 36°",
            "solution": "Diğer yüzdesi: 100 − (35 + 25 + 30) = 10. Kişi sayısı: 200 × 10/100 = 20. Dilim açısı: 360 × 10/100 = 36°.",
        },
        {
            "type": QuestionType.TABLO_SORUSU,
            "difficulty": "orta",
            "question": (
                "Aşağıdaki tabloda 400 öğrenciye yapılan favori spor anketinin "
                "sonuçları yer almaktadır.\n\n"
                "| Spor       | Öğrenci Sayısı |\n"
                "|------------|----------------|\n"
                "| Futbol     | 160            |\n"
                "| Basketbol  | 100            |\n"
                "| Voleybol   | 80             |\n"
                "| Yüzme      | 60             |\n\n"
                "Bu veriler daire grafiğinde gösterildiğinde basketbol dilimi "
                "kaç derece olur?"
            ),
            "answer": "90°",
            "solution": "Basketbolun yüzdesi: 100/400 = 1/4. Daire grafiğinde dilim açısı: 360 × 1/4 = 90°.",
        },
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "zor",
            "question": "Bir okuldaki spor tercihi anketi daire grafiğinde basketbol 108°, futbol 144°, voleybol 72° dilime karşılık geliyor. Toplam 60 öğrenci ankete katıldıysa kalan kategoride kaç öğrenci vardır?",
            "answer": "6 öğrenci",
            "solution": "Kalan açı: 360 − (108 + 144 + 72) = 36°. Öğrenci sayısı: 60 × 36/360 = 6.",
        },
    ],
    "M.7.6.2": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "Bir öğrencinin haftalık deneme sınavı netleri 12, 14, 11, 16, 14, 18, 13'tür. Bu verilerin ortancası ve tepe değeri nedir?",
            "answer": "Ortanca 14, tepe değer 14.",
            "solution": "Sıralı: 11, 12, 13, 14, 14, 16, 18 → orta değer (4. sıra) = 14. En çok tekrar eden değer = 14.",
        },
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "zor",
            "question": "8 öğrencinin matematik notlarının aritmetik ortalaması 75'tir. En düşük notu çıkardıktan sonra ortalama 78'e yükselmiştir. Çıkarılan notun değeri kaçtır?",
            "answer": "54",
            "solution": "İlk toplam: 75 × 8 = 600. Yeni toplam: 78 × 7 = 546. Çıkan not: 600 − 546 = 54.",
        },
    ],
    "M.7.7.1": [
        {
            "type": QuestionType.ISLEM,
            "difficulty": "orta",
            "question": "Bir zar atıldığında üst yüzüne 4'ten büyük bir sayı gelme olasılığını kesir, ondalık ve yüzde olarak ifade ediniz.",
            "answer": "2/6 = 1/3 ≈ 0,33 ≈ %33,33",
            "solution": "4'ten büyük sayılar: 5 ve 6. Toplam sonuç: 6. P = 2/6 = 1/3 ≈ 0,33 ≈ %33,33.",
        },
        {
            "type": QuestionType.AKIL_YURUTME,
            "difficulty": "zor",
            "question": "Bir torbada 5 mavi, 4 kırmızı ve 3 yeşil top vardır. Torbadan rastgele çekilen bir topun mavi VEYA kırmızı olma olasılığı nedir? Sonucu yüzde olarak ifade ediniz.",
            "answer": "9/12 = %75",
            "solution": "Toplam top: 5+4+3 = 12. İstenen olay: 5+4 = 9. P = 9/12 = 0,75 = %75.",
        },
    ],
}
