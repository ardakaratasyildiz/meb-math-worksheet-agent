# Şahıs Şirketi & Ödeme Lansmanı — Kuruluş Checklist'i

> **Durum:** taslak · 2026-07-15
> **⚠️ Yasal uyarı:** Bu belge bir SMMM/avukat tavsiyesi DEĞİLDİR. Türkiye vergi ve
> şirket mevzuatı değişebilir; kişisel durumuna göre farklılaşır. **Her maddeyi bir
> Serbest Muhasebeci Mali Müşavir (SMMM) ile teyit et.** Şirket için SMMM ile
> çalışmak fiilen zorunludur.
> **Bağlam:** [`IYZICO_ENTEGRASYON_PLANI.md`](./IYZICO_ENTEGRASYON_PLANI.md) ·
> [`MONETIZATION_PLAN.md`](./MONETIZATION_PLAN.md)

---

## 0. Sıralama mantığı (önce oku)

- Şirket kurmak **teknik geliştirmenin ön koşulu değil.** iyzico **sandbox** şirketsiz test edilir.
- Şirket **yalnızca** şunlar için gerekir: iyzico **prod** (gerçek tahsilat) + **fatura** kesmek.
- Şirketi kurduğun an **Bağkur + vergi beyanı yükümlülüğü başlar** (aylık gider).
- **Doğru sıra:** Faz 1 (teknik + yasal metinler + sandbox) → hazır olunca Faz 2 (şirket kur) → Faz 3 (iyzico prod + go-live). Şirketi lansmandan ~2 hafta önce kur.

---

## Faz 1 — Şirket ÖNCESİ (şimdi yapılabilir, şirketsiz)

### 1.1 Teknik ön koşullar (bkz. iyzico planı P0)
- [x] Sunucu-tarafı Clerk JWT doğrulama (kimlik spoof'unu kapat) — **CANLI & DOĞRULANDI**
      (2026-07-16). PR #93 primitif `app/services/clerk_auth.py` + PR #94 `me/*` wiring;
      Render'da `CLERK_ISSUER=https://clerk.soruatolyesi.com` set edildi. Canary:
      token'sız `me/*` → 401 "Kimlik doğrulanamadı", sahte-imzalı token → 401,
      public akışlar (curriculum 200 / shared 404) sağlam. Rollback = env'i sil.
- [x] Turso prod'da açık (abonelik durumu kalıcı) — **doğrulandı** (`api.soruatolyesi.com/readyz`
      → `db_backend: turso`, 2026-07-16).
- [ ] billing_store + billing router + iyzico_client (sandbox modunda)
- [ ] Kota enforcement (402 + paywall)
- [ ] iyzico **sandbox** uçtan uca test yeşil

### 1.2 Web sitesi yasal metinleri (iyzico başvurusunun ŞARTI)
iyzico başvuruda siteyi inceler; bunlar yayında olmalı. Kod tarafı — **hazırlayabilirim**:
- [ ] **Mesafeli satış sözleşmesi** (`/legal/mesafeli-satis`)
- [ ] **Ön bilgilendirme formu** (checkout öncesi onay)
- [ ] **Gizlilik politikası / KVKK aydınlatma metni** (`/legal/privacy` — doldur)
- [ ] **İptal & iade / cayma hakkı koşulları** (dijital hizmette cayma istisnası dahil)
- [ ] **Çerez politikası** (var — kontrol)
- [ ] **Künye/iletişim**: ticari unvan, adres, e-posta, telefon, vergi dairesi + no
- [ ] Fiyatların **KDV dahil** ve TL gösterimi; toplam bedelin net görünmesi
> Not: Künye/sözleşmelerdeki ticari unvan + vergi no şirket kurulmadan **netleşmez**;
> şablonları şimdi hazırlarız, şirket bilgisi çıkınca doldururuz.

### 1.3 İş kararları — ✅ KAPANDI (2026-07-16, bkz. MONETIZATION_PLAN §6)
- [x] SKU seti: **iki Pro kademesi** — Pro ₺189/ay (1000 soru/ay), Pro+ ₺249/ay
      (fair-use sınırsız + tam veli/öğretmen analitiği). Ücretsiz 100 soru/ay kalıcı +
      7g kartsız deneme. Lansmanda yalnız aylık (2 SKU). Kurumsal = Faz 2 manuel.
- [x] Fiyat + KDV: fiyatlar **KDV DAHİL** gösterilir (B2C).
- [x] e-Arşiv fatura: **başta manuel** (GİB/SMMM), hacim artınca entegratör.

### 1.4 Kuruluş için hazırlık / araştırma
- [ ] **SMMM bul** (aylık ücret + kuruluşu o yapar). Kuruluşun anahtar adımı budur.
- [ ] **Genç girişimci istisnası** uygunluğunu SMMM'ye sor (aşağıda §Faz 2.0)
- [ ] **e-Devlet** hesabı aktif (çoğu işlem oradan)
- [ ] **e-İmza** temini gerekip gerekmediğini SMMM'ye sor

---

## Faz 2 — Şahıs şirketi kuruluşu (lansmandan ~2 hafta önce)

> Bunların çoğunu **SMMM senin adına yapar.** Sen belge/onay sağlarsın.

### 2.0 Önce: Genç girişimci istisnası (KAÇIRMA — para)
- [ ] 29 yaş altı + ilk kez mükellef isen: **gelir vergisi istisnası** (yıllık kazanç
      istisna tutarına kadar, ilk 3 yıl) + **Bağkur prim teşviki** (1 yıl devlet karşılar)
      olabilir. Uygunluğu SMMM ile teyit et; kuruluşta beyan gerekir.

### 2.1 Kuruluş adımları
- [ ] **Faaliyet (NACE) kodu** seçimi — yazılım/SaaS için ör. **62.01** (bilgisayar
      programlama). SMMM doğru kodu seçer (fatura keseceğin faaliyet).
- [ ] **İşe başlama bildirimi** → vergi dairesi kaydı (İnteraktif Vergi Dairesi /
      e-Devlet üzerinden SMMM yapar)
- [ ] **İş yeri adresi**: ev adresi kullanılabilir. Kira ise **kira sözleşmesi** +
      gerekebilecek **muvafakatname**; kendi evinse tapu/ikametgah. (Stopaj/kira
      giderini SMMM'ye sor.)
- [ ] **İmza beyannamesi** (şahısta imza sirküleri yerine bu; noter)
- [ ] **Vergi levhası** çıkışı (kayıt sonrası)
- [ ] **Bağkur (SGK 4-b)** kaydı — kuruluşla **otomatik** başlar (aylık prim yükümü)
- [ ] **Defter-Beyan Sistemi** kaydı (şahısta işletme defteri — SMMM tutar)
- [ ] **Vergi dairesi yoklaması**: memur adresi doğrulamaya gelebilir (evde ol/erişilebilir)

### 2.2 Fatura altyapısı
- [ ] **e-Arşiv fatura** başvurusu (şahıs şirketi B2C'ye e-arşiv keser) — GİB portalı
      veya özel entegratör. Ciro eşiği aşılırsa e-Fatura zorunlu olabilir (SMMM izler).
- [ ] Fatura kesme akışı: satış (iyzico webhook) → fatura tetikleyici (manuel/otomatik)

### 2.3 Banka
- [ ] **Ticari/işletme banka hesabı** aç (vergi levhası + kimlik ile). iyzico
      ödemeleri (payout) bu IBAN'a yatar. Şahısta bireysel hesap da olabilir ama
      ticari hesap muhasebe/ayrışma için önerilir — SMMM'ye sor.

---

## Faz 3 — iyzico prod & go-live (şirket kurulduktan sonra)

### 3.1 iyzico başvuru evrakı
- [ ] **Vergi levhası**
- [ ] **Kimlik** (şahıs sahibi)
- [ ] **Banka IBAN** (ticari hesap)
- [ ] **İmza beyannamesi**
- [ ] **Web sitesi** (Faz 1.2 metinleri yayında + fiyat/KDV görünür)
- [ ] iyzico işletme doğrulama sürecini tamamla (onay birkaç gün sürebilir)

### 3.2 Teknik go-live (iyzico planı §11)
- [ ] iyzico **prod** API key'leri (`IYZICO_API_KEY/SECRET`, `IYZICO_BASE_URL=prod`)
- [ ] iyzico **Abonelik Ürünü + Pricing Plan**'ler prod'da kurulu
- [ ] `premium_all=false` + `BILLING_ENABLED=true`
- [ ] Webhook prod URL'i iyzico panelinde kayıtlı + imza doğrulama test
- [ ] Birkaç allowlist tenant ile **canary** → ilk gerçek ödeme
- [ ] Herkese aç + GA4 funnel (checkout_start → subscription_active) izle

---

## Faz 4 — Kuruluş sonrası sürekli yükümlülükler (bilincinde ol)

- [ ] **Aylık** SMMM ücreti + **Bağkur** primi (sabit aylık gider)
- [ ] **KDV beyannamesi** (dijital hizmette KDV %20; dönemsel)
- [ ] **Geçici (kurumlar/gelir) vergi** beyanı (3 aylık)
- [ ] **Yıllık gelir vergisi** beyannamesi
- [ ] Faturaların düzenli kesilmesi + kayıt

---

## Kim ne yapıyor?

| İş | Kim |
|---|---|
| SMMM bulmak, banka hesabı, iyzico başvurusu, kimlik/imza evrakı | **Sen** (gerçek dünya) |
| Şirket kuruluş işlemleri, vergi kaydı, defter, beyannameler | **SMMM** |
| Genç girişimci uygunluk teyidi, KDV/fatura stratejisi | **SMMM** |
| Web sitesi yasal metin sayfaları (şablon + entegrasyon) | **Claude (kod)** |
| iyzico teknik entegrasyon (billing router/webhook/kota) | **Claude (kod)** |
| Fiyat/SKU/paketleme kararı | **Sen** (Claude öneri sunar) |

---

## Şimdi başlayabileceğimiz (kod) işler — şirket beklemez
1. Yasal metin sayfaları şablonları (mesafeli satış, ön bilgilendirme, KVKK, iptal/iade, künye) — ticari unvan/vergi no sonra doldurulur.
2. iyzico planı P0'ları (Clerk JWT doğrulama + Turso).
3. iyzico sandbox entegrasyonu.
