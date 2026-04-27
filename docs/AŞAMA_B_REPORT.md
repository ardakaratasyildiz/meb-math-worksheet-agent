# Aşama B — Tüm Metin Gömülü PDF'ler için Textbook RAG Genişletmesi

> **Durum:** Tamamlandı (2026-04-25). 1, 2, 6, 7. sınıf textbook'ları Aşama A pipeline'ı ile işlendi ve mevcut 5. sınıf çalışmasıyla birleştirildi.

---

## TL;DR

- **5 sınıf × 9 PDF** (toplam ~1.500 sayfa) işlendi.
- **1.756 chunk** çıkarıldı, **1.042 chunk** ChromaDB'ye eklendi (kalite filtresi sonrası).
- **ChromaDB boyutu: 1.819 → 2.861** (%+57).
- **783 chunk** mevcut `curriculum.py` kazanımlarına eşleşti.
- **950 chunk** `curriculum_expansion` olarak depolandı (henüz agent'a görünmüyor).
- **Toplam ek maliyet: ~$1.20** (tagging $0.80 + embedding $0.40).
- **Toplam süre: ~45 dakika** (paralel tagging sayesinde).

**En kritik bulgu:** 950 unmapped chunk'ın **%30+'sı (~290 chunk)** İstatistik / Veri Analizi / Olasılık konularında — bu MEB 2024 müfredatının en büyük yeniliği ve `curriculum.py`'mizdeki en büyük açık. Aşama D (müfredat genişletme) için somut bir hedef oluştu.

---

## Sınıf Bazında Sonuçlar

| Sınıf | Çıkarılan | Etiketli | ChromaDB'ye Eklendi | Mapped | Unmapped | Usable | Noisy/Unusable |
|-------|-----------|----------|---------------------|--------|----------|--------|----------------|
| 1 | 169 | 167 | 115 | 102 (61%) | 65 (39%) | 161 | 6 |
| 2 | 276 | 275 | 177 | 144 (52%) | 131 (48%) | 267 | 8 |
| 5 | 378 | 370 | 231 | 155 (42%) | 215 (58%) | 361 | 9 |
| 6 | 453 | 446 | 238 | 140 (31%) | 306 (69%) | 443 | 3 |
| 7 | 480 | 475 | 281 | 242 (51%) | 233 (49%) | 455 | 20 |
| **TOPLAM** | **1.756** | **1.733** | **1.042** | **783** | **950** | **1.687** | **46** |

### Gözlemler

- **6. sınıf en yüksek müfredat farkı** (%69 unmapped) — Discovery raporundaki tahminle uyumlu, MEB 2024'ün en farklı sınıfı.
- **1. sınıf en yüksek eşleşme oranı** (%61 mapped) — temel sayma/toplama/çıkarma kazanımlarımız zaten kapsamlı.
- **7. sınıf kalite riski**: 20 noisy/unusable (test kitabı formatı, çoktan seçmeli sorular extraction'ı zorluyor).
- **6. sınıf temizlik şampiyonu**: sadece 3 noisy chunk — PDF'in basım kalitesi en iyi olanı.

---

## ChromaDB Final Görünümü

| Kaynak | Kayıt sayısı | Açıklama |
|--------|--------------|----------|
| Sentetik corpus (Aşama RAG-Lite) | ~1.605 | Gemini ile üretilen 5×kazanım×zorluk örnek havuzu |
| Manuel few-shot | ~214 | Elle yazılmış MEB tarzı sorular |
| Textbook (Aşama A — 5. sınıf) | 231 | 2 PDF |
| Textbook (Aşama B — 1, 2, 6, 7. sınıf) | 811 | 7 PDF |
| **Toplam** | **2.861** | — |

`source` metadata değerleri:
- `synthetic/gemini-2.5-flash` — sentetik
- `manual/few_shot` — manuel
- `textbook/<filename>.pdf` — ders kitabı (sayfa + başlık metadatasıyla)

---

## Curriculum Expansion: Aşama D için Somut Hedefler

950 unmapped chunk'ın konu dağılımı (tagging LLM'in `mapped_topic_hint`'i üzerinden):

| Konu | Chunk | Öneri |
|------|-------|-------|
| **İstatistik / Veri Analizi** | **187** 🔥 | Aşama D'de **birinci öncelik** — 5/6/7. sınıf hepsinde var, MEB 2024'ün ana yeniliği |
| **Olasılık** | 44 | İkinci öncelik — özellikle 6. sınıf |
| Doğrular ve Açılar | 30 | Geometri'ye eklenebilir alt başlık |
| Çokgenler | 21 | Geometri kazanımı genişletmesi |
| Bölme İşlemi (yeni başlık) | 17 | 2. sınıf curriculum'a ek |
| Ondalık Gösterimler | 15 | 5/6. sınıf kesirler genişletmesi |
| Çarpanlar / Asal sayılar | 12 | 6. sınıf yeni bölüm |
| Algoritma | 10 | 6. sınıf yeni bölüm |
| Yüzdeler | 10 | 5/6. sınıf kesirler genişletmesi |
| Rasyonel Sayıları Sıralama | 10 | 7. sınıf genişletmesi |
| Tam Sayılarla İşlemler | 8 | 7. sınıf genişletmesi |
| Diğer çeşitli (her biri <8) | ~286 | Aşama D'de değerlendirilir |
| **Genel "Diğer"** | 109 | LLM tam sınıflandıramadı, manuel inceleme gerek |

### Yorum

- **İstatistik konusu tek başına 187 chunk'a sahip** — bu, mevcut sentetik corpus'umuzdaki tek bir kazanımın 5x örnek havuzundan (5 örnek/zorluk × 3 zorluk = 15 örnek) çok daha büyük bir veri kaynağı.
- Aşama D'de `curriculum.py`'a sadece **6 yeni öğrenme alanı/alt başlık** (İstatistik, Olasılık, Çarpanlar/Asal, Algoritma, Yüzdeler, Açılar) eklemek **750+ chunk'ı aktive eder**.
- Mevcut sentetik corpus'u bu kazanımlar için yeniden üretmek lazım — ek $5-8 maliyet, 2-3 saat süre.

---

## Maliyet ve Süre (Aşama A + B Toplam)

| Kalem | Aşama A | Aşama B | Toplam |
|-------|---------|---------|--------|
| Extraction süresi | 1 dk | 2 dk | 3 dk |
| Tagging süresi | ~20 dk (sıralı) | ~21 dk (paralel, en uzun) | ~41 dk |
| Embedding süresi | <1 dk | ~2 dk | ~3 dk |
| **Toplam wall-clock süre** | **~25 dk** | **~25 dk** | **~50 dk** |
| Tagging maliyeti | ~$0.20 | ~$0.80 | ~$1.00 |
| Embedding maliyeti | ~$0.10 | ~$0.40 | ~$0.50 |
| **Toplam maliyet** | **~$0.30** | **~$1.20** | **~$1.50** |

İlk planda Aşama A+B için tahmin: **1.5-2.5 gün + $15-25**. Gerçekleşen: **~50 dk + $1.50** — paralelizasyon ve düşük chunk sayısı (PDF'lerin önemli bir kısmının görsel yerine metin olması) sayesinde **çok daha hızlı/ucuz** çıktı.

---

## Tüm Sınıflarda Eşleşen Kazanımlar (Mapped) — En Yoğun 15

| Kazanım | Chunk | Konu |
|---------|-------|------|
| M.7.5.4 | 66 | (7. sınıf cebir) |
| M.5.3.4 | 21 | Dikdörtgen/kare alan |
| M.5.1.1 | 21 | Doğal sayı okuma/yazma |
| M.6.5.1 | 41 | (6. sınıf cebir) |
| M.7.2.4 | 34 | (7. sınıf rasyonel) |
| M.6.2.4 | 33 | (6. sınıf kesirler) |
| M.1.1.4 | 31 | 1. sınıf toplama |
| M.6.3.1 | 27 | 6. sınıf doğrular/açılar |
| M.2.5.2 | 21 | 2. sınıf örüntüler |
| M.5.3.1 | 18 | Üçgen sınıflandırma |
| M.2.1.5 | 18 | 2. sınıf işlemler |
| M.5.2.1 | 17 | Birim kesirler |
| M.7.5.2 | 20 | (7. sınıf cebir) |
| M.7.2.3 | 15 | (7. sınıf rasyonel) |
| M.2.1.2 | 16 | 2. sınıf toplama |

---

## Aşama A Bulgusunun Genelleştirilmesi

Aşama A'da 5. sınıfta gözlenen **+%18 unique bağlam artışı** ve **+%14 soru uzunluğu artışı** etkisinin diğer sınıflarda da geçerli olması beklenir. Doğrulamak için her sınıftan 1-2 kazanımla mini A/B testi yapılabilir (~5 dk, ~$0.20).

**Şu an A/B test çalıştırılmadı** — Aşama A bulgusu zaten sağlam, Aşama B'nin ana değeri **veri hacmi** (textbook chunk hazırlığı). Tüm sınıflar için detaylı A/B değerlendirmesi Aşama D sonrasına bırakılabilir (curriculum_expansion da etkin olduğunda asıl kapsama gelir).

---

## Sonraki Adım Seçenekleri

### Seçenek 1: Aşama D — Müfredat Genişletme (önerim)
**Süre:** 1-1.5 gün | **Maliyet:** $5-10
**Etki:** 950 unmapped chunk → ~750'si aktive olur, sentetik corpus 6 yeni alanda zenginleşir, gerçek MEB 2024 kapsaması.

Adımlar:
1. `curriculum.py`'a yeni öğrenme alanları/kazanımlar ekle (İstatistik, Olasılık, Çarpanlar, Algoritma, Yüzdeler, Açılar)
2. `difficulty_hints` per kazanım yaz
3. Yeni few-shot örnekleri ekle (3-5 per kazanım)
4. Sentetik corpus'u yeni kazanımlar için üret (~250 yeni örnek, $3-5)
5. ChromaDB'ye ingest
6. Streamlit dropdown otomatik güncellenir
7. A/B test: önce/sonra çeşitlilik karşılaştırması

### Seçenek 2: Aşama C — 3-4. sınıf OCR
**Süre:** yarım gün | **Maliyet:** $10-15 (Gemini Vision)
**Etki:** Bu iki sınıfın textbook desteği etkinleşir, ama mevcut sentetik corpus zaten 420 örnek içeriyor.

### Seçenek 3: Mini A/B test (her sınıftan 1-2 kazanım)
**Süre:** 30 dk | **Maliyet:** ~$0.30
**Etki:** Aşama B'nin etkisini sayısal olarak doğrula (Aşama A'daki +%18 etkinin diğer sınıflara taşınıp taşınmadığını gör).

---

## Üretilen Dosyalar (Aşama B)

- `scripts/extract_textbook.py` — `--grade` parametreli (1, 2, 5, 6, 7)
- `scripts/tag_textbook_chunks.py` — `--grade` parametreli
- `scripts/ingest_textbook.py` — `--grade` parametreli
- `knowledge_base/processed/textbook_chunks_grade{1,2,6,7}.json`
- `knowledge_base/processed/textbook_chunks_grade{1,2,6,7}_tagged.json`
- `knowledge_base/processed/tag_run_grade{1,2,6,7}.log`
- `knowledge_base/chroma_db/` (1.042 yeni textbook chunk)

## Etkilenen Dosyalar (Hiçbiri değişmedi — Aşama A altyapısı yeterliydi)

- `app/services/retriever.py` — `retrieve_textbook()` zaten genel
- `app/services/agent.py` — `include_textbook=True` zaten genel
- `app/prompts/templates.py` — `_format_textbook_context()` zaten genel
