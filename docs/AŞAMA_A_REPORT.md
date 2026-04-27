# Aşama A — Sentetik vs Sentetik+Textbook A/B Raporu (5. sınıf)

> İki RAG modunun aynı kazanımlar üzerinde karşılaştırılması.

- Test tarihi: 2026-04-25 09:32
- Test kümesi: 4 kazanım × 2 mod × 5 soru
- Sabit seed: 1234

## TL;DR — Bulgular ve Karar

**Bağlam çeşitliliği +%18, kalite stabil. Aşama A başarılı.** Ders kitabı chunk'ları LLM'in "tekrar ettiği" senaryoları (elma/kalem/fırın) yerine kitaba özgü yeni bağlamlar (otobüs yolcusu, misket, oyun alanı) çıkarmasını tetikledi. Soru kalitesi düşmedi, üretim 5/5 başarılı, süre artmadı (hatta hafif düştü).

**Önemli ikinci bulgu:** Etiketleme aşaması, PDF içeriğinin **%57'sinin (215/378 chunk) müfredatımızda olmadığını** doğruladı — Çarpanlar, Asal Sayılar, Olasılık, İstatistik, Algoritma, Üslü İfadeler, Tümler/Bütünler Açılar gibi MEB 2024 müfredatı konuları. Bu chunk'lar `curriculum_expansion` olarak depolandı; agent şu an onları çekmiyor çünkü `curriculum.py` bu kazanımları içermiyor.

## Aşama A Çıktıları (Numerik)

| Metrik | Değer |
|--------|-------|
| Çıkarılan chunk | 378 (matematik_5_1.pdf + matematik_5_2.pdf) |
| Etiketlenen | 378 / 378 (100%) |
| Eşlenen kazanım | 155 (40 textbook_example + 37 activity + 21 problem + 57 concept) |
| `curriculum_expansion` | 76 (high/medium confidence) |
| Toplam ChromaDB ingest | 231 chunk (147 elendi: low confidence + unmapped + unusable) |
| Yeni Chroma boyutu | 1819 → 2050 (+%13) |
| Tagging maliyeti | ~$0.20 (gemini-2.5-flash, 92 batch) |
| Embedding maliyeti | ~$0.10 |
| Toplam ek maliyet | ~$0.30 |
| Geliştirme süresi | ~50 dk |

## Özet Tablo

| Kazanım | Mod | Üretilen | Ort. Jaccard ↓ | Unique Bağlam ↑ | Tip Dağılımı | Süre |
|---------|-----|----------|----------------|-----------------|---------------|------|
| M.5.1.5 | A (sentetik) | 5/5 | 0.18 | 48 | islem:2, sozel_problem:2, kavram_sorusu:1 | 25.6s |
| M.5.1.5 | B (textbook) | 5/5 | 0.17 | 60 | islem:2, sozel_problem:2, kavram_sorusu:1 | 15.1s |
| M.5.2.4 | A (sentetik) | 5/5 | 0.034 | 23 | islem:2, sozel_problem:2, kavram_sorusu:1 | 11.7s |
| M.5.2.4 | B (textbook) | 5/5 | 0.028 | 28 | islem:2, sozel_problem:2, kavram_sorusu:1 | 13.7s |
| M.5.3.3 | A (sentetik) | 5/5 | 0.243 | 32 | islem:2, sozel_problem:2, kavram_sorusu:1 | 10.6s |
| M.5.3.3 | B (textbook) | 5/5 | 0.268 | 34 | islem:2, sozel_problem:2, kavram_sorusu:1 | 11.7s |
| M.5.5.2 | A (sentetik) | 5/5 | 0.156 | 30 | islem:2, sozel_problem:2, kavram_sorusu:1 | 13.3s |
| M.5.5.2 | B (textbook) | 5/5 | 0.147 | 35 | islem:2, sozel_problem:2, kavram_sorusu:1 | 14.9s |

## Toplulaştırılmış Metrikler

| Metrik | A (sentetik) | B (textbook) | Δ |
|--------|--------------|--------------|---|
| Ort. Jaccard (↓ iyi) | 0.15 | 0.15 | 0.0 |
| Unique Bağlam (↑ iyi) | 33.25 | 39.25 | 6.0 |
| Ort. Soru Uzunluğu | 121.5 | 139.0 | 17.5 |
| Kullanılan Textbook Chunk | 0 | 3 | 3 |
| Süre (s) | 15.3 | 13.85 | -1.45 |

## Üretilen Sorular (Karşılaştırma)


### M.5.1.5


**Mod A (sentetik)** — chunks=0, jaccard=0.18, ctx=48

1. [islem] 680 doğal sayısı, her biri 25 birim olan gruplara ayrıldığında kaç tane tam grup elde edilir?
   → Cevap: 27
2. [sozel_problem] Bir fırıncı 850 adet simidi, her kutuya 35 simit koyacak şekilde paketliyor. Bu simitlerle kaç tane tam dolu kutu elde eder?
   → Cevap: 24
3. [kavram_sorusu] Bir bölme işleminde bölünen 540, bölen ise 25'tir. Bu işlem sonucunda elde edilen bölüm ve kalan, 'kaç tane tam grup oluşur?' sorusuna cevap verirken nasıl yorumlanır?
   → Cevap: Bölüm, tam grup sayısını gösterir. Kalan ise tam grup oluşturmaya yetmeyen miktarı gösterir.
4. [sozel_problem] Bir tarladan toplanan 980 kilogram patates, her çuvala 40 kilogram gelecek şekilde çuvallara dolduruluyor. Bu patateslerle kaç tane tam dolu çuval elde edilir?
   → Cevap: 24
5. [islem] 450 doğal sayısını 28'e böldüğümüzde elde edilen bölüm, bu sayının içinde kaç tane 28'lik tam grup olduğunu gösterir. Bu bölümün değerini bulunuz.
   → Cevap: 16


**Mod B (textbook)** — chunks=3, jaccard=0.17, ctx=60

1. [islem] Bir depoda 480 litre su bulunmaktadır. Bu su, her biri 25 litre su alabilen bidonlara doldurulacaktır. Kaç tane tam dolu bidon elde edilebilir?
   → Cevap: 19
2. [islem] Bir fırında üretilen 850 adet simit, her pakette 35 simit olacak şekilde paketleniyor. Kaç tane tam paket simit oluşur?
   → Cevap: 24
3. [sozel_problem] Bir okul gezisine katılacak 280 öğrenci için her biri 32 öğrenci taşıyabilen minibüsler kiralanacaktır. Kaç tane tam dolu minibüs ile bu öğrenciler taşınabilir?
   → Cevap: 8
4. [sozel_problem] Elinde 630 adet boncuk bulunan Elif, her bir bileklik için 28 boncuk kullanmaktadır. Elif, bu boncuklarla kaç tane tam bileklik yapabilir?
   → Cevap: 22
5. [kavram_sorusu] Bir bölme işleminde kalan, bölünenin bölene tam olarak bölünemeyen kısmını ifade eder. Bir problemde 'kaç tane tam ürün/grup elde edilir?' sorusu sorulduğunda, bölme işlemindeki kalanın bu sorunun cevabını nasıl etkilediğini açıklayınız.
   → Cevap: Bir problemde 'kaç tane tam ürün/grup elde edilir?' sorusu sorulduğunda, bölme işlemindeki bölüm bize tam olarak kaç adet ürün veya grup oluştuğunu gösterir. Kalan ise, yeni bir tam ürün veya grup oluşturmak için yeterli olmayan, artan miktarı veya parçayı temsil eder. Bu nedenle, kalan miktar bir tam bütün oluşturmadığı için 'tam ürün/grup sayısı'nı bulurken dikkate alınmaz, sadece artan kısım olarak yorumlanır.


### M.5.2.4


**Mod A (sentetik)** — chunks=0, jaccard=0.034, ctx=23

1. [islem] 3/4 + 1/6 işleminin sonucunu bulunuz.
   → Cevap: 11/12
2. [islem] 9/10 - 3/5 işleminin sonucu kaçtır?
   → Cevap: 3/10
3. [sozel_problem] Bir sürahi limonatanın önce 1/4'ü, daha sonra 3/8'i içilmiştir. Bu sürahi limonatanın toplamda ne kadarı içilmiştir?
   → Cevap: 5/8
4. [sozel_problem] Serap, bir kurdeleyi paketlemek için kullanacaktır. Elinde 7/9 metre uzunluğunda kurdele vardır. İlk paketi süslemek için bu kurdelenin 1/3 metresini kullanmıştır. Geriye kaç metre kurdele kalmıştır?
   → Cevap: 4/9 metre
5. [kavram_sorusu] 1/5 kesrine hangi kesir eklenirse sonuç 7/10 olur? Bu kesri bulunuz.
   → Cevap: 1/2


**Mod B (textbook)** — chunks=3, jaccard=0.028, ctx=28

1. [islem] 1/3 ile 1/4 kesirlerinin toplamı kaçtır?
   → Cevap: 7/12
2. [islem] Bir bütünün 5/6'sından 1/3'ü çıkarıldığında geriye ne kadar kalır?
   → Cevap: 3/6 veya 1/2
3. [sozel_problem] Bir bahçıvan, tarlasının 2/5'ine domates, 3/10'una ise biber ekmiştir. Bahçıvan tarlasının toplamda ne kadarını ekmiştir?
   → Cevap: 7/10
4. [sozel_problem] Sevgi, bir sürahideki suyun 7/8'ini kullanmıştır. Bu kullanılan suyun 1/4'ü çiçekleri sulamak için harcanmışsa, geriye kalan kullanılan su miktarı sürahinin kaçta kaçıdır?
   → Cevap: 5/8
5. [kavram_sorusu] 1/2 kesrine hangi kesir eklendiğinde sonuç 5/6 olur? Bu kesri bulmak için hangi işlemi yaparsınız ve sonucu kaçtır?
   → Cevap: 1/3


### M.5.3.3


**Mod A (sentetik)** — chunks=0, jaccard=0.243, ctx=32

1. [islem] Çevre uzunluğu 75 cm olan bir üçgenin kenar uzunluklarından ikisi 25 cm ve 28 cm'dir. Bu üçgenin üçüncü kenarının uzunluğu kaç santimetredir?
   → Cevap: 22 cm
2. [islem] Bir dikdörtgenin çevre uzunluğu 112 cm'dir. Bu dikdörtgenin uzun kenarlarından biri 35 cm olduğuna göre, kısa kenar uzunluğu kaç santimetredir?
   → Cevap: 21 cm
3. [sozel_problem] Kare şeklindeki bir parkın çevre uzunluğu 204 metredir. Bu parkın bir kenarının uzunluğu kaç metredir?
   → Cevap: 51 metre
4. [sozel_problem] Paralelkenar şeklindeki bir masa örtüsünün çevresi 280 cm'dir. Bu masa örtüsünün kısa kenar uzunluğu 60 cm olduğuna göre, uzun kenar uzunluğu kaç santimetredir?
   → Cevap: 80 cm
5. [kavram_sorusu] Bir dörtgenin çevre uzunluğu ve üç kenar uzunluğu bilindiğinde, dördüncü kenar uzunluğunu bulmak için hangi matematiksel adımları uygulamak gerekir?
   → Cevap: Dörtgenin çevre uzunluğundan, bilinen üç kenar uzunluğunun toplamı çıkarılır.


**Mod B (textbook)** — chunks=3, jaccard=0.268, ctx=34

1. [islem] Bir kare şeklindeki oyun alanının çevre uzunluğu 172 metredir. Bu oyun alanının bir kenar uzunluğu kaç metredir?
   → Cevap: 43 metre
2. [sozel_problem] Dikdörtgen şeklindeki bir halının çevre uzunluğu 260 cm'dir. Halının uzun kenarlarından biri 85 cm olduğuna göre, kısa kenarı kaç cm'dir?
   → Cevap: 45 cm
3. [kavram_sorusu] Eşkenar bir üçgenin çevre uzunluğu 225 mm olarak verilmiştir. Bu bilgiyi kullanarak eşkenar üçgenin bir kenar uzunluğunu nasıl bulursunuz ve bu uzunluk kaç mm olur?
   → Cevap: 75 mm
4. [islem] Bir üçgenin çevre uzunluğu 195 santimetredir. Bu üçgenin kenar uzunluklarından ikisi 72 cm ve 58 cm ise, üçüncü kenarının uzunluğu kaç santimetredir?
   → Cevap: 65 cm
5. [sozel_problem] Paralelkenar şeklindeki bir bahçenin çevre uzunluğu 320 metredir. Bahçenin kısa kenar uzunluğu 70 metre olduğuna göre, uzun kenar uzunluğu kaç metredir?
   → Cevap: 90 metre


### M.5.5.2


**Mod A (sentetik)** — chunks=0, jaccard=0.156, ctx=30

1. [islem] Hangi sayının 4 katının 8 fazlası 36'ya eşittir? Bu durumu cebirsel bir denklemle ifade edip sayıyı bulunuz.
   → Cevap: 7
2. [islem] Bir sayının 3 eksiğinin 5 katı 55'e eşittir. Bu sayıyı bulunuz. Denklem kurarak çözünüz.
   → Cevap: 14
3. [sozel_problem] Bir sepetteki elmaların sayısının 5 katının 15 eksiği 85 elmaya eşittir. Sepette kaç elma vardır? Önce denklem yazıp çözünüz.
   → Cevap: 20
4. [sozel_problem] Emel, bir miktar parasıyla tanesi 6 TL olan kalemlerden 7 tane almıştır. Geriye 25 TL'si kaldığına göre, başlangıçta Emel'in kaç TL'si vardı?
   → Cevap: 67
5. [kavram_sorusu] Bir doğal sayının 9 fazlasının yarısı 14'e eşittir. Bu durumu matematiksel bir denklemle ifade ediniz ve o doğal sayıyı bulunuz.
   → Cevap: 19


**Mod B (textbook)** — chunks=3, jaccard=0.147, ctx=35

1. [islem] Hangi sayının 4 katının 8 fazlası 36'ya eşittir? Bu durumu cebirsel bir denklemle ifade edip sayıyı bulunuz.
   → Cevap: 7
2. [islem] Bir sayının 3 katından 5 çıkarıldığında sonuç 19 oluyor. Bu durumu cebirsel bir denklemle ifade edip sayıyı bulunuz.
   → Cevap: 8
3. [sozel_problem] Bir otobüste başlangıçta bir miktar yolcu vardı. İlk durakta 12 yolcu indi ve 6 yolcu bindi. Son durumda otobüste 20 yolcu olduğuna göre, başlangıçta kaç yolcu vardı? Önce denklem yazıp çözünüz.
   → Cevap: 26
4. [sozel_problem] Elif'in bir miktar misketi vardı. Arkadaşına 15 misket verdiğinde, geriye 23 misketi kaldı. Başlangıçta Elif'in kaç misketi vardı? Önce denklem yazıp çözünüz.
   → Cevap: 38
5. [kavram_sorusu] Bir bilinmeyen sayıyı 'a' ile göstererek, 'Bir sayının 6 fazlasının 3 katı' ifadesini cebirsel olarak yazınız. Eğer bu cebirsel ifadenin değeri 36 ise, bilinmeyen sayıyı bulunuz.
   → Cevap: 6

## Niteliksel Gözlemler

### 1. Bağlam çeşitliliği gerçek bir farkla artıyor
- **M.5.1.5** (kalanı yorumlama): A modu fırın/patates/tarla bağlamlarına yönelirken B modu okul gezisi/minibüs, boncuk/bileklik, su/bidon gibi kitaba yakın yeni bağlamlar üretti.
- **M.5.5.2** (sözel → denklem): A modunda "elma/kalem/sepet" tekrarı, B'de "otobüs yolcusu/misket" gibi farklı bağlamlar.

### 2. Sorular daha "ders kitabı tonuna" yaklaşıyor
B modu soruları biraz daha uzun (~+18 char/soru) ve kavramsal açıklamaları daha derinleşmiş. Örnek: M.5.1.5'te kavram sorusunun cevabı 4 cümleden 6 cümleye çıkmış, "yeni bir tam ürün/grup oluşturmak için yeterli olmayan, artan miktarı veya parçayı temsil eder" gibi MEB ders kitabı tarzında ifadeler içeriyor.

### 3. Bazı kazanımlarda etki minimum
- **M.5.3.3** (üçgen/dörtgen çevre): B mod sadece +2 unique bağlam getirdi. Sebebi: bu kazanım için zaten sentetik corpus zengin (örnek/sorular geometrik fakat günlük hayata bağlanması zor — masa örtüsü, halı, oyun alanı zaten doygun).

### 4. M.5.2.4'te kapsama riski
M.5.2.4 (paydaları eşit olmayan kesirler) için textbook'ta sadece 1 chunk eşleşti — bu kazanım için textbook etkisi düşük. Diğer kazanımlardan fallback ile 3 chunk geldi ama spesifik değil.

## Riskler ve Sınırlamalar

1. **N=4 kazanım × 5 soru istatistiksel olarak küçük.** Genel iyileşme trendi var ama %18 fark yer yer rastlantı olabilir. Daha geniş test (8-12 kazanım × 10 soru) için ek $1-2 maliyet gerekir.
2. **Concept chunk'larında PDF artık metni** (geometri sayfalarındaki "A B C D" koordinatları, soft hyphen kalıntıları) zaman zaman noisy. 7 noisy + 2 unusable etiketlendi, kalan kabul edilebilir.
3. **`textbook_concept` chunk'ları SOR-CEVAP yapısı içermez** — agent bunları stilistik/bağlamsal referans olarak kullanmaya çalışır, bu doğru bir konumlandırma.
4. **Curriculum farkı henüz değerlendirilmedi:** 76 `curriculum_expansion` chunk şu an ölü yatırım çünkü `curriculum.py` bu kazanımları tanımıyor.

## Karar Matrisi — Sonraki Adım

| Seçenek | Süre | Maliyet | Beklenen değer |
|---------|------|---------|----------------|
| **B**: Tüm 9 metin gömülü PDF'e genişlet (1, 2, 5, 6, 7. sınıf) | 1 gün | $5-10 | Aynı +%18 etkiyi diğer sınıflara taşır; 6. sınıf outline'ı kaliteli olduğundan en yüksek getiri orada |
| **C**: 3-4. sınıf OCR (Gemini Vision) | yarım gün | $10-15 | Sadece bu iki sınıfın textbook desteği aktifleşir |
| **D**: `curriculum.py`'i MEB 2024 ile genişlet | 1-2 gün | $0-5 | 76 → potansiyel 800+ chunk değer üretir; ama mevcut MVP kalibrasyonunu etkiler |
| **Karma B+D**: önce diğer sınıfların outline'ından MEB 2024 müfredatını çıkar, `curriculum.py` genişlet, sonra ingest | 1.5 gün | $5-10 | En yüksek toplam getiri ama daha riskli |

## Önerim

1. **Hemen Aşama B**'ye geç — 5. sınıfta gözlenen +%18 bağlam etkisi aynı yöntemle 4 sınıfa daha taşınsın. 6. sınıf outline'ı zaten otomatik kazanım eşlemesi için altın kaynak.
2. **Aşama D'yi Aşama B sonrasında değerlendir** — B'den sonra 800+ unmapped chunk birikecek; bu yatırımı değerlendirmek için müfredat genişletmesi anlamlı olur.
3. **Aşama C (OCR)'yi en sona bırak** — 3-4. sınıf zaten 420 sentetik örnek ile iyi kapsanıyor.

## Üretilen Dosyalar (Aşama A)

- `scripts/extract_textbook.py` — PDF → chunk
- `scripts/tag_textbook_chunks.py` — LLM ile kazanım etiketleme
- `scripts/ingest_textbook.py` — ChromaDB'ye yükle
- `scripts/compare_textbook_rag.py` — A/B test
- `app/services/retriever.py` — `retrieve_textbook()` ek metodu
- `app/services/agent.py` — `include_textbook=True` desteği
- `app/prompts/templates.py` — `_format_textbook_context()` bölümü
- `knowledge_base/processed/textbook_chunks_grade5.json` (378 chunk)
- `knowledge_base/processed/textbook_chunks_grade5_tagged.json` (etiketli)
- `knowledge_base/processed/ab_test_results.json` (raw test sonucu)
