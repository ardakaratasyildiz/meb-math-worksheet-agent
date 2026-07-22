# 28 Temmuz — EAS Dev Build Hazırlık & Gün Planı

**Amaç:** O gün sürpriz olmasın. Mobil (`apps/mobile`, `feat/mobile-foundation`) için
ilk **dev build**'i alıp `pk_live`'a geçmek → şu an Expo Go'da 401 veren
**korumalı uçları** (alıştırma sonucu kaydı / ilerleme / gamification / rol-set /
deneme geçmişi) tek seferde açmak + IAP testine kapı aralamak.

> Not: `apps/mobile/AGENTS.md` "v57 docs oku" diyor. **Kod yazmadan önce**
> https://docs.expo.dev/versions/latest/ (EAS Build) sürüm notlarını teyit et.

---

## 0) EN KRİTİK KARAR — SDK 54 mi, 57 mi? → **Önce 54**

Handoff "SDK 57 + pk_live birlikte" diyordu. **Öneri: bunları AYIR.**

- Dev build'in değeri (pk_live, korumalı uçlar, IAP) **SDK sürümünden BAĞIMSIZ.**
- SDK 54 şu an çalışıyor (tsc + `expo export` yeşil, cihazda Expo Go ile test edildi).
- SDK 54→57 = ~15 expo paketi + React Native sürüm zıplaması + React 19.1 override +
  reactCompiler yeniden açma + kırıcı değişiklikler → **riskli, ayrı ve acelesiz pass.**

**Karar:** İlk dev build'i **SDK 54 üzerinde** al → her şeyi çalıştır (pk_live +
korumalı uçlar + IAP smoke) → **SONRA** SDK 57 yükseltmesini ayrı yap (§7).
Böylece 28 Tem'de tek değişken var (dev build + pk_live), iki riskli iş üst üste binmez.

---

## 1) Ön-koşullar (hesaplar — İRREDUCIBLE, kullanıcı yapar)

| Hesap | Maliyet | Ne için | Zorunlu mu |
|---|---|---|---|
| **Apple Developer** | $99/yıl | iOS dev build (cihaz provizyon, imzalama) | iOS için **ŞART** |
| **Google Play Developer** | $25 (tek sefer) | Play Store yayını | Dev APK için **GEREKMEZ** (sonra) |
| **Expo (EAS)** | Ücretsiz | EAS build sunucusu | **ŞART** (ücretsiz katman yeter) |

- **Android dev build APK** için Apple/Google gerekmez — ücretsiz Expo hesabı + EAS yeter.
  Android'i **önce** deneyebiliriz (Apple hesabı beklerken hızlı doğrulama).
- iOS için Apple hesabı + (fiziksel cihaz UDID veya EAS'ın internal dağıtımı).

---

## 2) Ortam değişkenleri stratejisi (kritik — yanlışı beyaz ekran/401 yapar)

`apps/mobile/.env` **gitignore'lu** → EAS build sunucusu onu GÖRMEZ.

- **Dev-client (development profili):** cihazdaki kabuk, çalışma anında JS'i **yerel
  Metro**'dan yükler (`expo start --dev-client`). Env = **yerel `.env`** (Metro okur).
  → 28 Tem'de yapılacak: yerel `.env`'de `EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY`'i
  **pk_live** yap, `expo start --dev-client` çalıştır. pk_live dev build'de ÇALIŞIR
  (standalone; Expo Go'da çalışmıyordu — fark bu).
- **Embedded build (preview/production):** JS gömülür → env **build anında** okunur →
  yerel `.env` görünmez. Bu profillerde env'i **eas.json `env`** bloğuna veya
  **EAS environment variables**'a (`eas env:create`) koy.

**Değerler (hepsi EXPO_PUBLIC = public, bundle'a gömülür — sır değil):**
- `EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY` = `pk_live_Y2xlcmsuc29ydWF0b2x5ZXNpLmNvbSQ` (prod Clerk)
- `EXPO_PUBLIC_API_URL` = `https://api.soruatolyesi.com`
- `EXPO_PUBLIC_API_KEY` = web'deki `NEXT_PUBLIC_API_KEY` ile aynı (public)

> pk_test (dev instance `awaited-leech-99`) yalnız Expo Go içindi; dev build'de pk_live'a geçilir.

---

## 3) Adım adım (dev build günü)

```bash
# PATH (bu makinede Node taşınabilir kurulu):
export PATH="/c/Users/arda.karatas/AppData/Local/Programs/nodejs:$PATH"
cd apps/mobile

# 0. EAS CLI + giriş
npm i -g eas-cli          # veya: npx eas-cli@latest
eas login                 # Expo hesabı
eas whoami                # doğrula

# 1. Proje EAS'a bağla (ilk sefer projectId yazar app.json/extra'ya)
eas init                  # veya build:configure (eas.json zaten var)

# 2. ANDROID dev build (Apple beklemeden hızlı doğrulama) — APK
eas build --profile development --platform android
#   → tamamlanınca QR/link ile cihaza APK kur

# 3. iOS dev build (Apple Developer hesabı + cihaz gerektirir)
eas build --profile development --platform ios
#   → Apple girişini ister, provizyonu EAS halleder, cihaza kur

# 4. Yerel .env → pk_live yap (§2), sonra dev sunucu:
npx expo start --dev-client
#   → cihazdaki dev build'i aynı ağdaki Metro'ya bağla (Expo Go DEĞİL)
```

---

## 4) Doğrulama (dev build cihazda açılınca)

1. **Giriş** (pk_live → prod Clerk). E-posta + 2FA akışı (sign-in-form.tsx) çalışmalı.
2. **RoleGate** → rol seç → backend `POST /api/me/role` artık **200** (dev'de 401'di).
3. **Korumalı uçlar** — bir alıştırma çöz → sonuç kaydı, `/api/me/progress`,
   `/api/me/gamification`, `/api/me/attempts` (Gelişim + Deneme Geçmişi) **veri döner**.
4. **Worksheet** üret → PDF paylaş (zaten çalışıyordu; regresyon olmasın).

---

## 5) İkon & splash markalama (şu an placeholder)

- `app.json`: `icon` = Expo default (`icon.png`), `ios.icon` = `expo.icon/` (default),
  splash = `splash-icon.png` + mavi `#208AEF`. **Derlenen app Expo default ikonu taşır.**
- Gerekli: **1024×1024 KARE, dolu-zemin** maskot app ikonu (App Store şeffaflık kabul etmez;
  iOS köşeleri kendi yuvarlar). `fox_assets/icon1-4` sadece ~220px → yetersiz.
- **Aksiyon:** yüksek-çöz kare maskot ikonu üretilince `app.json`'a bağla. Dev build'i
  **bloklamaz** (placeholder ile de build alınır), ama store'dan önce şart.

---

## 6) Riskler & geri dönüş

- **iOS provizyon takılırsa:** önce Android APK ile akışı doğrula (Apple'dan bağımsız).
- **pk_live beyaz ekran:** yalnız Expo Go'da olur; dev build'de olmamalı. Olursa
  `lib/clerk-reset.ts` ile client state temizle + yeniden başlat.
- **Env boş (401/boş ekran):** §2 — dev-client'ta yerel `.env` pk_live mı, Metro yeniden
  başladı mı kontrol et.
- **Geri dönüş:** SDK 54 dalı sağlam; dev build başarısızsa Expo Go + pk_test akışına dönülür.

---

## 7) SDK 54 → 57 geçişi (AYRI, sonraki pass — 28 Tem'e sokma)

Dev build 54'te çalıştıktan SONRA, acelesiz:
1. `npx expo install expo@^57` → `npx expo install --fix` (tüm expo-* hizala).
2. React Native + React sürümlerini SDK 57 matrisine getir; kök `overrides` (React 19.x
   tek kopya) gözden geçir; **reactCompiler**'ı yeniden açmayı değerlendir (kapalıydı).
3. Kırıcı değişiklikler: expo-router / reanimated / clerk-expo sürüm notları.
4. Her adımda `npx tsc --noEmit` + `npx expo export` + cihazda dev-client testi.
5. Yeşilse dev build'i 57 ile yeniden al.

---

## 8) IAP / RevenueCat (downstream — dev build sonrası)

- Store hesapları açılınca: RevenueCat projesi + ürün (abonelik) tanımı.
- Backend `billing_store.py` provider-agnostik hazır → RevenueCat **webhook alıcısı** +
  `/api/me/entitlements` ucu yazılır (backend Faz 5). Entitlement Clerk userId'ye bağlı
  (iyzico ile ortak).
- `react-native-purchases` (RevenueCat SDK) mobile eklenir; dev build'de sandbox test.
