# Play reddi — "Misleading Claims / Missing Source Link for Government Information"

**Tarih:** 18 Ağustos 2026 · **Uygulama:** `com.soruatolyesi.app` · **Durum:** Rejected
(yeni sürüm yayına alınmadı; mağazadaki eski sürüm varsa yayında kalır).

## 1) Google tam olarak ne diyor?

Gerekçe **içerikle değil, iddiayla** ilgili. Mağaza açıklamasında "MEB müfredatına
uygun" deniyor → Google bunu **devlet kaynaklı bilgi** sayıyor. Bu durumda iki şey
zorunlu:

1. Bilginin **resmî kaynağına** açık, geçerli ve çalışan bağlantı (tercihen `.gov`/`.gov.tr`).
2. Uygulamanın **o kurumu temsil etmediğine** dair, açıklamada **kolayca görülen** bir uyarı.

İkisi de yoktu. Devlet bağlantısı iddia etmediğimiz için **itiraz (appeal) yolu bize
göre değil** — itiraz, MEB'le resmî yetki/anlaşma belgesi olanlar içindir. Doğru yol:
açıklamayı düzeltip yeniden göndermek.

## 2) Ne yapıldı (bu commit)

Uygulama içi ayak — Google'ın "Clarify and/or add to the information in your app" adımı:

| Dosya | Değişiklik |
|---|---|
| `apps/mobile/src/lib/legal.ts` | Tek doğruluk kaynağı: bağımsızlık uyarısı (kısa/uzun) + 3 resmî MEB bağlantısı |
| `apps/mobile/src/app/about.tsx` | Yeni "Hakkında & Kaynaklar" ekranı — uyarı + tıklanabilir resmî kaynaklar + "içerik yapay zekâ ile üretilir" notu |
| `apps/mobile/src/components/meb-notice.tsx` | Kompakt künye kutusu (uyarı + ekrana giden bağlantı) |
| `apps/mobile/src/app/(tabs)/create.tsx` | Üretim (kazanım/ünite seçimi) ekranının altına künye |
| `apps/mobile/src/app/(tabs)/profile.tsx` | "Hakkında & Kaynaklar" satırı + sürüm altında tek satır uyarı |
| `frontend/components/Footer.tsx` | Web'de aynı bildirim + resmî kaynak bağlantıları (site mağaza sayfasından linkli) |
| `scripts/make_play_feature.py` | Özellik grafiğindeki (1024×500) MEB iddiasını kaldırır, bağımsızlık notu ekler |

**Özellik grafiği (feature graphic).** Eski görselde "MEB müfredatına uygun sorular"
yazıyordu — aynı politika görsellere de işliyor. Betik maskotu ve zemini korur; yalnız
alt başlık bandını arka plan degradesiyle yeniden boyayıp yeni metni yazar:

```bash
python scripts/make_play_feature.py
# ~/Desktop/play-store/play-feature-1024x500.png → …-v2.png
```

Yeni metin: `1-8. sınıf · 5 ders · kazanım bazlı` / `Çalışma kağıdı ve quiz · PDF + çözüm`.
Görselde bağımsızlık uyarısı YOK ve olması gerekmiyor: uyarı, iddianın yapıldığı yerde —
yani **açıklama metninde** (§3) aranıyor; grafik artık hiçbir kurum iddiası taşımıyor.
(İstenirse betikteki `DISCLAIMER` doldurulunca alt satır olarak basılır.)

Mağaza metinleri repoda tutulmuyor (Play Console'a elle giriliyor) → §3'teki metinler
kopyala-yapıştır içindir.

## 3) Yeni mağaza metinleri (tr-TR) — kopyala-yapıştır

### Kısa açıklama (≤80 karakter)

```
MEB müfredatına göre çalışma kağıdı üret. Resmî MEB uygulaması değildir.
```

### Tam açıklama (≤4000 karakter)

```
Soru Atölyesi, 1-8. sınıf için çalışma kağıtlarını ve quizleri saniyeler içinde hazırlar. Sınıfı ve konuyu seç, kaç soru istediğini söyle; gerisini uygulama yapar.

⚠️ ÖNEMLİ BİLDİRİM
Soru Atölyesi bağımsız bir eğitim uygulamasıdır. T.C. Millî Eğitim Bakanlığı (MEB), Talim ve Terbiye Kurulu Başkanlığı veya başka herhangi bir resmî kurumla bağlantılı, ortaklı ya da bu kurumlarca onaylı DEĞİLDİR; hiçbirini temsil etmez ve resmî bir devlet hizmeti sunmaz. Uygulamadaki sınıf, ünite ve kazanım başlıkları MEB'in kamuya açık öğretim programlarına dayanır. Sorular, cevap anahtarları ve çözümler yapay zekâ ile üretilir; MEB'in resmî yayını, ders kitabı veya sınav materyali değildir.

📚 RESMÎ KAYNAKLAR
Uygulamada kullanılan müfredat (öğretim programı, ünite ve kazanım) bilgisinin kaynakları:
• T.C. Millî Eğitim Bakanlığı — https://www.meb.gov.tr
• Öğretim programları / Türkiye Yüzyılı Maarif Modeli — https://tymm.meb.gov.tr
• Talim ve Terbiye Kurulu Başkanlığı, öğretim programları ve kazanım listeleri — https://mufredat.meb.gov.tr
Güncel ve bağlayıcı bilgi için lütfen yukarıdaki resmî kaynaklara başvurun.

NE YAPABİLİRSİN?
• Çalışma kağıdı üret — 1-8. sınıf; matematik, fen bilimleri, Türkçe, sosyal bilgiler, İngilizce. Ünite ve kazanım seçimi MEB'in kamuya açık öğretim programlarındaki başlıklara göre yapılır.
• PDF olarak indir, paylaş veya yazdır — cevap anahtarı ve adım adım çözümler dahil.
• Uygulama içinde quiz olarak çöz, anında puanını gör.
• Yanlışlarını takip et; hangi konuda eksiğin olduğunu gör.
• Eksiklerine göre çalışma programı oluştur.
• Öğretmensen sınıf oluştur, ödev ata; velinsen çocuğunun gelişimini takip et.

KİMLER İÇİN?
• Öğrenciler — konu tekrarı ve sınav öncesi alıştırma
• Öğretmenler — hızlı ödev ve sınıf içi çalışma kağıdı
• Veliler — evde düzenli alıştırma ve gelişim takibi

İÇERİK NASIL ÜRETİLİR?
Sorular yapay zekâ ile üretilir ve seçtiğin kazanımla hizalanması için otomatik denetimlerden geçer. Buna rağmen hata içerebilir; kullanmadan önce kontrol etmeni öneririz. Üretilen içerik resmî bir kaynak veya sınav materyali değildir.

ABONELİK
Uygulama ücretsiz kullanılabilir. Daha fazla çalışma kağıdı için isteğe bağlı abonelikler sunulur:
• Pro — aylık 50 çalışma kağıdı
• Pro+ — aylık 120 çalışma kağıdı
Abonelik Google Play hesabından tahsil edilir ve iptal edilmediği sürece otomatik yenilenir. Yenilemeyi dönem bitiminden en az 24 saat önce Google Play > Abonelikler bölümünden iptal edebilirsin. Güncel fiyatlar uygulama içinde gösterilir.

Kullanım Koşulları: https://soruatolyesi.com/legal/terms
Gizlilik Politikası: https://soruatolyesi.com/legal/privacy
İletişim: destek@soruatolyesi.com

Soru Atölyesi bağımsız bir eğitim uygulamasıdır ve MEB'i temsil etmez.
```

> Aynı metnin İngilizce yerelleştirmesi varsa **onu da** güncelle; Google reddi tek tek
> dil sürümleri üzerinden verir (bu ret `tr-TR` açıklaması için geldi).

## 4) Play Console adımları

1. Play Console → uygulama → **Store presence → Main store listing** → dil `tr-TR`.
2. Kısa açıklama ve tam açıklamayı §3'teki metinlerle değiştir → **Kaydet**.
3. Ekran görüntülerinde/feature graphic'te "MEB", "resmî", "Bakanlık" ibaresi veya MEB
   logosu/amblemi VARSA kaldır (görsel iddia da aynı politikaya girer).
4. **Publishing overview** → bekleyen değişiklikleri **incelemeye gönder**.
5. Uygulama içi künyeyi de göndermek için (önerilir, şart değil):
   `eas build -p android --profile production` → yeni AAB'yi yükle.
   `versionCode` elle artırılmaz — `eas.json`'da `appVersionSource: remote` +
   production profilinde `autoIncrement: true` var, EAS kendi artırır.
6. İnceleme sonucunu bekle (genelde 1-7 gün).

> **İtiraz (Submit an appeal) gönderme.** MEB'den yetki belgemiz yok; itiraz reddedilir
> ve süreci uzatır. Doğru yol açıklamayı düzeltip yeniden göndermektir.

## 5) Kontrol listesi (göndermeden önce)

- [ ] Açıklamanın **ilk ekranında** görünen bir bağımsızlık uyarısı var
- [ ] En az bir **çalışan** `.gov.tr` kaynak bağlantısı var (3'ü de test edildi: 18 Ağu 2026 ✅)
- [ ] Başlıkta ve alt başlıkta "MEB", "resmî", "Bakanlık" iddiası yok
- [ ] Özellik grafiğinde MEB iddiası yok (v2 yüklendi)
- [ ] Ekran görüntülerinde MEB logosu/amblemi ve "MEB müfredatına uygun" üstyazısı yok
- [ ] Uygulama içinde uyarı + kaynaklar görünür (Profil → Hakkında & Kaynaklar)
- [ ] Aynı düzeltme **App Store** açıklamasına da uygulandı (Apple 2.3.1/5.2.5 benzer
      şekilde yanıltıcı kurum iddiasına takar — aynı metni kullan)
