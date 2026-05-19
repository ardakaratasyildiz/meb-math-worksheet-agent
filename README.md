# Soru Atölyesi — MEB Matematik Çalışma Kağıdı Üretici

MEB matematik müfredatına uygun (1.→7. sınıf) çalışma kağıdı üreten otomatik
sistem. Gemini destekli, RAG tabanlı; SVG geometri şekilleri, LaTeX matematik
notasyonu ve 16 farklı soru tipi (LGS-stili çoktan seçmeli dahil) üretir.

**Canlı:**
- Frontend: https://sheetgen.vercel.app
- Backend: https://sheetgen-backend.onrender.com

## Mimari

```
Soru Atölyesi
├── Backend (FastAPI · Python 3.13)        — Render Docker, free tier
│   ├── /api/curriculum/*                  — sınıf/konu/kazanım listeleri
│   ├── /api/worksheets/generate           — JSON üretim (LLM)
│   ├── /api/worksheets/generate.pdf       — PDF üretim
│   ├── /api/worksheets/render.pdf         — JSON → PDF (LLM çağrısız)
│   ├── /api/worksheets/generate.stream    — SSE streaming
│   ├── /admin/*                           — cache stats, history (X-Admin-Key)
│   └── /healthz, /readyz                  — health check
│
├── Frontend (Next.js 15 · TypeScript · Tailwind · shadcn/ui)
│   ├── /                                  — Landing + features + FAQ
│   ├── /generate                          — Form + üretim + preview
│   ├── /history                           — Kullanıcı bazlı geçmiş
│   ├── /sign-in, /sign-up                 — Clerk v7 auth (10k MAU free)
│   └── /pricing, /features                — Bilgi sayfaları
│
├── Vector DB                              — ChromaDB on-disk, 8449 chunk
├── DB (history + LLM cache)               — Turso (libSQL) embedded replica
└── LLM                                    — Gemini 2.5 Flash + Anthropic fallback
```

## Özellikler

### Müfredat & İçerik
- **123 kazanım** kodu (M.X.Y.Z), 1-7. sınıf MEB matematik
- **7 öğrenme alanı**: Doğal Sayılar, Kesirler, Geometri, Ölçme, Cebir, Veri İşleme, Olasılık
- **Kazanım × zorluk kalibrasyonu** — her kazanım için kolay/orta/zor somut sınırlar
- **ChromaDB few-shot havuzu**: 8449 chunk (MEB ders kitabı + LGS-tarzı testler + sentetik)
- **PDF kaynak format**: `X.sinif_N.pdf` ya da `new_X_sinif_N.pdf`

### Soru Tipleri (16 tip, 3 grup)
- **Açık uçlu sözel**: işlem, sözel problem, kavram, akıl yürütme, modelleme, günlük hayat
- **Görsel ve yapısal**: salt işlem (LaTeX), tablo (HTML), geometri (SVG), grafik (SVG), örüntü (SVG)
- **Format çeşitliliği**: çoktan seçmeli, boşluk doldurma, doğru/yanlış, eşleştirme, sıralama

### Render Katmanı
- **Frontend**: react-markdown + remark-gfm (tablolar) + remark-math + rehype-katex (LaTeX)
- **SVG**: isomorphic-dompurify ile sanitize, inline render
- **PDF**: ReportLab + svglib (SVG embed) + matplotlib mathtext (LaTeX → PNG)
- **Cevapsız sürüm**: kullanıcı PDF'te cevap anahtarı/çözüm sayfasını kapatabilir (sınav modu)

### Kalite Kapıları
- **SymPy math verifier** — deterministic aritmetik kontrol
- **Gemini critic** — LLM judge (kazanım uyumu + zorluk)
- **Semantic dedup** — cosine ≥ 0.88 ile tekrar önleme
- **Math-aware retry** — eksik tip dağılımı yeniden istenir
- **Source-aware retrieval** — aynı PDF'ten max 2 chunk (textbook retrieval)

### Üretim Akışı (Multi-Mode)
- **Tek zorluk** — kullanıcı seçilen zorluk
- **Karışık** — kolay (30%) + orta (40%) + zor (30%) shuffle
- **Progresyon** — aynı dağılım, kolay → orta → zor sıralı

### LLM Cache
- ChromaDB `generation_cache` koleksiyonu, cosine > 0.92 ile semantic hit
- Aynı (sınıf, konu, kazanım, zorluk, sayı) parametre kombinasyonları cache'ten döner

### Multi-LLM Fallback Chain
- Gemini 2.5 Flash → Flash Lite → Pro → Anthropic Claude Sonnet
- 503/timeout'larda otomatik geçiş, 3 retry per model

## Kurulum (Lokal)

> Lokal Docker hedeflenmedi. Backend doğrudan uvicorn ile, frontend Codespaces'tan.

```bash
# Backend
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements.txt
copy .env.example .env            # GEMINI_API_KEY zorunlu

# Backend çalıştır
uvicorn app.main:app --reload     # http://localhost:8000

# Frontend (Codespaces içinde önerilir — Node lokal'de yok)
cd frontend
npm install
npm run dev                       # http://localhost:3000
```

## Önemli Endpoint'ler

| Method | Path | Açıklama |
|---|---|---|
| `GET` | `/healthz` | Render health check |
| `GET` | `/readyz` | ChromaDB + Gemini ready |
| `GET` | `/api/curriculum/grades` | Sınıf listesi (1-7) |
| `GET` | `/api/curriculum/grades/{id}/topics` | Konu listesi |
| `GET` | `/api/curriculum/grades/{id}/topics/{topic_id}/kazanimlar` | Kazanım listesi |
| `POST` | `/api/worksheets/generate` | JSON üretim |
| `POST` | `/api/worksheets/generate.pdf` | PDF üretim |
| `POST` | `/api/worksheets/render.pdf` | Mevcut worksheet → PDF |
| `POST` | `/api/worksheets/generate.stream` | SSE streaming |

### Üretim isteği örneği

```bash
curl -X POST https://sheetgen-backend.onrender.com/api/worksheets/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <API_KEY>" \
  -d '{
    "grade": 5,
    "topic_id": "cebir",
    "kazanim_kod": "M.5.5.1",
    "difficulty": "orta",
    "question_count": 10,
    "difficulty_mode": "single",
    "question_types": null,
    "include_answer_key": true,
    "include_solutions": true,
    "tenant_id": "user-abc-123"
  }'
```

## Deployment

**Render** (backend): `render.yaml` blueprint, auto-deploy main push.
**Vercel** (frontend): GitHub integration, auto-deploy main push.
**Turso** (libSQL): `TURSO_DATABASE_URL` env set, history + cache kalıcı.
**Cold start**: GitHub Actions cron (`.github/workflows/keepalive.yml`) 5 dk'da bir `/healthz`'a ping.

## Sprint Geçmişi (kısa özet)

| Sprint | Tarih | İçerik |
|---|---|---|
| 1-4 | 2026-04 | Kalite + çeşitlilik + production rigor + UX (PDF, multi-LLM) |
| 5 | 2026-05-07 | 1-7. sınıf MEB PDF ingest (ChromaDB 7267) |
| 6 | 2026-05 | Backend prod-ready (Docker, healthz, Sentry, cache) |
| 7 | 2026-05 | Next.js + Clerk frontend |
| 8 | 2026-05 | Render Blueprint + deploy artefaktları |
| 9 + 9.5 | 2026-05-09 | Clerk v7 migration, Turso, admin endpoints |
| 10 | 2026-05-12 | **Go-live** (Render + Vercel + Turso) |
| 11 | 2026-05-12 | UI rewrite + Soru Atölyesi rebrand |
| **12-A** | 2026-05-19 | 5 yeni soru tipi + kullanıcı toggle UX |
| **12-B** | 2026-05-19 | SVG/LaTeX render + 75 yeni PDF (734 yeni chunk) |

**A/B eval (Sprint 12-B sonrası):** delivered ratio %100, critic pass %100,
avg duration 29s, 18/18 başarılı senaryo.

## Değerlendirme & CI

```bash
# Hızlı doğrulama (~2 dk, 1 senaryo)
python scripts/eval/ab_runner.py --quick

# Tam karşılaştırma (~25-30 dk, 6 senaryo × 3 config × 3 iter)
python scripts/eval/ab_runner.py

# Eşik kontrolü
python scripts/eval/check_regression.py \
    --raw knowledge_base/eval/ab_raw_<ts>.json \
    --config baseline
```

`.github/workflows/eval.yml` — `quick-eval` PR'da, `full-eval` nightly cron'da.

## Teknoloji Stack

| Katman | Teknoloji |
|---|---|
| Backend | Python 3.13, FastAPI, Pydantic 2, slowapi |
| LLM | Gemini 2.5 Flash, Anthropic Claude Sonnet (fallback) |
| Vector DB | ChromaDB (on-disk, image'a commit) |
| Cache + History | Turso (libSQL embedded replica) ya da sqlite3 fallback |
| Frontend | Next.js 15, TypeScript, Tailwind, shadcn/ui |
| Auth | Clerk v7 (10k MAU free) |
| Render katmanı | react-markdown, remark-gfm, remark-math, rehype-katex, isomorphic-dompurify |
| PDF | ReportLab, svglib (<1.6), matplotlib mathtext |
| Hosting | Render (backend), Vercel (frontend) |
| Observability | Sentry (5k event/ay free) |

## Lisans

(TODO: Uygun lisans eklenecek)
