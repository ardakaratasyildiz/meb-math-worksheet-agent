# Soru Bankası & Kalite Mimarisi Planı (Faz A–D)

_Oluşturma: 2026-07-19. Kaynak: iki dış mimari önerisinin (kalite→banka→batch; modüler monolit+kuyruk) mevcut kod tabanına karşı doğrulanmış, kırpılmış hâli._

> **Karar özeti.** Dış öneriler teknik olarak sağlam ama **maliyet/ölçek** optimize ediyor;
> bizim bağlayıcı kısıtımız (organik trafik ~0, indeksleme/dağıtım darboğazı) ve LLM maliyeti
> zaten küçük (~480 TL/ay, %86'sı thinking — `docs/GEMINI_COST_POLICY.md` ile çoktan ele alındı).
> Bu yüzden **yalnızca kaliteye → SEO'ya → elde tutmaya hizmet eden 4 fazı** alıyoruz.
> **Postgres YOK** — Turso (libSQL, `history.sqlite3`) yeterli ve zaten kalıcı.
> **ERTELENEN** (trafik/gelir gerçekleşince): Gemini Batch API, Redis kuyruk/worker, parametrik
> şablonlar (en fazla 1 pilot), prompt caching, idempotency, adaptif overshoot.

## 0. Mevcut durum (doğrulanmış temel)

| Alan | Bugünkü gerçek | Dosya |
|---|---|---|
| Soru saklama | Yalnız **set-düzeyi JSON blob**; tekil seçilebilir soru **yok** | `llm_cache.py`, `worksheet_history.py`, `quiz_store.py` |
| Set-cache | Tek soru history'yle çakışınca **tüm set eleniyor** (`continue`) | `llm_cache.py:143-148` |
| Kalite metriği | Red nedenleri yalnız geçici `GenerationTrace`'te, **kalıcı değil** | `schemas.py:391-419`, `agent.py` |
| Ledger | token/maliyet/`cache_hit` var; `generation_source`/red nedeni **yok** | `usage_ledger.py:37-53` |
| Doğrulayıcı | `math_verifier` yalnız `SALT_ISLEM`+`ISLEM` (SymPy), fail-open | `math_verifier.py:27,192` |
| Critic | Koşulsuz, **per-generate tek batched çağrı**, `gemini-2.5-flash-lite` | `critic.py:83-153` |
| DB | Turso/libSQL embedded replica (`TURSO_DATABASE_URL`); commit'te remote sync | `db_connection.py:57-87` |
| Chroma | **Salt-okuma RAG** (add/upsert yok) — kaynak-doğruluk değil | `retriever.py` |
| Arka plan işi | **Hiç yok** (queue/worker/scheduler/Batch API yok) | — |
| Eval altyapısı | **Var** ama flaky: scenarios/metrics/check_regression/thresholds | `scripts/eval/` |

## Faz sırası ve bağımlılıklar

```
A (ölçüm)  ──►  B (soru bankası)  ──►  C (yapısal doğrulayıcı)  ──►  D (regresyon kapısı)
   │               │  keystone            │ quality_score besler        │ prompt_version'a dayanır
   └── telemetri B'nin etkisini ölçer ────┘                             │
                   └── prompt_version / curriculum_version damgası ─────┘
```

Her faz **feature-flag arkasında karanlıkta ship** edilir (default kapalı), sonra backfill,
sonra flag açılır — go-live disiplini: önce backend flag + canlı doğrulama, sonra frontend
(2026-07-10 çok-ders go-live'ındaki skew-önleme ile aynı).

---

# Faz A — Kalite / red kaydını kalıcılaştır  (küçük · ~2-3 gün)

**Amaç.** `GenerationTrace`'in zaten ürettiği ama attığımız red/kaynak verisini kalıcı kıl.
Uçuşu körlemesine yapmayı bitir; B'nin etkisini (canlı üretim oranı ↓) ölçebil.

**Tasarım kararı.** Ayrı tablo değil — mevcut tek yazma noktası `USAGE_LEDGER.record()`'ı genişlet
(hot-path'te ikinci yazma yok). Per-generation **agregat** granülerlik yeterli; per-question
red nedeni doğal olarak Faz B'de soru satırının statüsünde yaşayacak.

### A.1 Şema — `usage_ledger` tablosuna ekleme (additive, geriye uyumlu)

`usage_ledger.py::_init_db()` içine idempotent "ADD COLUMN IF NOT EXISTS" yardımcısı ekle
(SQLite `ALTER TABLE ADD COLUMN`; var olan satırlar NULL alır):

```
subject                TEXT
kazanim_kod            TEXT
difficulty             TEXT
generation_source      TEXT     -- 'live' | 'cache' | 'bank' | 'mixed'
requested_count        INTEGER
delivered_count        INTEGER
retry_rounds           INTEGER
dedup_rejected_string  INTEGER
dedup_rejected_semantic INTEGER
math_verifier_rejected INTEGER
critic_rejected        INTEGER
cached_content_tokens  INTEGER  -- Gemini usage_metadata.cached_content_token_count:
                                -- implicit prompt-cache bize ŞU AN ne kadar yardım ediyor (ölç, sonra karar)
```

Yardımcı desen (Turso/SQLite ikisinde de çalışır):
```python
def _add_col(db, table, col, decl):
    cols = {r[1] for r in db.execute(f"PRAGMA table_info({table})").fetchall()}
    if col not in cols:
        db.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")
```

### A.2 `record()` imzasını genişlet

`usage_ledger.py:62` — yeni **opsiyonel** kwargs (mevcut çağrılar kırılmaz):
`subject`, `kazanim_kod`, `difficulty`, `generation_source`, `requested_count`,
`delivered_count`, `retry_rounds`, `dedup_rejected_string`, `dedup_rejected_semantic`,
`math_verifier_rejected`, `critic_rejected`. Best-effort (mevcut try/except yutma korunur).

### A.3 Çağrı noktalarını besle

- `worksheets.py::_build_worksheet` (~`:344-355`): çok-bucket'ta trace'ler zaten merge ediliyor
  → red sayaçlarını **bucket'lar arası topla**, `generation_source` = trace `cache_hit`'ten türet
  (`cache`→cache_hit True, aksi `live`; Faz B'de `bank`/`mixed` eklenir).
- `quizzes.py` (~`:79`): tekil generate → trace'ten doğrudan.
- **Cached token ölçümü:** `gemini_client`'te çağrı dönüşündeki
  `usage_metadata.cached_content_token_count`'ı `GenerationTrace`'e taşı → ledger'a yaz.
  Bugün implicit caching (2.5+ default açık) bize ne kadar yardım ediyor **hiç bilmiyoruz**;
  bu alan prompt-caching yatırımının ROI'sini veriyle açar (aşağıda "Prompt caching" bloğu).

### A.4 Admin görünürlüğü

- `admin.py`'a küçük bir uç: `GET /admin/quality/summary` — son N günde
  ders×kazanım×tip×zorluk kırılımında: teslim oranı (`delivered/requested`),
  red oranları (verifier/critic/dedup), canlı-üretim oranı, soru başı maliyet.
- Mevcut admin maliyet kartının (PR #126) yanına "kalite" kartı; frontend opsiyonel (önce API).

### A.5 Test & çıktı

- `tests/test_usage_ledger_quality.py`: yeni kolonların yazıldığı + eski `record()` çağrısının
  hâlâ çalıştığı (geriye uyum). CI testleri doğrudan koşuyor → `python tests/test_*.py`.
- **Çıktı:** 1-2 hafta canlı baseline → B'nin "canlı üretim oranı" hedefine referans.

---

# Faz B — Soru bankası primitifi  (orta · ~1-2 hafta · KEYSTONE)

**Amaç.** Tekil, seçilebilir, metadata'lı soru envanteri. İki anlık kazanım:
(1) set-atma israfını bitir (soru-bazlı seçim, çakışan **tek soruyu** ele, gerisini kullan);
(2) sonraki her şeyin + **statik SEO içeriğinin** zemini.

### B.1 Şema — yeni tablo `question_bank` (aynı `history.sqlite3` / Turso)

Yeni modül `app/services/question_bank.py`, singleton `QUESTION_BANK` (llm_cache.py deseni birebir):

```sql
CREATE TABLE IF NOT EXISTS question_bank (
    id                   TEXT PRIMARY KEY,        -- uuid4 hex
    subject              TEXT NOT NULL,           -- SubjectId (istekte var → resolve gerekmez)
    grade                INTEGER NOT NULL,
    selection_key        TEXT NOT NULL,           -- agent.selection_key ile AYNI:
                                                  --   math: unit_id|topic_id ; diğer: "{subject}:{unit_id}"
    kazanim_kod          TEXT,                    -- NULL = auto-dağılım
    difficulty           TEXT NOT NULL,           -- Difficulty
    question_type        TEXT NOT NULL,           -- QuestionType
    yeni_nesil           INTEGER DEFAULT 0,       -- premium havuz ayrımı (cache_key ile aynı mantık)
    question_json        TEXT NOT NULL,           -- Question.model_dump(mode="json") — TAM soru
    normalized_question  TEXT NOT NULL,           -- diversity.normalize_question(question) — çakışma/dedup
    embedding            BLOB,                    -- opsiyonel 768-dim (GeminiEmbedder) — semantik seçim/dedup
    source               TEXT NOT NULL,           -- 'live' | 'batch' | 'editorial'
    model                TEXT,
    prompt_version       TEXT,                    -- içerik sürümleme (Faz D damgası)
    curriculum_version   TEXT,
    math_verifier_status TEXT,                    -- 'pass' | 'fail' | 'na'
    critic_status        TEXT,                    -- 'pass' | 'fail' | 'na'
    critic_confidence    REAL,
    quality_score        REAL,                    -- kompozit (Faz C/D iyileştirir); backfill'de NULL
    usage_count          INTEGER DEFAULT 0,
    last_served_at       REAL,
    created_at           REAL NOT NULL,
    archived_at          REAL                     -- yumuşak silme (sürüm bump / kalite düşüşü)
);
CREATE INDEX IF NOT EXISTS idx_qb_select ON question_bank(
    subject, grade, selection_key, kazanim_kod, difficulty, question_type, yeni_nesil, archived_at
);
CREATE INDEX IF NOT EXISTS idx_qb_norm ON question_bank(normalized_question);
```

**Neden `selection_key`:** `agent.py`'daki mevcut namespacing'i (`:532,539,547`) birebir yansıtır
→ ders/ünite karışması olmaz, matematik verisi ayrı kalır.

### B.2 `QUESTION_BANK` API

```python
def select(*, subject, grade, selection_key, kazanim_kod, difficulty,
           allowed_types, yeni_nesil, count,
           exclude_normalized: set[str],            # tenant history-seen (string)
           seen_embeddings=None,                    # tenant semantik dışlama
           min_quality: float = 0.0) -> tuple[list[Question], int]:
    """Bankadan uygun, az kullanılmış, çeşitli soruları seç.
    Dönüş: (seçilen sorular, açık = count - len(seçilen)).
    Sıralama: usage_count ASC, quality_score DESC (az servis edilmiş + kaliteli önce).
    Filtre: archived_at IS NULL, quality yeterli, normalized_question ∉ exclude_normalized,
            tip ∈ allowed_types (veya hepsi), yeni_nesil eşleşir.
    Ek: seçilenler arası + tenant seen_embeddings'e karşı semantik dedup (0.88 eşik)."""

def add(questions: list[Question], *, subject, grade, selection_key, difficulty,
        yeni_nesil, source, model, prompt_version, curriculum_version,
        statuses: dict) -> int:
    """Teslim edilen canlı soruları bankaya yaz. Aynı (selection_key, normalized_question)
    varsa atla (idempotent). Dönüş: eklenen satır sayısı."""
```

**Kritik fark (set-cache bug fix):** `select` **soru-bazlı** dışlar — çakışan tek soru düşer,
kalan kaliteli sorular kullanılmaya devam eder. `llm_cache.py:143-148`'in "tüm seti at" davranışı biter.

### B.3 `agent.generate()` entegrasyonu (yeni akış)

`enable_question_bank` flag açıkken, mevcut cache-lookup adımının (`agent.py:585-629`) yerine:

```
1. selection_key + distribution çöz (bugünkü gibi).
2. history-seen (string) + seen_embeddings topla (bugünkü gibi, :683-713).
3. selected, deficit = QUESTION_BANK.select(..., exclude_normalized=history_seen, count=question_count)
4a. deficit == 0:
       worksheet'i bankadan kur (renumber), history'e yaz, usage_count++ / last_served_at güncelle,
       ledger generation_source='bank'. LLM ATLANIR.
4b. deficit > 0:
       yalnız `deficit` kadar CANLI üret (overshoot ratio deficit'e uygulanır) →
       _process_batch → semantic dedup → math_verifier → critic (bugünkü boru hattı) →
       geçenleri QUESTION_BANK.add(...) ile yaz →
       final = selected + yeni; history'e yaz; ledger source = 'mixed' (selected>0) / 'live'.
```

**Write-back:** verifier+critic'ten geçen her canlı soru bankaya yazılır (statüleriyle). Banka
kullanıldıkça büyür → canlı üretim oranı popüler kombinasyonlarda düşer (Plan 1 hedefi: <%50).

### B.4 Set-cache'in akıbeti

- **Rollout:** banka canlı üretimin ÖNÜNE girer; `enable_generation_cache` ayrı flag olarak
  kalır ama banka açıkken **okuma yolu bankaya devredilir** (set-cache okuması atlanır).
- **Nihai durum:** banka set-cache'i tümüyle ikame eder → `enable_generation_cache=False`.
  `generation_cache` tablosu ve `llm_cache.py` bir sonraki temizlikte kaldırılır (önce backfill kaynağı).
- İkisi bir arada koşarken çift-yazma yok: cache put'u devre dışı, sadece banka yazar.

### B.5 Backfill — `scripts/backfill_question_bank.py`

Mevcut set-blob'larından bankayı doldur (tek seferlik):
- Kaynak: `generation_cache.questions_json` + `worksheet_history.item_json` (+ opsiyonel `quizzes.questions_json`).
- Her soru için: `normalize_question`, `(selection_key, normalized_question)` dedup, `source='live'`
  (legacy), `quality_score=NULL` (bilinmiyor → seçimde min_quality=0 ile yine kullanılabilir),
  `math_verifier_status='na'`.
- Embedding: opsiyonel, toplu — GeminiEmbedder ile parti parti (maliyet küçük; ertelenebilir,
  seçim embedding'siz de çalışır).
- **Turso notu:** commit'te remote'a sync eden `_SyncOnCommit` var → backfill'i lokal replica'da
  toplu yaz, sonra tek sync; ya da parti başına commit throttle. `scripts/backfill_subject.py` ve
  [[subject-aware-rag]] doğrudan-sqlite deseni referans (Chroma HNSW-fail dersi burada geçerli değil,
  saf sqlite).

### B.6 Test & rollout

- `tests/test_question_bank.py`: select soru-bazlı dışlama (çakışan tek soru düşer, gerisi gelir);
  add idempotent; deficit hesabı; yeni_nesil havuz ayrımı (`test_cache_yeni_nesil.py` deseni).
- `enable_question_bank` default **False** → ship → backfill → canlı API'de tek kazanımla doğrula
  (`select` gerçek soru dönüyor mu) → flag aç → ledger'da `generation_source='bank'` oranını izle.
- **Rollback:** flag=False → eski cache yolu; banka tablosu zararsız kalır.

### B.7 SEO köprüsü (bankayı ŞİMDİ yapmanın asıl gerekçesi)

Banka dolunca `scripts/export_seo_data.py` benzeri bir uç, kalite-onaylı (quality_score yüksek,
critic pass) soruları **statik SEO sayfalarına** besleyebilir → doğrudan indeksleme/dağıtım
darboğazına saldırır. Bu, "kalite mimarisi" ile gerçek darboğaz arasındaki köprü.

---

# Faz C — Deterministik doğrulayıcıyı genişlet  (küçük/orta · ~3-5 gün)

**Amaç.** Kalite (maliyet değil — critic zaten flash-lite/maliyetin %2'si). `math_verifier`
bugün yalnız 2 tipi kontrol ediyor; ucuz yapısal kontrolleri tüm tiplere yay, red nedenini
**kaydet** (sessiz düşürme yerine → Faz A/B telemetrisine bağlanır).

### C.1 Yeni modül `app/services/structural_verifier.py`

`verify_structural(q: Question) -> VerifyResult(is_verifiable, is_valid, reason)`, hepsi **fail-open**:

| Tip | Deterministik kontrol |
|---|---|
| `COKTAN_SECMELI` | `options` var, tam 4 (A–D), `correct_index` aralıkta, tekrarlı şık yok, `answer` = `options[correct_index]` |
| `DOGRU_YANLIS` | `correct_bool` None değil; `answer` ∈ {Doğru, Yanlış} tutarlı |
| `BOSLUK_DOLDURMA` | `blanks` boş değil; adet = sorudaki `___` sayısı |
| `ESLESTIRME` | GFM tablo iki kolon; cevap çiftleri kolon öğeleriyle örtüşür |
| `TABLO_SORUSU` / `GRAFIK_OKUMA` | tablo/eksen varsa ve soru toplam/max/min/fark istiyorsa → **deterministik yeniden hesap**, cevapla karşılaştır (best-effort) |
| `GORSEL_GEOMETRI` | `<svg` var (bugün `_process_batch`'te), ölçü-etiketi sağlık kontrolü |

Not: `_process_batch` (`agent.py:1132-1207`) bugün bazı yapısal filtreleri (svg-zorunlu, MC A–D,
E-şıkkı reddi) **sessizce** yapıyor. Faz C bunları tipli doğrulayıcıya taşır ve **reason** üretir.

### C.2 Entegrasyon

- `agent.generate()`'te `math_verifier` (SymPy, math-only) yanında `structural_verifier` (tüm tipler)
  koştur; ikisi `math_verifier_rejected` sayacına ayrık `reason`'larla katkı verir.
- Statü → Faz B `add()`'e `math_verifier_status`/`reason` olarak akar → `quality_score`'a girdi.
- `quality_score` v1 (basit kompozit): `verifier_pass(1/0)*0.4 + critic_pass*0.4 + (1-critic_conf_if_fail)*... `
  — Faz D metrikleriyle rafine edilir; başlangıçta pass/fail + critic_confidence yeterli.

### C.3 Test

- `tests/test_structural_verifier.py`: her tip için geçerli/geçersiz örnek; fail-open (parse
  edilemeyen → is_verifiable=False, valid sayılır). `tests/test_reference_integrity.py` deseni.

---

# Faz D — Eval / kalite regresyon kapısı  (küçük · ~2-4 gün)

**Amaç.** `scripts/eval/` **zaten var** ama flaky ([[quick-eval-flaky-gate]]). Sürüm-damgalı,
düşük-varyanslı, prompt/model/şablon değişiminde bloklayan bir kapıya çevir.

### D.1 İçerik sürümleme damgası (önkoşul, B ile birlikte)

- `app/prompts/` (veya config) içinde `PROMPT_VERSION` sabiti; prompt düzenlemesinde bump.
- `CURRICULUM_VERSION`. Her ikisi `GenerationTrace`'e + `question_bank` satırına yazılır (Faz B).
- Eval bu sürümlere göre anahtarlanır → "hangi sürüm neyi regresyona soktu" izlenir.

### D.2 Sabit golden set + düşük varyans

- `scripts/eval/scenarios.py`'yi genişlet: ders×sınıf×kazanım×tip×zorluk sabit senaryo kümesi,
  senaryo başına **daha büyük n** (küçük örnek eşik zıplamasını [[quick-eval-flaky-gate]] kırar).
- Seed kontrolü; mutlak eşik yerine **yuvarlanan baseline'a göre** karşılaştır (`check_regression.py`).

### D.3 Metrikler & kapı

`scripts/eval/metrics.py` (mevcut) üzerine: teslim oranı, `math_verifier`/`critic` red oranı,
kazanım uyumu, soru başı maliyet, çeşitlilik. Eşikler `scripts/eval/thresholds.json`.

- **Kapı:** `PROMPT_VERSION`/model/şablon değişince eval koş; eşik dışına çıkarsa **PR blokla**.
- Önce **non-required** (mevcut politika: lint/pytest yeşilse gerekçeyle merge), stabil olunca
  required'a terfi et.

### D.4 Test & CI

- `python tests/test_*.py` doğrudan koşuyor ([[ci-eval-runs-tests-directly]]) → eval yardımcılarına
  birim testleri; regresyon-kapısı kararının deterministik olduğunu doğrula.

---

## Özet: efor, sıra, flag

| Faz | Efor | Flag (default False) | Bağımlılık | Ana çıktı |
|---|---|---|---|---|
| **A** ölçüm | ~2-3 gün | — (ledger her zaman yazar) | yok | red/kaynak telemetrisi |
| **B** banka | ~1-2 hafta | `enable_question_bank` | A (ölçüm faydalı) | tekil soru envanteri + set-atma fix |
| **C** doğrulayıcı | ~3-5 gün | `enable_structural_verifier` | B (quality_score) | tipli deterministik kalite |
| **D** kapı | ~2-4 gün | eval required-terfi | B (sürüm damgası), C (metrik) | regresyon koruması |

## Kırmızı çizgiler (mimari disiplin)

- **Postgres yok** — Turso/`history.sqlite3` tek ilişkisel kaynak. Yeni tablolar aynı dosyada.
- **Chroma salt-retrieval kalır** — soru bankası ilişkisel DB'de; Chroma yeniden üretilebilir indeks.
- **Redis/worker/Batch API yok (şimdilik)** — tek free-tier instance; async iş gerekene dek
  (Batch pre-gen), en basit araçla (script / Render cron / in-process) başlanır, Redis değil.
- **Migrasyonsuz-güvenli:** `CREATE TABLE IF NOT EXISTS` + idempotent `ADD COLUMN`; mevcut tablolara
  yıkıcı dokunma yok; matematik verisi + `worksheet_history`/quiz akışı korunur.
- **Karanlıkta ship + go-live skew önleme:** flag'ler kapalı ship → backfill → canlı doğrula →
  flag aç → metrikle izle → gerekirse flag=False rollback.

## Prompt caching — neden tam faz değil, ne yapıyoruz (ölçüm-güdümlü)

**Tavan düşük, çünkü:**
1. **Maliyet sürücümüz output/thinking; caching yalnız input'u indirir.** `GEMINI_COST_POLICY.md §2`:
   çıktının ~%100'ü thinking, "thinking maliyetin baş sürücüsü". Prompt caching thinking token'a
   dokunmaz, sadece ortak-önek input'unu ~%75 indirir → faturanın azınlığının bir dilimi (aylık ~tek haneli TL).
2. **İmplicit caching 2.5+'ta zaten açık** → bedava kısım otomatik yakalanıyor. Explicit cache =
   saatlik saklama bedeli; yalnız **uzun stabil önek + yüksek tekrar** varsa kâr eder.
3. **Bizde önek stabil değil:** math few-shot RAG ile isteğe göre seçiliyor; history-dışlama +
   context token'ları dinamik ve prompt'un erkenine giriyor → ortak-önek kısa. Trafik ~0 → sıcak segment yok.
4. **Faz B baskın:** banka isabeti **tüm çağrıyı** atlar (input+output+thinking = %100), caching
   input'un dilimini kısmi indirir. Aynı israfı banka çok daha iyi kapatır.

**Yine de plana giren iki ucuz parça (ölç → sonra yatır):**
- **[Faz A içinde] Ölç:** `cached_content_token_count`'ı kaydet (yukarıda). İmplicit caching'in
  bugünkü gerçek katkısını gör.
- **[Faz D SONRASI, gated] Önek/sonek ayrımı:** prompt'u stabil-önek (sistem + müfredat kuralları +
  editoryal örnekler) / dinamik-sonek (adet, zorluk, history, dışlama) diye böl → implicit caching
  otomatik daha iyi tutar, explicit API gerekmez. **Prompt sırası üretim davranışını etkiler →
  Faz D regresyon kapısından GEÇMELİ** (bu yüzden D'den sonra).
- **Explicit cache:** ölçüme bağlı — cached-token verisi "sıcak, uzun-önekli kazanım" gösterirse
  değerlendir; yoksa ertele.

## Ertelenenler (bilinçli — trafik/gelir tetikler)

Gemini Batch API (%50 × $1.7/gün = ihmal edilebilir + async altyapı), Redis kuyruk/worker,
parametrik soru şablonları (en fazla 1 pilot tip — dört işlem — B+C kanıtlandıktan sonra),
**explicit** prompt caching (yukarıdaki bloğa göre ölçüme bağlı), idempotency/`request_id`,
adaptif overshoot (sabit 1.3 şimdilik iyi). Faz A telemetrisi bunların ROI'sini ne zaman pozitife
döneceğini gösterecek.
