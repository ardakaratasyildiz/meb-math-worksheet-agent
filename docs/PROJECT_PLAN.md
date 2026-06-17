# Soru Atölyesi — Tek Proje Planı (Master Roadmap)

> **Bu dokümanın amacı:** Projenin TEK doğru yol haritası. Kim devam ederse etsin,
> buraya bakıp **aynı sırayla, aynı stratejiyle** ilerler. Diğer tüm plan
> dokümanları (`GROWTH_ROADMAP`, `LEARNING_PLATFORM_PLAN`, `GRADE8_LGS_PLAN`,
> `LGS_SEO_PLAN`, `FUNNEL_FIXES_PLAN`, `ANON_GENERATION_PLAN`, `RAG_*`) artık bu
> planın **detay ekleridir**; çelişki olursa **bu doküman geçerlidir**.
>
> Güncel: 2026-06-17 (mevcut durum koddan doğrulandı).

---

## 0. Bu dokümanı nasıl kullan (devralan geliştirici için)

1. **§1–3'ü oku** → ürünü, mimariyi, nerede olduğumuzu anla.
2. **§4'ü içselleştir** → "sırada ne var?" sorusunu bu kural cevaplar.
3. **§5'e git** → ilk açık (🟡/🔴) kalemi bul, o fazın çıkış kapısını geç, sonrakine geç.
4. Yeni fikir → kod değil, **§5'e backlog satırı** + §4 ritüeliyle sıraya sok.

Tek cümlelik çalışma kuralı:
> **"Bu iş §2'deki metriği kıpırdatıyor mu VE açık bir fazda mı? Değilse backlog."**

---

## 1. Ürün ve mimari oryantasyonu

**Ne:** Soru Atölyesi — MEB matematik müfredatına (1–8. sınıf + LGS) uygun çalışma
kağıdı/quiz üreten, RAG tabanlı, Gemini destekli üretim platformu. İki yüzey:
- **`/generate`** → üret → **PDF indir** (gel-al, açık-uçlu dahil tüm tipler).
- **`/practice`** → üret → **site içinde çöz → otomatik puanla → geliş** (yalnız
  otomatik-puanlanabilir tipler; kişisel, login zorunlu).

**Canlı:** soruatolyesi.com (frontend Vercel), backend Render, DB Turso.

### Mimari (tek bakış)
```
Backend (FastAPI · Python 3.13 · Render)
  app/routers/    curriculum · worksheets · quizzes · me · admin · health · [shared*]
  app/services/   agent(LLM) · retriever(RAG) · grading · quiz_store · structured
                  progress · gamification · db_connection
  app/data/       curriculum.py (CURRICULUM[1..8] sözlüğü — sınıf/konu/kazanım)
  app/models/     schemas.py (Pydantic) · enums.py (QuestionType, Difficulty)
  app/prompts/    templates.py (üretim prompt'ları)
  scripts/        ingest_* · extract_* · tag_* · eval/ (PDF → ChromaDB hattı)

Frontend (Next.js 15 · App Router · Vercel)
  app/            / (landing) · generate · coz/* · history · sign-in/up · [q/*]
  components/     GenerateForm · QuizSolver · ... (shadcn/ui tabanlı)
  lib/            api.ts(backend wrapper) · types.ts · curriculum.ts · analytics.ts(GA4)
                  store.ts(zustand)
  middleware.ts   Clerk auth — /practice, /history, /admin login-gated; gerisi public
  manifest.ts     PWA

Veri & servisler
  ChromaDB        on-disk, image'a commit (few-shot + textbook chunk havuzu)
  Turso (libSQL)  worksheet_history + quizzes/attempts/mastery_state + LLM cache
  LLM             Gemini 2.5 Flash → Flash Lite → Pro → Claude Sonnet (fallback zinciri)
```
*[shared*] / [q/*] = bu planda eklenecek (Faz 3 paylaşım).*

### Bilinmesi gereken kritik desenler
- **`tenant_id` = Clerk `userId`.** Frontend backend'i **doğrudan** paylaşılan
  `NEXT_PUBLIC_API_KEY` (X-API-Key) ile çağırır; backend `tenant_id`'yi
  **doğrulamadan güvenir** (Clerk JWT doğrulaması yok — bilinen sınır).
- **Anti-kopya:** quiz soruları **cevaplı** saklanır (sunucuda); çözücüye **cevapsız**
  gönderilir; puanlama **sunucuda** (`grade_quiz`, LLM'siz: normalize + SymPy).
- **Kalite kapıları:** SymPy math verifier + Gemini critic + semantic dedup. **Bu
  hendek matematik-özeldir** (yeni derslerde yeniden kurulmalı — §5 Faz 4).
- **Deploy:** main'e push → Render + Vercel otomatik deploy. **Frontend lokalde
  build edilemez** (node yok) → `frontend-ci` GitHub Action (lint+typecheck) ile doğrula.
- **Doğrulama:** routing/SSR/render değişiminde **merge öncesi Vercel preview URL'ini
  curl'le** (CI runtime hatası yakalamaz).
- **İsimlendirme (karar 2026-06-17):** kodda **İngilizce** route/identifier/dosya
  isimleri kullan; kullanıcıya görünen **Türkçe metin** (UI label, "Çöz & Geliş")
  ve **SEO keyword slug'ları** (`/lgs-matematik`, `/5-sinif-*`) Türkçe kalır. Bu
  gereği `/coz` → **`/practice`** rename'i yapıldı (alt: `/new`, `/progress`,
  `/history`, `/quiz`, `/shares`; `.coz-theme`→`.practice-theme`; `CozTodayCard`→
  `PracticeTodayCard`); eski `/coz/*` → 301 redirect (`next.config.mjs`).

---

## 2. Kuzey Yıldızı ve yöneten metrik

> **Kuzey yıldızı: erişim büyüt + içerik kapsamı genişlet. Para kazanma bunların
> ardından.** (Karar: 2026-06-17)

İçerik genişliği = büyüme kaldıracı (yeni içerik → yeni programatik SEO yüzeyi →
organik trafik). İki öncelik tek çark:
```
   Yeni içerik (sınıf/konu/ders)
            │
            ▼
   Programatik SEO yüzeyi  ──►  Organik trafik  ──►  Üretim (anonim, login'siz)
            ▲                                                │
            │                                                ▼
   Hız + maliyet (cache)  ◄──  Kullanım verisi  ◄──  PDF/QR + paylaşım → yeni kullanıcı
            │                                                │
            └───────────────  Dönüşüm + retention (/practice)  ◄──┘
```

### Yöneten metrik (her işin sınavı)
| Metrik | Tanım | Kaynak |
|---|---|---|
| **Organik oturum / hafta** | SC + GA4 organik trafik | Search Console, GA4 |
| **Haftalık aktif kullanıcı (WAU)** | Haftada ≥1 worksheet **veya** quiz üreten/çözen benzersiz kullanıcı | GA4 + Turso |

İkincil: ziyaret→ilk-üretim dönüşümü, indekslenen sayfa sayısı, `/practice` dönen-kullanıcı
+ seri (streak), PDF/QR→yeni-ziyaret, **paylaşılan quiz→çözülme→üye oranı**.

---

## 3. Mevcut durum (koddan doğrulandı, 2026-06-17)

### ✅ Bitti (canlıda)
| Alan | Kanıt |
|---|---|
| Cold-start çözümü | warm-up ping (`59dc2e8`) + `/healthz` HEAD UptimeRobot uyumu (`5dfc2e2`) |
| 8.sınıf + LGS içeriği | `CURRICULUM[8]`, `schemas.py le=8`, ChromaDB ingest (`4e6542a`), startup ingest (`1e16d31`), UI (`9859527`) |
| Anonim üretim | login'siz `/generate`, PDF indirme Clerk kapısında (`#46`) |
| White-label PDF | header'a kurum/öğretmen logosu (`#40`) |
| PWA + paylaşım | kurulabilir PWA (`app/manifest.ts`) + "WhatsApp'a at" (`#39`) |
| Programatik SEO | LGS hub + 71+ long-tail landing (`#41/#42/#44`); SC = DNS TXT doğrulanmış |
| `/practice` öğrenme döngüsü | `yeni · quiz/[id] · ilerleme · history` + oyunlaştırma rozet/seviye/seri (`#36`) + 30 günlük grafik (`#35`); API `quizzes.py`+`me.py` |
| Mobil web UX | navbar hamburger (`#37`), responsive |

### 🟡 Açık gerçek boşluklar (fazlar bunları hedefler)
- North-star **dashboard** yok (Faz 0.2) · **PAT revoke + legal** (Faz 0.4)
- Faz 2 dönüşüm/viral **ölçümü** eksik (özellik var, ölçüm yok)
- **`/practice` paylaşımı: PR A+B ✅ canlı** (link paylaş + public `/q/[code]` çözme + üye-ol funnel). Kalan: PR C frontend (sahip sonuç panosu) + PR D (uygulama-içi paylaşım)
- SEO **otomasyonu** yok (içerik→sayfa elle) (Faz 1B)
- **Yeni dersler** yok (Faz 4) · **para kazanma** yok (Faz 5)
- 🔴 **Gemini billing/kota planı** yok (ölçek önkoşulu)

---

## 4. Çalışma ilkesi — anti-dağınıklık ritüeli

"Kafası kopuk tavuk" hissinin sebebi plansızlık değil, **önceliksiz paralel
track'lerdi.** Çözüm = haftada bir, ~15 dk:

1. **Bak:** §2 metrikleri bu hafta ne yaptı?
2. **Seç:** Sıradaki işi **yalnız mevcut açık fazdan** + **§2'yi en çok kıpırdatandan** seç.
3. **Kapı:** Mevcut fazın çıkış kapısı geçilmeden sonraki faza ağırlık verme
   (paralel-ucuz işler hariç, işaretli).
4. **Yaz:** Yeni fikir → §5 backlog satırı, hemen kod değil.

İlke: **önce traction, sonra breadth; ölç-yönlendir, körlemesine değil;
kapasite-bilinçli (Gemini kotası her genişlemenin önünde).**

---

## 5. Faz faz yol haritası

Fazlar **kapasite-bağımsız sıralıdır** (hız kapasiteyle değişir, sıra değişmez).
Her fazın bir **çıkış kapısı** var; geçilmeden sonrakine ağırlık verme.

### FAZ 0 — Temel & görünürlük — ✅ büyük ölçüde DONE
Amaç: kör uçuşu bitir, dönüşüm sızıntılarını kapat (config/borç, özellik değil).

- 0.1 Cold-start ✅ (warm-up + UptimeRobot). *Trafik artınca → paid Render eşiği (§7).*
- **0.2 🟡 North-star dashboard** — GA4'te WAU + organik oturum + ziyaret→ilk-üretim'i
  **tek görünümde** topla; DebugView ile event'leri doğrula. *Her şeyin önkoşulu.*
- 0.3 Backlog konsolidasyonu ✅ (bu doküman).
- **0.4 🔴 Operasyonel borçlar** — PAT revoke (güvenlik); legal placeholder'ları
  doldur (KVKK/gizlilik — para track'inin önkoşulu). Düşük efor.

**Çıkış kapısı:** dashboard canlı + PAT revoke. → *Kalan: 0.2, 0.4.*

---

### FAZ 1 — İçerik × SEO çarkı (ANA MOTOR) — kısmen DONE, sürekli
Burada içerik (#4) ve büyüme (#1) birleşir: her içerik damlası → SEO yüzeyi.

- **1A 8.sınıf + LGS içeriği** ✅ DONE (detay: `GRADE8_LGS_PLAN.md`).
- **1B 🟡 Programatik SEO otomasyonu** — desen kurulu (71+ sayfa, `LGS_SEO_PLAN.md`).
  Açık iş: içerik→sayfa'yı **mekanikleştir** — yeni sınıf/konu/ders eklenince SEO
  sayfaları `CURRICULUM`'dan otomatik üretilip sitemap'e girsin (elle sayfa yazma yok).
  8.sınıf konu/kazanım sayfalarının SC'de indekslenmesini izle.

**Çıkış kapısı:** 8.sınıf SEO sayfaları indeksleniyor + organik oturum trend yukarı.

---

### FAZ 2 — Dönüşüm & virallik (Faz 1 ile PARALEL, ~$0) — DONE, ölçüm açık
- 2.1 Landing showroom ✅ / 2.3 PWA+WhatsApp ✅ / 2.4 White-label PDF ✅
  (detay: `FUNNEL_FIXES_PLAN.md`, `ANON_GENERATION_PLAN.md`).
- **🟡 Açık iş = ölçüm + iyileştirme (yeni özellik değil):** ziyaret→ilk-üretim
  dönüşümünü ve PDF/QR→yeni-ziyaret viral döngüsünü GA4'te gerçekten ölç; zayıf halkayı iyileştir.

**Çıkış kapısı:** dönüşüm + en az 1 viral kanal GA4'te ölçülüyor, trend izleniyor.

---

### FAZ 3 — Retention + Paylaşım (`/practice`) — v1 DONE, paylaşım = SIRADAKİ BÜYÜK İŞ
`/practice` kişisel döngüsü canlı (çöz→puanla→ilerleme→oyunlaştırma). **Açık ve en yüksek
büyüme değerli kalem: quiz paylaşımı** — retention'ı acquisition'a bağlayan viral kaldıraç.

#### Neden bu, neden şimdi
Bugün `/practice` kapalı kişisel döngü. Paylaşım dışarı açar (öğretmen→öğrenci,
öğrenci→arkadaş): her paylaşılan quiz, **login duvarı olmadan** çözülebilen bir viral
giriş noktası → çözen değer görür → "ilerlemeni takip et" ile üye olur.
**Ölçülen döngü: paylaş → link açıldı → çözüldü → üye oldu.**

#### Yeniden kullanılan altyapı (tek engel: owner-scope)
`_to_public()` cevap soyma, `grade_quiz()` puanlama, `attempts(solver_tenant_id)` →
**paylaşılan çözüm çözenin kendi ilerlemesine otomatik akar.** Tek mimari engel:
`QUIZ_STORE.get(quiz_id, owner_tenant_id)` owner-scoped → paylaşım = bu erişimi
**yalnız geçerli bir share üzerinden** güvenle açmak. `/q/*` rotası middleware'de
otomatik public.

#### Bağlayıcı kararlar
1. **Çözme PUBLIC (login yok)** — viralliğin amacı; çözüm sonrası "üye ol" CTA'sı.
2. **MVP = link/kod**; uygulama-içi kullanıcı→kullanıcı paylaşım **PR D'ye ertelendi**.
3. **Misafir opsiyonel isim girer** (`solver_label`) → sahip panosunda anlamlı.
4. Giriş yapmış çözenin denemesi kendi mastery'sine sayılır; misafirinki yalnız sahip panosuna.

#### Alt-fazlar (her PR bağımsız, tek başına test edilebilir)
> **Tam dosya/satır seviyesi detay: `SHARING_PLAN.md`.** Aşağısı sıra + kapsam.

- **PR A — Backend paylaşım + public çözme** ✅ DONE & MERGED (PR #48)
  - ✅ `shares` tablosu + `attempts` migration (`share_id`, `solver_label`) → `quiz_store.py`.
  - ✅ `QuizStore`: `create_share` (idempotent), `get_share_by_code`, `get_quiz_by_id`
    (owner-scope'suz), `revoke_share`, `record_attempt(..., share_id, solver_label)`,
    `list_shares`, `share_results`.
  - ✅ Public router `app/routers/shared.py` (`main.py` `prefix="/api/shared"`):
    `GET /{code}` (cevapsız), `POST /{code}/attempt` (per-IP rate-limit, misafir+üye).
  - ✅ `POST /api/quizzes/{id}/share` + `GET /api/me/shares` + `/shares/{id}/results`.
  - ✅ Şemalar + `tests/test_sharing.py` (anti-kopya regresyon dahil) — tüm suite geçti.
- **PR B — Frontend paylaş + public çözme sayfası** ✅ DONE & MERGED (PR #49) → **viral döngü canlı**
  - ✅ `ShareQuizButton` (link kopyala + WhatsApp `navigator.share`) → `QuizSolver` sonuç ekranı.
  - ✅ `app/q/[code]/page.tsx` (public): `QuizSolver` **shared mod** (`shareCode` prop);
    misafir "Adın" input'u; çözüm sonrası **üye-ol CTA**.
  - ✅ `lib/api.ts` + `lib/types.ts` + GA4 event'leri (`quiz_share_create/open/attempt/signup`).
- **PR C — Sahip sonuç panosu** (backend ✅ PR #48'de geldi) ← SIRADAKİ (frontend)
  - Kalan = frontend: `app/practice/shares/page.tsx` (liste) + `[shareId]/page.tsx`
    (sonuç tablosu); `/practice` hub'ına "Paylaşımlarım" kartı. (`GET /api/me/shares`
    + `/shares/{id}/results` zaten canlı.)
- **PR D — (sonra) uygulama-içi paylaşım** — `share_type='user'` + kullanıcı bulma
  (kullanıcı adı/davet) + gelen kutusu. `LEARNING_PLATFORM_PLAN` §13 açık sorusu çözülünce.

**Sıra:** A → B (viral döngüyü açar, en yüksek değer) → C (sahip değeri) → D (sonra).
**Çıkış kapısı:** paylaşılan quiz→çözülme→üye oranı GA4'te ölçülüyor.

**Mevcutu bozmama:** `/generate`, `/api/worksheets/*`, PDF, mevcut `get()`/`submit_attempt`
→ sıfır dokunuş; eklenen alanlar opsiyonel; `/q/*` silinse `/practice`+`/generate` etkilenmez.

---

### FAZ 4 — Yeni dersler (büyük içerik bahsi, KAPI arkasında)
> Açılış koşulu: matematik çarkı dönüyor (organik trafik + WAU trendi yukarı) **VE**
> kapasite (§7) çözülmüş. Erken başlama.

- ⚠️ **Kalite hendeği matematik-özel** (SymPy verifier + math critic). Yeni ders =
  yeni doğrulama stratejisi (LLM critic + küratörlü few-shot, deterministik verifier yok).
- **Strateji: dar pilot.** Önce yapısal/sayısal sorusu olan ders (ör. **LGS Fen** —
  MCQ + sayısal) tek konuda pilotla, kalite kapısını kur, sonra genişlet. Sözel-ağır
  (Türkçe okuma-anlama) en sona. Her ders Faz 1B çarkına girer (yeni SEO yüzeyi).

**Çıkış kapısı:** 1 yeni ders 1 konuda critic-geçer kalitede canlı + SEO sayfası indeksli.

---

### FAZ 5 — Monetization (ERTELENDİ; mimari şimdiden hazır)
> Açılış koşulu: tekrarlayan anlamlı kullanım + kapasite + legal tamam.

- Sıra: **white-label B2B / zümre paketi** (2.4 üstüne) → pay-as-you-go kredi →
  (çok sonra) AI API kiralama.
- **Şimdiden hazır hooks:** `tenant_id`, white-label PDF, üretim metering, legal sayfalar.
- Önkoşul: Gemini billing/kota planı (§7).

**Çıkış kapısı:** ilk ödeme alındı + birim ekonomi (LLM maliyeti < gelir) doğrulandı.

---

## 6. Mobil uygulama stratejisi

**Karar: native ŞİMDİ DEĞİL — aşamalı git; native ~Faz 5 civarı, metrik kapısı arkasında.**

**Neden:** Acquisition kanalı **web/SEO** (TR K-8 için veli/öğretmen/öğrenci Google'da
arar) → native'in faydası acquisition değil **retention**. PWA zaten kurulu → mobil
"uygulama" değerinin çoğu ~$0 elimizde.

**Aşamalı yol (ucuzdan pahalıya, her adım metrik kapılı):**
1. **Şimdi:** PWA'yı sıkılaştır (offline kabuk, "ana ekrana ekle" teşviki, ikon/splash) — ~$0.
2. **Sonra:** **PWA Web Push** — `/practice` seri/streak bildirimi ("serini koru"). Native'in
   en büyük retention avantajı; native'siz alınır (iOS 16.4+ destekler). Service worker +
   Web Push API; subscription Turso'da. — ~$0.
3. **KAPI — native'e ancak şu üçü birden olunca geç:** (a) `/practice`'da anlamlı dönen-kullanıcı/
   streak kohortu var, (b) PWA push retention'a **yetmedi** (ölçüldü), (c) çift kod tabanı
   + store maliyetini taşıyacak kapasite var (≈ Faz 5).
4. **Geçilirse — teknoloji:** önce **Capacitor** (mevcut Next.js/PWA'yı sarıp App
   Store + Play'e koy, tek kod tabanı — önerilen ilk native adım); yetmezse **Expo/React
   Native**. Flutter önerilmez (React/TS yığını dışı).

---

## 7. Kapasite & maliyet track'i (faz-bağımsız, büyümeden ÖNDE gitmeli)

| İş | Durum |
|---|---|
| **Gemini billing/kota planı** (free-tier tavanı) | 🔴 AÇIK — Faz 4/5 önkoşulu |
| Cache warming gerçek-popüler veriyle (GA4'ten) | script hazır (`#7`), veri bekliyor |
| Cost-meter doğruluğu | düzeltildi (`#5`), izlenebilir |
| Render free-tier → paid eşiği | trafik artınca; cold-start kalıcı çözümü |
| ChromaDB image boyutu (her ingest commit'le büyür; 8.sınıf ekledi) | izle; gerekirse harici vector store |

**Kapı:** Bunlar çözülmeden Faz 4/5'e (breadth/monetization) geçme → yoksa kota duvarı / sürpriz maliyet.

---

## 8. Açık operasyonel borçlar (faz-bağımsız)
- 🔒 PAT revoke (güvenlik — Faz 0.4)
- 📄 Legal placeholder'lar (KVKK/gizlilik — Faz 0.4, para önkoşulu)
- 🔴 Gemini billing planı (Faz 5 önkoşulu — §7)
- Render paid eşiği (§7)

---

## 9. Bugünden somut sıra (öncelikli açık işler)
1. **Faz 0.2** — north-star dashboard (kör uçuşu bitir; her şeyin önkoşulu).
2. **Faz 0.4** — PAT revoke + legal (güvenlik + para önkoşulu, düşük efor).
3. **Faz 2 ölçüm** — dönüşüm + viral döngü GA4'te gerçekten ölçülüyor mu?
4. **Faz 3 paylaşım** — PR A (#48) + PR B (#49) ✅ MERGED & canlı (link paylaş + public `/q/[code]` + GA4 funnel). **Sıradaki = PR C frontend** (`/practice/shares` sahip sonuç panosu; backend hazır). Detay `SHARING_PLAN.md`.
5. **Faz 1B** — içerik→SEO sayfa otomasyonu + 8.sınıf indeks takibi.
6. **Mobil** — PWA Web Push (retention, ~$0; §6 adım 2).

---

## 10. Detay doküman haritası (bu planın ekleri)
| Doküman | Kapsam | Bu planda |
|---|---|---|
| `SHARING_PLAN.md` | Quiz paylaşımı — dosya/satır seviyesi | Faz 3 |
| `GRADE8_LGS_PLAN.md` | 8.sınıf+LGS içerik hattı | Faz 1A (✅) |
| `LGS_SEO_PLAN.md` | Programatik SEO deseni | Faz 1B |
| `FUNNEL_FIXES_PLAN.md`, `ANON_GENERATION_PLAN.md` | Dönüşüm/anonim üretim | Faz 2 (✅) |
| `LEARNING_PLATFORM_PLAN.md` | `/practice` öğrenme döngüsü vizyonu | Faz 3 |
| `GROWTH_ROADMAP.md` | Bu planın atası (büyüme fazları) | §2/§5 |
| `RAG_ROADMAP.md`, `RAG_PDF_*` | İçerik kalite/RAG altyapısı | Faz 1/4 besler |

> Bu dokümanlar **detay/arşiv**dir. Strateji ve sıra **bu dosyadadır.** Yeni bir
> karar alındığında **önce burayı güncelle.**
