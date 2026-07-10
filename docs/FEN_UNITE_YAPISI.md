# Fen Bilimleri — 2024 TYMM Ünite Yapısı (3–8. Sınıf)

> Kaynak: `knowledge_base/Fen/mufredat/fen_ogretim_programi_2024_TYMM.pdf`
> (234 sayfa, MEB 2024 onaylı, `2024programfen345678Onayli`). Çıkarım: PyMuPDF
> metin + FB kod doğrulaması. Tarih: 2026-07-10.
>
> **Kod formatı:** `FB.{sınıf}.{ünite}.{öğrenme_çıktısı}` (ör. `FB.5.1.1`).
> 8. sınıf üniteleri "bölüm" katmanı taşır → 4 seviyeli: `FB.8.{ünite}.{bölüm}.{çıktı}`.
> **Bu, sistemin ünite-bazlı yapısına (`app/data/units.py`) doğrudan hizalanır.**
>
> ⚠️ Öğrenme çıktısı sayıları **gösterge** (metin çıkarımından); Faz 1'de kazanım
> metinleri + tam kodlar elle doğrulanacak. Ünite adları ve sayıları FB koduyla teyitli.
>
> 📄 **Tam kazanım metinleri (182 öğrenme çıktısı):** `docs/FEN_KAZANIMLAR.md`.
> Kod yapısı: 3-4. sınıf 3 seviyeli (`FB.sınıf.ünite.çıktı`), 5-8. sınıf 4 seviyeli
> (`FB.sınıf.ünite.bölüm.çıktı`).

## Genel tablo
| Sınıf | Ünite sayısı | Kademe |
|---|---|---|
| 3 | 8 | İlkokul (Fen'in başlangıcı) |
| 4 | 8 | İlkokul |
| 5 | 7 | Ortaokul |
| 6 | 7 | Ortaokul |
| 7 | 7 | Ortaokul |
| 8 | 7 | Ortaokul (LGS) |

## 3. Sınıf (8 ünite)
1. Bilimsel Keşif Yolculuğu
2. Canlılar Dünyasına Yolculuk
3. Yer Bilimciler İş Başında
4. Maddeyi Tanıyalım, Karıştırıp Ayıralım
5. Hareketi Keşfediyorum
6. Yaşamımızı Kolaylaştıran Elektrik
7. Toprağı Tanıyorum, Tarımı Keşfediyorum
8. Canlıların Yaşam Alanlarına Yolculuk

## 4. Sınıf (8 ünite)
1. Bilime Yolculuk  *(FB.4.1 — "bilimin özellikleri", sayfa 51'de teyitli)*
2. Sağlıklı Besleniyorum
3. Dünya'mızı Keşfedelim
4. Maddenin Değişimi
5. Mıknatısı Keşfediyorum
6. Enerji Dedektifleri
7. Işığın Peşinde
8. Sürdürülebilir Şehirler ve Topluluklar

## 5. Sınıf (7 ünite)
1. Gökyüzündeki Komşularımız ve Biz  *(FB.5.1 — "Güneş, Dünya ve Ay", sayfa 16'da teyitli)*
2. Kuvveti Tanıyalım
3. Canlıların Yapısına Yolculuk
4. Işığın Dünyası
5. Maddenin Doğası
6. Yaşamımızdaki Elektrik
7. Sürdürülebilir Yaşam ve Geri Dönüşüm

## 6. Sınıf (7 ünite)
1. Güneş Sistemi ve Tutulmalar
2. Kuvvetin Etkisinde Hareket
3. Canlılarda Sistemler
4. Işığın Yansıması ve Renkler
5. Maddenin Ayırt Edici Özellikleri
6. Elektriğin İletimi ve Direnç
7. Sürdürülebilir Yaşam ve Etkileşim

## 7. Sınıf (7 ünite)
1. Uzay Çağı
2. Kuvvet ve Enerjiyi Keşfedelim
3. Vücudumuzdaki Sistemler
4. Işığın Kırılması ve Mercekler
5. Maddenin Doğasına Yolculuk
6. Elektriklenme
7. Sürdürülebilir Yaşam ve Enerji

## 8. Sınıf (7 ünite) — LGS kapsamı
1. Mevsimler ve İklim  *(FB.8.1 — "Mevsimlerin Oluşumu", sayfa 191'de teyitli)*
2. Yaşamı Kolaylaştıran Kuvvet
3. Yaşamın Gizemi
4. Sesin Dünyası
5. Periyodik Tablo ve Maddenin Etkileşimi
6. Elektriğin Yolculuğu
7. Sürdürülebilir Yaşam ve Madde Döngüleri

## Faz 1 için notlar
- Her sınıfta **7. ünite "Sürdürülebilir Yaşam ..."** ortak eksen (çevre/döngü);
  ünite adlandırmada bu tekrar korunmalı.
- Öğrenme çıktısı **metinleri + süreç bileşenleri** (a/b/c maddeleri) henüz
  çıkarılmadı → `scripts/derive_fen_curriculum.py` bunları FB kodlarıyla eşleyip
  `app/subjects/fen/curriculum.py` + units verisine dolduracak, elle doğrulanacak.
- Ünite adları TYMM 2024 ile birebir; **EBA örnek soru kitapçıkları eski müfredat
  ünitelerine göre** olabilir → çıkarımda ünite eşlemesi (crosswalk) gerekebilir
  (ör. eski "DNA ve Genetik Kod" → yeni "Yaşamın Gizemi").
