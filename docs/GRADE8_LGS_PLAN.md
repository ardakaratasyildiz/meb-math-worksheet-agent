# 8. Sınıf + LGS Hazırlık — Model Besleme Planı

> Durum: **Plan onaylandı, geliştirme bekliyor.** Tarih: 2026-06-13
> Kaynak: `knowledge_base/8.Sınıf/` (40 PDF, hepsi metin-tabanlı, OCR gerekmiyor)

## 0. Amaç ve kalite çıtası

8. sınıf + LGS hazırlık konseptinde soru üretebilen bir model. İki öncelik:

1. **LGS çıkmış soruları (lgs1–lgs15) = ALTIN STANDART.** Bunlar gerçek sınav
   soruları. Model bu soruları "iyice öğrenmeli" ve **bu kalitede** (LGS tarzı,
   4 şıklı, muhakeme-ağırlıklı, gerçekçi senaryolu) çıktı üretebilmeli. Bu yüzden
   LGS soruları sadece bağlam değil, **few-shot kalite çıpası** olarak işlenir.
2. **Görsel sorular atlanmaz.** LGS'in önemli kısmı geometri/grafik/tablo görselli.
   Bunlar Gemini **vision (multimodal)** ile okunup mevcut sistemin formatına
   (soru metnine gömülü **inline `<svg>`** / Markdown tablo) çevrilir.

## 1. Mevcut mimari (1–7 çalışıyor, 8'e uyarlanacak)

```
PDF → [extract] → chunk JSON → [tag (Gemini)] → tagged JSON → [ingest] → ChromaDB
                                                                              ↓
                                              üretimde retriever (grade=8 filtresi)
```

Üretimde iki retrieval yolu var (`app/services/retriever.py`):
- `retrieve()` → few-shot **Soru+Cevap** örnekleri (textbook hariç) → **LGS soruları buraya düşer**
- `retrieve_textbook()` → cevapsız kavram/örnek chunk'ları (sınıf filtreli)

Görsel format teyidi: visual few-shot örnekleri `question` alanının **içine inline
`<svg>...</svg>` gömüyor** (ayrı alan yok). Şema düz:
`{grade, topic_id, kazanim_kod, difficulty, question_type, question, answer, solution, source}`.

## 2. İçerik track'leri

| Track | Dosyalar | İşleme | content_type | Hedef |
|---|---|---|---|---|
| **A — Ders/konu** | `8 - Matematik Ders Kitabı - MEB.pdf` (365s), `konu_ozet*`, `konu_ozeti*` | extract → tag → ingest_textbook | `textbook_*` | Bağlam (cevapsız kavram/örnek) |
| **B1 — LGS metin soruları** | `lgs*`, `yazili*`, `c1_matematik_8` (metin soruları) | vision-MCQ extractor → ingest_to_chroma | (yok → few-shot) | **Altın few-shot Q+A** |
| **B2 — LGS görsel soruları** | `lgs*` görselli sayfalar | vision → inline SVG/tablo | (yok → few-shot) | **Görsel few-shot Q+A** |

> **Duplicate uyarısı:** `lgsornek1/2/3.pdf` dosya boyutları `lgs13/14/15.pdf` ile
> birebir aynı → muhtemelen kopya. Extractor md5 ile elenecek (mevcut
> `_file_quick_hash` deseni).

## 3. Fazlar

### Faz 0 — Klasör düzeni + manifest
- `extract_textbook._discover_grade_pdfs`'i **alt-klasör + manifest** destekleyecek
  şekilde genişlet. `knowledge_base/8.Sınıf/manifest.json`:
  ```json
  [{"file": "lgs1.pdf", "grade": 8, "track": "lgs"},
   {"file": "8 - Matematik Ders Kitabı - MEB.pdf", "grade": 8, "track": "textbook"}, ...]
  ```
  Dosya isimlerini değiştirmeden hangi PDF'in hangi track olduğunu açıkça kontrol ederiz.
- Büyük PDF'leri (`8.Sınıf/*.pdf`, ~400MB) `.gitignore`'a ekle; sadece üretilen
  JSON + ChromaDB versiyonlanır (mevcut desen).

### Faz 1 — Müfredat altyapısını 8'e aç
**1a. `CURRICULUM[8]`'i PDF'lerden türet + elle doğrula** (en kritik):
- Yeni: `scripts/derive_grade8_curriculum.py`. `yazili*`, `c1_matematik_8`, ders
  kitabındaki gerçek `M.8.x.x` kodlarını + kazanım metinlerini Gemini ile çıkar,
  MEB 2024 8. sınıf müfredatıyla eşleştir, `difficulty_hints`'li `CURRICULUM[8]`
  bloğu üret (7 öğrenme alanı: Çarpanlar-Katlar / Üslü / Kareköklü, Cebirsel
  İfadeler-Özdeşlikler, Doğrusal Denklem-Eşitsizlik, Üçgenler, Dönüşüm-Geometrik
  Cisimler, Veri Analizi, Olasılık).
- Çıktıyı `app/data/curriculum.py`'ye **elle gözden geçirerek** ekle (resmi-olmayan
  kod sorununu tekrarlamamak için — bkz. memory).

**1b. 7→8 sınır kodları:**
| Dosya | Değişiklik |
|---|---|
| `app/data/curriculum.py:36` | `GRADE_LEVELS` → `8: EducationLevel.ORTAOKUL` |
| `app/models/schemas.py:88,471` | `ge=1, le=7` → `le=8` |
| `app/routers/curriculum.py:26,48` | `grade_id > 7` → `> 8` |
| `scripts/extract_textbook.py:381` | `choices=range(1, 8)` → `range(1, 9)` |
| `scripts/discover_pdfs.py:53` | `1 <= g <= 7` → `<= 8` |
| `app/main.py:41`, docstring'ler | "1-7" → "1-8" (kozmetik) |

> `get_grades()` API'si `CURRICULUM.keys()`'ten türüyor → `CURRICULUM[8]` eklenince
> frontend sınıf seçici **otomatik** 8'i gösterir. Frontend'de sabit grade listesi
> olup olmadığı tek noktada kontrol edilecek.

### Faz 2 — Çıkarım
**Track A (ders kitabı):**
- `extract_textbook.py --grade 8` → `textbook_chunks_grade8.json` (~3000 chunk beklenir).
- HEADER_RE'yi 8. sınıf kitabı başlık kalıplarıyla doğrula (gerekirse "Sıra Sizde",
  "Kendimi Değerlendiriyorum" eklenir).

**Track B — yeni `scripts/extract_lgs_questions.py` (vision tabanlı):**
- Her LGS/yazılı PDF sayfasını `get_pixmap` ile **görüntüye** çevir; **cevap anahtarı**
  sayfalarını bağlama dahil et.
- Gemini 2.5 Flash (vision) → yapısal Pydantic şema:
  `{stem, options[A–D], correct_answer, solution, kazanim_kod, difficulty, question_type, has_visual}`.
- **Görsel sorular (B2):** `has_visual=true` ise modelden görseli **yeniden üretmesini**
  iste:
  - Geometri şekli → inline `<svg>` (mevcut `geometry_svg_examples` formatı).
  - Grafik (sütun/çizgi) → inline `<svg>` veya Markdown.
  - Tablo → Markdown tablo (`tablo_sorusu`).
  - `question_type` buna göre: `gorsel_geometri` / `grafik_okuma` / `tablo_sorusu` / `coktan_secmeli`.
- Üretilen SVG'yi `app/services/svg_utils.py` ile sanitize/doğrula.
- **Faithfully reproduce edilemeyen görseller** (fotoğraf, karmaşık şekil) sessizce
  atılmaz → `knowledge_base/processed/lgs_visual_review.json`'a sayfa referansıyla
  yazılır (elle değerlendirme kuyruğu) ve **loglanır**.
- Çıktı: `knowledge_base/processed/lgs_examples.json` (mevcut few-shot şeması).

### Faz 3 — Etiketleme + Ingest
**Track A:** `tag_textbook_chunks.py --grade 8` → `..._tagged.json` → `ingest_textbook.py --grade 8 --dry-run` (istatistik) → gerçek ingest.

**Track B:** `ingest_to_chroma.py`'ye `_load_lgs()` ekle (`_load_format` deseni birebir).
`source="lgs/<dosya>"`, `content_type` set etme → retriever bunları few-shot Q&A
olarak görür. `python scripts/ingest_to_chroma.py` (idempotent).

### Faz 4 — Few-shot çıpa + LGS üretim modu
- `app/data/few_shot/grade_8.py`: LGS çıkarımındaki **en kaliteli** Q&A'leri her
  kazanım için elle seç → sabit kalite çıpası (7. sınıf şablonu).
- `app/data/few_shot/__init__.py`: `grade_8` import + `EXAMPLES_BY_GRADE[8]`.
- **LGS üretim modu:** 8. sınıf üretiminde `coktan_secmeli` tipini öne çıkar;
  `app/prompts/templates.py`'de grade=8 için "LGS tarzı: gerçekçi senaryo, 4 şık,
  tek doğru, çeldiriciler anlamlı" yönlendirmesi ekle. `agent.py` tip-dağılımı kontrol.

### Faz 5 — Doğrulama
- Smoke: grade=8 her öğrenme alanından 1 soru üret; retriever'ın 8. sınıf few-shot
  + textbook chunk çektiğini logdan doğrula.
- `scripts/eval/scenarios.py`'ye 8. sınıf senaryoları ekle → `math_verifier` + `critic`.
- Manuel göz: üslü/kareköklü (LaTeX render), görsel sorular (SVG render), LGS tarzı kalite.

### Faz 6 — Deploy
- ChromaDB commit (`chroma.sqlite3` versiyonlu). frontend-ci (lint+typecheck) doğrula.
- Render API yeni DB'yi alır; Vercel frontend sınıf-8'i otomatik gösterir.

## 4. Gemini maliyet tahmini (yaklaşık, USD)

Modeller: tagging/extraction `gemini-2.5-flash`, embedding `gemini-embedding-001`.
Yaklaşık birim fiyat: Flash giriş ~$0.30/1M, çıkış ~$2.50/1M; Pro giriş ~$1.25/1M,
çıkış ~$10/1M; embedding ~$0.15/1M. *(Fiyatlar yaklaşık; Gemini ücretsiz kotası bir
kısmını karşılayabilir.)*

| İş | Hacim | Giriş tok. | Çıkış tok. | ~Maliyet |
|---|---|---|---|---|
| **A — Textbook tagging** (Flash) | ~3000 chunk / batch 4 = ~750 çağrı | ~3.75M | ~0.26M | **~$1.8** |
| **B — LGS vision çıkarımı** (Flash) | ~450 sayfa (dedup sonrası) / ~225 çağrı, görselli | ~1.35M | ~0.56M | **~$1.8** |
| B görsel SVG için Pro (opsiyonel) | görselli ~%40 çağrı Pro'ya | — | — | **+~$2.5** |
| Faz 1a müfredat türetme | birkaç çağrı | <0.3M | — | ~$0.2 |
| Embedding ingest | ~3650 doc × ~400 tok = ~1.5M | 1.5M | — | ~$0.2 |
| **Tek temiz koşu (Flash-only)** | | | | **~$4** |
| **Tek koşu (görseller Pro ile)** | | | | **~$6.5** |
| **Geliştirme iterasyonu dahil (×2, resumable)** | | | | **~$8–15** |

**Özet: tüm iş baştan sona ~$5–15 aralığında.** Scriptler resumable (`tagged:true`
atlanır) → yeniden koşmalarda maliyet düşük. Görsel kalitesi için Flash yetmezse
sadece görselli alt-küme Pro'ya alınır.

## 5. Riskler
1. **Görsel reprodüksiyon:** Bazı görseller (fotoğraf, karmaşık diyagram) SVG'ye
   sadık çevrilemez → review kuyruğuna düşer, sessiz kayıp yok.
2. **Kazanım eşleşmesi:** PDF kodları gerçek ama extraction'da kopukluk olabilir;
   tagging `confidence=low + null` ile gürültüyü eler.
3. **Müfredat doğruluğu:** `CURRICULUM[8]` otomatik türetilip **elle doğrulanır**.
4. **LGS telif:** Çıkmış sorular few-shot **örnek**; üretim bunları kopyalamaz,
   stilini öğrenir. Birebir tekrar üretimi önlemek için diversity penalty mevcut.

## 6. Efor sırası
Faz 1 (müfredat) ve Faz 2-B (vision LGS extractor) en yoğun. Gerisi mevcut
pipeline'ın tekrar kullanımı. Geliştirme sırası: **Faz 0 → 1 → 2A → 3A** (textbook
hattını uçtan uca çalıştır, doğrula) → **2B → 3B → 4** (LGS + görsel) → **5 → 6**.
