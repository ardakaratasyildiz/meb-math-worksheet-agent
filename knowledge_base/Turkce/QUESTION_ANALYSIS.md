# MEB Türkçe (5–8) — Soru Yapısı Analizi

> Amaç: Türkçe çoktan seçmeli (MC) soru üreten worksheet-generator için **hangi soru şekillerini üretmesi gerektiğini** netleştirmek. Bu doküman resmi MEB kaynaklarındaki soru yapısının taksonomisini, çeldirici mantığını, sınıf ilerleyişini ve görsel içerik yükünü, birebir (verbatim) örneklerle verir.
>
> Analiz edilen kaynaklar (repo: `knowledge_base/Turkce/`):
> - **EBA Kazanım Testleri (`ornek_sorular/{5,6,7,8}.sinif/kt_*.pdf`)** — okundu: 5.sınıf kt_1/5/10/15/20/30; 6.sınıf kt_1/8/15/22/30; 7.sınıf kt_1/10/20/30; 8.sınıf kt_2 (tam, 47 soru) + kt_1 taranmış. Format tüm 88 dosyada tarandı.
> - **ÖDSGM Beceri Temelli Sorular (`sorular/{5,6,7}_turkce_beceri_*.pdf` + `*_ca.pdf` cevap anahtarları)** — okundu: 5/6/7 beceri_1 tam + 5/6/7 beceri_ca + 8.sınıf turk_ca.
> - **3. parti hex-isimli dosyalar (`{5,6,7,8}.sinif/<hex>.pdf`)** — örneklendi: 5.sınıf a5f8c4ef6d, 6.sınıf 23012400db, 8.sınıf 151a76ee8b + 5f2f35d45d.
>
> Tüm PDF'lerde gömülü metin var (taranmış görüntü değil). Cevap anahtarları: beceri dosyalarının kendisinde cevap YOK (karekod ile ulaşılıyor); ayrı `*_ca.pdf` dosyaları tema bazında metinsel cevap anahtarı içeriyor. kt_ dosyalarının 5/6/7 sınıfında ayrı cevap anahtarı YOK; 8.sınıf için `turk_ca.pdf` var.

---

## 0. EN ÖNEMLİ TEK İÇGÖRÜ

**Türkçe MC sorularının kalbi "parça (metin) + metne dayalı tek bir dil/anlama işlemi"dir; izole gramer sorusu bile çoğu zaman bir paragrafın/dizenin içine gömülür.** Soru neredeyse hiçbir zaman "X nedir?" diye sormaz; bunun yerine bir uyaran (parça, dize, cümle listesi, tablo, görsel) verir ve **"aşağıdakilerden hangisi..."** kalıbıyla bir seçim/eşleştirme/çıkarım ister. Çeldiriciler rastgele değildir: hepsi dilbilgisel/anlamsal olarak makul, aynı kategoriden ve parçayla ilişkilidir — doğru cevap "tek farklı olan"dır (genellikle **olumsuz köklü** soru: *hangisi yanlıştır / değildir / kullanılmamıştır / değinilmemiştir / söylenemez*).

---

## 1. ÇOKTAN SEÇMELİ (MC) MANTIĞI

| Özellik | Bulgu |
|---|---|
| **Seçenek sayısı** | **Her zaman 4 seçenek: A) B) C) D)**. 88 kt dosyasının ve tüm beceri dosyalarının hiçbirinde A–E (5 şık) yok. (A–E lise/YKS'dir; ortaokul Türkçe = A–D.) |
| **Doğru cevap** | Tek doğru cevap. |
| **Kök (stem) kalıbı** | Uyaran + yönerge cümlesi. Çok yaygın olumsuz kalıplar: *"…hangisinde … kullanılmamıştır?"*, *"…hangisi yanlıştır?"*, *"…hangisine değinilmemiştir / ulaşılamaz / söylenemez?"*, *"…hangisi getirilemez?"*. Olumlu kalıp da var: *"…hangisinde … vardır / kullanılmıştır?"* |
| **Kazanım etiketi** | kt dosyalarında her booklet tek konu; başlıkta konu adı yazılı (ör. "Sözcükte Anlam - 1 (Çok Anlamlılık)"). |
| **Cevap anahtarı formatı** | Basit liste: `1. D  2. D  3. A …` (tema/booklet bazında). |

### Çeldirici (çeldirici / distraktör) tasarımı — gözlemlenen kurallar
1. **Aynı kategoriden seçenekler.** Sözcük anlamı sorusunda 4 şık da aynı sözcüğün farklı cümlelerdeki kullanımıdır; söz sanatı sorusunda 4 dize; metin türü sorusunda 4 kısa paragraf. Öğrenci "kategori dışı" ile eleyemez.
2. **Tek ayırt edici nitelik.** Doğru cevap belirli bir kritere uyan/uymayan tek seçenektir; diğer 3'ü kritere uyar (veya uymaz). Ör. "mecaz kullanılMAMIŞtır" → 3 şıkta mecaz var, 1'inde gerçek anlam.
3. **Makul ama yanlış tuzaklar.** Yardımcı düşünce/çıkarım sorularında çeldiriciler parçada *geçen* ama sorulan ölçüte (ana fikir / değinilen / kesin çıkarım) uymayan doğru-görünen ifadelerdir. Klasik tuzak: parçada söylenene benzeyen ama "kesin olarak çıkarılamayan" aşırı-genelleme.
4. **Ayraç içi anlam eşleştirme.** Sözcük/deyim sorularında seçenek = "cümle (parantez içinde sözlük anlamı)"; 3 eşleşme doğru, 1'i uyuşmaz → yanlış eşleşme aranır.
5. **Numaralı öge kombinasyonları.** "I ve II / Yalnız I / II ve IV" tipi seçenekler (dizelerde/cümlelerde numaralanmış ögeler için).

**Birebir örnek (5. sınıf, kt_1, S1 — Sözcükte Anlam / Çok Anlamlılık):**
> "Kurmak" sözcüğü aşağıdaki cümlelerden hangisinde "Bir şeyi oluşturan parçaları birleştirerek bütün duruma getirmek" anlamında kullanılmıştır?
> A) Dünyanın en büyük devletlerini kuranlar kimlerdi?
> B) Geniş çölde çadırlarımızı kurup keşfe çıktık.
> C) Derneği, ilçede sevilip sayılan bir avukat kurmuştu.
> D) Çocukça bir sevinçle kurduğu saat çalıyor.

---

## 2. PARAGRAF (OKUDUĞUNU ANLAMA) SORULARI — EN KRİTİK BÖLÜM

Türkçe sınavının en büyük ağırlığı **"Parçada Anlam"**tır. Parça uzunluğu sınıfa göre değişir: 5–6. sınıfta **3–8 satır** (tek paragraf), 7. sınıfta **4–10 satır**, 8. sınıfta **çok cümleli, bazen çok paragraflı** ve sık sık **bir metne bağlı 2 soru** ("29 ve 30. soruları aşağıdaki metne göre cevaplayınız"). Aşağıda gözlemlenen paragraf ALT-TÜRLERİ (üretimde bunları hedefleyin):

### 2A. Ana düşünce / ana fikir / "asıl anlatılmak istenen"
Parçanın vermek istediği temel yargı. Fabl/öykü parçalarında "asıl anlatılmak istenen" (özdeyiş/ders) sorulur.
> **6.sınıf kt_15 S7:** Susuzluktan kırılan bir köpek … kendi yansımasını görüp korktuğu için su içemez … kendini suya atar … kana kana su içer. **Bu parçada asıl anlatılmak istenen aşağıdakilerden hangisidir?** A) Gereksiz korkulardan kurtulan insan, amacına ulaşır. …

### 2B. Konu
"Ne hakkında?" → ana fikirden farklı; daha genel/başlıksal.
> **6.sınıf kt_15 S5:** (selamlaşma parçası) **Bu parçanın konusu aşağıdakilerden hangisidir?** A) Etkili iletişim yöntemleri B) Selamlaşmanın önemi C) … (doğru: B)

### 2C. Başlık ("en uygun başlık")
> **6.sınıf kt_15 S2:** (haberciliğin tarihi parçası) **Bu metne verilebilecek en uygun başlık…** A) Haberciliğin Tarihi (doğru) B) Haberciliğin Kuralları …

### 2D. Ana duygu (şiirde) / duygu tespiti
> **6.sınıf kt_15 S3:** "Sivas'ta iplik iplik bir yağmurla…" **Bu dizelerde aşağıdaki duygulardan hangisi yoktur?** A) Özlem B) Yalnızlık C) Korku D) Üzüntü (doğru: C)

### 2E. Yardımcı düşünce / "değinilmemiştir" / "ulaşılamaz" / "söylenemez"
Parçada ele alınMAYAN yan ayrıntı aranır. Çok yüksek frekanslı.
> **6.sınıf kt_15 S9:** (fındık parçası) **…fındıkla ilgili aşağıdakilerden hangisine değinilmemiştir?** A) Nerelerde yetiştirildiğine B) Yıllık üretim miktarına C) … D) Hangi mevsimde meyve verdiğine (doğru: D)

### 2F. Anlatım biçimleri / teknikleri
Betimleme / öyküleme / açıklama / tartışma **ve** karşılaştırma, tanımlama, örneklendirme, benzetme, tanık gösterme, nesnel/öznel anlatım. 6–8. sınıfta yoğun.
> **6.sınıf kt_30 S7:** "Yola çıktığımızda hava kararmak üzereydi…" **Bu parçanın anlatımında aşağıdakilerden hangisine başvurulmuştur?** A) Betimlemeye (doğru) B) Kişileştirmeye C) Örneklendirmeye D) Benzetmeye
>
> **8.sınıf kt_2 S2 (öznel/nesnel):** "Öznel anlatım kişisel görüşler içerir. Nesnel anlatım … kanıtlanabilir yargılarla oluşturulur. **…hangisinde öznel bir anlatıma başvurulmuştur?**" → doğru: C ("…düşünüyor, … sağlanamayacaktır." içeren seçenek).

### 2G. Metin türü tanıma
Hikâye / masal / fabl / haber metni / anı / roman / bilgilendirici vs. öyküleyici (hikâye edici) ayrımı.
> **5.sınıf kt_30 S1:** (Endonezya'da karaya vuran balinalar) **Bu metnin türü…?** A) Hikâye B) Fabl C) Masal D) Haber metni (doğru: D)
>
> **5.sınıf kt_30 S2:** **Aşağıdakilerden hangisi bilgilendirici bir metindir?** (4 kısa paragraf; doğru: D = su döngüsü tanımı).

### 2H. Hikâye unsurları + anlatıcı bakış açısı
Olay / yer / zaman / şahıs; I. veya III. kişi ağzından anlatım.
> **6.sınıf kt_30 S3:** (kardeşlerin oyun parçası) **Bu parçada aşağıdaki hikâye unsurlarından hangisine yer verilmemiştir?** A) Olay B) Yer C) Zaman D) Şahıs
>
> **6.sınıf kt_30 S2:** **…hangisinde olay üçüncü kişinin ağzından anlatılmıştır?**

### 2I. Paragrafta anlam akışı (yapı soruları) — ÇOK sık, kendi alt-grubu
- **Cümle sıralama (olay sırası / giriş-gelişme-sonuç):**
  > **5.sınıf kt_15 S1:** Numaralanmış cümleler olayların oluşuna göre… doğru sıralanmıştır? A) I-III-II-IV …
- **Parça tamamlama** (başa / ortaya boşluğa / sona getirilecek cümle) — "getirilmelidir" veya olumsuz "getirilemez":
  > **5.sınıf kt_15 S7:** "- - - - Çölün kavurucu … sıcağı…" **Bu parçanın başına anlam akışına göre aşağıdakilerden hangisi getirilmelidir?**
  > **5.sınıf kt_15 S8:** "…Dünya hayatının süsüne aldanma… - - - -" **…boş bırakılan yere aşağıdakilerden hangisi getirilemez?**
- **Boşluğa sözcük/söz öbeği getirme (sırasıyla):**
  > **5.sınıf kt_1 S5:** "…balinalar - - - - iletişim kuruyor. Su altında koku iyi bir şekilde - - - -…" **…sırasıyla getirilmelidir?** (doğru: D "şarkı söyleyerek - iletilmediğinden")
- **Anlam bütünlüğünü bozan cümle:**
  > **6.sınıf beceri_1 S8:** (yüzme tarihi, I–IV numaralı) **…hangisi bu parçanın anlam bütünlüğünü bozmaktadır?** (doğru: C — Türkiye'ye özgü tarih cümlesi)
- **Paragrafı ikiye bölme:**
  > **5.sınıf kt_15 S9:** "…Bu parça iki paragrafa ayrılmak istenirse ikinci paragraf kaçıncı cümleyle başlar?"
- **Dağınık cümlelerden anlamlı paragraf / kelime oluşturma** (bazen bulmaca/akrostiş biçiminde):
  > **5.sınıf kt_15 S6:** A, I, K, S harfli cümleler sıralanınca hangi sözcük oluşur? (ASKI/ISKA/KISA/ASIK)
- **Düşünceyi geliştirme yolları** (tanımlama, örneklendirme, karşılaştırma, sayısal veri, benzetme, tanık gösterme) — 8. sınıfta belirgin.

### 2J. Sözcük/söz öbeği anlamı — bağlamdan
Parçada geçen bir sözcüğün/deyimin bağlamdaki anlamı; ya da "yerine kullanılabilir/kullanılamaz".
> **8.sınıf kt_2 S18:** "…çıkış kapılarımıza kilit vurmaktır." **altı çizili ifadenin yerine aşağıdakilerden hangisi getirilebilir?** A) özgürlüklerimize (doğru) …
> **8.sınıf kt_2 S21:** "yüreğinde davullar gümbürder" sözüyle anlatılmak isteneni hangi numaralı sözler karşılar? (I ve II / …)

### 2K. Metne dayalı çıkarım / yargı
"çıkarılabilir / ulaşılabilir / söylenebilir" ya da olumsuzu; ve "kesin olarak çıkarılacak yargı".
> **7.sınıf kt_20 S10:** "Genç ressam, bu yılki ikinci ödülünü yine Ankara'da aldı." **…kesin olarak çıkarılacak yargı?** D) Ankara'da birden fazla ödül almıştır. (doğru: D; A/B/C aşırı-çıkarım tuzağı)

### 2L. Görsel/tablo/grafik/infografik okuma → **kendi bölümü, bkz. §5**

---

## 3. PARAGRAF-DIŞI SORU TÜRLERİ (dil bilgisi, yazım, noktalama, anlam)

Bu türler de çoğunlukla bir cümle/dize/parça içine gömülüdür.

### 3A. Sözcükte anlam
Gerçek/mecaz/terim anlam; çok anlamlılık; eş anlam (anlamdaş); zıt anlam (karşıt); eş seslilik (sesteş); somut/soyut; genel/özel.
> **5.sınıf kt_1 S7:** **…hangisinde altı çizili sözcük mecaz anlamda kullanılmıştır?** (doğru: D "…düşünceleriyle sivrilir")
> **5.sınıf kt_5 S3:** "gaye" sözcüğünün eş anlamlısı? A) amaç (doğru)

### 3B. Söz sanatları
Benzetme (teşbih), kişileştirme (teşhis), konuşturma (intak), abartma (mübalağa), karşıtlık (tezat). 5–6. sınıfta yoğun; genelde dizelerde.
> **5.sınıf kt_5 S8:** **Aşağıdaki dizelerin hangisinde kişileştirme yoktur?**
> **6.sınıf kt_8 S12:** "…Türkçe aşağıdakilerden hangisine benzetilmemiştir?" (Destanlara/Ana sütüne/Dağ başlarına/Bayraklara → doğru: C)

### 3C. Cümlede anlam
Neden-sonuç, amaç-sonuç, koşul-sonuç; öznel/nesnel; kanıtlanabilirlik; anlamca en yakın cümle; duygu (yakınma, pişmanlık, hayıflanma, şaşırma, özlem); kesin yargı; varsayım/olasılık; öneri/eleştiri.
> **7.sınıf kt_20 S8:** **Aşağıdaki dizelerin hangisinde neden-sonuç ilişkisi yoktur?**
> **7.sınıf kt_20 S11:** **…hangisi kanıtlanabilirlik açısından diğerlerinden farklıdır?** (doğru: A — öznel yargı)
> **5.sınıf beceri_1 S7:** "hayıflanma" tanımı verilir → **hangisinde hayıflanma anlamı vardır?** (doğru: D)

### 3D. Sözcük yapısı / kök-ek (biçim bilgisi)
İsim/fiil kökü; yapım eki vs. çekim eki; iyelik eki, hâl eki, çoğul eki, soru eki; basit/türemiş/birleşik sözcük; ek işlevi.
> **5.sınıf kt_10 S3:** **…hangisinde yapım eki yoktur?**
> **6.sınıf kt_22 S1:** **…hangisi hem yapım hem de çekim eki almıştır?**
> **6.sınıf kt_22 S5:** (dizelerde I/II/III) **…sözcüklerin yapısı** (Basit/Türemiş/Birleşik) tablo-eşleştirme.

### 3E. Ses bilgisi (özellikle 5. sınıf)
Ünlü düşmesi, ünlü daralması, ünsüz yumuşaması (değişimi), ünsüz benzeşmesi (sertleşmesi), ünsüz türemesi. Kural açıklaması verilip örnek istenir.
> **5.sınıf kt_20 S4:** "…'kitap' sözcüğüne aşağıdaki eklerden hangisi getirilirse ünsüz yumuşaması meydana gelir?"

### 3F. Sözcük türleri / dil bilgisi (7–8. sınıf ağırlıklı)
Zarf (durum/zaman/yer-yön/miktar/soru), sıfat, isim, edat/bağlaç; fiilimsi; **fiil çatısı** (etken/edilgen, geçişli/geçişsiz — 8. sınıf); cümle ögeleri; **cümle türleri** (kurallı/devrik, isim/fiil cümlesi — 8. sınıf).
> **7.sınıf kt_10 S1:** "kolay" sözcüğü hangi cümlede **zarf görevinde** kullanılmıştır?
> **7.sınıf kt_10 S8:** numaralı zarfların türleri (Zaman/Durum/Miktar/Yer-yön) sırasıyla eşleştirme.

### 3G. Yazım kuralları & noktalama (7–8. sınıf ağırlıklı)
Noktalama işaretlerinin işlevleri (özellikle **virgül, üç nokta, kesme işareti, eğik çizgi**); büyük harf; yazım yanlışı bulma; parantezlere işaret yerleştirme.
> **7.sınıf kt_30 S1:** Konuşmada ( ) yerlere sırasıyla hangi noktalama işaretleri? (-)(?)(...)(!) tarzı.
> **8.sınıf kt_2 S40:** 4 büyük-harf kuralı verilip **…hangisinde yazım yanlışı vardır?**

### 3H. Deyim / atasözü
Anlam eşleştirme; metne katkı; atasözüyle çelişen/uyuşan.
> **5.sınıf beceri_1 S3:** 3 deyim anlamı verilir → **…hangisinde bu açıklamaları karşılayan bir deyim kullanılMAMIŞtır?** (doğru: A "ağzını bıçak açmıyordu")

---

## 4. SINIF İLERLEYİŞİ (5 → 8)

| Boyut | 5. sınıf | 6. sınıf | 7. sınıf | 8. sınıf (LGS tarzı) |
|---|---|---|---|---|
| **Booklet yapısı** | 28 kt, her biri 2 sayfa, **tek konu, 12 soru** | 28 kt, aynı | 27 kt, aynı | **8 kt = 8 TEMA**, 12–26 sayfa, **40–53 karışık soru** |
| **Parça uzunluğu** | Kısa (3–6 satır) | Kısa-orta | Orta (4–10 satır) | Uzun, çok cümleli, **metne bağlı 2 soru** blokları |
| **Baskın konular** | Sözcükte anlam, söz sanatları temel, kök-ek, **ses bilgisi**, metin türleri, paragrafta sıralama | + biçim bilgisi (ekler), parçada anlam (ana fikir/konu/başlık), anlatım özellikleri, tür karşılaştırma | + zarflar, cümlede anlam (neden/amaç-sonuç, öznel/nesnel, kanıtlanabilirlik), noktalama | + **fiil çatısı, cümle türleri, anlatım bozukluğu, düşünceyi geliştirme yolları**; ağır çıkarım |
| **Bilişsel düzey** | Tanıma/bulma | Bulma + yorum | Yorum + karşılaştırma | **Çok adımlı çıkarım, sentez, mantık** |
| **Görsel yükü** | Düşük (tablo/dize numaralama) | Düşük-orta | Orta | **Yüksek** (§5) |

**Not (müfredat geçişi):** 3. parti "Yazılıya Hazırlanıyorum" dosyaları yeni **2024 TYMM** kazanım kodlarını kullanıyor: 5–6. sınıf `T.O.x` (okuma) / `T.Y.x` (yazma) biçiminde; 8. sınıf hâlâ eski `T.8.3.x / T.8.4.x` kodlarını kullanıyor (geçiş dönemi). Üretimde konu ekseni için TYMM üniteleri esas alınmalı.

---

## 5. GÖRSEL İÇERİK (RENDER İÇİN KRİTİK)

Görsel yükü **kaynak tipine ve sınıfa** göre çok değişir:

- **kt 5/6/7 (kazanım testleri):** Ağırlıkla düz metin. Görsel = (a) dize/parça içinde sözcüklerin altına yerleştirilmiş **I, II, III, IV numaralandırması**; (b) gramer için küçük **tablolar** (ek tablosu, sözcük sınıflama); (c) ara sıra **bulmaca/harf kutusu** (akrostiş, çengel). Bunlar metinle üretilebilir.
- **kt 8 (tematik) + TÜM beceri dosyaları:** **Yüksek görsel yoğunluğu.** Gözlemlenen görsel türleri:
  - **İnfografik / bilgilendirme grafiği** (simge + açıklama eşleştirme; ör. 8.kt_2 S4 "2023 Eğitim Vizyonu"),
  - **Harita / kroki** (yol tarifi; 8.kt_2 S5),
  - **Tablo** (balık pişirme, kan grubu-besin, kulüp katılım sayıları),
  - **Sütun/çizgi grafik** (kan bağışı; egzersiz süresi grafiği),
  - **Zaman çizelgesi / timeline** (sanatçı biyografisi; 8.kt_2 S36),
  - **Mantık kurgusu / logic-grid** (kim-hangi-nerede; 8.kt_2 S6, S16, S22),
  - **Algoritma / akış şeması** (8.kt_2 S12),
  - **Şıkları görsel olan sorular** (A/B/C/D birer resim/tablo/grafik — ör. kübizm eseri seçme, simetri, çizim yorumu),
  - **Özel görseller:** dijital saat 7-segment (7.beceri_1 S1), altıgen kelime oyunu (8.kt_2 S47), afiş/poster, ürün görselleri.

**Üretim açısından uyarı:** 8. sınıf ve beceri sorularının kabaca **%30–40'ı görsele bağımlıdır** ve şıkları resim olan sorular metinle yeniden üretilemez. Generator ya (a) görsel gerektirmeyen alt-türlere odaklanmalı, ya da (b) **metinle ifade edilebilir görselleri** üretebilmeli: tablo (Markdown/HTML tablo), sayısal veri listesi, inline SVG basit grafik/harita, zaman çizelgesi. Saf-görsel (resim şıklı) türler MC üretiminde atlanmalı veya metinsel eşdeğere (tablo/veri) çevrilmeli.

---

## 6. BİREBİR ÖRNEKLER + DOĞRULANMIŞ CEVAPLAR (few-shot çekirdeği için)

Cevaplar, ilgili cevap anahtarı dosyalarından doğrulanmıştır (beceri: `*_ca.pdf`; 8.sınıf: `turk_ca.pdf` "2. Tema").

**[Sözcükte anlam – çok anlamlılık] 5.sınıf kt_1 S1** → cevap yok (5/6/7 kt cevap anahtarı repoda yok). Kök: bkz. §1 örnek.

**[Görselden çıkarım / infografik] 5.sınıf beceri_1 S8** (En Zor Dil infografiği):
> Bu bilgilerden hareketle aşağıdakilerin hangisine ulaşılabilir?
> A) Türkçe en çok konuşulan dillerin başında gelir. B) Baskçanın kendine özgü bir yapısı vardır. C) Arikapu, dünyada konuşulan en eski dildir. D) Dünyada en çok konuşulan dil, en zengin dildir.
> **Doğru: B** (5_ca 1.Tema S8=B). *Çeldirici mantığı: A/C/D infografikte olmayan aşırı-genellemeler; B doğrudan desteklenir.*

**[Yardımcı düşünce / değinilmemiştir] 5.sınıf beceri_1 S6** (nesli tükenen hayvanlar):
> Bu parçada aşağıdakilerin hangisine değinilmemiştir?
> A) Hayvan soylarının tükenmesinin iklim değişikliğine yol açtığına … (doğru: **A** — parçada tersi ilişki var: iklim değişikliği tükenmenin nedeni.)

**[Duygu – hayıflanma] 5.sınıf beceri_1 S7** → **D** (5_ca=D).

**[Metin içi çıkarım – sorunun cevabı yok] 5.sınıf beceri_1 S10** (somon balıkları) → **A** ("dönme nedeni" metinde yok).

**[Öznel/nesnel anlatım] 8.sınıf kt_2 S2** → **C** (turk_ca 2.Tema S2=C).

**[Kelime anlamı – kullanılmamıştır] 8.sınıf kt_2 S1** ("çalakalem/dört başı mamur/az söz…"):
> Bu metinde aşağıdakilerden hangisinin anlamını karşılayan bir söz kullanılmamıştır? A) Gelişigüzel B) Anlaşılması güç C) Kısa ve öz anlatım D) Eksiksiz, kusursuz
> **Doğru: B** (turk_ca 2.Tema S1=B).

**[Mantık kurgusu – logic grid] 8.sınıf kt_2 S6** (spor müsabakaları, 5 kişi/şehir/branş) → **D** (S6=D). *Not: metinle üretilebilir ama çözümü çok-adımlı mantık gerektirir; kalite kontrolü şart.*

**[Tablo okuma + mantık] 8.sınıf kt_2 S16** (balık tava/ızgara tablosu) → **C** (S16=C).

**[Söz sanatı – kişileştirme yoktur] 5.sınıf kt_5 S8** → cevap anahtarı yok; kök §3B'de.

**[Anlatım özellikleri – söylenemez] 6.sınıf kt_30 S10** (zekâ parçası):
> Bu parçayla ilgili aşağıdakilerden hangisi söylenemez? A) Nesnel anlatım B) Tanımlama C) Karşılaştırma D) Benzetme (kalıp: 3 teknik var, 1'i yok).

---

## 7. GENERATOR İÇİN ÖZET KURALLAR (checklist)

1. **Format:** Tek doğru cevaplı, **4 şık (A–D)**. Asla A–E üretme.
2. **Kök kalıbı:** Uyaran (parça/dize/cümle/tablo) + "aşağıdakilerden hangisi…" yönergesi. Olumsuz kökleri (yanlıştır/değildir/kullanılmamıştır/değinilmemiştir/söylenemez) bolca kullan — kaynakta çok yaygın.
3. **Çeldiriciler:** 4 şık aynı kategoriden, dilbilgisel olarak makul; doğru cevap tek ayırt edici. Çıkarım sorularında "parçada geçen ama ölçüte uymayan" ve "aşırı-genelleme" tuzakları koy.
4. **Ağırlık dağılımı (kaynağa uygun):** Parçada anlam (§2) en yüksek pay; ardından sözcükte/cümlede anlam, söz sanatları, dil bilgisi, yazım-noktalama. Sınıf profiline göre ayarla (§4 tablosu).
5. **Sınıf kalibrasyonu:** 5. sınıf kısa parça + ses bilgisi/kök-ek; 8. sınıf uzun parça + çıkarım + fiil çatısı/cümle türleri/anlatım bozukluğu.
6. **Görsel:** Saf-görsel (resim şıklı) türlerden kaçın; tablo/veri/zaman-çizelgesi gibi metinle ifade edilebilir görselleri tercih et.
7. **Dil:** Kaynaktaki resmî, ölçme-değerlendirme üslubunu koru ("Bu parçada / Bu dizelerde / Buna göre / Aşağıdakilerden hangisi…").

---

## 8. 3. PARTİ HEX DOSYALARI — DÜRÜST DEĞERLENDİRME

`{5,6,7,8}.sinif/<hex>.pdf` dosyaları **çoktan seçmeli soru bankası DEĞİLDİR.** Bunlar MEB **Temel Eğitim Genel Müdürlüğü (TEGM)** tarafından hazırlanan **"YAZILIYA HAZIRLANIYORUM"** (yazılı sınav öncesi hazırlık) çalışmalarıdır ve üzerinde açıkça **"Örnek soru niteliği taşımamaktadır"** yazar. İçerik:
- **Açık uçlu / kısa cevaplı** sorular (sözcük anlamı tahmini, özetleme, mesaj yazma, tür belirleme + gerekçe),
- **Boşluk/tablo doldurma** (noktalama yerleştirme, çatı tablosu, kurallı/devrik işaretleme),
- **Doğru/Yanlış (D/Y)** tablo-yorumlama,
- **Yazma görevleri** (haber metni, bilgilendirici metin),
- Her dosyanın sonunda **ÇÖZÜMLER** (model cevaplar) ve **ÖĞRENME ÇIKTISI** kodları.

**Sonuç:** MC few-shot korpusu için **kullanılamaz** (soru tipi uyuşmuyor). Ancak değerlidir çünkü: (a) güncel **TYMM kazanım kodları** taksonomisini verir; (b) sınıf-uygun **parça/metin üslubunu** ve konu senaryolarını gösterir; (c) ileride **açık uçlu / D-Y / tablo** soru tipi eklenirse doğrudan şablon olur. Bu dosyalar MC üretimi için değil, **metin havuzu + kazanım eşlemesi** için ingest edilmelidir.
