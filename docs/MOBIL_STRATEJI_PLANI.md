# Soru Atölyesi — Mobil Uygulama Stratejisi & Yol Haritası

> **Durum:** tasarım / hizalama · 2026-07-20 · Kararlar birlikte alındı (aşağıda §2).
> **Kapsam:** Bu belge mobil uygulamanın **strateji, mimari, teknoloji ve yol
> haritası** kaynağıdır. Ödeme iş modeli / fiyat / değer çiti kararları
> [`MONETIZATION_PLAN.md`](./MONETIZATION_PLAN.md)'de; ödeme altyapısı (entitlement,
> Clerk doğrulama, Turso) [`IYZICO_ENTEGRASYON_PLANI.md`](./IYZICO_ENTEGRASYON_PLANI.md)
> ve [`TEKNIK_MIMARI.md`](./TEKNIK_MIMARI.md)'de. Şirket kuruluşu
> [`SIRKET_KURULUS_CHECKLIST.md`](./SIRKET_KURULUS_CHECKLIST.md)'te.
> **Çıkış kapısı (v1):** App Store + Google Play'de yayında; sıcak lead'ler abone;
> mobil IAP → backend entitlement → hem mobilde hem web'de premium doğrulanmış.

---

## 0. Yönetici özeti

- **Stratejik hamle:** Web'den **hiç ödeme almadan** (ücretsiz SEO/edinim hunisi
  olarak kalır), tüm tahsilatı **mobil App Store / Google Play IAP** üzerinden
  yaparız. Bu, Türkiye'de **şirket kurmadan** yasal gelir sağlar (GVK Mük. 20/B
  kazanç istisnası — §3).
- **Entitlement hesaba bağlıdır:** mobilde abone olan kullanıcı web'deki
  premium özellikleri (ör. gelecekteki öğretmen "Sınıfım") de kullanır. Tek premium
  bayrağı, Clerk hesabına bağlı. Web ve mobil ödeme yolları **tek entitlement
  sisteminde birleşir** (iyzico planındaki `entitlements` bağı + Clerk P0 doğrulama).
- **v1 kapsamı:** öğrenci çekirdeği + çalışma kağıdı üretimi. Öğretmen "Sınıfım" v2.
- **İlke:** *daha az şey yap, ama native ve kusursuz yap.* Kalite, takvimin önünde.
  WebView-wrapper **reddedildi** (yüzeysel + Apple 4.2 reddi). Çekirdek içerik **tam
  native** render edilir.
- **Teknoloji omurgası:** Expo (React Native) + monorepo, web stack'iyle hizalı
  (Tailwind→NativeWind, Zustand, zod, Clerk). Ödeme = RevenueCat.
- **~1000 kullanıcıya** ulaşınca şirket açılır + iyzico ile web ödemesi devreye
  girer (o aşama bu belgenin dışı; iyzico planı hazır bekliyor).

---

## 1. Neden mobil-önce, neden şirketsiz

| | Web (iyzico) | Mobil (IAP) |
|---|---|---|
| Şirket | **Gerekir** | **Gerekmez** (GVK Mük. 20/B) |
| Vergi | Kademeli gelir vergisi + muhasebeci | **%15 sabit stopaj, nihai** |
| KDV | Var (mükellef biziz) | **Muaf** (Apple/Google son kullanıcıdan tahsil edip yatırır) |
| Muhasebeci | Zorunlu (~3-6K TL/ay) | Gerekmez |
| Platform komisyonu | iyzico ~%3 | Apple/Google **%15** (Small Business / <$1M) |
| Aylık sabit yük | Muhasebeci + Bağ-Kur | Bağ-Kur |

**Mantık:** Erken/düşük ciro aşamasında (organik edinim hâlâ düşük — bkz.
[[acquisition-bottleneck]]) şirket + muhasebeci sabit yükü, kazançtan büyük olur.
Mobil-IAP operasyonel olarak çok daha basit ve tavana (2025: 4.3M TL) kadar
şirketsiz yürür. 1000 kullanıcıda denklem değişince şirkete geçilir.

> ⚠️ **Katil kural:** İstisna **yalnız App Store / Google Play üzerinden** elde
> edilen gelir için geçerli. **Web'den tahsilat yaparsak istisna o gelir için
> geçmez** → o yüzden web'de kasıtlı olarak hiç ödeme almıyoruz. Web = ücretsiz.

---

## 2. Birlikte alınan kararlar (bağlayıcı)

1. **Web'den ödeme YOK.** Web ücretsiz kalır (SEO/edinim hunisi). Tüm tahsilat mobil
   IAP.
2. **Entitlement hesaba bağlı, tek premium bayrağı.** Mobil IAP → RevenueCat webhook
   → backend `entitlements` (Clerk userId'ye bağlı). Premium'un nerede kullanıldığı
   istemci meselesi.
3. **v1 = öğrenci çekirdeği + çalışma kağıdı.** Öğretmen "Sınıfım" v2.
4. **Kalite > takvim.** Eylül baskısı hedef değil; "içimize sinen sağlam v1".
   Yetişirse ekstra özellik bonus; yetişmezse v2 (Ekim, dönem içi).
5. **Çekirdek içerik tam native.** WebView-wrapper reddedildi.
6. **Maskot:** mevcut tilki adapte edilir; kaliteli statik + **anahtar anlarda hafif
   Lottie** (doğru cevap, rozet) v1'de. Tam karakter animasyonu v2.
7. **Bireysel (şahıs) geliştirici hesabı** — şirketsiz istisna planıyla uyumlu.
8. **Monorepo** (tek gerçek kaynağı; zod şemaları/tipler/API client paylaşılır).
9. **Çalışma modeli:** Claude geliştirmenin çoğunu yürütür; kullanıcı orkestra +
   karar + cihaz testi + mağaza konsolları + zevk kararı.

---

## 3. Vergi & yasal model (GVK Mükerrer 20/B)

**Ne:** "Sosyal İçerik Üreticiliği ... ile Mobil Cihazlar İçin Uygulama
Geliştiriciliğinde Kazanç İstisnası" (GVK Mük. 20/B, 318 & 325 Seri No.lu Tebliğ).

**Şartlar:**
1. **Gerçek kişi** olmak (şirket değil).
2. Gelir **elektronik uygulama paylaşım/satış platformları** (App Store, Google Play)
   üzerinden gelmeli. Kapsam içi: **abonelik, uygulama içi satın alma, uygulama içi
   reklam**. Kapsam dışı: web sitesi gelirleri, freelance, danışmanlık.
3. Vergi dairesinden **"İstisna Belgesi"** alınır.
4. Türkiye'de bir bankada **özel hesap** açılır; **tüm kazanç bu hesaptan geçer**.
   Banka otomatik **%15 stopaj** keser (nihai vergi — yıllık beyan yok).
5. Yıllık hasılat tavanın altında kalmalı (**2025: 4.300.000 TL**; 2026 tavanı
   ~5,3-7M TL bandında, 4. vergi dilimine endeksli — **mali müşavire doğrulat**).
   Aşılırsa o yıl istisna düşer, normal beyan gerekir.

**KDV:** İstisna kapsamındaki gelir KDV'den muaf. Apple/Google, Türkiye'deki son
kullanıcıdan %20 KDV'yi **kendisi** tahsil edip GİB'e ayrı yatırır — biz taraf
değiliz, net tutar bize aktarılır.

**Bağ-Kur:** Yükümlülük var (2026'da ~9-10K TL/ay).

**Apple/Google ödemesi ↔ özel hesap:** App Store Connect / Play Console'daki banka
& vergi bilgisi, istisna belgesiyle açılan **özel hesaba** yönlendirilmeli. Bu
koordinasyon para akmadan önce tamam olmalı.

> **Aksiyon:** İstisna belgesi + özel banka hesabı = **bürokrasi hattı**, 1. gün
> başlatılır (kod beklemez). Kesin rakam/başvuru için mali müşavir.

---

## 4. Kapsam — v1

### İçeride (native, cilalı)
- **Maskotlu onboarding** — ilk izlenim, marka.
- **Giriş** (Clerk, aynı hesap web+mobil).
- **Çekirdek öğrenme döngüsü:** ders/konu seç → soru çöz (`/coz`) → maskot tepkili
  anlık geri bildirim → ilerleme kaydı.
- **Oyunlaştırma:** seri (streak), rozet; anahtar anlarda hafif Lottie.
- **Çalışma kağıdı üret → PDF → WhatsApp paylaş** (katil kullanım senaryosu).
- **Öğrenci ilerleme panosu** (kazanım-bazlı doğru/yanlış, trend).
- **Abonelik duvarı** (RevenueCat IAP; aylık + yıllık).

### Dışarıda (v2 kuyruğu)
- Öğretmen **"Sınıfım"** (sınıf yönetimi, ödev atama, sınıf istatistikleri) — web'de
  kalır; mobil aboneliği web'de bu özelliği açar.
- Fiyat kademesi (öğrenci vs öğretmen paketi).
- Offline mod (libSQL yerel replika — mimari buna açık kurulur).
- Push kampanyaları.
- Tam maskot karakter animasyonu / sesli rehber.

> **Apple güvenliği:** Mobil uygulama **kendi başına değerli** (soru çöz + çalışma
> kağıdı + ilerleme). Web-only öğretmen özelliği "üstüne bonus", ana satış gerekçesi
> değil → 3.1.3(b) multiplatform kuralına uygun (IAP'den al → başka platformda kullan
> = izinli yön).

---

## 5. Mimari

### 5.1 Paylaşılan vs native

```
                    ┌─────────────────────────────┐
                    │   Render Backend API         │
                    │   (FastAPI) — DEĞİŞMEZ       │
                    │   üretim, /coz, quiz, RAG,   │
                    │   PDF/SVG, subject_resolve,  │
                    │   critic, entitlements        │
                    └───────┬──────────────┬───────┘
                            │              │
                 ┌──────────┴───┐   ┌──────┴──────────┐
                 │  Web (Next)  │   │ Mobil (Expo/RN) │
                 │  = TÜM özell.│   │ = öğrenci çekir.│
                 │  ücretsiz    │   │ + IAP tahsilat  │
                 └──────────────┘   └─────────────────┘
                        └──────── Turso/libSQL ────────┘
                              (tek veri, tek hesap)
```

**%100 paylaşılan:** Backend API, Turso, Clerk kimliği, iş mantığı (curriculum,
RAG, few-shot, critic, PDF/SVG üretimi), entitlement kaydı.

**Native (yeni iş):** UI katmanı, IAP/RevenueCat, Clerk Expo entegrasyonu, PDF
indirme + native paylaşım, matematik native render, navigasyon, push, native
yetenekler, mağaza yayın hattı.

### 5.2 Entitlement akışı (kalbin kalbi)

```
Kullanıcı (mobil)                RevenueCat            Backend (Render)
    │  IAP satın al  ──────────────▶ │                       │
    │                                │  webhook (imzalı) ───▶ │  entitlements
    │                                │                       │  UPSERT
    │                                │                       │  (clerk_user_id,
    │◀──── premium aktif ────────────│                       │   plan, expires)
    │                                                        │
Web / Mobil herhangi istemci  ── GET /me/entitlements ──────▶│  premium: true/false
```

- **Tek premium bayrağı**, Clerk `userId`'ye bağlı. Web ve mobil aynı kaydı okur.
- **iyzico planıyla birleşme:** Aynı `entitlements` tablosu + aynı **Clerk
  sunucu-tarafı token doğrulama (P0)**. Mobil IAP, iyzico'nun kurduğu/kuracağı
  entitlement altyapısına oturur — ikinci bir abonelik durumu yönetmeyiz.
- **P0 önkoşul (iyzico planından devralınan):** Backend, entitlement kararı veren
  uçlarda Clerk oturum token'ını **sunucu-tarafı doğrulamalı** (JWKS ile). Aksi
  halde header değiştirip bedava premium olunur. Mobil için de zorunlu.
- **RevenueCat webhook** imza doğrulaması + idempotent upsert (tekrar teslimatlar).

---

## 6. Teknoloji stack'i (kalite öncelikli, web ile hizalı)

| Katman | Web (mevcut) | Mobil | Not |
|---|---|---|---|
| Framework | Next.js 15 / TS | **Expo (RN) + TypeScript** | Dev client (Expo Go değil); native modüle açık |
| Navigasyon | Next dosya-routing | **Expo Router** | Aynı zihin modeli |
| Kimlik | @clerk/nextjs v7 | **@clerk/clerk-expo** | Token expo-secure-store; deep-link config |
| Ödeme | (iyzico, sonra) | **RevenueCat** (react-native-purchases) | IAP + entitlement webhook |
| Stil | Tailwind + cva + shadcn | **NativeWind + cva** | Web design-system'ini aynalar |
| State | Zustand | **Zustand** | Aynısı |
| Form | react-hook-form + zod | **react-hook-form + zod** | zod şemaları monorepo'da paylaşılır |
| Veri | fetch | **TanStack Query** | Cache/loading/error/retry |
| İkon | lucide-react | **lucide-react-native** | Aynı set |
| **Matematik render** | react-markdown + rehype-katex | **native markdown + SVG matematik** | Backend MathJax/KaTeX → SVG; react-native-svg ile satır-içi. **WebView YOK** |
| Animasyon | tailwindcss-animate | **Reanimated + gesture-handler** + **Lottie** (lottie-react-native) | Mikro-hareket + anahtar-an animasyonu |
| Font | — | **expo-font** (Fredoka + Nunito) | Marka tutarlılığı |
| PDF | tarayıcı | **expo-file-system + expo-sharing** | İndir → native paylaş → WhatsApp |
| Build/Deploy | Vercel | **EAS Build + Submit + Update** | Mac gerekmez; EAS Update = JS düzeltmesi incelemesiz |
| Crash | — | **Sentry (sentry-expo)** | TestFlight'tan itibaren |
| Test | — | **Maestro E2E + RN Testing Library** | Kritik akışlar: giriş, satın alma, kağıt üretimi |

### 6.1 Matematik render kararı (tam native)

Web'deki `react-markdown + rehype-katex` DOM'a bağlı, RN'de çalışmaz. **Kalite
optimumu:**
- Markdown yapısı native render (`react-native-markdown-display` veya küçük özel).
- Matematik ifadeleri **backend'de MathJax/KaTeX ile SVG'ye** çevrilir; mobilde
  `react-native-svg` ile **native metinle satır-içi** dizilir.
- Kazanç: seçilebilir/temalanabilir/dinamik-boyutlu native metin + keskin,
  ölçeklenebilir, animasyonlanabilir matematik. Çekirdekte WebView yok.
- Bedel: backend ifade-başına SVG endpoint'i + native satır-içi kompozisyon.
  (Backend zaten SVG üretiyor; server-side KaTeX→SVG fizibil.)

> Web'deki [[ssr-dompurify-esm-landmine]] mobilde **yok** (SSR/DOM yok). (c) WebView
> yolu seçilmediği için sanitizasyon backend SVG üretiminde yapılır.

### 6.2 Monorepo (Turborepo)

```
soruatolyesi/
├── apps/
│   ├── web/        # mevcut Next.js (dikkatli taşınır — prod'u kırma)
│   └── mobile/     # yeni Expo
└── packages/
    └── shared/     # zod şemaları, tipler, API client, sabitler (curriculum/subject)
```

- zod şemaları paylaşılır → backend kontratları web+mobilde birebir eşleşir.
- **Risk:** canlı web'i monorepo'ya taşımak dikkat ister; ayrı bir hazırlık adımı
  (§8 Faz 0) olarak, prod doğrulamasıyla yapılır.

---

## 7. Çalışma modeli — iş bölümü

**Claude yürütür:** kod, mimari, config, debug, RevenueCat/Clerk/Expo entegrasyonu,
backend SVG pipeline, monorepo kurulumu, dokümantasyon, adım adım komutlar.

**Kullanıcı yürütür (irreducible):** ürün/zevk kararları, **cihazda test**, App Store
Connect / Play Console tıklama, **IAP sandbox** elle deneme, ekran görüntüsü yükleme,
Apple incelemesine anlık yanıt, görsel cila onayı.

**Ritim:** yoğun git-gel — Claude üretir → kullanıcı cihazda çalıştırır/bakar →
geri bildirim → Claude düzeltir. Görsel cila döngüsü kullanıcının gözünü ister.

---

## 8. Yol haritası (kalite-kapılı, takvim esnek)

> Tarihler **göstergesel**; kalite kapıları takvimin önünde. Eylül sonu = *arzu
> edilen yumuşak lansman hedefi*, sert son tarih değil. İki hat paralel yürür.

### Hat A — Bürokrasi/hesaplar (1. gün başlar, çoğu kullanıcı aksiyonu)
- [ ] Apple Developer **bireysel** kayıt ($99/yıl) — kimlik doğrulama günler-haftalar
- [ ] Google Play Console ($25 tek sefer)
- [ ] **İstisna belgesi** (vergi dairesi) + **özel banka hesabı**
- [ ] Apple/Google ödemesini özel hesaba yönlendir (Connect/Console banka+vergi)
- [ ] Gizlilik politikası sayfası (web) + **uygulama içi hesap silme** (Apple zorunlu)

### Hat B — Geliştirme (faz-bazlı)

| Faz | İçerik | Kalite kapısı |
|---|---|---|
| **Faz 0 — Temel** | Monorepo kurulumu (web dikkatli taşınır) + `packages/shared` + Expo iskelet + EAS + Clerk giriş + API bağlantısı | Telefonda giriş + API'ye vuruş; web prod bozulmadı |
| **Faz 1 — Tasarım sistemi** | Token'lar (renk/tipografi/boşluk/radius), çekirdek bileşenler (Button/Card/Input), **maskot bileşeni + pozlar + hafif Lottie'ler** | Figma → kod; tutarlı, markalı bileşen kütüphanesi |
| **Faz 2 — Çalışma kağıdı dilimi** | Kağıt üret ekranı → backend → PDF → **WhatsApp paylaş** | İlk **oynanabilir build**; sıcak lead'lere TestFlight |
| **Faz 3 — Öğrenme döngüsü** | Ders/konu seç + **soru çözme** (native markdown + SVG matematik) + maskotlu geri bildirim + ilerleme kaydı | Çekirdek döngü native ve akıcı |
| **Faz 4 — Oyunlaştırma + pano** | Seri/rozet + anahtar-an Lottie + öğrenci ilerleme panosu + döngü hissi cila | 2. TestFlight (dolu deneyim) |
| **Faz 5 — Ödeme** | RevenueCat + paywall + backend entitlement webhook + web premium okuması + **Clerk P0 doğrulama** + sandbox | Abonelik uçtan uca; mobil→web premium doğrulandı |
| **Faz 6 — Cila + sertleştirme** | Hata/boş/yükleniyor durumları, erişilebilirlik (dinamik yazı, ekran okuyucu), hesap silme, gizlilik etiketi, Sentry, Maestro E2E, mağaza görselleri | "İçimize sinen" kalite çıtası; testler yeşil |
| **Faz 7 — Yayın** | Final QA → Apple + Google submit → ret düzeltme döngüsü → yumuşak → halka açık lansman | Yayında; prod'da IAP çalışıyor |

> **Erken kullanıcı = TestFlight** (review/IAP gerektirmez). Faz 2 sonunda sıcak
> lead'lere verilir → erken geri bildirim + beklenti, mağaza tabanına takılmadan.

---

## 9. Riskler & aksilikler (en olasıdan)

1. 🔴 **Bürokrasi hattı kritik yol.** Apple kaydı / istisna belgesi / banka; dev'i
   değil **submit'i** bloklar → 1. gün başlat.
2. 🔴 **IAP sandbox** en çok debug yiyen yer (restore, abonelik durumları) →
   RevenueCat yükü alır, yine de Faz 5 tek başına.
3. 🟠 **Apple 4.2 reddi** ("bu bir web sitesi"). Panzehir: tam native + gerçek
   özellikler (push, native paylaşım, IAP, native nav). WebView reddedildiği için
   risk düşük ama sıfır değil.
4. 🟠 **Clerk Expo oturum/deep-link** config (OAuth redirect, e-posta doğrulama geri
   dönüşü) — ilk-kez tuzağı.
5. 🟠 **Monorepo migrasyonu canlı web'i kırabilir** → Faz 0'da prod doğrulamasıyla,
   geri-alınabilir adımlarla.
6. 🟡 **Çalışma modeli gecikmesi** (kod→cihaz test→düzelt round-trip). Kalite-first
   olduğumuz için tolere edilir.
7. 🟡 **Sertifika/imzalama** — EAS managed credentials çoğunu halleder.
8. 🟡 **Windows'ta Mac yok** — EAS bulut build çözer; iOS testi için gerçek iPhone
   (kendi/arkadaş) + IAP sandbox gerekir.
9. 🟡 **Gizlilik zorunlulukları** — App Privacy etiketi, veri toplama beyanı (Clerk),
   uygulama içi hesap silme.
10. 🟡 **Yayın sonrası native güncelleme gecikmesi** — EAS Update JS düzeltmelerini
    incelemesiz iter (native değişiklik review ister).

---

## 10. Maliyet (nakit)

| Kalem | Tutar |
|---|---|
| Apple Developer | $99/yıl (~3.300 TL) |
| Google Play | $25 tek sefer (~830 TL) |
| RevenueCat | ~$2.5K/ay gelire kadar ücretsiz, sonra %1 |
| EAS | Ücretsiz kademe başlangıç için yeterli; gerekirse ~$99/ay |
| Maskot | Mevcut tilki adapte ≈ 0; poz seti çizdirilirse birkaç bin TL |
| **Başlangıç nakit** | **~5-6K TL** + geliştirme zamanı |

Asıl maliyet nakit değil, geliştirme zamanı ve öğrenme eğrisi.

---

## 11. Açık işler / önkoşullar

> **Kod tabanı denetimi (2026-07-21):** Backend'in "Hat A" önkoşullarının **çoğu
> iyzico hazırlığında ZATEN yapılmış** — yeniden yazılmayacak. Aşağıda gerçek durum.

**Backend — HAZIR (yeniden kullanılacak):**
- ✅ Clerk sunucu-tarafı token doğrulama (P0) — `app/services/clerk_auth.py` tam
  (JWKS, strict/lenient dependency, `resolve_tenant_id` spoof koruması).
  `clerk_auth_enabled` bayrağı arkasında.
- ✅ `entitlements.py` — plan kararı (free/trial/pro/pro-plus) + kota + trial.
- ✅ `billing_store.py` — `subscriptions` + `billing_events` (idempotency). `provider`
  alanı sağlayıcı-bağımsız → **RevenueCat `provider='revenuecat'` ile aynı depoyu
  kullanır**, ayrı şema gerekmez.
- ✅ `/api/me/*` uçları (progress, gamification, attempts, quizzes…) Clerk-korumalı,
  mobil bunları AYNEN tüketir.

**Backend — GERÇEKTEN yeni iş (Faz 5, mağaza ürünleri gelince/28+):**
- [ ] **RevenueCat webhook alıcısı** (yeni `app/routers/billing.py`): imza doğrula →
      RevenueCat olayını `billing_store.upsert(provider='revenuecat', …)` ile eşle
      (`record_event` idempotency mevcut). Olay→durum eşlemesi (INITIAL_PURCHASE/
      RENEWAL→active, CANCELLATION→cancel, EXPIRATION→expired, BILLING_ISSUE→past_due).
- [ ] **`/api/me/entitlements` okuma ucu** — `plan_of` + kota; web+mobil ortak premium
      durumu. (Mobil ayrıca RevenueCat SDK'sından da entitlement alır.)
- [ ] **Matematik → SVG** (Faz 3): `math_renderer.render_latex_to_png` matplotlib
      kullanıyor → `savefig(format="svg")` ile **SVG varyantı eklemek trivial**.
      (MathJax/KaTeX server-side gerekmez; mevcut altyapı yeter.) SVG blokları +
      `{{chart/pattern/table}}` direktifleri zaten SVG üretiyor → mobil `react-native-svg`
      ile doğrudan gösterir.

**Diğer:**
- [~] Mali müşavir / istisna belgesi başvurusu — **başvuruldu (2026-07-20)**; onay bekliyor.
- [ ] Apple + Google hesap başvurusu — **28 Temmuz'da** (ödeme o zaman).
- [ ] Tasarım: maskot poz seti + hafif Lottie'ler (Figma).
- [ ] Karar (v2): fiyat kademeleri, offline-first (libSQL yerel replika).

---

## 12. UX & Tasarım İlkeleri (2026-07-22 eklendi)

Dış bir öneri listesinden, uygulamamıza uyanlar süzülerek alındı. İlke: *önce
problemi/akışı çöz, ekranı değil.*

### Bağlayıcı karar
- **İki ayrı birinci-sınıf akış korunur — teke DÜŞÜRÜLMEZ:**
  1. **Çalışma Kağıdı Üret** (üret → PDF → WhatsApp paylaş) — yazdır/paylaş senaryosu.
  2. **Çöz / Geliş döngüsü** (alıştırma çöz → puanla → eksik kazanım → eksiğe özel yeni test).
  Rehberli huni bunları BİRLEŞTİRMEZ; her biri kendi sekmesi/akışı.

### Uygulanacak ilkeler
- **Tek ekran = tek amaç, az seçenek.** Mevcut worksheet/practice ekranları tüm
  seçicileri (ders/sınıf/ünite/zorluk/adet) aynı anda gösteriyor → **adımlı huniye**
  çevrilecek: "Bugün ne çalışacaksın?" → ders → sınıf → konu → (üret | çöz) → sonuç →
  (döngüde) eksiğe özel yeni test.
- **Alt sekme navigasyonu** (başparmak ergonomisi), her iki akış ayrı:
  🏠 Ana · 📄 Kağıt · ✏️ Çöz · 📈 Gelişim · 👤 Profil.
- **Karanlık mod baştan** — token'lar tema-duyarlı (ışık/koyu) kurulacak (sonradan
  eklemek pahalı).
- **Skeleton yükleyiciler** (spinner yerine) — çalışıyor hissi.
- **Yardımcı/aksiyonlu hata mesajları** ("İnternet yok — tekrar dene").
- **Dokunma hedefi** ≥ 44×44pt (iOS) / 48×48dp (Android); **8px grid** disiplini.
- **Ödül/geri bildirim** yüzeyde (XP/seri/kazanım kartı — mevcut, öne çıkarılacak).
- **Kısa giriş** — e-posta+kod (mevcut); ilerde Google/Apple OAuth.
- **AI görünmez yardımcı** — kullanıcı "modeli" değil "sonucu" ister (mevcut yaklaşım).

### Öncelik
- **Ucuz/hemen:** karanlık mod token'ları · skeleton · hata mesajları · dokunma hedefi.
- **Odaklı pass:** rehberli huni + alt sekme navigasyonu (mevcut ekranların akış/nav
  yeniden düzeni; mantık/API aynı kalır).
- **Sonra:** performans (TanStack Query cache, lazy load), erişilebilirlik cilası.

---

*Bu belge birlikte alınan kararların kaynağıdır; kapsam/karar değişirse burası
güncellenir.*
