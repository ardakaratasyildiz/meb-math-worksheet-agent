# İngilizce — Soru Yapısı Analizi (MEB, 5-8. Sınıf)

> Tarih: 2026-07-10. Amaç: worksheet-generator için resmî MEB İngilizce soru
> kaynaklarının **soru yapısını** karakterize etmek (few-shot + prompt/critic tasarımı).
> Kaynaklar `knowledge_base/Ingilizce/` altında (bkz. `SOURCES.md`).
> Yöntem: gömülü metin (PyMuPDF) + 8. sınıf cevap anahtarı.

## 0. Taranan kaynaklar ve dürüst kapsam notu

| Kaynak | Konum | Format | Cevap anahtarı | Taranan örnek |
|---|---|---|---|---|
| EBA ünite örnek soruları 8 | `ornek_sorular/8.sinif/unite_1..10` | **Çoktan seçmeli (A-D)** | ✅ `cevap_anahtari.pdf` (tam) | u1, u5, u9 + tüm CA |
| EBA ünite örnek soruları 5/6/7 | `ornek_sorular/{5,6,7}.sinif/unite_1..12` | **Çoktan seçmeli (A-D)** | ❌ ayrı CA yok | 5: u1,u5,u9 / 6: u1,u6,u11 / 7: u1,u4,u10 |
| ÖDSGM beceri temelli 5/6/7 | `sorular/{5,6,7}.sinif/beceri_1..10` | **Çoktan seçmeli (A-D), parça-yoğun** | ❌ ayrı CA yok | 5: beceri_1 / 6: beceri_3 / 7: beceri_5 |
| Hex-adlı "3rd-party" dosyalar | `{5,6,8}.sinif/*.pdf` | **AÇIK UÇLU** — MC DEĞİL | ✅ bazı dosyalarda ÇÖZÜM | 5: 0903c3cd3c / 6: 4ee7f2341b / 8: 029124c433 |

**⚠️ Önemli düzeltme (görev varsayımı yanlış):** Hex-adlı dosyalar üçüncü-taraf soru
bankası **değildir**. Bunlar MEB **Temel Eğitim Genel Müdürlüğü**'nün resmî
**"YAZILIYA HAZIRLANIYORUM"** (yazılı sınav öncesi hazırlık) materyalleridir ve
**çoktan seçmeli içermez** — fill-in-the-blank, kısa cevap, tablo doldurma, eşleştirme,
paragraf yazma soruları içerir; TYMM öğrenme çıktı kodlarıyla (`E6.1.R1`, `E8.7.R1` vb.)
etiketlidir ve bazılarında tam ÇÖZÜM (answer key) vardır. Ayrıca üzerlerinde
"Örnek soru niteliği taşımamaktadır" ibaresi bulunur. **MC worksheet few-shot'u için
kullanılmaz; yazma/açık-uçlu üretim ekseni için ayrı bir kaynaktır.**

Not: 5/6/7 EBA setleri ile beceri setleri **eski (2018) program ünite adlarını**
taşır (Hello!, My Town, Games and Hobbies…). Yalnızca 8. sınıf, görevde listelenen
TYMM tema adlarını kullanır. Bu, TYMM'e hizalarken crosswalk gerektirir (bkz. §6).

---

## 1. Çoktan seçmeli (MC) mantığı

**Ortak iskelet (tüm sınıflar, EBA + ÖDSGM):**
- **4 seçenek: A) B) C) D)**, **tek doğru cevap**. (Fen/LGS ile aynı 4'lü yapı.)
- Kök çoğunlukla **boşluk tamamlama** biçiminde: cümle `- - - -.` ile biter ve
  seçenekler boşluğu doldurur. Bu, İngilizce MC'nin **en yaygın kalıbıdır**.
- **Yönerge dili:** neredeyse tamamen **İNGİLİZCE** ("For questions 1-5, choose the
  best option to fill in the blanks.", "Read the text and answer the question.",
  "Which of the following is CORRECT?"). Türkçe yönerge yok denecek kadar az; Türkçe
  yalnızca görsel içi realia'da (poster) ara sıra görülür (ör. 8/u1'de bir posterde
  "satranç, balık tutma" gibi TR sözcükler bilinçli çeldirici olarak).
- **Kök dili:** %100 İngilizce. Sorular tema/işlev temelli, dilbilgisi terimi geçmez
  (öğrenciden "present simple" değil, "günlük rutin ifadesini seç" beklenir).

**Cevap anahtarı formatı (8. sınıf, doğrulanmış):**
```
ENGLISH ANSWER KEY
Unit 1
1. D   2. A   3. B   4. C   5. B   6. D   7. D   8. D  ...  32. C
Unit 2 ... Unit 10
```
Düz `soru_no. harf` listesi, ünite başlıklı. Doğru-cevap dağılımı dengeli
(u1'de A×5, B×8, C×9, D×10 — belirgin bir "hep C" biası yok).

**Çeldirici (distractor) tasarımı — gözlemlenen desenler:**
1. **Anlam-yakını / aynı kategori çeldirici:** doğru cevapla aynı sözcük alanından
   (ör. hava durumu: sunny/rainy/windy/freezing — hepsi geçerli sıfat, biri bağlama uyar).
2. **NOT / EXCEPT / CANNOT kalıbı** (çok yaygın, özellikle 6-8): "Which of the following
   does **NOT** have an answer in the text?" / "which is **NOT** correct?" — öğrenci
   metinde geçmeyeni/çelişeni bulur. Çeldiriciler metinde **açıkça geçen** doğru
   bilgilerdir; tuzak, "cevabı olmayan" olanı ayırt etmektir.
3. **Soru-cevap uyumsuzluğu (functional):** diyalogda bir replik verilir, öğrenci onu
   doğuran soruyu/yanıtı seçer; çeldiriciler dilbilgisel olarak doğru ama işlevsel
   olarak yanlış yanıtlardır ("What time is it?" → "It is at Sunshine Theatre" çeldirici).
4. **Çıkarım gerektiren çeldirici (8. sınıf):** seçenekler metni yeniden ifade eder
   (paraphrase); yüzeysel eşleşme yerine anlam eşleşmesi gerekir.
5. **Sayısal/tablo tuzağı:** grafik/anket verisiyle "less/more/half/25%" ifadelerini
   yanlış eşleyen çeldiriciler (8/u5 internet anketleri).

---

## 2. Soru tipleri taksonomisi (gözlemlenen sıklıkla)

Sıklık nitel: ⬤⬤⬤ = çok yaygın, ⬤⬤ = yaygın, ⬤ = ara sıra.

### A. Vocabulary / functional gap-fill (boşluk doldurma) — ⬤⬤⬤
Kısa bağlamda sözcük veya işlevsel ifade seçimi. En temel tip (özellikle 5-6).
> **[G6/u11, weather]** "Wear your sunglasses because the weather is - - - -.
> A) sunny B) lightning C) rainy D) windy" → **A**
> **[G6/u11]** "William: - - - -? Sophia: It's ten degrees Celsius.
> A) How many hours… B) How do you feel… C) What's the temperature D) What's the day today" → **C**

### B. Dialogue / conversation completion (diyalog tamamlama) — ⬤⬤⬤
İki-üç kişilik replik; eksik repliği/soruyu seç. İşlevsel dil çekirdeği.
> **[G5/u1]** "Maria: - - - -? Brad: Brad Mc Carty.
> A) What is your name B) Where are you from C) What do you like D) How old are you" → **A**
> **[G8/u1, friendship]** Blake–Arthur planlaması: "Arthur: - - - -.
> Which completes the conversation? … C) That sounds great but I have to train for the tournament …" → doğru: bağlam-uyumlu ret+gerekçe.

### C. Reading comprehension — kısa metin/e-posta/biyografi — ⬤⬤⬤
Kısa paragraf + 1-3 soru. Alt-tipler: ana fikir/başlık, detay bulma, çıkarım,
"cevabı olmayan soru".
> **[G8/u5, internet]** Metin sonrası: "What can be the best title for the text?
> A) Dangerous Effects… B) Disadvantages of Internet on Young People C)… D)…" → **B**
> **[G7/u4]** "Which of the following does NOT have an answer in the text? …
> C) What does Emre look like?" → doğru: metinde görünüş anlatılmaz.

### D. "Realia" / doküman okuma — davetiye, poster, ilan, web sitesi, TV rehberi — ⬤⬤⬤ (8) / ⬤⬤ (5-7)
Görsel-metin (invitation card, poster, job ad, cinema listing, channel schedule).
8. sınıfta baskın; LGS stili. Sık kalıp: "Which does NOT have an answer in the poster?"
> **[G8/u1]** Mountain-bike posteri: "Which of the following does NOT have an answer
> in the poster? A) How long is the trip? B) Is there anything to eat? C) How can we
> learn details? D) Which equipment do we need?" → **A**
> **[G8/u1]** Cinema listing (Drama/Action/SciFi/Comedy, yaş+saat) → iki kişiye uygun
> filmi seç. Tablo/çizelge okuma + kısıt eşleştirme.

### E. Visual → sentence (görsel temelli) — ⬤⬤ (5-7'de belirgin)
Resimden eylem/nesne/saat okuma. Metin PDF'te görsel yerine boşluk/etiket kalır.
> **[G5/u9]** "Christopher - - - - every morning. A) has a shower B) gets on the bus
> C) washes his face D) brushes his teeth" (resme göre) — sınıf 5'te saat okuma da:
> "It's - - - -. A) seven o'clock B) half past seven C) quarter to seven D) quarter past seven"
> **[G7/u1]** "'Sarah has got curly blonde hair.' Which girl is Sarah? A)B)C)D)" (4 resim)

### F. Functional language — istek/öneri/kabul-ret/karşılaştırma/tarif — ⬤⬤
İşlev odaklı: yön tarifi (5/My Town), teklif+kabul/ret (6/breakfast, 8/friendship),
karşılaştırma (6/downtown comparatives), tarih söyleme (7/biographies).
> **[G6/u6]** "Mark: Would you like some orange juice? Alice: No thanks…
> Mark: - - - -? Alice: It is my favourite drink…" → **B) Would you like some pancakes**
> **[G7/u10]** Tarih okuma: "graduated … on the - - - -. D) nineteenth of June, nineteen seventy-five" → **D**

### G. Sıralama / eşleştirme / uyumsuz cümle (grammar/coherence in use) — ⬤⬤
Cümle sıralama, tabloya kişi eşleme, "irrelevant/odd sentence" bulma.
> **[G5/u1]** "Choose the irrelevant sentence: (I)…(II)…(III) I think math is difficult.(IV)…" → **C**
> **[G5/u1]** Selamlaşma sıralaması: "III-IV-I-II?" → doğru sıra.

### H. Çoklu-kişi / mantık-eşleştirme (çıkarım-yoğun) — ⬤⬤⬤ (8'de baskın)
Birden çok kişi replik/tablo verir; kısıtları eşleyip "kim/hangisi" sorulur. LGS'nin
imza tipi. Yüksek bilişsel yük (çıkarım + eleme).
> **[G8/u1]** 5 arkadaş davete cevap verir → "Who refuses the invitation by giving an
> excuse?" → çoklu-seçim (Julia, Sophia, Rose).
> **[G8/u1]** İş ilanı + 4 aday profili → "who is the most appropriate person for the job?"
> (yaş+deneyim+kişilik kısıtlarını eşle) → **C) George**
> **[G7/u5, TV]** Kanal çizelgesi + aile tercihleri → "Which channel can they watch together?"

### I. Grafik/anket/sayısal veri yorumu — ⬤⬤ (8) / ⬤ (7)
Bar/pie/anket verisi → doğru/yanlış ifade veya doğru grafiği seçme.
> **[G8/u5]** "A hundred people joined a survey… Which statement is NOT correct?"
> (Kind 25 / Generous 10 / Funny 45 / Helpful 20 verisiyle) → yüzde/karşılaştırma çeldiricileri.
> **[G8/u5]** "Which graph shows the results of the article?" (4 bar grafik seçeneği)

---

## 3. Görsel içerik yoğunluğu (render açısından kritik)

Görsel bağımlılığı sınıfla **artar** ve worksheet üretiminde en zor kısımdır:

- **5-6. sınıf:** saat kadranları, tek nesne/eylem resimleri, basit haritalar
  (My Town yön tarifi), bayraklar. Görsel çoğu kez "seçeneği resme göre seç" biçiminde.
- **7. sınıf:** kişi portreleri (görünüş), TV çizelgeleri, timetable tabloları.
- **8. sınıf (LGS):** **realia yoğun** — invitation card, poster, ilan, web sitesi ekranı,
  telefon ekranı, sinema/kanal çizelgesi, anket formu, bar/pie grafik, kişi-özellik
  tabloları. Bir ünitenin (u1 Friendship) 32 sorusunun büyük kısmı görsel/tablo içerir.

**Üretim çıkarımı:** MC üretiminde görsel-bağımlı sorular **metin-tabloya çevrilebilir**
olmalı (davetiye/çizelge → HTML tablo/kutu; grafik → sayısal liste). Saf resim gerektiren
(portre, "hangi kız Sarah") tipler ya SVG ile üretilmeli ya da düşük öncelikli tutulmalı.
Fen'deki inline-SVG deseni burada da geçerli (özellikle poster/kart layout'ları).

---

## 4. Sınıf ilerlemesi (5 → 8)

| Boyut | 5. sınıf | 6. sınıf | 7. sınıf | 8. sınıf (LGS) |
|---|---|---|---|---|
| Kök uzunluğu | 1 cümle / kısa diyalog | kısa diyalog | orta metin | **çok-kişi + realia + tablo** |
| Metin türü | tek cümle, mini-tablo | mini paragraf, tablo | paragraf, timetable | e-posta, poster, ilan, grafik, anket |
| Bilişsel yük | tanıma/hatırlama | anlama | anlama + basit çıkarım | **çıkarım + eleme + çoklu-kısıt eşleme** |
| Baskın tip | A gap-fill, B diyalog, E görsel | A/B + F fonksiyon + karşılaştırma | C okuma + F + tarih/biyografi | D realia + H çoklu-kişi + I grafik |
| NOT/EXCEPT sıklığı | düşük | orta | yüksek | **çok yüksek** |
| Seçenek uzunluğu | kısa kelime öbeği | öbek | cümle | **tam cümle / paraphrase** |

Kısacası: 5-6 = **sözcük/işlev tanıma**; 7 = **okuma+işlev**; 8 = **gerçek-dünya
metinlerinde çıkarımlı okuma** (LGS profili). Üretici sınıfa göre kök karmaşıklığını,
seçenek uzunluğunu ve NOT/çıkarım oranını ölçeklemeli.

---

## 5. Tema/işlev hizalaması (dilbilgisi değil, ünite teması)

Sorular **soyut dilbilgisi değil, ünite teması/işlevi** etrafında kurulur. Gözlemlenen
ünite başlıkları (örnek soru setlerinden):

- **5. sınıf (eski program adları):** Hello! · My Town · Games and Hobbies · My Daily Routine
- **6. sınıf:** Life · Yummy Breakfast · Downtown · Weather and Emotions
- **7. sınıf:** Appearance and Personality · Sports · Biographies · Wild Animals
- **8. sınıf (TYMM tema adları):** Friendship · Teen Life · In the Kitchen · On the Phone ·
  The Internet · Adventures · Tourism · Chores · Science · Natural Forces

Her tema, dilbilgisini örtük taşır (ör. Friendship → present simple + sıklık zarfları +
davet/kabul-ret işlevi; Biographies → past simple + tarihler; Downtown → karşılaştırma
sıfatları; Weather → hava durumu sıfatları). **Üretim etiketi konu değil ünite/tema
olmalı** (Fen deseni, `app/data/units.py`).

---

## 6. Worksheet-generator için çıkarımlar (özet)

1. **Şablon = boşluk-tamamlamalı 4'lü MC (A-D), İngilizce kök + İngilizce yönerge,
   tek doğru.** Türkçe yönerge kullanma.
2. **Tema-güdümlü üret:** her soru bir üniteye/işleve bağlı olmalı; dilbilgisini örtük ver.
3. **Sınıfa göre ölçekle:** 5-6 kısa/tanıma, 7 okuma, 8 realia+çıkarım+NOT/EXCEPT.
4. **NOT/EXCEPT/CANNOT kalıbını** açıkça destekle — resmî setlerin imza tipi;
   çeldiriciler "metinde geçen doğru bilgiler", doğru cevap "geçmeyen/çelişen".
5. **Realia'yı yapılandırılmış layout'a çevir** (davetiye/poster/çizelge → HTML kutu/tablo,
   grafik → sayı listesi); saf resim tiplerini SVG veya düşük öncelik.
6. **Crosswalk gerekli:** 5/6/7 kaynak setleri eski program ünite adlarını taşır → TYMM
   ünite/tema adlarına eşle.
7. **Açık-uçlu eksen ayrı:** hex-adlı YAZILI-prep dosyaları (fill-in/kısa-cevap/yazma,
   TYMM `E*.R*/W*` çıktı kodlu, ÇÖZÜM'lü) MC değildir — writing/open-ended üretim
   modu için ayrı few-shot kaynağı olarak değerlendir.
8. **Few-shot altını 8. sınıf** oluşturur (tam cevap anahtarı + LGS profili). 5/6/7'de
   ayrı cevap anahtarı yok → kalite kontrolünde bu setlerin cevabı doğrulanamaz;
   critic/self-check ile telafi et.

---

## En kritik tek içgörü

**MEB İngilizce MC'si "dilbilgisi testi" değil, ünite-teması içinde bağlam ve işlev
testidir.** Kök neredeyse her zaman `- - - -` boşluklu bir cümle/diyalog ya da kısa bir
realia (davetiye/poster/tablo/grafik) üzerine kuruludur; çeldiriciler aynı sözcük
alanından/temadan seçilir ve öğrenci **anlamı bağlamda** (soru-yanıt uygunluğu, "cevabı
olmayan soru", çıkarım) ayırt eder. Sınıf yükseldikçe değişen şey gramer değil,
**metnin gerçekçiliği ve gereken çıkarım derinliğidir** — 8. sınıf, çoklu-kişi/realia
üzerinde eleme-çıkarım gerektiren LGS profiline ulaşır. Üretici bu yüzden tema+işlev+sınıf
üçlüsüne göre koşullanmalı, soyut gramer konusuna göre değil.
