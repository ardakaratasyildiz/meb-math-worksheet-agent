# 🧠 RAG Tabanlı Geliştirme — Detaylı Yol Haritası

> **Durum:** Saklı plan. MVP çalıştığı ve aşağıdaki "Geçiş Kriterleri" henüz tetiklenmediği için **uygulanmadı**. Gerekli olduğunda bu dokümanı referans al.

## 1. Amaç

MVP'deki temel zayıflık: Gemini'ye yalnızca **kazanım metni (1 cümle) + 3 hint + 2-3 elle yazılmış few-shot** veriliyor. Gemini gerçek MEB ders kitabını görmez; kendi genel matematik bilgisiyle MEB'e benzetmeye çalışır.

RAG'ın getirdiği: **Gerçek MEB ders kitabı içeriğini üretim sırasında prompt'a enjekte etmek.** Gemini benzetmez, doğrudan okur.

---

## 2. Avantajlar (Somut)

| Mevcut MVP | RAG ile |
|-----------|---------|
| Gemini "5. sınıf kesirler" için *eğitim verisindeki* genel bilgiyi kullanır | Gemini MEB 5. sınıf kitabı sf. 142'deki pasajı okur |
| Few-shot havuzu manuel, ölçeklenemez (214 örnek toplam) | Ders kitabındaki yüzlerce örnek, alıştırma, problem otomatik erişilebilir |
| Yeni sınıf eklemek = haftalarca manuel veri girişi | Yeni PDF at, ingest et, bitti |
| "MEB tarzı" vaadiyle taklit üretir | Gerçek MEB cümle yapısı, tanım, emphasis Gemini'ye geçer |
| Aynı kazanımda sadece 2-3 alt-örüntü | Kitapta tanımlı 10-15 alt-örüntü çıkabilir |
| Hallucination riski (yanlış kural, yanlış sınıf düzeyi) | Groundtruth metin orada — sapma azalır |
| Semantik dedup yok (string-level) | Embedding altyapısı zaten kurulu → cosine similarity ile semantik dedup bedava |

---

## 3. Veri Kaynakları (MEB Resmi)

| Kaynak | Ne İçerir | Ulaşım |
|--------|-----------|--------|
| **EBA ders kitapları** | Konu anlatımı + örnek soru + alıştırma (altın kaynak) | `eba.gov.tr` → PDF indir |
| **mufredat.meb.gov.tr** | Resmi kazanım dokümanı + açıklamalar | Tek PDF |
| **ÖBA (ogmmateryal.eba.gov.tr)** | Öğretmen etkinlikleri, ek problemler | HTML scrape veya manuel |
| **EBA konu sayfaları** | Video transkripti + özet | HTML scrape |
| **Opsiyonel: çıkmış sınavlar** | Sınav sorularıyla kalibrasyon | Resmi arşivler |

---

## 4. Ingestion Pipeline

```
PDF → Metin çıkar → Akıllı chunk → Kazanıma etiketle → Embed → Vector DB'ye yaz
```

### Chunking Stratejisi (Kritik)

Rastgele 500 karakter kesme **işe yaramaz**. Seçenekler:

- **Başlık bazlı:** "5.2.3 Paydaları Eşit Kesirlerle Toplama" başlığı altındaki tüm içerik bir chunk (kazanım kodu doğrudan eşlenir).
- **Soru bazlı:** Her örnek/alıştırma ayrı chunk (MEB kitapları genelde numaralı).
- **Paragraf bazlı:** Konu anlatımı için 200-400 token paragraflar.

### Chunk Metadata

Her chunk'a aşağıdaki etiketler:

```python
{
    "grade": 5,
    "topic_id": "kesirler",
    "kazanim_kod": "M.5.2.3",        # ← Zorlu eşleme
    "content_type": "ornek_soru",     # konu_anlatimi / ornek_soru / etkinlik / alistirma
    "source": "MEB_2024_5.sinif_matematik_ders_kitabi",
    "page": 142,
}
```

### Kazanım Kodu Eşleme (En Zorlu Parça)

İki yol:

1. **Semi-manuel:** PDF'lerin başlık yapısını elle eşle — 1-2 gün. Genelde kitapların içerik tablosu kazanım kodlarına karşılık gelen bölümleri belirtir.
2. **LLM asistanlı:** Her chunk için Gemini'ye "bu metin hangi kazanıma denk düşer? Seçenekler: [...]" diye sor. Toplu olarak batch API ile ucuz.

En iyi sonuç: ikisinin karması. Başlık eşleştirme + belirsiz olanları LLM'e sor.

---

## 5. Embedding + Vector DB Seçimi

### Embedding Modeli

| Model | Avantaj | Dezavantaj |
|-------|---------|------------|
| `gemini-embedding-001` | Gemini ile aynı ekosistem, Türkçe iyi | API maliyeti |
| `text-embedding-004` (Google) | Çok ucuz, hızlı | Daha küçük boyut (768) |
| `multilingual-e5-large` (open-source) | Ücretsiz, self-host | Kurulum gerekiyor, GPU'da hızlı |

**Öneri:** Geliştirmede `text-embedding-004`, ciddileşirse `gemini-embedding-001`.

### Vector DB

| Seçenek | Ne zaman? |
|---------|-----------|
| **ChromaDB** | Geliştirme / tek makine, SQLite benzeri, sıfır setup |
| **pgvector** | Halihazırda Postgres varsa, tek DB |
| **Qdrant** | Prod, ücretsiz self-host seçeneği, yüksek performans |
| **Pinecone** | Managed, kolay ama maliyetli |

**Öneri:** ChromaDB lokal ile başla, büyürse Qdrant'a geç.

---

## 6. Retrieval Stratejisi

### Temel Sorgu

```python
query = f"{kazanim_metin} {difficulty_hint} örnek soru"
results = vectorstore.search(
    query=query,
    k=5,
    filter={
        "grade": req.grade,
        "kazanim_kod": req.kazanim_kod,
        "content_type": ["ornek_soru", "alistirma"],
    }
)
```

### Hibrit Retrieval (Önemli)

Matematik için tek başına dense embedding yetmez. "Eşkenar üçgen" exact match'i kaybedebilirsin.

**Çözüm:** Dense (embedding) + sparse (BM25 / keyword) karması — genelde 0.7 × dense + 0.3 × bm25. Çoğu vector DB bunu native destekler (Qdrant, Weaviate, Chroma 0.5+).

### Re-ranker (Opsiyonel Ama Etkili)

Top-5'i top-3'e daraltmak için cross-encoder (örn. `bge-reranker-v2-m3`). Embedding hızlı ama kaba; cross-encoder yavaş ama isabetli. Kombinasyon harika.

---

## 7. Prompt Entegrasyonu

Mevcut `build_user_prompt`'a yeni blok:

```
─── MEB DERS KİTABI PASAJLARI ───
Bu pasajlar hedef kazanım için MEB ders kitabından alınmıştır.
Stil, dil ve pedagojik yaklaşımı referans al (KOPYALAMA):

[Pasaj 1 — 5. sınıf ders kitabı, sf. 142, kazanım M.5.2.3]
Kesirlerde paydalar eşitse, toplama ve çıkarma işleminde paylar...

[Pasaj 2 — 5. sınıf alıştırma kitabı, problem 23]
Bir halının 3/8'i kırmızı, 4/8'i mavidir. Geriye...
```

Few-shot bloğu **kalır** — RAG onu değiştirmez, güçlendirir. Elle yazılmış stil kalibrasyonu + retrieved MEB içeriği birlikte çalışır.

---

## 8. Semantik Dedup (Bedava Kazanım)

Embedding altyapısı kurulu olduğu için mevcut string-level dedup semantik olana yükseltilir:

```python
q_emb = embed(new_question)
for prev_emb in history_embeddings:
    if cosine_similarity(q_emb, prev_emb) > 0.85:
        reject  # Sayılar farklı ama yapı/bağlam aynı
```

"Ali'nin 3 elması Ayşe'ye 2..." ile "Burak'ın 4 armudu Mert'e 1..." şu an dedup'tan geçer (farklı string) — semantik dedup ikisini benzer görür ve reddeder.

---

## 9. Mimariye Eklenecek Dosyalar

```
GenAgent/
├── knowledge_base/                  # YENİ
│   ├── raw/                         # Orijinal MEB PDF'leri
│   │   ├── 5_sinif_ders_kitabi_2024.pdf
│   │   └── ...
│   ├── processed/                   # Parse edilmiş + chunk'lanmış JSON
│   └── chroma_db/                   # Vector store (gitignore)
│
├── app/
│   ├── services/
│   │   ├── embedder.py              # YENİ — embedding wrapper
│   │   ├── retriever.py             # YENİ — query + filter + re-rank
│   │   ├── semantic_dedup.py        # YENİ — cosine benzerlik kontrolü
│   │   └── agent.py                 # DEĞİŞİR — retriever enjekte
│   │
│   └── prompts/
│       └── templates.py             # DEĞİŞİR — retrieved passage bloğu
│
└── scripts/                         # YENİ
    ├── ingest_pdfs.py               # PDF → chunk → embed → store
    ├── tag_kazanimlar.py            # LLM asistanlı kazanım etiketleme
    └── eval_rag_vs_mvp.py           # Karşılaştırmalı kalite ölçümü
```

---

## 10. Uygulama Planı — Faz Sıralaması

### Faz 1 — POC (1-2 gün)

**Amaç:** RAG'ın gerçekten fark yaratıp yaratmadığını anlamak.

- 1 sınıf (5. sınıf) × 1 konu (kesirler) × 1 PDF
- Manuel chunk (~100 chunk)
- ChromaDB lokal
- Agent'a `use_rag=True/False` flag'i ekle, MVP ile yan yana karşılaştır
- 20 soruluk kör değerlendirme: MVP vs RAG, hangi daha MEB-like?

### Faz 2 — Ölçekleme (3-5 gün)

**Amaç:** Tüm müfredatı kapla.

- 7 sınıf × tüm ders kitapları ingest
- Otomatik pipeline (`scripts/ingest_pdfs.py`)
- Kazanım etiketleme (semi-manuel + LLM yardımıyla)
- Hybrid retrieval
- İlk versiyonu servise bağla

### Faz 3 — Kalite (2-3 gün)

**Amaç:** Üretim kalitesini yükselt.

- Re-ranker ekle
- Semantic dedup ile string dedup'ı değiştir
- Evaluation harness: çeşitlilik skoru, doğruluk skoru, stil skoru
- Monitoring: hangi kazanımda hangi chunk çekiliyor görünürlüğü

---

## 11. Maliyet / Karmaşıklık Tablosu

| Kalem | Tahmini maliyet |
|-------|-----------------|
| **Embedding ingestion** (~1M token, tüm müfredat) | ~$1-5 tek seferlik |
| **Embedding sorguları** (üretim başı 1 query) | <$0.001 / üretim |
| **Vector DB** | ChromaDB $0 · Qdrant self-host $0 · Pinecone managed $50-100/ay |
| **PDF parsing / chunking geliştirme** | 1-2 gün developer |
| **Kazanım etiketleme** | 2-3 gün developer (veya ~$20 LLM cost fully automated) |
| **Retriever + agent entegrasyonu** | 1-2 gün developer |
| **Re-ranker (opsiyonel)** | +1 gün |

**Toplam ilk kurulum:** ~1 hafta developer + <$50 cloud maliyeti

---

## 12. Hukuki Not

MEB ders kitapları **kamusal kullanıma açık**. Ancak:

- Yeniden yayımlama ≠ dahili RAG kullanımı (güvenli)
- Üretilen sorular **transformative work** sayılır (RAG sadece referans, çıktı türetilmiş içerik)
- Yine de production'a geçmeden kurum hukuku kısa bir onay versin

---

## 13. Geçiş Kriteri — RAG Ne Zaman Gerekir?

Şunlardan en az biri tetiklenirse RAG'a geç:

- ☐ Kullanıcı/öğretmen geri bildirimi: "Sorular MEB ders kitabıyla örtüşmüyor" veya "tek tip"
- ☐ Aynı kazanımda 50+ üretim sonrası **benzersiz soru oranı < %60**
- ☐ Manuel few-shot bakımı **sürdürülemez** (yüzlerce örneği güncellemek zor)
- ☐ **Yeni sınıf ekleme** ihtiyacı (8-12 için manuel yaklaşım bariz maliyetli)
- ☐ Zorluk kalibrasyonunun "orta" ile "zor" arası **bulanık** kaldığına dair geri dönüşler

Bu kriterlerden birini veri ile doğrulamadan RAG'a geçmek **over-engineering** olur.

---

## 14. Hızlı Başlangıç Kontrol Listesi

RAG implementasyonuna başlamadan önce:

- [ ] MVP kalite metriği toplandı (çeşitlilik skoru, doğruluk skoru, kullanıcı geri bildirimi)
- [ ] Geçiş kriterlerinden en az biri tetiklendi
- [ ] MEB ders kitabı PDF'leri indirildi (`knowledge_base/raw/`)
- [ ] Embedding API (Google/OpenAI/local) seçildi
- [ ] Vector DB seçimi yapıldı (ChromaDB → Qdrant → Pinecone rotası)
- [ ] Kurum hukuku onayı alındı (prod için)
- [ ] POC için değerlendirme rubriği hazır (20 sorulu kör test)
