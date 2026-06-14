# LGS SEO Planı

**Tarih:** 2026-06-14
**Kapsam:** Hub sayfası + LGS-odaklı long-tail alt-konu sayfaları
**Durum:** Onay bekliyor (inşa başlamadı)

---

## 1. Neden — mevcut boşluk

Programatik SEO motoru çalışıyor (~235 statik sayfa, ~325 sitemap URL). Ama LGS tarafında iki net boşluk var:

1. **LGS hub/landing sayfası yok.** "LGS matematik", "LGS hazırlık", "LGS matematik çalışma kağıdı" Türkiye'de çok yüksek hacimli head-term'ler. Bu sorgulara oynayan tek bir güçlü sayfa yok — LGS şu an sadece `layout.tsx` keywords'te ve OG görselinde geçiyor.
2. **8. sınıfın hiç alt-konu (long-tail) sayfası yok.** Mevcut 74 alt-konu sayfasının tamamı 1.-7. sınıf. LGS sınıfının long-tail kapsamı sıfır. Halbuki en yüksek ticari niyetli aramalar burada ("LGS üslü sayılar soruları", "LGS çarpanlar ve katlar çalışma kağıdı" vb.).

8. sınıfta hâlihazırda **5 müfredat konu sayfası** var (`8-sinif-dogal-sayilar`, `-cebir`, `-geometri`, `-veri-isleme`, `-olasilik`), toplam 43 kazanım. Yani altyapı hazır; eksik olan hub + alt-konu katmanı.

---

## 2. Part A — LGS Hub Sayfası

**Route:** `/lgs-matematik` (top-level, temiz head-term URL)
*Alternatif:* `/calismalar/lgs` (mevcut hub şemasıyla tutarlı ama head-term için top-level daha güçlü). **Öneri: `/lgs-matematik`.**

**Hedef anahtar kelimeler:** LGS matematik · LGS hazırlık · LGS matematik çalışma kağıdı · 8. sınıf LGS · LGS matematik konuları

**İçerik bloğu (benzersiz öz içerik — thin/doorway değil):**
- H1: "LGS Matematik Çalışma Kağıdı — 8. Sınıf Hazırlık"
- LGS sınavı + matematik kapsamı hakkında benzersiz tanıtım paragrafı
- 5 ana konuya kart linkleri (mevcut `8-sinif-*` müfredat sayfaları)
- Tüm LGS alt-konularına link grid (Part B'den beslenir)
- Mini FAQ: "LGS'de matematik kaç soru?", "Hangi konular çıkar?", "Nasıl çalışılır?" → FAQPage rich-result fırsatı
- Üretece CTA (`/generate?grade=8`)

**Structured data:** `CollectionPage` (hasPart → 8. sınıf LearningResource'lar) + `FAQPage`

**Sitemap:** priority 0.9, changeFrequency weekly

**İç-link:** Ana sayfa (8. sınıf kartlarının yanına "LGS hazırlık" linki) + `/calismalar` hub + footer'a `/lgs-matematik` ekle.

---

## 3. Part B — LGS Long-tail Alt-konu Sayfaları

Mevcut `ALTKONU_PAGES` motorunu 8. sınıf girdileriyle genişlet. **Sıfır risk:** `generateStaticParams` + `sitemap.ts` bunları otomatik toplar, üretim hattına dokunmaz (alt-konular konu seviyesine deep-link eder).

URL deseni: `/calismalar/8-sinif-<topic>/<slug>` (mevcut `[slug]/[kazanim]` route'unu paylaşır).

LGS'de sık çıkan, arama hacmi yüksek alt-konular (~14 sayfa):

| topicId | Alt-konu | slug |
|---|---|---|
| dogal_sayilar | Üslü İfadeler | `uslu-ifadeler` |
| dogal_sayilar | Kareköklü İfadeler | `karekoklu-ifadeler` |
| dogal_sayilar | Çarpanlar ve Katlar (EBOB-EKOK) | `carpanlar-ve-katlar` |
| dogal_sayilar | Gerçek (Rasyonel/İrrasyonel) Sayılar | `gercek-sayilar` |
| cebir | Çarpanlara Ayırma | `carpanlara-ayirma` |
| cebir | Cebirsel İfadeler ve Özdeşlikler | `ozdeslikler` |
| cebir | Doğrusal Denklemler | `dogrusal-denklemler` |
| cebir | Doğrunun Eğimi | `dogrunun-egimi` |
| cebir | Eşitsizlikler | `esitsizlikler` |
| geometri | Üçgenler ve Pisagor Bağıntısı | `ucgenler-pisagor` |
| geometri | Dönüşüm Geometrisi (öteleme-yansıma-dönme) | `donusum-geometrisi` |
| geometri | Geometrik Cisimler (silindir-koni-piramit) | `geometrik-cisimler` |
| veri_isleme | Veri Analizi ve Grafikler | `veri-analizi` |
| olasilik | Basit Olayların Olasılığı | `basit-olaylarin-olasiligi` |

Her sayfa mevcut `AltKonu` şemasını izler: benzersiz `intro`, 4-6 `skills`, `difficulty` (kolay/orta/zor). Başlık ve description'larda doğal yerlerde "LGS" çerçevesi (örn. description: "...LGS hazırlık için..."). `family` alanıyla varsa alt sınıflara çapraz-link (örn. üçgenler).

---

## 4. Topical authority / iç-link stratejisi

- Hub → 5 konu + 14 alt-konu (merkezî dağıtım düğümü)
- Alt-konu sayfaları → hub + kardeş alt-konular + üst konu (mevcut breadcrumb/ilgili-içerik bloğu otomatik)
- Ana sayfa + footer → hub
- Sonuç: 8. sınıf/LGS kümesi tek bir otorite ağı olur (şu an dağınık ve hub'sız)

---

## 5. Sıralama ve risk

1. **Part B (alt-konu verisi)** önce — sıfır risk, hub'ı besler. Tek dosya (`altkonular.ts`) + otomatik sitemap/route.
2. **Part A (hub sayfası)** sonra — yeni route, düşük risk. Part B linklerini içerir.
3. Tek PR'da A+B birlikte gidebilir (frontend-ci lint+typecheck ile doğrulanır; lokalde node yok).

**Açık karar:** Hub URL'i `/lgs-matematik` mi `/calismalar/lgs` mi? (Öneri: `/lgs-matematik`.)

---

## 6. Beklenen çıktı

- +1 head-term hub sayfası ("LGS matematik" kümesi)
- +14 long-tail LGS alt-konu sayfası (~325 → ~339 sitemap URL)
- 8. sınıf/LGS için kapalı iç-link otorite ağı
- FAQPage + CollectionPage rich-result adayları
