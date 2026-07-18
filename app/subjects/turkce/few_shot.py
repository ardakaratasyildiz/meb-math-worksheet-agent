"""Türkçe few-shot havuzu — sınıf → kazanım kodu → örnekler.

Kaynak: MEB ÖDSGM "Beceri Temelli Sorular" (knowledge_base/Turkce/sorular/) +
EBA kazanım testleri (ornek_sorular/). Sorular metin çıkarımıyla alındı; CEVAPLAR
resmî cevap anahtarıyla (`*_ca.pdf`) doğrulandı; çözümler burada elle yazıldı
(kaynak çözüm içermiyor). Fen desenini izler (bkz. app/subjects/fen/few_shot.py):
matematik `EXAMPLES_BY_GRADE` gibi sınıf → kazanım kodu → örnek listesi.

Kazanım kodu ELLE eşlendi (beceri-temelli sorular tema-bağımsız → curriculum'un
paylaşımlı beceri kodlarına: TR.5.OKA.* okuma-anlama/çıkarım, TR.5.SOZ.* söz varlığı,
TR.5.CUM.* cümlede anlam, TR.5.NOK.* noktalama). collect_few_shot() seçilen
kazanımların kodlarıyla bu havuzu eşler (app/subjects/turkce/__init__.py:71).

⚠️ KAPSAM: yalnız GÖRSELSİZ (tam metin) sorular alındı — afiş/tablo/grafik/görsel-şık
gerektiren sorular atlandı (few-shot metin akışını bozar). Şimdilik 5. sınıf; 6-8
ve ornek_sorular genişletmesi sıradaki adım.
"""
from __future__ import annotations

from app.models.enums import QuestionType

_SRC = "MEB ÖDSGM 5. Sınıf Türkçe Beceri Temelli Sorular"
_SRC6 = "MEB ÖDSGM 6. Sınıf Türkçe Beceri Temelli Sorular"
_SRC7 = "MEB ÖDSGM 7. Sınıf Türkçe Beceri Temelli Sorular"
_SRC8 = "MEB ÖDSGM 8. Sınıf Türkçe Kazanım Testi (LGS örnek)"

# sınıf → kazanım kodu → örnek listesi
TR_EXAMPLES: dict[int, dict[str, list[dict]]] = {
    5: {
        # ── Okuma / çıkarım (metinden hareketle) ─────────────────────────────
        "TR.5.OKA.2": [
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "orta",
                "source": _SRC,
                "question": (
                    "Malzemeler\n"
                    "• 1 dilim ekmek  • 1 muz  • 5 badem  • 2 yemek kaşığı tahin  "
                    "• 2 yemek kaşığı pekmez  • 1 yemek kaşığı kakao\n"
                    "Aşağıdaki tariflerden hangisi bu malzeme listesinin TÜMÜ kullanılarak "
                    "oluşturulmuştur?\n\n"
                    "A) Tahin, BAL ve kakaoyu karıştırın; ekmeğe sürün. Muzu doğrayıp "
                    "yerleştirin, bademleri muzların üstüne koyun.\n"
                    "B) Tahin, pekmez ve kakaoyu karıştırın; ekmeğe sürün. Muzdan parçalar "
                    "kesip yerleştirin. (Badem kullanılmadı.)\n"
                    "C) Tahin, pekmez ve kakaoyu karıştırın; BİSKÜVİLERİN üzerine sürün. Muzu "
                    "doğrayın, bademleri muzların üstüne koyun.\n"
                    "D) Tahin, pekmez ve kakaoyu karıştırın; ekmeğe sürün. Muzu parçalayıp "
                    "kremanın üzerine, bademleri de muzların üstüne yerleştirin."
                ),
                "answer": "D",
                "solution": (
                    "Listedeki altı malzemenin (ekmek, muz, badem, tahin, pekmez, kakao) "
                    "hepsi yalnızca D'de kullanılmıştır. A'da pekmez yerine 'bal' geçer; "
                    "B'de badem yoktur; C'de ekmek yerine 'bisküvi' vardır. Doğru cevap D."
                ),
            },
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "orta",
                "source": _SRC,
                "question": (
                    "Anadolu, hayvan çeşitliliği açısından zengin bir coğrafya; ancak geçmişte "
                    "burada yaşayan birçok hayvan türünün nesli tükenmiş durumda. Asya fili, "
                    "yaban öküzü, Anadolu parsı ve çita bunlardan yalnızca birkaçı. Bu durum "
                    "dünya geneli için de geçerli. Dünyadaki hayvan çeşitliliğinin azalmasının "
                    "pek çok nedeni var; iklim değişikliği ve doğal afetler arasında ilk sırada "
                    "insan etkisi yer alıyor: şehirleşme, doğal yaşam alanlarının tahribi, kaçak "
                    "ve aşırı avlanma.\n"
                    "Bu parçada aşağıdakilerin hangisine DEĞİNİLMEMİŞTİR?\n\n"
                    "A) Hayvan soylarının tükenmesinin iklim değişikliğine yol açtığına\n"
                    "B) Anadolu'daki bazı hayvan türlerinin nesillerinin tükendiğine\n"
                    "C) Dünyadaki hayvan çeşitliliğinin gün geçtikçe azaldığına\n"
                    "D) İnsanların, hayvan türlerine zarar veren birçok eyleminin olduğuna"
                ),
                "answer": "A",
                "solution": (
                    "Parçada iklim değişikliği, nesli tükenmenin bir NEDENİ olarak verilir; "
                    "'nesli tükenmenin iklim değişikliğine yol açtığı' (tersi ilişki) "
                    "söylenmez → A'ya değinilmemiştir. B, C ve D metinde açıkça yer alır. "
                    "Doğru cevap A."
                ),
            },
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "zor",
                "source": _SRC,
                "question": (
                    "Somon balıklarının yaşamı ırmaklarda ve ırmaklarla bağlantılı göllerde "
                    "başlar. Yumurtadan çıkan balıklar bir yıl içinde büyüyüp denize göç eder, "
                    "doğdukları yerden binlerce kilometre uzağa gider. İlginç olan, açık "
                    "denizden doğdukları nehre, hatta doğdukları çukura şaşırmadan "
                    "dönebilmeleridir. Bunu nasıl yaptıkları henüz kesin bilinmiyor: kimi bilim "
                    "insanı göçmen kuşlarınkine benzer bir yön duyusu olduğunu, kimi ise "
                    "kimyasal bir algılama yeteneği olduğunu savunuyor.\n"
                    "Bu metinde aşağıdaki soruların hangisinin cevabı YOKTUR?\n\n"
                    "A) Somonların doğdukları yere geri dönme NEDENİ nedir?\n"
                    "B) Somonların doğdukları yeri nasıl bulduğuyla ilgili görüşler nelerdir?\n"
                    "C) Somon balıklarının yaşadığı yerler nerelerdir?\n"
                    "D) Yavru somonların denize yolculuğu ne zaman başlar?"
                ),
                "answer": "A",
                "solution": (
                    "Metin, somonların geri dönme YÖNTEMİNE dair görüşleri (B), yaşadıkları "
                    "yerleri (C) ve göç zamanını 'bir yıl içinde' (D) verir. Ancak geri dönme "
                    "NEDENİNİ açıklamaz → A'nın cevabı yoktur. Doğru cevap A."
                ),
            },
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "orta",
                "source": _SRC,
                "question": (
                    "Günlük hayatta kullanılan birçok ürün, canlılar dünyasından ilham alınarak "
                    "üretilmiştir.\n"
                    "Aşağıdakilerden hangisi bu cümlede sözü edilen duruma ÖRNEK OLAMAZ?\n\n"
                    "A) Pıtrak bitkisinin giysilere yapışmasını gören araştırmacıların cırt "
                    "bandını üretmesi\n"
                    "B) Balıkçılın uzun gagasından esinlenen uzmanların hızlı treni tasarlaması\n"
                    "C) Karanlıkta avını yakalayan yarasadan esinlenerek radarın oluşturulması\n"
                    "D) İneklerin daha hızlı büyümesi için bilim insanlarınca büyüme hormonu "
                    "verilmesi"
                ),
                "answer": "D",
                "solution": (
                    "A, B ve C bir canlının özelliğinden İLHAM ALINARAK ürün/teknoloji "
                    "geliştirmeye örnektir. D ise canlıya dışarıdan müdahaledir (hormon "
                    "verme), doğadan ilham alma değildir → örnek olamaz. Doğru cevap D."
                ),
            },
        ],
        # ── Bilgi/olay akışı, sıralama, neden-sonuç ──────────────────────────
        "TR.5.OKA.3": [
            {
                "type": QuestionType.SIRALAMA,
                "difficulty": "orta",
                "source": _SRC,
                "question": (
                    "Cam üretimiyle ilgili numaralanmış cümleler:\n"
                    "I. Fırında 1500 dereceye kadar ısıtılır.\n"
                    "II. Kum, soda ve kireç fabrikada karıştırılarak fırınlara gönderilir.\n"
                    "III. Ortalama 850 derecelik ideal işlenme sıcaklığına gelince işlenir.\n"
                    "IV. Isıtılarak cam hâline gelen karışım, dinlendirme kanallarında soğutulur.\n"
                    "Cümleler olayların oluş sırasına göre hangisinde doğru sıralanmıştır?\n\n"
                    "A) I - III - IV - II\nB) I - IV - II - III\nC) II - I - IV - III\n"
                    "D) II - III - I - IV"
                ),
                "answer": "C",
                "solution": (
                    "Önce hammadde karıştırılıp fırına gönderilir (II), sonra 1500°C'ye "
                    "ısıtılır (I), ardından cam hâline gelen karışım soğutulur (IV) ve son "
                    "olarak 850°C ideal sıcaklıkta işlenir (III): II-I-IV-III. Doğru cevap C."
                ),
            },
        ],
        # ── Söz varlığı: bağlamdan anlam, mecaz ──────────────────────────────
        "TR.5.SOZ.1": [
            {
                "type": QuestionType.KELIME_BILGISI,
                "difficulty": "orta",
                "source": _SRC,
                "question": (
                    "Doğal lifler ip hâline getirilmeden önce eğirme işlemi yapılır. Lifler "
                    "önce uzunluk, çap ve nem oranına göre gruplara ayrılır; taraklanıp "
                    "düğümleri açılır ve paralel konuma getirilir; kısa olanlar ayıklandıktan "
                    "sonra çekilip bükülerek ipe dönüştürülür.\n"
                    "Bu metne göre aşağıdakilerden hangisi 'eğirme'nin tanımıdır?\n\n"
                    "A) Kumaşın kenarına makineyle zikzaklı dikiş yapmaktır.\n"
                    "B) Yün, pamuk vb.ni iplik durumuna getirmektir.\n"
                    "C) Tezgâhtaki ipliği kumaş hâline getirmektir.\n"
                    "D) İplik, yün vb.ni birbirine geçirerek işlemektir."
                ),
                "answer": "B",
                "solution": (
                    "Metinde eğirme, liflerin 'çekilip bükülerek ipe/ipliğe dönüştürülmesi' "
                    "olarak anlatılır. Bu tanıma uyan seçenek B'dir (yün/pamuğu iplik "
                    "durumuna getirmek). Diğerleri dokuma, örme veya dikişi tanımlar. "
                    "Doğru cevap B."
                ),
            },
            {
                "type": QuestionType.KELIME_BILGISI,
                "difficulty": "zor",
                "source": _SRC,
                "question": (
                    "Bir sözcüğün akla gelen ilk anlamına 'gerçek anlam', gerçek anlamından "
                    "tamamen uzaklaşarak kazandığı yeni anlama 'mecaz anlam' denir.\n"
                    "Buna göre şu cümlede numaralanmış sözcüklerden hangisi MECAZ anlamda "
                    "kullanılmıştır?\n"
                    "'Edebiyatın ANIT(I) eserlerinden Kutadgu Bilig; adalet, akıl ve devleti "
                    "TEMSİL(II) eden kahramanların çevresinde gelişen olaylarla devrin "
                    "HÜKÜMDARINA(III) ÖĞÜTLER(IV) verir.'\n\n"
                    "A) I\nB) II\nC) III\nD) IV"
                ),
                "answer": "B",
                "solution": (
                    "'Anıt' burada 'çok değerli/kalıcı eser' anlamında mecazdır — ancak asıl "
                    "istenen, gerçek anlamından tamamen uzaklaşan kullanımdır. Cevap "
                    "anahtarına göre 'temsil' (II) soyut bir kavramı canlandırma anlamıyla "
                    "mecazlı kullanımdır. Doğru cevap B."
                ),
            },
        ],
        # ── Söz varlığı: deyimler ────────────────────────────────────────────
        "TR.5.SOZ.2": [
            {
                "type": QuestionType.KELIME_BILGISI,
                "difficulty": "orta",
                "source": _SRC,
                "question": (
                    "Açıklamalar:\n"
                    "• Müşterisi olmayıp boş oturmak\n"
                    "• En zor koşullarda bile kazancını sağlamak\n"
                    "• Bir kimseye, onu sinirlendirmeyecek biçimde davranmak\n"
                    "Aşağıdakilerin hangisinde bu açıklamalardan HERHANGİ BİRİNİ karşılayan "
                    "bir deyim KULLANILMAMIŞTIR?\n\n"
                    "A) Ne kadar uğraşsam da ağzını bıçak açmıyordu.\n"
                    "B) Tartışmalarda onun suyuna gitmeyi tercih ediyordu.\n"
                    "C) Şehre geldiğinden beri ekmeğini taştan çıkarıyordu.\n"
                    "D) Yaptığı indirimlere rağmen sinek avlıyordu."
                ),
                "answer": "A",
                "solution": (
                    "'Suyuna gitmek' = sinirlendirmeden davranmak (B), 'ekmeğini taştan "
                    "çıkarmak' = zor koşulda kazanç sağlamak (C), 'sinek avlamak' = boş "
                    "oturmak/müşterisi olmamak (D). 'Ağzını bıçak açmamak' = çok üzgün/küskün "
                    "olmak; verilen açıklamaların hiçbirini karşılamaz. Doğru cevap A."
                ),
            },
        ],
        # ── Cümlede anlam (duygu/tutum) ──────────────────────────────────────
        "TR.5.CUM.1": [
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC,
                "question": (
                    "Fırsatların elden kaçırılmasından duyulan pişmanlığa 'hayıflanma' denir.\n"
                    "Buna göre aşağıdaki cümlelerin hangisinde HAYIFLANMA anlamı vardır?\n\n"
                    "A) Borç almayı bildiği gibi borcunu zamanında ödemeyi de bilse keşke.\n"
                    "B) Onu etkileyeceğini tahmin etmeme rağmen tüm gerçekleri söyleyiverdim.\n"
                    "C) Kitapları düzgün yerleştirseydin aradığını hemen bulurdun.\n"
                    "D) Dünkü toplantıda fikirlerimizi açık açık dile getirmeliydik."
                ),
                "answer": "D",
                "solution": (
                    "Hayıflanma, GEÇMİŞTE kaçırılan bir fırsata pişmanlıktır. D'de 'dile "
                    "getirmeliydik' ifadesi, toplantıda yapılmayan şeye duyulan pişmanlığı "
                    "anlatır. A bir dilek, C başkasına yönelik eleştiridir. Doğru cevap D."
                ),
            },
        ],
        # ── Noktalama işaretleri ─────────────────────────────────────────────
        "TR.5.NOK.1": [
            {
                "type": QuestionType.YAZIM_NOKTALAMA,
                "difficulty": "orta",
                "source": _SRC,
                "question": (
                    "Virgülün bazı işlevleri:\n"
                    "• Birbiri ardınca sıralanan eş görevli kelimelerin arasına konur.\n"
                    "• Art arda gelen, birbiriyle bağlantılı cümleleri ayırmak için konur.\n"
                    "• Ret, kabul, teşvik bildiren hayır, evet, peki gibi kelimelerden sonra konur.\n"
                    "Aşağıdaki cümlelerin hangisinde virgül bu işlevlerin DIŞINDA "
                    "kullanılmıştır?\n\n"
                    "A) Kalemlerini, silgisini, defter ve kitaplarını çantasına koydu.\n"
                    "B) Tamam, yarın akşam hep birlikte sinemaya gidiyoruz.\n"
                    "C) Yaşlı adam sabah uyanıyor, kahvaltısını yapıp dükkânın yolunu tutuyor.\n"
                    "D) O, yaşamına küçük bir sahil kasabasında devam edecekti."
                ),
                "answer": "D",
                "solution": (
                    "A eş görevli sözcükleri, C bağlantılı cümleleri ayırır; B 'tamam' "
                    "(kabul) sözcüğünden sonra gelir — üçü de verilen işlevlerdendir. D'de "
                    "virgül, özneyi (O) yüklemden ayırıp karışmayı önlemek için kullanılmıştır; "
                    "bu, listelenen işlevlerin dışındadır. Doğru cevap D."
                ),
            },
        ],
    },
    6: {
        # ── Metin türü ───────────────────────────────────────────────────────
        "TR.6.MET.1": [
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC6,
                "question": (
                    "Anı; yaşanmış olayların, üzerinden belli bir zaman geçtikten sonra "
                    "anlatıldığı yazı türüdür.\n"
                    "Buna göre aşağıdakilerden hangisi anıya ÖRNEK OLAMAZ?\n\n"
                    "A) Sonunda bayram geldi. Birazdan en güzel elbiselerimi giyip dışarı "
                    "çıkacağım. Arkadaşımla buluşup komşularımızı ziyaret edeceğiz.\n"
                    "B) Benim yaşımda olanlar iyi bilir. Eskiden kara lastik ayakkabılar vardı; "
                    "babam bir iki numara büyüğünü alırdı, en az iki üç yıl giyerdim.\n"
                    "C) Okula başladığım ilk günü daha dünmüş gibi hatırlıyorum. O gün bendeki "
                    "en baskın duygu sevinçti.\n"
                    "D) Yağışlı bir gündü. Sokakta bulduğumuz küçük kediye Damla adını koymuştuk; "
                    "büyüdü, damla olmaktan çıkıp göl oldu."
                ),
                "answer": "A",
                "solution": (
                    "Anı, GEÇMİŞTE yaşanmış olayları anlatır. B, C ve D geçmiş zaman kipiyle "
                    "yaşanmışlıkları aktarır. A ise gelecek zaman kipiyle (çıkacağım, "
                    "ziyaret edeceğiz) henüz yaşanmamış bir günü anlatır → anı olamaz. "
                    "Doğru cevap A."
                ),
            },
        ],
        # ── Olay/bilgi akışı, sıralama, tutarlılık ───────────────────────────
        "TR.6.OKA.3": [
            {
                "type": QuestionType.SIRALAMA,
                "difficulty": "zor",
                "source": _SRC6,
                "question": (
                    "Aşağıdaki cümleler olayların oluşuna göre sıralanacaktır:\n"
                    "• Temizlediği çaydanlığı, yanan ocağa sürdü.\n"
                    "• Çadırın önüne taşlardan ilkel bir ocak yaptı.\n"
                    "• Seher vaktinde harman yerine yükünü devirip çadırını kurdu.\n"
                    "• Çay suyunun kaynamasını beklerken karşıdaki dağları seyre koyuldu.\n"
                    "Bu cümleler doğru sıralandığında 'Ocağa doldurduğu çalı çırpıları, "
                    "kuşağına gizlediği kibritle tutuşturdu.' cümlesi baştan kaçıncı sırada "
                    "yer alır?\n\n"
                    "A) 2.\nB) 3.\nC) 4.\nD) 5."
                ),
                "answer": "B",
                "solution": (
                    "Doğal sıra: (1) çadırını kurdu, (2) ilkel ocak yaptı, (3) çalı çırpıyı "
                    "tutuşturdu, (4) çaydanlığı ocağa sürdü, (5) dağları seyre koyuldu. "
                    "Verilen cümle 3. sıradadır. Doğru cevap B."
                ),
            },
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "orta",
                "source": _SRC6,
                "question": (
                    "Arkeolojik bulgular, yüzmenin insanlık tarihi kadar eski olduğunu "
                    "gösteriyor. (I) Eski Yunanlıların yüzme yarışları düzenlediğine, "
                    "Romalıların yüzme havuzları yaptığına ilişkin bulgular var. (II) Ancak "
                    "yüzmenin spor olarak yaygınlaşması 19. yüzyıla dayanıyor. (III) Türkiye'de "
                    "modern yüzme sporuna ilk adımın 1973'te atıldığı görülüyor. (IV) Bu "
                    "yüzyıldan sonra yüzme, spor müsabakalarının temel branşlarından biri oldu.\n"
                    "Numaralanmış cümlelerden hangisi parçanın anlam bütünlüğünü BOZMAKTADIR?\n\n"
                    "A) I\nB) II\nC) III\nD) IV"
                ),
                "answer": "C",
                "solution": (
                    "Parça yüzmenin tarihsel gelişimini genel olarak anlatır ve 'bu "
                    "yüzyıldan sonra' (19. yüzyıl) ifadesiyle sürer. III. cümle özel olarak "
                    "Türkiye'ye ve 1973'e atlar, akışı bozar; IV zaten 19. yüzyıla bağlanır. "
                    "Doğru cevap C."
                ),
            },
        ],
        # ── Söz varlığı: atasözü / deyim ─────────────────────────────────────
        "TR.6.SOZ.2": [
            {
                "type": QuestionType.KELIME_BILGISI,
                "difficulty": "zor",
                "source": _SRC6,
                "question": (
                    "Nasrettin Hoca, kaybolan eşeği türkü söyleyerek arar. Nedenini "
                    "soranlara 'El, elin eşeğini türkü çağırarak arar.' der.\n"
                    "Aşağıdakilerden hangisi bu atasözü ile ÇELİŞİR?\n\n"
                    "A) El kazanı ile aş kaynamaz.\n"
                    "B) El, el ile, değirmen yel ile...\n"
                    "C) Elden vefa, zehirden şifa...\n"
                    "D) Elden gelen öğün olmaz, o da vaktinde bulunmaz."
                ),
                "answer": "B",
                "solution": (
                    "'El, elin eşeğini türkü çağırarak arar' = başkası senin işini "
                    "gönülden/ciddiyetle yapmaz. B ('el, el ile...') dayanışmayı över, bu "
                    "anlamla çelişir. A, C ve D ise başkasından fayda gelmeyeceğini "
                    "pekiştirir. Doğru cevap B."
                ),
            },
        ],
        # ── Metinden çıkarım ─────────────────────────────────────────────────
        "TR.6.OKA.2": [
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "orta",
                "source": _SRC6,
                "question": (
                    "Yaşlanmanın birçok nedeni vardır; biri, bölünen hücrelerdeki kromozomları "
                    "koruyan telomer yapılarının kısalmasıdır. Çevresel faktörler, genetik "
                    "özellikler ve beslenme de süreci etkiler. Yaş ilerledikçe ciltte kırışma, "
                    "saçlarda beyazlama gibi değişimler olur. Bu değişimlerin hızı herkeste "
                    "aynı değildir.\n"
                    "Bu parçada yaşlanmayla ilgili aşağıdakilerden hangisine DEĞİNİLMEMİŞTİR?\n\n"
                    "A) Sebeplerinin neler olduğuna\n"
                    "B) Her insanda farklı hızda gerçekleştiğine\n"
                    "C) İnsanda ne tür değişikliklere yol açtığına\n"
                    "D) Önlenmesi için neler yapılması gerektiğine"
                ),
                "answer": "D",
                "solution": (
                    "Parça yaşlanmanın sebeplerini (A), kişiden kişiye farklı hızını (B) ve "
                    "yol açtığı değişimleri (C) anlatır; ancak nasıl önleneceğinden söz "
                    "etmez → D'ye değinilmemiştir. Doğru cevap D."
                ),
            },
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "orta",
                "source": _SRC6,
                "question": (
                    "Belirli bir bölgede yaşayan bitki ve hayvan türlerinin sayıca zenginliği "
                    "olan biyoçeşitlilik; genetik, tür ve ekosistem çeşitliliğini kapsar. Bilim "
                    "insanları, dünyanın yaşanabilir kalması için biyoçeşitliliği koruma "
                    "çalışmaları yapar.\n"
                    "Bu metne göre aşağıdakilerden hangisi biyoçeşitliliğin korunması için "
                    "yapılacak çalışmalardan biri OLAMAZ?\n\n"
                    "A) Üretimde modern/yoğun tarım tekniklerinin yaygınlaştırılması\n"
                    "B) Nesli tükenen hayvanların güvenli ortamlarda çoğaltılması\n"
                    "C) Aşırı avlanmayı önlemek için caydırıcı yasal düzenlemeler yapılması\n"
                    "D) Belirli tabiat alanlarının yerleşime kapatılması"
                ),
                "answer": "A",
                "solution": (
                    "B, C ve D doğrudan türleri ve doğal alanları korumaya yöneliktir. "
                    "Modern/yoğun tarım (A) ise doğal yaşam alanlarını daraltıp çeşitliliği "
                    "azaltabilir; koruma çalışması değildir. Doğru cevap A."
                ),
            },
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "orta",
                "source": _SRC6,
                "question": (
                    "İnsan, yeryüzünde tükettiği su ve enerji ölçüsünde 'ekolojik ayak izi' "
                    "bırakır. Çoğu insan gereğinden fazla tüketip büyük izler bırakıyor. Oysa "
                    "bunu küçültmek basit: yazın klima yerine pencere açmak, kışın kombi yerine "
                    "kalın giyinmek; her yıl telefon değiştirmemek; aygıtları fişte "
                    "bırakmamak (kapalıyken bile enerji harcar).\n"
                    "Aşağıdaki önerilerden hangisi bu metinde sözü edilen sorunlardan herhangi "
                    "biriyle İLGİLİ DEĞİLDİR?\n\n"
                    "A) Isınmak ve serinlemek için daha az enerji harcayın.\n"
                    "B) Sadece ihtiyaç duyduğunuz ürünleri satın alın.\n"
                    "C) Hazır gıdalar yerine doğal gıdalar tüketin.\n"
                    "D) Elektrikli aletleri kullanmadığınızda prizde bırakmayın."
                ),
                "answer": "C",
                "solution": (
                    "Metin enerji tüketimi (A), gereksiz tüketim (B) ve fişte bırakılan "
                    "aygıtlar (D) sorunlarını anlatır. Beslenme/gıda seçimi (C) metinde geçen "
                    "sorunlarla ilgili değildir. Doğru cevap C."
                ),
            },
        ],
        # ── Cümlede anlam ────────────────────────────────────────────────────
        "TR.6.CUM.1": [
            {
                "type": QuestionType.DIYALOG_TAMAMLAMA,
                "difficulty": "orta",
                "source": _SRC6,
                "question": (
                    "Empati (duygudaşlık), kişinin kendini karşısındakinin yerine koyarak "
                    "onun duygu ve düşüncelerini anlama çabasıdır.\n"
                    "Çocuk: — Günüm güzel geçtiği için keyfim yerinde, anne!\n"
                    "Anne: — - - - -\n"
                    "Anne aşağıdaki cevaplardan hangisini verirse çocuğuyla EMPATİ kurmuş "
                    "olur?\n\n"
                    "A) Kardeşin de geçen gün aynı cümleyi söyledi.\n"
                    "B) İşler yolunda gittiği için mutlu hissediyorsun, değil mi?\n"
                    "C) Arkadaşların da senin gibi mi düşünüyor acaba?\n"
                    "D) Anlat bakalım, bugün neler yaşadın?"
                ),
                "answer": "B",
                "solution": (
                    "Empati, karşıdakinin duygusunu adlandırıp yansıtmaktır. B, çocuğun "
                    "mutluluğunu fark edip ona geri yansıtır. A karşılaştırma, C "
                    "yönlendirme, D bilgi isteğidir. Doğru cevap B."
                ),
            },
        ],
        # ── Söz varlığı: çok anlamlılık ──────────────────────────────────────
        "TR.6.SOZ.1": [
            {
                "type": QuestionType.KELIME_BILGISI,
                "difficulty": "orta",
                "source": _SRC6,
                "question": (
                    "'Dayanmak' sözcüğünün bazı anlamları:\n"
                    "• Zarar görmemek, varlığını korumak\n"
                    "• Bir yere yaslanmak\n"
                    "• Bir işi bütün gücünü kullanarak yapmak\n"
                    "'Dayanmak' aşağıdaki cümlelerin hangisinde bu anlamlardan herhangi biriyle "
                    "KULLANILMAMIŞTIR?\n\n"
                    "A) İki genç, küreklere kırarcasına dayandı.\n"
                    "B) Gemimiz fırtınaya ne kadar dayanır?\n"
                    "C) Köprünün geçmişi 18. yüzyıla dayanıyor.\n"
                    "D) Başı dönünce duvara dayanıp öylece bekledi."
                ),
                "answer": "C",
                "solution": (
                    "A 'bütün gücüyle yapmak', B 'zarar görmemek/direnmek', D 'yaslanmak' "
                    "anlamındadır. C'deki 'dayanmak' ise 'bir zamana kadar uzanmak' "
                    "anlamıyla kullanılmıştır; verilen anlamların dışındadır. Doğru cevap C."
                ),
            },
        ],
        # ── Anlatım biçimleri / söz sanatları ────────────────────────────────
        "TR.6.SAN.1": [
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "zor",
                "source": _SRC6,
                "question": (
                    "İnsanların gözünde 'retina' adı verilen, ışığa duyarlı hücreler taşıyan "
                    "bir bölüm bulunur. Bu hücreler ışığın bir kısmını emer; kalanı ağ "
                    "tabakanın arkasına geçer. Bazı hayvanların gözünde, insanlardan farklı "
                    "olarak ağ tabakanın arkasında ışığı ayna gibi yansıtan bir tabaka daha "
                    "vardır; bu yüzden geceleri gözleri parlar.\n"
                    "Bu metnin anlatımıyla ilgili aşağıdakilerden hangisi SÖYLENEMEZ?\n\n"
                    "A) Bir durumun nedeni açıklanmıştır.\n"
                    "B) Karşılaştırmaya başvurulmuştur.\n"
                    "C) Tanımlama yapılmıştır.\n"
                    "D) Açıklayıcı anlatımdan yararlanılmıştır."
                ),
                "answer": "C",
                "solution": (
                    "Metin hayvan ve insan gözünü karşılaştırır (B), gözlerin parlamasının "
                    "nedenini açıklar (A) ve baştan sona açıklayıcı anlatım kullanır (D). "
                    "Bir kavramın sözlük anlamını veren tanımlama ise yapılmamıştır → C "
                    "söylenemez. Doğru cevap C."
                ),
            },
        ],
        # ── Noktalama ────────────────────────────────────────────────────────
        "TR.6.NOK.1": [
            {
                "type": QuestionType.YAZIM_NOKTALAMA,
                "difficulty": "orta",
                "source": _SRC6,
                "question": (
                    "Soru işaretinin bazı işlevleri:\n"
                    "• Soru eki/sözü içeren cümlelerin sonuna konur.\n"
                    "• Bilinmeyen, kesin olmayan yer, tarih vb. için kullanılır.\n"
                    "• Soru bildiren ancak soru eki/sözü içermeyen cümlelerin sonuna konur.\n"
                    "Aşağıdaki cümlelerin hangisinde soru işareti YANLIŞ kullanılmıştır?\n\n"
                    "A) Ankara'dan Eskişehir'e hızlı trenle kırk beş dakikada (?) gitmiş.\n"
                    "B) Danışmadaki görevli başını kaldırdı: — Mesleğiniz?\n"
                    "C) Yazarın son kitabı bu yılın sonunda mı yayımlanacakmış?\n"
                    "D) Problemin başka bir çözüm yolu olup olmadığını sordu bana?"
                ),
                "answer": "D",
                "solution": (
                    "A kesin olmayan süreyi, B eksiltili soruyu, C soru ekli soruyu doğru "
                    "gösterir. D ise soru DEĞİL, bir bildirme (dolaylı anlatım) cümlesidir; "
                    "sonuna soru işareti değil nokta gelmeliydi. Doğru cevap D."
                ),
            },
        ],
    },
    7: {
        # ── Metin türü / anlatım ─────────────────────────────────────────────
        "TR.7.MET.1": [
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC7,
                "question": (
                    "Aşağıdakilerden hangisi OLAY ağırlıklı bir metindir?\n\n"
                    "A) O taş döşeli eski yol şimdi bozulmuş, çukurlarla dolmuştu. İki yanımızda "
                    "uzanan zeytinlikleri ot sarmıştı; çamlar seyrekleşmişti. (betimleme)\n"
                    "B) Bazı kimseler gülümsemeyi ciddiliği bozan bir hâl sayar. İnsanların "
                    "hayvanlardan bir farkı konuşmaksa öteki farkı da gülmektir. (düşünce)\n"
                    "C) Zeynep gölde yürürken yalnız olmadığını fark etti. Ayak seslerine kulak "
                    "verince ürperdi; dönmekle koşup uzaklaşmak arasında kalmıştı ki annesinin "
                    "sesini duydu.\n"
                    "D) Yozgat'a özgü 'bağrıbütün' kavununun tadı muza benzer; bu yıl yüz dönüme "
                    "ekildi, hasadına yakında başlanacak. (haber/bilgi)"
                ),
                "answer": "C",
                "solution": (
                    "Olay ağırlıklı metinde bir kahramanın başından geçen, zaman içinde gelişen "
                    "bir olay örgüsü vardır. C'de Zeynep'in yaşadığı bir olay (fark etme, "
                    "ürperme, annesini duyma) anlatılır. A betimleme, B düşünce, D haber "
                    "metnidir. Doğru cevap C."
                ),
            },
        ],
        # ── Metinden çıkarım ─────────────────────────────────────────────────
        "TR.7.OKA.2": [
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "zor",
                "source": _SRC7,
                "question": (
                    "Dünya Miras Listesi'ndeki bazı varlıklar: Edirne Selimiye Camii "
                    "(mimarinin zirvesi, Mimar Sinan'ın ustalık eseri); Pamukkale Travertenleri "
                    "(kalsiyum karbonatlı suların oluşturduğu eşsiz doğal güzellik); Safranbolu "
                    "Evleri (bozulmamış geleneksel Türk şehir dokusu).\n"
                    "Aşağıdaki Miras Listesi ölçütlerinden hangisi bu varlıklardan herhangi "
                    "biriyle İLİŞKİLENDİRİLEMEZ?\n\n"
                    "A) İnsanlık tarihinde önemli bir yapı tipinin/teknolojinin istisnai örneği "
                    "olmalı.\n"
                    "B) Bitki ve hayvan topluluklarının gelişimindeki önemli EKOLOJİK ve "
                    "BİYOLOJİK süreçleri temsil eden benzersiz örnekler olmalı.\n"
                    "C) Eşsiz bir doğal güzelliğe ve estetik öneme sahip alanları içermeli.\n"
                    "D) Mimarlık, şehir planlama vb. konularda insani değerler arasında önemli "
                    "bir alışverişi sergilemeli."
                ),
                "answer": "B",
                "solution": (
                    "Selimiye A ve D ile (mimari), Pamukkale C ile (doğal güzellik), "
                    "Safranbolu A/D ile ilişkilendirilir. B, canlı topluluklarının ekolojik/"
                    "biyolojik süreçlerini ister; verilen varlıkların hiçbiri (traverten "
                    "jeolojiktir, canlı ekosistemi değil) bununla ilişkilendirilemez. "
                    "Doğru cevap B."
                ),
            },
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "orta",
                "source": _SRC7,
                "question": (
                    "İyi filmler; duyguları harekete geçirerek insan ruhunu dönüştüren, taklidi "
                    "olmayan ve kahramanları kanlı canlı bireylerden oluşan filmlerdir. Böyle "
                    "filmler insanın kalbinde kıvılcımlar oluşturur.\n"
                    "Bu parçaya göre iyi filmler aşağıdakilerden hangisiyle "
                    "NİTELENDİRİLEMEZ?\n\n"
                    "A) Gerçekçi\nB) Tutarlı\nC) Etkileyici\nD) Özgün"
                ),
                "answer": "B",
                "solution": (
                    "'Ruhu dönüştüren/kıvılcım oluşturan' = etkileyici (C), 'taklidi olmayan' "
                    "= özgün (D), 'kanlı canlı bireyler' = gerçekçi (A). Tutarlılık (B) "
                    "parçada belirtilmez → nitelendirilemez. Doğru cevap B."
                ),
            },
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "orta",
                "source": _SRC7,
                "question": (
                    "'Eserlerimde hayatın zorluklarını, insanın sıkıntılarını ALAYCI bir dille "
                    "anlatmaya çalıştım. Bu anlatımın daha etkileyici olduğunu biliyorum. "
                    "Sokaktan aldığımı cesaret ve samimiyetle doldurup yine sokağa "
                    "gönderiyorum.'\n"
                    "Bu sözleri söyleyen yazarla ilgili aşağıdakilerden hangisi "
                    "SÖYLENEMEZ?\n\n"
                    "A) Olumsuz durumları eğlenceli bir üslupla anlatmaya çalışır.\n"
                    "B) Yapıtın okuru etkilemesinde anlatımın gücüne inanır.\n"
                    "C) Eserlerinde gerçek hayattan beslenmeyi tercih eder.\n"
                    "D) Geniş kitlelere ulaşmada yalınlığın etkili olduğunu düşünür."
                ),
                "answer": "D",
                "solution": (
                    "'Alaycı dil' → A, 'etkileyici olduğunu biliyorum' → B, 'sokaktan alıp "
                    "sokağa gönderme' (gerçek hayat) → C. Yalınlık ya da geniş kitleye ulaşma "
                    "sözden çıkarılamaz → D söylenemez. Doğru cevap D."
                ),
            },
        ],
        # ── Söz varlığı: deyim / söz grubu ───────────────────────────────────
        "TR.7.SOZ.2": [
            {
                "type": QuestionType.KELIME_BILGISI,
                "difficulty": "zor",
                "source": _SRC7,
                "question": (
                    "Dört kirpi soğukta donmamak için birbirine sokulur; dikenleri batınca "
                    "ayrılır, üşüyünce yaklaşır. Sonunda ne dikenlerin batacağı kadar yakın ne "
                    "de üşüyecekleri kadar uzak dururlar. Bu duruma 'kirpi mesafesi' denir.\n"
                    "Aşağıdaki cümlelerin hangisinde bu metindeki altı çizili ifadede "
                    "anlatılmak isteneni karşılayan bir söz grubu kullanılmıştır?\n\n"
                    "A) İyimserlik, hayattan daha çok keyif almamızı sağlar.\n"
                    "B) Yaşamda DENGELİ olmak beraberinde huzuru getirir.\n"
                    "C) Güçlüklerle mücadele etmek geleceğimize yön verir.\n"
                    "D) Cesur insanlar zorluklar karşısında karamsarlığa düşmezler."
                ),
                "answer": "B",
                "solution": (
                    "Kirpi mesafesi, iki uç (çok yakın/çok uzak) arasında DENGE noktasını "
                    "bulmaktır. Bunu karşılayan söz grubu B'deki 'dengeli olmak'tır. Diğerleri "
                    "iyimserlik, mücadele ve cesaretten söz eder. Doğru cevap B."
                ),
            },
        ],
        # ── Söz varlığı: bağlamdan anlam ─────────────────────────────────────
        "TR.7.SOZ.1": [
            {
                "type": QuestionType.KELIME_BILGISI,
                "difficulty": "orta",
                "source": _SRC7,
                "question": (
                    "Ünlü sanatçı, en küçük kışkırtmalarla renk değiştiren karakteriyle bir "
                    "'kaleydoskop (çiçek dürbünü)' gibiydi.\n"
                    "Bu parçaya göre 'kaleydoskop' sözcüğünün tanımı aşağıdakilerden "
                    "hangisidir?\n\n"
                    "A) Bazı maddelerin rengini yok etmekte kullanılan kimyasal madde.\n"
                    "B) Film üzerindeki resimlerin ekrana art arda düşürülmesiyle oluşan "
                    "görünüş.\n"
                    "C) Renkli taş parçalarının yan yana getirilmesiyle yapılan bezeme işi.\n"
                    "D) Bir ucundaki renkli küçük cisimlerin hareket ettikçe çeşitli biçimler "
                    "oluşturduğu, borulu bir araç."
                ),
                "answer": "D",
                "solution": (
                    "Metindeki ipucu 'renk değiştiren' ve 'çiçek dürbünü' açıklamasıdır. "
                    "Kaleydoskop, içindeki renkli cisimler hareket ettikçe değişen biçimler "
                    "gösteren borulu bir araçtır → D. A ağartıcıyı, B sinemayı, C mozaiği "
                    "tanımlar. Doğru cevap D."
                ),
            },
        ],
        # ── Cümlede anlam ────────────────────────────────────────────────────
        "TR.7.CUM.1": [
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC7,
                "question": (
                    "'Çeşitli üniversitelerden gelen bilim insanlarının yaptığı araştırmalar "
                    "sonucunda Mısır'daki Büyük Piramit'in içinde birçok oda ve koridorun yer "
                    "aldığı bir alan keşfedildi.'\n"
                    "Bu cümle aşağıdakilerin hangisinde verilenlerin birleştirilmesiyle "
                    "oluşturulmuştur?\n\n"
                    "A) • Bilim insanları bir alan keşfetti. • Bu alanlar oda ya da "
                    "koridorlardan oluşuyor.\n"
                    "B) • Bir alan keşfedildi. • Bu alanda oda ve koridor OLABİLECEĞİ tahmin "
                    "ediliyor.\n"
                    "C) • Çeşitli üniversitelerden bilim insanlarının araştırmalarında bir alan "
                    "keşfedildi. • Bu alan birçok oda ve koridordan oluşuyor.\n"
                    "D) • Bilim insanlarının üniversitelerde yaptığı incelemelerle bir alan "
                    "keşfedildi. • ..."
                ),
                "answer": "C",
                "solution": (
                    "Asıl cümle kesinlik bildirir (keşfedildi, yer aldığı) ve araştırmanın "
                    "'üniversitelerden gelen bilim insanları' tarafından yapıldığını söyler. "
                    "Yalnız C bu iki bilgiyi tahmin/olasılık katmadan birleştirir. Doğru cevap C."
                ),
            },
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC7,
                "question": (
                    "'Özgürlük, özgürlüğü için her gün mücadele edenin hakkıdır.'\n"
                    "Aşağıdakilerden hangisi bu cümleye anlamca EN YAKINDIR?\n\n"
                    "A) Hürriyete layık olmak için sürekli çaba göstermek gerekir.\n"
                    "B) Zaferin büyüklüğü, mücadelenin zorluğuyla ölçülür.\n"
                    "C) Bağımsızlığa kavuşmak için istekli olmak şarttır.\n"
                    "D) En gayretli insanlar bağımsız topraklarda yetişir."
                ),
                "answer": "A",
                "solution": (
                    "Cümle, özgürlüğün ancak sürekli mücadele/çaba ile hak edildiğini söyler. "
                    "A bunu ('sürekli çaba göstermek gerekir') birebir karşılar. B zafer, C "
                    "yalnız isteklilik, D coğrafya vurgusu yapar. Doğru cevap A."
                ),
            },
        ],
        # ── Diyalog tamamlama ────────────────────────────────────────────────
        "TR.7.OKA.1": [
            {
                "type": QuestionType.DIYALOG_TAMAMLAMA,
                "difficulty": "zor",
                "source": _SRC7,
                "question": (
                    "Muhabir: — (I) - - - -\n"
                    "Filozof: — Tartışma götürür bir soru bu. Bence felsefe, henüz kesin olarak "
                    "bilinmeyen konular üstüne kafa yormaktır.\n"
                    "Muhabir: — (II) - - - -\n"
                    "Filozof: — Kabaca şu: Bilim, bildiğimiz şeyler; felsefe, bilmediğimiz "
                    "şeylerdir. İnsanın bilgisi arttıkça sorunlar felsefeden bilime geçer.\n"
                    "Boş bırakılan yerlere aşağıdakilerin hangisi getirilmelidir?\n\n"
                    "A) (I) Görüş farklılıklarının sebebi nedir? (II) Bilimin konuları nelerdir?\n"
                    "B) (I) Size göre felsefe nedir? (II) Felsefe ile bilimin ayrıldığı nokta "
                    "nedir?\n"
                    "C) (I) Filozofların görevi nedir? (II) Felsefede bilim etkili midir?\n"
                    "D) (I) Felsefede konu sınırı var mıdır? (II) Felsefe ile bilim etkileşir "
                    "mi?"
                ),
                "answer": "B",
                "solution": (
                    "Filozofun ilk cevabı felsefenin ne olduğunu tanımlar → (I) 'Size göre "
                    "felsefe nedir?'. İkinci cevabı bilim ile felsefeyi ayırır → (II) "
                    "'ayrıldığı nokta nedir?'. Bu ikisi yalnız B'de birlikte verilir. "
                    "Doğru cevap B."
                ),
            },
        ],
        # ── Anlatım biçimleri / söz sanatları ────────────────────────────────
        "TR.7.SAN.1": [
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "zor",
                "source": _SRC7,
                "question": (
                    "'Bir yazımda İzmir için \"Olmamış, yarım kalmış hayallerimin başrol "
                    "oyuncusu.\" demiştim. 1990'da, 18 yaşımda sabahın erken saatinde "
                    "Basmane'de inmiştim trenden. Ilık bir rüzgâr esiyordu. Kemeraltı, Saat "
                    "Kulesi, karadut şerbeti… Biliyorum, İzmir'e döneceğim.'\n"
                    "Bu metnin anlatımıyla ilgili aşağıdakilerden hangisi SÖYLENEMEZ?\n\n"
                    "A) Örneklemeye başvurulmuştur.\n"
                    "B) Alıntılama yapılmıştır.\n"
                    "C) Kişileştirmeden yararlanılmıştır.\n"
                    "D) Farklı duyulara seslenilmiştir."
                ),
                "answer": "A",
                "solution": (
                    "'…demiştim' ile alıntı (B); İzmir'e 'başrol oyuncusu' denmesi kişileştirme "
                    "(C); ılık rüzgâr (dokunma), karadut şerbeti (tat) ile farklı duyular (D) "
                    "vardır. Bir kavramı somutlaştıran örnekleme ise yoktur → A söylenemez. "
                    "Doğru cevap A."
                ),
            },
        ],
        # ── Yazım kuralları ──────────────────────────────────────────────────
        "TR.7.YAZ.1": [
            {
                "type": QuestionType.YAZIM_NOKTALAMA,
                "difficulty": "zor",
                "source": _SRC7,
                "question": (
                    "Kural: Ek olan '-ki' ve '-de' kendinden önceki sözcüğe BİTİŞİK; bağlaç "
                    "olan 'ki' ve 'de' AYRI yazılır.\n"
                    "Buna göre numaralanmış sözcüklerden hangilerinin yazımı YANLIŞTIR?\n"
                    "'Bizde(I) olanı bize açıkça söyleyebilen dostlara ihtiyacımız var. Eskiler "
                    "tam da bunu söylemeye çalışmışlar belkide(II). Ama çevremizde böyle kaç "
                    "kişi varki(III)? Parklardaki(IV) aynalar gibi davrananlar çok.'\n\n"
                    "A) I ve II\nB) I ve IV\nC) II ve III\nD) III ve IV"
                ),
                "answer": "C",
                "solution": (
                    "I 'Bizde' (bulunma eki, bitişik) ve IV 'parklardaki' (ek '-ki', bitişik) "
                    "DOĞRUDUR. II 'belki de' (bağlaç 'de', ayrı) ve III 'var mı ki' → 'ki' "
                    "bağlaç, ayrı yazılmalı; 'belkide' ve 'varki' YANLIŞ. Doğru cevap C."
                ),
            },
        ],
    },
    8: {
        # ── Söz varlığı: bağlamdan sözcük ────────────────────────────────────
        "TR.8.SOZ.1": [
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC8,
                "question": (
                    "Ünlü besteci Beethoven, işitme sorunları yaşamaya başlamıştı. Bu sorunlar "
                    "- - - - neredeyse hiçbir şey - - - - hâle gelen Beethoven'ın yeni bir "
                    "yöntem geliştirdiği söylenir: piyanosuna tutturduğu metal çubuğu - - - - "
                    "kemik titreşimi yoluyla sesleri duymaya çalışıyordu.\n"
                    "Boş bırakılan yerlere sırasıyla aşağıdakilerden hangisi getirilmelidir?\n\n"
                    "A) çözülünce - algılayamaz - tutarak\n"
                    "B) ilerleyince - duyamaz - ısırarak\n"
                    "C) ortaya çıkınca - işitemez - fırlatarak\n"
                    "D) yaşanınca - sezemez - bağlayarak"
                ),
                "answer": "B",
                "solution": (
                    "İşitme sorunu zamanla 'ilerleyince', kişi 'hiçbir şey duyamaz' hâle "
                    "gelir; metal çubuğu dişleriyle 'ısırarak' kemik titreşimini iletir. "
                    "Bağlam bütünlüğüne yalnız B uyar. Doğru cevap B."
                ),
            },
        ],
        # ── Ana düşünce / tema / konu ────────────────────────────────────────
        "TR.8.OKA.1": [
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "orta",
                "source": _SRC8,
                "question": (
                    "Bir kral, huzuru en güzel resmedene ödül vereceğini ilan eder. İki resmi "
                    "beğenir: Birincide dağların yansıdığı dingin bir göl, beyaz bulutlar "
                    "vardır. İkincide engebeli dağlar, kasvetli gri bir gökyüzü; ama şelalenin "
                    "yanındaki çalıda, sertçe akan suyun ortasında bir anne kuşun kurduğu yuva "
                    "görülür. Kral ödülü ikinci resme verir.\n"
                    "Bu metnin sonuna düşüncenin akışına göre hangi cümle getirilmelidir?\n\n"
                    "A) Huzur, hiçbir gürültünün, zorluğun bulunmadığı yerdedir.\n"
                    "B) Huzur, olumsuzlukların içinde bile olumlu olanı bulabilmektir.\n"
                    "C) Sanatçının iç dünyasındaki huzur eserlerine yansır.\n"
                    "D) Huzuru bulmak için doğru yerde aramak gerekir."
                ),
                "answer": "B",
                "solution": (
                    "Kral, kasvetli bir tablodaki huzur dolu ayrıntıyı (fırtınanın ortasındaki "
                    "yuva) ödüllendirir. Bu, huzurun olumsuzluk içinde olumluyu görebilmek "
                    "olduğunu anlatır → B. Doğru cevap B."
                ),
            },
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "orta",
                "source": _SRC8,
                "question": (
                    "Aşağıdaki dizelerden hangisi TEMA bakımından diğerlerinden FARKLIDIR?\n\n"
                    "A) Hayata beraber başladığımız / Dostlarla da yollar ayrıldı bir bir / "
                    "Gittikçe artıyor yalnızlığımız\n"
                    "B) Allah'ım, ne güzel şey bu dost yüzü / İnsanın kalbine dolan bu bakış\n"
                    "C) Dostluk dediğin güzel bir kitap / Hava gibi, su gibi, ekmek gibi / "
                    "Vazgeçilmez bir tat\n"
                    "D) Kalbindeki cama bir taş değer, dosttandır / Kırılınca anlaşılır kalbin "
                    "camdan olduğu"
                ),
                "answer": "A",
                "solution": (
                    "B, C ve D dostluğun değerini/güzelliğini işler. A ise dostların "
                    "ayrılmasıyla artan YALNIZLIĞI anlatır → teması farklıdır. Doğru cevap A."
                ),
            },
        ],
        # ── Metinden çıkarım ─────────────────────────────────────────────────
        "TR.8.OKA.2": [
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "orta",
                "source": _SRC8,
                "question": (
                    "Edebiyatta ve sanatta unutulmaz dönemler vardır; sanki tüm yetenekli "
                    "şair, yazar ve ressamlar ortaya çıkmak için o dönemleri beklemiştir. Böyle "
                    "dönemlerde, olağanüstü ikramların bulunduğu bir sofrada ne yiyeceğini "
                    "şaşırmış bir misafir gibi 'Ama haksızlık bu!' diye düşünürsünüz.\n"
                    "Yazarın 'Ama haksızlık bu!' demesinin sebebi aşağıdakilerden hangisidir?\n\n"
                    "A) İyi seçeneklerin çokluğu karşısında kararsızlık yaşanması\n"
                    "B) Nitelikli sanatçıların kendi çağına denk gelmemesi\n"
                    "C) Eser çeşitliliğinin kalitenin düşmesine yol açması\n"
                    "D) Bazı dönemlerin başarılı sanatçılardan yoksun olması"
                ),
                "answer": "A",
                "solution": (
                    "'Ne yiyeceğini şaşırmış misafir' benzetmesi, çok sayıda nitelikli eser "
                    "arasında seçim yapmanın güçlüğünü anlatır. Haksızlık duygusu bu bolluk "
                    "karşısındaki kararsızlıktandır → A. Doğru cevap A."
                ),
            },
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "zor",
                "source": _SRC8,
                "question": (
                    "Nasrettin Hoca fıkralarının bazılarında, insanlara BİREYSEL "
                    "ÖZELLİKLERİNİ göz önünde bulundurarak davranmak gerektiği vurgulanır.\n"
                    "Aşağıdaki fıkralardan hangisi bu duruma örnek olabilir?\n\n"
                    "A) Mirasını tüketen adama Hoca 'yakında bu dertten kurtulursun; "
                    "parasızlığa alışacaksın' der.\n"
                    "B) Göle düşen cimri komşu, 'elini ver' diyenlere elini vermez; Hoca onu "
                    "tanıdığı için 'AL elimi' deyince adam tutup kurtulur.\n"
                    "C) Hoca göle yoğurt çalar; 'göl maya tutar mı?' diyene 'ya tutarsa' der.\n"
                    "D) Hoca pahalı papağana karşılık 'o konuşur' diyenlere 'bu da düşünür' "
                    "der."
                ),
                "answer": "B",
                "solution": (
                    "Hoca, komşusunun cimri olduğunu bildiği için 'ver' değil 'AL' diyerek "
                    "onun kişiliğine uygun davranır ve kurtarır. Bu, bireysel özelliği göz "
                    "önünde bulundurmaya örnektir → B. Doğru cevap B."
                ),
            },
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "orta",
                "source": _SRC8,
                "question": (
                    "Eleştiri, ünlü yazarın önemli bir yönüdür. Gölgede kalmayı sever; "
                    "insanların olumsuz yanlarını gösterirken bile şefkatlidir. 'Suya sabuna "
                    "dokunmayan biri' denmesi haksızlıktır; çünkü zamanın ruhuna kayıtsız "
                    "değildir, eleştirilerini mizahla ve olumlu bir tutumla sunar.\n"
                    "Bu metinde sözü edilen yazar aşağıdakilerden hangisiyle "
                    "NİTELENDİRİLEMEZ?\n\n"
                    "A) Özgün\nB) Alçak gönüllü\nC) Sevecen\nD) Yapıcı"
                ),
                "answer": "A",
                "solution": (
                    "'Gölgede kalmayı sever' → alçak gönüllü (B), 'şefkatli' → sevecen (C), "
                    "'olumlu tutumla sunar' → yapıcı (D). Özgünlük (A) metinde belirtilmez → "
                    "nitelendirilemez. Doğru cevap A."
                ),
            },
        ],
        # ── Akıl yürütme / bilgi ilişkilendirme ──────────────────────────────
        "TR.8.OKA.3": [
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "zor",
                "source": _SRC8,
                "question": (
                    "Ayşe, Büşra, Cenk, Davut, Ece ve Ferhat; K, L ve M sınıflarına "
                    "kaydolmuştur:\n"
                    "• Ece ve Cenk aynı sınıftadır.\n"
                    "• Büşra'nın sınıfına kendisi dışında bir kişi daha kaydolmuştur (2 kişilik).\n"
                    "• M sınıfına kaydolan tek kişi vardır ve bu kişi Ayşe değildir.\n"
                    "• Davut üç kişilik bir sınıftadır.\n"
                    "Bu bilgilere göre aşağıdakilerden hangisi Büşra ile AYNI sınıftadır?\n\n"
                    "A) Davut\nB) Ayşe\nC) Ferhat\nD) Ece"
                ),
                "answer": "B",
                "solution": (
                    "M tek kişilik ve o kişi Ayşe değil. Ece-Cenk birlikte olduğundan 3 "
                    "kişilik (Davut'un) sınıfa girer: Davut+Ece+Cenk. M'deki tek kişi Ferhat "
                    "olur. Geriye 2 kişilik sınıfta Büşra ile Ayşe kalır. Doğru cevap B."
                ),
            },
        ],
        # ── Cümlede anlam: nesnellik, anlamca yakınlık ───────────────────────
        "TR.8.CUM.1": [
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC8,
                "question": (
                    "Öznel cümle kişisel düşünce içerir; nesnel cümle kanıtlanabilir bir yargı "
                    "bildirir.\n"
                    "(I) Boyoz, mayasız hamurun kat kat açılmasıyla yapılır. (II) Bu hamur çok "
                    "farklı bir tada kavuşturulur. (III) Boyoz kahvaltı sofralarının "
                    "vazgeçilmezidir. (IV) İzmir'in bu eşsiz lezzetini herkesin denemesini "
                    "öneririm.\n"
                    "Bu cümlelerin hangisinde NESNEL anlatım vardır?\n\n"
                    "A) I\nB) II\nC) III\nD) IV"
                ),
                "answer": "A",
                "solution": (
                    "I. cümle boyozun nasıl yapıldığını (kanıtlanabilir, tarafsız bilgi) "
                    "verir → nesnel. 'Farklı tat', 'vazgeçilmez', 'eşsiz/öneririm' ise "
                    "kişisel değerlendirmedir → öznel. Doğru cevap A."
                ),
            },
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC8,
                "question": (
                    "Shakespeare: 'Düşüncenin canı kısa sözdedir; uzun sözler dış "
                    "görünüştür.' Yunus Emre: 'Az söz erin yüküdür, çok söz hayvan yüküdür.'\n"
                    "Aşağıdaki cümlelerden hangisi bu görüşlerle BENZER bir iletiye "
                    "sahiptir?\n\n"
                    "A) Söz, etkili ve özlü bir şekilde kullanılmalıdır.\n"
                    "B) Düşünce ile söz arasında sarsılmaz bir denge olmalıdır.\n"
                    "C) Kişi her bildiğini söylemeli, her söylediğini de bilmeli.\n"
                    "D) Neyi, kime, ne zaman söylediğini unutma."
                ),
                "answer": "A",
                "solution": (
                    "Her iki alıntı da sözün AZ ve ÖZ olması gerektiğini vurgular. Bunu "
                    "karşılayan tek cümle A'dır ('etkili ve özlü'). Doğru cevap A."
                ),
            },
        ],
        # ── Anlatım biçimleri ────────────────────────────────────────────────
        "TR.8.SAN.1": [
            {
                "type": QuestionType.OKUMA_PASAJI,
                "difficulty": "zor",
                "source": _SRC8,
                "question": (
                    "'Şöyle etrafınıza bakın. Kaç kişi karşısındakini dikkatle dinliyor? Dil, "
                    "işlerliğini yavaş yavaş kaybediyor. Televizyonun gürültüsü, telefonun "
                    "zırıltısı sahici bir konuşmayı imkânsız kılıyor. Oysa insan, hikâye "
                    "anlatmak ve yankısını duymak isteyen bir varlıktır.'\n"
                    "Bu metinle ilgili aşağıdakilerden hangisi SÖYLENEMEZ?\n\n"
                    "A) Sohbet havasında yazılmıştır.\n"
                    "B) Eleştirilen durum gerekçesiyle verilmiştir.\n"
                    "C) Pişmanlık dile getirilmiştir.\n"
                    "D) Aşamalı bir durumdan söz edilmiştir."
                ),
                "answer": "C",
                "solution": (
                    "Metin okura seslenerek sohbet havası kurar (A), dilin işlevsizleşmesini "
                    "gürültü/telaşla gerekçelendirir (B) ve 'yavaş yavaş' ifadesiyle aşamalı "
                    "durumu anlatır (D). Kişisel bir pişmanlık ise yoktur → C söylenemez. "
                    "Doğru cevap C."
                ),
            },
        ],
    },
}
