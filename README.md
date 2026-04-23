# 📐 MEB Matematik Çalışma Kağıdı Üretici

MEB müfredatına uygun (1-7. sınıf) matematik soruları üreten, **Gemini destekli FastAPI + Streamlit** mikroservisi.

Sınıf, konu, kazanım kodu ve zorluk seviyesi seçersin; servis MEB ders kitabı tarzında açık uçlu sorular + çözüm adımları + cevap anahtarı üretir.

## ✨ Özellikler

- **Hardcoded MEB müfredatı** — 1-7. sınıf, 5 öğrenme alanı, **107 kazanım** kodu ve metniyle
- **Kazanım × zorluk kalibrasyonu** — her kazanım için kolay / orta / zor somut sınırlar (sayı aralığı, adım sayısı, bağlam karmaşıklığı)
- **214 few-shot örnek** — her biri zorluk etiketli; prompt'a hedef zorluğa uyanlar önceliklendirilerek enjekte edilir
- **Katmanlı prompt** — System (sabit kural) + Few-shot (dinamik) + User (kazanım + soru tipi dağılımı)
- **Soru tipi taksonomisi** — işlem / sözel problem / kavram / akıl yürütme / modelleme / günlük hayat; zorluğa göre dağılım otomatik
- **Üretim geçmişi** — aynı isteği tekrarlayınca in-memory history ile önceki bağlamlardan uzaklaşır
- **Retry loop** — dedup sonrası eksik kalırsa ek Gemini çağrısı ile tamamlar
- **Zorluğa bağlı temperature** — kolay 0.55, orta 0.80, zor 1.00
- **Model fallback** — `gemini-2.5-flash` 503 verirse `flash-lite` → `pro` zincirine geçer
- **Streamlit arayüzü** — cascading dropdown'lar, kazanım önizlemesi, anında üretim

## 🏗️ Mimari

```
GenAgent/
├── app/
│   ├── main.py                 FastAPI uygulaması
│   ├── config.py               Ayarlar (.env)
│   │
│   ├── models/
│   │   ├── enums.py            Difficulty, QuestionType, TopicId, EducationLevel
│   │   └── schemas.py          Pydantic request/response modelleri
│   │
│   ├── data/
│   │   ├── curriculum.py       107 kazanım + difficulty_hints (kolay/orta/zor)
│   │   └── few_shot/           Sınıf başına örnek havuzu
│   │       ├── grade_1.py ... grade_7.py
│   │
│   ├── services/
│   │   ├── agent.py            Gemini agent, backoff, fallback, retry loop
│   │   ├── diversity.py        Soru tipi dağılımı + normalize hash dedup
│   │   ├── examples.py         Zorluk bilincinde few-shot seçici
│   │   └── history.py          (grade, topic, kazanim, difficulty) history cache
│   │
│   ├── routers/
│   │   ├── curriculum.py       GET grades / topics / kazanimlar
│   │   └── worksheets.py       POST /api/worksheets/generate
│   │
│   └── prompts/
│       └── templates.py        System + few-shot + user + retry prompt builder
│
├── streamlit_app.py            Streamlit arayüz
├── implementation_plan.md      İlk plan (Türkçe)
├── docs/
│   └── RAG_ROADMAP.md          Sonraki iterasyon: RAG tabanlı geliştirme
├── requirements.txt
├── .env.example
└── README.md
```

## 🚀 Kurulum

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements.txt
copy .env.example .env            # GEMINI_API_KEY değerini doldurun
```

## ▶️ Çalıştırma

### 1. Backend (FastAPI)
```bash
uvicorn app.main:app --reload
```
- Swagger UI: http://localhost:8000/docs

### 2. Arayüz (Streamlit)
Ayrı bir terminalde:
```bash
streamlit run streamlit_app.py
```
- Arayüz: http://localhost:8501

> Streamlit `API_BASE` ortam değişkeniyle farklı backend'e bağlanabilir:
> `set API_BASE=http://localhost:8000 && streamlit run streamlit_app.py`

## 🌐 API Endpoint'leri

| Method | Path | Açıklama |
|--------|------|----------|
| `GET`  | `/health` | Sağlık kontrolü |
| `GET`  | `/api/curriculum/grades` | Mevcut sınıfları listeler (1-7) |
| `GET`  | `/api/curriculum/grades/{id}/topics` | Sınıfa ait konular + kazanım sayısı |
| `GET`  | `/api/curriculum/grades/{id}/topics/{topic_id}/kazanimlar` | Konunun kazanımları + metinleri |
| `POST` | `/api/worksheets/generate` | Çalışma kağıdı üretir |

### Örnek İstek

```bash
curl -X POST http://localhost:8000/api/worksheets/generate \
  -H "Content-Type: application/json" \
  -d '{
    "grade": 5,
    "topic_id": "cebir",
    "kazanim_kod": "M.5.5.1",
    "difficulty": "zor",
    "question_count": 5
  }'
```

### Cevap (kısaltılmış)

```json
{
  "worksheet": {
    "title": "5. Sınıf - Cebir ve Denklemler Çalışma Kağıdı",
    "grade": 5,
    "topic": "Cebir ve Denklemler",
    "difficulty": "zor",
    "question_count": 5,
    "questions": [
      {
        "number": 1,
        "question": "Bir sayının 4 katından 10 eksik, 30 elmaya eşittir. Bu sayının 5 katından 20 eksik kaç elma olur?",
        "answer": "55",
        "solution_steps": "4x - 10 = 30 → x = 10. 5×10 - 20 = 30. ...",
        "kazanim_kod": "M.5.5.1",
        "question_type": "akil_yurutme"
      }
    ],
    "answer_key": [ ... ]
  },
  "metadata": {
    "generated_at": "2026-04-23T12:00:00Z",
    "model": "gemini-2.5-flash",
    "curriculum": "MEB"
  }
}
```

## 📋 Müfredat Kapsamı

| Sınıf | Kapsam | Kazanım Sayısı |
|-------|--------|----------------|
| 1 | 100'e kadar sayılar, temel geometri, örüntüler | 12 |
| 2 | 1000'e kadar, çarpmaya giriş, cm/m | 12 |
| 3 | 10.000'e kadar, dört işlem, kesirlere giriş | 14 |
| 4 | Büyük sayılar, kesir türleri, açılar, alan | 16 |
| 5 | 9 basamaklı sayılar, kesir toplama-çıkarma, denklemler | 18 |
| 6 | Tam sayılar, kesirlerle dört işlem, alan formülleri | 16 |
| 7 | Rasyonel sayılar, çember-daire, eşitsizlikler, oran-orantı | 19 |

**Toplam: 107 kazanım · 214 few-shot örnek**

> 1-2. sınıflarda "Kesirler" alanı mevcut olmadığından bu sınıf-konu kombinasyonu API tarafından 400 ile reddedilir.

## 🔮 Sonraki İterasyon: RAG ile Geliştirme

MVP şu an **hardcoded kazanımlar + elle yazılmış few-shot** ile çalışıyor. Sonraki büyük adım: **MEB ders kitaplarını RAG (Retrieval-Augmented Generation) pipeline'ı ile entegre etmek.**

Detaylı yol haritası: **[docs/RAG_ROADMAP.md](docs/RAG_ROADMAP.md)**

### Kısa Özet — RAG Neden Gerekli?

Şu an Gemini'ye kazanım metni (1 cümle) + 3 hint + 2-3 few-shot veriliyor. RAG'la **MEB ders kitabından alınan gerçek pasajlar** prompt'a enjekte edilecek. Gemini benzetmez, doğrudan okur.

### Geçiş Kriterleri

Aşağıdakilerden en az biri tetiklenirse RAG'a geçilecek:

- Geri bildirim: "Sorular MEB ders kitabıyla örtüşmüyor" / "tek tip"
- Aynı kazanımda 50+ üretim sonrası benzersiz soru oranı < %60
- Manuel few-shot bakımı sürdürülemez hale gelir
- 8-12. sınıf ekleme ihtiyacı doğar

### Mimariye Eklenecekler

```
knowledge_base/
├── raw/                    MEB PDF'leri
├── processed/              Chunk'lanmış veri
└── chroma_db/              Vector store

app/services/
├── embedder.py             Embedding wrapper
├── retriever.py            Hybrid dense + BM25
└── semantic_dedup.py       Cosine similarity dedup
```

Detaylar: **[docs/RAG_ROADMAP.md](docs/RAG_ROADMAP.md)**

## 📐 İlk Plan Dokümanı

Projenin ilk tasarım dokümanı: **[implementation_plan.md](implementation_plan.md)**

## 🧪 Teknoloji

- **Backend:** Python 3.13 + FastAPI + Pydantic 2
- **LLM:** Google Gemini (`google-genai`), `gemini-2.5-flash` (fallback: `flash-lite`, `pro`)
- **Arayüz:** Streamlit
- **Config:** pydantic-settings (.env)

## ⚖️ Lisans

(TODO: Uygun lisans eklenecek)
