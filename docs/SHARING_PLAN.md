# /practice Quiz Paylaşımı — Somut Uygulama Planı

> Durum: **uygulama planı** (2026-06-17). `PROJECT_PLAN.md` Faz 3'ün açık kalemi:
> retention'ı acquisition'a bağlayan **viral kaldıraç**. Kaynak vizyon:
> `LEARNING_PLATFORM_PLAN.md` §7/§12 (paylaşım) + §15 ("önce link/kod, sonra
> uygulama-içi"). Bu doküman koddan doğrulanmış mevcut quiz altyapısına oturur.

---

## 1. Amaç ve büyüme mantığı

Bugün `/practice` kapalı bir kişisel döngü: kullanıcı kendi quiz'ini üretir → çözer →
gelişir. **Paylaşım, döngüyü dışarı açar:** öğretmen→öğrenci, öğrenci→arkadaş,
veli→çocuk. Her paylaşılan quiz, login duvarı olmadan çözülebilen bir **viral giriş
noktası** olur → çözen kişi değer görür → "kendi ilerlemeni takip et" ile üye olur.

**Ölçülen döngü:** `paylaş → link açıldı → çözüldü → üye oldu` (GA4, §9).

---

## 2. Mevcut altyapı — neyi yeniden kullanıyoruz (koddan doğrulandı)

| Mevcut | Paylaşıma katkısı |
|---|---|
| `quizzes` tablosu, sorular **cevaplı** saklanıyor (`quiz_store.py:48`) | Paylaşılan quiz aynı kayıttan cevapsız sunulur — yeni depolama yok |
| `_to_public()` cevap soyma (`quizzes.py:153`) | Paylaşılan çözücüye **aynı anti-kopya** ile sunulur |
| `grade_quiz()` saf/LLM'siz puanlama (`grading.py`) | Paylaşılan denemede **birebir** yeniden kullanılır |
| `attempts` tablosu `solver_tenant_id` + `quiz_id` ile (`quiz_store.py:70`) | Paylaşılan deneme çözenin kendi tenant'ına yazılır → **çözenin ilerlemesine otomatik akar** |
| `update_mastery()` (`quiz_store.py:354`) | Giriş yapmış çözen, paylaşılan quiz'den de ustalık kazanır — ek iş yok |
| Migration deseni (`ALTER TABLE attempts ADD COLUMN`, `quiz_store.py:93`) | `share_id` / `solver_label` sütunları aynı idempotent desenle eklenir |
| `/practice(.*)` login-gated; `/q/*` public olur (`middleware.ts:10`) | Çözme public, sahip panosu login arkasında |
| `track()` GA4 (`analytics.ts:19`) | Viral döngü event'leri |

**Tek gerçek mimari engel:** `QUIZ_STORE.get(quiz_id, owner_tenant_id)` (`quiz_store.py:155`)
ve `get_quiz`/`submit_attempt` **owner-scoped** → sahibi olmayan biri quiz'i ne
getirebilir ne çözebilir. Paylaşım = bu erişimi **yalnız geçerli bir share üzerinden**
güvenli şekilde açmak.

---

## 3. Bağlayıcı ürün kararları (uygulamadan önce netleşen)

1. **Çözme PUBLIC (login YOK).** Paylaşılan quiz link'i giriş duvarı olmadan
   çözülür — viralliğin tüm amacı bu. (Anonim üretim funnel'ıyla tutarlı, PR #46.)
   Çözüm sonrası **"ilerlemeni kaydet → üye ol"** CTA'sı (funnel).
2. **MVP = link/kod paylaşımı.** Uygulama-içi kullanıcı→kullanıcı paylaşımı (kullanıcı
   bulma sorunu, `LEARNING_PLATFORM_PLAN` §13 açık sorusu) **PR D'ye ertelenir**.
3. **Misafir çözücü opsiyonel isim girer.** "Adın (opsiyonel)" → `solver_label`.
   Giriş yapmadan çözen birinin sonucu sahibin panosunda anlamlı görünsün (öğretmen
   hangi öğrenci olduğunu görür) — öğrenci hesabı zorunlu olmadan.
4. **Giriş yapmış çözenin denemesi kendi ilerlemesine sayılır.** Misafir çözenin
   denemesi yalnız sahibin panosuna düşer (mastery güncellenmez — tenant yok).
5. **Sahip, paylaştığı quiz'in tüm sonuçlarını görür** (kim, kaç doğru, ne sürede).

---

## 4. Veri modeli değişiklikleri (`app/services/quiz_store.py`)

### 4.1 Yeni tablo: `shares` (`_init_db` içine, ~satır 108 civarı)
```sql
CREATE TABLE IF NOT EXISTS shares (
    id TEXT PRIMARY KEY,
    quiz_id TEXT NOT NULL,
    owner_tenant_id TEXT NOT NULL,
    share_code TEXT NOT NULL UNIQUE,   -- link kodu (kısa, tahmin edilemez)
    share_type TEXT NOT NULL DEFAULT 'link',  -- 'link' (MVP) | 'user' (PR D)
    target_tenant_id TEXT,             -- 'user' paylaşımı için (PR D), nullable
    revoked INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_shares_code ON shares(share_code);
CREATE INDEX IF NOT EXISTS idx_shares_owner ON shares(owner_tenant_id, created_at DESC);
```

### 4.2 `attempts` migration (idempotent, `quiz_store.py:89-96` desenini izle)
```python
if "share_id" not in cols:
    self._db.execute("ALTER TABLE attempts ADD COLUMN share_id TEXT")
if "solver_label" not in cols:
    self._db.execute("ALTER TABLE attempts ADD COLUMN solver_label TEXT")
```
- `share_id`: deneme bir paylaşımdan mı geldi (sahip panosu gruplaması).
- `solver_label`: misafir çözücünün opsiyonel adı.

> `solver_tenant_id` NOT NULL kısıtı var → misafir için sabit sentinel
> (`"anon"`) + gerçek ayrım `solver_label` ve client tarafı anon-id ile yapılır.
> Alternatif: kısıtı gevşetmek yerine sentinel basit ve mevcut FIFO/index'leri bozmaz.

### 4.3 Yeni `QuizStore` metotları
```python
create_share(quiz_id, owner_tenant_id) -> {"id", "share_code"}
    # quiz sahibe ait mi doğrula (get ile); değilse None. share_code = uuid4().hex[:10].
    # Aynı quiz'e tekrar çağrılırsa mevcut aktif share'i döndür (idempotent, çift link yok).

get_share_by_code(code) -> dict | None
    # revoked=0 olan share + bağlı quiz_id; yoksa None.

get_quiz_by_id(quiz_id) -> dict | None
    # get()'in owner-scope'suz versiyonu — YALNIZ share çözümünden sonra çağrılır.
    # (Mevcut get() korunur; bu ek metot owner filtresi olmadan okur.)

record_attempt(..., share_id=None, solver_label=None)
    # mevcut imzaya iki opsiyonel param; INSERT'e iki sütun eklenir.

list_shares(owner_tenant_id) -> [{share_id, share_code, quiz_id, title, grade,
    topic_id, created_at, attempt_count, avg_score_pct}]
    # shares ⋈ quizzes ⋈ attempts(COUNT/AVG) — sahip panosu listesi.

share_results(share_id, owner_tenant_id, limit=200) -> [{solver_label, score,
    total, duration_seconds, completed_at, per_kazanim}]
    # owner doğrulaması (share owner_tenant_id eşleşmeli) sonra attempts WHERE share_id.
```

---

## 5. API yüzeyi

### 5.1 Yeni public router: `app/routers/shared.py` → `app/main.py:74` sonrası kaydet
```python
app.include_router(shared.router, prefix="/api/shared", tags=["shared"])
```

| Method | Path | Auth | İş |
|---|---|---|---|
| `GET` | `/api/shared/{code}` | public (X-API-Key) | share çöz → **cevapsız** `QuizPublic` (reuse `_to_public`) |
| `POST` | `/api/shared/{code}/attempt` | public, **per-IP rate-limit** | cevap → `grade_quiz` → kaydet (`share_id`, `solver_tenant_id` veya `"anon"`, `solver_label`) → giriş yapmışsa `update_mastery` → `AttemptResult` |

### 5.2 Quiz router'a ekleme (`app/routers/quizzes.py`)
| Method | Path | Auth | İş |
|---|---|---|---|
| `POST` | `/api/quizzes/{id}/share` | owner (tenant_id body/query) | `create_share` → `{share_code, share_url}` |
| `POST` | `/api/quizzes/{id}/share/revoke` | owner | `revoked=1` (opsiyonel, PR C) |

### 5.3 Sahip panosu — `app/routers/me.py`'ye ekleme
| Method | Path | İş |
|---|---|---|
| `GET` | `/api/me/shares?tenant_id=` | `list_shares` → paylaştıklarım + özet sayaç |
| `GET` | `/api/me/shares/{share_id}/results?tenant_id=` | `share_results` → sonuç panosu |

### 5.4 Anti-kopya doğrulaması (değişmez)
- Çözücüye gönderilen `QuizPublic` cevapsız (`_to_public` zaten `options` gönderir,
  `correct_index`/`answer`/`solution_steps` göndermez).
- Puanlama sunucuda (`grade_quiz`), cevap istemciye yalnız **gönderimden sonra**
  (sonuç ekranında) döner — mevcut `/attempt` davranışıyla aynı.
- `share_code` tahmin edilemez (10 hex). Public `/attempt` **per-IP rate-limit**
  (`limiter`, `worksheets`/`quizzes` deseni) → brute-force ile cevap madenciliği yavaşlar.

### 5.5 Yeni şemalar (`app/models/schemas.py`)
```python
class CreateShareResponse(BaseModel):
    share_code: str
    share_url: str            # backend boş bırakır; frontend BASE+/q/{code} kurar (ya da env)

class SharedAttemptRequest(SubmitAttemptRequest):  # + opsiyonel alanlar
    solver_label: str | None = None
    # tenant_id opsiyonel olmalı (misafir) → SubmitAttemptRequest.tenant_id'i
    # shared akış için override eden ayrı şema; "anon" sentinel router'da atanır.

class ShareSummary(BaseModel):
    share_id: str; share_code: str; quiz_id: str; title: str
    grade: int; topic_id: str; created_at: str
    attempt_count: int; avg_score_pct: int | None

class SharesResponse(BaseModel):
    items: list[ShareSummary]

class ShareResultItem(BaseModel):
    solver_label: str | None; score: int; total: int
    duration_seconds: int | None; completed_at: str

class ShareResultsResponse(BaseModel):
    title: str; question_count: int
    items: list[ShareResultItem]
```

---

## 6. Frontend

### 6.1 API client (`frontend/lib/api.ts`) — yeni fonksiyonlar
```ts
createShare(quizId, tenantId) -> { share_code, share_url }
getSharedQuiz(code) -> QuizPublic                 // public, tenant_id YOK
submitSharedAttempt(code, { answers, duration_seconds, tenant_id?, solver_label? }) -> AttemptResult
listMyShares(tenantId) -> ShareSummary[]
getShareResults(shareId, tenantId) -> ShareResultsResponse
```
Tipler `frontend/lib/types.ts`'e eklenir (mevcut quiz tip blokunun yanına).

### 6.2 Public çözme rotası: `frontend/app/q/[code]/page.tsx`
- `/q/*` middleware `isProtectedRoute` dışında → **otomatik public** (`middleware.ts:10`).
- `QuizSolver`'ı **paylaşılan mod** ile yeniden kullan. En temiz yol: `QuizSolver`'a
  opsiyonel prop'lar ekle —
  ```ts
  <QuizSolver shareCode={code} />   // varsa: getSharedQuiz + submitSharedAttempt yolu
  ```
  `shareCode` verildiğinde:
  - Yükleme: `getSharedQuiz(code)` (userId beklemez; misafir de çözer).
  - `userId` varsa `tenant_id`'yi gönder (ilerlemeye sayılsın); yoksa
    **opsiyonel "Adın" input'u** göster → `solver_label`.
  - Gönderim: `submitSharedAttempt(code, …)`.
  - Sonuç ekranı (`ResultsView`) aynen çalışır; ek olarak misafire **"İlerlemeni
    kaydetmek için üye ol"** CTA'sı (`SignUpButton`, funnel).
- Bu rota **`/practice` layout'unun dışında** (login-gated değil) → `app/q/` kendi sade
  layout'unu kullanır (practice-theme istenirse className ile uygulanır, login zorunlu DEĞİL).

### 6.3 "Paylaş" aksiyonu (yeni bileşen `frontend/components/ShareQuizButton.tsx`)
- Nerede: `QuizSolver` `ResultsView` aksiyon satırı (`QuizSolver.tsx:413`) + quiz
  geçmişi (`QuizHistoryList.tsx`).
- Akış: tıkla → `createShare(quizId, userId)` → `share_url` → **kopyala** + **WhatsApp'a
  at** (mevcut PWA paylaşım deseni #39, `navigator.share`) + link önizleme.
- Idempotent: aynı quiz'e tekrar basınca aynı link.

### 6.4 Sahip sonuç panosu: `frontend/app/practice/shares/page.tsx` (login-gated)
- `/practice` altında → otomatik login zorunlu.
- `listMyShares(userId)` → kartlar (quiz başlığı, çözülme sayısı, ort. skor, link kopyala).
- Karta tıkla → `frontend/app/practice/shares/[shareId]/page.tsx` → `getShareResults`
  → tablo (çözen adı, skor, süre, tarih).
- `/practice` hub'ına (`app/practice/page.tsx`) 4. kart: **"Paylaşımlarım"**.
- `/practice` layout sekme çubuğu varsa oraya da ekle.

### 6.5 GA4 event'leri (`frontend/lib/analytics.ts` `track()`)
| Event | Nerede |
|---|---|
| `quiz_share_create` | ShareQuizButton, link oluştu |
| `quiz_share_open` | `/q/[code]` sayfa görüntüleme |
| `quiz_share_attempt` | paylaşılan çözüm gönderildi (misafir/üye ayrımı param) |
| `quiz_share_signup` | `/q/[code]` sonrası CTA'dan kayıt |

Funnel: `create → open → attempt → signup` = viral katsayı ölçümü.

---

## 7. Fazlama (her PR bağımsız, tek başına test edilebilir)

| PR | Kapsam | Çıktı |
|---|---|---|
| **A — Backend paylaşım + public çözme** ✅ DONE | `shares` tablosu + attempts migration; `quiz_store` metotları; `shared.py` router (`GET /{code}`, `POST /{code}/attempt`); `POST /api/quizzes/{id}/share`; şemalar; per-IP rate-limit; `tests/test_sharing.py`. **C'nin backend'i de bu PR'da geldi** (`GET /api/me/shares` + `/results` + `revoke_share`). | API ile link üret + misafir çöz + puanla |
| **B — Frontend paylaş + public çözme sayfası** ← SIRADAKİ | `ShareQuizButton`; `/q/[code]` (QuizSolver shared mod + misafir isim + üye-ol CTA); api.ts/types.ts; GA4 event'leri | **Viral döngü canlı** (paylaş→çöz→üye) |
| **C — Sahip sonuç panosu** (backend ✅) | Kalan = frontend: `/practice/shares` liste + detay; hub kartı | Sahip kim çözdü/kaç doğru görür |
| **D — (sonra) uygulama-içi paylaşım** | `share_type='user'` + `target_tenant_id`; kullanıcı bulma (kullanıcı adı/davet); gelen kutusu | Kullanıcı→kullanıcı paylaşım |

> Sıra: **A → B** viral döngüyü açar (en yüksek büyüme değeri). **C** sahip değerini
> ekler. **D** plan §13 açık sorusu (kullanıcı bulma) çözülünce.

---

## 8. Mevcutu bozmama sınırları (bağlayıcı)
- `/generate`, `GenerateForm`, `/api/worksheets/*`, PDF → **sıfır dokunuş**.
- Mevcut `QUIZ_STORE.get(quiz_id, owner_tenant_id)` **korunur**; `get_quiz_by_id`
  ek metottur (owner-only akış değişmez).
- `submit_attempt` (`quizzes.py:255`) mevcut owner-scoped davranışı korur; paylaşılan
  çözüm **ayrı** `shared.py` endpoint'inden geçer (karışmaz).
- `record_attempt`'a eklenen `share_id`/`solver_label` **opsiyonel** → mevcut çağrı
  (`quizzes.py:274`) değişmeden çalışır.
- `/q/*` rotası tümüyle silinse `/practice` ve `/generate` etkilenmez.

---

## 9. Riskler & açık noktalar
1. **Cevap madenciliği (link brute-force):** cevaplar sunucuda ama paylaşılan quiz'e
   tekrar tekrar deneme göndererek cevap çıkarılabilir (plan §13). Azaltım: per-IP
   rate-limit + üretim çeşitliliği. MVP'de kabul.
2. **Güven modeli:** backend `tenant_id`'yi paylaşılan X-API-Key arkasında **doğrulamadan
   güvenir** (mevcut durum; Clerk JWT doğrulaması yok). Sahip-only endpoint'ler
   (`/api/me/shares`) bu varsayımı sürdürür. Kötü niyetli istemci başka tenant'ın
   paylaşımını görebilir → kabul edilen mevcut risk; sertleştirme ileride (Clerk JWT).
3. **Misafir kimliği:** `solver_tenant_id="anon"` sentinel + `solver_label`. Aynı
   misafirin tekrar çözümleri ayrışmaz (panoda iki "anon" satırı) — kabul; gerçek
   ayrım için üyelik CTA'sı zaten var.
4. **Spam/abuse:** public `/attempt` ve `/share` create rate-limitli olmalı.

---

## 10. Test
- **Backend birim:** share create idempotent; `get_share_by_code` revoked filtreler;
  misafir attempt kaydı (`share_id` + `solver_label` + `anon`); üye attempt → mastery
  güncelleniyor; `share_results` owner doğrulaması (başka tenant 404/boş).
- **Anti-kopya regresyon:** `GET /api/shared/{code}` cevap alanlarını sızdırmıyor
  (`correct_index`/`answer`/`solution_steps` yok).
- **E2E (Vercel preview, `verify-preview-before-merge` memory):** link üret → gizli
  pencerede `/q/{code}` aç (login'siz) → çöz → skor + üye-ol CTA → sahip panosunda
  sonuç görünüyor.
- frontend-ci (lint+typecheck) — `frontend-build-ci` memory (lokalde build yok).
