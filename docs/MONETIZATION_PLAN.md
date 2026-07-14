# Monetizasyon / Abonelik Planı (İSKELET — tartışma taslağı)

> Durum: **taslak, hizalama bekliyor.** 2026-07-10.
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

### Değer çiti (KESİNLEŞTİ — 2026-07-10)
Tek Pro planı, persona-farkında mesajlaşma. Hibrit: öğretmen **ve** veli ana persona.

| Özellik | 🆓 Ücretsiz | ⭐ Pro |
|---|---|---|
| Anonim önizleme üretimi (girişsiz) | ✅ (SEO motoru) | ✅ |
| Giriş yapınca üretim | **aylık ~10-15 kağıt/quiz** (kota) | **fair-use sınırsız** |
| Kalite | standart | **yeni nesil** |
| PDF indirme | ✅ **alt bilgide "Soru Atölyesi ile üretildi"** | ✅ **markasız + kendi logo (white-label)** |
| Quiz çözme (kendi + paylaşılan) | ✅ | ✅ |
| İlerleme panosu + oyunlaştırma | ✅ | ✅ (daha derin analitik) |
| Sınıf / ödev atama | **temel: 1 sınıf** (viral döngü) | **çoklu sınıf + sonuç panosu + kazanım analitiği** |

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
- **Veli:** sınırsız pratik + yeni nesil kalite + çocuğun derin ilerleme takibi.
  (Kasual veli ücretsiz kalır → ağızdan ağıza yayar, sorun değil.)

### ⭐ Pro fiyat & trial
- **Aylık-öncelikli** fiyat + yıllık "aylık ₺X gibi" çerçeveli.
- **7 gün kartsız reverse trial.**
- Fiyat hipotezi (DOĞRULANACAK): MEA ~%50 × NA education aylık →
  **~₺149-199/ay**, yıllık **~₺990-1290** (≈2 ay bedava, "≈₺99/ay" gösterimi).
  Lansmanda %50 intro indirim.

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
- **Persona:** hibrit — öğretmen **ve** veli ana persona (tek Pro plan, persona-farkında mesaj).
- **Değer çiti:** bölüm 2'deki tablo. Fence = hacim (kota) + profesyonellik (white-label) +
  yönetim (çoklu sınıf/analitik). Alışkanlık döngüsü (çözme/ilerleme/oyunlaştırma) ücretsiz.
- **Karar A:** ücretsiz PDF'te "Soru Atölyesi ile üretildi" footer AÇIK (dağıtım + upgrade tetiği).
- **Karar B:** sınıf/ödev viral kısmı ücretsiz (1 sınıf + öğrenci çözme), ölçek+analitik Pro.

**⏳ Açık (TARTIŞILACAK):**
1. **Ücretsiz kota seviyesi** — öneri: cömert (~10-15/ay), organik erişim darboğazı nedeniyle.
   Kota birimi: kağıt mı, quiz mi, ikisi ortak havuz mu? Aylık mı haftalık mı reset?
2. **Ödeme + tüzel kişilik** — iyzico mı PayTR mı; şirket/şahıs işletme hazır mı?
3. **Fiyat çıpası** — ₺149-199/ay hipotezi kabul mü, yoksa WTP ölçümüyle mi netleştirelim?
4. **Trial uzunluğu** — 7 gün (öneri) vs daha uzun (rapor: uzun trial %70 daha iyi çevirir
   ama piyasa kısaltıyor).

---

## 7. Ölçüm (para öncesi bile)
- Huni: giriş → kota doldurma → trial başlangıç → trial bitiş davranışı → (Faz B) ödeme.
- Kuzey metrik (çıkış kapısı): ilk ödeme + birim ekonomi (LTV > CAC + LLM maliyeti).
- Reverse trial dönüşüm oranı (hedef: rapor %4.5 mertebesi).
