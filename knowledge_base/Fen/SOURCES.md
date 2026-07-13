# Fen Bilimleri — Kaynak Künyesi

> Tarih: 2026-07-10. Tüm PDF'ler `knowledge_base/**/*.pdf` kuralıyla **gitignore'da**
> (repoya girmez; sadece üretilen JSON + ChromaDB versiyonlanır). Bu dosya (`.md`)
> izlenebilirlik için commit'lenir.
>
> **İlke:** Yalnızca **resmî / kamuya açık MEB kaynakları** indirildi (telifli özel
> yayınevi soru bankaları dahil edilmedi). Aşağıda otomatik indirilenler kaynak
> URL'siyle işaretlidir; kaynağı belirtilmeyenler **elle eklenmiştir (doğrulanmalı)**.

## 1. Ders kitapları (Track A — bağlam/kavram)

| Sınıf | Dosya | Kaynak | Not |
|---|---|---|---|
| 3 | `3.sinif/c1_fen-bilimleri-3.pdf` (8.1M) | mufredat.meb.gov.tr TTKB/İlkokul/3 | Resmî |
| 4 | `4.sinif/c1_fen-bilimleri-4.pdf` (6.9M) | mufredat.meb.gov.tr TTKB/İlkokul/4 | Resmî |
| 5 | `5.sinif/fen_bilimleri_5_1.pdf` (20M), `_5_2.pdf` (17M) | tymm.meb.gov.tr (Türkiye Yüzyılı Maarif Modeli, yeni müfredat) | Resmî, güncel |
| 6 | `6.sinif/fen_bilimleri_6_1.pdf` (19M), `_6_2.pdf` (13M) | tymm.meb.gov.tr | Resmî, güncel |
| 7 | `7.sinif/c1_fen-bilimleri-7.pdf` (2.0M), `fen-bilimleri-7-tam.pdf` (612K) | mufredat.meb.gov.tr TTKB/Ortaokul/7 | ⚠️ İkisi de küçük — **tam kitap olmayabilir**, doğrula. TYMM'de 7. sınıf henüz yok. |
| 8 | `8.sinif/c1_fen-bilimleri-8.pdf` (12M) | mufredat.meb.gov.tr TTKB/Ortaokul/8 | Resmî |

## 1b. ODSGM resmî çalışma kitapları — TAM içerik (2026-07-13 eklendi)
> Kademeli TYMM geçişinde 3-4-7-8 için TYMM ders kitabı HENÜZ yok (resmî
> tymm.meb.gov.tr sayfası doğrulandı: yalnız 5-6). mufredat.meb TTKB "c1"
> dosyaları KISMİ (~50 sf). Tam içerik için ODSGM resmî e-kitap/çalışma
> kitapları indirildi (cdn.eba.gov.tr, kamuya açık):

| Sınıf | Dosya | Sayfa | Kaynak |
|---|---|---|---|
| 3 | `3.sinif/3fen_calisma_kitabi_odsgm.pdf` (63M) | 200 | cdn.eba.gov.tr/.../ekitap/veri/3fen.pdf (ODSGM, meb.ai/xo3BL6) |
| 4 | `4.sinif/4fen_calisma_kitabi_odsgm.pdf` (75M) | 312 | cdn.eba.gov.tr/.../ekitap/veri/4fen.pdf (ODSGM, meb.ai/UFEBqqH) |
| 8 | `8.sinif/8fen_calisma_kitabi_odsgm.pdf` (63M) | 153 | cdn.eba.gov.tr/.../ekitap/lgs/8fen_ck2.pdf (ODSGM) |
| 8 | `8.sinif/lgs_fen_odsgm.pdf` (198M) | 392 | cdn.eba.gov.tr/.../ekitap/lgs/lgs2/lgs_fen_a.pdf (LGS Fen soru derlemesi) |

**Sonuç:** 3, 4, 5, 6, 8 → TAM içerik (TYMM ders kitabı ya da ODSGM çalışma kitabı).
**7. sınıf → hâlâ KISMİ:** tam ders/çalışma kitabı kamuya açık tek-PDF olarak
bulunamadı (mufredat c1 = 56 sf alıntı + 2024 TYMM programı + EBA ünite örnek
soruları + beceri cevap anahtarı ile kısmen kaplanıyor). LGS ağırlığı 8'de olduğu
için 7 boşluğu düşük riskli; ileride EBA viewer'dan (ogmmateryal) temin edilebilir.

## 2. Örnek soru kitapçıkları (Track B — few-shot ALTIN kaynak)
Resmî MEB/EBA **ünitelendirilmiş örnek sorular** (`cdn.eba.gov.tr/yardimcikaynaklar/2022/11/kt/{sınıf}kt/fen/`):

| Sınıf | Konum | Adet | Cevap anahtarı |
|---|---|---|---|
| 5 | `ornek_sorular/5.sinif/unite_1..9.pdf` | 9 ünite | ⚠️ ayrı CA inmedi (soru PDF'i içinde olabilir) |
| 6 | `ornek_sorular/6.sinif/unite_1..9.pdf` | 9 ünite | ⚠️ ayrı CA inmedi |
| 7 | `ornek_sorular/7.sinif/unite_1..9.pdf` | 9 ünite | ⚠️ ayrı CA inmedi |
| 8 | `ornek_sorular/8.sinif/unite_1..7.pdf` (22–32M) | 7 ünite | ✅ `cevap_anahtari.pdf` |

ÖDSGM **beceri temelli sorular — cevap anahtarları** (odsgm.meb.gov.tr, 2019-2020):
- `sorular/5_fen_beceri_cevap.pdf`, `6_...`, `7_...` (soru PDF'leri ayrı bulunamadı; cevap tabloları elde).

## 3. Müfredat / kazanımlar (Faz 1 için kritik) — GÜNCEL 2024 TYMM baz alınır
> ⚠️ **2018 programı BAZ ALINMAZ (çok eski, kaldırıldı).** Sistem artık **ünite
> bazlı** (dünkü TYMM geliştirmesi, commit 9f32892 — `app/data/units.py` /
> `units.json`). Fen müfredatı da TYMM ünite yapısına hizalanacak.

- `mufredat/fen_ogretim_programi_2024_TYMM.pdf` (3.6M) — **2024 onaylı** Fen
  Bilimleri Dersi Öğretim Programı (3-8, ünite bazlı). Kaynak:
  `tymm.meb.gov.tr/upload/program/2024programfen345678Onayli.pdf`. **Faz 1'de
  ünite/kazanım yapısı buradan türetilecek** (PyMuPDF ile metin çıkarımı).
- `mufredat/coktan_secmeli_soru_yazim_kilavuzu.pdf` (11M) — MEB **Bağlam Temelli
  Çoktan Seçmeli Soru Yazım Kılavuzu** (TYMM). Kaynak:
  `tymm.meb.gov.tr/upload/kilavuz/coktan-secmeli-soru-yazim-kilavuzu.pdf`.
  Fen prompt + critic kurallarının (soru yazım standardı, çeldirici tasarımı)
  temeli. Üretim kalitesi için değerli.
- Çıkarım kuralı: **ÖSYM/ÖDSGM ünite yapısına ve TYMM programına uy** —
  konu bazlı değil, ünite bazlı etiketle (`app/data/units.py` deseni).

## 4. Elle eklenmiş / önceden var olan (DOĞRULANMALI)
Aşağıdakiler otomatik indirilmedi; klasörde mevcuttu (kullanıcı ekledi). İçerik ve
kaynağı **kullanım öncesi teyit edilmeli**:
- `8.sinif/lgs1..15.pdf`, `lgsornek1..3.pdf` — LGS deneme kitapçıkları. ⚠️ Bunlar
  matematik projesindeki `knowledge_base/8.Sınıf/` ile **aynı dosyalar olabilir**
  (çok-dersli kitapçık mı, yoksa math-only mu → teyit et; `GRADE8_LGS_PLAN.md`).
- `5.sinif/*Kazanım Tarama Testi*.pdf`, `5fen_5.pdf` — kazanım tarama testleri.
- Hex-isimli dosyalar (`5.sinif/28e12adde7.pdf`, `6.sinif/3f3edcba7e.pdf`,
  `8.sinif/0f1f55cd43.pdf` vb.) — 3. parti sitelerden indirilmiş olabilir →
  **telif ve kaynak belirsiz**, ingest öncesi gözden geçir.

## 5. Bilinen eksikler / yapılacaklar
1. **7. sınıf tam ders kitabı** — indirilenler küçük; tam sürüm gerekebilir.
2. **5/6/7 örnek soru cevap anahtarları** — ünite PDF'lerinin içinde mi kontrol et,
   değilse ayrı bul.
3. **Beceri temelli soru PDF'leri** (5/6/7) — sadece cevap anahtarı elde; soru
   kitapçıkları ayrı temin edilebilir.
4. **LGS Fen çıkmış sorular (branş derlemesi)** — çok-dersli LGS kitapçıklarından
   Fen bölümü vision ile ayrıştırılacak (Faz 2-B).
5. Elle eklenen hex/3. parti dosyaların telif teyidi.

## Özet
- **Toplam:** 83 PDF / ~435 MB (gitignore'da).
- **Resmî indirilenler:** 5-6 ders kitabı (tymm), 3-4-7-8 ders kitabı (mufredat),
  32 EBA ünite örnek soru kitapçığı (5-8), 3 ÖDSGM cevap anahtarı, 1 öğretim programı.
- **En değerli few-shot kaynağı:** `ornek_sorular/` (ünite bazlı, müfredat-hizalı,
  resmî) + `8.sinif/` LGS kitapçıkları (teyit sonrası).
