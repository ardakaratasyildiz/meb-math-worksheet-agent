# SheetGen — Frontend

Next.js 14 + TypeScript + Tailwind + shadcn/ui + Clerk auth.
Backend: aynı repo'nun kökündeki FastAPI uygulaması (`../app`).

## Geliştirme (GitHub Codespaces)

Lokal makinede Node.js gerekmez — Codespaces tarayıcıdan Node + npm hazır gelir.

```bash
# Yeni Codespace aç (GitHub repo > Code > Codespaces > New)
cd frontend
cp .env.example .env.local        # Clerk + backend URL'leri doldur
npm install                        # ~1-2 dk
npm run dev                        # http://localhost:3000
```

Aynı Codespace içinde backend de çalışıyorsa (port 8000), frontend
otomatik bağlanır.

## Lokal (Node varsa)

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

## Ortam değişkenleri

| Anahtar | Açıklama |
|---|---|
| `NEXT_PUBLIC_API_URL` | Backend URL'i. Lokal: `http://localhost:8000`. Prod: Render URL. |
| `NEXT_PUBLIC_API_KEY` | Backend `API_KEYS` env'inden bir tanesi (boş bırakılırsa auth devre dışı; prod'da MUTLAKA set et). |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | clerk.com'dan al. |
| `CLERK_SECRET_KEY` | clerk.com'dan al (asla repo'ya commit etme). |

## Yapı

```
frontend/
├── app/
│   ├── layout.tsx          ← ClerkProvider + ThemeProvider + TopNavBar + Toaster
│   ├── globals.css         ← HSL theme: emerald primary, light/dark
│   ├── page.tsx            ← Landing (public)
│   ├── generate/page.tsx   ← Üretim ekranı (login gerekli)
│   ├── history/page.tsx    ← localStorage tabanlı geçmiş (login gerekli)
│   ├── sign-in/[[...sign-in]]/page.tsx
│   └── sign-up/[[...sign-up]]/page.tsx
├── components/
│   ├── ui/                 ← shadcn primitives (button, card, input, ...)
│   ├── theme-provider.tsx  ← next-themes
│   ├── TopNavBar.tsx       ← logo + dark/light + UserButton
│   ├── GenerateForm.tsx    ← cascading select form
│   ├── QuestionPreview.tsx ← skeleton + sonuç + PDF buton
│   ├── QuestionCard.tsx    ← tek soru render
│   └── HistoryList.tsx     ← geçmiş listesi
├── lib/
│   ├── utils.ts            ← cn() helper
│   ├── types.ts            ← Backend Pydantic'in TS karşılığı
│   ├── api.ts              ← Backend fetch wrapper
│   ├── store.ts            ← Zustand: form state
│   └── history.ts          ← localStorage history CRUD
├── middleware.ts           ← Clerk auth middleware (/generate, /history korumalı)
└── tailwind.config.ts      ← emerald primary, shimmer/fade animations
```

## Auth akışı

- `/`, `/sign-in`, `/sign-up` → public
- `/generate`, `/history` → Clerk middleware ile korumalı; oturumsuz kullanıcılar
  `/sign-in`'e yönlendirilir, login sonrası `/generate`'e döner.

## Backend bağımlılığı

Frontend, backend'in şu endpoint'lerini kullanır:

- `GET  /api/curriculum/grades`
- `GET  /api/curriculum/grades/{grade}/topics`
- `GET  /api/curriculum/grades/{grade}/topics/{topic_id}/kazanimlar`
- `POST /api/worksheets/generate` → JSON sonuç
- `POST /api/worksheets/generate.stream` → SSE (Sprint 7.5+ kullanılacak)
- `POST /api/worksheets/render.pdf` → PDF blob

Backend lokal çalıştırma:

```bash
cd ..
uvicorn app.main:app --reload --port 8000
```

## Deploy (Vercel)

1. Vercel'de yeni proje, root directory `frontend`
2. Build command: `npm run build` (default)
3. Env vars: yukarıdaki tablo
4. Backend URL'ini `NEXT_PUBLIC_API_URL` olarak set et

## Notlar

- **Tema rengi**: emerald-600 (`hsl(161, 94%, 30%)` light / `hsl(161, 84%, 42%)` dark).
  Değiştirmek için `app/globals.css`'teki `--primary` ve `--ring` değişkenlerini güncelle.
- **Dark mode** default; kullanıcı `TopNavBar`'dan toggle edebilir.
- **History**: tarayıcı localStorage'ında — cihazlar arası senkron için
  Sprint 7.5'te backend `user_history` endpoint'i eklenecek.
- **SSE streaming**: backend endpoint hazır ama UI hâlâ blocking fetch
  kullanıyor (basit, çalışıyor). Gerçek perceived latency kazanımı için
  Sprint 7.5'te EventSource entegrasyonu yapılacak.
