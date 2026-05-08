# Deploy Guide — Sprint 8

Sıfır maliyetli production deploy. **Toplam süre: ~45-60 dk** (hesap açma dahil).

```
GitHub repo (main branch)
    │
    ├─→ Render: backend (FastAPI Docker)         → meb-genagent-backend.onrender.com
    │   └─ knowledge_base/ image içinde, history.sqlite3 runtime'da
    │
    ├─→ Vercel: frontend (Next.js)                → meb-genagent.vercel.app
    │   └─ Clerk auth + backend'e fetch
    │
    └─→ UptimeRobot: 14 dk'da bir /healthz ping  → cold start sıfır
```

## Sıralı checklist

- [ ] 1. Clerk hesabı + uygulama oluştur ([clerk.com](https://clerk.com))
- [ ] 2. Render hesabı + backend deploy (render.yaml ile)
- [ ] 3. Vercel hesabı + frontend deploy
- [ ] 4. Backend'e Vercel URL'ini CORS_ORIGINS olarak ekle
- [ ] 5. UptimeRobot hesabı + /healthz monitor
- [ ] 6. Live smoke test (kayıt → üret → PDF indir)

---

## 1. Clerk auth setup (~5 dk)

1. [clerk.com/sign-up](https://clerk.com/sign-up) → ücretsiz hesap aç (10k MAU/ay)
2. **Create application** → adı: `meb-genagent`
3. Sign-in options: **Email** + **Google** (öğretmenler için kolay)
4. **API Keys** sekmesi → şu iki değeri kopyala:
   - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` (pk_test_… veya pk_live_…)
   - `CLERK_SECRET_KEY` (sk_test_… veya sk_live_…)
5. **Domains** sekmesi → Vercel deploy URL'i hazır olduğunda ekle (Adım 3'te)

> Test mode'da kalabilirsin (50 user'a kadar). Production mode için
> `Production` toggle'ını aç + custom domain (opsiyonel).

---

## 2. Render backend deploy (~15 dk)

1. [render.com](https://render.com) → GitHub ile sign in (ücretsiz, kart yok)
2. **New** → **Blueprint** → repo'yu seç (`meb-math-worksheet-agent`)
3. Render `render.yaml`'ı otomatik okur, **Apply** bas
4. Açılan service'in **Environment** sekmesinde şu sırları (`sync: false`) gir:

| Key | Değer |
|---|---|
| `GEMINI_API_KEY` | Google AI Studio'dan al ([aistudio.google.com](https://aistudio.google.com/app/apikey)) |
| `API_KEYS` | Rastgele güçlü string üret (ör. `openssl rand -hex 32`); frontend'in `NEXT_PUBLIC_API_KEY`'iyle aynı olacak |
| `SENTRY_DSN` | (opsiyonel) sentry.io'da proje aç → DSN al |
| `CORS_ORIGINS` | **Şimdilik boş bırak**, Vercel URL'i Adım 3 sonrası buraya |
| `ANTHROPIC_API_KEY` | (opsiyonel, fallback) — boş bırakılabilir |

5. **Manual Deploy** → **Deploy latest commit** (ilk build ~5-8 dk; ChromaDB image
   içinde geldiği için ek setup gerekmez)
6. Build başarılıysa: `https://meb-genagent-backend.onrender.com/healthz` → `{"status":"ok"}`
7. Backend URL'ini bir yere not al (Vercel'de kullanacaksın)

**Önemli:** Free tier 15 dk inaktif sonra uyur; ilk istek ~30-60sn cold start.
UptimeRobot ile çözüyoruz (Adım 5).

---

## 3. Vercel frontend deploy (~10 dk)

1. [vercel.com/signup](https://vercel.com/signup) → GitHub ile sign in
2. **Add New** → **Project** → repo'yu seç → **Import**
3. **Configure Project**:
   - **Root Directory**: `frontend` ⚠ KRITIK
   - **Framework Preset**: Next.js (otomatik algılanır)
   - **Build Command**: default (`npm run build`)
4. **Environment Variables** ekle:

| Key | Değer |
|---|---|
| `NEXT_PUBLIC_API_URL` | Render backend URL'i (Adım 2'den) |
| `NEXT_PUBLIC_API_KEY` | Adım 2'deki `API_KEYS` ile aynı string |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk publishable key |
| `CLERK_SECRET_KEY` | Clerk secret key |
| `NEXT_PUBLIC_CLERK_SIGN_IN_URL` | `/sign-in` |
| `NEXT_PUBLIC_CLERK_SIGN_UP_URL` | `/sign-up` |
| `NEXT_PUBLIC_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL` | `/generate` |
| `NEXT_PUBLIC_CLERK_SIGN_UP_FALLBACK_REDIRECT_URL` | `/generate` |

5. **Deploy** → ~2-3 dk
6. Deploy URL'ini al (ör. `https://meb-genagent.vercel.app`)
7. Clerk dashboard → **Domains** → Vercel URL'ini ekle

---

## 4. Backend'e Vercel URL'i (CORS) (~2 dk)

1. Render → service → **Environment**
2. `CORS_ORIGINS` =
   ```
   https://meb-genagent.vercel.app,https://meb-genagent-*.vercel.app
   ```
   (ikinci pattern preview deploy'lar için)
3. **Save Changes** → service otomatik restart olur (~30sn)

---

## 5. UptimeRobot — cold start fix (~3 dk)

1. [uptimerobot.com](https://uptimerobot.com) → ücretsiz hesap (50 monitor)
2. **Add New Monitor**:
   - **Type**: HTTP(s)
   - **Friendly name**: `MEB Backend Healthz`
   - **URL**: `https://meb-genagent-backend.onrender.com/healthz`
   - **Monitoring interval**: `5 minutes` (free tier minimum) — Render 15 dk
     sonra uyuduğu için bu yeter
3. **Create Monitor**

> 5 dk'da bir ping → backend hep uyanık → kullanıcılar cold start yaşamaz.
> Aylık ~8640 ping; UptimeRobot free tier rahat kaldırır.

---

## 6. Live smoke test (~5 dk)

Vercel deploy URL'inden:

- [ ] Landing açılıyor mu? (`/`)
- [ ] **Sign up** ile yeni hesap aç (test email)
- [ ] `/generate`'e otomatik yönlendir
- [ ] Form doldur (Sınıf 5 / Cebir / M.5.5.1 / Orta / 5 soru)
- [ ] **Üret** → ~30sn sonra sorular geldi
- [ ] **PDF indir** → Türkçe karakterler doğru
- [ ] Aynı parametrelerle tekrar üret → ⚡ **Cache** rozeti, ~1sn
- [ ] `/history` → kayıt görünüyor

Hata olursa:
- **CORS error** (browser console): Render'da `CORS_ORIGINS`'i kontrol et
- **401**: `NEXT_PUBLIC_API_KEY` ≠ Render'daki `API_KEYS` (eşit olmalı)
- **502/503**: Render service uyumuş, ilk istek 30-60sn bekle (UptimeRobot devreye girince çözülür)
- **Clerk redirect döngüsü**: Clerk Domains'e Vercel URL'i ekledin mi?

---

## Maliyet beklentisi (50 öğretmen, ~10 kağıt/ay/user)

| Servis | Plan | Aylık |
|---|---|---|
| Render web service | Free | $0 |
| Vercel | Hobby (free) | $0 |
| Clerk | Free (10k MAU) | $0 |
| UptimeRobot | Free (50 monitor) | $0 |
| Sentry | Free (5k event/ay) | $0 |
| Gemini API | Pay-as-you-go | $0.20-0.50 (cache hit'le düşer) |
| **Toplam** | | **~$0.50/ay** |

Domain (opsiyonel): yıllık ~$15. Cloudflare DNS/proxy ücretsiz.

---

## Production sonrası bakım

- **Cost**: Render dashboard → Logs → "cost_meter" arat → token usage görünür
- **Cache hit oranı**: Lokalde `python scripts/cache_report.py` (prod'da log'tan çıkar)
- **Hata tracking**: Sentry dashboard → Issues
- **Eval gate**: GitHub Actions haftalık Pazartesi 02:00 UTC otomatik (`.github/workflows/eval.yml`)

---

## Rollback

Bozuk deploy gelirse:

- **Render**: dashboard → Events → önceki deploy'da "Rollback" butonu
- **Vercel**: Deployments → istediğin deploy'da "Promote to Production"

Hızlı, otomatik. CI gate (`eval.yml`) PR'ları zaten threshold check'ten geçiriyor;
bozuk eval main'e merge olamaz.
