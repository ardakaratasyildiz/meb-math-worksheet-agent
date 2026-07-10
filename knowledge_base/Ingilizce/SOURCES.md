# İngilizce — Kaynak Künyesi

> Tarih: 2026-07-10. Tüm PDF'ler `knowledge_base/**/*.pdf` kuralıyla **gitignore'da**
> (repoya girmez; sadece üretilen JSON + ChromaDB versiyonlanır). Bu dosya (`.md`)
> izlenebilirlik için commit'lenir.
>
> **İlke:** Yalnızca **resmî / kamuya açık MEB kaynakları** indirildi (telifli özel
> yayınevi soru bankaları dahil edilmedi). İngilizce Türkiye'de **2. sınıfta başlar**
> (2-8 arası). Aşağıda otomatik indirilenler kaynak URL'siyle işaretlidir.
>
> **⚠️ TYMM 2024 açılımı kısmî:** İngilizce ders kitapları TYMM'de yalnızca
> **2, 5, 6, 7** için yayında. 3, 4, 8 henüz yok (aşağıda eksikler).

## 1. Ders kitapları (Track A — bağlam/kavram)
Kaynak: `tymm.meb.gov.tr/upload/kitap/...` (Türkiye Yüzyılı Maarif Modeli, yeni müfredat).
Sayfa: `tymm.meb.gov.tr/ders-kitaplari/temel-egitim`.

| Sınıf | Dosya | Kaynak dosya adı | Not |
|---|---|---|---|
| 2 | `2.sinif/ingilizce_2_ders_kitabi.pdf` (250M) | `ingilizce-2-sinif-ders-kitabi.pdf` | ⚠️ **TRUNCATED** — CDN 262160384 baytta kesiyor, `%%EOF` yok, tam değil. Erken üniteler okunur, sonu eksik. |
| 2 | `2.sinif/ingilizce_2_calisma_kitabi.pdf` (144M) | `ingilizce-2-sinif-calisma-kitabi.pdf` | ✅ Tam (çalışma kitabı) |
| 5 | `5.sinif/ingilizce_5_ders_kitabi.pdf` (210M) | `ingilizce-5-sinif-ders-kitabi.pdf` | ✅ Tam |
| 5 | `5.sinif/ingilizce_5_calisma_kitabi.pdf` (79M) | `ingilizce-5-sinif-calisma-kitabi.pdf` | ✅ Tam |
| 5 | `5.sinif/multi_english_5_ders_2.pdf` (230M) | `multi-english-5-ders-kitabi-2.pdf` | ✅ Tam (Multi-English serisi, cilt 2) |
| 5 | `5.sinif/multi_english_5_workbook_1.pdf` (90M) | `multi-english-5-work-book-1.pdf` | ✅ Tam |
| 5 | `5.sinif/multi_english_5_workbook_2.pdf` (79M) | `multi-english-5-work-book-2.pdf` | ✅ Tam |
| 5 | `5.sinif/multi_english_5_ders_1.pdf` (250M) | `multi-english-5-ders-kitabi-1.pdf` | ⚠️ **TRUNCATED** — aynı 262160384 bayt kesme, `%%EOF` yok. Multi-English serisi cilt 1 eksik; ancak grade 5 diğer 5 kitapla zaten kapsanıyor. |
| 6 | `6.sinif/multi_english_6_ders_kitabi.pdf` (164M) | `multi-english-6-ders-kitabi.pdf` | ✅ Tam |
| 6 | `6.sinif/multi_english_6_workbook.pdf` (31M) | `multi-english-6-work-book.pdf` | ✅ Tam |
| 7 | `7.sinif/multi_english_7_ders_kitabi.pdf` (158M) | `multi-english-7-ders-kitabi.pdf` | ✅ Tam |
| 7 | `7.sinif/multi_english_7_workbook.pdf` (77M) | `multi-english-7-work-book.pdf` | ✅ Tam |

> Not: Bu kitaplar görsel/etkileşimli dil kitapları olduğu için çok büyük (30–250M).
> İki dosya (`ingilizce_2_ders_kitabi`, `multi_english_5_ders_1`) MEB CDN'inde tam olarak
> **262160384 baytta** kesilmiş (origin sorunu; `Content-Range` toplamı da bu değeri
> veriyor, range ile devamı **alınamıyor** → kaynakta eksik). Yine de ~250M gerçek içerik
> taşıdıkları için silinmedi; PyMuPDF xref onarımı ile erken sayfalar çıkarılabilir.

## 2. Örnek soru kitapçıkları (Track B — few-shot ALTIN kaynak)
Resmî MEB/EBA **ünite bazlı kazanım/örnek soruları**
(`cdn.eba.gov.tr/yardimcikaynaklar/2022/11/kt/{sınıf}kt/ing/{N}.pdf`).
Kaynak sayfa (8. sınıf): `odsgm.meb.gov.tr/www/8-sinif-ingilizce-unitelendirilmis-ornek-sorular/icerik/673`.

| Sınıf | Konum | Adet | Cevap anahtarı |
|---|---|---|---|
| 5 | `ornek_sorular/5.sinif/unite_1..12.pdf` | 12 | ⚠️ ayrı CA yok (soru PDF'i içinde olabilir) |
| 6 | `ornek_sorular/6.sinif/unite_1..12.pdf` | 12 | ⚠️ ayrı CA yok |
| 7 | `ornek_sorular/7.sinif/unite_1..12.pdf` | 12 | ⚠️ ayrı CA yok |
| 8 | `ornek_sorular/8.sinif/unite_1..10.pdf` | 10 | ✅ `cevap_anahtari.pdf` (`ing_ca.pdf`) |

> `unite_N.pdf` isimleri EBA kaynak `{N}.pdf` dosyalarına birebir karşılık gelir
> (Fen'deki `unite_N` konvansiyonuyla hizalı). Bunlar müfredat-hizalı, resmî ve
> **en değerli few-shot kaynağı**. 2, 3, 4. sınıf için EBA'da İngilizce kazanım
> testi **yok** (404).

## 3. ÖDSGM beceri temelli sorular (Track B — ek few-shot)
`cdn.eba.gov.tr/yardimcikaynaklar/2022/01/odsgm/beceri/2223/ing/{sınıf}_ing_{N}.pdf`
(2022-2023, beceri temelli soru kitapçıkları). Kaynak sayfa:
`odsgm.meb.gov.tr/www/{6,7}-sinif-beceri-temelli-testler/icerik/{489,490}`.

| Sınıf | Konum | Adet |
|---|---|---|
| 5 | `sorular/5.sinif/beceri_1..10.pdf` | 10 |
| 6 | `sorular/6.sinif/beceri_1..10.pdf` | 10 |
| 7 | `sorular/7.sinif/beceri_1..10.pdf` | 10 |

> 8. sınıf bu yolda **yok** (8 için ünitelendirilmiş örnek sorular — §2 — kullanılır).
> Bunlar okuma/dinleme-parçalı, beceri odaklı tam soru kitapçıklarıdır (2–18M).

## 4. Müfredat / kazanımlar (Faz 1 için kritik) — GÜNCEL 2024 TYMM baz alınır
> ⚠️ **2018 programı BAZ ALINMAZ (kaldırıldı).** Sistem **ünite bazlı**
> (`app/data/units.py` / `units.json`). İngilizce müfredatı da TYMM ünite/tema
> yapısına hizalanacak (Fen deseni, commit f4e3a1d).

- `mufredat/ingilizce_ogretim_programi_2024_TYMM.pdf` (11.6M) — **2024 İngilizce
  Dersi Öğretim Programı (2-8)**. Kaynak:
  `tymm.meb.gov.tr/upload/program/ingilizce-dersi-2-8.pdf`. **Faz 1'de ünite/tema
  yapısı buradan türetilecek** (PyMuPDF ile metin çıkarımı).
  > Not: İngilizce program dosyası Fen'deki `2024program...Onayli.pdf` desenini
  > kullanmaz; slug tabanlı `ingilizce-dersi-2-8.pdf` adıyla yayınlanmış.
- `mufredat/ingilizce_ogretim_programi_kilavuzu.pdf` (8.7M) — **İngilizce Dersi
  Öğretim Programı Tanıtım Kılavuzu** (TYMM). Kaynak:
  `tymm.meb.gov.tr/upload/kilavuz/ingilizce-ogretim-programi-kilavuzu.pdf`.
  Program felsefesi/yaklaşımı + beceri çerçevesi.
- `mufredat/coktan_secmeli_soru_yazim_kilavuzu.pdf` (10M) — MEB **Bağlam Temelli
  Çoktan Seçmeli Soru Yazım Kılavuzu** (TYMM, ders-bağımsız; Fen ile aynı dosya).
  Kaynak: `tymm.meb.gov.tr/upload/kilavuz/coktan-secmeli-soru-yazim-kilavuzu.pdf`.
  Prompt + critic kurallarının (soru yazım standardı, çeldirici tasarımı) temeli.
- Çıkarım kuralı: **TYMM programına uy** — konu değil, **ünite/tema** bazlı etiketle.

## 5. Bilinen eksikler / yapılacaklar
1. **3, 4, 8. sınıf ders kitapları** — TYMM'de İngilizce için henüz **yok** (2024
   açılımı 2/5/6/7 ile sınırlı; 3, 4, 8 sonraki dalgada gelecek). TTKB
   `mufredat.meb.gov.tr` üzerinde eski müfredat kitapları aranabilir ama TYMM ünite
   yapısına hizasız olur — Faz 1 için düşük öncelik.
2. **2 truncated ders kitabı** (`ingilizce_2_ders_kitabi`, `multi_english_5_ders_1`)
   — MEB CDN origin'de 250M'de kesik. Tekrar indirmek düzeltmez (server toplamı da
   kesik veriyor). Alternatif: EBA etkileşimli kitap sürümü veya bölünmüş PDF ara.
3. **5/6/7 örnek soru cevap anahtarları** — ayrı CA inmedi; ünite PDF'lerinin içinde
   mi kontrol et, değilse ayrı bul.
4. **3, 4. sınıf örnek soru / beceri sorusu** — EBA'da İngilizce için yok; ilkokul
   İngilizcesi için resmî ünite bazlı soru havuzu sınırlı.
5. **8. sınıf beceri temelli** — ÖDSGM beceri yolunda 8 yok; §2'deki ünitelendirilmiş
   örnek sorular (LGS-hizalı) kullanılır.

## Özet
- **Toplam:** 92 PDF / ~2134 MB (gitignore'da).
- **Ders kitapları (12):** TYMM 2/5/6/7 (2 dosya truncated, 10 tam).
- **Örnek sorular (47):** EBA ünite bazlı 5-8 (5/6/7 = 12'şer, 8 = 10 + cevap anahtarı).
- **ÖDSGM beceri temelli (30):** 5/6/7 = 10'ar tam soru kitapçığı.
- **Müfredat (3):** 2024 İngilizce öğretim programı (2-8) + tanıtım kılavuzu + çoktan
  seçmeli soru yazım kılavuzu.
- **En değerli few-shot kaynağı:** `ornek_sorular/` (ünite bazlı, müfredat-hizalı,
  resmî) + `sorular/` (beceri temelli, okuma/dinleme parçalı).
- **En kritik Faz 1 girdisi:** `mufredat/ingilizce_ogretim_programi_2024_TYMM.pdf`
  (ünite/tema + kazanım çıkarımı).
