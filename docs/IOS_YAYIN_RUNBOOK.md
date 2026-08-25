# iOS — Yayın Koşu Kitabı (App Store)

`apps/mobile` için App Store Connect kurulumu, abonelik ürünleri, TestFlight ve
inceleme başvurusu. Android karşılığı: [PLAY_YAYIN_RUNBOOK.md](./PLAY_YAYIN_RUNBOOK.md).
RevenueCat/EAS ortak adımları: [MOBIL_STORE_HAZIRLIK.md](./MOBIL_STORE_HAZIRLIK.md).

Sabitler (kodda tanımlı, değiştirilmez):

| Ne | Değer |
|---|---|
| Paket kimliği | `com.soruatolyesi.app` |
| Abonelikler | `pro-aylik` (₺199/ay) · `proplus-aylik` (₺349/ay) |
| Ek paketler | `topup-25` · `topup-75` — **ilk turda AÇILMAZ** |
| Cihaz desteği | Yalnız iPhone (`ios.supportsTablet` tanımlı değil) → iPad ekran görüntüsü gerekmez |

---

## 0) Ön koşul: tacir doğrulaması + sözleşme

App Store Connect → İş (Business) → Anlaşmalar, Vergi ve Bankacılık.

1. **Tacir Durumu (Trader Status)** "In Review" ise beklenir; Apple adres/telefon
   doğrulaması isteyebilir (e-postayı takip et). Bir haftayı geçerse Developer
   Support'a bilet aç.
2. Doğrulama bitince **Ücretli Uygulamalar** sözleşmesinde "İncele/Kabul et" düğmesi
   belirir → kabul et.
3. Üç bölümü doldur: **İletişim** (bireyselsen hepsi sen) · **Banka** (TRY IBAN, hesap
   sahibi adı Apple hesabındaki yasal adla birebir aynı) · **Vergi** (W-8BEN; TC kimlik
   yabancı vergi numarası olarak, anlaşma avantajında Türkiye seçilir).

Durum **Active** olmadan abonelik ürünü oluşturulamaz ve sandbox satın alma çalışmaz.

---

## 1) Bundle kimliği

developer.apple.com/account → Identifiers → `+` → App IDs → App → **Explicit** →
`com.soruatolyesi.app`. In-App Purchase yeteneği varsayılan açık gelir.

(EAS ilk build'de otomatik da oluşturabilir; elle yapmak daha öngörülebilir.)

---

## 2) App Store Connect'te uygulama kaydı

Uygulamalar → `+` → Yeni Uygulama:

| Alan | Değer |
|---|---|
| Platform | iOS |
| Ad | Soru Atölyesi (App Store genelinde benzersiz olmalı) |
| Birincil dil | Türkçe |
| Paket kimliği | `com.soruatolyesi.app` |
| SKU | serbest, ör. `soruatolyesi-ios-001` |
| Kullanıcı erişimi | Tam Erişim |

Kayıttan sonra **Apple ID (ascAppId)** görünür — 10 haneli sayı. Bu değer + **Team ID**
(developer.apple.com → Membership) `eas.json` submit bloğu için gerekli, bana ilet.

---

## 3) Abonelik ürünleri

Uygulama → Para Kazanma → **Abonelikler**.

1. **Abonelik grubu** oluştur: ör. "Soru Atölyesi Üyelik". İkisi de AYNI grupta olmalı →
   kullanıcı Pro ↔ Pro+ geçişi yapabilir, iki ayrı abonelik ödemez.
2. Gruba iki abonelik ekle:

| Referans adı | Ürün kimliği | Süre | Fiyat |
|---|---|---|---|
| Pro Aylık | `pro-aylik` | 1 ay | ₺199 |
| Pro+ Aylık | `proplus-aylik` | 1 ay | ₺349 |

3. Her ürün için **yerelleştirme** (görünen ad + açıklama) gir.
4. Grup içinde **seviye**: Pro+ üstte, Pro altta (yükseltme/düşürme davranışı).
5. **Tanıtım teklifi / ücretsiz deneme EKLEME** — deneme bizim tarafımızda, kartsız
   (7 gün / 20 kağıt, sunucuda). Mağaza denemesi kart ister ve iptal/iade sürtünmesi getirir.
6. Her ürüne **inceleme ekran görüntüsü** ve inceleme notu gerekir (ilk gönderimde şart).

> Sandbox testi için ürünlerin "Gönderilmeye Hazır" olması yeterli; incelemeye
> sunulmaları gerekmez. Ama **ilk yayında abonelikler bir uygulama sürümüyle BİRLİKTE
> gönderilir** — tek başına onaylanmazlar.

---

## 4) RevenueCat anahtarları

1. App Store Connect → Kullanıcılar ve Erişim → **Entegrasyonlar** → Uygulama İçi Satın
   Alma → anahtar üret → **`.p8` indir** (tek seferlik!). Key ID + Issuer ID'yi not al.
2. Uygulama → Genel → Uygulama Bilgileri → **Uygulamaya Özel Paylaşılan Sır** üret, sakla.
3. RevenueCat: proje → iOS uygulaması (`com.soruatolyesi.app`) → `.p8` + sır yükle →
   ürünleri içe aktar → entitlement `pro` / `pro-plus` → offering `default`.
4. RevenueCat → API keys → **public SDK key** (`appl_...`) → EAS'e ve yerel `.env`'e yazılır.

`.p8` ve paylaşılan sır **paylaşılmaz**; doğrudan RevenueCat paneline yüklenir.

---

## 5) Sandbox test hesabı

Kullanıcılar ve Erişim → **Sandbox** → Test Hesapları → `+`.
- Mevcut bir Apple Kimliği OLMAYAN e-posta (takma adres: `adresin+sandbox@gmail.com`).
- Ülke: Türkiye.
- Cihazda: Ayarlar → Geliştirici → **Sandbox Apple Hesabı** ile giriş.

---

## 6) EAS ortam değişkenleri + build

```bash
export PATH="/c/Users/arda.karatas/AppData/Local/Programs/nodejs:$PATH"
cd apps/mobile
eas login

for ENV in production preview; do
  eas env:set --name EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY \
    --value pk_live_Y2xlcmsuc29ydWF0b2x5ZXNpLmNvbSQ --environment $ENV \
    --visibility plaintext --non-interactive
  eas env:set --name EXPO_PUBLIC_API_URL --value https://api.soruatolyesi.com \
    --environment $ENV --visibility plaintext --non-interactive
  eas env:set --name EXPO_PUBLIC_API_KEY --value "<yerel .env'deki değer>" \
    --environment $ENV --visibility sensitive --non-interactive
done
eas env:list --environment production   # üçü de görünmeli
```

RevenueCat anahtarı gelince: `EXPO_PUBLIC_REVENUECAT_IOS_KEY` aynı kalıpla eklenir.

**Atlanırsa:** gömülü build'de değişkenler boş kalır → açılışta beyaz ekran (Clerk yok)
ve API 401.

```bash
eas build --profile production --platform ios
```

İlk çalıştırmada Apple girişi ister, sertifika/provizyonu EAS yönetir.

---

## 7) TestFlight

```bash
eas submit --platform ios --latest
```

`eas.json` → `submit.production.ios` doldurulmuş olmalı (`appleId`, `ascAppId`,
`appleTeamId`). Yükleme sonrası App Store Connect'te işleme ~10-30 dk sürer.

İhracat şifreleme sorusu **çıkmaz** — `ITSAppUsesNonExemptEncryption: false` app.json'da tanımlı.

Kendi cihazına TestFlight'tan kur, **gerçek akışı** test et (§9 kabul kriteri).

---

## 8) Mağaza listeleme bilgileri

Uygulama → Dağıtım hazırlığı:

| Alan | Not |
|---|---|
| Ekran görüntüleri | **6.9" iPhone** (1320×2868) yeterli. Simülatörde `Cmd+S` ile alınır; iPhone 16 Pro Max simülatörü tam bu boyutu verir. iPad gerekmez (uygulama iPhone-only). |
| Açıklama + anahtar kelimeler | MEB müfredatı, çalışma kağıdı, sınıf düzeyi vb. |
| Destek URL'si | `https://soruatolyesi.com/faq` |
| Gizlilik politikası URL'si | `https://soruatolyesi.com/legal/privacy` |
| **Uygulama Gizliliği** (veri toplama anketi) | E-posta/ad (hesap), kullanım verisi, tanımlayıcılar → beyan et. Muhasebe kayıtlarının anonimleştirilerek saklandığını unutma. |
| Yaş sınırı anketi | Eğitim içeriği, uygunsuz içerik yok |
| Lisans sözleşmesi | Apple'ın standart EULA'sı kullanılabilir (paywall'da kendi koşullarımıza da link var) |
| **İnceleme notu + demo hesabı** | Uygulama giriş duvarlı → **çalışan bir test hesabı e-posta/şifresi ŞART**. Notta denemenin sunucu tarafında kartsız işlediğini de yaz. |

---

## 9) Kabul kriteri (göndermeden önce hepsi geçmeli)

- [ ] TestFlight sürümünde **giriş çalışıyor** (beyaz ekran yok = EAS env doğru).
- [ ] Çalışma kağıdı üretiliyor, PDF paylaşılıyor.
- [ ] Paywall'da fiyatlar **mağazadan** geliyor (kodda yazan ₺199 değil).
- [ ] Sandbox hesabıyla `pro-aylik` satın alınıyor.
- [ ] RevenueCat panosunda olay görünüyor (Customer History).
- [ ] `GET /api/me/entitlements` → `plan: "pro"`.
- [ ] "Satın almaları geri yükle" çalışıyor.
- [ ] Profil → "Hesabımı sil" hesabı gerçekten kapatıyor (Apple 5.1.1(v)).
- [ ] Gizlilik / Kullanım Koşulları linkleri açılıyor.
- [ ] Bildirim ayarları ekranı çalışıyor, hatırlatma kuruluyor.

### Render ön koşulları

| Env | Değer |
|---|---|
| `REVENUECAT_WEBHOOK_AUTH` | RevenueCat webhook başlığıyla birebir aynı sır |
| `REVENUECAT_PRODUCT_MAP` | `pro-aylik:pro,proplus-aylik:pro-plus` |
| `REVENUECAT_ALLOW_SANDBOX` | Test boyunca `true`, **yayın günü `false`** |
| `CLERK_SECRET_KEY` | Hesap silme ucu için (yoksa 503 → red) |

---

## 10) Gönderim

Uygulama sürümü + abonelikler **birlikte** gönderilir. İnceleme genelde 24-48 saat.

Red gelirse mesajı olduğu gibi paylaş — çoğu red metin/ekran görüntüsü düzeltmesiyle kapanır.

---

## Sırası gelmemiş / bilinen açıklar

- `eas.json` → `submit.production.ios`: `appleId` + `ascAppId` + `appleTeamId` (§2'den sonra).
- **Gizlilik manifestosu** (`PrivacyInfo.xcprivacy`): `app.json`'da `ios.privacyManifests`
  tanımlı değil. Expo çoğunu otomatik üretir; ilk yüklemede Apple `ITMS-91053` uyarısı
  gönderirse eklenecek.
- Uzaktan push bildirimleri: APNs anahtarı gerekiyor
  ([MOBIL_BILDIRIM_PLANI.md](./MOBIL_BILDIRIM_PLANI.md) Faz 2). Yayın için şart değil.
