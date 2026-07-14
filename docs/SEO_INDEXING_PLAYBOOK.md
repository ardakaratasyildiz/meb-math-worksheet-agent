# SEO İndeksleme & Backlink Playbook

**Tarih:** 2026-07-13 · **Yöneten metrik:** organik oturum/hafta.
Kaynak teşhis: `scripts/seo_index_status.py`, `scripts/metrics_report.py` (canlı SC + GA4).

> **Bu dokümanın tek işi:** yeni-domain darboğazını (indeksleme + otorite) kapatmak.
> Kod işi DEĞİL — sayfalar, sitemap, iç linkleme, canonical, structured data hepsi
> doğru. Kaldıraç saha işinde: elle Request Indexing + backlink + zaman.

---

## 1. Durum teşhisi (2026-07-13)

| Ölçüm | Değer |
|---|---|
| Sitemap URL | 310 (hepsi matematik) |
| Aramada performans gösteren sayfa | **6** |
| Programatik sayfa indeksli | **0** |
| Organik arama oturumu (28g) | 9 (trafiğin çoğu referral/direct) |
| SC tıklama / gösterim (28g) | 13 / 163 |

**Kritik bulgu:** 163 gösterimin ~137'si tek markasal sorgu — **"soru atölyesi"**
(pos 1.0). Yani tüm organik trafik markasal/navigasyonel. **Marka-dışı keşif sıfır.**

**Head-term hub'ların coverage durumu (`seo_index_status.py --hubs`):**

- ✅ İndeksli: `/`, `/calismalar`
- ⚠️ **Crawled - not indexed** (tarandı, indekslemeye değer bulunmadı → otorite eşiği):
  `/lgs-matematik`, `/1..6-sinif-matematik`
- ❌ **Unknown to Google** (hiç taranmadı → keşif sorunu):
  `/7-sinif-matematik` ve düşük-sınıf konu sayfalarının çoğu

**Teşhis:** Teknik engel YOK. Sorun = **~2 aylık domain otoritesi ~0** → Google
tarama bütçesi ayırmıyor + taradığını indekslemeye değmez buluyor.

**Bu yüzden yeni sayfa (ör. Fen/Türkçe SEO landing'leri) ŞU AN işe yaramaz:**
göz ardı edilen 310 sayfalık yığına indekslenmeyecek 40 sayfa daha eklemek olur.
Yeni ders SEO'su, hub'lar indekslenmeye BAŞLADIKTAN sonra açılmalı.

---

## 2. İşe yarayan / yaramayan (yeni domain)

| ✅ Yarar | ❌ Yaramaz |
|---|---|
| Backlink (yeni domainde **1 numaralı** kaldıraç) | Daha çok sayfa üretmek |
| Elle "Request Indexing" (SC, ~10-12/gün) | Sitemap re-submit |
| Marka arama hacmini artırmak (paylaşım/PR) | Kod/teknik SEO ince ayarı (zaten doğru) |
| İç linkleme (yapıldı, PR #65) + zaman | Meta/keyword oynaması |

---

## 3. Request Indexing worklist (SC · günlük ~10-12 kota)

Search Console → üstteki arama kutusuna URL yapıştır → **"URL'nin test edilmesini
iste" / "Request Indexing"**. Sıra değerden düşüğe. UNKNOWN sayfalarda en etkili
(keşfi zorlar); crawled-not-indexed'da nudge + otorite gerekir.

**Gün 1-2 — head term'ler (en yüksek değer):**
```
https://soruatolyesi.com/7-sinif-matematik      ← unknown, önce bu (keşif)
https://soruatolyesi.com/lgs-matematik          ← en yüksek arama hacmi
https://soruatolyesi.com/8-sinif ... (varsa)
https://soruatolyesi.com/6-sinif-matematik
https://soruatolyesi.com/5-sinif-matematik
https://soruatolyesi.com/4-sinif-matematik
https://soruatolyesi.com/3-sinif-matematik
https://soruatolyesi.com/2-sinif-matematik
https://soruatolyesi.com/1-sinif-matematik
```

**Gün 3+ — en çok arama hacmi olan konu/kazanım sayfaları** (LGS + üst sınıf önce).
Güncel unknown/not-indexed listesini çekmek için:
```
python scripts/seo_index_status.py --limit 60
```
UNKNOWN kovasındakileri önce, CRAWLED_NOT_INDEXED sonra iste.

> Not: crawled-not-indexed sayfalarda Request Indexing tek başına yetmeyebilir —
> Google zaten görüp geçti. Bunları asıl açan §4 backlink'ler. İkisini paralel yürüt.

### 3b. Yarı-otomatik: Google Indexing API (`scripts/seo_request_indexing.py`)

Elle tek tek yerine toplu bildirim. **Dürüst çerçeve:** API resmî olarak yalnız
JobPosting/BroadcastEvent destekler; genel sayfalarda indekslemeyi garanti etmez
AMA tipik olarak **bir crawl tetikler** → "unknown" (hiç taranmamış) sayfalarda
değerli (keşfi zorlar), "crawled-not-indexed"de sınırlı.

**Kurulum (bir kez, kullanıcı):**
1. **Indexing API'yi etkinleştir** (şu an SERVICE_DISABLED):
   `https://console.developers.google.com/apis/api/indexing.googleapis.com/overview?project=gen-lang-client-0770878935`
   veya gcloud varsa: `! gcloud services enable indexing.googleapis.com --project=gen-lang-client-0770878935`
2. **SC'de sahiplik:** Search Console → soruatolyesi.com → Ayarlar → Kullanıcılar ve
   izinler → ekle `metrics-reader@gen-lang-client-0770878935.iam.gserviceaccount.com`
   rol **Sahip (Owner)**. (Indexing API yalnız site sahiplerini kabul eder.)

**Kullanım:**
```
python scripts/seo_request_indexing.py --dry-run          # ne gönderilecek, göster
python scripts/seo_request_indexing.py --only-unknown     # sadece keşif sayfaları
python scripts/seo_request_indexing.py                    # unknown + not-indexed (≤180/gün)
```
Kota 200/gün (script tavanı 180). Coverage'ı otomatik çekip indeksli olanları atlar,
"unknown"ı önceler.

---

## 4. Backlink & dağıtım playbook (asıl kaldıraç)

Hedef: birkaç **konu-alakalı, indeksli** siteden `soruatolyesi.com`'a link + marka
bahsi. 5-10 kaliteli link bile ~2 aylık domainde crawl bütçesini kökten değiştirir.

**Hızlı kazançlar (bugün yapılabilir):**
1. **Ekşi Sözlük** — "soru atölyesi" başlığı aç/besle (linkli). Hem backlink hem
   marka-arama tetikler (zaten çalışan tek kanal markasal arama).
2. **Facebook öğretmen/veli grupları** (TR'de dev): "Sınıf Öğretmenleri",
   "LGS Veli Grubu", "Matematik Öğretmenleri Paylaşım" — ücretsiz araç olarak paylaş.
   Gruplar nofollow olsa da referral + marka-arama + dolaylı keşif getirir.
3. **Ekşi/Reddit/Quora TR** eğitim başlıklarında ilgili sorulara faydalı cevap + link.
4. **Ürün dizinleri:** Product Hunt (eğitim), alternatif "ücretsiz eğitim araçları"
   TR blog derlemeleri, okul-öncesi/eğitim kaynak dizinleri.

**Orta vade (haftalık 1-2):**
5. **Öğretmen blogları / eğitim siteleri** — konuk yazı veya "faydalı kaynaklar"
   listesine eklenme talebi (dofollow, konu-alakalı = en değerli).
6. **YouTube LGS/matematik kanalları** — açıklama linki karşılığı içerik/işbirliği.
7. **Yerel okul/dershane** iletişimi — sınıf kodu özelliğiyle (öğretmen→öğrenci)
   organik olarak site linki paylaşılır.

**İlke:** konu-alaka > link adedi. 3 eğitim sitesinden dofollow link, 50 alakasız
dizinden iyidir.

---

## 5. Ölçüm ritmi (haftalık)

```
# İndeks coverage — hub'lar hızlı, tam tarama yavaş (kota ~2000/gün)
python scripts/seo_index_status.py --hubs
python scripts/seo_index_status.py --limit 60

# Organik oturum + funnel
PYTHONIOENCODING=utf-8 python scripts/metrics_report.py
```

**Başarı sinyali (sırayla beklenir):**
1. Hub'lar UNKNOWN → CRAWLED → **INDEXED** geçer (§5 script "indeksli" sayısı artar).
2. SC gösterim marka-dışı sorgulara yayılır ("5. sınıf matematik çalışma kağıdı" vb.).
3. Organik oturum/hafta çift haneye çıkar → **o zaman** yeni ders SEO landing'leri aç
   (Fen/Türkçe/Sosyal/İngilizce — altyapı codegen-hazır, [[feedback-plan-progress]]).

**Baz çizgisi (2026-07-13):** hub'larda 2/10 indeksli, organik 9 oturum/28g.
Bir sonraki kontrolde bu iki sayı yükseliyorsa çark dönüyor demektir.
