# 🔎 Faz 0 Keşif Raporu — MEB Ders Kitabı PDF'leri

> **Durum:** Faz 0 tamamlandı. Bu rapor 11 PDF'in gerçek içeriğini, çıkarılabilirliğini ve planın revize edilen bölümlerini içerir.
>
> **Çıktı dosyası:** `knowledge_base/processed/discovery_report.json` (makine-okunabilir)
> **Önceki plan:** `docs/RAG_PDF_PLAN.md`

---

## 🎯 Executive Summary

**İyi haberler:**
- 11 PDF'in **9'u metin gömülü** (OCR gerekmez, hızlı ve ucuz extraction)
- **6. sınıf kitaplarında otomatik outline** var (27+19 giriş) — kazanım eşleme için **altın kaynak**
- Örnek / Etkinlik başlıkları regex ile yakalanabiliyor (özellikle 5. sınıf'ta zengin)
- Matematik sembolleri ve sayılar düzgün çıkıyor (derinden test edildi)

**Dikkat edilmesi gerekenler:**
- **3. ve 4. sınıf ders kitapları TARANMIŞ** → OCR gerekli (+4-8 saat, kalite riski)
- **Ciddi müfredat farkı:** Yeni MEB 2024 müfredatı (Çarpanlar, Asal sayılar, Olasılık, İstatistik, Algoritma) bizim `curriculum.py`'de yok
- "Matematik Ders Kitabı-MEB.pdf" aslında **7. sınıf test/kazanım kavrama kitabı** — ders kitabı değil
- Hiçbir PDF'in metadata'sında title yok, İçindekiler otomatik çıkarımı 6. sınıf hariç başarısız

**Sonuç:** Full RAG uygulanabilir, ancak tahmini süre **1.5-2 gün** ve maliyet **$15-25** — ilk tahminimin üst sınırında. Müfredat farkı yönetimi için önemli bir karar gerekiyor (aşağıda).

---

## 📁 PDF Envanteri ve Durum

| Dosya | Sınıf | Sayfa | Extraction | Outline | TOC sayfası | Ort. metin/sayfa | Not |
|-------|-------|-------|------------|---------|--------------|------------------|-----|
| `matematik_1_1.pdf` | 1 | 193 | ✅ Metin | 0 | 2 | 226 char | 1. dönem |
| `matematik_1_2.pdf` | 1 | 161 | ✅ Metin | 0 | 3 | 388 char | 2. dönem |
| `matematik_2_1.pdf` | 2 | 182 | ✅ Metin | 0 | 1 | 487 char | |
| `matematik_2_2.pdf` | 2 | 203 | ✅ Metin | 0 | 5 | 1.055 char | |
| `3.Sinif-Matematik-Ders-Kitabi-MEB-pdf.pdf` | 3 | 288 | **❌ OCR gerek** | 0 | 0 | 0 char | Taranmış |
| `4.Sinif-Matematik-Ders-Kitabi-MEB-pdf.pdf` | 4 | 303 | **❌ OCR gerek** | 0 | 3 | 0 char | Taranmış |
| `matematik_5_1.pdf` | 5 | 171 | ✅ Metin | 0 | 4 | 1.001 char | **Örnek yoğunluğu yüksek** |
| `matematik_5_2.pdf` | 5 | 189 | ✅ Metin | 0 | 5 | 1.416 char | Etkinlik zengin |
| `matematik_6_1.pdf` | 6 | 222 | ✅ Metin | **27** 🥇 | 3 | 1.180 char | Otomatik TOC altın kaynak |
| `matematik_6_2.pdf` | 6 | 166 | ✅ Metin | **19** 🥇 | 3 | 1.120 char | Otomatik TOC var |
| `Matematik Ders Kitabı-MEB.pdf` | 7 | 270 | ✅ Metin | 0 | 5 | 1.351 char | **Test kitabı, ders kitabı değil** |

**Toplam:** 2.346 sayfa | ~600 MB | 9 metin gömülü + 2 taranmış

**Tahmin:** Metin gömülü PDF'lerden **~1.800 sayfadan 6.000-9.000 chunk** çıkar (sayfa başına 3-5 ortalama).

---

## 🧭 Kritik Bulgu #1 — Müfredat Farkı

6. sınıf PDF'lerinin otomatik outline'ında **bizim `curriculum.py`'de yer almayan konular** var. Bu yeni MEB 2024 müfredatının bir parçası:

### 6. Sınıf 1. Kitap Outline (Özetle)

| Sayfa | Bölüm | Bizde Var mı? |
|-------|-------|---------------|
| 16-21 | **Çarpanlar** | ❌ YOK |
| 21-26 | **Katlar** | ❌ YOK |
| 27-37 | **Kalansız Bölünebilme** (OBEB-OKEK) | ❌ YOK |
| 38-49 | **Asal Sayılar** | ❌ YOK |
| 49-56 | Ortak Kat / Ortak Bölen | ❌ YOK |
| 64-114 | **İstatistiksel Araştırma + Kategorik Veri** | ❌ YOK |
| 124-141 | Ondalık Gösterim, Kesir ile Bölme | ✅ M.6.2.x |
| 141-193 | Uzunluk Ölçme, Gerçek Yaşam | ✅ M.6.4.x |
| 200-215 | **Olasılık** | ❌ YOK |

### 6. Sınıf 2. Kitap Outline

| Sayfa | Bölüm | Bizde Var mı? |
|-------|-------|---------------|
| 21-53 | Doğrular, Açılar, Üçgen Açıları, Dörtgenler | ✅ M.6.3.x |
| 58-73 | **Bilinmeyen Nicelikler** (cebirsel ifadeler) | ✅ M.6.5.x |
| 77-84 | **Örüntüler** | ✅ (kısmen M.6.5.x) |
| 84-96 | **Algoritma** | ❌ YOK |
| 102-140 | Alan Ölçme, Paralelkenar, Üçgen Alanı | ✅ M.6.3.x |
| 142-157 | Çember, Merkez Açı | ✅ kısmen (bizde M.7.3.x) |

### Etkileri

- **Yeni MEB 2024 müfredatı ~%40-50 farklı:** Çarpanlar, Asal sayılar, İstatistik, Olasılık, Algoritma gibi önemli konular eklenmiş
- **Bizim `curriculum.py` ~2020 müfredatına yakın**
- PDF'leri bire bir kullanırsak, kazanım kodu eşlemesinde **%50'ye yakın chunk'ı atlamak zorunda kalırız** veya `kazanim_kod=null` bırakırız (retriever yine `grade` + `topic_id` ile bulabilir)

### Üç Seçenek

| Seçenek | Ne yapılır | Maliyet | Risk |
|---------|-----------|---------|------|
| **A — Sadece eşleşen kısımları kullan** | Müfredatımızdaki kazanımlara karşılık gelen sayfaları extract et, gerisini atla | +0 saat | Veri kaybı ~%40-50 |
| **B — `curriculum.py`'i genişlet** | Yeni müfredatla uyumlu hale getir, eksik kazanımları ekle | +4-6 saat manuel + LLM yardımlı | Mevcut MVP kalibrasyonu etkilenir; tüm sentetik corpus güncellenmeli |
| **C — Hibrit** | Eşleşenleri otomatik eşle + eşleşmeyenleri `content_type="curriculum_expansion"` etiketiyle sakla, ileride kullanım için | +1-2 saat | Storage büyür ama esneklik korunur |

**Önerim: C (Hibrit)** — Şu an `curriculum.py`'imize sadık kalalım, eşleşmeyen içeriği de store'a yazıp metadata ile işaretleyelim. Kullanmak istersek geleceğe açık kalır.

---

## 🧭 Kritik Bulgu #2 — Taranmış PDF'ler (3. ve 4. sınıf)

Her iki PDF'te her sayfa 1 image, 0 metin. OCR şart.

### OCR Seçenekleri

| Seçenek | Süre | Maliyet | Kalite |
|---------|------|---------|--------|
| **Tesseract (yerel)** | 4-8 saat | $0 | Orta — matematik sembollerinde %70-80 |
| **Google Document AI** | 30-60 dk | ~$30-50 | Yüksek — %90+ |
| **Azure Computer Vision** | 30-60 dk | ~$15-25 | Yüksek |
| **Gemini Vision API** | 1-2 saat | ~$10-15 | Yüksek — multimodal |

**Önerim:** Faz 1'de **Gemini Vision API** kullanılsın — zaten aynı sağlayıcı, API key hazır, Türkçe + matematik karma içerik için iyi.

### 3. ve 4. Sınıfı Şimdilik Atla Önerisi

Bir alternatif: **Full RAG'a önce metin gömülü 9 PDF'le başla, OCR işini ikinci faza bırak.** Nedenleri:
- 3. ve 4. sınıf sentetik corpus'umuzda zaten iyi kapsandı (180+240=420 örnek)
- OCR pipeline'ı kurulumu başka session'a taşır, diğer sınıflar için değer hemen gelir
- 3. ve 4. sınıf özellikle kritikse daha sonra Gemini Vision ile ~1 saatte halledilebilir

---

## 🔍 Kritik Bulgu #3 — İçerik Yapısı (Örnek/Etkinlik Dağılımı)

Discovery sırasında 10 sayfadan sample alındığında, şu başlıklar regex ile yakalandı:

| PDF | Örnek başlığı | Etkinlik | Alıştırma |
|-----|---------------|----------|-----------|
| `matematik_5_1.pdf` | **8** | 6 | 0 |
| `matematik_5_2.pdf` | **3** | **8** | 0 |
| `matematik_6_1.pdf` | 0 | 2 | 0 |
| `matematik_6_2.pdf` | 1 | 4 | 0 |
| Diğer sınıflar | ~0 | 0-1 | 0 |

**Gözlemler:**
- **5. sınıf kitapları çok zengin:** "Örnek 1, Örnek 2, ... Örnek N" başlıklı çözümlü örnekler
- **Tüm sınıflarda "Etkinlik" bloğu var** (sorular + problemler)
- **"Kazanım:" etiketi yok** — MEB artık bu biçimde yazmıyor
- **"Alıştırma" başlığı nadir** — sorular genelde numaralı listeler halinde

### Chunking İmplikasyonu

- **Örnek blokları:** `^Örnek \d+` regex → 1 chunk = 1 örnek (hedef ~500-1000 chunk sadece 5. sınıftan)
- **Etkinlik blokları:** `^Etkinlik(\s+\d+)?` → 1 chunk = 1 etkinlik (~200-400 chunk)
- **Diğer konu anlatımı:** Paragraf bazlı 200-400 token chunks (~2000-3000 chunk)

**Tahmini toplam chunk sayısı:** 3.000-5.000 (ilk tahmin 2.000-4.000'di, revize edildi).

---

## 📊 Revize Edilmiş Zaman ve Maliyet Tahminleri

| Kalem | İlk tahmin | **Revize tahmin** | Açıklama |
|-------|-----------|-------------------|----------|
| Extraction (9 metin gömülü PDF) | 2-4 saat | **1-2 saat** | Daha hızlı — metin kolayca çıkıyor |
| OCR (2 taranmış PDF) | 4-8 saat yerel | **1-2 saat Gemini Vision** | Maliyet +$10-15 ama süre kısalır |
| Chunking | 2-4 saat | **2-3 saat** | Aynı |
| Kazanım etiketleme | 2-3 saat | **4-6 saat** | Müfredat farkı + hibrit yaklaşım |
| Embedding | $0.50 | **~$1.00** | Daha çok chunk |
| Ingestion + entegrasyon | 1-2 saat | 1-2 saat | Aynı |
| Değerlendirme | 2 saat | 2 saat | Aynı |
| **TOPLAM** | **1-2 gün + $5-15** | **1.5-2.5 gün + $15-25** | Müfredat yönetimi + OCR |

---

## ⚠️ Güncellenmiş Risk Matrisi

| Risk | Olasılık | Etki | Azaltma |
|------|----------|------|---------|
| Taranmış PDF'lerde OCR kalite düşüklüğü | Orta | Bu iki sınıfta zayıf RAG | Gemini Vision kullan; alternatif: bu sınıfları atla |
| **Müfredat farkı** (yeni MEB 2024) | **Yüksek** | **~%40-50 veri eşleşmez** | Hibrit yaklaşım (Bulgu #1, Seçenek C) |
| Matematik sembol kaybı | Düşük | Sorular anlamsızlaşır | Test edildi, sorun yok; spot-check yeterli |
| Chunking çok granüler | Düşük | Retrieval parçalı | Örnek/etkinlik bazlı chunking düzenli sonuç veriyor |
| `matematik_5_1.pdf` tip yapısı farklı | Düşük | 5. sınıftan ekstra değer çıkarabiliriz | Bonus — 5. sınıf pilotu bu dosyayla yapılabilir |
| Hukuki/telif | Düşük | Dahili kullanım güvenli | Production öncesi kurum onayı |

---

## 🛣️ Önerilen Yol Haritası (Revize)

### Aşama A — "Hızlı Kazanım" POC (önerim, 4-6 saat)
**Amaç:** 5. sınıf için Full RAG prototipini kur ve etkinliğini görün.

1. `matematik_5_1.pdf` + `matematik_5_2.pdf` extract et (hızlı)
2. Örnek/Etkinlik başlıklarını regex ile chunk'la (~400-500 chunk)
3. LLM ile kazanım etiketleme (sadece 5. sınıf için, ~$3-5)
4. ChromaDB'ye ingest et (`content_type="textbook_example/textbook_activity"`)
5. Agent retrieval'ını güncelle — "5. sınıf ise textbook chunk'ı da çek"
6. **Karşılaştırmalı test:** Sentetik vs Sentetik+Textbook

**Eğer sonuç net bir iyileşme gösterirse** Aşama B'ye geç; göstermezse yatırım daha dikkatli planlanır.

### Aşama B — Tüm Metin Gömülü PDF'ler (1 gün)
1., 2., 5., 6., 7. sınıf PDF'leri (9 dosya) Aşama A mantığıyla işle.

### Aşama C — Taranmış PDF'ler (3. ve 4. sınıf, yarım gün)
Gemini Vision API ile OCR → chunk → etiketle → ingest.

### Aşama D — Müfredat Genişletmesi (opsiyonel, 1 gün)
Yeni MEB 2024 müfredatındaki Çarpanlar/Asal/İstatistik/Olasılık/Algoritma için `curriculum.py`'e kazanımlar eklensin, sentetik corpus da genişletilsin.

---

## 📌 Benim Özet Tavsiyem

1. **Hemen Aşama A'yı (5. sınıf POC) yap** — bu session'a sığar, 4-6 saat
2. Sonuçlar güzel çıkarsa sen onay ver → Aşama B (1 gün, farklı session)
3. Aşama C (OCR) iş değerine göre sonraya bırakılabilir
4. Aşama D müfredat genişletmesi projenin stratejik bir ayrı kararı — bu plan dokümanına eklendi ama şimdi yapılmayacak

---

## 📂 İlgili Dosyalar

- `knowledge_base/processed/discovery_report.json` — ham makine-okunabilir çıktı
- `scripts/discover_pdfs.py` — bu keşifi üreten script (tekrar çalıştırılabilir)
- `docs/RAG_PDF_PLAN.md` — ilk plan dokümanı (revize edildi)
- `docs/RAG_ROADMAP.md` — genel RAG yol haritası
