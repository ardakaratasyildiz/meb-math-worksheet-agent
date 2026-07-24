# Monetizasyon / Abonelik Planı (İSKELET — tartışma taslağı)

> Durum: **model netleşti (persona bazlı + aile bağlı-hesap).** Güncelleme 2026-07-23 (bkz. §6).
> Kaynak analiz: RevenueCat *State of Subscription Apps 2026* (SOSA, 333 sf.) +
> bizim birim ekonomi & edinim gerçeklerimiz.
> Bu belge PROJECT_PLAN Faz 5 (Monetization — "mimari hazır, ertelendi")'in
> somutlaştırılmış hâlidir. Çıkış kapısı: **ilk ödeme alındı + birim ekonomi doğrulandı.**

---

## 0. Kuzey yıldızı & çerçeve

- Ürün stratejisi kuzey yıldızı (PROJECT_PLAN): **erişim büyüt + içerik kapsamı → para SONRA.**
  Monetizasyon bunu **baltalamamalı** (özellikle organik erişimi).
- Fiyatlama **değere göre**, maliyete göre değil: LLM üretim maliyeti ~$0.0004/soru,
  marj ~%85+ ([[unit-economics-llm-cost]]). Fiyatı LLM maliyeti belirlemez.
- Yön (kullanıcı kararı, 2026-07-09): **önce bireysel abonelik, sonra B2B kurumsal/zümre.**

---

## 1. Rapordan bize dokunan 4 belirleyici bulgu

1. **Freemium bizde tercih değil, zorunluluk.**
   Hard paywall install→paid'de 5× çeviriyor (10.7% vs 2.1%) ama 1-yıl retention
   neredeyse aynı (27% vs 28%). Hard paywall'un bedeli = ücretsiz kullanıcıların
   getirdiği organik erişim/word-of-mouth. **1 numaralı darboğazımız tam bu**
   (organik ~0, indeksleme — GROWTH_ROADMAP). Rapor: freemium doğru seçim, ücretsiz
   kullanıcılar word-of-mouth/marka ölçeği getiriyorsa. → **Anonim üretim + ücretsiz
   kademe kalmak ZORUNDA.**

2. **"Reverse trial" en yüksek kaldıraç.**
   Ücretsiz ürüne paywall eklerken: kayıt olan kullanıcıya 7 gün **kartsız tam Pro**,
   süre bitince paywall'da kaybı göster (kayıp-kaçınma). Rapor: freemium dönüşümü
   %0.4 → %4.5 (11×). 7 gün = Education'ın 5-9g tatlı noktası + MEA hızlı Day-0 kararı.

3. **Türkiye = MEA profili.**
   - Plan dağılımı **%52-55 aylık** (en yüksek), yıllık en düşük (%19) → aylığı öne koy.
   - Fiyatlar NA'nın **~%45-55'i** → TRY fiyatı buna göre.
   - Day-0 dönüşümü en hızlı (%63.5) → değeri/teklifi öne al.
   - Yıllığı **"aylık ₺X gibi"** çerçevele → +%30 trial-start, +%10 yıllık alım (fiyat sabit).
   - İlk yenileme make-or-break (yıllıkların ¾'ü bir kez bile yenilemiyor).
   - Android/yerel tahsilatta **%32 istemsiz churn** → iyzico/PayTR dunning-retry kritik.

4. **AI ürünüyüz: +%41 gelir/ödeyen ama -%30 retention.**
   Genel AI "satar ama tutmaz." Panzehir: müfredat-bağlı **dönem boyu tekrar-kullanım**.
   Konumlandırma: "tek seferlik AI oyuncağı" değil, **"dönem boyu MEB asistanı."**

### Yararlı benchmark'lar (referans)
| Metrik | Değer (rapor) |
|---|---|
| Education yıllık medyan fiyat | $44.99 (rapordaki en yüksek kategori) |
| Education aylık medyan | $9.99 |
| Emerging market fiyat / NA | ~%45-55 |
| Trial→paid (Education, MEA) | ~%24.9 |
| Y1 RLTV/ödeyen (Education, MEA) | ~$20 |
| Standart intro indirim | −%50 |
| Yıllık aktif yenileme oranı | %83 (aylık %39, haftalık %19) |

---

## 2. Önerilen model: Freemium + Reverse-trial + fair-use kota

### Değer çiti (REVİZE — 2026-07-23; "iki Pro kademesi" 2026-07-16 kararını GÜNCELLER → PERSONA BAZLI)
**Kademe ekseni değişti (2026-07-23, kullanıcı kararı):** Soyut "Pro / Pro+" (kota vs
analitik ayrımı bulanıktı) yerine **persona bazlı iki ücretli paket — 👨‍👩‍👧 Aile ve 🎓 Öğretmen**
+ **kalıcı ücretsiz kademe** + **7 gün kartsız reverse trial**. Gerekçe: bu üründe **satın
alan ≠ kullanan** (veli öder/çocuk kullanır; öğretmen öder/sınıfı kullanır) → müşteri
kendini bir "kutuda" görünce paket canlanır. Fiyat aralığı aynı (~₺199-249); sadece sunum
netleşti.

| Özellik | 🆓 Ücretsiz (kalıcı) | 🎁 7g Deneme | 👨‍👩‍👧 Aile ~₺199/ay | 🎓 Öğretmen ~₺249/ay |
|---|---|---|---|---|
| Anonim önizleme üretimi (girişsiz, web) | ✅ (SEO motoru) | — | ✅ | ✅ |
| Giriş sonrası üretim kotası | **30-50 soru/ay** | tam-Pro / 7 gün | **sınırsız\*** | **sınırsız\*** |
| Kalite | standart | **yeni nesil** | **yeni nesil** | **yeni nesil** |
| PDF indirme | ✅ footer "Soru Atölyesi ile üretildi" | ✅ white-label | ✅ **white-label** | ✅ **white-label** |
| Quiz çözme (kendi + paylaşılan) | ✅ | ✅ | ✅ | ✅ |
| İlerleme + oyunlaştırma | ✅ | ✅ | ✅ | ✅ |
| Temel sınıf/ödev + veli bağı | ✅ (viral döngü) | ✅ | ✅ | ✅ |
| **Çocuk takibi (bağlı çocuk, derin ilerleme)** | 1 çocuk, temel | ✅ | **3 çocuğa kadar, derin** | — |
| **Çoklu sınıf + ödev/sonuç analitiği (kazanım kırılımı)** | 1 sınıf, temel | ✅ | — | **tam** |

\***"sınırsız" = arka planda ~2.500 soru/ay adil-kullanım tavanı** (pazarlamada sınırsız;
tavan yalnız kötüye-kullanım kuyruğunu keser — bkz. §2.1 ekonomi).

**Kota birimi = soru/ay** (USAGE_LEDGER üretim başına soru sayar), **aylık reset**,
**cache-hit üretimler kotadan düşmez** (fiyat sayfasındaki söz korunur). Anonim üretim
kotasızdır (SEO motoru — web). Aile/Öğretmen ayrımı **kota değil, kime hizmet ettiği**:
Aile = çocuk takibi (3 çocuğa kadar), Öğretmen = çoklu sınıf + ödev analitiği. White-label,
sınırsız üretim ve yeni-nesil kalite **her iki üründe de** var.

### Aile hesap modeli — "bağlı hesaplar" (KARAR 2026-07-23)
Aile paketinde **ödeyen veli, kullanan çocuk.** Model = **bağlı hesaplar** (mevcut
`parent-code`/`link-child` mimarisiyle birebir; ekstra mimari yok):
- Veli **kendi** Clerk hesabına abone olur → entitlement veli hesabında.
- Kodla bağladığı çocuk hesapları (max 3) premium'u **miras alır.**
- Çocuk kendi cihazında **kendi hesabıyla** girer, premium'u görür.
- **Entitlement kuralı (yeni):** `plan_of` çözümü = *"tenant premium mi VEYA tenant'ı
  bağlayan bir veli premium mi"*. `entitlements.py` içinde bağlı-veli lookup eklenir.
- (Alternatif "profiller / Netflix modeli" — tek veli hesabı altında çocuk profilleri —
  KVKK-küçük dostu ama yeni mimari; v2'ye ertelendi. Küçük yaş ağırlığı artarsa yeniden bakılır.)
- **Öğretmen paketi seat/aile İÇERMEZ:** tek hesap; sınıfa katılan öğrenciler ücretsiz (viral döngü).

**Tasarım prensipleri (neden böyle):**
1. **Ücretsiz PDF footer'ı = dağıtım kaldıracı.** Her ücretsiz PDF "Soru Atölyesi ile
   üretildi" taşır → organik erişim (darboğazımız). Footer'ı kaldırmak (white-label)
   başlı başına Pro sebebi. **[Karar A: footer AÇIK.]**
2. **Alışkanlık döngüsü ücretsiz, para hacim + profesyonellik + yönetime biner.**
   Çözme/ilerleme/oyunlaştırma ücretsiz (kullanım = retention = ileride dönüşüm).
   Kota dolan hacim için, öğretmen white-label + sınıf için öder.
3. **Sınıf/ödev hem Pro hem büyüme döngüsü.** Öğretmen ödev atayınca 20-30 öğrenci
   siteye girer (viral edinim). O yüzden **viral kısım ücretsiz** (1 sınıf + öğrenci
   katılım/çözme), **ölçek+analitik Pro** (çoklu sınıf, sonuç panosu, kazanım kırılımı).
   **[Karar B: viral kısım ücretsiz, ölçek Pro.]**

**Persona başına "neden ödeyeyim":**
- **Öğretmen:** white-label + çoklu sınıf/ödev/sonuç panosu + hacim. (Güçlü çıpa.)
- **Veli:** çocuğa sınırsız pratik + yeni nesil kalite + 3 çocuğa kadar derin ilerleme takibi.
  (Kasual veli ücretsiz kalır → ağızdan ağıza yayar, sorun değil.)

### Fiyat & trial (GÜNCELLENDİ — 2026-07-23)
- İki persona paketi: **Aile ~₺199/ay**, **Öğretmen ~₺249/ay**. İkisi de sınırsız üretim
  (fair-use tavanlı) + white-label + yeni nesil kalite; ayrım çocuk-takibi vs sınıf-analitiği.
  Fiyatlar **KDV DAHİL** gösterilir (B2C).
- **7 gün kartsız reverse trial** (tam-Pro deneyim).
- Lansmanda **yalnız aylık** (2 SKU: `aile-aylik`, `ogretmen-aylik`). Yıllık plan
  ("aylık ₺X gibi" çerçeveyle) sonra eklenebilir — MEA aylık-ağırlıklı profiline uygun.
- Fiyatlar başlangıç çıpası; RevenueCat/mağaza fiyatında kolay ayarlanır (WTP verisiyle iterasyon).
- (Ref: rapor hipotezi ~₺149-199/ay idi; ₺199/₺249 bu aralığın üst-ucu, değer ürünü için savunulabilir.)

### 2.1 Ekonomi — net gelir tuzağı & fair-use tavanı (2026-07-23 eklendi)
Mobil IAP'te **gösterilen fiyat ile cebe giren çok farklı.** Gösterilen ₺200/ay (KDV dahil):

```
₺200 gösterilen (KDV dahil)
 −KDV %20 (Apple/Google GİB'e yatırır, biz taraf değiliz)  → ₺166.7
 −Platform komisyonu %15 (Small Business / <$1M)           → ₺141.7
 −GVK Mük. 20/B banka stopajı %15 (nihai vergi)            → ₺120.4  ← net (founder)
```
- **Tipik Pro kullanıcı** (300-800 soru/ay): LLM maliyeti ~₺5-16 → **marj ~%90**. Rahat kurtarır.
- **TUZAK:** Gerçek "sınırsız" abuse tail (~10.000 soru) LLM'de ~₺160-200'e çıkar (₺40/$ kur) →
  net gelir ₺120'yi **geçer, zarar.** Ayrıca kur yükselirse TL maliyet artar, IAP fiyatı yapışkan.
- **Çözüm:** "sınırsız" pazarla ama arkada **~2.500 soru/ay adil-kullanım tavanı.** Bu gerçek
  kullanıcıların ~%99'unu kapsar; tavanda LLM ~₺50 → hâlâ ~₺70 marj. `USAGE_LEDGER` zaten sayıyor;
  tavan aşımında nazik "bu ay çok ürettin, gelecek ay sıfırlanacak" mesajı (churn'e sürüklemeden).
- **Not:** Soru sınırı bir MALİYET aracı değil, bir **segmentasyon/kötüye-kullanım** aracı
  ([[unit-economics-llm-cost]]: soru başına ~$0.0004-0.0005, LLM fiyatı belirlemiyor).

### 🏫 Kurum/Zümre (B2B) — Faz 2
- Koltuk/okul lisansı, faturalı. Yüksek ARPU, GROWTH_ROADMAP'e uygun. Bireysel motor
  oturunca eklenir.

---

## 3. Bizim mimariye entegrasyon (somut)

| Parça | Bizde ne var | Ne eklenir |
|---|---|---|
| Yetki kararı | `app/services/entitlements.py` seam (allowlist) | `is_premium` → Turso abonelik durumu (aktif sub veya trial) |
| Abonelik durumu | yok | Turso/libSQL `subscriptions` tablosu: tenant_id, plan, status, period_end, provider_ref, trial_end |
| Kota ölçümü | `USAGE_LEDGER` her üretimi tenant bazında kaydediyor | Aylık sayaç → ücretsiz kotayı generate uçlarında uygula (402/paywall sinyali) |
| Ödeme | yok | iyzico/PayTR hosted checkout + webhook → sub satırını güncelle; recurring + dunning |
| Reverse trial | yok | İlk girişte `trialing` sub (trial_end +7g), sunucu-otoriter |
| Paywall UI | yok | 2-planlı, vurgulu fiyat, "aylık ₺X" çerçeve, sosyal kanıt, "istediğin an iptal", güven-önce yerleşim (kota dolunca/trial bitince, jarring değil) |
| Kimlik | Clerk (userId = tenant_id) | değişmez |

**Enforcement noktaları:** `worksheets.py` + `quizzes.py` generate uçları → üretimden
önce entitlement + kota kontrolü. Sunucu her zaman otoriter (client bayrağına güven yok —
mevcut `entitlements` ilkesi korunur).

---

## 4. Sert önkoşullar (kod değil — canlı tahsilat için ZORUNLU)
- **Tüzel kişilik** (şahıs/limited şirket) + ödeme sağlayıcısı işletme onayı.
- **Mesafeli satış sözleşmesi + KVKK/gizlilik + iade/cayma politikası.**
- Bunlar PROJECT_PLAN'da "para track'inin önkoşulu" (legal placeholder'lar hâlâ açık).
- Kod bunlara paralel kurulabilir; ama canlı tahsilat bunlar olmadan AÇILAMAZ.

---

## 5. Fazlama (öneri)
- **Faz A — Paywall seam + reverse trial (tahsilatsız):** kota + trial + paywall UI +
  entitlement Turso'ya bağlanır. Para YOK; sadece dönüşüm hunisi ölçülür (kaç kişi kotayı
  dolduruyor, trial bitince ne yapıyor). Riski düşük, öğrenme yüksek.
- **Faz B — Gerçek tahsilat:** iyzico/PayTR entegrasyonu + webhook + dunning + legal.
  Önkoşullar (bölüm 4) tamamsa açılır.
- **Faz C — B2B kurumsal/zümre:** koltuk lisansı, fatura.

---

## 6. Kararlar
**✅ Kapandı (2026-07-10):**
- **Persona:** hibrit — öğretmen **ve** veli ana persona.
- **Karar A:** ücretsiz PDF'te "Soru Atölyesi ile üretildi" footer AÇIK (dağıtım + upgrade tetiği).
- **Karar B:** sınıf/ödev viral kısmı ücretsiz (temel sınıf/ödev + veli bağı), ölçek+analitik Pro.

**✅ Kapandı (2026-07-23 — kademe ekseni PERSONA BAZLI + aile hesap modeli):**
- **Plan yapısı:** **persona bazlı** — 👨‍👩‍👧 Aile + 🎓 Öğretmen (bölüm 2 tablosu).
  ~~Soyut Pro/Pro+~~ (2026-07-16) GÜNCELLENDİ. Gerekçe: satın alan ≠ kullanan; müşteri
  kendini "Aile" ya da "Öğretmen" kutusunda görünce paket canlanır. Fiyat aralığı aynı.
- **Aile hesap modeli:** **bağlı hesaplar** — veli öder, kodla bağlı çocuklar (max 3) premium'u
  miras alır (mevcut parent-code/link-child mimarisi; §2 "Aile hesap modeli"). Profiller/Netflix
  modeli v2'ye ertelendi. Öğretmen = tek hesap (seat yok), öğrenciler ücretsiz.
- **Fiyat:** Aile **~₺199/ay**, Öğretmen **~₺249/ay**; ikisi de sınırsız (fair-use ~2.500 soru/ay).
  KDV **dahil**. Lansmanda yalnız aylık (2 SKU: `aile-aylik`, `ogretmen-aylik`). Yıllık sonra.
- **Fair-use tavanı:** "sınırsız" pazarla, arkada ~2.500 soru/ay (§2.1 ekonomi: mobil IAP net
  gelir ~₺120, gerçek-sınırsız abuse tail ~₺200 zarar riski → tavan marjı korur).

**✅ Kapandı (2026-07-16 — ARŞİV, 2026-07-23 GÜNCELLENDİ):**
- ~~İki Pro kademesi (Pro ₺189 / Pro+ ₺249, kota + analitik ayrımı).~~ Persona bazlıya çevrildi (üstte).
- **Ücretsiz kota:** **kalıcı 100 soru/ay** (tüm ders ortak havuz, aylık reset, cache-hit sayılmaz).
  Kalıcı ücretsiz kademe KORUNUR (erişim darboğazı → footer motoru + alışkanlık döngüsü yaşasın).
- **Trial:** **7 gün kartsız** tam-Pro (reverse trial).
- **Kurumsal/B2B:** Faz 2 — manuel/teklif (self-serve değil).
- **Ödeme sağlayıcı:** **iyzico** (Abonelik API; docs/IYZICO_ENTEGRASYON_PLANI.md).
- **KDV gösterimi:** KDV dahil (B2C). **e-Arşiv fatura:** başta manuel (GİB/SMMM), hacimle otomatikleşir.

**⏳ Açık (kod dışı — SMMM/gerçek dünya):**
- Tüzel kişilik kuruluşu (şahıs şirketi) — docs/SIRKET_KURULUS_CHECKLIST.md.
- Genç girişimci istisnası uygunluğu (SMMM'ye).
- WTP (ödeme istekliliği) verisiyle fiyat iterasyonu (lansman sonrası ölç).

---

## 7. Ölçüm (para öncesi bile)
- Huni: giriş → kota doldurma → trial başlangıç → trial bitiş davranışı → (Faz B) ödeme.
- Kuzey metrik (çıkış kapısı): ilk ödeme + birim ekonomi (LTV > CAC + LLM maliyeti).
- Reverse trial dönüşüm oranı (hedef: rapor %4.5 mertebesi).
