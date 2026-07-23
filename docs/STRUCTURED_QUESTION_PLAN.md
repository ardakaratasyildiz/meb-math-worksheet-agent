# Yapısal Soru Üretimi Planı (D1 MC şıkları + D2 figür→SVG)

> Durum: **tasarım netleşti, inşa bekliyor.** 2026-07-23.
> Kaynak: thinking/critic A/B bulgusu (scripts/eval/thinking_ab.py) — üretim
> maliyetini/churn'ü sürükleyen **format-drop döngüsü**: şıksız MC (112) + şekilsiz/
> bozuk SVG (97) vs 0 matematik hatası. A+C (critic 0.75 + overshoot 1.8) canlıya
> alındı (PR #132); **asıl kalıcı fix bu belge (D).**
> Karar (2026-07-23): MC doğru cevap = **answer=harf + correct_index türet**;
> kapsam = **D1 + D2 birlikte tasarlandı, D1 önce inşa.**

---

## 0. Temel gerçek (haritadan) — altyapının ÇOĞU zaten var

- `Question` modeli (`app/models/schemas.py:344-359`) **zaten** `options: list[str]`,
  `correct_index`, `blanks`, `correct_bool` taşıyor.
- **Çözme yolu bunları zaten tüketiyor:** `QuizQuestionPublic.options`, web
  `QuizSolver.tsx:283`, mobil `solve.tsx:115`, `attempt-detail-view.tsx:19`. Tipler
  hazır (`apps/web/lib/types.ts:101`, `packages/shared/src/worksheet.ts:62`).
- **Boşluk:** (a) LLM şıkları yapısal alana yazmıyor — metne gömüyor; worksheet yolu
  `Question.options`'ı DOLDURMUYOR. (b) worksheet render'ı (PDF/web/mobil) şıkları
  metinden parse ediyor. (c) geometri figürü için deterministik renderer yok.
- **Backend'de direktif→SVG zaten var** (`app/services/svg_utils.py`): `{{chart:pie|bar}}`,
  `{{pattern:...}}` (daire/kare/üçgen + büyüyen), `{{table:...}}`. Pipeline:
  `agent.py:1155` `process_pattern_directives(process_chart_directives(...))` → sonra
  `<svg>` kontrolü (`agent.py:1161`). **D2 bu şablonu geometriye genişletir.**

---

## D1 — Çoktan seçmeli yapısal şıklar

### Üret
- **Şema:** `GeneratedQuestion` (`agent.py:137`) → `options: list[str] | None` ekle.
  `answer` = doğru şıkkın HARFİ (A-D) kalır (mevcut). `correct_index` **türetilir**
  (harf→index), şemaya eklenmez.
- **Prompt (5 ders + `templates.py:75`):** "A) B) C) D)'yi `question`'a göm" →
  "`question` = yalnız soru kökü; `options` = 4 düz metin şık (harf öneki YOK);
  `answer` = doğru şık harfi." Değişecek dosyalar: `app/prompts/templates.py:75`,
  `app/subjects/{fen,sosyal,turkce,ingilizce}/prompt.py` (MC talimatı + "ayrı alan yok"
  cümleleri).
- **Few-shot:** MC örnekleri (`app/subjects/*/few_shot.py` + math few-shot) yeni yapısal
  formata taşınır — model formatı örnekten öğrenir (kaçınılmaz iş).

### Doğrula (`agent.py:1176-1191` yeniden yaz)
- Gömülü-metin "A).." kontrolü KALDIRILIR. Yerine: MC ise `len(options)==4` (2-5 tolere
  edilebilir) + `answer` harfi options aralığında → değilse ele. **5-şık (E) sorunu
  otomatik biter** (dizi sabit boy). `_process_batch` `Question(options=..., correct_index=
  <harften türet>)` set eder (türetme: mevcut `structured._answer_letter` mantığı).

### Tüket (worksheet render'ı `.options`'a geçir; fallback KORUNUR)
| Yer | Değişiklik |
|---|---|
| PDF `_question_block` (`pdf_renderer.py:523`) | `q.options` doluysa kök + "A) …B) …" formatını RENDERER üretir; None ise mevcut metin yolu (fallback) |
| Web `QuestionCard` (`QuestionCard.tsx:155-197`) | `q.options` doluysa ondan; None ise `splitInlineOptions` fallback |
| Mobil `create.tsx:197` | `q.options` doluysa şık listesi; None ise ham metin fallback |
| Çözme yolu (web/mobil) | **değişmez** (zaten `.options`) |

### Bridge (`app/services/structured.py`)
- `derive_structured_fields` (`:231`): LLM `options` sağladıysa ONA GÜVEN (yeni yol);
  yoksa mevcut `_parse_mcq` metin-parse (eski cache/few-shot). Comment "parser
  authoritative" → "LLM structured varsa öncelikli" olarak güncellenir.

### Geriye uyum (kritik — canlı kırılmasın)
- Eski cache'lenmiş kağıtlar + eski few-shot: `options=None` → renderer'lar metin
  fallback'iyle AYNEN render eder. Cache zamanla yapısala dolar. `generation_cache`
  anahtarı değişmez.

**D1 çözer:** tüm derslerde şıksız MC drop (112) → az yeniden-üretim + çok geçerli MC.
**D1 çözmez:** figür/SVG (97) → D2.

---

## D2 — Figür → deterministik SVG (direktif genişletme)

Model ham geometri SVG'sini güvenilir üretemiyor. Çözüm: model **kompakt spec/direktif**
üretir, backend SVG'yi **deterministik** çizer (chart/pattern/table şablonu).

### D2a — Mevcut direktiflere yönlendir (düşük efor, prompt+eleme)
- **GRAFIK_OKUMA → `{{chart:bar|…}}`/`{{chart:pie|…}}`** (renderer VAR, `svg_utils.py:102-191`).
- **ORUNTU_SEKIL → `{{pattern:…}}`** (renderer VAR, `svg_utils.py:295-348`).
- Prompt: bu tiplerde **ham `<svg>` yasak, direktif ZORUNLU.** Few-shot bu tipleri
  direktifle gösterir. Eleme: bu tiplerde direktif→SVG çıkmadıysa ele (mevcut `<svg>`
  kontrolü direktif işlendikten sonra zaten çalışıyor).
- Etki: 97 drop'un grafik/örüntü kısmını kaynağında keser; sıfır yeni renderer.

### D2b — Yeni `{{geo:…}}` geometri direktifi (orta efor, yeni renderer)
- **Yeni:** `app/services/svg_utils.py` içine `render_geo_svg(spec)` + `process_geo_directives`
  (chart/pattern ile birebir desen). `agent.py:1155` pipeline'ına eklenir.
- **Kapsam (grade-8 LGS ağırlıklı, minimal set):**
  - `{{geo:right_triangle|a=3|b=4|c=?}}` — dik üçgen, kenar/hipotenüs etiketli (Pisagor).
  - `{{geo:triangle|sides=…|angles=…}}` — genel üçgen, kenar/açı etiketli.
  - `{{geo:rectangle|w=|h=}}` / `{{geo:square|s=}}` — dörtgen, ölçü etiketli.
  - `{{geo:circle|r=}}` — çember, yarıçap etiketli.
  - (opsiyonel sonra: koordinat düzlemi, açı, dönüşüm.)
  - Üçgen çizim temeli VAR (`svg_utils.py:246` pattern renderer'da triangle).
- Prompt: GORSEL_GEOMETRI'de ham SVG yasak → `{{geo:…}}` zorunlu; kapsam-dışı figür
  gerekiyorsa o tipi üretme (metin tabanlı tipe düş).
- Etki: geometri figür drop'unu kaynağında keser → **geometri düğümü (₺7)** açılır.

### D2 kapsam kararı
- **D2a önce** (bedava kazanç, renderer var). **D2b sonra** (yeni renderer; grade-8
  geometri ROI'si yüksek). D2b'nin figür kümesi bilinçli DAR — model dar spec'i güvenilir
  üretir; egzotik figür istenirse metin tipine düşülür (drop yerine).

---

## İnşa sırası (öneri)

1. **Faz 1 — D1 backend** (şema+prompt+few-shot+validate+bridge) + **eval** (thinking_ab
   harness'iyle şıksız-drop düşüşü + kalite). Backend main→Render. Riski düşük (fallback).
2. **Faz 2 — D1 render tüketicileri** (PDF + web QuestionCard + mobil create). Web Vercel
   (fallback canlıyı korur), mobil dala girer. Faz 1 ile aynı anda da gidebilir (fallback
   sayesinde sıralama esnek), ama önce backend yapısal veri üretsin.
3. **Faz 3 — D2a** (grafik/örüntü direktif yönlendirme; prompt+few-shot+eleme) + eval.
4. **Faz 4 — D2b** (`{{geo}}` renderer + prompt) + eval; geometri drop/maliyet ölçülür.

Her fazdan sonra `scripts/eval/thinking_ab.py` (dynamic thinking KORUNUR — A/B'de
kanıtlandı) ile drop sayıları + ₺/kağıt + critic/teslim ölçülür.

## Deploy
- Backend: main→Render (mevcut akış; PR + lint + pytest + eval-gate non-required).
- Web: apps/web Vercel — **QuestionCard fallback şart** (eski data + kademeli rollout).
- Mobil: feat/mobile-foundation ile gider (28 Tem dev build sonrası cihaz doğrulaması).
- **Rollback:** her tüketici `.options` yoksa metin fallback'e döndüğü için, backend
  prompt'u geri alınırsa (options üretmeyi durdurursa) render'lar eski yola düşer —
  kademeli/güvenli.

## Test/kabul kriterleri
- Şıksız MC drop **~0'a** (D1). Grafik/örüntü drop ~0 (D2a). Geometri figür drop belirgin
  düşüş (D2b).
- Kalite regresyonu YOK: critic geçişi ≥ mevcut, teslim 10/10, ham soru gözle kıyas.
- ₺/kağıt: cebir/fen zaten A+C ile düştü; D geometri + kalan MC churn'ünü de düşürmeli.

## Açık noktalar
- Few-shot MC/figür örneklerinin migrasyon eforu (5 ders) — inşa sırasında ölçülür.
- D2b geometri figür kümesinin nihai listesi (grade-8 kazanımlarına bakılarak daraltılır).
- `answer` MC'de harf kalıyor; ileride "tam metin" istenirse `structured._answer_letter`
  fallback matcher (`:99-107`) zaten hazır.
