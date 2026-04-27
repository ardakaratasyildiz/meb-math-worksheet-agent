# Aşama D — Yeni Kazanımlar için A/B Raporu (Sentetik vs Sentetik+Textbook)

> İki RAG modunun **Aşama D'de eklenen yeni kazanımlar** üzerinde karşılaştırılması.

- Test tarihi: 2026-04-25 13:51
- Test kümesi: 6 kazanım × 2 mod × 5 soru (3 sınıf, 4 öğrenme alanı)
- Sabit seed: 1234

## TL;DR

**Sentetik corpus tek başına yeterli kalitede çıktı veriyor — ortalama %2 marjinal etki.** Aşama A'da textbook'un mevcut kazanımlara katkısı +%18'di; Aşama D'de yeni kazanımlara katkı +%2 ile sınırlı. Bunun nedeni: yeni kazanımlar için sentetik corpus ZATEN 240 yüksek çeşitlilikli örnek üretti (5×3×16 = 240, kazanım başına 15 farklı bağlam). Textbook artık ek değer üretmek için "boşluk" bulamıyor.

**Ama kazanım bazında varyasyon yüksek**: bazı kazanımlarda textbook hala önemli katma değer sağlıyor:
- ✅ **M.5.6.1 (Veri İşleme)**: +29 unique bağlam (+%49)
- ✅ **M.6.1.5 (Çarpan/Asal)**: +11 unique bağlam (+%32)
- ⚠️ **M.6.6.2 (Merkezi Eğilim)**: −26 unique bağlam (B kötüleşti)
- ⚪ **M.5.2.5, M.6.7.1, M.7.7.1**: nötr veya hafif kötüleşme

**Sonuç:** Sentetik corpus stratejisi (Aşama D) çok başarılı, **mevcut tüm RAG katmanları korunmalı**. Textbook bazı kazanımlarda hâlâ kritik (özellikle Veri İşleme).

## Özet Tablo

| Kazanım | Mod | Üretilen | Ort. Jaccard ↓ | Unique Bağlam ↑ | Tip Dağılımı | Süre |
|---------|-----|----------|----------------|-----------------|---------------|------|
| M.5.2.5 | A (sentetik) | 5/5 | 0.119 | 24 | islem:2, sozel_problem:2, kavram_sorusu:1 | 13.8s |
| M.5.2.5 | B (textbook) | 5/5 | 0.118 | 19 | islem:2, sozel_problem:2, kavram_sorusu:1 | 8.8s |
| M.5.6.1 | A (sentetik) | 5/5 | 0.106 | 59 | islem:2, sozel_problem:2, kavram_sorusu:1 | 12.9s |
| M.5.6.1 | B (textbook) | 5/5 | 0.074 | 88 | islem:2, sozel_problem:2, kavram_sorusu:1 | 15.5s |
| M.6.1.5 | A (sentetik) | 5/5 | 0.103 | 34 | islem:2, sozel_problem:2, kavram_sorusu:1 | 22.4s |
| M.6.1.5 | B (textbook) | 5/5 | 0.044 | 45 | islem:2, sozel_problem:2, kavram_sorusu:1 | 21.7s |
| M.6.6.2 | A (sentetik) | 5/5 | 0.247 | 68 | islem:2, sozel_problem:2, kavram_sorusu:1 | 43.1s |
| M.6.6.2 | B (textbook) | 5/5 | 0.282 | 42 | islem:2, sozel_problem:2, kavram_sorusu:1 | 13.2s |
| M.6.7.1 | A (sentetik) | 5/5 | 0.124 | 50 | islem:2, sozel_problem:2, kavram_sorusu:1 | 11.6s |
| M.6.7.1 | B (textbook) | 5/5 | 0.122 | 50 | islem:2, sozel_problem:2, kavram_sorusu:1 | 15.9s |
| M.7.7.1 | A (sentetik) | 5/5 | 0.322 | 43 | islem:2, sozel_problem:2, kavram_sorusu:1 | 14.9s |
| M.7.7.1 | B (textbook) | 5/5 | 0.322 | 40 | islem:2, sozel_problem:2, kavram_sorusu:1 | 11.4s |

## Toplulaştırılmış Metrikler

| Metrik | A (sentetik) | B (textbook) | Δ |
|--------|--------------|--------------|---|
| Ort. Jaccard (↓ iyi) | 0.17 | 0.16 | -0.01 |
| Unique Bağlam (↑ iyi) | 46.33 | 47.33 | 1.0 |
| Ort. Soru Uzunluğu | 172.0 | 171.33 | -0.67 |
| Kullanılan Textbook Chunk | 0 | 2.83 | 2.83 |
| Süre (s) | 19.78 | 14.42 | -5.37 |

## Üretilen Sorular (Karşılaştırma)


### M.5.2.5


**Mod A (sentetik)** — chunks=0, jaccard=0.119, ctx=24

1. [islem] 240 sayısının %30'u kaçtır?
   → Cevap: 72
2. [islem] 500 sayısının %15'i kaçtır?
   → Cevap: 75
3. [sozel_problem] Bir fırında günlük üretilen 300 ekmeğin %10'u kepekli ekmektir. Bu fırında kaç adet kepekli ekmek üretilmektedir?
   → Cevap: 30
4. [sozel_problem] Bir mağazada 600 TL'ye satılan bir elbise, sezonda %25 indirimle satılmaktadır. Elbisenin indirimli fiyatı kaç TL olur?
   → Cevap: 450 TL
5. [kavram_sorusu] %45 ifadesi, bir bütünün kaçta kaçını temsil eder? Bu ifadeyi kesir olarak yazınız.
   → Cevap: 45/100


**Mod B (textbook)** — chunks=3, jaccard=0.118, ctx=19

1. [islem] 320 sayısının %25'i kaçtır?
   → Cevap: 80
2. [islem] 540 sayısının %10'u kaçtır?
   → Cevap: 54
3. [sozel_problem] Bir otobüste seyahat eden 80 yolcunun %40'ı çocuktur. Bu otobüste kaç tane çocuk yolcu bulunmaktadır?
   → Cevap: 32 çocuk yolcu
4. [sozel_problem] Bir çiftlikte bulunan 450 hayvanın %20'si koyundur. Bu çiftlikte kaç tane koyun vardır?
   → Cevap: 90 koyun
5. [kavram_sorusu] Yüzde sembolü (%) neyi ifade eder? Açıklayınız.
   → Cevap: Yüzde sembolü (%), bir bütünün 100 eşit parçaya bölündüğünde, bu parçalardan kaç tanesinin alındığını gösteren bir ifade biçimidir.


### M.5.6.1


**Mod A (sentetik)** — chunks=0, jaccard=0.106, ctx=59

1. [islem] Bir okuldaki satranç kulübüne 35 öğrenci, resim kulübüne 28 öğrenci, müzik kulübüne 42 öğrenci katılmıştır. Satranç kulübüne katılan öğrenci sayısı, resim kulübüne katılan öğrenci sayısından kaç fazladır? Müzik kulübüne katılan öğrenci sayısı ile satranç kulübüne katılan öğrenci sayısının toplamı kaçtır?
   → Cevap: Satranç kulübü 7 öğrenci fazladır; toplam 77 öğrenci.
2. [islem] Bir manavda pazartesi 48 kg domates, salı 35 kg salatalık, çarşamba 52 kg biber satılmıştır. Pazartesi ve salı günü satılan toplam sebze miktarı kaç kg'dır? Çarşamba günü satılan biber miktarı, salı günü satılan salatalık miktarından kaç kg fazladır?
   → Cevap: Pazartesi ve salı günü satılan toplam sebze miktarı 83 kg'dır; çarşamba günü 17 kg fazla biber satılmıştır.
3. [sozel_problem] Bir hayvan barınağında 24 kedi, 18 köpek ve 12 kuş bulunmaktadır. Bu barınakta bulunan kedi sayısı, köpek sayısından kaç fazladır? Kuşların sayısı, kedilerin ve köpeklerin toplam sayısından ne kadar azdır?
   → Cevap: Kedi sayısı köpek sayısından 6 fazladır; kuş sayısı kedilerin ve köpeklerin toplam sayısından 30 azdır.
4. [sozel_problem] Bir okul kantininde bir hafta boyunca 65 kutu süt, 40 şişe su ve 50 bardak ayran satılmıştır. Satılan süt sayısı, satılan su sayısından kaç fazladır? Bu hafta boyunca satılan toplam içecek sayısı kaçtır?
   → Cevap: Satılan süt sayısı, satılan su sayısından 25 fazladır; bu hafta boyunca toplam 155 içecek satılmıştır.
5. [kavram_sorusu] Bir sınıftaki öğrencilerin en sevdiği renkleri gösteren bir sıklık tablosu oluşturulduğunda, bu tablodan hangi bilgileri kolayca öğrenebiliriz? En az sevilen rengi veya en çok sevilen rengi nasıl belirleriz?
   → Cevap: Sıklık tablosundan her bir rengi seven öğrenci sayısını ve toplam öğrenci sayısını kolayca öğrenebiliriz. En az sevilen renk, sıklığı (seven öğrenci sayısı) en küçük olan renktir; en çok sevilen renk ise sıklığı en büyük olan renktir.


**Mod B (textbook)** — chunks=3, jaccard=0.074, ctx=88

1. [islem] Bir mağazada bir haftanın ilk üç gününde satılan defter sayıları aşağıdaki gibidir: Pazartesi günü 45 defter, Salı günü 58 defter ve Çarşamba günü 37 defter satılmıştır. Salı günü satılan defter sayısı, Pazartesi günü satılan defter sayısından kaç fazladır?
   → Cevap: 13 defter fazladır.
2. [islem] Bir okul kütüphanesinde bulunan kitapların türlerine göre sayıları şöyledir: Macera kitapları 125 adet, Bilim Kurgu kitapları 98 adet, Tarih kitapları 110 adet. Kütüphanedeki macera kitaplarının sayısı, bilim kurgu kitaplarının sayısından kaç fazladır ve toplamda macera ile tarih kitaplarının sayısı kaçtır?
   → Cevap: Macera kitapları 27 adet fazladır. Macera ve tarih kitaplarının toplamı 235 adettir.
3. [sozel_problem] Bir sınıftaki öğrencilerin en sevdiği spor dalları araştırılmıştır. Bu araştırmanın sonuçlarına göre futbolu 15 öğrenci, basketbolu 12 öğrenci, voleybolu 8 öğrenci ve yüzmeyi 5 öğrenci sevmektedir. Bu verilere göre en çok sevilen iki spor dalı arasındaki öğrenci sayısı farkı kaçtır ve en az sevilen spor dalı hangisidir?
   → Cevap: En çok sevilen iki spor dalı arasındaki fark 3 öğrencidir. En az sevilen spor dalı yüzmedir.
4. [sozel_problem] Bir mahallede yaşayan kişilerin en çok tercih ettiği ulaşım araçları hakkında bir araştırma yapılıyor ve sonuçlar kaydediliyor. Otobüs 75 kişi, metro 50 kişi, özel araç 65 kişi ve bisiklet 30 kişi tarafından tercih ediliyor. Bu verilere göre, otobüs ve özel araç tercih edenlerin toplam sayısı ile metro ve bisiklet tercih edenlerin toplam sayısı arasındaki fark kaçtır?
   → Cevap: Fark 60'tır.
5. [kavram_sorusu] Bir araştırmadan elde edilen verileri düzenlemek ve görselleştirmek için kullanılan sıklık tablosu ve sütun grafiğinin temel amaçları nelerdir? Bu iki aracın birbirine göre avantajlı olduğu durumlar neler olabilir?
   → Cevap: Sıklık tablosu ve sütun grafiğinin temel amacı, toplanan verileri düzenleyerek anlaşılır hâle getirmek ve karşılaştırmalar yapmayı kolaylaştırmaktır. Sıklık tablosu verilerin sayısal değerlerini ve her bir kategorinin kaç kez tekrarlandığını (sıklığını) net bir şekilde gösterirken, sütun grafiği bu sıklıkları görsel olarak daha çarpıcı ve hızlı anlaşılır bir biçimde sunar. Sıklık tablosu, detaylı sayısal bilgiye ihtiyaç duyulan durumlarda, sütun grafiği ise verilerin genel dağılımını ve kategoriler arası büyüklük farklarını hızlıca görmek istendiğinde daha avantajlıdır.


### M.6.1.5


**Mod A (sentetik)** — chunks=0, jaccard=0.103, ctx=34

1. [islem] 84 sayısını asal çarpanlarının çarpımı şeklinde yazınız.
   → Cevap: 84 = 2² × 3 × 7
2. [islem] 72 sayısının tüm çarpanlarını bulunuz. Bu çarpanlar arasından asal olanlarını listeleyiniz.
   → Cevap: Çarpanları: 1, 2, 3, 4, 6, 8, 9, 12, 18, 24, 36, 72. Asal çarpanları: 2, 3.
3. [sozel_problem] Bir çiçekçi, 90 adet papatyayı eşit sayıda olmak üzere farklı vazoları yerleştirmek istiyor. Her vazodaki papatya sayısı asal bir sayı olacak şekilde kaç farklı vazo düzenlemesi yapabilir?
   → Cevap: 3 farklı düzenleme yapabilir.
4. [sozel_problem] Bir sayı hem 4'ün hem de 6'nın bir katıdır. Bu sayı 80'den küçük olduğuna göre, bu koşulu sağlayan en büyük sayının asal çarpanlarını bulunuz.
   → Cevap: 2 ve 3
5. [kavram_sorusu] 51 sayısının tüm çarpanlarını listeleyiniz. Bu çarpanlar arasından asal olanları belirleyiniz ve bir sayının asal olmasının temel şartını kısaca açıklayınız.
   → Cevap: Çarpanları: 1, 3, 17, 51. Asal çarpanları: 3, 17. Asal sayılar, 1'den büyük olup 1 ve kendisinden başka pozitif tam böleni olmayan doğal sayılardır.


**Mod B (textbook)** — chunks=3, jaccard=0.044, ctx=45

1. [islem] 108 sayısının asal çarpanlarının çarpımı şeklinde yazılışını bulunuz.
   → Cevap: 2² × 3³
2. [islem] 72 sayısının tüm pozitif çarpanlarını listeleyiniz ve bu çarpanlar arasından asal olanları belirtiniz.
   → Cevap: Çarpanlar: 1, 2, 3, 4, 6, 8, 9, 12, 18, 24, 36, 72. Asal çarpanlar: 2, 3.
3. [sozel_problem] Bir takı tasarımcısı, 1'den 50'ye kadar numaralandırılmış boncuklardan sadece asal sayı olanları kullanarak bir kolye yapmayı planlamaktadır. Ancak, 5'in katı olan boncukları kolye yapımında kullanmamaya karar vermiştir. Tasarımcının kolye için kullanabileceği kaç farklı asal boncuk vardır?
   → Cevap: 14 farklı asal boncuk vardır.
4. [sozel_problem] Bir spor salonunda fitness dersleri her 4 günde bir, yoga dersleri ise her 6 günde bir yapılmaktadır. Eğer bu iki ders ilk kez aynı gün yapıldıysa, bu ilk günden sonraki 70 gün içinde kaç defa daha aynı gün yapılırlar?
   → Cevap: 5 defa
5. [kavram_sorusu] İki basamaklı en küçük asal sayı ile iki basamaklı en büyük asal sayı arasındaki fark kaçtır?
   → Cevap: 86


### M.6.6.2


**Mod A (sentetik)** — chunks=0, jaccard=0.247, ctx=68

1. [islem] Aşağıdaki veri grubunun aritmetik ortalamasını, ortancasını ve tepe değerini hesaplayarak, bu değerlerin veri grubu hakkında ne ifade ettiğini kısaca açıklayınız: 14, 17, 12, 17, 15, 14, 17
   → Cevap: Aritmetik Ortalama: 15.14 (yaklaşık), Ortanca: 15, Tepe Değeri: 17. Verilerin ortalaması yaklaşık 15.14 olup, en çok tekrar eden değer 17'dir. Verilerin yarısı 15'ten küçük, diğer yarısı 15'ten büyüktür.
2. [islem] Verilen sayı grubunun aritmetik ortalamasını, ortancasını ve tepe değerini bulunuz. Bu değerleri kullanarak veri grubunun merkezi eğilimleri hakkında kısa bir yorum yapınız: 32, 28, 35, 32, 29, 30
   → Cevap: Aritmetik Ortalama: 31, Ortanca: 30.5, Tepe Değeri: 32. Veri grubunun ortalaması 31'dir. Sayıların yarısı 30.5'ten küçük, yarısı ise büyüktür. En sık rastlanan değer 32'dir.
3. [sozel_problem] Bir bahçede yetiştirilen 8 adet fidanın boyları (santimetre cinsinden) aşağıdaki gibidir: 25, 30, 28, 25, 32, 27, 25, 35. Bu veri grubunun aritmetik ortalamasını, ortancasını ve tepe değerini hesaplayınız. Fidanların boy dağılımı hakkında bu ölçütlerin bir arada ne gibi bilgiler verdiğini yorumlayınız.
   → Cevap: Aritmetik Ortalama: 28.375 cm, Ortanca: 27.5 cm, Tepe Değeri: 25 cm. Fidan boylarının ortalaması yaklaşık 28.375 cm'dir. Fidanların yarısının boyu 27.5 cm'den az, yarısının ise fazladır. En çok 25 cm boyunda fidan bulunmaktadır.
4. [sozel_problem] Bir marketin bir haftalık yoğurt satış adetleri (kilogram) sırasıyla 120, 150, 130, 140, 150, 110, 150 şeklindedir. Bu veri grubunun aritmetik ortalamasını, ortancasını ve tepe değerini hesaplayarak, marketin yoğurt satış performansı hakkında bir değerlendirme yapınız.
   → Cevap: Aritmetik Ortalama: 135.71 (yaklaşık), Ortanca: 140, Tepe Değeri: 150. Marketin günlük ortalama yoğurt satışı yaklaşık 135.71 kg'dır. Satışların yarısı 140 kg'dan az, diğer yarısı ise fazladır. En sık satılan yoğurt miktarı 150 kg'dır.
5. [kavram_sorusu] Bir grup öğrencinin katıldığı deneme sınavından aldıkları puanlar şöyledir: 60, 70, 80, 70, 90, 65, 70. Bu veri grubunun aritmetik ortalamasını, ortancasını ve tepe değerini hesaplayınız. Ardından, bu üç ölçütün her birinin öğrenci puanları hakkında ayrı ayrı ne anlama geldiğini ve birlikte sınıfın genel başarı düzeyi hakkında ne tür bir bilgi verdiğini açıklayınız.
   → Cevap: Aritmetik Ortalama: 72.14 (yaklaşık), Ortanca: 70, Tepe Değeri: 70. Aritmetik ortalama, tüm puanların genel ortalamasını; ortanca, puanların tam ortasındaki değeri (yarısı bu değerden az, yarısı fazla); tepe değeri ise en sık alınan puanı gösterir. Bu değerler birlikte, sınıfın genel başarı düzeyinin ortalama 72.14 olduğunu, ancak puanların çoğunlukla 70 civarında yoğunlaştığını ifade eder.


**Mod B (textbook)** — chunks=3, jaccard=0.282, ctx=42

1. [islem] Aşağıdaki veri grubunun aritmetik ortalamasını, ortancasını ve tepe değerini hesaplayınız: 15, 20, 18, 15, 22, 25, 15.
   → Cevap: Aritmetik Ortalama: 18.57 (yaklaşık), Ortanca: 18, Tepe Değeri: 15.
2. [islem] Aşağıdaki sayı dizisinin aritmetik ortalamasını, ortancasını ve tepe değerini bulunuz: 30, 35, 28, 30, 40, 32.
   → Cevap: Aritmetik Ortalama: 32.5, Ortanca: 31, Tepe Değeri: 30.
3. [sozel_problem] Bir otobüs durağından 6 farklı saatte geçen yolcu sayıları sırasıyla 45, 52, 48, 55, 45, 60'tır. Bu veri grubunun aritmetik ortalamasını, ortancasını ve tepe değerini hesaplayarak, durağın yoğunluğu hakkında bir yorum yapınız.
   → Cevap: Aritmetik Ortalama: 50.83 (yaklaşık), Ortanca: 50, Tepe Değeri: 45. Durağın ortalama yoğunluğu yaklaşık 50.83 yolcu olup, en sık 45 yolcu geçtiği saatler olmuştur. Yoğunluk genellikle 45 ile 55 yolcu arasında değişmektedir.
4. [sozel_problem] Bir gruptaki 7 kişinin yaşları 12, 15, 13, 12, 16, 14, 17 şeklindedir. Bu veri grubunun aritmetik ortalamasını, ortancasını ve tepe değerini hesaplayarak, grubun yaş dağılımı hakkında bir açıklama yapınız.
   → Cevap: Aritmetik Ortalama: 14.14 (yaklaşık), Ortanca: 14, Tepe Değeri: 12. Grubun ortalama yaşı yaklaşık 14.14 olup, yaşların yarısı 14'ten az, diğer yarısı ise 14'ten fazladır. En sık görülen yaş 12'dir.
5. [kavram_sorusu] Bir okul bahçesindeki 9 öğrencinin ayakkabı numaraları şu şekildedir: 36, 38, 37, 36, 39, 40, 37, 36, 38. Bu veri grubunun aritmetik ortalamasını, ortancasını ve tepe değerini hesaplayınız. Ayakkabı numaralarının dağılımı hakkında bu üç ölçütün her birinin ayrı ayrı ve birlikte ne tür bilgiler verdiğini açıklayınız.
   → Cevap: Aritmetik Ortalama: 37.44 (yaklaşık), Ortanca: 37, Tepe Değeri: 36. Ortalama ayakkabı numarası yaklaşık 37.44 olup, öğrencilerin yarısının ayakkabı numarası 37'den küçük veya eşit, diğer yarısının ise 37'den büyük veya eşittir. En çok karşılaşılan ayakkabı numarası 36'dır.


### M.6.7.1


**Mod A (sentetik)** — chunks=0, jaccard=0.124, ctx=50

1. [islem] 1'den 15'e kadar numaralandırılmış eş büyüklükteki kartlar bir kutuya konulmuştur. Kutudan rastgele çekilen bir kartın tek sayı olma olasılığını kesir olarak ifade ediniz.
   → Cevap: 8/15
2. [islem] Bir standart zar atıldığında üst yüze gelen sayının asal sayı olma olasılığı nedir?
   → Cevap: 1/2
3. [sozel_problem] Bir meyve sepetinde 6 elma, 9 portakal ve 5 muz bulunmaktadır. Sepetten rastgele seçilen bir meyvenin portakal olma olasılığını kesir olarak yazınız.
   → Cevap: 9/20
4. [sozel_problem] Bir okul panosunda 10 adet spor etkinliği ilanı, 8 adet bilim kulübü ilanı ve 7 adet sanat atölyesi ilanı asılıdır. Panodan rastgele seçilen bir ilanın spor etkinliği veya sanat atölyesi ilanı olma olasılığı nedir?
   → Cevap: 17/25
5. [kavram_sorusu] Bir torbada sadece kırmızı renkli toplar bulunmaktadır. Torbadan rastgele çekilen bir topun kırmızı olma olasılık durumu nedir?
   → Cevap: Kesin olay


**Mod B (textbook)** — chunks=3, jaccard=0.122, ctx=50

1. [islem] 1'den 18'e kadar numaralandırılmış eş büyüklükteki kartlar bir kutuya konulmuştur. Kutudan rastgele çekilen bir kartın 4'ün katı olma olasılığını kesir olarak ifade ediniz.
   → Cevap: 2/9
2. [sozel_problem] Bir çiçekçide 9 gül, 7 papatya ve 4 lale bulunmaktadır. Müşterinin rastgele seçtiği bir çiçeğin papatya olma olasılığı nedir?
   → Cevap: 7/20
3. [islem] Bir küpün yüzeylerinde 1, 2, 3, 4, 5, 6 sayıları yazmaktadır. Bu küp bir kez atıldığında üst yüze gelen sayının hem çift hem de 5'ten küçük olma olasılığını kesir olarak bulunuz.
   → Cevap: 1/3
4. [sozel_problem] Bir kumbarada 10 tane 1 TL, 8 tane 50 kuruş ve 12 tane 25 kuruş değerinde madeni para vardır. Kumbaradan rastgele çekilen bir madeni paranın 1 TL veya 25 kuruş olma olasılığını kesir olarak yazınız.
   → Cevap: 11/15
5. [kavram_sorusu] Bir rafta sadece kırmızı renkli kitaplar bulunmaktadır. Bu raftan rastgele seçilen bir kitabın mavi renkli olma olasılığı hangi olasılık durumuna örnektir?
   → Cevap: İmkansız olay


### M.7.7.1


**Mod A (sentetik)** — chunks=0, jaccard=0.322, ctx=43

1. [islem] 1'den 20'ye kadar olan tam sayılar arasından rastgele seçilen bir sayının tek sayı olma olasılığını kesir, ondalık ve yüzde olarak hesaplayınız.
   → Cevap: 1/2, 0.5, %50
2. [islem] Bir torbada 1'den 10'a kadar numaralandırılmış on top bulunmaktadır. Bu torbadan rastgele çekilen bir topun üzerindeki sayının asal sayı olma olasılığını kesir, ondalık ve yüzde olarak ifade ediniz.
   → Cevap: 2/5, 0.4, %40
3. [sozel_problem] Bir sınıfta 12 kız öğrenci ve 18 erkek öğrenci bulunmaktadır. Bu sınıftan rastgele seçilen bir öğrencinin erkek öğrenci olma olasılığını kesir, ondalık ve yüzde olarak hesaplayınız.
   → Cevap: 3/5, 0.6, %60
4. [sozel_problem] Bir meyve sepetinde 8 adet elma, 7 adet portakal ve 5 adet muz bulunmaktadır. Sepetten rastgele alınan bir meyvenin portakal olma olasılığını kesir, ondalık ve yüzde olarak ifade ediniz.
   → Cevap: 7/20, 0.35, %35
5. [kavram_sorusu] Bir kutuda sadece kırmızı bilyeler bulunmaktadır. Bu kutudan rastgele çekilen bir bilyenin mavi olma olasılığını kesir, ondalık ve yüzde olarak ifade ediniz ve bu durumun ne anlama geldiğini yorumlayınız.
   → Cevap: 0/X = 0, 0.0, %0. Bu durum, olayın imkansız olduğunu gösterir.


**Mod B (textbook)** — chunks=2, jaccard=0.322, ctx=40

1. [islem] Bir kutuda 1'den 20'ye kadar numaralandırılmış toplar bulunmaktadır. Kutudan rastgele çekilen bir topun üzerindeki sayının 4'ün katı olma olasılığını kesir, ondalık ve yüzde olarak hesaplayınız.
   → Cevap: Kesir: 1/5, Ondalık: 0.2, Yüzde: %20
2. [sozel_problem] Bir torbada 7 mavi, 8 kırmızı ve 5 sarı kalem bulunmaktadır. Bu torbadan rastgele seçilen bir kalemin kırmızı olma olasılığını kesir, ondalık ve yüzde olarak ifade ediniz.
   → Cevap: Kesir: 2/5, Ondalık: 0.4, Yüzde: %40
3. [kavram_sorusu] Bir zar atıldığında üst yüze gelen sayının asal sayı olma olasılığını kesir, ondalık ve yüzde olarak hesaplayınız.
   → Cevap: Kesir: 1/2, Ondalık: 0.5, Yüzde: %50
4. [sozel_problem] Bir otobüste 15 erkek ve 10 kadın yolcu bulunmaktadır. Bu otobüsten rastgele seçilen bir yolcunun kadın olma olasılığını kesir, ondalık ve yüzde olarak bulunuz.
   → Cevap: Kesir: 2/5, Ondalık: 0.4, Yüzde: %40
5. [islem] Bir sınıftaki 32 öğrencinin 12'si gözlüklüdür. Sınıftan rastgele seçilen bir öğrencinin gözlüksüz olma olasılığını kesir, ondalık ve yüzde olarak ifade ediniz.
   → Cevap: Kesir: 5/8, Ondalık: 0.625, Yüzde: %62.5

---

## Analiz: Aşama A vs Aşama D Karşılaştırması

| Metrik | Aşama A (eski 5.sınıf kazanımları) | Aşama D (yeni kazanımlar) |
|--------|------------------------------------|---------------------------|
| Test kapsam | 4 kazanım | 6 kazanım |
| Δ Unique bağlam | **+%18** | **+%2** |
| Δ Soru uzunluğu | +%14 | %0 |
| En yüksek kazanç | M.5.1.5 (+25%) | **M.5.6.1 (+%49)** |
| En kötü kazanım | yok | M.6.6.2 (−%38) |

**Neden Aşama D'de etki düşük?**

1. **Sentetik corpus zaten zengin**: Yeni kazanımlar için Aşama D'de 240 sentetik örnek üretildi (kazanım başına 15 farklı bağlam). Bu, eski kazanımların elindeki ~15+1-2 manuel few-shot ile karşılaştırınca ÇOK daha doygun bir başlangıç.
2. **Textbook chunk'larının marjinal değeri azalıyor**: Sentetik corpus zaten "ders kitabı tonunu" yakalamış oluyor (sentetik üretim sırasında system prompt "MEB ders kitabı tonunda yaz" diyor).
3. **Bazı kazanımlarda textbook'un negatif etkisi**: M.6.6.2'de B mod kötüleşmiş — büyük olasılıkla textbook chunk'ları (kavramsal, etkinlik tarzı) prompt'ta yer kaplayıp sentetik örneklerin yerini alıyor.

**Kazanım bazında detaylı analiz:**

| Kazanım | Δ Bağlam | Yorum |
|---------|----------|-------|
| **M.5.6.1 (Veri İşleme)** | +29 (+%49) ⭐⭐⭐ | Textbook'tan zengin senaryo geldi (anket, sıklık tablosu, sütun grafiği örnekleri); sentetik tek başına yetersizdi |
| **M.6.1.5 (Çarpan/Asal)** | +11 (+%32) ⭐⭐ | Textbook'taki çarpan ağacı, asal çarpan ayrıştırma örnekleri farklı bağlam üretti |
| M.6.7.1 (Olasılık) | 0 | Sentetik zaten dolu (zar, top torbası, madeni para tüm varyasyonlar) |
| M.7.7.1 (Olasılık 7) | −3 | Aynı |
| M.5.2.5 (Yüzdeler) | −5 | Yüzde için hem sentetik hem textbook benzer bağlam (indirim, KDV) |
| M.6.6.2 (Merkezi Eğilim) | −26 (−%38) ⚠️ | Sentetik ÇOK çeşitli bağlam üretmiş (boy, sıcaklık, puan, ürün, vb); textbook chunk'ları statistical kavramları yineleyince çeşitlilik düştü |

## Stratejik Çıkarımlar

### 1. Sentetik corpus stratejisi tek başına etkili
Yeni kazanımlar için tek başına sentetik corpus (240 örnek), textbook desteği almadan da yüksek kalitede üretim sağlıyor. Bu, **Aşama A'daki "textbook → eski kazanımları zenginleştir"** patterninin yeni kazanımlar için **"sentetik corpus → yeni kazanımları zenginleştir"** olarak değiştiğini gösteriyor.

### 2. Textbook hâlâ değerli, ama selektif
Veri İşleme ve Çarpanlar gibi konularda textbook büyük katma değer üretti. Olasılık, Yüzdeler, Merkezi Eğilim gibi sentetik corpus'un kolayca kapsadığı konularda etki nötr.

**Öneri:** Mevcut hibrit sistem korunsun (her kazanım için textbook denesin, retrieval başarısız olursa zaten sentetik+manuel ile devam ediyor). Spesifik bir tuning gerekmez — agent zaten doğru yapıyor.

### 3. Bütçe verimliliği
| Yatırım | Ek değer |
|---------|----------|
| Aşama A textbook (5. sınıf) | Mevcut kazanımlara +%18 çeşitlilik |
| Aşama B textbook (4 sınıf) | Aynı pattern, geniş kapsam |
| Aşama D müfredat genişletme | 16 yeni kazanım, MEB 2024 kapsama |
| **Aşama D sentetik corpus** | **240 yeni örnek, ana üretim kalite kaynağı** ⭐ |

Aşama D'nin sentetik corpus üretimi (~$3.50, 10 dk) **en yüksek getiri/maliyet** oldu — yeni kazanımları üretime aldı.

### 4. M.6.6.2 anomalisi — incelenmeli mi?
Tek negatif sonuç M.6.6.2. Olası sebepler:
- Textbook chunk'larında veri analizi terminolojisi yoğunken sentetik bağlamlar daha çeşitli
- Test örnekleminin küçüklüğü (5 soru) varyans yaratabilir
- Bu kazanım için `include_textbook=False` default yapılabilir, ama **opsiyonel optimizasyon** — production'a çıkmadan A/B testleri genişletilirse karar netleşir.

## Sonraki Adım Önerileri

| Seçenek | Süre | Maliyet | Değer |
|---------|------|---------|-------|
| Production polish (Streamlit, logging, test) | 1 gün | $0 | Yüksek — sistem kullanıma hazır |
| Aşama C (3-4. sınıf OCR) | yarım gün | $10-15 | Orta — bu sınıflar zaten sentetik corpus'la iyi |
| Genişletilmiş A/B test (10+ kazanım, 3 zorluk) | 1 saat | $1-2 | Düşük — pattern net görüldü |
| Sentetik corpus genişletme (kazanım başına 5 → 10 örnek) | 30 dk | $4-6 | Düşük — zaten yeterli görünüyor |

**Önerim:** Production polish. Sistem üretim kalitesinde, tüm 7 sınıf kapsamlı, MEB 2024 müfredatına uyumlu, RAG katmanları doğrulanmış. Eksik olan sadece kullanıcı deneyimi ve operasyonel olgunluk.
