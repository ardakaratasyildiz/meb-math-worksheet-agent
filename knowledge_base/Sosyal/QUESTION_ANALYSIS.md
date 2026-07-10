# Sosyal Ekseni — Soru Yapısı Analizi (QUESTION_ANALYSIS)

> Tarih: 2026-07-10. Amaç: worksheet-generator'ı beslemek için resmî MEB "Sosyal"
> ekseni soru kaynaklarının **soru yapısını** karakterize etmek. Metin gömülü PDF'lerden
> PyMuPDF (fitz) ile çıkarıldı; görseller (harita/tablo/resim) metin dökümünde kaybolur,
> bu yüzden görsel bağımlılığı ayrıca not edildi.

## 0. Ders–sınıf haritası (KRİTİK doğruluk gereksinimi)

| Sınıf | Ders | MC soru bankası durumu |
|---|---|---|
| 1, 2, 3 | **Hayat Bilgisi** | ❌ MC örnek soru bankası YOK (aşağıda not) |
| 4 | **Sosyal Bilgiler** | ❌ EBA'da yok (kaynakta 404 — SOURCES.md md.4/1) |
| 5, 6, 7 | **Sosyal Bilgiler** | ✅ EBA kazanım testleri (MC) |
| **8** | **T.C. İnkılap Tarihi ve Atatürkçülük** | ✅ EBA kazanım testleri (MC) + CA |

**⚠️ 8. sınıf = İNKILAP TARİHİ, "Sosyal Bilgiler" DEĞİL. Doğrulandı (§4).**

---

## 1. Kaynak envanteri ve gerçek içerik türü

Analiz, iki temelde FARKLI soru türü barındıran kaynakları ayırt eder:

### A) Çoktan seçmeli (MC) — `ornek_sorular/{5,6,7,8}.sinif/kazanim_testi_unite_*.pdf`
EBA ünitelendirilmiş **kazanım testleri**. **Tek gerçek MC kaynağı.** Şık A–D, tek doğru.
- 5. sınıf: 8 test (~94 MC) — öğrenme alanı: *Birey ve Toplum* (1–4), *Kültür ve Miras* (1–4)
- 6. sınıf: 8 test (~95 MC) — *Birey ve Toplum*, *Kültür ve Miras*
- 7. sınıf: 7 test (~84 MC; **ünite 2 kaynakta yok/404**) — *Birey ve Toplum*, *Kültür ve Miras*
- 8. sınıf: 6 test (~160 MC) — İnkılap 6 ünitesi (§4)

### B) Açık uçlu (MC DEĞİL) — `*_ornek_sinav*.pdf`, `*_ornek_2025.pdf`
ÖDSGM **ortak yazılı senaryo** kitapçıkları (5,6,7,8). Kendi metinleri açıkça şunu der:
> *"Çoktan seçmeli, eşleştirme, doğru/yanlış gibi diğer soru türleri kesinlikle
> kullanılmayacaktır."*
Yani bunlar **açık uçlu / kısa cevaplı** yazılı örnekleridir; MC değildir. Kazanım
etiketli senaryo + açık uçlu soru formatı. (few-shot için "açık uçlu" modda değerli;
MC üretimi için kullanılmaz.)

### C) Açık uçlu (MC DEĞİL) — hex adlı dosyalar `{5,6,8}.sinif/<hex>.pdf`
**Bunlar 3. parti/telifli soru bankası DEĞİL.** MEB **Temel Eğitim Genel Müdürlüğü
"YAZILIYA HAZIRLANIYORUM"** yazılı-öncesi hazırlık setleridir (resmî). Açık uçlu +
tablo doldurma + boşluk doldurma; **ÇÖZÜMLER (cevap) ve yeni TYMM kazanım kodları
(örn. `SB.5.3.2`, `SB.5.4.1`) gömülü.** (Not: 7.sinif klasöründe hex dosya YOK; oradaki
tek dosya ders kitabıdır.)

### D) Cevap anahtarı — `sorular/{5,6,7}_sos_beceri_cevap.pdf`
ÖDSGM 2019–2020 "beceri temelli sorular" **yalnızca cevap anahtarı** (A–D harf
tabloları, ünite başına ~20 soru). **Soru metinleri YOK** (kaynakta 403). Bu anahtarlar
`kazanim_testi_unite_*` testlerine AİT DEĞİLDİR (ayrı, farklı soru seti).

### Cevap anahtarı durumu (MC testleri için)
- 8. sınıf: ✅ `kazanim_testi_cevap_anahtari.pdf` — 6 ünite tam (aşağıda doğrulandı).
- 5/6/7. sınıf: ❌ kazanım testleri için **ayrı cevap anahtarı YOK** (kaynakta 404).
  → 5/6/7 MC örneklerinde "doğru cevap" *çıkarımdır*, resmî anahtarla doğrulanmadı.

### Hayat Bilgisi (1–3)
Resmî ünitelendirilmiş MC örnek soru **bulunamadı** (EBA'da HB kazanım testi/örnek soru
yok — SOURCES.md md.4/2). Bu eksen için few-shot yalnızca ders kitabı + 2024 TYMM
programından türetilebilir. **1–3 için MC şablonu 4–7 deseninden uyarlanmalı.**

---

## 2. MC (şıklı) mantığı — Sosyal Bilgiler (5–7) ve İnkılap (8) ortak

- **Format:** Numaralı kök (genellikle bir kısa okuma parçası / diyalog / metin) +
  4 şık **A) B) C) D)**, tek doğru cevap.
- **Kök tipi:** Neredeyse her soru **bağlam temelli** — önce bir metin/senaryo/alıntı,
  sonra "Buna göre… aşağıdakilerden hangisi…" kalıbı. Salt ezber az.
- **Sık kalıplar:**
  - "…**hangisi söylenemez / ulaşılamaz / değildir**" (olumsuz kök — çeldirici tasarımı
    burada kritik; 3 doğru + 1 yanlış).
  - **I–II–III öncül** listesi + "hangilerine ulaşılabilir?" → şıklar "Yalnız I / I ve II /
    II ve III / I, II ve III" (kombinasyon mantığı, çok yaygın).
  - "En uygun başlık hangisidir?" (metin yorumu).
- **Çeldirici tasarımı:** Çeldiriciler makul ama metinden desteklenmeyen çıkarımlar;
  olumsuz köklerde çeldirici = metinle uyumlu doğru ifade (öğrenci "doğru"yu seçme
  tuzağına düşer). I–II–III kalıbında kısmi-doğru kombinasyonlar.

---

## 3. Soru tipleri / çeşitlilik (gözlemlenen)

### Sosyal Bilgiler (5–7)
| Tip | Açıklama | Gözlem |
|---|---|---|
| Olgusal bilgi | Kavram/terim tanıma (el sanatı, bayram türü) | Yaygın (5) |
| Kavram | Tanım→örnek eşleme (grup, rol, sen/ben dili) | Yaygın (5–7) |
| Metin/kaynak yorumu | Kısa parça → çıkarım | **En baskın tip** |
| Sebep-sonuç | Olayın nedeni/sonucu | Orta |
| Görsel yorumlama | Şıklar **resim** (A/B/C/D görsel); "hangisi doğal varlık" | Var, metinde kaybolur |
| Harita/tablo okuma | Harita/tablo → çıkarım | 5/6'da az, 7'de biraz |
| Beceri/senaryo | Günlük yaşam senaryosu → uygun davranış | Yaygın |

### T.C. İnkılap Tarihi (8)
| Tip | Açıklama | Gözlem |
|---|---|---|
| Olay–sebep–sonuç | Sanayi İnkılabı, Balkan Savaşları etkileri | Yaygın |
| Belge/metin yorumu | Atatürk sözü/mektubu/telgraf → çıkarım | **Çok yaygın** |
| Atatürk ilkeleri | Cumhuriyetçilik/Halkçılık/Milliyetçilik uygulama eşleme | Ünite 4'te yoğun |
| Harita okuma | Balkan/Trablusgarp/cephe haritaları → çıkarım | Yaygın (~14 referans) |
| Kişilik çıkarımı | M. Kemal metninden kişilik özelliği çıkarma | Yaygın (ünite 1) |
| I–II–III / LGS-tarzı çıkarım | Çok-öncüllü akıl yürütme | Çok yaygın |
| Kronoloji | Saf tarih-sıralama sorusu | **Gözlenmedi** (olay-yorumu tercih ediliyor) |

---

## 4. GRADE-8 = İNKILAP TARİHİ DOĞRULAMASI ✅

Tüm 8. sınıf kaynakları (kazanım testleri, ornek_sinav, 2025, hex örnek) başlıkta
**"T.C. İNKILAP TARİHİ VE ATATÜRKÇÜLÜK"** taşır ve içerik tümüyle İnkılap Tarihi'dir
(Kurtuluş Savaşı, Atatürk ilke ve inkılapları, Atatürkçülük). Kazanım kodları `İTA.8.x`.

**Ünite kapsamı (kazanim_testi_unite_1..6 başlıklarından doğrulandı):**
1. **Bir Kahraman Doğuyor** (M. Kemal'in hayatı, Osmanlı'nın durumu, fikir akımları)
2. **Millî Uyanış: Bağımsızlık Yolunda Atılan Adımlar** (I. Dünya Savaşı, Mondros, Kuvâ-yı Millîye)
3. **Millî Bir Destan: Ya İstiklal Ya Ölüm!** (Kurtuluş Savaşı cepheleri, Lozan)
4. **Atatürkçülük ve Çağdaşlaşan Türkiye** (Atatürk ilkeleri, inkılaplar, Tevhid-i Tedrisat)
5. **Demokratikleşme Çabaları**
6. **Atatürk Dönemi Türk Dış Politikası**

Cevap anahtarı 6 üniteyi de kapsar (Ü1: 33 soru, Ü2: 46, Ü3: 34 … A–D). Klasik İnkılap
müfredatı; **"Sosyal Bilgiler" içeriği değildir.**

---

## 5. Görsel içerik notu (render için önemli)

- MC testlerinde **görsel bağımlılığı yüksek ama metinde görünmez.** Sık formlar:
  - Şıkların kendisi **resim** ("Aşağıdaki görsellerden hangisi… A) B) C) D)" +
    resim altyazıları — 5. sınıf Kültür-Miras'ta yaygın).
  - Kök içi **harita** (8. sınıf ~14 harita referansı: Balkan, Trablusgarp, cepheler;
    5. sınıf Selanik haritası) — döküm sadece etiketleri/lejantı bırakır.
  - **Tablo** (fikir akımları, medeniyet-özellik eşleme; 5:7, 7:4, 8:9 referans).
- **Sonuç:** Üretici görsel-temelli soruları ya (a) metne-çevrilmiş biçimde (tablo→metin,
  harita→sözel betimleme) üretmeli ya da inline SVG üretmeli. Salt-metin few-shot,
  görsel soruların bir kısmını eksik temsil eder.
- Açık uçlu setlerde (B, C) tablo-doldurma/boşluk-doldurma yaygın; bunlar MC'ye
  doğrudan uymaz.

---

## 6. Sınıf ilerlemesi (5 → 8)

- **5:** Kısa parçalar, somut/günlük (haklar, gruplar, roller, ilk uygarlıklar). Görsel
  şıklar ve basit tanıma bol. Bilişsel yük düşük.
- **6:** Benzer alanlar, biraz daha uzun senaryolar; çok-öncüllü (I–II–III) kalıp artar.
- **7:** İletişim, sen/ben dili gibi soyut kavramlar; metin yorumu ağırlığı artar,
  başlık-bulma/çıkarım daha sık.
- **8 (İnkılap):** En uzun kökler; tarihi belge/alıntı yorumu, harita+I-II-III çıkarımı,
  ilke-uygulama eşleme. **LGS seviyesi akıl yürütme.** Salt-ezber neredeyse yok.

---

## 7. Örnek sorular (gerçek, birebir)

### 7.1 Sosyal Bilgiler 5 — kavram (Kültür ve Miras)
> **1.** Tarihçiler … Yazının kullanılmasından önceki dönemleri "tarih öncesi", sonraki
> dönemleri "tarihî devirler" olarak adlandırmışlardır. Buna göre aşağıdakilerden hangisi
> "tarihî devirlere" geçildiğinin **kanıtıdır**?
> A) Kemikten yapılmış eşyalar  B) Mağaradaki resimler  **C) Çivi yazılı tabletler**  D) Heykeller
> *(cevap çıkarım — 5. sınıf kazanım testi CA'sı yok)*

### 7.2 Sosyal Bilgiler 5 — beceri/senaryo (olumsuz kök)
> **6.** Aşağıdaki seçeneklerin hangisinde çocuk haklarıyla ilgili **yanlış** bilgi
> verilmiştir? A) Her çocuk temel yaşama hakkına sahiptir. B) Çocuklar zorla
> çalıştırılamaz. **C) On beş yaşına kadar her insan çocuk sayılır.** D) Temiz çevrede
> yaşamak her çocuğun hakkıdır. *(C = 18 yaş olmalı; çıkarım)*

### 7.3 Sosyal Bilgiler 6 — kavram (rol) — olumsuz kök
> **4.** …taksicilik yapıyorum. Çocuklarım…, Annem de bizimle kalıyor… Metne göre
> aşağıdakilerden hangisi Yasin Bey'in üstlendiği rollerden **biri değildir**?
> A) Evlat  B) Şoför  C) Baba  **D) Kardeş** *(çıkarım)*

### 7.4 Sosyal Bilgiler 7 — kavram (iletişim / "sen dili")
> **2.** "Sen dili"… Buna göre aşağıdaki cümlelerden hangisi "sen dili"ne örnek olabilir?
> **A) Neden sürekli geç kalıyorsun?**  B) Seni göremeyince meraklandım.  C) Yüksek sesle
> konuştuğunda üzülüyorum.  D) Benimle oynarsan mutlu oluyorum. *(çıkarım)*

### 7.5 İnkılap 8 — olay/sebep-sonuç (✅ resmî CA: Ü1-S1 = D)
> **1.** Avrupa'da gelişen Sanayi İnkılabı ile … Osmanlı pazarları Avrupa'dan gelen
> maliyeti düşük sanayi mallarıyla doldu… Buna göre Sanayi İnkılabı'nın Osmanlı
> Devleti'nde aşağıdakilerden hangisine neden olduğu söylenebilir?
> A) İşsiz insan sayısında azalma  B) Küçük el tezgâhlarının artışı  C) Vergi gelirlerinin
> yükselmesi  **D) Ülke topraklarının uluslararası açık bir pazara dönüşmesine** ✅

### 7.6 İnkılap 8 — kişilik çıkarımı (✅ resmî CA: Ü1-S4 = A)
> **4.** Mustafa Kemal, 31 Mart Vakası'ndan sonra subayların siyasete karışmasının
> tehlikelerini sezmişti… Balkan Savaşları'nda öngörüleri gerçekleşmiştir. Bu metinden
> M. Kemal'in hangi kişisel özelliği çıkarılabilir?
> **A) İleri görüşlülüğü**  B) Eğitimciliği  C) İdealistliği  D) Sabırlılığı ✅

### 7.7 İnkılap 8 — harita + I-II-III çıkarımı (✅ resmî CA: Ü1-S5 = A)
> **5.** [Selanik haritası: Ticaret gemileri / Demir yolu / Batılı fikirler] Bu haritaya
> göre Selanik ile ilgili I. Ticaretin en yoğun yaşandığı şehir II. Kültürel gelişmeler
> yayılma imkânı bulmuştur III. Farklı dinlere mensup insanların kaynaştığı şehir…
> hangilerine ulaşılabilir? **A) Yalnız II**  B) Yalnız III  C) I ve III  D) I, II ve III ✅
> *(harita gerektirir — render notu §5)*

### 7.8 İnkılap 8 — Atatürk ilkeleri (belge/uygulama eşleme)
> **1.** Halkçılık; bütün vatandaşların yasalar önünde eşit olmalarını… esas alan Atatürk
> ilkesidir. Buna göre aşağıdaki uygulamalardan hangisi halkçılık ilkesine göre hareket
> edildiğinin göstergesidir?
> A) Millî kültürün korunması  B) Büyük yatırımların devlet tarafından yapılması
> C) Bilimsel gelişmelerin takibi  **D) Kadınlara erkeklerle aynı hakların sağlanması** ✅
> *(Ü4-S1; CA Ü4: 1.D 2.C 3.B 4.D … ile uyumlu)*

### 7.9 İnkılap 8 — belge (Atatürk mektubu) yorumu
> **3.** Atatürk'ün Kurtdereli Mehmet Efendi'ye mektubu: "…milletimin şerefini korumak
> için her şeyi yapardım…" Bu mektuba göre Atatürk Türk sporcularına aşağıdakilerden
> hangisini tavsiye etmektedir?
> A) Sporun yalnızca yeteneğe bağlı kalması  **B) Sporcunun millî heyecan içinde
> yetişmesi**  C) Sadece başarıyı esas alması  D) Güreşe daha fazla önem verilmesi
> *(Ü4-S3 CA = B ile uyumlu)*

### 7.10 Açık uçlu örnek (İnkılap 8, ornek_2025 — MC DEĞİL, karşılaştırma için)
> **Kazanım İTA.8.3.6.** Lozan'da yabancı okulların Türkiye'nin yasalarına uygun
> faaliyet göstermesi… "Yapılan bu düzenlemeyi **bağımsız devlet anlayışı açısından
> değerlendiriniz.**" *(şık yok — açık uçlu yazılı senaryo.)*

---

## 8. Üretici için çıkarımlar (özet)

1. **MC üretimi:** Yalnızca `kazanim_testi_unite_*` desenini few-shot al (A–D, bağlam
   temelli kök, olumsuz-kök ve I-II-III kalıpları dahil). `ornek_sinav`/`2025`/hex
   dosyaları **açık uçlu**; MC few-shot'una karıştırma.
2. **8. sınıf ekseni = İnkılap Tarihi** olarak etiketle; kazanım kodu `İTA.8.x`; ünite
   adları §4. "Sosyal Bilgiler 8" ETİKETİ KULLANMA.
3. **Cevap doğrulaması:** 8 için resmî CA var (güvenilir). 5/6/7 kazanım testleri için CA
   yok → üretilen MC'nin doğru cevabını model kendi üretmeli; resmî anahtarla eşleştirme
   yapılamaz.
4. **Görsel:** harita/tablo/resim-şık bağımlı sorular yaygın; ya sözelleştir ya inline SVG.
5. **1–4 boşluğu:** Hayat Bilgisi (1–3) ve Sosyal Bilgiler 4 için resmî MC yok → şablon
   5–7'den uyarlanır, güçlük düşürülür.
</content>
</invoke>
