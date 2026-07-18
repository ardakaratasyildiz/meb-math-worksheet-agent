"""Sosyal Bilgiler / İnkılap Tarihi few-shot havuzu — sınıf → kazanım kodu → örnekler.

Kaynak: MEB ÖDSGM/EBA ünitelendirilmiş **kazanım testleri**
(knowledge_base/Sosyal/ornek_sorular/{5,6,7,8}.sinif/kazanim_testi_unite_*.pdf).
Sorular PyMuPDF (fitz) ile metin çıkarımıyla alındı; uzun pasajlar anlam bozulmadan
makul biçimde kısaltıldı. Yapı Fen/Türkçe deseniyle aynı: dict[grade][kazanim_kod]
-> [{type, difficulty, source, question, answer, solution}] (bkz. app/subjects/fen/few_shot.py).

⚠️ KAPSAM: yalnız GÖRSELSİZ (tam metin) sorular alındı. Harita/tablo/grafik/görsel-şık
gerektiren sorular ATLANDI (few-shot metin akışını bozar) — sosyalde harita soruları
çok olduğundan yalnız okuduğunu-anlama / çıkarım / kavram / belge-yorumu soruları seçildi.

⚠️ CEVAP DOĞRULAMA (kritik fark — bkz. knowledge_base/Sosyal/QUESTION_ANALYSIS.md §4):
- **8. sınıf (İnkılap Tarihi):** cevaplar resmî `kazanim_testi_cevap_anahtari.pdf` ile
  BİREBİR doğrulandı (güvenilir çekirdek). En zengin kapsam burada.
- **5/6/7. sınıf:** kazanım testleri için resmî cevap anahtarı kaynakta YOK (404;
  `*_sos_beceri_cevap.pdf` FARKLI bir soru setine aittir, bu testlere ait değildir).
  Bu yüzden 5/6/7'de yalnızca cevabı metin/tanımdan ya da tartışmasız tarihsel olgudan
  KESİN çıkan (tahmin gerektirmeyen) sorular alındı; çözümler bunu gerekçelendirir.

KAZANIM EŞLEME: EBA kazanım testleri ESKİ müfredat öğrenme alanlarına göre dizilidir
(ünite no ≠ 2024 TYMM ünite no). Her soru 2024 TYMM kazanım koduna (SOS_CURRICULUM,
app/subjects/sosyal/curriculum.py) İÇERİĞE göre elle eşlendi. collect_few_shot() seçilen
kazanımların kodlarıyla bu havuzu eşler (app/subjects/sosyal/__init__.py:78).
NOT: 2024 grade-8 müfredatı yalnız 4 ünite içerir (İTA.8.1–8.4); kazanım testinin 5-6.
üniteleri (Demokratikleşme / Dış Politika) karşılık gelen kazanım olmadığından alınmadı.
"""
from __future__ import annotations

from app.models.enums import QuestionType

_SRC_5 = "MEB ÖDSGM/EBA 5. Sınıf Sosyal Bilgiler kazanım testi"
_SRC_6 = "MEB ÖDSGM/EBA 6. Sınıf Sosyal Bilgiler kazanım testi"
_SRC_7 = "MEB ÖDSGM/EBA 7. Sınıf Sosyal Bilgiler kazanım testi"
_SRC_8 = "MEB ÖDSGM/EBA 8. Sınıf İnkılap Tarihi kazanım testi (resmî CA ile doğrulandı)"

# sınıf → kazanım kodu → örnek listesi
SOS_EXAMPLES: dict[int, dict[str, list[dict]]] = {
    # ══════════════════════════════════════════════════════════════════════
    # 5. SINIF — cevaplar metin/tanımdan kesin çıkarım (resmî CA yok, §doc)
    # ══════════════════════════════════════════════════════════════════════
    5: {
        # ── Gruplar ve roller ─────────────────────────────────────────────
        "SB.5.1.1": [
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "kolay",
                "source": _SRC_5,
                "question": (
                    "Elif okula başlayacağı için erkenden kalktı. Kahvaltısını yaptı ve "
                    "annesiyle okulun yolunu tuttu. Okuldaki ilk gününde okulunu ve "
                    "arkadaşlarını çok sevdi.\n"
                    "Elif'in okuldaki rolü aşağıdakilerden hangisidir?\n\n"
                    "A) Öğrenci\nB) Oyuncu\nC) Çocuk\nD) Öğretmen"
                ),
                "answer": "A",
                "solution": (
                    "Bir bireyin rolü, içinde bulunduğu gruba göre değişir. Elif okul "
                    "grubunda ders gören biri olarak 'öğrenci' rolündedir; 'çocuk' ailedeki, "
                    "'öğretmen' ise ders veren kişinin rolüdür. Doğru cevap A."
                ),
            },
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC_5,
                "question": (
                    "Aşağıdakilerden hangisi 5. sınıftaki Ömer'in okuldaki "
                    "sorumluluklarından biri OLAMAZ?\n\n"
                    "A) Derse zamanında girmek\n"
                    "B) Kırılan sırayı/tahtayı onarmak\n"
                    "C) Çantasını hazırlamak\n"
                    "D) Boşa akan musluğu kapatmak"
                ),
                "answer": "B",
                "solution": (
                    "Derse zamanında girmek, çantasını hazırlamak ve boşa akan musluğu "
                    "kapatmak bir öğrencinin okuldaki sorumluluklarıdır. Kırılan tahtayı "
                    "onarmak ise teknik bir iştir, öğrencinin rolünün gerektirdiği bir "
                    "sorumluluk değildir. Doğru cevap B."
                ),
            },
        ],
        # ── Etkin/bilinçli vatandaşlık ────────────────────────────────────
        "SB.5.4.2": [
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC_5,
                "question": (
                    "Etkin ve bilinçli bir vatandaşın özellikleri:\n"
                    "I. Yasaların gereklerini yerine getirir.\n"
                    "II. Bulunduğu ortamda kurallara uygun davranır.\n"
                    "III. Haklarını bilir, sorumluluklarını yerine getirir.\n"
                    "IV. Bireysel çıkarlarını her şeyin önünde tutar.\n"
                    "Yukarıdakilerden hangileri etkin ve bilinçli bir vatandaşta bulunması "
                    "beklenen özelliklerdendir?\n\n"
                    "A) I, II ve III\nB) I, II ve IV\nC) I, III ve IV\nD) II, III ve IV"
                ),
                "answer": "A",
                "solution": (
                    "Etkin vatandaş yasalara ve kurallara uyar (I, II), hak ve "
                    "sorumluluklarının bilincindedir (III). Bireysel çıkarını toplumun "
                    "önüne koymak (IV) etkin vatandaşlıkla bağdaşmaz. Doğru cevap A."
                ),
            },
        ],
        # ── Temel insan hakları / çocuk hakları ───────────────────────────
        "SB.5.4.3": [
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "kolay",
                "source": _SRC_5,
                "question": (
                    "Zeynep: 'Geçen hafta hasta olduğum için okula gidemedim. Babam beni "
                    "hastaneye götürdü. Doktor benimle ilgilendi ve ilaç yazdı. İlaçlarımı "
                    "almak için eczaneye gittik. Doktorun tavsiyelerine uyduğum için kısa "
                    "sürede iyileştim.'\n"
                    "Buna göre Zeynep hangi hakkını kullanmıştır?\n\n"
                    "A) Eğitim\nB) Beslenme\nC) İfade özgürlüğü\nD) Sağlık"
                ),
                "answer": "D",
                "solution": (
                    "Metinde hastalanma, hastane, doktor, ilaç ve tedavi süreci "
                    "anlatılmaktadır; bunların tümü sağlık hakkının kullanımına örnektir. "
                    "Doğru cevap D."
                ),
            },
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC_5,
                "question": (
                    "Aşağıdaki durumlardan hangisi çocuklara verildiğinde Birleşmiş "
                    "Milletler Çocuk Haklarına Dair Sözleşme İHLAL EDİLMİŞ OLMAZ?\n\n"
                    "A) Satranç kulübüne katılması\n"
                    "B) İşçi olarak çalıştırılması\n"
                    "C) Sokakta mendil satması\n"
                    "D) Askere alınması"
                ),
                "answer": "A",
                "solution": (
                    "Çocukların çalıştırılması (B), sokakta çalıştırılması (C) ve askere "
                    "alınması (D) Çocuk Hakları Sözleşmesi'ne aykırıdır. Bir kulübe katılıp "
                    "boş zamanını değerlendirmek ise bir haktır, ihlal değildir. Doğru cevap A."
                ),
            },
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC_5,
                "question": (
                    "Çocuk Haklarına Dair Sözleşme'nin bazı maddeleri:\n"
                    "• Taraf devletler çocuğun hayatını sürdürmesi ve gelişmesi için en "
                    "yüksek çabayı gösterir. (Md. 6)\n"
                    "• Bütün çocuklara gerekli tıbbi yardım ve bakım sağlanır. (Md. 24)\n"
                    "• İlköğretim herkes için zorunlu ve parasızdır. (Md. 28)\n"
                    "Bu maddeler aşağıdaki alanlardan hangisiyle İLİŞKİLENDİRİLEMEZ?\n\n"
                    "A) Eğitim\nB) Güvenlik\nC) Yaşama\nD) Sağlık"
                ),
                "answer": "B",
                "solution": (
                    "Madde 6 yaşama, Madde 24 sağlık, Madde 28 eğitim hakkıyla ilgilidir. "
                    "Verilen maddelerin hiçbiri güvenlik hakkına değinmez; bu yüzden "
                    "güvenlik ile ilişkilendirilemez. Doğru cevap B."
                ),
            },
        ],
    },
    # ══════════════════════════════════════════════════════════════════════
    # 6. SINIF — cevaplar metin/tanımdan kesin çıkarım (resmî CA yok, §doc)
    # ══════════════════════════════════════════════════════════════════════
    6: {
        # ── Roller ve rollerin değişmesi ──────────────────────────────────
        "SB.6.1.1": [
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC_6,
                "question": (
                    "Semih Bey, gün boyu doktor rolünü üstlendikten sonra akşam taksiyle "
                    "eve giderken yolcu (müşteri) rolündedir. Evine geldiğinde ise "
                    "çocuklarına karşı baba rolündedir.\n"
                    "Buna göre Semih Bey ile ilgili;\n"
                    "I. Gün içinde birden fazla rol üstlenmiştir.\n"
                    "II. Rollerinin gereğini yerine getirememektedir.\n"
                    "III. Üstlendiği roller yetenek ve değerlerine uygun değildir.\n"
                    "yargılarından hangilerine ulaşılabilir?\n\n"
                    "A) Yalnız I\nB) I ve III\nC) II ve III\nD) I, II ve III"
                ),
                "answer": "A",
                "solution": (
                    "Metin, Semih Bey'in aynı gün içinde doktor, yolcu ve baba gibi farklı "
                    "roller üstlendiğini gösterir (I). Rollerin gereğini yerine "
                    "getiremediğine (II) veya rollerin ona uygun olmadığına (III) dair "
                    "hiçbir bilgi yoktur. Doğru cevap A."
                ),
            },
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC_6,
                "question": (
                    "'İsmim Yasin Yıldırım, taksicilik yapıyorum. Çocuklarım evimizin "
                    "neşesidir, ödevlerine yardımcı olurum. Annem de bizimle kalıyor; akşam "
                    "eve geldiğimde ilk iş annemin elini öper, bir sıkıntısı olup olmadığını "
                    "sorarım.'\n"
                    "Metne göre aşağıdakilerden hangisi Yasin Bey'in üstlendiği rollerden "
                    "biri DEĞİLDİR?\n\n"
                    "A) Evlat\nB) Şoför\nC) Baba\nD) Kardeş"
                ),
                "answer": "D",
                "solution": (
                    "Metinde Yasin Bey'in taksici (şoför), çocuklarının babası ve annesine "
                    "karşı evlat rolleri açıkça yer alır. Bir kardeşinden söz edilmediği "
                    "için 'kardeş' rolü metinden çıkarılamaz. Doğru cevap D."
                ),
            },
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "kolay",
                "source": _SRC_6,
                "question": (
                    "Roller doğuştan sahip olunan ve sonradan kazanılan roller olmak üzere "
                    "ikiye ayrılır.\n"
                    "Buna göre aşağıdakilerden hangisi DOĞUŞTAN sahip olunan bir role "
                    "örnektir?\n\n"
                    "A) Evlat\nB) Öğretmen\nC) Öğrenci\nD) Yönetici"
                ),
                "answer": "A",
                "solution": (
                    "Öğretmenlik, öğrencilik ve yöneticilik eğitim veya çalışmayla sonradan "
                    "kazanılan rollerdir. Evlatlık ise kişi dünyaya geldiği anda sahip olduğu "
                    "doğuştan bir roldür. Doğru cevap A."
                ),
            },
        ],
        # ── Kültürel bağlar / millî değerler ve toplumsal birlik ──────────
        "SB.6.1.2": [
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC_6,
                "question": (
                    "Toplumsal yaşamın vazgeçilmezi olan değerlerin, örf ve âdetlerin, "
                    "gelenek ve göreneklerin nesilden nesile aktarılmasını sağlayan kültürel "
                    "öge aşağıdakilerden hangisidir?\n\n"
                    "A) Din\nB) Tarih\nC) Dil\nD) Ahlak"
                ),
                "answer": "C",
                "solution": (
                    "Değerlerin, geleneklerin ve birikimin kuşaktan kuşağa aktarılmasını "
                    "sağlayan temel araç dildir; kültür büyük ölçüde dil aracılığıyla "
                    "taşınır. Doğru cevap C."
                ),
            },
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC_6,
                "question": (
                    "'Bir toplumu millet yapan en önemli özelliklerden biri de ortak bir "
                    "geçmişe sahip olmasıdır. Geçmişi olmayan bir toplumun geleceği de olmaz.'\n"
                    "Yukarıdaki metinde kültürel ögelerden hangisinin önemine vurgu "
                    "yapılmıştır?\n\n"
                    "A) Dil\nB) Din\nC) Dayanışma\nD) Tarih"
                ),
                "answer": "D",
                "solution": (
                    "Metin 'ortak geçmiş' ve 'geçmişini bilmek' üzerinde durmaktadır; bir "
                    "toplumun geçmişini konu alan kültürel öge tarihtir. Doğru cevap D."
                ),
            },
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC_6,
                "question": (
                    "Zeliha: 'Karşımızdaki daireye üç çocuklu bir aile taşındı. İlk başta "
                    "onlardan pek hoşlanmadım; giyim-kuşamları ve şiveleri bizden çok "
                    "farklıydı. Fakat onları tanıdıkça ne kadar sıcakkanlı ve iyi niyetli "
                    "insanlar olduklarını anladım; şimdi çok iyi anlaşıyoruz.'\n"
                    "Buna göre aşağıdaki yargılardan hangisine ULAŞILAMAZ?\n\n"
                    "A) İnsanlar birbirini tanıdıkça ön yargılar artar.\n"
                    "B) İnsanlar arasındaki iletişim önemlidir.\n"
                    "C) Ön yargılar arkadaşlık ilişkilerini olumsuz etkiler.\n"
                    "D) Farklılıklar ön yargılara neden olabilmektedir."
                ),
                "answer": "A",
                "solution": (
                    "Metinde Zeliha komşularını tanıdıkça ön yargılarının AZALDIĞI "
                    "anlatılır. 'Tanıdıkça ön yargıların arttığı' (A) metinle çelişir, bu "
                    "yüzden ulaşılamaz. B, C ve D metinle uyumludur. Doğru cevap A."
                ),
            },
        ],
    },
    # ══════════════════════════════════════════════════════════════════════
    # 7. SINIF — Osmanlı (Ortak Mirasımız); cevaplar metin/olgudan kesin
    # ══════════════════════════════════════════════════════════════════════
    7: {
        # ── Osmanlı'nın cihan devleti hâline gelmesi ──────────────────────
        "SB.7.3.1": [
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC_7,
                "question": (
                    "Mısır'a yönelik seferleri sonucunda Baharat Yolu'nu Osmanlı denetimine "
                    "alan; fetihlerle hazineyi doldurduktan sonra hazineyi mühürletip "
                    "'Benim altınla doldurduğum hazineyi, torunlarımdan her kim doldurabilirse "
                    "kendi mührüyle mühürlesin; aksi hâlde hazine benim mührümle kalsın.' "
                    "diye vasiyet eden Osmanlı padişahı kimdir?\n\n"
                    "A) Yavuz Sultan Selim\nB) Fatih Sultan Mehmet\n"
                    "C) Kanuni Sultan Süleyman\nD) Osman Bey"
                ),
                "answer": "A",
                "solution": (
                    "Mısır Seferi (1517), Baharat Yolu'nun ele geçirilmesi ve hazineyi "
                    "mühürleyip doldurma vasiyeti Yavuz Sultan Selim'e aittir. Doğru cevap A."
                ),
            },
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC_7,
                "question": (
                    "• Barbaros Hayrettin Paşa öncülüğündeki Osmanlı donanması ile Andrea "
                    "Dorya komutasındaki Haçlı donanması arasında 27 Eylül 1538'de yapılmıştır.\n"
                    "• Osmanlı'nın galibiyetiyle Akdeniz'deki üstünlük Osmanlı'ya geçmiştir.\n"
                    "• Günümüzde 'Deniz Kuvvetleri Günü' olarak kutlanır.\n"
                    "Özellikleri verilen olay aşağıdakilerden hangisidir?\n\n"
                    "A) İnebahtı Deniz Savaşı\nB) Rodos'un Fethi\n"
                    "C) Preveze Deniz Savaşı\nD) Girit'in Fethi"
                ),
                "answer": "C",
                "solution": (
                    "Barbaros Hayrettin Paşa'nın 1538'de kazandığı ve Akdeniz hâkimiyetini "
                    "Osmanlı'ya getiren zafer Preveze Deniz Savaşı'dır. İnebahtı ise 1571'de "
                    "kaybedilen savaştır. Doğru cevap C."
                ),
            },
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC_7,
                "question": (
                    "Fetret Devri'nde (1402-1413) Osmanlı Devleti'nin Balkanlardaki "
                    "ilerleyişi duraksamış, Anadolu Türk birliği bozulmuş ve beylikler "
                    "yeniden kurulmuştur.\n"
                    "Verilen bilgide Fetret Devri'nin hangi alandaki etkisinden söz "
                    "edilmiştir?\n\n"
                    "A) Dinî\nB) Siyasi\nC) Ekonomik\nD) Kültürel"
                ),
                "answer": "B",
                "solution": (
                    "İlerleyişin durması, Türk birliğinin bozulması ve beyliklerin yeniden "
                    "kurulması yönetim ve devlet düzeniyle ilgili gelişmelerdir; bunlar siyasi "
                    "etkilerdir. Doğru cevap B."
                ),
            },
            {
                "type": QuestionType.KAYNAK_METIN,
                "difficulty": "orta",
                "source": _SRC_7,
                "question": (
                    "Yavuz Sultan Selim, Memluklerle 1516'da Mercidabık, 1517'de Ridaniye "
                    "Savaşı'nı yaptı. Sonucunda Memluk Devleti'ne son verildi, Mısır "
                    "Osmanlı'ya bağlandı, Kutsal Emanetler İstanbul'a getirildi ve Osmanlı "
                    "Baharat Yolu'nun önemli kısmına hâkim oldu.\n"
                    "Verilen bilgide Mısır'ın fethinin;\n"
                    "I. dinî,\nII. siyasi,\nIII. ekonomik\n"
                    "sonuçlarından hangilerine değinilmiştir?\n\n"
                    "A) Yalnız I\nB) I ve II\nC) II ve III\nD) I, II ve III"
                ),
                "answer": "D",
                "solution": (
                    "Kutsal Emanetlerin getirilmesi dinî (I), Memluk Devleti'ne son "
                    "verilmesi siyasi (II), Baharat Yolu'na hâkim olunması ekonomik (III) "
                    "sonuçtur; üçü de metinde yer alır. Doğru cevap D."
                ),
            },
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "zor",
                "source": _SRC_7,
                "question": (
                    "İstimâlet, Osmanlı kaynaklarında halkı -özellikle gayrimüslim tebaayı- "
                    "gözetme, onlara adil davranma anlamında kullanılmıştır.\n"
                    "Buna göre Osmanlı Devleti'nin istimâlet politikasıyla aşağıdakilerden "
                    "hangisini gerçekleştirmeye çalıştığı SÖYLENEMEZ?\n\n"
                    "A) Gayrimüslimleri ayrıcalıklı (imtiyazlı) hâle getirmeyi\n"
                    "B) Fethedilen yerlerde kalıcılığı sağlamayı\n"
                    "C) Halkın devlete bağlılığını artırmayı\n"
                    "D) Toplumsal barış ve huzuru tesis etmeyi"
                ),
                "answer": "A",
                "solution": (
                    "İstimâlet, gayrimüslimlere ADİL ve eşit davranmayı, bağlılığı ve kalıcı "
                    "barışı (B, C, D) amaçlar. Onlara Müslümanlardan üstün ayrıcalık vermeyi "
                    "değil; bu yüzden A söylenemez. Doğru cevap A."
                ),
            },
        ],
        # ── Osmanlı kültür ve medeniyeti (hoşgörü, yönetim, millet sistemi) ─
        "SB.7.3.3": [
            {
                "type": QuestionType.KAYNAK_METIN,
                "difficulty": "orta",
                "source": _SRC_7,
                "question": (
                    "Fatih Sultan Mehmet, İstanbul'un fethinden sonra şehirden ayrılanların "
                    "dönmesi için tedbirler almış; Ayasofya'da toplanan halka korkmadan "
                    "evlerine ve işlerine dönebileceklerini söylemiş, onlara can, mal ve ırz "
                    "güvenliği vermiştir.\n"
                    "Metne göre Osmanlı Devleti ile ilgili aşağıdakilerden hangisine "
                    "ULAŞILAMAZ?\n\n"
                    "A) Hoşgörü politikası uygulandığına\n"
                    "B) Halk egemenliğine (cumhuriyete) geçildiğine\n"
                    "C) Halkın koruma altına alındığına\n"
                    "D) Birlikte yaşama isteğine önem verildiğine"
                ),
                "answer": "B",
                "solution": (
                    "Metinde padişahın halka güvence vermesi hoşgörüyü, korumayı ve birlikte "
                    "yaşama isteğini gösterir (A, C, D). Osmanlı bir monarşidir; 'halk "
                    "egemenliğine geçildiği' metinden çıkarılamaz. Doğru cevap B."
                ),
            },
            {
                "type": QuestionType.KAYNAK_METIN,
                "difficulty": "orta",
                "source": _SRC_7,
                "question": (
                    "Osmanlı Devleti'nde Hristiyan ve Yahudiler de tıpkı Müslümanlar gibi "
                    "hür tebaadan sayılırdı. Kilise ve havralar devletçe korunur, herkes "
                    "dinine göre ibadetini yapardı. Farklı milletler kendi devletlerinden "
                    "görmedikleri hoşgörüyü Osmanlı'dan görmüştü.\n"
                    "Buna göre Osmanlı Devleti ile ilgili aşağıdakilerden hangisine "
                    "ULAŞILAMAZ?\n\n"
                    "A) Sınırları içinde birçok milletin bulunduğuna\n"
                    "B) Müslümanların diğerlerinden üstün tutulduğuna\n"
                    "C) Farklı dinden insanların bir arada yaşadığına\n"
                    "D) Halka din ve inanç hürriyeti tanındığına"
                ),
                "answer": "B",
                "solution": (
                    "Metin, gayrimüslimlerin de hür sayıldığını ve serbestçe ibadet "
                    "ettiğini, yani eşit muamele gördüğünü anlatır. 'Müslümanların üstün "
                    "tutulduğu' bilgisi metinle çelişir. Doğru cevap B."
                ),
            },
            {
                "type": QuestionType.KAYNAK_METIN,
                "difficulty": "orta",
                "source": _SRC_7,
                "question": (
                    "Fatih Sultan Mehmet, Bosna'yı fethedince yayımladığı fermanla "
                    "rahiplere: 'Kiliselerinizde korkusuzca ibadet edin, memleketimde "
                    "korkusuzca oturun; canlarınız, mallarınız ve kiliseleriniz bana itaat "
                    "ettiğiniz sürece güvencem altındadır.' demiştir.\n"
                    "Bu fermanın yayımlanmasında;\n"
                    "I. adalet ve hoşgörü anlayışı,\nII. din ve vicdan hürriyeti,\n"
                    "III. fetihleri sona erdirme\n"
                    "düşüncelerinden hangilerinin hâkim olduğu söylenebilir?\n\n"
                    "A) Yalnız II\nB) I ve II\nC) II ve III\nD) I, II ve III"
                ),
                "answer": "B",
                "solution": (
                    "Ferman, halka güvence vererek adalet-hoşgörü (I) ile din ve vicdan "
                    "hürriyetini (II) yansıtır. Fetihlerin sona erdirilmesiyle (III) hiçbir "
                    "ilgisi yoktur. Doğru cevap B."
                ),
            },
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC_7,
                "question": (
                    "Osmanlı Devleti'nde yönetenler; gördükleri vazife ve eğitime göre "
                    "seyfiye, kalemiye ve ilmiye olmak üzere üç sınıfa ayrılmıştır.\n"
                    "Aşağıdakilerden hangisi ilmiye sınıfını oluşturan görevlilerden biri "
                    "DEĞİLDİR?\n\n"
                    "A) Kazasker\nB) Kadı\nC) Şeyhülislam\nD) Defterdar"
                ),
                "answer": "D",
                "solution": (
                    "İlmiye sınıfı eğitim, hukuk ve din işleriyle ilgilenir; kazasker, kadı "
                    "ve şeyhülislam bu sınıftandır. Defterdar ise maliye işlerine bakan "
                    "kalemiye sınıfı görevlisidir. Doğru cevap D."
                ),
            },
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC_7,
                "question": (
                    "Osmanlı Devleti'nde uygulanan bu düzen, çok uluslu yapıdaki farklı "
                    "dinlere mensup toplumları barış içinde yaşatmayı hedeflemiş; devlet "
                    "içindeki milletlerin örf ve âdetlerini korumalarını sağlamıştır.\n"
                    "Metinde sözü edilen uygulama aşağıdakilerden hangisidir?\n\n"
                    "A) Devşirme sistemi\nB) Gaza ve cihat anlayışı\n"
                    "C) Millet sistemi\nD) İskân politikası"
                ),
                "answer": "C",
                "solution": (
                    "Farklı din ve milletlerin kendi örf-âdetleriyle bir arada barış içinde "
                    "yaşatılmasını sağlayan uygulama millet sistemidir. Doğru cevap C."
                ),
            },
        ],
    },
    # ══════════════════════════════════════════════════════════════════════
    # 8. SINIF — İNKILAP TARİHİ — cevaplar resmî CA ile doğrulandı (çekirdek)
    # ══════════════════════════════════════════════════════════════════════
    8: {
        # ── Osmanlı'nın XIX-XX. yy durumu ve fikir akımları ───────────────
        "İTA.8.1.1": [
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC_8,
                "question": (
                    "Avrupa'da gelişen Sanayi İnkılabı ile sanayileşen Avrupalı devletler, "
                    "kapitülasyonlar sayesinde ürettikleri malları Osmanlı ülkesine "
                    "kolaylıkla ihraç etti. Osmanlı pazarları düşük maliyetli Avrupa "
                    "mallarıyla doldu; insanlar ithal ürünlere yöneldi.\n"
                    "Buna göre Sanayi İnkılabı'nın Osmanlı Devleti'nde aşağıdakilerden "
                    "hangisine neden olduğu söylenebilir?\n\n"
                    "A) İşsiz insan sayısının azalmasına\n"
                    "B) Küçük el tezgâhlarının sayısının artmasına\n"
                    "C) Devlet vergi gelirlerinin çok yükselmesine\n"
                    "D) Ülke topraklarının uluslararası açık bir pazara dönüşmesine"
                ),
                "answer": "D",
                "solution": (
                    "Kapitülasyonlarla ucuz Avrupa mallarının Osmanlı pazarını doldurması, "
                    "ülkenin dışa açık bir pazar hâline gelmesine yol açmıştır. Yerli üretim "
                    "gerileyeceğinden A ve B yanlıştır. Doğru cevap D."
                ),
            },
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC_8,
                "question": (
                    "Fransız İhtilali'nden etkilenen ve Jön Türkler olarak bilinen aydınlar, "
                    "gayrimüslim isyanlarının temel nedenini padişahın ülkeyi tek başına "
                    "yönetmesi olarak görüyordu. Onlara göre bir anayasa hazırlanmalı, meclis "
                    "açılmalı, herkese temsil hakkı verilmeli ve padişah bu meclisle birlikte "
                    "yönetmeliydi.\n"
                    "Buna göre Jön Türkler hangi alanda değişim yaşanmasını savunmuştur?\n\n"
                    "A) Askerî örgütlenme\nB) Yönetim sistemi\nC) Ekonomik yapı\n"
                    "D) Dış politika"
                ),
                "answer": "B",
                "solution": (
                    "Anayasa, meclis ve padişahın meclisle birlikte yönetmesi talepleri "
                    "devletin yönetim sistemine yöneliktir (meşrutiyet). Doğru cevap B."
                ),
            },
        ],
        # ── Atatürk'ün hayatı (çocuk/komutan/devlet adamı) ────────────────
        "İTA.8.1.2": [
            {
                "type": QuestionType.KAYNAK_METIN,
                "difficulty": "orta",
                "source": _SRC_8,
                "question": (
                    "Mustafa Kemal anlatıyor: 'Selanik Mülkiye Rüştiyesinde iken "
                    "mahallemizdeki Binbaşı Kadri Bey'in oğlu askerî rüştiyeye devam ediyor, "
                    "askerî üniforma giyiyordu. Onu gördükçe ben de öyle giyinmeye "
                    "hevesleniyordum. Sokaklarda subaylar görüyor, subay olmak için önce "
                    "askerî rüştiyeye girmek gerektiğini anlıyordum. Annem istemiyordu; ona "
                    "sezdirmeden sınava girdim.'\n"
                    "Bu bilgiye göre Mustafa Kemal'in askerlik mesleğine ilgi duymasında "
                    "aşağıdakilerden hangisi etkili olmuştur?\n\n"
                    "A) Ailesi\nB) Çevresi\nC) Öğretmenleri\nD) Okuduğu kitaplar"
                ),
                "answer": "B",
                "solution": (
                    "Komşu çocuğunun üniforması ve sokakta gördüğü subaylar, yani çevresi "
                    "onu askerliğe özendirmiştir. Annesi ise karşı çıkmıştır; bu yüzden "
                    "aile (A) yanlıştır. Doğru cevap B."
                ),
            },
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC_8,
                "question": (
                    "Matematikte çok başarılı olan Mustafa Kemal, yabancı dilini "
                    "ilerletmek için tatillerde Selanik'te Frerler Okuluna gitti. Okuduğu "
                    "kitaplarla Rousseau, Voltaire, Montesquieu gibi Fransız düşünürleri "
                    "tanıdı; hürriyet, bağımsızlık, adalet, eşitlik kavramlarını özümsedi.\n"
                    "Verilen metinde Mustafa Kemal ile ilgili;\n"
                    "I. Okuduğu kitapların düşünce dünyasını şekillendirdiği,\n"
                    "II. Kitap okumayı ve öğrenmeyi sevdiği,\n"
                    "III. Hedefleri için azimle çalıştığı\n"
                    "çıkarımlarından hangileri yapılabilir?\n\n"
                    "A) Yalnız I\nB) I ve II\nC) II ve III\nD) I, II ve III"
                ),
                "answer": "D",
                "solution": (
                    "Düşünürleri okuyup kavramları özümsemesi I'i, kitap okuma alışkanlığı "
                    "II'yi, tatilde ek okula gidip dilini ilerletmesi III'ü destekler; üçü de "
                    "çıkarılabilir. Doğru cevap D."
                ),
            },
        ],
        # ── Mustafa Kemal'in kişilik özellikleri ──────────────────────────
        "İTA.8.1.3": [
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC_8,
                "question": (
                    "Mustafa Kemal, 31 Mart Vakası'ndan sonra subayların siyasete "
                    "karışmasının tehlikelerini sezmiş, ordunun siyasetten uzak durması "
                    "gerektiğini savunmuştu. Nitekim Balkan Savaşları sırasında öngörüleri "
                    "gerçekleşmiş ve ordu büyük bir felaketle karşılaşmıştır.\n"
                    "Bu metinden Mustafa Kemal'in hangi kişisel özelliği çıkarılabilir?\n\n"
                    "A) İleri görüşlülüğü\nB) Eğitimciliği\nC) İdealistliği\nD) Sabırlılığı"
                ),
                "answer": "A",
                "solution": (
                    "Gelecekteki tehlikeyi önceden sezip uyarması ve öngörülerinin "
                    "gerçekleşmesi, onun ileri görüşlü (ileriyi gören) bir kişi olduğunu "
                    "gösterir. Doğru cevap A."
                ),
            },
            {
                "type": QuestionType.KAYNAK_METIN,
                "difficulty": "zor",
                "source": _SRC_8,
                "question": (
                    "Mustafa Kemal'in Vatan ve Hürriyet Cemiyeti'nin Selanik şubesi "
                    "açılışındaki konuşmasından: 'Memleketin tehlikeli anlarını hepiniz "
                    "anlarsınız. Onu kurtarmak tek hedefimizdir. Şimdilik gizli çalışmak "
                    "zorundayız. Milleti hâkim kılmak, kısaca vatanı kurtarmak için sizi "
                    "göreve çağırıyorum.'\n"
                    "Bu konuşmadan Mustafa Kemal ile ilgili aşağıdakilerden hangisine "
                    "ULAŞILAMAZ?\n\n"
                    "A) Liderlik vasfına sahip olduğuna\n"
                    "B) Millî bir ordu kurmayı amaçladığına\n"
                    "C) Bağımsızlık duygusuyla hareket ettiğine\n"
                    "D) Millî egemenlik anlayışını benimsediğine"
                ),
                "answer": "B",
                "solution": (
                    "Konuşma; liderliği (A), bağımsızlık duygusunu (C) ve 'milleti hâkim "
                    "kılma' sözüyle millî egemenliği (D) yansıtır. Millî ordu kurma hedefine "
                    "(B) dair bir ifade yoktur. Doğru cevap B."
                ),
            },
            {
                "type": QuestionType.KAYNAK_METIN,
                "difficulty": "zor",
                "source": _SRC_8,
                "question": (
                    "Mustafa Kemal, 1910'da Fransa'daki Picardie Manevraları sonrası şöyle "
                    "der: 'Bu kadar hazırlık barış için yapılmaz. Aklımızı başımıza "
                    "almalıyız. Çıkacak savaş bütün dünyayı ateşe atabilir ve biz bunun "
                    "dışında kalamayız.'\n"
                    "Bu sözlere bakılarak Mustafa Kemal ile ilgili aşağıdaki yargılardan "
                    "hangisine ULAŞILAMAZ?\n\n"
                    "A) Osmanlı'nın çıkacak bir savaşta tarafsız kalması gerektiğini "
                    "savunmuştur.\n"
                    "B) Avrupa'nın askerî hazırlıklarını tehlikeli bulmuştur.\n"
                    "C) Osmanlı'nın tedbirli olması gerektiğini vurgulamıştır.\n"
                    "D) Büyük bir savaşın yaşanabileceğini öngörmüştür."
                ),
                "answer": "A",
                "solution": (
                    "'Bunun dışında kalamayız' sözü, Osmanlı'nın savaşa gireceğini kabul "
                    "eder; bu yüzden tarafsızlık savunusu (A) metinle çelişir. Savaşı öngörme "
                    "(D), tehlike (B) ve tedbir (C) sözlerde vardır. Doğru cevap A."
                ),
            },
        ],
        # ── Birinci Dünya Savaşı'nın nedenleri ────────────────────────────
        "İTA.8.2.1": [
            {
                "type": QuestionType.KAYNAK_METIN,
                "difficulty": "orta",
                "source": _SRC_8,
                "question": (
                    "Sömürge topraklarından elde edilen zenginlik Avrupa'da refah ortamı "
                    "oluşturmuş; kömür ve demir gibi maden kaynaklarının bolluğu, sanayinin "
                    "ihtiyaç duyduğu enerji ve demiri düşük maliyetle karşılamıştır. Bu "
                    "madenlere sahip İngiltere, Almanya ve Fransa avantaj elde etmiştir.\n"
                    "Buna göre Avrupa'da Sanayi İnkılabı'nın gerçekleşmesinde;\n"
                    "I. Enerji kaynaklarının varlığı,\nII. Yeterli sermaye birikimi,\n"
                    "III. Teknolojik gelişme\n"
                    "durumlarından hangilerinin etkili olduğu söylenebilir?\n\n"
                    "A) Yalnız I\nB) I ve II\nC) II ve III\nD) I, II ve III"
                ),
                "answer": "D",
                "solution": (
                    "Maden/enerji kaynakları I'i, sömürgelerden gelen zenginlik (sermaye) "
                    "II'yi, buhar gücüyle işleyen makineler III'ü destekler; üçü de "
                    "etkilidir. Doğru cevap D."
                ),
            },
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "zor",
                "source": _SRC_8,
                "question": (
                    "Milliyetçilik düşüncesinin etkisiyle Osmanlı ve Avusturya-Macaristan "
                    "yönetimindeki milletler isyan etmişti. Rusya bu isyanları destekliyor, "
                    "ayrıca sıcak denizlere inmek için Boğazları ele geçirmek istiyordu. "
                    "Osmanlı ve Avusturya-Macaristan ise Rusya'ya karşı Almanya ile "
                    "yakınlaşmak zorunda kalmıştı.\n"
                    "Bu duruma göre milliyetçilik fikrinin aşağıdaki gelişmelerden hangisine "
                    "neden olduğu SÖYLENEMEZ?\n\n"
                    "A) Devletler arası ittifakların oluşmasına\n"
                    "B) Sömürgecilik hareketlerinin başlamasına\n"
                    "C) Balkanlarda hâkimiyet mücadelesine\n"
                    "D) Çok uluslu devletlerde bağımsızlık hareketlerine"
                ),
                "answer": "B",
                "solution": (
                    "Metin ittifaklaşmayı (A), Balkan mücadelesini (C) ve bağımsızlık "
                    "isyanlarını (D) açıklar. Sömürgeciliğin başlaması (B) milliyetçiliğin "
                    "değil ekonomik/sanayi rekabetinin sonucudur; metinde yoktur. Doğru "
                    "cevap B."
                ),
            },
            {
                "type": QuestionType.KAYNAK_METIN,
                "difficulty": "zor",
                "source": _SRC_8,
                "question": (
                    "İngiltere Kralı: 'Sanayi İnkılabı'nı ilk yapan ve en fazla sömürgeye "
                    "sahip devletiz; güçlü bir donanmamız var. Osmanlı'nın Orta Doğu petrol "
                    "alanları ilgimizi çekiyor.'\n"
                    "Rus Çarı: 'En büyük amacımız Boğazları alıp sıcak denizlere inmek. "
                    "Balkanlarda hâkimiyet kurmaya çalıştık; soydaşımız Slavları "
                    "yönlendirdik.'\n"
                    "Buna göre aşağıdakilerden hangisi İngiltere ve Rusya'nın Osmanlı "
                    "üzerindeki amaçlarından biri DEĞİLDİR?\n\n"
                    "A) Balkanlarda etkinlik/isyan hareketlerini desteklemek\n"
                    "B) Yer altı kaynaklarını ele geçirmek\n"
                    "C) Osmanlı'yı kendi yanlarında savaşa çekmek\n"
                    "D) Panslavizm politikasını gerçekleştirmek"
                ),
                "answer": "C",
                "solution": (
                    "İngiltere petrolü (B), Rusya Balkanlar-Slavlar (A, D-Panslavizm) "
                    "amaçlarını dile getirir. Osmanlı'yı yanlarında savaşa çekmekten (C) söz "
                    "edilmez. Doğru cevap C."
                ),
            },
        ],
        # ── Cephelerin savaşa etkisi ──────────────────────────────────────
        "İTA.8.2.3": [
            {
                "type": QuestionType.KAYNAK_METIN,
                "difficulty": "orta",
                "source": _SRC_8,
                "question": (
                    "İtilaf Devletleri'nin Çanakkale Cephesi'ni açma amaçları:\n"
                    "• İstanbul'u işgal ederek Osmanlı'yı teslim almak,\n"
                    "• Karadeniz'i geçerek Ruslara yardım götürmek,\n"
                    "• Savaşa girmeyen devletleri kendi yanlarına çekmek.\n"
                    "Bu amaçlar dikkate alındığında;\n"
                    "I. Rusya'nın henüz İtilaf'a katılmadığı,\n"
                    "II. Osmanlı'nın stratejik açıdan önemli bir konumda olduğu,\n"
                    "III. İtilaf'ın savaşı kısa sürede bitirmeyi hedeflediği\n"
                    "yorumlarından hangilerine ulaşılabilir?\n\n"
                    "A) Yalnız I\nB) Yalnız II\nC) II ve III\nD) I, II ve III"
                ),
                "answer": "C",
                "solution": (
                    "Ruslara yardım götürme amacı, Rusya'nın zaten İtilaf'ta olduğunu "
                    "gösterir; bu yüzden I yanlıştır. İstanbul/Boğazlar'ın hedef olması "
                    "Osmanlı'nın stratejik önemini (II), savaşı bitirme isteği kısa sürede "
                    "sonuç alma hedefini (III) verir. Doğru cevap C."
                ),
            },
        ],
        # ── Mondros'a karşı tutumlar (Osmanlı/M.Kemal/aydın/halk) ─────────
        "İTA.8.3.1": [
            {
                "type": QuestionType.KAYNAK_METIN,
                "difficulty": "orta",
                "source": _SRC_8,
                "question": (
                    "Mondros Ateşkes Antlaşması'nın bazı maddeleri:\n"
                    "• İç güvenlik için gereken dışında Osmanlı ordusu terhis edilecek.\n"
                    "• İtilaf Devletleri güvenliklerini tehdit eden stratejik noktaları işgal "
                    "edebilecek.\n"
                    "• Boğazlar İtilaf Devletlerince işgal edilecek.\n"
                    "• Telsiz, telgraf hatları ile demiryolları İtilaf denetimine bırakılacak.\n"
                    "Bu maddelerle aşağıdakilerden hangisinin amaçlandığı SÖYLENEMEZ?\n\n"
                    "A) Anadolu'da çıkabilecek azınlık isyanlarının engellenmesi\n"
                    "B) Haberleşme ve ulaşımın kontrol altına alınması\n"
                    "C) Anadolu-Rumeli bağlantısının kesilmesi\n"
                    "D) Osmanlı'nın savunmasız bırakılması"
                ),
                "answer": "A",
                "solution": (
                    "Ordunun terhisi savunmasızlığı (D), telgraf/demiryolu denetimi "
                    "haberleşme-ulaşım kontrolünü (B), Boğazların işgali bağlantının "
                    "kesilmesini (C) sağlar. Maddeler azınlık isyanlarını engellemeyi değil, "
                    "işgalleri kolaylaştırmayı amaçlar. Doğru cevap A."
                ),
            },
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC_8,
                "question": (
                    "Mondros sonrası işgaller karşısında iki görüş: Damat Ferit "
                    "Hükûmeti'ne göre işgaller geçiciydi, İtilaf'ı kızdırmamak için sessiz "
                    "kalınmalı ve uzlaşmacı olunmalıydı. Türk halkı ise cemiyetler kurarak, "
                    "telgraflar çekip mitingler düzenleyerek protesto etti ve silahlı "
                    "direniş kuvvetleri oluşturdu.\n"
                    "Verilenlerden hareketle aşağıdaki yargılardan hangisi SÖYLENEMEZ?\n\n"
                    "A) İstanbul Hükûmeti ile halk arasında görüş ayrılığı vardır.\n"
                    "B) Türk halkı vatanı korumak için teşkilatlanmıştır.\n"
                    "C) Kurtuluş için bağımsızlıktan uzak fikirler de vardır.\n"
                    "D) İstanbul Hükûmeti'ne göre milletin istiklalini milletin kararı "
                    "kurtaracaktır."
                ),
                "answer": "D",
                "solution": (
                    "İki görüş görüş ayrılığını (A), halkın direnişi teşkilatlanmayı (B), "
                    "hükûmetin uzlaşmacılığı bağımsızlıktan uzak fikri (C) gösterir. "
                    "'Milletin istiklalini milletin kararı kurtarır' anlayışı İstanbul "
                    "Hükûmeti'ne değil Millî Mücadele'ye aittir. Doğru cevap D."
                ),
            },
        ],
        # ── Millî Mücadele hazırlık dönemi (genelge/kongre/cemiyet) ───────
        "İTA.8.3.2": [
            {
                "type": QuestionType.KAYNAK_METIN,
                "difficulty": "orta",
                "source": _SRC_8,
                "question": (
                    "Erzurum Kongresi kararlarından bazıları:\n"
                    "• Millî sınırlar içinde vatan bir bütündür, bölünemez.\n"
                    "• Kuvâ-yı Millîye'yi tek kuvvet tanımak ve millî iradeyi hâkim kılmak "
                    "esastır.\n"
                    "• Manda ve himaye kabul edilemez.\n"
                    "Bu kararlardan hareketle aşağıdakilerden hangisi SÖYLENEMEZ?\n\n"
                    "A) Yeni bir yönetim anlayışına işaret edilmiştir.\n"
                    "B) Osmanlı Hükûmeti'nin denetlenmesi amaçlanmıştır.\n"
                    "C) Vatanın bütünlüğü ilkesine vurgu yapılmıştır.\n"
                    "D) Tam bağımsızlık (manda reddi) ilkesi dile getirilmiştir."
                ),
                "answer": "B",
                "solution": (
                    "'Millî irade' millî egemenlik/yeni anlayışı (A), 'vatan bir bütündür' "
                    "bütünlüğü (C), manda-himaye reddi bağımsızlığı (D) gösterir. Osmanlı "
                    "Hükûmeti'nin denetlenmesine dair karar yoktur. Doğru cevap B."
                ),
            },
            {
                "type": QuestionType.KAYNAK_METIN,
                "difficulty": "orta",
                "source": _SRC_8,
                "question": (
                    "Sivas Kongresi kararlarından bazıları:\n"
                    "• Manda ve himaye kesin olarak reddedilmiştir.\n"
                    "• Yurttaki tüm cemiyetler 'Anadolu ve Rumeli Müdafaa-i Hukuk Cemiyeti' "
                    "adı altında birleştirilmiştir.\n"
                    "• Temsil Heyeti genişletilerek bütün ulus adına söz söyleme yetkisi "
                    "verilmiştir.\n"
                    "Kongre kararlarına göre;\n"
                    "I. Temsil Heyeti bütün vatanı temsil eder hâle gelmiştir.\n"
                    "II. Ulusal örgütlenme tüm vatanı kapsayacak biçimde genişletilmiştir.\n"
                    "III. Tam bağımsızlık hedeflenmiştir.\n"
                    "yargılarından hangilerine ulaşılabilir?\n\n"
                    "A) I ve II\nB) I ve III\nC) II ve III\nD) I, II ve III"
                ),
                "answer": "D",
                "solution": (
                    "Temsil Heyeti'nin bütün ulus adına yetkilendirilmesi I'i, cemiyetlerin "
                    "tek çatıda birleştirilmesi II'yi, manda-himaye reddi tam bağımsızlığı "
                    "(III) verir; üçü de doğrudur. Doğru cevap D."
                ),
            },
            {
                "type": QuestionType.KAYNAK_METIN,
                "difficulty": "orta",
                "source": _SRC_8,
                "question": (
                    "Amasya Genelgesi'nin öne çıkan maddeleri: 'Vatanın bütünlüğü, milletin "
                    "bağımsızlığı tehlikededir. Osmanlı Hükûmeti üzerine aldığı sorumluluğu "
                    "yerine getirememektedir. Milletin bağımsızlığını yine milletin azim ve "
                    "kararı kurtaracaktır.' Genelge, birkaç komutanın görüş ve onayı "
                    "alınarak hazırlanmıştır.\n"
                    "Metne göre Amasya Genelgesi ile ilgili aşağıdakilerden hangisine "
                    "ULAŞILAMAZ?\n\n"
                    "A) Osmanlı hükûmet üyeleri değiştirilmiştir.\n"
                    "B) Millî Mücadele'nin gerekçesi belirtilmiştir.\n"
                    "C) Genelge kararları kişisellikten çıkarılmıştır.\n"
                    "D) Millî Mücadele'nin yol haritası belirlenmiştir."
                ),
                "answer": "A",
                "solution": (
                    "Tehlike vurgusu gerekçeyi (B), birden çok komutanın onayı "
                    "kişisellikten çıkarmayı (C), 'milletin kararı kurtaracaktır' sözü yol "
                    "haritasını (D) verir. Hükûmet üyelerinin değiştirilmesine dair bilgi "
                    "yoktur. Doğru cevap A."
                ),
            },
        ],
        # ── Millî Mücadele siyasi/askerî gelişmeleri ──────────────────────
        "İTA.8.3.3": [
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC_8,
                "question": (
                    "23 Nisan 1920'de açılan TBMM; ulusal bağımsızlığı öngördüğü için İtilaf "
                    "Devletleri'ni, ulusal egemenliği öngördüğü için Osmanlı yönetimini "
                    "rahatsız etti. Bunlar halkı TBMM'ye karşı kışkırttı ve Anadolu'da "
                    "isyanlar çıktı. TBMM ayaklanmaları bastırmayı başardı.\n"
                    "Buna göre;\n"
                    "I. TBMM'yi yıpratmak için girişimlerde bulunulmuştur.\n"
                    "II. Ayaklanmaların bastırılması TBMM'nin otoritesini güçlendirmiştir.\n"
                    "III. İstanbul Hükûmeti ve İtilaf, TBMM'nin karşısında yer almıştır.\n"
                    "yargılarından hangilerine ulaşılabilir?\n\n"
                    "A) Yalnız I\nB) I ve III\nC) II ve III\nD) I, II ve III"
                ),
                "answer": "D",
                "solution": (
                    "Kışkırtma girişimleri I'i, isyanların bastırılıp otorite kurulması "
                    "II'yi, hem İstanbul hem İtilaf'ın rahatsızlığı III'ü destekler; üçü de "
                    "doğrudur. Doğru cevap D."
                ),
            },
            {
                "type": QuestionType.KAYNAK_METIN,
                "difficulty": "orta",
                "source": _SRC_8,
                "question": (
                    "Bazı milletvekilleri taarruzun hemen yapılmasını isterken Mustafa "
                    "Kemal onları şöyle yatıştırdı: 'Ordumuzun kararı taarruzdur; fakat bu "
                    "taarruzu erteliyoruz. Sebebi, hazırlığımızı tamamen tamamlamaya biraz "
                    "daha zaman gerekmesidir. Yarım hazırlıkla yapılacak taarruz, hiç "
                    "taarruz etmemekten daha kötüdür.'\n"
                    "Buna göre Mustafa Kemal'in taarruzu ertelemesinin sebebi nedir?\n\n"
                    "A) Milletvekillerinin isteklerini yerine getirmek\n"
                    "B) Savunma savaşı yapmak\n"
                    "C) Taarruzu yaz aylarında yapmak\n"
                    "D) Ordunun eksiklerini tamamlamak"
                ),
                "answer": "D",
                "solution": (
                    "'Hazırlığımızı tamamlamaya zaman gerek' ve 'yarım hazırlıkla taarruz "
                    "kötüdür' sözleri, ertelemenin nedeninin ordunun eksiklerini tamamlamak "
                    "olduğunu gösterir. Doğru cevap D."
                ),
            },
            {
                "type": QuestionType.KAYNAK_METIN,
                "difficulty": "orta",
                "source": _SRC_8,
                "question": (
                    "İsmet Bey I. İnönü Savaşı ile ilgili Meclise şu telgrafı gönderdi: "
                    "'Askerlerimiz aralıksız düşman taarruzlarını bir an gerilemeksizin "
                    "göğüslüyor, Yunanların ilerlemesine imkân bırakmıyorlardı. Sonunda "
                    "tükenen, gücü kırılan düşman oldu; taarruzlarından sonuç alamayacağını "
                    "anladı ve geri çekildi.'\n"
                    "Verilen bilgiye göre aşağıdaki çıkarımlardan hangisi yapılabilir?\n\n"
                    "A) Millî Mücadele'nin askerî safhası sona ermiştir.\n"
                    "B) Yunan ordusu Anadolu'yu boşaltma kararı almıştır.\n"
                    "C) Başarılı bir savunma yapan Türk ordusu zafer kazanmıştır.\n"
                    "D) Türk ordusu kısa sürede tüm kayıplarını telafi etmiştir."
                ),
                "answer": "C",
                "solution": (
                    "Telgraf, düşman taarruzlarının göğüslenip püskürtüldüğü başarılı bir "
                    "savunma zaferini anlatır. Savaşın veya işgalin sona erdiğine (A, B) dair "
                    "bilgi yoktur. Doğru cevap C."
                ),
            },
        ],
        # ── Türk milletinin Millî Mücadele'deki rolü ──────────────────────
        "İTA.8.3.4": [
            {
                "type": QuestionType.KAYNAK_METIN,
                "difficulty": "zor",
                "source": _SRC_8,
                "question": (
                    "Mustafa Kemal 'Söylev'de Millî Mücadele ruhunu şöyle anlatır: 'Millet "
                    "fertleri; yalnız düşman karşısında bulunanlar değil, köyünde, evinde, "
                    "tarlasında bulunan herkes silahla vuruşan savaşçı gibi kendini vazifeli "
                    "sayarak bütün varlığını mücadeleye verecekti. Bunu ağır davranarak "
                    "yapan milletler, başarabileceklerine inanmış sayılmazlar.'\n"
                    "Bu sözlerden hareketle aşağıdakilerden hangisine ulaşılabilir?\n\n"
                    "A) Vatan savunmasında maddi imkânlara öncelik verilmelidir.\n"
                    "B) Halk çatışma bölgelerinden uzak güvenli alanlara taşınmalıdır.\n"
                    "C) Düşman karşısında yalnız askerî birliklerin mücadelesi yeterlidir.\n"
                    "D) Topyekûn mücadeleyi benimseyen milletler başarılı olur."
                ),
                "answer": "D",
                "solution": (
                    "Herkesin -asker olsun olmasın- kendini vazifeli sayması, tüm milletin "
                    "katıldığı topyekûn mücadeleyi anlatır. Bu yüzden yalnız ordunun "
                    "yeterliliği (C) reddedilir. Doğru cevap D."
                ),
            },
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC_8,
                "question": (
                    "Millî Mücadele'de Türk kadını; işgallere karşı dernekler kurmuş, "
                    "mitingler düzenlemiş, ordu ve kimsesizler için yardım toplamış, cephane "
                    "imalathanelerinde çalışmış ve kağnılarla cepheye erzak-cephane "
                    "taşımıştır.\n"
                    "Buna göre Türk kadınının yaptığı faaliyetlerle ilgili aşağıdakilerden "
                    "hangisi SÖYLENEMEZ?\n\n"
                    "A) Anadolu'daki azınlıkların haklarını savunmuşlardır.\n"
                    "B) Cephe gerisinde faaliyetlerde bulunmuşlardır.\n"
                    "C) Millî bilincin uyandırılması için çalışmışlardır.\n"
                    "D) İşgallere karşı örgütlenmişlerdir."
                ),
                "answer": "A",
                "solution": (
                    "Yardım toplamak ve cepheye taşımak cephe gerisi faaliyetini (B), "
                    "miting/dernek millî bilinç ve örgütlenmeyi (C, D) gösterir. Azınlık "
                    "haklarını savunmaya (A) dair bilgi yoktur. Doğru cevap A."
                ),
            },
        ],
        # ── Cumhuriyet'in ilanına kadar geçen süreç (Lozan/başkent/ilan) ──
        "İTA.8.4.1": [
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC_8,
                "question": (
                    "Türkiye, Lozan Konferansı'nda şu isteklerde bulunmuştur:\n"
                    "• Kapitülasyonlar ve Düyun-u Umumiye İdaresi'nin kaldırılması,\n"
                    "• İstanbul ve Boğazların boşaltılması,\n"
                    "• Yunanistan'ın tazminat ödemesi.\n"
                    "Türkiye'nin bu isteklerle aşağıdakilerden hangisini amaçladığı "
                    "SÖYLENEMEZ?\n\n"
                    "A) Savaşın verdiği ekonomik zararı telafi etmeyi\n"
                    "B) Ekonomik bağımlılığı ortadan kaldırmayı\n"
                    "C) Toprak bütünlüğünü sağlamayı\n"
                    "D) Mevcut sınırlarını genişletmeyi"
                ),
                "answer": "D",
                "solution": (
                    "Tazminat isteği zararı telafiyi (A), kapitülasyon/Düyun-u Umumiye'nin "
                    "kaldırılması ekonomik bağımsızlığı (B), boşaltma istekleri bütünlüğü (C) "
                    "amaçlar. İstekler yeni topraklar (sınır genişletme) içermez. Doğru "
                    "cevap D."
                ),
            },
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC_8,
                "question": (
                    "Lozan'dan sonra Ankara başkent ilan edildi. Devlet başkanlığı fiilen "
                    "TBMM Başkanı olarak Atatürk tarafından yürütülüyordu. Fethi Bey'in "
                    "istifasıyla hükûmetin kurulmasında sistem sorunu belirginleşti; meclis "
                    "hükûmeti sisteminden kabine sistemine geçilmesi kararlaştırıldı ve 29 "
                    "Ekim 1923'te Cumhuriyet ilan edildi.\n"
                    "Bu bilgilere göre Cumhuriyet'in ilan edilme nedenleri arasında "
                    "aşağıdakilerden hangisi YER ALMAZ?\n\n"
                    "A) Devlet başkanlığı sorununun yaşanması\n"
                    "B) Rejimin adının henüz konulmamış olması\n"
                    "C) Hükûmet bunalımının ortaya çıkması\n"
                    "D) Başkent meselesinin krize dönüşmesi"
                ),
                "answer": "D",
                "solution": (
                    "Metinde devlet başkanlığı (A), rejimin adının konulması ihtiyacı (B) ve "
                    "hükûmet bunalımı (C) nedenler arasındadır. Ankara başkent ilan edilmiş, "
                    "başkent bir kriz olmamıştır. Doğru cevap D."
                ),
            },
            {
                "type": QuestionType.KAYNAK_METIN,
                "difficulty": "orta",
                "source": _SRC_8,
                "question": (
                    "İsmet Paşa, Ankara'nın başkent yapılma nedenlerini şöyle anlatır: "
                    "'Boğazlar askerî bakımdan tamamen açık ve emniyetsiz; Lozan'ın "
                    "sonuçları ve tarihî şartlar bizi endişeye sevk ediyor. Ayrıca "
                    "Anadolu'nun ortasında bir Anadolu Hükûmeti olarak yeni devleti "
                    "çalıştırmak istiyoruz.'\n"
                    "Buna göre Ankara'nın başkent seçilmesinde;\n"
                    "I. siyasi,\nII. ekonomik,\nIII. jeopolitik (güvenlik-konum)\n"
                    "nedenlerinden hangileri etkili olmuştur?\n\n"
                    "A) Yalnız I\nB) I ve III\nC) II ve III\nD) I, II ve III"
                ),
                "answer": "B",
                "solution": (
                    "'Yeni devleti Anadolu ortasından yönetmek' siyasi (I); Boğazların "
                    "emniyetsizliği ve Anadolu'nun ortasında güvenli konum jeopolitik (III) "
                    "nedendir. Ekonomik bir gerekçeden (II) söz edilmez. Doğru cevap B."
                ),
            },
        ],
        # ── Atatürk inkılapları (neden-sonuç) ─────────────────────────────
        "İTA.8.4.2": [
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC_8,
                "question": (
                    "Tevhid-i Tedrisat Kanunu'ndan sonra 1925'te yabancı okullarda; tarih, "
                    "coğrafya, yurttaşlık derslerinin Türk öğretmenlerce okutulması, Türk "
                    "müfettişlerce denetlenmesi ve derslerde Türklük aleyhine ifadelere yer "
                    "verilmemesi kararlaştırıldı.\n"
                    "Buna göre Türkiye'nin yabancı okullar konusundaki tutumuyla "
                    "aşağıdakilerden hangisini amaçladığı söylenebilir?\n\n"
                    "A) Eğitim kalitesini artırmayı\nB) Okulların kapatılmasını\n"
                    "C) Millî kültüre zarar verilmesini önlemeyi\n"
                    "D) Yalnızca laik eğitim yapılmasını"
                ),
                "answer": "C",
                "solution": (
                    "Türkçe derslerin Türk öğretmenlerce verilmesi, denetim ve Türklük "
                    "aleyhine ifadelerin yasaklanması, millî kültürün korunmasını ve zarar "
                    "görmesinin önlenmesini amaçlar. Okulların kapatılması (B) istenmemiştir. "
                    "Doğru cevap C."
                ),
            },
            {
                "type": QuestionType.KAYNAK_METIN,
                "difficulty": "orta",
                "source": _SRC_8,
                "question": (
                    "Atatürk 1923 İzmir konuşmasında: 'Bizim toplumumuz için ilim ve fen "
                    "gerekli ise bunları aynı derecede hem erkek hem de kadınlarımızın elde "
                    "etmesi gerekir. Kadınlarımız erkeklerin geçtiği bütün öğretim "
                    "basamaklarından geçecek; toplum yaşamında erkeklerle birlikte "
                    "yürüyerek birbirinin yardımcısı olacaklardır.'\n"
                    "Bu sözlerle Atatürk;\n"
                    "I. Kadınların eğitimine önem verilmesini,\n"
                    "II. Kadın-erkek eşitliğine yönelik adımları,\n"
                    "III. Kadının sosyal hayata aktif katılımını\n"
                    "amaçlarından hangilerini istemiştir?\n\n"
                    "A) I ve II\nB) I ve III\nC) II ve III\nD) I, II ve III"
                ),
                "answer": "D",
                "solution": (
                    "'İlim/fen kadınlar için de gerekli' I'i, 'aynı öğretim basamakları' "
                    "eşitliği II'yi, 'toplum yaşamında erkeklerle birlikte' sosyal katılımı "
                    "III'ü destekler; üçü de amaçlanır. Doğru cevap D."
                ),
            },
            {
                "type": QuestionType.KAYNAK_METIN,
                "difficulty": "zor",
                "source": _SRC_8,
                "question": (
                    "Atatürk, İzmir İktisat Kongresi'nin açılışında: 'Yeni Türkiye'yi hak "
                    "ettiği yüksek düzeye ulaştırmak için zaman kaybetmeden ekonomimize "
                    "öncelik vermek zorundayız; çünkü günümüz bütünüyle ekonomi çağıdır.' "
                    "dedi.\n"
                    "Aşağıdakilerden hangisi Atatürk'ün bu sözü doğrultusunda alınan "
                    "kararlardan biri OLAMAZ?\n\n"
                    "A) Yabancı yatırımların tamamen engellenmesi\n"
                    "B) Aşar vergisinin kaldırılması\n"
                    "C) Özel girişimcilere kredi imkânı verilmesi\n"
                    "D) Vergi sisteminin çağın gereklerine uygun düzenlenmesi"
                ),
                "answer": "A",
                "solution": (
                    "Aşarın kaldırılması, girişimciye kredi ve vergi düzenlemesi ekonomiyi "
                    "geliştirmeye yöneliktir. Ekonomik kalkınmayı önemseyen bir anlayış "
                    "yabancı yatırımı tamamen engellemez; A bu sözle bağdaşmaz. Doğru cevap A."
                ),
            },
        ],
        # ── Atatürk ilke ve inkılapları arasındaki ilişki ─────────────────
        "İTA.8.4.3": [
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC_8,
                "question": (
                    "Halkçılık; bütün vatandaşların yasalar önünde eşit olmasını, devlet "
                    "imkânlarından eşit yararlanmasını esas alan ve her türlü ayrımcılığı "
                    "reddeden Atatürk ilkesidir.\n"
                    "Buna göre aşağıdaki uygulamalardan hangisi halkçılık ilkesine göre "
                    "hareket edildiğinin göstergesidir?\n\n"
                    "A) Millî kültürün korunması ve geliştirilmesi\n"
                    "B) Büyük yatırımların devlet tarafından yapılması\n"
                    "C) Bilimsel ve teknolojik gelişmelerin takip edilmesi\n"
                    "D) Kadınlara erkeklerle aynı sosyal ve ekonomik hakların sağlanması"
                ),
                "answer": "D",
                "solution": (
                    "Halkçılık eşitlik ve ayrımcılığın reddi demektir. Kadın-erkek eşitliği "
                    "doğrudan bu eşitlik anlayışının uygulamasıdır. A milliyetçilik, B "
                    "devletçilik, C inkılapçılıkla ilgilidir. Doğru cevap D."
                ),
            },
            {
                "type": QuestionType.KAYNAK_METIN,
                "difficulty": "orta",
                "source": _SRC_8,
                "question": (
                    "Atatürk'ün, güreşçi Kurtdereli Mehmet Efendi'ye mektubundan: 'Parlak "
                    "başarılarının sırrını, güreşirken bütün milletini arkanda hissetmene "
                    "ve milletinin şerefini korumak için her şeyi yapmana bağladığını "
                    "öğrendim. Bunu en az başarıların kadar beğendim; bu sözünün Türk "
                    "sporcularına bir meslek ilkesi olmasını diliyorum.'\n"
                    "Bu mektuba göre Atatürk, Türk sporcularına aşağıdakilerden hangisini "
                    "tavsiye etmektedir?\n\n"
                    "A) Sporun yalnızca yeteneğe bağlı kalmasını\n"
                    "B) Sporcunun millî heyecan içinde yetişmesini\n"
                    "C) Sporun sadece başarıyı esas almasını\n"
                    "D) Güreşe diğer sporlardan daha fazla önem verilmesini"
                ),
                "answer": "B",
                "solution": (
                    "Atatürk, 'milletini arkanda hissetme' ve 'milletin şerefini koruma' "
                    "sözünü örnek göstererek sporcunun millî duygu ve heyecanla yetişmesini "
                    "tavsiye eder. Doğru cevap B."
                ),
            },
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC_8,
                "question": (
                    "Cumhuriyetçilik ilkesi; halk egemenliğini esas alan, yöneticilerin "
                    "halk tarafından belli bir süre için seçilmesini sağlayan ve cumhuriyet "
                    "rejimini ön plana çıkaran Atatürk ilkesidir.\n"
                    "Buna göre cumhuriyetçilik ilkesi için;\n"
                    "I. Ülke yönetiminde tek kişinin egemenliğini reddeder.\n"
                    "II. Halkın yönetimde söz sahibi olmasını savunur.\n"
                    "III. Seçimlerin belli aralıklarla yapılmasını öngörür.\n"
                    "yargılarından hangilerine ulaşılabilir?\n\n"
                    "A) Yalnız I\nB) I ve II\nC) II ve III\nD) I, II ve III"
                ),
                "answer": "D",
                "solution": (
                    "Halk egemenliği tek kişi egemenliğini reddeder (I) ve halkı söz sahibi "
                    "yapar (II); yöneticinin 'belli bir süre için' seçilmesi düzenli "
                    "seçimleri (III) gerektirir. Üçü de doğrudur. Doğru cevap D."
                ),
            },
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "zor",
                "source": _SRC_8,
                "question": (
                    "Devletçilik; o günün ihtiyaçlarından doğan, Türkiye'nin koşullarına "
                    "uygun, iktisadi ve sosyal kalkınmayı öngören; özel mülkiyete de yer "
                    "veren ve teşebbüs hürriyetini savunan bir ekonomik modeldir.\n"
                    "Bu bilgilere göre aşağıdakilerden hangisinin devletçilik ilkesiyle "
                    "ilgili olduğu SÖYLENEMEZ?\n\n"
                    "A) Ekonomik kalkınmayı hedeflemesi\n"
                    "B) Özel sektöre yatırım fırsatı sunması\n"
                    "C) Yabancı sermayeyi teşvik etmesi\n"
                    "D) Toplumun ihtiyaçlarından ortaya çıkması"
                ),
                "answer": "C",
                "solution": (
                    "Tanım; kalkınmayı (A), özel mülkiyet-teşebbüs hürriyetini (B) ve o "
                    "günün ihtiyaçlarından doğmayı (D) içerir. Yabancı sermayenin teşvikine "
                    "(C) dair bir ifade yoktur. Doğru cevap C."
                ),
            },
        ],
    },
}
