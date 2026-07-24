# Monetizasyon / Abonelik Planı (İSKELET — tartışma taslağı)

> Durum: **KESİN — Pro/Pro+ kota-merdiveni + ek-paket (top-up) + Kurumsal(Faz2).** Güncelleme 2026-07-24 (bkz. §2 + §6).
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

### Değer çiti (KESİN — 2026-07-24; persona-SKU kararını GÜNCELLER → kota-merdiveni + top-up)
**Karar evrimi:** ~~Persona-SKU (Aile/Öğretmen, 2026-07-23)~~ kullanıcıyı kilitliyordu (ihtiyacı
iki personaya yayılan kişi "ben hangisiyim?" diye kalıyordu). **Persona artık PAZARLAMA dili**
(landing "veli/öğretmen misin?"), ürün DEĞİL. Ürün = tek **Pro** + **kota merdiveni**; TÜM
özellikler her ücretli kademede. Fark = yalnız **aylık kağıt kotası** (net sayı, bulanık değil).
**"Sınırsız" YOK → açık, cömert aylık çalışma-kağıdı sınırı** (gizli maliyet-tavanı = kandırma;
kullanıcı kararı 2026-07-24). Kota birimi = **çalışma kağıdı** (soru değil — kullanıcının zihinsel
+ bizim üretim/maliyet birimi).

| Özellik | 🆓 Ücretsiz | ⭐ Pro ₺199/ay | ⭐⭐ Pro+ ₺349/ay |
|---|---|---|---|
| Aylık çalışma kağıdı (açık; cache-hit SAYILMAZ) | **10** | **50** | **120** |
| Kalite | standart | **yeni nesil** | **yeni nesil** |
| PDF indirme | footer "Soru Atölyesi ile üretildi" | **white-label** | **white-label** |
| Quiz çözme + ilerleme + oyunlaştırma | ✅ | ✅ | ✅ |
| Çocuk takibi (bağlı hesap, **paylaşımlı kota**) | 1, temel | **3'e kadar, derin** | **3'e kadar, derin** |
| Çoklu sınıf + ödev/sonuç analitiği | 1 sınıf (viral) | **tam** | **tam** |
| 7 gün kartsız reverse trial | — | ✅ | ✅ |

**TEK fark = KOTA (50 vs 120).** White-label + çocuk takibi + çoklu sınıf/ödev **HER İKİ ücretli
kademede de** → veli de öğretmen de aynı ürünü alır, persona-kilit yok. Pro+ = 2.4× kota, +%75
fiyat (cazip yükseltme). Anonim önizleme (web, girişsiz) kotasız (SEO motoru). Anlık kota =
abonelik kotası (aylık reset) + varsa aktif ek-paket kredisi (aşağı).

### Ek kağıt paketi (top-up — KARAR 2026-07-24)
Abone aylık kotayı bitirince ay-sonunu beklemeden **ek kağıt satın alır** (tüketilebilir IAP):
- **Paketler:** +25 kağıt **₺89** · +75 kağıt **₺199**. Kağıt-başı fiyat abonelikten YÜKSEK
  (bilinçli: marj + "sürekli alıyorsan Pro+'a geç" doğal upsell'i).
- **Yalnız aktif aboneye** (Pro/Pro+). Ücretsiz kullanıcı → Pro'ya yönlendirilir.
- **30 günlük kullanım süresi** (satın alımdan; kullanılmazsa yanar — şeffaf tüketilebilir).
- **Tüketim sırası:** önce abonelik kotası (use-or-lose, aylık sıfırlanır), sonra ek paket;
  bir ek paket ay-sonundan önce bitecekse önce o harcanır ("en erken biten önce" → israfı önle).

### Aile hesap modeli — "bağlı hesaplar, PAYLAŞIMLI kota" (KARAR 2026-07-23/24)
Aile senaryosu = veli Pro/Pro+ alır, çocuk kullanır. Model = **bağlı hesaplar** (mevcut
`parent-code`/`link-child`; ekstra mimari yok):
- Veli kendi hesabına abone → 3 çocuğa kadar kodla bağlar → çocuklar premium'u **miras alır**
  (kendi cihazında kendi hesabıyla girer).
- **KRİTİK: kota PAYLAŞILIR** — aile TEK havuz (çocuk başına DEĞİL). 3 çocuk = "3 bedava
  sınırsız hesap" DEĞİL; hepsi tek Pro/Pro+ havuzundan çeker → maliyet çocuk sayısından bağımsız.
  3 çocuk sınırı = "gerçek aile" sınırı (bir sınıfa dağıtılmasın → o Kurumsal).
- **Entitlement kuralı:** `plan_of` = *"tenant premium mi VEYA bağlayan velisi premium mi"*;
  kota sayacı veli + bağlı çocukları TEK havuzda toplar. (Profiller/Netflix modeli → v2.)
- **Öğretmen ayrı paket DEĞİL** (persona-SKU kaldırıldı); öğretmen de Pro/Pro+ alır, sınıfa
  katılan öğrenciler ücretsiz (viral).

**Tasarım prensipleri:**
1. **Ücretsiz PDF footer'ı = dağıtım kaldıracı** (organik erişim darboğazımız); white-label = upgrade sebebi. **[Karar A: footer AÇIK.]**
2. **Alışkanlık döngüsü ücretsiz** (çözme/ilerleme/oyunlaştırma); para **hacme (kota) + profesyonelliğe (white-label)** biner.
3. **Sınıf/ödev viral kısmı ücretsiz** (1 sınıf + öğrenci çözme), ölçek (çoklu sınıf/analitik) ücretli. **[Karar B]**
4. **Persona = mesaj, Pro = ürün** (kilit yok). Yüksek-WTP'yi (öğretmen/dershane) **Kurumsal** ayrıca yakalar (Faz 2).

### Fiyat & trial (KESİN — 2026-07-24)
- **Pro ₺199/ay** (50 kağıt) · **Pro+ ₺349/ay** (120 kağıt) · ek paket **+25 ₺89 / +75 ₺199**
  (tüketilebilir, 30 gün, aboneye). Fiyatlar **KDV DAHİL** (B2C).
- **7 gün kartsız reverse trial.** Ayrı intro-indirim YOK (trial zaten kanca).
- Lansmanda **yalnız aylık** (SKU: `pro-aylik`, `proplus-aylik` + consumable `topup-25`, `topup-75`).
  Yıllık ("ayda ₺X gibi") sonra — MEA aylık-ağırlıklı.
- Fiyatlar başlangıç çıpası; RevenueCat/mağazada WTP verisiyle ayarlanır.

### 2.1 Ekonomi — net gelir & marj (GÜNCEL 2026-07-24)
Mobil IAP: **net gelir = gösterilen × ~0.60** (KDV −%20 → platform komisyonu −%15 → GVK Mük.20/B
banka stopajı −%15; hepsi nihai). Örn:
```
₺199 gösterilen → /1.20 (KDV) = ₺165.8 → ×0.85 (platform) = ₺140.9 → ×0.85 (stopaj) = ₺120  net
```
- Pro ₺199 → net **~₺120** · Pro+ ₺349 → net **~₺210** · +25 paket ₺89 → net ~₺53 · +75 ₺199 → net ~₺119.
- **Kağıt başı maliyet (D1+D2b+A+C sonrası, ÖLÇÜLDÜ — [[gen-cost-quality-2026-07]]):** harmanlanmış
  **~₺1-3/kağıt** (grade 8 zor uç ₺2.88; alt sınıf + cache-hit çok daha ucuz/bedava).
- **Marj kuralı (net-gelir/kağıt > maliyet ~₺1.5):** Pro ₺2.40/kağıt · Pro+ ₺1.75/kağıt ·
  +25 ₺2.14/kağıt · +75 ₺1.59/kağıt → **hepsi maliyet üstünde** ✅. Açık kağıt sayısı zaten
  worst-case'i sınırlar → **gizli maliyet-tavanına gerek YOK** (kullanıcı kararı: şeffaflık > "sınırsız yalanı").
- **Anti-bot:** görünmez günlük hız limiti (~15 kağıt/gün) — pazarlama sınırı değil, otomasyon freni.
- Not: LLM fiyatı fiyatı belirlemiyor; değere göre fiyatla. ([[unit-economics-llm-cost]] güncellendi:
  eski ₺0.02/soru varsayımı geçersiz — gerçek grade-8 ~₺1-3/kağıt.)

### 🏫 Kurum/Zümre (B2B) — Faz 2
- Koltuk/okul lisansı, faturalı. Yüksek ARPU, GROWTH_ROADMAP'e uygun. Bireysel motor
  oturunca eklenir.

---

## 3. Bizim mimariye entegrasyon (somut)

| Parça | Bizde ne var | Ne eklenir |
|---|---|---|
| Yetki kararı | `app/services/entitlements.py` seam (allowlist) | `is_premium` → Turso abonelik durumu (aktif sub veya trial) |
| Abonelik durumu | yok | Turso/libSQL `subscriptions` tablosu: tenant_id, plan, status, period_end, provider_ref, trial_end |
| Kota ölçümü | `USAGE_LEDGER` her üretimi tenant bazında kaydediyor (cache-hit hariç) | Aylık **çalışma-kağıdı** sayacı (soru değil) → plan kotasını generate uçlarında uygula (402/paywall). **Aile: veli+bağlı çocuklar TEK havuz.** |
| Ek paket kredisi (top-up) | yok | `top_up_credits` tablosu (tenant, amount, remaining, purchased_at, expires_at+30g). Tüketim: önce abonelik kotası, sonra en-erken-biten kredi. |
| Ödeme | yok | **RevenueCat** (mobil IAP): auto-renewable (Pro/Pro+) + **consumable** (topup-25/75) webhook → billing_store upsert. |
| Reverse trial | yok | İlk girişte `trialing` sub (trial_end +7g), sunucu-otoriter |
| Paywall UI | yok | Pro/Pro+ 2-kademe kartı (persona-farkında mesaj) + ek-paket CTA (kota dolunca) + "7 gün ücretsiz" + "istediğin an iptal"; güven-önce yerleşim |
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
**✅ KESİN (2026-07-24 — persona-SKU → Pro/Pro+ kota-merdiveni + top-up; nihai sayılar):**
- **Ürün = tek Pro + kota merdiveni; persona = pazarlama dili, SKU DEĞİL.** ~~Persona-SKU (Aile/
  Öğretmen, 2026-07-23)~~ kilitliyordu → kaldırıldı. TÜM özellikler her ücretli kademede; fark = yalnız kota.
- **Paketler:** 🆓 Ücretsiz **10 kağıt/ay** · ⭐ Pro **₺199 / 50 kağıt** · ⭐⭐ Pro+ **₺349 / 120 kağıt**.
  Kota birimi = **çalışma kağıdı** (soru değil), cache-hit sayılmaz. **"Sınırsız" YOK → açık sayı**
  (gizli maliyet-tavanı = kandırma; şeffaflık kararı).
- **Ek kağıt paketi (top-up):** +25 **₺89**, +75 **₺199** — tüketilebilir IAP, **30 günlük** süre,
  yalnız aboneye. Tüketim: önce abonelik kotası, sonra en-erken-biten kredi.
- **Aile = bağlı hesaplar + PAYLAŞIMLI kota** (3 çocuğa kadar, tek havuz → "3 bedava hesap" değil).
- **Kurumsal (okul/dershane) = AYRI, teklif-bazlı, faturalı, Faz 2** (yüksek-WTP'yi yakalar; IAP değil).
- **Marj doğrulandı:** net-gelir/kağıt (Pro ₺2.40 / Pro+ ₺1.75 / +25 ₺2.14 / +75 ₺1.59) > maliyet
  ~₺1.5 ([[gen-cost-quality-2026-07]] ölçümü). 7g reverse trial, ayrı intro-indirim yok, yalnız aylık.
- Açık: yıllık plan (sonra), fair-use günlük hız-limiti değeri (anti-bot), WTP ile fiyat iterasyonu.

**✅ Kapandı (2026-07-10):**
- **Persona:** hibrit — öğretmen **ve** veli ana persona.
- **Karar A:** ücretsiz PDF'te "Soru Atölyesi ile üretildi" footer AÇIK (dağıtım + upgrade tetiği).
- **Karar B:** sınıf/ödev viral kısmı ücretsiz (temel sınıf/ödev + veli bağı), ölçek+analitik Pro.

**⏸ ARŞİV (2026-07-23 — persona-SKU; 2026-07-24'te Pro/Pro+ kota-merdivenine ÇEVRİLDİ → üstteki KESİN blok geçerli. Yalnız "bağlı-hesap aile" kararı korundu, paylaşımlı-kota olarak):**
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
