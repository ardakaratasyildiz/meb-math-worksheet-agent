# Sosyal (Sosyal Bilgiler ekseni) — Kaynak Künyesi

> Tarih: 2026-07-10. Tüm PDF'ler `knowledge_base/**/*.pdf` kuralıyla **gitignore'da**
> (repoya girmez; sadece üretilen JSON + ChromaDB versiyonlanır). Bu dosya (`.md`)
> izlenebilirlik için commit'lenir.
>
> **İlke:** Yalnızca **resmî / kamuya açık MEB kaynakları** indirildi (telifli özel
> yayınevi soru bankaları dahil edilmedi). Aşağıda otomatik indirilenler kaynak
> URL'siyle işaretlidir.

## Ders–sınıf haritası (Sosyal ekseni 3 dersten oluşur)
| Sınıf | Ders | Klasör |
|---|---|---|
| 1, 2, 3 | **Hayat Bilgisi** | `1.sinif/`, `2.sinif/`, `3.sinif/` |
| 4, 5, 6, 7 | **Sosyal Bilgiler** | `4.sinif/` … `7.sinif/` |
| 8 | **T.C. İnkılap Tarihi ve Atatürkçülük** | `8.sinif/` |

## 1. Ders kitapları (Track A — bağlam/kavram)

| Sınıf | Ders | Dosya | Kaynak | Not |
|---|---|---|---|---|
| 1 | Hayat Bilgisi | `1.sinif/hayat_bilgisi_1_1.pdf` (37.5M), `_1_2.pdf` (53.1M) | tymm.meb.gov.tr (TYMM 2024 yeni müfredat) | Resmî, güncel |
| 2 | Hayat Bilgisi | `2.sinif/hayat_bilgisi_2_1.pdf` (15.6M), `_2_2.pdf` (17.1M) | tymm.meb.gov.tr | Resmî, güncel |
| 3 | Hayat Bilgisi | `3.sinif/c1_hayat_bilgisi_3.pdf` (2.7M) | mufredat.meb.gov.tr TTKB/İlkokul/3 | Resmî. TYMM'de 3. sınıf henüz yok (500). |
| 4 | Sosyal Bilgiler | `4.sinif/c1_sosyal_bilgiler_4.pdf` (5.5M) | mufredat.meb.gov.tr TTKB/İlkokul/4 | Resmî. TYMM'de 4. sınıf henüz yok (500). |
| 5 | Sosyal Bilgiler | `5.sinif/sosyal_bilgiler_5_1.pdf` (38.3M), `_5_2.pdf` (43.5M) | tymm.meb.gov.tr (TYMM 2024) | Resmî, güncel |
| 6 | Sosyal Bilgiler | `6.sinif/sosyal_bilgiler_6_1.pdf` (87.8M), `_6_2.pdf` (30.5M) | tymm.meb.gov.tr | Resmî, güncel |
| 7 | Sosyal Bilgiler | `7.sinif/c1_sosyal_bilgiler_7.pdf` (3.1M) | mufredat.meb.gov.tr TTKB/Ortaokul/7 | Resmî. TYMM'de 7. sınıf henüz yok (500). |
| 8 | İnkılap Tarihi | `8.sinif/c1_TC_inkilap_8.pdf` (2.7M) | mufredat.meb.gov.tr TTKB/Ortaokul/8/İnkılap Tarihi | Resmî. TYMM'de 8. sınıf İnkılap ders kitabı henüz yok (500). |

Çalışan TYMM ders kitabı deseni: `https://tymm.meb.gov.tr/upload/kitap/{slug}_{sınıf}_{cilt}.pdf`
(`hayat_bilgisi_1_1`, `sosyal_bilgiler_5_1` …). TTKB fallback:
`https://mufredat.meb.gov.tr/Dosyalar/TTKB/{İlkokul|Ortaokul}/{sınıf}/{ders}/c1_...pdf`.

## 2. Örnek soru kitapçıkları (Track B — few-shot ALTIN kaynak)

### 2a. EBA ünitelendirilmiş kazanım testleri (ünite bazlı — EN DEĞERLİ, Fen deseniyle aynı)
`https://cdn.eba.gov.tr/yardimcikaynaklar/2022/11/kt/{sınıf}kt/{ders}/{ünite}.pdf`
(Sosyal Bilgiler ders slug = `sos`, İnkılap = `ink`):

| Sınıf | Ders | Konum | Adet | Cevap anahtarı |
|---|---|---|---|---|
| 5 | Sosyal Bilgiler | `ornek_sorular/5.sinif/kazanim_testi_unite_1..8.pdf` | 8 ünite | ⚠️ ayrı `sos_ca.pdf` yok (404) |
| 6 | Sosyal Bilgiler | `ornek_sorular/6.sinif/kazanim_testi_unite_1..8.pdf` | 8 ünite | ⚠️ ayrı CA yok |
| 7 | Sosyal Bilgiler | `ornek_sorular/7.sinif/kazanim_testi_unite_1,3..8.pdf` | 7 ünite | ⚠️ **ünite 2 kaynakta 404** (eksik); ayrı CA yok |
| 8 | İnkılap Tarihi | `ornek_sorular/8.sinif/kazanim_testi_unite_1..6.pdf` | 6 ünite | ✅ `kazanim_testi_cevap_anahtari.pdf` |

### 2b. EBA örnek soru kitapçıkları (sınav bazlı örnek sorular)
`.../2023/10/ornek1_1_1/`, `.../ornek1_2_1/`, `.../2025/03/ornek2/` (Sosyal = `sos{sınıf}`, İnkılap = `sos8`/`ita8`):

| Sınıf | Ders | Dosyalar |
|---|---|---|
| 5 | Sosyal Bilgiler | `sosyal_5_ornek_sinav1.pdf`, `_sinav2.pdf`, `_2025.pdf` |
| 6 | Sosyal Bilgiler | `sosyal_6_ornek_sinav1.pdf`, `_sinav2.pdf`, `_2025.pdf` |
| 7 | Sosyal Bilgiler | `sosyal_7_ornek_sinav1.pdf`, `_sinav2.pdf`, `_2025.pdf` |
| 8 | İnkılap Tarihi | `inkilap_8_ornek_sinav1.pdf` (`sos8`), `_sinav2.pdf` (`sos8`), `_2025.pdf` (`ita8`) |

### 2c. ÖDSGM beceri temelli sorular — cevap anahtarları (odsgm.meb.gov.tr, 2019-2020)
`https://odsgm.meb.gov.tr/kurslar/pdf/beceri/cvp/1920/{sınıf}_sos_ca.pdf`:
- `sorular/5_sos_beceri_cevap.pdf`, `6_...`, `7_...` (cevap tabloları).
- ⚠️ Soru PDF'leri (`destekmateryal/.../{sınıf}_sos_{n}.pdf`) **403** verdi (referer denendi, açılmadı) →
  Fen'deki durumla aynı: sadece cevap anahtarları elde.

## 3. Müfredat / kazanımlar (Faz 1 için kritik) — GÜNCEL 2024 TYMM baz alınır
> Sistem **ünite bazlı** (TYMM geliştirmesi, `app/data/units.py` / `units.json`).
> Sosyal ekseni müfredatı da TYMM ünite yapısına hizalanacak.

- `mufredat/hayat_bilgisi_ogretim_programi_2024_TYMM.pdf` (2.3M) — 2024 onaylı
  Hayat Bilgisi Dersi Öğretim Programı (1-3). Kaynak:
  `tymm.meb.gov.tr/upload/program/2024programhay123Onayli.pdf`.
- `mufredat/sosyal_bilgiler_ogretim_programi_2024_TYMM.pdf` (3.9M) — 2024 onaylı
  Sosyal Bilgiler Dersi Öğretim Programı (4-7). Kaynak:
  `tymm.meb.gov.tr/upload/program/2024programsos4567Onayli.pdf`.
- `mufredat/inkilap_tarihi_ogretim_programi_2024_TYMM.pdf` (2.0M) — 2024 onaylı
  T.C. İnkılap Tarihi ve Atatürkçülük Dersi Öğretim Programı (8). Kaynak:
  `tymm.meb.gov.tr/upload/program/2024programink8Onayli.pdf`.
- **Soru yazım kılavuzu:** MEB Bağlam Temelli Çoktan Seçmeli Soru Yazım Kılavuzu
  ders-bağımsızdır; zaten `knowledge_base/Fen/mufredat/coktan_secmeli_soru_yazim_kilavuzu.pdf`
  altında mevcut (tekrar indirilmedi). Kaynak:
  `tymm.meb.gov.tr/upload/kilavuz/coktan-secmeli-soru-yazim-kilavuzu.pdf`.
- Çıkarım kuralı: **TYMM programına uy** — konu bazlı değil, ünite bazlı etiketle
  (`app/data/units.py` deseni). Ünite/kazanım yapısı programlardan PyMuPDF ile türetilir.

## 4. Bilinen eksikler / yapılacaklar
1. **4. sınıf Sosyal Bilgiler örnek soru** — EBA'da ne kazanım testi (`4kt/sos` 404)
   ne de örnek soru booklet'i (`sos4` 404) yok. Few-shot için 4. sınıf boşta.
2. **Hayat Bilgisi (1-3) örnek soru** — EBA kazanım testi / örnek soru koleksiyonunda
   Hayat Bilgisi yok (`{1,2,3}kt/hb|hay|hayat` hepsi 404). İlkokul 1-3 için resmî
   ünitelendirilmiş örnek soru bulunamadı → few-shot yalnızca ders kitabı + programdan.
3. **7. sınıf Sosyal ünite 2 kazanım testi** — kaynakta 404 (7 ünite indi, 2. eksik).
4. **TYMM ders kitapları (3, 4, 7, 8)** — TYMM'de henüz yayınlanmadı (500); TTKB'nin
   önceki program kitapları kullanıldı. TYMM rollout ilerledikçe güncelle.
5. **ÖDSGM beceri temelli SORU PDF'leri (5/6/7)** — 403; sadece cevap anahtarları elde.
6. Sosyal ekseninde LGS = İnkılap 8; LGS Sosyal çıkmış sorular çok-dersli
   kitapçıklardan (Fen `8.sinif/lgs*.pdf`) vision ile ayrıştırılabilir (Faz 2-B).

## Özet
- **Toplam:** 60 PDF / ~381 MB (gitignore'da).
- **Ders kitabı (12):** Hayat Bilgisi 1-2 (TYMM, 2'şer cilt), 3 (TTKB); Sosyal Bilgiler
  5-6 (TYMM, 2'şer cilt), 4 & 7 (TTKB); İnkılap 8 (TTKB).
- **Örnek soru (42):** 29 EBA ünitelendirilmiş kazanım testi ünitesi (5-8) + 1 İnkılap CA
  + 12 EBA örnek soru booklet'i (5-8, 3'er). *(ornek_sorular klasörü = 42 dosya)*
- **ÖDSGM (3):** 5/6/7 Sosyal beceri temelli cevap anahtarı.
- **Müfredat (3):** Hayat Bilgisi / Sosyal Bilgiler / İnkılap 2024 onaylı TYMM programları.
- **En değerli few-shot kaynağı:** `ornek_sorular/` ünite bazlı `kazanim_testi_unite_*`
  (müfredat-hizalı, resmî) + örnek soru booklet'leri.
</content>
</invoke>
