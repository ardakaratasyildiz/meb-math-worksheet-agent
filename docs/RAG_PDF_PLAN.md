# 📚 RAG PDF Entegrasyon Planı — Gerçek MEB Ders Kitaplarının Eklenmesi

> **Durum:** Plan aşaması. Sentetik corpus (RAG-Lite) tamamlandıktan sonra bu plan devreye alınır. `knowledge_base/` altındaki 11 PDF hazır.

## 1. Önceki Aşamalar

| Aşama | Durum | Veri |
|-------|-------|------|
| **MVP** | ✅ Tamamlandı | 214 manuel few-shot |
| **RAG-Lite (Faz 1)** | 🏃 Devam ediyor | ~1605 sentetik örnek (Gemini ile üretilen) |
| **Full RAG (bu plan)** | 📋 Planlanıyor | MEB ders kitabı PDF'lerinden extract edilecek pasajlar |

Bu plan **RAG-Lite üstüne katmanlanır**, onu değiştirmez. Aynı ChromaDB, aynı retriever, yeni data kaynağı.

---

## 2. PDF Envanteri

| Dosya | Boyut | Tahmini Sınıf | Not |
|-------|-------|----------------|-----|
| `matematik_1_1.pdf` | 137 MB | 1. sınıf (1. kitap) | High-res görsel ağırlıklı olasılığı yüksek |
| `matematik_1_2.pdf` | 119 MB | 1. sınıf (2. kitap) | Aynı |
| `matematik_2_1.pdf` | 17 MB | 2. sınıf (1. kitap) | |
| `matematik_2_2.pdf` | 14 MB | 2. sınıf (2. kitap) | |
| `3.Sinif-Matematik-Ders-Kitabi-MEB-pdf.pdf` | 20 MB | 3. sınıf | |
| `4.Sinif-Matematik-Ders-Kitabi-MEB-pdf.pdf` | 10 MB | 4. sınıf | |
| `matematik_5_1.pdf` | 59 MB | 5. sınıf (1. kitap) | |
| `matematik_5_2.pdf` | 130 MB | 5. sınıf (2. kitap) | Büyük |
| `matematik_6_1.pdf` | 9 MB | 6. sınıf (1. kitap) | |
| `matematik_6_2.pdf` | 8 MB | 6. sınıf (2. kitap) | |
| `Matematik Ders Kitabı-MEB.pdf` | 77 MB | **Muğlak — muhtemelen 7. sınıf** | Dosya adı belirsiz |

**Toplam:** ~600 MB, tahmini 3000-5000 sayfa.

**İlk iş:** Her PDF'nin gerçek içeriğini sample extraction'la doğrulamak + naming convention'ı sabitlemek.

---

## 3. Beş Temel Zorluk

1. **PDF tipi bilinmiyor** — Metin gömülü mü yoksa OCR gerektiren taranmış mı? 137 MB'lık kitaplar büyük ihtimalle high-res resim-ağırlıklı. Faz 0'da sample ile netleştirilecek.

2. **Matematik sembolleri** — `⅔`, `π`, `∠`, `√` gibi semboller PDF extraction'da çoğu zaman `?` veya boşluk olur. Post-processing regex gerekir.

3. **Tablo yapıları** — İşlem tabloları, kazanım matrisleri iç içe cell'lerle kompleks. `pdfplumber` hatırı sayılır ama mükemmel değil.

4. **Kazanım ↔ sayfa aralığı eşleşmesi** — Bir chunk'ın hangi kazanıma denk düştüğü **altın bilgi**. Retrieval'ın başarısı buna bağlı.

5. **Sunulan PDF'nin tutarsız isimlendirmesi** — "Matematik Ders Kitabı-MEB.pdf" hangi sınıfa ait belirsiz.

---

## 4. Üç-Tip Chunk Mimarisi

Tüm chunk'lar aynı ChromaDB'ye yazılacak, `content_type` metadata'sı ile ayırt edilecek. Retriever `content_type` filtresiyle sorgu tipine göre daralt edecek.

| content_type | Ne içerir | Chunk boyutu | Tahmini adet |
|--------------|-----------|--------------|--------------|
| `konu_anlatimi` | Tanımlar, kavram açıklamaları, kural kutuları | 200-400 token | 300-500 |
| `ornek_soru` | Çözümlü örnekler ("Örnek 3: ..."), etkinlik | 1 örnek = 1 chunk | 800-1500 |
| `alistirma` | Alıştırma/test soruları, numaralı bloklar | 1 soru = 1 chunk | 1000-2000 |

**Toplam tahmin:** 2000-4000 chunk (sentetik + manuel ~1900 chunk'a ek olarak).

---

## 5. Faz Planı — 6 Faz

### Faz 0 — Keşif (30-60 dk)
**Amaç:** Somut planı PDF'lerin gerçek içeriğine göre güncelleme.

- [ ] Her PDF'ten 3-5 sayfa örnek çıkar (`pymupdf` ile)
- [ ] Taranmış mı / metin gömülü mü tespit et (her PDF için)
- [ ] İçindekiler tablosunu çıkar / göster
- [ ] "Matematik Ders Kitabı-MEB.pdf" gerçek sınıfını belirle
- [ ] Kazanım ↔ sayfa haritası ön tasla (sadece İçindekiler'den)
- [ ] Matematik sembollerinin nasıl extract edildiğini test et

**Çıktı:** `knowledge_base/processed/discovery_report.json` — her PDF için metadata + sample metin.

### Faz 1 — Extraction Pipeline (3-5 saat)
**Amaç:** Tüm sayfaları temiz metne çevir.

- Ana kütüphane: `pymupdf` (hızlı, saf metin için ideal)
- Fallback: `pdfplumber` (tablo-ağırlıklı sayfalar için)
- OCR fallback: `pytesseract` + Türkçe dil paketi (taranmış sayfalar için, ≥4 saat)
- Post-processing:
  - Sayfa numarası / üst-alt bilgi temizle
  - Matematik sembollerini regex ile normalize et
  - Aşırı boşluk / newline normalizasyonu

**Çıktı:** `knowledge_base/processed/pdf_raw/{grade}_{book}_p{page:03d}.json`
```json
{"grade": 5, "book": 1, "page": 142, "text": "...", "extraction_method": "pymupdf"}
```

### Faz 2 — Akıllı Chunking (2-4 saat)
**Amaç:** Sayfaları anlamlı chunk'lara böl ve tipine göre etiketle.

Strateji:
- **Başlık tabanlı parse** — Regex ile yakala:
  - `^Örnek \d+` → `ornek_soru`
  - `^(\d+\.\d+ )?Konu:? ` → `konu_anlatimi`
  - `^Alıştırma|^Test|^\d+\.` → `alistirma`
- **Paragraf bazlı split** — İki newline = chunk sınırı (konu anlatımı için)
- **Sayı tabanlı split** — Numaralı listeler her öğe ayrı chunk (alıştırma için)

**Çıktı:** `knowledge_base/processed/pdf_chunks/{grade}_{book}.jsonl` — her satır bir chunk.

### Faz 3 — Kazanım Etiketleme (4-6 saat, en kritik faz)
**Amaç:** Her chunk'a `kazanim_kod` ata — retrieval'ın başarısı buna bağlı.

Üç strateji kombinasyonu:

1. **İçindekiler tablosu eşleme (hedef %70 coverage):**
   - PDF'nin başındaki içindekileri parse et
   - "5.2 Kesirlerle Toplama-Çıkarma .............. sf 142" → sayfa 142 itibaren M.5.2.x
   - Her chunk'ın `page` alanından hangi bölüme düştüğünü bul
   - Başlık → kazanım kodu mapping'ini `docs/book_toc_mapping.json`'de tut

2. **LLM asistanlı (%25 belirsiz için):**
   - Şüpheli chunk'ı Gemini'ye: *"Bu metin 5. sınıf kesirler konusunda, aşağıdaki kazanımlardan hangisini kapsar? [M.5.2.1, M.5.2.2, M.5.2.3, M.5.2.4]. Confidence (0-1) ile yanıtla."*
   - Confidence > 0.7 → otomatik ata
   - Confidence ≤ 0.7 → manuel kuyruğa veya `kazanim_kod=null` kalır

3. **Fallback:**
   - Eşleşemeyen chunk'a `kazanim_kod=null`
   - Retrieval yine `topic_id` + `grade` filtresiyle çalışır

**Çıktı:** Her chunk metadata'sında `kazanim_kod`, `confidence`, `mapping_method` (`toc`/`llm`/`fallback`).

### Faz 4 — Ingestion (1-2 saat)
**Amaç:** Etiketli chunk'ları ChromaDB'ye yükle.

- `scripts/ingest_pdfs.py` — mevcut `ingest_to_chroma.py` mantığını extend eder
- Her chunk: embedding al → Chroma'ya ekle (aynı collection)
- Metadata:
  ```json
  {
    "grade": 5,
    "topic_id": "kesirler",
    "kazanim_kod": "M.5.2.3",
    "difficulty": "orta",  // optional, konu anlatımı için null
    "content_type": "ornek_soru",
    "source": "MEB_matematik_5_1",
    "page": 142,
    "mapping_method": "toc",
    "confidence": 0.95
  }
  ```
- **ID stratejisi:** `sha1(source + page + chunk_index)` — idempotent

### Faz 5 — Retrieval Güncellemesi (1-2 saat)
**Amaç:** Textbook pasajları üretim zamanında prompt'a enjekte edilsin.

Değişiklikler:
- `retriever.py`:
  - `content_type` filtresi eklendi (prompt'a eklenirken türü seçilebilir)
  - Hybrid retrieval (opsiyonel): **BM25** (sparse) + **dense** karması (0.3/0.7)
  - "Eşkenar üçgen" gibi exact-match ihtiyacı için sparse önemli
- Agent'ın `_collect_few_shot_rag` fonksiyonu:
  - 3 `ornek_soru` + 1 `konu_anlatimi` + 2 `alistirma` karması çeker
  - Ders kitabı pasajları prompt'ta ayrı bir blok olarak görünür

### Faz 6 — Karşılaştırmalı Değerlendirme (2 saat)
**Amaç:** Üç modu kör testle karşılaştır.

- **MVP** (manuel few-shot)
- **RAG-Lite** (sentetik corpus)
- **Full RAG** (sentetik + MEB textbook)

Her kazanım için aynı parametrelerle 3 versiyon üret. 5 bağımsız öğretmen/değerlendiriciye rastgele sırayla göster:
- MEB-likeness (1-5)
- Matematiksel doğruluk (1-5)
- Çeşitlilik (1-5)
- Pedagojik uygunluk (1-5)

**Hedef:** Full RAG ortalama ≥ 4.0, RAG-Lite'tan ≥%15 üstün.

---

## 6. Dosya/Script Planı

```
GenAgent/
├── knowledge_base/
│   ├── raw/                         MOVE PDF'leri buraya taşıyacağız
│   │   ├── matematik_1_1.pdf
│   │   └── ...
│   ├── processed/
│   │   ├── discovery_report.json    Faz 0 çıktısı
│   │   ├── pdf_raw/                 Faz 1 çıktısı (sayfa başına JSON)
│   │   ├── pdf_chunks/              Faz 2 çıktısı (JSONL)
│   │   └── book_toc_mapping.json    Faz 3'te üretilen içindekiler → kazanım eşleşmesi
│   └── chroma_db/                   (mevcut)
│
└── scripts/
    ├── discover_pdfs.py             YENİ — Faz 0
    ├── extract_pdfs.py              YENİ — Faz 1
    ├── chunk_pdfs.py                YENİ — Faz 2
    ├── tag_kazanimlar.py            YENİ — Faz 3 (LLM-assisted)
    ├── ingest_pdfs.py               YENİ — Faz 4 (ingest_to_chroma'yı kullanır)
    └── eval_rag_modes.py            YENİ — Faz 6
```

---

## 7. Kütüphane Gereksinimleri

```
pymupdf>=1.24.0         # hızlı PDF metin çıkarma
pdfplumber>=0.11.0      # tablo ağırlıklı sayfalar için fallback
pytesseract>=0.3.10     # OCR (gerekli olursa)
Pillow>=10.0.0          # OCR için görsel işleme
rank_bm25>=0.2.2        # opsiyonel: hibrit retrieval için sparse score
```

Ek sistem bağımlılığı (OCR kullanılacaksa):
- **Tesseract OCR** + Türkçe dil paketi (`tesseract-ocr-tur`)

---

## 8. Zaman ve Maliyet

| Kalem | Süre | Maliyet |
|-------|------|---------|
| **Faz 0** keşif | 30-60 dk | $0 |
| **Faz 1** extraction (metin gömülüyse) | 2-4 saat | $0 |
| **Faz 1'** OCR fallback (gerekiyorsa) | +4-8 saat | $0 (yerel) |
| **Faz 2** chunking | 2-4 saat dev + 30 dk run | $0 |
| **Faz 3** kazanım etiketleme (LLM) | 2-3 saat dev + 1-2 saat LLM call | **$5-15** |
| **Faz 4** ingestion (~3000 chunk embed) | 20-30 dk | **~$0.50** |
| **Faz 5** retriever entegrasyonu | 1-2 saat | $0 |
| **Faz 6** değerlendirme | 2-4 saat | $0 |
| **Toplam** | **1-2 gün developer** | **$5-15** |

Embedding maliyeti: ~3000 chunk × ~500 char × $0.00013/1K char ≈ $0.20. Conservative üst sınır $1.

---

## 9. Risk Matrisi

| Risk | Olasılık | Etki | Azaltma |
|------|----------|------|---------|
| PDF'ler taranmış, OCR gerekir | Orta | +4-8 saat süre, %15 kalite düşüşü | Faz 0'da sample ile test; gerekirse kaliteli OCR'a (Azure/AWS) çıkılır |
| Matematik sembolleri kayıp | Yüksek | Sorular anlamsızlaşabilir | Regex post-processing + sembol replacement map |
| İçindekiler parse edilemiyor | Orta | Kazanım etiketleme %100 LLM'e kalır | LLM maliyeti $15'a çıkar, teknik olarak başarabilir |
| Kitap numaralandırması tutarsız | Yüksek | Manuel düzeltme gerekir | Her PDF için 5 dk manuel metadata girişi |
| Corpus büyüklüğünden ChromaDB yavaşlar | Düşük | Retrieval gecikmesi | HNSW indexi zaten hızlı; >10K chunk'ta Qdrant'a geçilir |
| Bazı kazanımlara hiç chunk gelmez | Orta | O kazanımlarda retrieval sentetik corpus'a düşer | Sentetik corpus fallback olarak zaten var — problem olmuyor |
| Hukuki: MEB içeriği ihlali | Düşük | Dahili kullanım ve transformative output — güvenli | Production'dan önce kurum hukuku onayı |

---

## 10. Başlangıç Kararı

**Önerilen sıralama:**

1. **Sentetik corpus tamamlansın** — devam ediyor (~60 dk daha)
2. **Faz 0 keşif** — sentetik bitince hemen başlayabilirim (30-60 dk)
3. **Faz 0 raporu** — hangi PDF'ler sorunlu, OCR gerekli mi, kazanım eşlemesi mümkün mü
4. **Karar noktası:** Keşif sonucuna göre Faz 1-6'nın maliyeti netleşir, devam edelim mi?
5. **Faz 1-6** — ayrı 1-2 günlük çalışma (session'a sığmayabilir)

---

## 11. Geçiş Kriterleri — Ne Zaman Full RAG Şart?

Sentetik corpus yeterli olmayabilir eğer:

- [ ] Kullanıcı geri bildirimi: "Bu gerçek MEB ders kitabı gibi değil"
- [ ] Sentetik üretimlerde **belirli bir Gemini stili** fazla belirginleşiyor (örn. "Ali/Ayşe aşırı sık kullanılıyor")
- [ ] MEB-spesifik terminoloji ("Etkinlik", "Problem Çözme Basamakları", "Kendimi Değerlendiriyorum") sentetik corpus'ta eksik
- [ ] 8. sınıf ve üzeri eklenmesi gerekiyor → sentetik corpus manuel kazanım girişi gerektirir; PDF'den otomatik çıkarım ölçeklenir

Bu kriterlerden biri tetiklendiğinde Faz 0 → Faz 6 sırası izlenir.
