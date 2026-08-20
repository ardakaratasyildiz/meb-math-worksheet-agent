# Google Play — Yayın Koşu Kitabı (Android)

`apps/mobile` için geliştirici hesabı kaydı, ödeme/banka kurulumu, abonelik ürünleri,
satın alma testi ve üretim erişimi başvurusu.
iOS karşılığı ve RevenueCat/EAS ortak adımları: [MOBIL_STORE_HAZIRLIK.md](./MOBIL_STORE_HAZIRLIK.md).
Mağaza açıklaması metinleri ve 18 Ağu 2026 "Misleading Claims" reddinin düzeltmesi:
[PLAY_POLICY_FIX.md](./PLAY_POLICY_FIX.md) — açıklamada MEB'e atıf yapıyorsan önce onu oku.

Sabitler (kodda tanımlı, değiştirilmez):

| Ne | Değer | Nerede |
|---|---|---|
| Paket adı | `com.soruatolyesi.app` | `apps/mobile/app.json` |
| Abonelik SKU'ları | `com.soruatolyesi.app.pro_aylik` (₺199) · `com.soruatolyesi.app.proplus_aylik` (₺349) | `src/app/paywall.tsx` |
| Ek paket SKU'ları | `com.soruatolyesi.app.topup_25` (₺89) · `com.soruatolyesi.app.topup_75` (₺199) | **ilk turda AÇILMAZ** |

---

## 0) Geliştirici hesabı kaydı

Hiç hesap yoksa buradan başlar. Hesap zaten varsa §0.5'teki doğrulama durumunu
kontrol et ve §1'e geç.

### 0.1 Hangi Google hesabıyla?

`play.google.com/console` → "Geliştirici hesabı oluştur".

- **Kalıcı, kişisel bir Gmail kullan.** Hesap devri (transfer) Google desteğiyle
  yürüyen ağır bir süreç — sonradan "şunu şu maile taşıyalım" kolay değil.
- Şirket/işveren mailiyle açma (bu proje kişisel; iş hesabıyla açılan Play hesabı
  işten ayrılınca kilitlenir).
- Bu hesaba **2 adımlı doğrulama** kur. Kaybı = uygulamanın kaybı.

### 0.2 Hesap türü — geri dönüşü zor karar

| | Bireysel (kendim) | Kuruluş (organization) |
|---|---|---|
| Gereken belge | Resmi kimlik | Kimlik + **D-U-N-S numarası** (ücretsiz, alınması ~30 gün) |
| 12 testçi / 14 gün kapalı test | **Zorunlu** (13 Kas 2023 sonrası açılan hesaplar) | Muaf, doğrudan üretime çıkabilir |
| Mağaza sayfasında görünen | Ad + ülke; **satıcıysan tam adres** (§0.5) | Şirket adı + adresi |
| Bu proje için | ✅ seçilen yol (GVK 20/B şirketsiz gelir modeli) | Şirket kurma kararı verilirse |

Bireyselden kuruluşa geçiş sonradan mümkün ama destek talebi + belge süreci gerektirir.

### 0.3 Kayıt formu

| Alan | Not |
|---|---|
| Geliştirici adı (kullanıcılara görünür) | `Soru Atölyesi` — mağazada uygulamanın altında bu yazar |
| Yasal ad | Kimlikteki adla **birebir** aynı (§0.5 ve §1 bunu karşılaştırır) |
| Yasal adres | Kimlik/adres kanıtındaki adres |
| İletişim e-postası + telefon | Doğrulama kodu gelir; ikisi de doğrulanmalı. Bu e-posta mağaza sayfasında görünür |
| Uygulama türü / geliştirme amacı | "Kendim için/kişisel" değil, gerçek durumu yaz |

### 0.4 25 USD kayıt ücreti

- **Tek seferlik**, hesap başına, **iade edilmez**. Uygulama başına değil.
- Kredi/banka kartıyla, Google Payments üzerinden ödenir.
- Pratik tuzak: kartın **yurt dışı/internet işlemi kapalıysa** ödeme reddedilir ve
  kayıt yarıda kalır. Reddedilirse önce bankadan izni aç, sonra tekrar dene.
- Bu ödeme için oluşan Google Payments profili, §1'deki **satıcı/ödemeler profili
  DEĞİLDİR**. İkisi ayrı; para almak için §1 şart.

### 0.5 Kimlik doğrulama — yayının önkoşulu

Google, hesabı doğrulamadan uygulama yayınlatmaz ve doğrulama için bir **son tarih**
verir (kaçırılırsa hesap kapatılabilir).

1. Play Console → Ayarlar → Geliştirici hesabı → **Hesap ayrıntıları** → doğrulama
   bölümü. Görevler burada listelenir, tamamlanmayanlar kırmızı görünür.
2. İstenenler: **resmi kimlik** (kimlik kartı / pasaport / ehliyet) fotoğrafı,
   bazen **adres kanıtı** (son 3 aylık fatura veya banka ekstresi — üzerindeki ad ve
   adres, §0.3'te yazdığınla aynı olmalı).
3. Sonuç genelde birkaç gün, bazen 1-2 hafta. Reddedilirse gerekçe e-postayla gelir;
   en sık sebep **ad/adres uyuşmazlığı**.

> ⚠ **Adres gizlenemez.** Uygulama içi satın alma ile para kazanan hesaplar (yani biz),
> tüketici mevzuatı gereği **tam adresini Google Play mağaza sayfasında göstermek
> zorunda.** Bireysel hesapta bu, ev adresin olur. Adresin herkese açık olmasını
> istemiyorsan tek gerçek alternatif kuruluş hesabıdır (§0.2) — sahte/uyumsuz adres
> yazmak doğrulamayı ve ödemeleri kilitler.

### 0.6 Takvimi bu adım belirler

Bireysel hesap (13 Kasım 2023 sonrası açıldıysa): üretim yayınına başvurmadan önce
**kapalı testte en az 12 testçiyle kesintisiz 14 gün** koşmak zorunlu. **İç test bu
süreye saymaz.** Yani en erken yayın günü = kapalı testi başlattığın gün + 14 +
inceleme süresi. Sıralamada en uzun iki kuyruk:

| Kuyruk | Süre | Ne zaman başlatılmalı |
|---|---|---|
| Kimlik doğrulama (§0.5) | birkaç gün – 2 hafta | İlk gün |
| Ödemeler profili + banka (§1) | 1-2 gün + banka hesabı açma | İlk gün |
| RevenueCat servis hesabı izinleri (§8) | 24-36 saat yayılma | İç testten önce |
| Kapalı test 12/14 (§10) | **14 gün + inceleme** | Mümkün olan en erken gün |

---

## 1) Ödemeler profili ve banka hesabı (satıcı hesabı)

iOS'taki "Anlaşmalar, Vergi ve Bankacılık" adımının karşılığı.
**Bu bitmeden abonelik ürünü oluşturulamaz** — yani §6 buna bağlı.

### 1.0 ÖNCE BANKA, SONRA PLAY (GVK 20/B)

Bu projenin gelir modeli şirketsiz, **GVK mükerrer 20/B** ("sosyal içerik üreticiliği
ve mobil uygulama geliştiriciliğinde kazanç istisnası") üzerine kurulu. İstisnanın
sıkı bir şartı var: **hasılatın tamamı, bu faaliyet için açılmış özel banka hesabından
münhasıran tahsil edilmeli.** Google'a rastgele bir IBAN verip ilk ödemeyi normal
hesabına almak, o gelir için istisnayı riske atar.

Doğru sıra:

1. **Vergi dairesinden istisna belgesi al.** Başvuru vergi dairesine (İnteraktif Vergi
   Dairesi üzerinden de yapılabiliyor) yapılır; mobil uygulama geliştiriciliği ve
   gelirin uygulama mağazaları üzerinden elde edildiği beyan edilir.
2. **Bankada bu faaliyete özel hesap aç** ve istisna belgesini bankaya ibraz et.
   Bankalar bu hesabı özel olarak işaretler; hesaba gelen **brüt tutardan %15 gelir
   vergisi stopajı** yapıp muhtasar beyanla bildirir. Belge ibraz edilmezse banka
   stopajı yapmaz → şart ihlal olur.
3. **Sadece bu IBAN'ı** Play (ve App Store) ödemeler profiline gir. Bu hesaba başka
   gelir sokma, uygulama gelirini başka hesaba aldırma.

Hadler ve rakamlar her yıl değişir: **2026 için istisna sınırı 5.300.000 TL**
(GVK 103'teki tarifenin 4. dilimi). Aşılırsa kazancın tamamı yıllık beyannameyle
beyan edilir, bankanın kestiği stopaj hesaplanan vergiden mahsup edilir.

> ⚠ Bu bölüm vergi tavsiyesi değil, iş sırasını doğru kurmak için not. Belge ve
> hesap türünü mali müşavirle teyit et — özellikle "hangi banka bu hesabı açıyor" ve
> "yurt dışından gelen Google ödemesinde stopajı doğru uyguluyor mu" sorularını.

### 1.1 Profili oluştur

Play Console → **Para Kazanma → Ödemeler profili → Ödemeler profili oluştur**.

| Alan | Not |
|---|---|
| Profil türü | Bireysel |
| Ad, adres | **§0.3/§0.5 ile birebir aynı.** Uyuşmazlık = ödemelerin askıya alınması |
| Vergi kimlik | Bireysel için TC kimlik numarası |
| Telefon | Ayrıca doğrulanır |
| ABD vergi bilgileri | İstenirse **W-8BEN** doldurulur (ABD'de mükellef olmadığın beyanı) |

Türkiye satışlarında **KDV'yi Google beyan edip ödüyor** — sana gelen tutar KDV hariçtir.
Aboneliklerde **Play hizmet ücreti %15**.

Kabaca cebe kalan (₺199 Pro, **tahmin**, mali müşavirle doğrula):

| Adım | Tutar |
|---|---|
| Mağaza fiyatı (KDV dahil) | ₺199 |
| − KDV (Google beyan eder, %20) | ≈ ₺166 |
| − Play hizmet ücreti %15 | ≈ ₺141 → hesabına gelen |
| − Banka stopajı %15 (§1.0) | ≈ **₺120** |

Yani etiket fiyatının kabaca **%60'ı** kalıyor. Fiyatlama kararlarında
(`docs/MONETIZATION_PLAN.md`) bu oranı kullan, ₺199'u değil.

### 1.2 Banka hesabını ekle

Ödemeler profili → **Ödeme yöntemleri / Ödeme ayarları → Banka hesabı ekle**.

| Alan | Not |
|---|---|
| Para birimi | TRY |
| Hesap sahibi adı | Bankadaki adla **birebir** — kısaltma, ikinci ad eksiği bile reddettirir |
| IBAN | §1.0'daki **özel hesabın** IBAN'ı (TR ile başlar, 26 hane) |
| Banka adı / SWIFT | Form isterse bankanın SWIFT/BIC kodu |

Doğrulama: Google hesabı ad eşleşmesiyle ve/veya küçük bir test tutarı yatırarak
doğrular (yatırırsa ekstrede görünen tutarı Console'a girersin). Doğrulanmamış hesaba
ödeme yapılmaz — bakiye birikir, kaybolmaz.

### 1.3 Ödeme takvimi

- Bir ayın kazancı ay sonunda kapanır, ödeme **takip eden ayın ~15'inde** yapılır.
- Bakiye **ödeme eşiğinin** altındaysa ödeme yapılmaz, sonraki aya devreder. Eşiği
  ödemeler profilinden görebilir/yükseltebilirsin.
- İlk ödeme genelde en yavaş olanıdır (doğrulamalar + eşik). "Para gelmedi" panikleme
  sebebi değil; Play Console → Ödemeler ekranı durumu satır satır gösterir.

---

## 2) Uygulamayı oluştur

Play Console → Uygulama oluştur:

| Alan | Değer |
|---|---|
| Uygulama adı | Soru Atölyesi |
| Varsayılan dil | Türkçe (Türkiye) |
| Uygulama mı, oyun mu | Uygulama |
| Ücretsiz mi, ücretli mi | **Ücretsiz** |

> "Ücretsiz" seçimi **sonradan değiştirilemez**. Gelir uygulama içi abonelikten
> geleceği için doğru cevap Ücretsiz. Ücretli seçilirse IAP modeli çöker.

Paket adını **girdiğin bir alan yoktur** — Play, paket adını ilk yüklenen AAB'nin
içinden okur (§4). Paket adı ilk yüklemeden sonra bir daha değiştirilemez.

---

## 3) EAS ortam değişkenleri — build'den ÖNCE

Play'e yüklenecek paket JS'i **içine gömer**; yerel `.env` derleme sunucusunda yoktur.
Atlanırsa uygulama açılışta **beyaz ekran** verir (Clerk anahtarı yok) ve API çağrıları
**401** döner.

```bash
export PATH="/c/Users/arda.karatas/AppData/Local/Programs/nodejs:$PATH"
cd apps/mobile
eas login && eas whoami

for ENV in production preview; do
  eas env:set --name EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY \
    --value pk_live_Y2xlcmsuc29ydWF0b2x5ZXNpLmNvbSQ \
    --environment $ENV --visibility plaintext --non-interactive

  eas env:set --name EXPO_PUBLIC_API_URL \
    --value https://api.soruatolyesi.com \
    --environment $ENV --visibility plaintext --non-interactive

  eas env:set --name EXPO_PUBLIC_API_KEY \
    --value "<yerel apps/mobile/.env'deki değer>" \
    --environment $ENV --visibility sensitive --non-interactive
done

eas env:list --environment production   # üç değişken de görünmeli
```

RevenueCat anahtarları (§8 sonrası) aynı kalıpla eklenir:
`EXPO_PUBLIC_REVENUECAT_ANDROID_KEY` (`goog_...`).

---

## 4) İlk build (AAB)

```bash
cd apps/mobile
eas build --profile production --platform android
```

- `production` profili **AAB** üretir. Play iç teste APK kabul etmez → `preview`
  profili (APK) bu iş için kullanılamaz.
- İlk çalıştırmada EAS **yükleme anahtarını (keystore)** kendisi üretmeyi önerir →
  kabul et. EAS saklar; kaybolursa Play'e yükleme yapılamaz (yedeğini
  `eas credentials` ile indirebilirsin).
- Sürüm numarası: `eas.json`'da `appVersionSource: remote` + `autoIncrement: true` →
  `versionCode` EAS tarafında otomatik artar, elle uğraşmazsın.
- Build ~10-20 dakika. Bitince EAS bir indirme bağlantısı verir.

Bu build **bildirimleri de içerir** (`expo-notifications` native modülü) — önceki
Android dev build'inde yoktu.

---

## 5) İç teste yükle

Play Console → Test → **İç test** → Yeni sürüm oluştur:

1. AAB'yi yükle.
2. **Play Uygulama İmzalama**'yı kabul et (varsayılan). Google imzalama anahtarını
   tutar, sen yükleme anahtarıyla yüklersin.
3. Sürüm notu yaz (tek satır yeter).
4. Testçi listesi oluştur → kendi Gmail adresini ve test edecekleri ekle.
5. Yayınla → Play sana bir **katılım (opt-in) bağlantısı** verir; testçiler o
   bağlantıdan katılıp uygulamayı Play'den kurar.

İç test **incelemeye girmez**, dakikalar içinde kurulabilir hale gelir.

> **Satın alma testi yalnız Play'den kurulan uygulamada çalışır.** Kenardan yüklenen
> APK'da imza eşleşmediği için IAP hep hata verir.

Yükleme sırasında Play **hedef API seviyesi** uyarısı verirse not al — Expo SDK
sürümünü yükseltmek gerekebilir.

---

## 6) Abonelik ürünleri

Ancak §5 tamamlandıktan sonra açılır: Para Kazanma → Ürünler → **Abonelikler**.

Play'in modeli iOS'tan farklı, üç katmanlı: **Abonelik → Temel plan → Teklif**.

### 6.1 Pro

1. Abonelik oluştur → **Ürün kimliği: `com.soruatolyesi.app.pro_aylik`** (bir daha değiştirilemez).
2. Ad: "Pro", açıklama: aylık 50 çalışma kağıdı.
3. **Temel plan ekle** → kimlik ör. `aylik` → tür: **Otomatik yenilenen** → süre: 1 ay.
4. Fiyat: Türkiye ₺199 (KDV dahil gösterim).
5. Temel planı **etkinleştir** — etkin değilse uygulama ürünü göremez.

### 6.2 Pro+

Aynısı: **`com.soruatolyesi.app.proplus_aylik`**, temel plan aylık, ₺349.

### 6.3 Yapılmayacaklar

- **Ücretsiz deneme teklifi ekleme.** Deneme bizim tarafımızda, kartsız çalışıyor
  (7 gün / 20 kağıt). Mağaza denemesi kart ister ve iptal/iade sürtünmesi getirir.
- **Ek paketleri (`com.soruatolyesi.app.topup_25`, `com.soruatolyesi.app.topup_75`) ilk turda açma.** Önce iki abonelikle
  tek değişkenli test edelim.

---

## 7) Lisans testçileri (ücretsiz test satın alma)

Play Console → Ayarlar → **Lisans testi** → Google hesaplarını ekle.

- Bu hesaplar satın almayı **ücretsiz** yapar (gerçek para çekilmez).
- Yenilenme **hızlandırılır**: aylık abonelik dakikalar içinde yenilenir → yenileme
  ve iptal akışlarını da test edebilirsin.
- Aynı hesaplar **iç test listesinde de** olmalı, yoksa uygulamayı kuramazlar.

---

## 8) RevenueCat için servis hesabı — EN UZUN KUYRUK, erken başlat

1. **Google Cloud Console** → Play'e bağlı proje → IAM ve Yönetim → Hizmet Hesapları →
   oluştur → **JSON anahtarı** indir (tek seferlik).
2. **Play Console → Ayarlar → API erişimi** → Cloud projesini bağla → bu servis
   hesabına izin ver:
   - **Finansal verileri görüntüle**
   - **Siparişleri ve abonelikleri yönet**
3. JSON'ı **RevenueCat** → Android uygulaması yapılandırmasına yükle.

> İzinlerin Google tarafında yayılması **24-36 saat** sürebilir. Bu süre dolmadan
> RevenueCat satın almayı doğrulayamaz ve kurulum bozukmuş gibi görünür. Panik yapma,
> bekle.

---

## 9) Uygulama içeriği beyanları

Play Console → Politika → **Uygulama içeriği**. Hazırlaması vakit alır, erken doldur.

| Beyan | Değer / not |
|---|---|
| **Uygulama erişimi** | Uygulamanın tamamı girişin arkasında → "Tüm veya bazı işlevler kısıtlı" seç ve **inceleme için çalışan bir test hesabı** (e-posta + şifre + varsa giriş adımı notu) gir. Boş bırakmak sık görülen ret sebebi: inceleyen içeri giremeyince uygulama "çalışmıyor" sayılır. |
| Gizlilik politikası | `https://soruatolyesi.com/legal/privacy` |
| Veri silme | `https://soruatolyesi.com/hesap/sil` (oturumsuz açılır — Play'in gereği) |
| Veri güvenliği formu | Toplanan veri + amaç. `usage_ledger` ve `billing_events` silinmez, `tenant_id` geri döndürülemez takma adla değiştirilir (VUK saklama) → "silme talebinde veriler silinir, muhasebe kayıtları anonimleştirilerek saklanır" olarak beyan et. |
| İçerik derecelendirmesi | Anket; eğitim uygulaması, şiddet/uygunsuz içerik yok. |
| Hedef kitle ve içerik | 1-8. sınıf → **çocuklar dahil** → **Families (Aileler) politikası** kapsamı. Reklam yok, bu işi kolaylaştırır. |
| Reklamlar | Yok. |

Bildirim izni (`POST_NOTIFICATIONS`, Android 13+) normal çalışma zamanı iznidir,
ayrı bir beyan formu gerektirmez.

---

## 10) Kapalı test — 12 kişi / 14 gün (bireysel hesap)

Play Console → Test → **Kapalı test** → sürüm oluştur (aynı AAB kullanılabilir).

- En az **12 testçi** katılım (opt-in) bağlantısını kabul etmiş olmalı. 12 farklı
  Google hesabı; Play'den kurmuş olmaları gerekir, kenardan yüklenen APK saymaz.
- **14 gün kesintisiz** sürmeli. Testçi sayısı 12'nin altına düşerse (biri çıkarsa)
  sayaç bozulur → 2-3 kişi **yedek** al, 14-15 kişiyle başla.
- Testçileri e-posta listesiyle ekle (Play Console → test listesi). Katıldıklarını
  tek tek teyit et; "linki gönderdim" yeterli değil, kabul etmeleri gerekiyor.
- Testçilerin uygulamayı **gerçekten kullanması** lehine — başvuruda "ne geri bildirim
  aldın" sorusuna cevap oradan çıkıyor. Kullanılmamış bir test turu reddedilebiliyor.
- İç test (§5) bu süreye **saymaz** — kapalı test ayrı bir kanaldır. İkisi paralel koşar.

### 10.1 Üretim erişimi başvurusu (14 gün dolunca)

Play Console → Dashboard (veya Test → Kapalı test) → **"Üretim erişimi için başvur"**.
Bir form doldurulur, serbest metin alanları var ve **gerçek cevap ister**:

| Soru | Ne yazılmalı |
|---|---|
| Testçileri nasıl buldun? | Somut anlat (öğretmen/veli tanıdıklar, arkadaş çevresi). "Satın aldım" izlenimi verme |
| Test sırasında ne geri bildirim aldın? | 3-5 madde: gerçek sorunlar (ör. paywall fiyat gösterimi, PDF indirme, bildirim izni) |
| Bu geri bildirimle uygulamada ne değişti? | Karşılık gelen düzeltmeler + hangi sürümde çıktı |
| Uygulama neden üretime hazır? | Kapsam (1-8. sınıf, 5 ders), abonelik akışının uçtan uca test edildiği (§11 listesi) |
| Hedef ülkeler / kitle | Türkiye; çocuklar dahil → Families politikası (§9 ile tutarlı olsun) |

- Google inceler: genelde **birkaç gün, 7 güne kadar** sürebiliyor.
- Reddedilirse gerekçe bildirilir, düzeltip tekrar başvurulur — ama her tur takvimden
  gün yer. Bu yüzden §9 beyanlarının başvuru anında **tamamlanmış** olması önemli.
- Üretim erişimi onaylanana kadar uygulama Play'de aranabilir/kurulabilir olmaz.

---

## 11) Uçtan uca satın alma testi (kabul kriteri)

Sırayla hepsi geçmeli:

- [ ] Play'den kurulan uygulamada **giriş çalışıyor** (beyaz ekran yok = §3 doğru).
- [ ] Çalışma kağıdı üretiliyor (API anahtarı doğru).
- [ ] Paywall'da fiyatlar **mağazadan** geliyor (kodda yazan ₺199 değil, Play'in
      döndürdüğü yerelleştirilmiş fiyat).
- [ ] Lisans testçisi hesabıyla `com.soruatolyesi.app.pro_aylik` satın alınıyor.
- [ ] **RevenueCat panosunda olay görünüyor** (Customer History).
- [ ] `GET /api/me/entitlements` → `plan: "pro"` dönüyor.
- [ ] Backend logunda webhook işlendi (`RevenueCat senkron: ... plan=pro status=active`).
- [ ] Uygulamada "Satın almaları geri yükle" çalışıyor.
- [ ] Bildirim ayarları ekranından günlük hatırlatma kuruluyor ve tetikleniyor.

### Render ön koşulları (yayından önce)

| Env | Değer |
|---|---|
| `REVENUECAT_WEBHOOK_AUTH` | RevenueCat webhook başlığıyla birebir aynı sır |
| `REVENUECAT_PRODUCT_MAP` | `com.soruatolyesi.app.pro_aylik:pro,com.soruatolyesi.app.proplus_aylik:pro-plus` |
| `REVENUECAT_ALLOW_SANDBOX` | Test boyunca `true`, **yayın günü `false`** |
| `CLERK_SECRET_KEY` | Hesap silme ucu için (yoksa 503 → mağaza reddi) |

---

## 12) Sırası gelmemiş işler

- `eas.json` → `submit.production.android`: servis hesabı JSON yolu (§8'den sonra).
- Ek paket ürünleri (`com.soruatolyesi.app.topup_25`, `com.soruatolyesi.app.topup_75`) — kod düzeltmesi canlıda, ürünler
  abonelik testi geçtikten sonra açılır.
- Uzaktan push bildirimleri: FCM projesi + `google-services.json`
  ([MOBIL_BILDIRIM_PLANI.md](./MOBIL_BILDIRIM_PLANI.md) Faz 2).
