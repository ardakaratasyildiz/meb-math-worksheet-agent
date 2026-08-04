# Mobil — Mağaza Hazırlık Koşu Kitabı

Kapsam: `apps/mobile` için **EAS ortam değişkenleri**, **ikon/splash markalama** ve
**RevenueCat satın-alma** kurulumu. Dev build günü notları için bkz.
[MOBIL_28TEM_HAZIRLIK.md](./MOBIL_28TEM_HAZIRLIK.md).

Neden gerekli: dev-client build'i JS'i yerel Metro'dan alır ve `.env` dosyasını okur;
**preview/production build'lerde JS gömülüdür**, `.env` derleme sunucusunda yoktur →
değişkenler boş kalır → Clerk açılmaz (beyaz ekran) ve API çağrıları 401 döner.

---

## 1) EAS ortam değişkenleri

`eas.json`'daki her profil artık bir ortam seçiyor:
`development → development`, `preview → preview`, `production → production`.
Değerler EAS sunucusunda tutulur (repo **public** olduğu için git'e YAZILMAZ).

```bash
export PATH="/c/Users/arda.karatas/AppData/Local/Programs/nodejs:$PATH"
cd apps/mobile
eas login && eas whoami

# --- production + preview (ikisine de aynı değerler) ---
for ENV in production preview; do
  eas env:set --name EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY \
    --value pk_live_Y2xlcmsuc29ydWF0b2x5ZXNpLmNvbSQ \
    --environment $ENV --visibility plaintext --non-interactive

  eas env:set --name EXPO_PUBLIC_API_URL \
    --value https://api.soruatolyesi.com \
    --environment $ENV --visibility plaintext --non-interactive

  # Değer = web'deki NEXT_PUBLIC_API_KEY ile aynı (yerel apps/mobile/.env'de var).
  eas env:set --name EXPO_PUBLIC_API_KEY \
    --value "<NEXT_PUBLIC_API_KEY>" \
    --environment $ENV --visibility sensitive --non-interactive
done

eas env:list --environment production   # doğrula
```

> `--visibility`: `plaintext` (panoda/loglarda görünür) · `sensitive` (loglarda maskelenir)
> · `secret` (EAS dışına hiç okunmaz — build sırasında da okunamaz, EXPO_PUBLIC_* için KULLANMA).

RevenueCat anahtarları §3'te, aynı kalıpla eklenir.

Yerel geliştirme değişmedi: `apps/mobile/.env` (gitignore'lu) Metro tarafından okunur.
İstersen EAS'takini yerele çekebilirsin: `eas env:pull --environment development`.

---

## 2) İkon & splash

**Tek doğruluk kaynağı:** `apps/mobile/assets/brand/icon-source.png` — maskot tilkinin
kare ikon kompozisyonu. Türevler elle düzenlenmez, betikle üretilir:

```bash
python scripts/make_mobile_icons.py                       # mevcut kaynaktan yenile
python scripts/make_mobile_icons.py /yol/yeni-ikon.png    # kaynağı değiştir (brand/ altına kopyalar)
```

| Üretilen dosya | Boyut | Kullanım |
|---|---|---|
| `assets/images/icon.png` | 1024×1024, saydamsız | Ana ikon (iOS + Android legacy) |
| `assets/images/android-icon-foreground.png` | 1024×1024, saydam | Android adaptive ön katman (mark %60) |
| `assets/images/android-icon-monochrome.png` | 1024×1024, saydam | Android 13+ temalı ikon (siluet) |
| `assets/images/splash-icon.png` | 1024×1024, saydam | Açılış ekranı markı |

Betiğin kaynak görselde temizlediği şeyler (üretilen görseller genelde "sunum" formatında gelir):
- **beyaz kenar boşluğu + gölge** → kenardan flood-fill ile ayrılır (gözler/krem tüy gibi
  iç beyazlar korunur, çünkü dış bölgeye bağlı değiller);
- **önceden yuvarlatılmış köşe** → köşe boşluğu çekirdek renkle doldurulur. Şart: iOS ikonu
  kare ve **saydam piksel içermez**, köşeleri işletim sistemi yuvarlar. Beyaz köşe bırakılırsa
  Play Store liste ikonunda ve kare gösteren launcher'larda beyaz üçgenler görünür;
- **sahte 3B kenar parlaması** → aşındırılır; OS kendi maskesini ve gölgesini uygular,
  içeri çizilmiş ikinci bir squircle kenarı bozuk görünür.

`app.json` tarafı:
- `ios.icon` **kaldırıldı** → tek `icon` alanına düşer. (Eskiden Expo'nun default
  `assets/expo.icon` klasörünü gösteriyordu; derlenen uygulama Expo ikonu taşıyordu.)
- Android adaptive: ön katman saydam, arka plan düz `backgroundColor` (`#2679E7` = kaynak
  zeminin ortalaması; betik çalışınca bu değeri yazdırır). Maske ön katmanın **dış %33'ünü
  kırpar** → mark merkezde ~%60 alanda durur. `backgroundImage` referansı kaldırıldı.
- Splash: saydam mark + `imageWidth: 220` (eskiden 76 = Expo default logo boyutu).

Artık kullanılmayan Expo şablon dosyaları: `assets/expo.icon/`,
`assets/images/android-icon-background.png` (silinebilir, referans yok).

**İhracat şifreleme beyanı:** `ios.infoPlist.ITSAppUsesNonExemptEncryption: false` eklendi.
Uygulama yalnız standart HTTPS kullanıyor (ABD ihracat muafiyeti kapsamında) — bu alan
olmadan her TestFlight/App Store yüklemesi "Missing Compliance" durumunda takılır ve
elle cevaplanması gerekir.

---

## 3) RevenueCat (mobil satın-alma)

Kod tarafı hazır: `apps/mobile/src/lib/purchases.ts` (guard'lı sarmalayıcı) +
`app/paywall.tsx` + backend `app/routers/billing.py` webhook alıcısı.
Eksik olan yalnız **hesap/ürün kurulumu ve anahtarlar**.

### 3.1 Ön koşullar
- Apple Developer ($99/yıl) — iOS ürünleri ve TestFlight için şart.
- Google Play Developer ($25, tek sefer) — Android ürünleri için şart.
- RevenueCat hesabı (ücretsiz katman yeterli).

### 3.2 Mağaza ürünleri (kimlikler kodda sabit — birebir aynı olmalı)

`apps/mobile/src/app/paywall.tsx` şu SKU'ları bekler:

| Ürün kimliği | Tür | Fiyat (docs/MONETIZATION_PLAN.md) |
|---|---|---|
| `pro-aylik` | Abonelik (aylık) | ₺199 / 50 kağıt |
| `proplus-aylik` | Abonelik (aylık) | ₺349 / 120 kağıt |
| `topup-25` | Tek seferlik (tüketilebilir) | ₺89 / +25 kağıt, 30 gün |
| `topup-75` | Tek seferlik (tüketilebilir) | ₺199 / +75 kağıt, 30 gün |

App Store Connect ve Play Console'da **aynı kimliklerle** oluştur.

### 3.3 RevenueCat panosu
1. Project oluştur → iOS ve Android app'lerini ekle (bundle/package: `com.soruatolyesi.app`).
2. Products: yukarıdaki 4 ürünü içeri aktar.
3. Entitlements: `pro` ve `pro-plus` oluştur; `pro-aylik → pro`, `proplus-aylik → pro-plus`.
4. Offerings: bir `default` offering + paketleri bağla (paywall fiyatları buradan okur).
5. API keys → **public SDK key**'leri kopyala (`appl_...` / `goog_...`).

### 3.4 Anahtarları EAS'e yaz
```bash
for ENV in production preview; do
  eas env:set --name EXPO_PUBLIC_REVENUECAT_IOS_KEY --value appl_xxx \
    --environment $ENV --visibility sensitive --non-interactive
  eas env:set --name EXPO_PUBLIC_REVENUECAT_ANDROID_KEY --value goog_xxx \
    --environment $ENV --visibility sensitive --non-interactive
done
```
Yerelde test için aynı iki satırı `apps/mobile/.env`'e de yaz.
Anahtar dolunca `purchasesSupported()` true olur ve paywall "yakında" modundan çıkar.

### 3.5 Webhook (backend) — GÜVENLİK KAPISI
`app/routers/billing.py:32` — `REVENUECAT_WEBHOOK_AUTH` **boşsa doğrulama atlanıyor**
(sadece uyarı logluyor), yani uç herkese açık. Ödeme açılmadan ÖNCE Render'da set et:

| Render env | Değer |
|---|---|
| `REVENUECAT_WEBHOOK_AUTH` | Rastgele uzun sır — RevenueCat webhook ayarındaki `Authorization` başlığıyla **birebir aynı** |
| `REVENUECAT_PRODUCT_MAP` | `pro-aylik:pro,proplus-aylik:pro-plus` |

RevenueCat → Integrations → Webhooks → URL `https://api.soruatolyesi.com/api/billing/revenuecat/webhook`,
Authorization header = yukarıdaki sır.

`app_user_id` = Clerk userId olarak gönderilir (`configurePurchases(appUserID)`), backend
bunu `tenant_id` ile eşler → abonelik iyzico ile ortak depoya yazılır.

---

## 4) Hesap silme (Apple 5.1.1(v) / Play veri-silme)

Üye olunabilen her uygulamada **uygulama içi** hesap silme zorunlu; yoksa inceleme reddeder.

- Uç: `POST /api/me/account/delete`, gövde `{"confirm": "HESABIMI SIL"}`, strict Clerk
  oturumu (client `tenant_id`'si hiç okunmaz). Yerel veri silinir → sonra Clerk kullanıcısı
  kapatılır. Ön koşul: Render'da **`CLERK_SECRET_KEY` set** olmalı, aksi halde uç 503 döner.
- Mobil yol: Profil → Ayarlar → "Hesabımı sil" (`app/delete-account.tsx`).
- Play konsoluna verilecek **veri silme URL'si**: `https://soruatolyesi.com/hesap/sil`
  (oturumsuz da açılır — Play'in gereği bu).
- `usage_ledger` ve `billing_events` silinmez, `tenant_id` geri döndürülemez takma adla
  değiştirilir (VUK saklama). Play "Veri güvenliği" formunda bunu "silme talebi üzerine
  veriler silinir, muhasebe kayıtları anonimleştirilerek saklanır" olarak beyan et.

---

## 5) Çıkmadan önce doğrulama

- [ ] `eas env:list --environment production` üç EXPO_PUBLIC değişkeni gösteriyor.
- [ ] `eas build --profile preview --platform android` → kurulan APK'da **giriş çalışıyor**
      (beyaz ekran yok = Clerk anahtarı build'e girmiş) ve kağıt üretiliyor (API key doğru).
- [ ] Cihazda ikon **maskot** (Expo default "A" değil), açılış ekranı marka renginde.
- [ ] Sandbox hesabıyla `pro-aylik` satın alınıyor → RevenueCat panosunda olay görünüyor →
      `/api/me/entitlements` `plan: pro` dönüyor.
- [ ] `REVENUECAT_WEBHOOK_AUTH` set (yanlış header ile istek 401 alıyor).
- [ ] Render'da `CLERK_SECRET_KEY` set → test hesabıyla Profil → "Hesabımı sil" akışı
      hesabı gerçekten kapatıyor (aynı e-postayla yeniden kayıt olunabiliyor).
