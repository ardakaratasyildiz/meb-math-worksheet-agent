# Türkçe — Kaynak Künyesi

> Tarih: 2026-07-10. Tüm PDF'ler `knowledge_base/**/*.pdf` kuralıyla **gitignore'da**
> (repoya girmez; sadece üretilen JSON + ChromaDB versiyonlanır). Bu dosya (`.md`)
> izlenebilirlik için commit'lenir.
>
> **İlke:** Yalnızca **resmî / kamuya açık MEB kaynakları** indirildi (telifli özel
> yayınevi soru bankaları dahil edilmedi). Aşağıda otomatik indirilenler kaynak
> URL'siyle işaretlidir. Sürüm Fen Bilimleri kaynak playbook'unun birebir Türkçe
> uyarlamasıdır (aynı CDN desenleri, `turk`/`turkce` slug'ıyla).

## 1. Ders kitapları (Track A — bağlam/kavram)

| Sınıf | Dosya | Kaynak | Not |
|---|---|---|---|
| 1 | `1.sinif/turkce_1_1.pdf` (141M), `turkce_1_2.pdf` (91M) | tymm.meb.gov.tr `upload/kitap/turkce_1_1.pdf` / `_1_2.pdf` | ✅ Resmî, güncel (2024 TYMM / Türkiye Yüzyılı Maarif Modeli) |
| 2 | `2.sinif/turkce_2_1.pdf` (35M), `turkce_2_2.pdf` (29M) | tymm.meb.gov.tr `upload/kitap/turkce_2_1.pdf` / `_2_2.pdf` | ✅ Resmî, güncel (TYMM) |
| 3 | `3.sinif/c1_turkce_3.pdf` (1.3M) | mufredat.meb.gov.tr `Dosyalar/TTKB/İlkokul/3/Türkçe/c1_turkce_3.pdf` | ⚠️ Eski program (TTKB); **küçük — tam kitap olmayabilir, doğrula**. TYMM'de 3. sınıf kitabı henüz yok. |
| 4 | `4.sinif/c1_turkce_4.pdf` (2.6M) | mufredat.meb.gov.tr `Dosyalar/TTKB/İlkokul/4/Türkçe/c1_turkce_4.pdf` | ⚠️ Eski program (TTKB). TYMM'de 4. sınıf kitabı henüz yok. |
| 5 | `5.sinif/turkce_5_1.pdf` (104M), `turkce_5_2.pdf` (68M) | tymm.meb.gov.tr `upload/kitap/turkce_5_1.pdf` / `_5_2.pdf` | ✅ Resmî, güncel (TYMM) |
| 6 | `6.sinif/turkce_6_1.pdf` (35M), `turkce_6_2.pdf` (29M) | tymm.meb.gov.tr `upload/kitap/turkce_6_1.pdf` / `_6_2.pdf` | ✅ Resmî, güncel (TYMM) |
| 7 | `7.sinif/c1_turkce_7.pdf` (5.3M) | mufredat.meb.gov.tr `Dosyalar/TTKB/Ortaokul/7/Türkçe/c1_turkce_7.pdf` | ⚠️ Eski program (TTKB). TYMM'de 7. sınıf kitabı henüz yok. |
| 8 | `8.sinif/c1_turkce_8.pdf` (2.0M) | mufredat.meb.gov.tr `Dosyalar/TTKB/Ortaokul/8/Türkçe/c1_turkce_8.pdf` | ⚠️ Eski program (TTKB); küçük. TYMM'de 8. sınıf kitabı henüz yok. |

> Not: TYMM `upload/kitap/turkce_{sınıf}_{cilt}.pdf` deseni 2026-07 itibarıyla
> yalnız **1, 2, 5, 6** sınıflarında yanıt veriyor (2024-25 birinci dalga). 3, 4, 7, 8
> için desen 500 döndü → bu sınıflarda **TTKB (mufredat.meb.gov.tr) eski program
> ders kitabı** yedek olarak alındı (Fen'de de aynı strateji uygulandı).

## 2. Örnek soru kitapçıkları (Track B — few-shot ALTIN kaynak)
Resmî MEB/EBA **kazanım testleri** (`cdn.eba.gov.tr/yardimcikaynaklar/2022/11/kt/{sınıf}kt/turk/{n}.pdf`).
Dosyalar yerelde `ornek_sorular/{sınıf}.sinif/kt_{n}.pdf` olarak adlandırıldı:

| Sınıf | Konum | Adet | Cevap anahtarı |
|---|---|---|---|
| 5 | `ornek_sorular/5.sinif/kt_*.pdf` | 28 test | ⚠️ ayrı CA yok (soru PDF'i içinde olabilir) |
| 6 | `ornek_sorular/6.sinif/kt_*.pdf` | 28 test | ⚠️ ayrı CA yok |
| 7 | `ornek_sorular/7.sinif/kt_*.pdf` | 27 test | ⚠️ ayrı CA yok |
| 8 | `ornek_sorular/8.sinif/kt_*.pdf` | 8 test | ✅ `turk_ca.pdf` (`8kt/turk/turk_ca.pdf`) |

> Not: 1-4. sınıflarda `{sınıf}kt/turk/` dizini yok (EBA kazanım testleri 5. sınıftan
> başlıyor). 5/6/7 için 24+4 aralığında tekil dosyalar (25-28 boş), 8 için yalnız 1-8.

ÖDSGM **beceri temelli sorular** (`cdn.eba.gov.tr/yardimcikaynaklar/2022/01/odsgm/beceri/2223/turk/{sınıf}_turkce_{n}.pdf`).
Dosyalar yerelde `sorular/{sınıf}_turkce_beceri_{n}.pdf` + `..._ca.pdf`:

| Sınıf | Konum | Adet | Cevap anahtarı |
|---|---|---|---|
| 5 | `sorular/5_turkce_beceri_1..6.pdf` | 6 kitapçık | ✅ `5_turkce_beceri_ca.pdf` |
| 6 | `sorular/6_turkce_beceri_1..8.pdf` | 8 kitapçık | ✅ `6_turkce_beceri_ca.pdf` |
| 7 | `sorular/7_turkce_beceri_1..8.pdf` | 8 kitapçık | ✅ `7_turkce_beceri_ca.pdf` |
| 8 | — | yok | ⚠️ `2223/turk` yolunda 8. sınıf beceri yok |

## 3. Müfredat / kazanımlar (Faz 1 için kritik) — GÜNCEL 2024 TYMM baz alınır
> ⚠️ **2018/2019 programı BAZ ALINMAZ.** Sistem **ünite bazlı** (TYMM geliştirmesi,
> commit 9f32892 — `app/data/units.py` / `units.json`). Türkçe müfredatı da TYMM ünite
> (tema) yapısına hizalanacak. Türkçe programı Fen'den farklı olarak **1-4** ve **5-8**
> olmak üzere iki ayrı PDF halinde yayımlanmış.

- `mufredat/turkce_ogretim_programi_2024_TYMM_ilkokul_1-4.pdf` (3.9M) — **2024 onaylı**
  İlkokul Türkçe Dersi Öğretim Programı (1-4). Kaynak:
  `tymm.meb.gov.tr/upload/program/2024programtur1234Onayli.pdf`. **Faz 1'de 1-4 ünite/tema
  yapısı buradan türetilecek** (PyMuPDF ile metin çıkarımı).
- `mufredat/turkce_ogretim_programi_2024_TYMM_ortaokul_5-8.pdf` (8.4M) — **2024 onaylı**
  Ortaokul Türkçe Dersi Öğretim Programı (5-8). Kaynak:
  `tymm.meb.gov.tr/upload/program/2024programtur5678Onayli.pdf`. **Faz 1'de 5-8 ünite/tema
  yapısı buradan türetilecek.**
- `mufredat/coktan_secmeli_soru_yazim_kilavuzu.pdf` (10M) — MEB **Bağlam Temelli
  Çoktan Seçmeli Soru Yazım Kılavuzu** (TYMM, ders-bağımsız). Kaynak:
  `tymm.meb.gov.tr/upload/kilavuz/coktan-secmeli-soru-yazim-kilavuzu.pdf`.
  Prompt + critic kurallarının (soru yazım standardı, çeldirici tasarımı) temeli;
  Fen'deki ile aynı dosya.
- Çıkarım kuralı: **TYMM programına ve EBA ünite yapısına uy** — konu bazlı değil,
  ünite/tema bazlı etiketle (`app/data/units.py` deseni).

## 4. Bilinen eksikler / yapılacaklar
1. **TYMM güncel ders kitabı 3, 4, 7, 8** — 2026-07 itibarıyla `upload/kitap/` deseninde
   yok; şu an TTKB eski program kitapları kullanılıyor. Rollout genişledikçe TYMM sürümleri
   ile değiştirilmeli.
2. **3. ve 8. sınıf TTKB kitapları küçük** (1.3M / 2.0M) — tam kitap mı yoksa özet/kritik
   konu mu, ingest öncesi doğrula.
3. **EBA kazanım testi cevap anahtarları (5, 6, 7)** — ayrı `turk_ca.pdf` yalnız 8. sınıfta
   bulundu; 5/6/7 için CA soru PDF'lerinin içinde mi kontrol et.
4. **1-4. sınıf örnek soru/kazanım testi** — EBA'da yok (kazanım testleri 5'ten başlıyor);
   ilkokul için few-shot havuzu ders kitabı etkinliklerinden türetilecek.
5. **8. sınıf ÖDSGM beceri temelli sorular** — `2223/turk` yolunda yok; farklı yıl/yol
   (ör. LGS örnek soru kitapçıkları, odsgm.meb.gov.tr) ile ayrıca aranabilir.
6. **8. sınıf EBA kazanım testi az** (yalnız 8 test; 5/6/7 ~28) — LGS odaklı ek kaynak
   (ÖDSGM örnek sorular / çıkmış LGS Türkçe) ileride eklenebilir.

## Özet
- **Toplam:** 132 PDF / ~695 MB (gitignore'da).
- **Resmî indirilenler:** 1-2-5-6 ders kitabı (TYMM, 2 cilt/sınıf = 8 dosya),
  3-4-7-8 ders kitabı (TTKB mufredat = 4 dosya), 91 EBA kazanım testi (5-8) + 1 CA,
  22 ÖDSGM beceri temelli kitapçık (5-7) + 3 CA, 2 öğretim programı (1-4 & 5-8) + 1 soru
  yazım kılavuzu.
- **En değerli few-shot kaynağı:** `ornek_sorular/` (EBA kazanım testleri, müfredat-hizalı,
  resmî) + `sorular/` (ÖDSGM beceri temelli sorular, cevap anahtarlı 5-7).
