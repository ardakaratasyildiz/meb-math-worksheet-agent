"""İngilizce few-shot havuzu — sınıf → kazanım kodu → örnekler.

Kaynak: resmî MEB/EBA örnek soruları (knowledge_base/Ingilizce/ornek_sorular/).
Sorular metin çıkarımıyla (PyMuPDF) alındı. Çözümler burada elle yazıldı (kaynak
çözüm içermiyor). Fen/Türkçe desenini izler (bkz. app/subjects/fen/few_shot.py):
sınıf → **kazanım kodu** → örnek listesi; şıklar `question` metnine gömülü,
`answer` = doğru şık harfi, `solution` Türkçe (Türk öğrenciye gösterilir).

⚠️ CEVAP DOĞRULAMA — kaynaklar arasında fark var:
  • 8. sınıf: `ornek_sorular/8.sinif/cevap_anahtari.pdf` (resmî `ing_ca.pdf`) ile
    her cevap **birebir doğrulandı** (kaynak: soru no → şık). En güvenilir set.
  • 5/6/7. sınıf: EBA ünite örnek sorularının **ayrı resmî cevap anahtarı repoda
    yok** (SOURCES.md §5.3). Bu yüzden buraya YALNIZCA cevabı metinden kesin
    türetilen (dil bilgisi zorunluluğu, açık bilgi, tek mantıklı seçenek) sorular
    alındı; çözümde gerekçe verildi. Yoruma açık/çeldiricisi tartışmalı sorular ve
    QR-kilitli beceri kitapçıkları (sorular/) alınmadı.

⚠️ KAPSAM: yalnız GÖRSELSİZ (tam metin) sorular alındı — afiş/tablo/grafik/görsel-şık
gerektiren sorular atlandı (few-shot metin akışını bozar; İngilizce'de görsel-realia
soruları sık). Metinsel tablo/kart içeren birkaç soru, tablo düz metne dönüştüğü
için tutuldu.

⚠️ KAZANIM ETİKETİ ELLE — EBA ünite kitapçıklarının teması ile 2024 TYMM ünite
kodları birebir örtüşmez (crosswalk; Fen'deki EBA↔TYMM sorunuyla aynı). Her soru
İÇERİĞİNE göre en yakın TYMM temasının kazanım koduna (ENG.<sınıf>.<ünite>.<beceri>)
eşlendi. Beceri son eki: R = reading (okuma), V = vocabulary (söz varlığı),
G = grammar/functional language (dil bilgisi/işlevsel dil).

Yapı: dict[grade][kazanim_kod] -> [{type, difficulty, source, question, answer, solution}].
"""
from __future__ import annotations

from app.models.enums import QuestionType

_SRC8 = "MEB ÖDSGM 8. Sınıf İngilizce Ünitelendirilmiş Örnek Sorular (cevap anahtarlı)"
_SRC5 = "MEB/EBA 5. Sınıf İngilizce ünite örnek soruları (cevap metin-içi doğrulandı)"
_SRC6 = "MEB/EBA 6. Sınıf İngilizce ünite örnek soruları (cevap metin-içi doğrulandı)"
_SRC7 = "MEB/EBA 7. Sınıf İngilizce ünite örnek soruları (cevap metin-içi doğrulandı)"

# sınıf → kazanım kodu → örnek listesi
ING_EXAMPLES: dict[int, dict[str, list[dict]]] = {
    # ═══════════════════════════════════════════════════════════════════════
    # 5. SINIF — greetings/school & daily routines (cevap metinden zorunlu)
    # ═══════════════════════════════════════════════════════════════════════
    5: {
        # ── Ünite 1: School life / greetings, countries, nationalities ──────
        "ENG.5.1.G1": [
            {
                "type": QuestionType.BOSLUK_DOLDURMA,
                "difficulty": "kolay",
                "source": _SRC5,
                "question": (
                    "David is from - - - -. He is - - - -.\n\n"
                    "A) French / France\n"
                    "B) British / Britain\n"
                    "C) Spain / Spanish\n"
                    "D) Chinese / China"
                ),
                "answer": "C",
                "solution": (
                    "İlk boşluk ülke (from + ülke), ikinci boşluk uyruk (He is + uyruk) "
                    "ister. Yalnız C doğru eşleşir: 'from Spain' (ülke) ve 'He is Spanish' "
                    "(uyruk). Diğer şıklarda ülke/uyruk yer değiştirmiş. Doğru cevap C."
                ),
            },
            {
                "type": QuestionType.DIYALOG_TAMAMLAMA,
                "difficulty": "kolay",
                "source": _SRC5,
                "question": (
                    "Maria : - - - -?\n"
                    "Brad  : Brad Mc Carty.\n\n"
                    "A) What is your name\n"
                    "B) Where are you from\n"
                    "C) What do you like\n"
                    "D) How old are you"
                ),
                "answer": "A",
                "solution": (
                    "Brad'in cevabı bir ad-soyad ('Brad Mc Carty') olduğu için soru adı "
                    "sormalıdır. 'What is your name?' bu cevabı gerektirir. B ülke, C hoşlanılan "
                    "şey, D yaş sorar. Doğru cevap A."
                ),
            },
            {
                "type": QuestionType.SIRALAMA,
                "difficulty": "orta",
                "source": _SRC5,
                "question": (
                    "I.   Nice to meet you.\n"
                    "II.  Nice to meet you, too.\n"
                    "III. Hello, I'm Grace.\n"
                    "IV.  Hi, my name is Mark.\n"
                    "Which of the following is the correct order of the sentences above?\n\n"
                    "A) III - IV - I - II\n"
                    "B) IV - I - II - III\n"
                    "C) I - II - III - IV\n"
                    "D) II - III - IV - I"
                ),
                "answer": "A",
                "solution": (
                    "Tanışma diyaloğu önce iki kişinin kendini tanıtmasıyla başlar "
                    "(III 'Hello, I'm Grace' → IV 'Hi, my name is Mark'), sonra tanışma "
                    "kalıbıyla karşılıklı devam eder (I 'Nice to meet you' → II 'Nice to "
                    "meet you, too'): III-IV-I-II. Doğru cevap A."
                ),
            },
        ],
        "ENG.5.1.R3": [
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "orta",
                "source": _SRC5,
                "question": (
                    "Clara is from England. She speaks English, Spanish and French. At "
                    "school, she loves art class most.\n"
                    "Which of the following does NOT have an answer in the text above?\n\n"
                    "A) Where is she from?\n"
                    "B) What is her favorite class?\n"
                    "C) How many languages can she speak?\n"
                    "D) How many classes does she have every day?"
                ),
                "answer": "D",
                "solution": (
                    "Metin nereli olduğunu (England → A), en sevdiği dersi (art → B) ve kaç "
                    "dil bildiğini (üç dil → C) veriyor. Ancak her gün kaç dersi olduğuna "
                    "dair bilgi YOK. Doğru cevap D."
                ),
            },
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "kolay",
                "source": _SRC5,
                "question": (
                    "Hello! My name is Billy. I'm ten years old. I'm British. I speak "
                    "English and Spanish.\n"
                    "Billy does NOT tell about his - - - -.\n\n"
                    "A) age\n"
                    "B) nationality\n"
                    "C) languages\n"
                    "D) favourite lesson"
                ),
                "answer": "D",
                "solution": (
                    "Billy yaşını (ten → A), uyruğunu (British → B) ve konuştuğu dilleri "
                    "(English, Spanish → C) söylüyor. En sevdiği dersten hiç söz etmiyor. "
                    "Doğru cevap D."
                ),
            },
        ],
        # ── Ünite 2: Classroom life / school subjects & timetables ──────────
        "ENG.5.2.V1": [
            {
                "type": QuestionType.KELIME_BILGISI,
                "difficulty": "orta",
                "source": _SRC5,
                "question": (
                    "Tim    : I like drawing pictures.\n"
                    "Amy    : I love doing sports.\n"
                    "Samuel : I really like solving problems.\n"
                    "Betty  : I enjoy doing experiments.\n"
                    "Whose favourite lesson is maths?\n\n"
                    "A) Tim's\nB) Amy's\nC) Samuel's\nD) Betty's"
                ),
                "answer": "C",
                "solution": (
                    "Matematik dersi 'solving problems' (problem çözme) ile ilişkilidir. "
                    "Bunu söyleyen Samuel'dir. Tim resim (art), Amy spor (P.E.), Betty deney "
                    "(science) sever. Doğru cevap C."
                ),
            },
        ],
        "ENG.5.2.G1": [
            {
                "type": QuestionType.BOSLUK_DOLDURMA,
                "difficulty": "kolay",
                "source": _SRC5,
                "question": (
                    "My best friend, Harry, - - - - maths because he is bad at solving "
                    "problems.\n"
                    "Which one completes the statement above?\n\n"
                    "A) dislikes\nB) enjoys\nC) likes\nD) loves"
                ),
                "answer": "A",
                "solution": (
                    "'because he is bad at solving problems' (problem çözmede kötü olduğu "
                    "için) olumsuz bir gerekçedir; bu yüzden fiil de olumsuz duygu bildirmeli: "
                    "'dislikes' (sevmez). B/C/D olumlu duygu bildirir, gerekçeyle çelişir. "
                    "Doğru cevap A."
                ),
            },
        ],
        # ── Ünite 3: Personal life / daily routines and activities ──────────
        "ENG.5.3.R3": [
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "orta",
                "source": _SRC5,
                "question": (
                    "Selena is my best friend. She gets up early in the mornings. After "
                    "breakfast, she walks to school. She has lunch at the school canteen. Her "
                    "lessons finish at half past three. After school, we go to the park to "
                    "play basketball.\n"
                    "According to the text, where does Selena do sports?\n\n"
                    "A) At the school canteen\n"
                    "B) At half past three\n"
                    "C) At the park\n"
                    "D) At home"
                ),
                "answer": "C",
                "solution": (
                    "Metinde spor (basketbol) 'we go to the park to play basketball' cümlesiyle "
                    "parkta yapılır. A kantin (öğle yemeği), B bir saat, D ev — hiçbiri sporla "
                    "ilgili yer değil. Doğru cevap C."
                ),
            },
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "orta",
                "source": _SRC5,
                "question": (
                    "Hi! My name is Mike. I wake up at seven o'clock on weekdays. I have "
                    "breakfast with my family. I go to school at quarter to eight. My lessons "
                    "start at eight o'clock. I have lunch at the school canteen. After school, "
                    "I arrive home at half past two. I play football with my friends. I do my "
                    "homework at five o'clock. In the evenings, I watch TV with my family and "
                    "read books.\n"
                    "Mike - - - - before doing his homework.\n\n"
                    "A) plays football with his friends\n"
                    "B) watches TV with his family\n"
                    "C) reads books\n"
                    "D) goes to bed early"
                ),
                "answer": "A",
                "solution": (
                    "Metnin sırasına göre Mike okuldan sonra futbol oynar ('play football'), "
                    "sonra saat beşte ödevini yapar ('do my homework at five'). Yani ödevden "
                    "ÖNCE futbol oynar. TV izleme ve kitap okuma akşam, ödevden sonradır. "
                    "Doğru cevap A."
                ),
            },
        ],
        "ENG.5.3.G1": [
            {
                "type": QuestionType.DIYALOG_TAMAMLAMA,
                "difficulty": "kolay",
                "source": _SRC5,
                "question": (
                    "Jane : Do you have a plan after school?\n"
                    "Mary : No, not really.\n"
                    "Jane : There is a movie on TV. Let's watch it together.\n"
                    "Mary : - - - -?\n"
                    "Jane : At nine.\n"
                    "Which of the following completes the conversation above?\n\n"
                    "A) What time does it start\n"
                    "B) What do they do after school\n"
                    "C) Where does the movie on\n"
                    "D) What time do you go to the theatre"
                ),
                "answer": "A",
                "solution": (
                    "Jane'in yanıtı bir saat: 'At nine'. Bu yanıt yalnızca bir zaman sorusuna "
                    "('What time does it start?' = film ne zaman başlar) uyar. B/C/D bu yanıtı "
                    "gerektirmez. Doğru cevap A."
                ),
            },
        ],
    },
    # ═══════════════════════════════════════════════════════════════════════
    # 6. SINIF — daily & study routines (cevap metinden zorunlu)
    # ═══════════════════════════════════════════════════════════════════════
    6: {
        # ── Ünite 2: Classroom life with daily and study routines ───────────
        "ENG.6.2.R3": [
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "orta",
                "source": _SRC6,
                "question": (
                    "George gets up at 6:30 a.m. and gets ready for school. His morning "
                    "routine: he washes his face at 6:35, has breakfast at 6:50, brushes his "
                    "teeth at 7:15, makes his bed at 7:25, gets dressed at 7:30.\n"
                    "According to the information above, George - - - -.\n\n"
                    "A) has breakfast after he makes his bed\n"
                    "B) washes his face after he has breakfast\n"
                    "C) brushes his teeth before he makes his bed\n"
                    "D) gets dressed before he washes his face"
                ),
                "answer": "C",
                "solution": (
                    "Saatlere göre diş fırçalama (7:15) yatak yapmadan (7:25) ÖNCEdir → C "
                    "doğru. A yanlış (kahvaltı 6:50, yatak 7:25); B yanlış (yüz 6:35, kahvaltı "
                    "6:50); D yanlış (giyinme 7:30, yüz 6:35). Doğru cevap C."
                ),
            },
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "kolay",
                "source": _SRC6,
                "question": (
                    "(I) I always get up at 7:00 a.m. on weekdays. (II) At first, I take a "
                    "nap. (III) Then, I wash my face and have breakfast. (IV) I go to school "
                    "at half past seven.\n"
                    "Choose the irrelevant sentence in the text above.\n\n"
                    "A) I\nB) II\nC) III\nD) IV"
                ),
                "answer": "B",
                "solution": (
                    "Metin sabah uyanma rutinini anlatıyor. 'take a nap' (kısa uyku/şekerleme) "
                    "sabah kalkış rutinine ters düşer — uykuya yeni uyanan biri şekerleme "
                    "yapmaz. Bu yüzden II ilgisizdir. Doğru cevap B."
                ),
            },
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "orta",
                "source": _SRC6,
                "question": (
                    "Paul is 12 years old. He is a student in the sixth grade. He gets up at "
                    "6:45 a.m. He has a big breakfast at 7 o'clock. He brushes his teeth and "
                    "gets dressed at 7:30 a.m. He goes to school at 7:45 a.m. His lessons start "
                    "at 8:30 a.m. He comes back home at 4:00 p.m. and has a rest. In the "
                    "evening, he has dinner at 7:30 p.m., then he does his homework. He goes to "
                    "bed at 10 p.m.\n"
                    "The text is about Paul's - - - -.\n\n"
                    "A) daily routine on weekdays\n"
                    "B) weekend activities\n"
                    "C) favourite school subjects\n"
                    "D) errands he runs at home"
                ),
                "answer": "A",
                "solution": (
                    "Metin, uyanmadan yatana kadar Paul'un gün içindeki sıralı etkinliklerini "
                    "saatleriyle veriyor; bu bir günlük rutindir (okul günü). Hafta sonu, sevilen "
                    "ders ya da ev işleri konusu değildir. Doğru cevap A."
                ),
            },
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "kolay",
                "source": _SRC6,
                "question": (
                    "Paul gets up at 6:45 a.m., has breakfast at 7 o'clock, goes to school at "
                    "7:45 a.m., his lessons start at 8:30 a.m., he has dinner at 7:30 p.m. and "
                    "goes to bed at 10 p.m.\n"
                    "Which of the following does Paul do at half past seven p.m.?\n\n"
                    "A) Brushing teeth\nB) Going to school\nC) Waking up\nD) Having dinner"
                ),
                "answer": "D",
                "solution": (
                    "'half past seven p.m.' = 7:30 akşam. Metinde bu saatte akşam yemeği yenir "
                    "('has dinner at 7:30 p.m.'). Diş fırçalama, okula gitme ve uyanma sabah "
                    "saatlerindedir. Doğru cevap D."
                ),
            },
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "orta",
                "source": _SRC6,
                "question": (
                    "Jack attends a folk dance class on Mondays, goes shopping with his father "
                    "on Tuesdays, meets with his friends on Wednesdays, and walks his pet at "
                    "weekends.\n"
                    "He is at the park with his dog now. What is the day today?\n\n"
                    "A) Monday\nB) Tuesday\nC) Wednesday\nD) Sunday"
                ),
                "answer": "D",
                "solution": (
                    "Jack köpeğini hafta sonları gezdirir ('walks his pet at weekends'). Şu an "
                    "köpeğiyle parkta olduğuna göre bugün hafta sonu olmalı. Seçenekler içinde "
                    "yalnız Sunday hafta sonudur. Doğru cevap D."
                ),
            },
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "kolay",
                "source": _SRC6,
                "question": (
                    "Jack's morning routine: he gets up at 08.00 a.m., has breakfast at 08.15 "
                    "a.m., gets dressed at 08.45 a.m., leaves home at 09.00 a.m., arrives at "
                    "school at 09.15 a.m.\n"
                    "Jack - - - - before getting dressed.\n\n"
                    "A) goes to school\nB) has breakfast\nC) arrives at school\nD) leaves home"
                ),
                "answer": "B",
                "solution": (
                    "Giyinme saati 08.45. Bu saatten önce yapılan tek eylem kahvaltıdır "
                    "(08.15). Okula gitme, okula varma ve evden çıkma giyinmeden sonradır. "
                    "Doğru cevap B."
                ),
            },
        ],
        # ── Ünite 4: Family life (Tim's routine — home) ─────────────────────
        "ENG.6.2.G1": [
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "orta",
                "source": _SRC6,
                "question": (
                    "Tim: I get up at 7 o'clock. Then, I have a shower, and I have breakfast "
                    "with my family. I leave home at 9 o'clock for school. In the evening, I "
                    "watch TV. I go to bed at 11 o'clock.\n"
                    "Which of the following does NOT have an answer in the text above?\n\n"
                    "A) What time does Tim go to school?\n"
                    "B) Who does Tim have breakfast with?\n"
                    "C) What time does Tim's school start?\n"
                    "D) What does Tim do in the evening?"
                ),
                "answer": "C",
                "solution": (
                    "Metin okula gitme saatini (9 → A), kahvaltıyı kiminle yaptığını (ailesiyle "
                    "→ B) ve akşam ne yaptığını (TV izler → D) veriyor. Ama okulun kaçta "
                    "başladığı söylenmiyor (evden çıkış saati ≠ ders başlama saati). Doğru cevap C."
                ),
            },
        ],
    },
    # ═══════════════════════════════════════════════════════════════════════
    # 7. SINIF — appearance & personality (cevap metinden zorunlu)
    # ═══════════════════════════════════════════════════════════════════════
    7: {
        # ── Ünite 3: Personal life / physical appearance & character ────────
        "ENG.7.3.V1": [
            {
                "type": QuestionType.KELIME_BILGISI,
                "difficulty": "orta",
                "source": _SRC7,
                "question": (
                    "My brother, John, is very selfish because he always - - - -.\n"
                    "Which of the following completes the sentence above?\n\n"
                    "A) thinks about only himself\n"
                    "B) takes care of poor people\n"
                    "C) spends time with his friends\n"
                    "D) buys presents for his friends"
                ),
                "answer": "A",
                "solution": (
                    "'selfish' (bencil) yalnızca kendini düşünen kişidir. Bu tanıma uyan tek "
                    "davranış 'thinks about only himself'tir. B/C/D olumlu/paylaşımcı "
                    "davranışlardır, bencillikle çelişir. Doğru cevap A."
                ),
            },
            {
                "type": QuestionType.KELIME_BILGISI,
                "difficulty": "kolay",
                "source": _SRC7,
                "question": (
                    "Harry is my best friend. He is a friendly and an easy-going person. He "
                    "also likes sharing everything with the people around him. He likes buying "
                    "them gifts for their birthdays. He is so - - - -.\n"
                    "Which of the following completes the statement above?\n\n"
                    "A) generous\nB) honest\nC) fair\nD) patient"
                ),
                "answer": "A",
                "solution": (
                    "Her şeyi paylaşan ve hediyeler alan biri 'generous' (cömert) olarak "
                    "nitelenir. 'honest' dürüst, 'fair' adil, 'patient' sabırlı demektir; "
                    "paylaşma/hediye davranışını karşılamaz. Doğru cevap A."
                ),
            },
            {
                "type": QuestionType.ESLESTIRME,
                "difficulty": "orta",
                "source": _SRC7,
                "question": (
                    "I.   Punctual   a. someone who always arrives at a certain place on time\n"
                    "II.  Selfish    b. someone who never tells lies\n"
                    "III. Generous   c. someone who only cares about herself\n"
                    "IV.  Honest     d. someone who likes sharing things with other people\n"
                    "Which of the following matchings is CORRECT?\n\n"
                    "A) I-b / II-c / III-d / IV-a\n"
                    "B) I-a / II-d / III-c / IV-b\n"
                    "C) I-a / II-c / III-d / IV-b\n"
                    "D) I-b / II-d / III-c / IV-a"
                ),
                "answer": "C",
                "solution": (
                    "Punctual = zamanında gelen (a), Selfish = yalnız kendini düşünen (c), "
                    "Generous = paylaşmayı seven (d), Honest = hiç yalan söylemeyen (b): "
                    "I-a / II-c / III-d / IV-b. Doğru cevap C."
                ),
            },
        ],
        "ENG.7.3.G1": [
            {
                "type": QuestionType.DIYALOG_TAMAMLAMA,
                "difficulty": "orta",
                "source": _SRC7,
                "question": (
                    "Tim : Who are they in this photo? They look very lovely and happy.\n"
                    "Jim : They are my parents. They were on holiday with my grandparents in "
                    "that photo.\n"
                    "Tim : So nice. - - - -?\n"
                    "Jim : Yes, she is. She is 34, and my father is 37.\n\n"
                    "A) What kind of sports does your mother do\n"
                    "B) Is your mother younger than your father\n"
                    "C) Where are they going to have a holiday\n"
                    "D) Can your mother do sports at home"
                ),
                "answer": "B",
                "solution": (
                    "Jim'in yanıtı 'Yes, she is' + yaş karşılaştırması (anne 34, baba 37). Bu, "
                    "evet/hayır ile yanıtlanan bir karşılaştırma sorusu gerektirir: 'Is your "
                    "mother younger than your father?' (34 < 37 → evet). Doğru cevap B."
                ),
            },
            {
                "type": QuestionType.DIYALOG_TAMAMLAMA,
                "difficulty": "orta",
                "source": _SRC7,
                "question": (
                    "Roar  : I think I'm very fat. It's time to go on a diet. I should stop "
                    "eating fast food.\n"
                    "Chris : I don't think so. You look fit and healthy. - - - -?\n"
                    "Roar  : 63 kg. Isn't it too much?\n"
                    "Chris : To me, it is quite normal. I'm heavier than you.\n\n"
                    "A) What are you like\n"
                    "B) Which sports can you do\n"
                    "C) How much do you weigh\n"
                    "D) Who is heavier than you"
                ),
                "answer": "C",
                "solution": (
                    "Roar'ın yanıtı bir kilo değeridir: '63 kg'. Bu yanıt yalnızca ağırlık "
                    "sorusuna ('How much do you weigh?') uyar. A kişilik, B spor, D kişi sorar. "
                    "Doğru cevap C."
                ),
            },
            {
                "type": QuestionType.DIYALOG_TAMAMLAMA,
                "difficulty": "kolay",
                "source": _SRC7,
                "question": (
                    "Sally  : I think Maria is very stubborn.\n"
                    "Thomas : Why do you think so?\n"
                    "Sally  : Because she - - - -.\n"
                    "Which of the following completes the conversation above?\n\n"
                    "A) always tells the truth\n"
                    "B) works long hours\n"
                    "C) never changes her mind\n"
                    "D) is afraid of planes"
                ),
                "answer": "C",
                "solution": (
                    "'stubborn' (inatçı) kişi fikrini değiştirmez. Bu tanımı karşılayan tek "
                    "gerekçe 'never changes her mind'dir. A dürüstlük, B çalışkanlık, D korku "
                    "ile ilgilidir. Doğru cevap C."
                ),
            },
        ],
        "ENG.7.3.R3": [
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "orta",
                "source": _SRC7,
                "question": (
                    "(I) Our maths teacher Mr. Bandley is a good-looking man. (II) He always "
                    "tells the truth. (III) He is tall and well-built. (IV) He has got short "
                    "curly fair hair and hazel eyes.\n"
                    "Which of the following is ODD?\n\n"
                    "A) I\nB) II\nC) III\nD) IV"
                ),
                "answer": "B",
                "solution": (
                    "I, III ve IV dış görünüşü (yakışıklı, uzun-yapılı, kıvırcık saç/ela göz) "
                    "anlatır. II ise 'always tells the truth' (dürüstlük) bir KİŞİLİK "
                    "özelliğidir; görünüş betimlemesine uymaz. Doğru cevap B."
                ),
            },
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "orta",
                "source": _SRC7,
                "question": (
                    "Hello! I am Amy. I have got two friends. Betty likes helping everyone and "
                    "sharing everything with her friends, so she is a helpful and generous "
                    "person. However, Carol only thinks of herself. I think sharing is key to "
                    "friendship because it means helping each other in difficult times. It is "
                    "not easy to be a friend with selfish people.\n"
                    "Amy believes that being - - - - is very important in a friendship.\n\n"
                    "A) brave\nB) generous\nC) stubborn\nD) outgoing"
                ),
                "answer": "B",
                "solution": (
                    "Amy 'sharing is key to friendship' diyerek paylaşmayı en önemli değer "
                    "sayar; paylaşan kişi 'generous' (cömert) olarak tanımlanır (Betty gibi). "
                    "Cesaret, inatçılık veya dışa dönüklük vurgulanmaz. Doğru cevap B."
                ),
            },
        ],
    },
    # ═══════════════════════════════════════════════════════════════════════
    # 8. SINIF — LGS örnek soruları, cevap anahtarı ile DOĞRULANMIŞ
    # ═══════════════════════════════════════════════════════════════════════
    8: {
        # ── Ünite 4: Family & home — friendship qualities / relationships ───
        "ENG.8.4.R3": [
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "orta",
                "source": _SRC8,
                "question": (
                    "Do you know Mark Twain and Nikola Tesla? Mark Twain (1835-1910) wrote "
                    "many books, and Nikola Tesla (1856-1943) was a famous scientist. They met "
                    "in New York in 1880s. They spent a lot of time together, and they shared "
                    "a lot of ideas. When they were in different countries, they wrote letters "
                    "to each other to keep in touch. Tesla loved Twain's books, and Twain "
                    "respected Tesla's scientific work.\n"
                    "We can understand from the text that Mark Twain and Nikola Tesla - - - -.\n\n"
                    "A) had the same jobs\n"
                    "B) were good friends\n"
                    "C) usually argued\n"
                    "D) rarely met"
                ),
                "answer": "B",
                "solution": (
                    "Birlikte çok vakit geçirmeleri, fikir paylaşmaları, mektuplaşmaları ve "
                    "birbirlerine saygı/sevgi duymaları iyi arkadaş olduklarını gösterir. "
                    "Meslekleri farklı (yazar/bilim insanı), tartışma veya nadiren görüşme "
                    "metinde yok. Doğru cevap B."
                ),
            },
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "orta",
                "source": _SRC8,
                "question": (
                    "Every morning, Mrs. Thompson gives each family member some duties with "
                    "notes on the fridge: 'Mr. Thompson, do not forget to go to the butcher and "
                    "do the grocery shopping.' 'Max, you are in charge of vacuuming the floors "
                    "and dusting the shelves.' 'Alice, today is laundry day. Put the clothes "
                    "into the machine.' 'Sam, your duty is to take out the garbage.'\n"
                    "Which of the following is NOT correct according to the information above?\n\n"
                    "A) Mr. Thompson must do some outdoor chores.\n"
                    "B) Max has to clean the floors and the shelves.\n"
                    "C) Alice is in charge of washing the clothes.\n"
                    "D) Sam is responsible for taking care of the pet."
                ),
                "answer": "D",
                "solution": (
                    "Sam'in görevi çöpü çıkarmaktır ('take out the garbage'), evcil hayvana "
                    "bakmak değil → D yanlıştır. Mr. Thompson dışarı işleri (kasap/market → A), "
                    "Max yer/raf temizliği (B), Alice çamaşır (C) yapar; bunlar doğrudur. "
                    "İstenen YANLIŞ ifade olduğundan doğru cevap D."
                ),
            },
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "kolay",
                "source": _SRC8,
                "question": (
                    "Student Responsibilities — As a student of class 3-A, I accept to obey "
                    "all the rules in my classroom: Study hard and do all my homework. Dress "
                    "appropriately. Respect all students and teachers. Come to class on time. "
                    "Help other students. Listen carefully to my teacher. Keep the classroom "
                    "clean and tidy.\n"
                    "A student in this class should - - - -.\n\n"
                    "A) hit their friends\n"
                    "B) be late for the lesson\n"
                    "C) not do their homework\n"
                    "D) not throw garbage on floor"
                ),
                "answer": "D",
                "solution": (
                    "Kurallar arasında 'Keep the classroom clean and tidy' (sınıfı temiz "
                    "tut) yer alır; bu da yere çöp atmamak demektir → D. A (arkadaşa vurmak), "
                    "B (geç kalmak), C (ödev yapmamak) kurallara aykırıdır. Doğru cevap D."
                ),
            },
        ],
        "ENG.8.4.V1": [
            {
                "type": QuestionType.KELIME_BILGISI,
                "difficulty": "orta",
                "source": _SRC8,
                "question": (
                    "Rosa's personal characteristics are: Honest, Responsible, Kind, "
                    "Generous, Adventurous.\n"
                    "Which of the following is NOT related to Rosa's personality?\n\n"
                    "A) She always says \"please\" and tells the truth.\n"
                    "B) She buys presents for her friends.\n"
                    "C) She likes doing extreme sports.\n"
                    "D) She never changes her mind."
                ),
                "answer": "D",
                "solution": (
                    "A = kind + honest, B = generous, C = adventurous ile örtüşür. 'never "
                    "changes her mind' ise 'stubborn' (inatçı) özelliğine karşılık gelir; "
                    "listede yoktur. İstenen İLGİSİZ ifade olduğundan doğru cevap D."
                ),
            },
            {
                "type": QuestionType.KELIME_BILGISI,
                "difficulty": "orta",
                "source": _SRC8,
                "question": (
                    "Jack   : What do you think of Tim?\n"
                    "Mary   : I think he is the best person in our office because he always "
                    "supports us.\n"
                    "George : He never lies to us, so we can count on him.\n"
                    "Ted    : He also says 'please' when he wants us to do something.\n"
                    "According to the conversation above, which of the following is NOT one of "
                    "the characteristics of Tim?\n\n"
                    "A) Amusing\nB) Helpful\nC) Honest\nD) Kind"
                ),
                "answer": "A",
                "solution": (
                    "Destek olması = helpful (B), yalan söylememesi = honest (C), 'please' "
                    "demesi = kind (D). 'Amusing' (eğlenceli/komik) ise konuşmada geçmez. "
                    "İstenen SAHİP OLMADIĞI özellik olduğundan doğru cevap A."
                ),
            },
        ],
        # ── Ünite 1: School life & events — invitations / accepting-refusing ─
        "ENG.8.1.R3": [
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "orta",
                "source": _SRC8,
                "question": (
                    "Dean is organizing a chess tournament on Sunday. Here are his friends' "
                    "responses:\n"
                    "Tina  : I will definitely be there. You have no chance to win.\n"
                    "Sam   : That sounds great, but I will be out of the town at the weekend.\n"
                    "Clark : That's a good idea. Text me about the time.\n"
                    "Peter : I'd love to join, but I have football training. I can join you "
                    "after it.\n"
                    "According to the conversation above, which of the following is CORRECT?\n\n"
                    "A) Tina isn't interested in playing chess.\n"
                    "B) Sam has to attend a course, so he can't join the tournament.\n"
                    "C) Clark needs extra information about the event.\n"
                    "D) Peter is available all day on Sunday."
                ),
                "answer": "C",
                "solution": (
                    "Clark 'Text me about the time' diyerek etkinliğin saati hakkında ek bilgi "
                    "ister → C doğru. Tina kesin katılacak (A yanlış), Sam şehir dışında olacak "
                    "(kurs değil, B yanlış), Peter antrenman sonrası katılabilir (tüm gün müsait "
                    "değil, D yanlış). Doğru cevap C."
                ),
            },
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "orta",
                "source": _SRC8,
                "question": (
                    "Gary  : I am organizing a movie night at home on Sunday evening. Who "
                    "wants to join?\n"
                    "Jenny : Great idea. I don't have any plans on that day.\n"
                    "Amy   : That sounds awesome, unfortunately, I do not think I can come.\n"
                    "Joe   : Thanks for inviting me, but my brother is coming on that day.\n"
                    "Which of the following is NOT correct according to the conversation "
                    "above?\n\n"
                    "A) Gary is having a birthday party.\n"
                    "B) Jenny is going to attend the event.\n"
                    "C) Amy refuses the invitation without making an excuse.\n"
                    "D) Joe will be with a guest on Sunday."
                ),
                "answer": "A",
                "solution": (
                    "Gary bir 'movie night' (film gecesi) düzenliyor, doğum günü partisi değil "
                    "→ A yanlış. Jenny katılacak (B doğru), Amy gerekçesiz reddediyor (C doğru), "
                    "Joe'nun kardeşi gelecek (D doğru). İstenen YANLIŞ ifade olduğundan doğru "
                    "cevap A."
                ),
            },
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "zor",
                "source": _SRC8,
                "question": (
                    "Alice plans a birthday party on Sunday evening and invites her friends. "
                    "Here are her friends' answers:\n"
                    "Sally  : That sounds great but I am going to a jazz concert.\n"
                    "Julia  : I'm sorry but I can't join you on Sunday night.\n"
                    "Anna   : I love parties, but I can't. I have to take care of my little "
                    "sister.\n"
                    "Sophia : It sounds nice but I have to leave before 6 pm.\n"
                    "Rose   : I'd love to but my grandparents will visit us at the weekend.\n"
                    "Alexis : A birthday party? I can't say no. Do you need any help?\n"
                    "Who refuses the invitation by giving an excuse?\n\n"
                    "A) Alexis, Sally, and Julia\n"
                    "B) Julia, Sophia, and Rose\n"
                    "C) Anna, Sophia, and Alexis\n"
                    "D) Sally, Anna, and Rose"
                ),
                "answer": "D",
                "solution": (
                    "Gerekçe sunarak reddedenler: Sally (jazz konseri), Anna (kardeşine bakma) "
                    "ve Rose (büyükanne-baba ziyareti). Julia gerekçe vermeden reddeder, Sophia "
                    "erken ayrılacağını söyler (kesin ret değil), Alexis daveti kabul eder. "
                    "Doğru cevap D."
                ),
            },
        ],
        # ── Ünite 3: Personal life & well-being — mobile phones / on the phone
        "ENG.8.3.R3": [
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "orta",
                "source": _SRC8,
                "question": (
                    "Customer Service : Hello, how can I help you?\n"
                    "Alice : Hi, I want to book a flight ticket from London to New York.\n"
                    "Customer Service : Sure. One way or return?\n"
                    "Alice : Return.\n"
                    "Customer Service : Can you tell me the dates on which you want to travel?\n"
                    "Alice : June 15th and June 26th.\n"
                    "Customer Service : Can I have your name and phone number, please?\n"
                    "Alice : Alice Black, 09502345678.\n"
                    "Customer Service : Your flight is reserved. Have a good flight.\n"
                    "Which of the following does NOT have an answer in the conversation "
                    "above?\n\n"
                    "A) What is the phone conversation about?\n"
                    "B) What is the destination of the flight?\n"
                    "C) What are the dates of the flights?\n"
                    "D) What is Alice's reason for travelling?"
                ),
                "answer": "D",
                "solution": (
                    "Konuşma konusu (uçak rezervasyonu → A), varış yeri (New York → B) ve "
                    "tarihler (15-26 Haziran → C) veriliyor. Ancak Alice'in seyahat NEDENİ "
                    "söylenmiyor. İstenen cevabı OLMAYAN soru olduğundan doğru cevap D."
                ),
            },
        ],
        "ENG.8.3.G1": [
            {
                "type": QuestionType.DIYALOG_TAMAMLAMA,
                "difficulty": "orta",
                "source": _SRC8,
                "question": (
                    "Mr. Cullingham : Hello, Mr. Archlair. My car is not working. I don't know "
                    "the problem.\n"
                    "Mr. Archlair : Hi, Mr. Cullingham. Oh, I am sorry to hear that.\n"
                    "Mr. Cullingham : And I have a meeting at ten o'clock.\n"
                    "Mr. Archlair : OK, tell me where you are and - - - -.\n"
                    "Which of the following completes the conversation?\n\n"
                    "A) I hope you will be more careful when you drive\n"
                    "B) I will send someone to take you and your car\n"
                    "C) I will see your car if you come to the garage\n"
                    "D) I will go to the meeting if you really want"
                ),
                "answer": "B",
                "solution": (
                    "Arabası bozulan ve saat 10'da toplantısı olan Mr. Cullingham'a yardım "
                    "gerekir. 'tell me where you are' (bana nerede olduğunu söyle) devamında "
                    "mantıklı çözüm, birini gönderip onu ve arabasını almaktır → B. Diğerleri ya "
                    "eleştiri (A) ya da duruma uymayan tekliflerdir. Doğru cevap B."
                ),
            },
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "orta",
                "source": _SRC8,
                "question": (
                    "You must write a text message to your friend because you want to change "
                    "the time of the meeting at the café.\n"
                    "Which of the following is the message you will send in that situation?\n\n"
                    "A) Hi Daniel, I have an appointment with my doctor. Sorry, I can't meet "
                    "you.\n"
                    "B) Hi Daniel. Can we meet an hour later? I am so sorry for that. I could "
                    "not finish my project, and I need a bit of extra time.\n"
                    "C) Hey Daniel, I cannot remember our meeting place for today. Can you send "
                    "me the café's name once again?\n"
                    "D) Hi Daniel, there were too many people, so I have left the café. Find me "
                    "in front of the cinema."
                ),
                "answer": "B",
                "solution": (
                    "Amaç buluşma SAATİNİ değiştirmektir. Yalnız B saat değişikliği önerir "
                    "('Can we meet an hour later?' = bir saat sonra buluşabilir miyiz). A "
                    "buluşmayı iptal eder, C yeri sorar, D yer değişikliği bildirir. Doğru cevap B."
                ),
            },
        ],
        # ── Ünite 2: Classroom life & learning — teen leisure preferences ───
        "ENG.8.2.R3": [
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "orta",
                "source": _SRC8,
                "question": (
                    "Hello. My name is Frank. I'm 14 years old and a student in 8th grade. On "
                    "weekdays, I get up at 7:30. I wash my hands and face before I have "
                    "breakfast with my family. I go to school at 8:40. After school, I like "
                    "reading books and playing chess with my brother, David. I usually read "
                    "detective books. My friends and I play basketball on Saturday afternoons.\n"
                    "Which of the following does NOT have an answer in the text?\n\n"
                    "A) What kind of games does Frank like playing?\n"
                    "B) What time does he get up on Tuesdays?\n"
                    "C) What does he do before the breakfast?\n"
                    "D) Where does he play basketball?"
                ),
                "answer": "D",
                "solution": (
                    "Oyun türü (satranç → A), hafta içi kalkış saati (7:30 → B) ve kahvaltı "
                    "öncesi yaptığı (ellerini/yüzünü yıkar → C) metinde var. Basketbolu NEREDE "
                    "oynadığı ise söylenmiyor (yalnız ne zaman: cumartesi öğleden sonra). "
                    "Doğru cevap D."
                ),
            },
            {
                "type": QuestionType.KELIME_BILGISI,
                "difficulty": "orta",
                "source": _SRC8,
                "question": (
                    "After a rock concert, some people wrote notes to the singer:\n"
                    "Jane : I think your concert was magnificent. At the end of the concert, I "
                    "was really happy.\n"
                    "Sam  : It's the worst performance I've ever seen. Your behavior during the "
                    "concert was insulting.\n"
                    "John : Your music is impressive. I cannot stop listening to your songs.\n"
                    "Mary : Your concerts are always terrific. I am fond of your voice.\n"
                    "Whose comment was disappointing for the singer?\n\n"
                    "A) Sam\nB) John\nC) Jane\nD) Mary"
                ),
                "answer": "A",
                "solution": (
                    "Jane, John ve Mary olumlu ve övücü yorumlar yazar (magnificent, "
                    "impressive, terrific). Sam ise 'worst performance' ve 'insulting' diyerek "
                    "olumsuz/hayal kırıklığı yaratan bir yorum yapar. Doğru cevap A."
                ),
            },
        ],
    },
}
