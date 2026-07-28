# Üretim Maliyeti — Ölçüm ve Düşürme Planı

_2026-07-26. Ölçüm yöntemi: `google.genai` SDK'sının `Models.generate_content` /
`embed_content` çağrıları patch'lenerek HER çağrının token'ı yakalandı (ledger'ın
saymadığı şema-drop / 429-retry / fallback çağrıları dahil). Yerel backend, gerçek
Gemini API, `enable_generation_cache=False`, 20 soru / tek zorluk (`single`)._

## 1. Ölçülen gerçek maliyet (20 soruluk kağıt)

| Senaryo | Model | $/kağıt | **TL/kağıt** | TL/soru | Süre | Çağrı |
|---|---|--:|--:|--:|--:|--:|
| sosyal g7 (sözel) | 2.5-flash (tb 512) | 0.0332 | **1.16** | 0.058 | 74 s | 5 |
| matematik g5 | 2.5-flash (tb 512) | 0.0858 | **3.00** | 0.150 | 166 s | 9 |
| türkçe g8 | 2.5-flash (tb −1) | 0.1039 | **3.64** | 0.182 | 207 s | 50 |
| matematik g8 | 2.5-flash (tb −1) | 0.1467 | **5.13** | 0.257 | **361 s** | 14 |
| matematik g7 geometri | **3.5-flash (tb −1)** | 0.2301 | **8.05** | 0.403 | 94 s | 7 |
| **ortalama** | | **0.1199** | **4.20** | 0.210 | | |

`mixed` mod ayrıca ölçüldü (sosyal g7, 10 soru): **1.51 TL** = 0.151 TL/soru →
aynı dersin `single` modundan **2.6× pahalı** (3 bucket = 3× sistem promptu +
3× overshoot yuvarlaması + 3× critic + 3× top-up).

Kur: 1 USD = 35 TL. Kullanıcının gözlemi (25 Tem: 4 kağıt ≈ 24 TL → 6 TL/kağıt)
bu tabloyla tutarlı — matematik ağırlıklı kullanımda 5-8 TL/kağıt normaldir.

## 2. Birim ekonomi — sorun burada

App Store/Play kesintisi %15 (küçük işletme programı) varsayımıyla:

| Plan | Brüt | Net | Kağıt | Gelir/kağıt | Maliyet/kağıt | **Brüt marj** | %80 marj için hedef |
|---|--:|--:|--:|--:|--:|--:|--:|
| Pro | ₺199 | ₺169 | 50 | 3.38 TL | 4.20 TL | **−%24** | 0.68 TL (**6.2×**) |
| Pro+ | ₺349 | ₺297 | 120 | 2.47 TL | 4.20 TL | **−%70** | 0.49 TL (**8.5×**) |

Yani **kotasını tam kullanan bir abone bugün zarar ettiriyor.** Kota dolduran
kullanıcı oranı düşük olsa bile marj, planın vaadiyle (açık kağıt sayısı, gizli
tavan yok — MONETIZATION_PLAN §2) çelişiyor. Hedef: **≤ 0.7 TL/kağıt**.

## 3. Kök nedenler (ölçümle)

### 3.1 KAPANDI — `mixed`/`progressive` modda HTTP 500 (saf israf)
`_build_worksheet` mixed'de `agent.last_model_used` okuyordu; `agent` yalnız
`single` modda bağlanıyor → `UnboundLocalError` → **500, ama 3 bucket'lık üretim
tamamlandıktan SONRA**. Canlıda doğrulandı: `difficulty_mode:"mixed"` → HTTP 500
/ 41 sn. Yani para tam ödenip kağıt teslim edilmiyor, kullanıcı tekrar deniyor
(→ 2×, 3× maliyet). Web (`GenerateForm.tsx:398`) ve mobil (`create.tsx:76`)
ikisi de bu modu gönderebiliyor. **Fix: model adı trace'ten okunur.**

### 3.2 KAPANDI — critic taşması (saf israf + KALİTE kaybı)
matematik g8 ölçümünde critic çağrısı: `gemini-2.5-flash-lite`, **65.524 çıktı
token'ı, 148 saniye**, ardından `Critic yanıtı parse edilemedi` → fail-open.
65.524 ≈ modelin 64K çıktı tavanı: 36 soruyu tek çağrıda denetlerken yanıt
yozlaşıp tavana dayanmış, JSON kesilmiş. Sonuç: o kağıtta **hiç filtreleme
yapılmadı** (kalite ↓) + kağıt maliyetinin %18'i ve süresinin %41'i boşa gitti.
**Fix:** `critic_batch_size=10` gruplama + `max_output_tokens = 512+128×n`
(sonlu tavan) + çözüm adımlarını 400 karakterde kesme + verdict index'lerini
global'e öteleme + token'ı gruplar arası biriktirme.

### 3.2b KAPANDI — ÜRETİCİ taşması / "format-drop" (en büyük tek israf kalemi)
Faz 1 ölçümünde yakalandı — critic'in aynısı, ama üretici modelde ve daha pahalı:
matematik g5 kağıdında `gemini-2.5-flash` **65.012 çıktı token'ı / 237 saniye**
yazdı (modelin 64K sert tavanı), JSON kesildi → `şemaya uymadı` → zincir
flash-lite'a düştü, o da **34.366 token** yaktı → aynı akıbet. Tek istekte
**~99K çıktı token'ı (~6.3 TL) HİÇBİR ŞEY için** harcandı; kullanıcı 18/20 soru
aldı. GEMINI_COST_POLICY'de "asıl sürücü format-drop/retry" notunun mekanizması
tam olarak budur ve ölçümle doğrulandı.

**Fix:** `agent.output_cap_for(question_count, thinking_budget)` → birincil
üretim, retry ve top-up çağrılarının hepsine `max_output_tokens`. Tavan =
soru×900 (ölçülen normal tüketim ~420-450/soru) + thinking payı. **Kritik
ayrıntı:** Gemini 2.5+ thinking token'larını da `max_output_tokens`'a sayar →
dinamik thinking (-1) için ayrı pay (20K) eklenir, aksi halde meşru geometri
üretimi (16.950 thinking + 7.188 içerik) kesilirdi.

### 3.3 AÇIK — thinking token'ları (matematik/geometri'nin baş kalemi)
Geometri kağıdında: **17.257 thinking + 7.127 içerik** token'ı. 3.5-flash çıktı
fiyatı $9/1M → thinking tek başına $0.155 / $0.229 = **o kağıdın maliyetinin
%67'si**. `thinking_budget=-1` (dinamik) güçlü modelde sınırsız bırakılıyor.

### 3.4 AÇIK — overshoot 1.8 israfı
`generation_overshoot_ratio=1.8` → 20 soru için **36 soru üretiliyor**; eleme
azsa (sosyal ölçümünde 36'dan yalnız 4 semantic-dedup elemesi) fazlalar
**kırpılıp ATILIYOR**. Ödenen ama çöpe giden: ~%40 çıktı token'ı. Fazla sorular
cache'e de yazılmıyor (`llm_cache.put` yalnız teslim edilen seti saklar).

### 3.5 ÖLÇÜLDÜ + KAPATILDI (kaldıraç küçük çıktı) — çözüm adımları
İlk tahmin **yanlıştı**: 524 eval sorusunun KARAKTER oranından "çözüm çıktının
%54'ü" çıkarılmıştı. Token bazlı ölçüm (Gemini `count_tokens`, matematik g5,
20 soru) gerçeği veriyor:

| Kalem | Değer |
|---|--:|
| ortalama çözüm uzunluğu | **84 token/soru** |
| teslim edilen JSON içeriğindeki payı | %38 (çözüm 1.673 tok / gövde 2.568 tok) |
| **tüm çıktı maliyetindeki payı** | **~%28** |
| kağıt başına TL karşılığı | ~0.26 TL (0.93 TL'lik kağıtta) |

Karakter oranı token oranından yüksekti çünkü o veri farklı ders/sınıf
karışımından (uzun LGS çözümleri dahil) geliyor ve LaTeX karakter başına daha az
token üretiyor. **Ders: maliyet payı karakterle değil token'la ölçülür.**

**A/B (include_solutions=True vs False, kısa-çözüm talimatı):**

| Kol | Maliyet | Çözüm uzunluğu |
|---|--:|--:|
| tam çözüm | 0.93 TL | 84 tok/soru |
| kısa çözüm | 1.06 TL | 59 tok/soru (−%29) |

Talimat işini yaptı (−%29 uzunluk) ama toplam maliyet DÜŞMEDİ. Nedensel değil,
gürültü: aynı ayarla ölçülen g5 koşuları 0.87 / 0.93 / 1.06 / 1.17 TL (±%15).
Teorik kazanç %29 × %28 ≈ **kağıt maliyetinin %8'i** → varyansın altında,
tek koşuyla ayırt edilemez.

**KARAR: geri alındı.** Kısaltma cache/havuz anahtarını ikiye bölüyordu
(`|kisacozum`) ve ödevler DAİMA `include_solutions=false` gönderiyor → üretimlerin
önemli kısmı ayrı havuza yazılacak, **yeniden kullanım kaybı ölçülemeyen %8'den
büyük**. Regresyon kilidi: `tests/test_spare_pool.py::test_no_concise_solution_key_split`.

Bu kalemin gerçek yolu Faz 3'tür: havuza yazılan sorunun çözümü **bir kez**
üretilir ve kalıcı saklanır → tekrar eden kullanımda çözüm maliyeti sıfırlanır.
Alternatif (ürün kararı): çözümleri HERKES için kısaltmak — %28'in içinden
anlamlı pay alır ama çözüm sayfası öğretmen/veli için değer taşıyor; 3+ tekrarlı
düzgün A/B şart.

### 3.6 AÇIK — top-up çağrıları hedeften büyük üretiyor
matematik g8: 5 eksik soru için atılan top-up çağrısı **24.302 çıktı token'ı**
üretti (ilk çağrıdan bile büyük). Retry prompt'u üretilmiş tüm soruları bağlama
koyuyor ve çıktı tavanı yok.

### 3.7 AÇIK — `mixed` mod 3 ayrı üretim koşusu
Ücretsiz kullanıcıda 3 bucket'ın **hepsi aynı modeli** alıyor (`is_premium_for_model`
= False) → 3 ayrı `generate()` koşusunun tek teknik gerekçesi kalmıyor. Prompt
zaten tip/zorluk dağılımı taşıyor → tek çağrıda "3 kolay + 4 orta + 3 zor"
istenebilir. Ölçülen fark: soru başına **2.6×**.

### 3.8 AÇIK — fallback zincirinde `gemini-2.5-pro` + sayılmayan token'lar
`GEMINI_FALLBACK_MODELS=gemini-2.5-flash-lite,gemini-2.5-pro`. Şema-drop gibi
KALICI hatada zincir pro'ya düşüyor ($10/1M çıktı = 2.5-flash'ın 4×'i) ve pro
thinking'i kapatamıyor. Ayrıca `call_with_chain` başarısız çağrının token'ını
istisna ile birlikte düşürüyor → **fatura ödüyor, defter görmüyor** (bu, faturayı
defterin üzerinde tutan farkın bir kısmı — GEMINI_COST_POLICY §1'deki 18× farkın
kalıntısı).

### 3.9 AÇIK — cache pratikte tutmuyor
`llm_cache` anahtarı **tam soru sayısını** içeriyor (`q20`) → 10 soruluk set 20
soruluk isteğe hizmet etmiyor; set-bazlı saklama soru-bazlı yeniden kullanıma
izin vermiyor.

## 4. Plan — kalite DÜŞMEDEN maliyeti 6-8× düşürmek

Sıra, (tasarruf × güvenlik) çarpımına göre.

### Faz 0 — saf israf (kalite etkisi YOK) ✅ bu oturumda yapıldı
1. ✅ `mixed`/`progressive` 500 fix (§3.1) — `tests/test_cost_waste_fixes.py`
2. ✅ Critic gruplama + sonlu çıktı tavanı (§3.2) — kalite **artar** (filtreleme
   fiilen geri geliyor), maliyet ve gecikme düşer

### Faz 1 — düşük riskli, ölçülebilir ✅ (mixed-birleştirme hariç) yapıldı
3. ✅ **Overshoot envantere çevrildi** (§3.4): `SpareQuestionPool` (soru-BAZLI,
   anahtarda soru sayısı YOK). Kırpılan fazlalar havuza yazılır; post-filter
   eksiği **önce bu istekteki yedeklerden, sonra havuzdan** kapanır — LLM top-up
   son çare. Havuzdan çekim `used_count` ile en az kullanılanı önceler, tenant
   history'siyle çakışanı atlar, çekilen soru SİLİNMEZ (farklı kullanıcıya
   tekrar servis = maliyet düşüşü).
4. ❌ **Sınav modunda kısa çözüm — DENENDİ, ÖLÇÜLDÜ, GERİ ALINDI** (§3.5).
   Kazanç kağıt maliyetinin ~%8'i (varyans ±%15 → ölçülemez); bedeli cache/havuz
   anahtarının bölünmesi ve yeniden kullanım kaybı. Doğru yol Faz 3 (çözümü
   havuzda bir kez üret, sonsuza kadar sakla).
5. ✅ **Top-up + birincil + retry çağrılarına çıktı tavanı** (§3.6, §3.2b).
6. ✅ **Fallback zincirinden `2.5-pro` çıkarıldı; başarısız çağrı token'ları
   deftere yazılıyor** (§3.8) — `ProviderResponse.wasted` + `wasted_cost_usd`.
7. ⏸ **`mixed` modu tek çağrıda birleştirme** (§3.7) — ERTELENDİ. Gerekçe:
   birleştirme `GeneratedQuestion`'a soru-başına `difficulty` alanı eklemeyi ve
   zorluk etiketini MODELİN kendi beyanına güvenmeyi gerektiriyor (bugün zorluk
   bucket'tan deterministik geliyor). Yanlış etiket → progressive sıralama ve
   zorluk kalibrasyonu bozulur = kalite riski. Faz 2 A/B'siyle birlikte
   değerlendirilmeli. Ara kazanç: havuz sayesinde küçük bucket'ların overshoot
   fazlaları da artık stoğa gidiyor.

### Faz 2 — geometri model/thinking kalibrasyonu (tek karar, ~−%30 toplam)

**Hedef:** geometri kağıdı 7.99 → ~2.5 TL. Faz 1 sonrası ortalamanın baskın
kalemi tek başına bu (diğer senaryolar 1.0-2.0 TL bandında).

**Neden şimdi mümkün:** geometri 3.5-flash'a 2026-07 A/B'siyle alındı, gerekçe
"2.5 geometri SVG'sinde zorlanıyor"du (GEMINI_COST_POLICY §3). O tarihte model
`<svg>`'yi ELLE çiziyordu. Bugün 8 şekil `{{geo:...}}` direktifiyle geliyor
(`svg_utils.process_geo_directives`: right_triangle, triangle, rectangle, square,
circle, parallelogram, trapezoid, angle) ve SVG'yi KOD üretiyor; modelin işi
~30 karakterlik direktif yazmak. `oruntu_sekil` de `{{pattern:...}}`'a geçmiş
(§6'daki plan tamamlanmış). **3.5'in gerekçesi büyük ölçüde ortadan kalkmış
olabilir — ölçmeden bilinemez.**

Ayrıca: 2026-07-23 thinking-tavanı A/B'si **REDDEDİLMİŞTİ**, ama
`scripts/eval/thinking_ab.py:TEST_MODEL = "gemini-2.5-flash"` → o deney *ucuz*
modeli 512/1024/2048 ile test etti. 17.257 thinking token'ının yandığı
**3.5-flash hiç test edilmedi.** Farklı rejim, yeniden ölçülmeli.

**Deney kolları:**

| Kol | Model | Thinking | Test ettiği soru |
|---|---|---|---|
| A (kontrol) | 3.5-flash | −1 (dinamik) | bugünkü prod |
| B | 3.5-flash | 4096 | thinking'in ne kadarı gerçekten gerekli |
| C | 2.5-flash | −1 | direktif çağında güçlü model gerekli mi (çıktı fiyatı 3.6× düşük) |
| D | 2.5-flash | 2048 | en ucuz kol (C geçerse dene) |

**Harness:** `scripts/eval/thinking_ab.py` yeniden kullanılır (LEVELS bütçe
haritası, RunRow token+maliyet+soru dökümü, JSON+özet çıktısı hazır). İki
eksiği var: (1) `TEST_MODEL` sabit → **`--models` ekseni parametreleştirilmeli**;
(2) senaryolar grade 8 sabit → geometri 6 ve 7 de eklenmeli. ~30 satır.

**Örneklem ve maliyet:** 3 geometri senaryosu (g6, g7, g8 `M.8.4.1.4`) × 4 kol ×
**5 iterasyon**, qcount=10. Neden 5: ölçülen koşu-arası varyans **±%15** —
2 iterasyonla %8'lik fark ayırt edilemez (kısa-çözüm dersi, §3.5). Tahmini
maliyet **~$6 (~210 TL)**. Erken kesme: önce A vs C 3 iterasyon; fark bariz ise
D'ye geç, değilse tam matrisi koş.

**Kalite metrikleri (otomatik):** `delivered/requested` · `critic_rejected` ·
`math_verifier_rejected` · **figürlü oran** (`<svg` içeren soru %'si — geometri
kağıdının asıl vaadi) · **direktif ihlali** (direktif yerine ham `<svg>` yazma).
Otomatikle ölçülemeyen: şekil-soru tutarlılığı → her koldan 10 soru göz denetimi.

**Karar eşiği (ÖNCEDEN yazılı — sonradan yorumla esnetilmeyecek):**
- C, A'ya göre eleme oranı **≤ +5 puan** VE figürlü oran **≥ %90** VE göz
  denetiminde şekil-soru tutarsızlığı yoksa → **geometri ucuz modele döner.**
- C düşer, B ≈ A ise → `gemini_thinking_budget_strong = 4096`.
- İkisi de düşerse → geometri pahalı KALIR; kaldıraç Faz 3'e devredilir (geometri
  sorusunu bir kez üret, sonsuza kadar yeniden kullan).

**Uygulama:** karar tek config satırı. Geri alma kolaylığı için `model_for`'daki
geometri dalına bayrak (`geometry_uses_strong_model: bool = True`) eklenmeli —
env ile redeploy'suz açılıp kapanabilsin.

### Faz 3 — soru havuzunu servise açmak (asıl yapısal kaldıraç, −%70+)

Faz 1'de havuz (`SpareQuestionPool`) inşa edildi ama **yalnız post-filter
eksiğini** kapatıyor. Faz 3 = havuzu **birincil servis yolu** yapmak.

**3a. Havuzu üretimin ÖNÜNE al (en büyük tek kazanç)**
- Bugünkü akış: cache → LLM üret → filtre → (yedek/havuz) → top-up.
- Hedef akış: cache → **havuz (istenen sayının tamamı)** → yalnız eksik kadar LLM.
- Tekrar engeli hazır: `GENERATION_HISTORY.seen_questions()` +
  `SPARE_POOL.take(exclude_norms=...)`.
- **Çeşitlilik riski:** iki kullanıcı aynı üniteyi seçince aynı 20 soruyu alır.
  Önlem: havuz ≥ 3× istenen sayı olduğunda `used_count ASC` + rastgele
  karıştırma; havuz doluluğu eşik altındaysa yine üret (havuzu büyütmek için).
- **Ayrıca çözülmesi gereken:** `GENERATION_HISTORY` FIFO `capacity_per_key=30`
  → havuz kalıcı ama tekrar-engeli hafızası sınırlı; uzun vadede kullanıcı eski
  soruyu yeniden görür. Kapasite/politika Faz 3'te gözden geçirilmeli.

**3b. Gece Batch API ile ön-doldurma (%50 indirim)**
- Gemini Batch: aynı model, asenkron, **yarı fiyat**. ÖNCE doğrulanmalı
  (2.5-flash batch desteği + kota + `google-genai` SDK yolu).
- Kapsam: (ders × sınıf × ünite × zorluk) ≈ 5 ders × 4-8 sınıf × ~6 ünite × 3
  zorluk ≈ **500-700 kova**; kova başına 20 soru ≈ 12K soru.
- Tek seferlik maliyet: 12K × ~0.06 TL (ucuz model, batch %50) ≈ **700-800 TL**.
  Karşılığı: ilk ~12K soru servisi bedava, sonrası marjinal.
- **Asıl nokta kalite:** ön-doldurma ÇEVRİMDIŞI olduğu için pahalı ayarlar burada
  kullanılabilir — güçlü model + yüksek thinking + sıkı critic + çift geçiş.
  Servis bedava olduğundan bu, "kaliteyi düşürmeden ucuzlatma" değil
  **kaliteyi YÜKSELTİP ucuzlatma** hamlesidir.
- Sıra: `usage_ledger`'daki grade/topic dağılımına göre en çok kullanılan
  kovalar önce (kör doldurma değil).

**3c. Havuz kalite döngüsü**
- **Sinyal 1 (mevcut, bedava):** `attempts.answers_json` soru-bazlı doğru/yanlış
  taşıyor → yanlış oranı anormal yüksek (ör. çok denemede %100 yanlış) soru =
  cevap anahtarı bozuk şüphesi. Bağlamak için havuz sorusuna kalıcı
  `question_id` + quiz sorusundan ona referans gerekiyor (bugün YOK).
- **Sinyal 2 (küçük iş):** "soruyu bildir" — bugün YOK (kodda hiç yok). Web+mobil
  tek dokunuş → havuzda `flagged_count`.
- **Sinyal 3:** critic'i havuz üzerinde periyodik yeniden koş (model
  güncellendiğinde eski stoğu yeniden denetle).
- **Eylem:** `quality_score` (kabul geçmişi − bayrak − yanlış-oranı anomalisi) →
  eşik altı havuzdan çıkar. Üst dilim "altın havuz" → few-shot besleme adayı
  (bugün few-shot 133 statik gerçek MEB sorusu; havuz onu büyütebilir).

**3d. Şema ve mimari işleri**
- `spare_questions` bugün: `pool_key, norm_question, question_json, used_count,
  created_at`. Eklenecek: `question_id` (kalıcı referans), `subject`, `grade`,
  `unit_id`, `kazanim_kod`, `question_type` (bugün pool_key string'inin İÇİNDE
  gömülü → sorgulanamaz), `quality_score`, `flagged_count`, `critic_pass`,
  `source` (live-overshoot | batch-prewarm).
- `generation_cache` (set-bazlı, `q{count}` anahtarlı, isabet oranı düşük) uzun
  vadede **gereksizleşir** → havuz yerini alır; geçişte bir arada yaşarlar,
  sonra cache kaldırılır (kod sadeleşir).
- Turso boyutu: 12K soru × ~2KB ≈ 25MB — sorun değil.
- Overshoot oranı (1.8) artık İSRAF DEĞİL: fazlalar stoğa gidiyor → düşürmeye
  gerek yok, hatta havuzu besliyor.

### Faz 4 — koruma bandı (ölçüm + tavan)

Faz 1'de canlıda ısıran iki gözlemlenebilirlik boşluğu da buraya ait.

**4a. Defter zenginleştirme** — `usage_ledger` bugün: tenant, model, tokens,
cost, grade, topic, question_count, cache_hit. Eklenecek: `subject`,
`difficulty_mode`, `plan` (free/pro/pro-plus/trial), `thinking_tokens` (ayrı),
`generated_count` vs `delivered_count`, `wasted_cost_usd` (Faz 1'de ölçülüyor
ama kolonu yok), `pool_hit_count`, `source`. Kazanç: **plan başına gerçek
TL/kağıt** panosu → marj kararları tahminle değil veriyle.

**4b. Kısmi teslim görünürlüğü (Faz 1'de canlıda ısırdı)**
mixed modda bucket hatası `except Exception` ile yutuluyor → kullanıcı sessizce
2/5 soru alıyor, biz göremiyoruz. Canlı arızayı ancak `trace.requested_count`'un
yalnız BAŞARILI bucket'ları toplamasından çıkarabildim. Yapılacak: bucket
hatalarını metadata'ya taşı (`bucket_errors`), Sentry'ye ayrı event, **teslim <
istenen** durumunda uyarı logu + defter alanı.

**4c. Günlük harcama alarmı** — 2026-07-10'da tek günde **$9.06** patlaması
olmuş (GEMINI_COST_POLICY §2), bugün alarm YOK. `usage_ledger` günlük toplamı +
eşik (ör. $2/gün) → e-posta/Sentry; mevcut keepalive workflow kalıbıyla cron.

**4d. Tenant başına maliyet tavanı** — kota birimi "kağıt" (MONETIZATION_PLAN §2)
ama kağıt maliyeti **10× değişiyor** (sözel 1.16 vs geometri 8 TL) → aynı kotayı
kullanan iki abone çok farklı maliyet üretir. Öneri: kota kağıt olarak KALSIN
(kullanıcıya anlaşılır), arkada maliyet tavanı olsun — tenant aylık LLM maliyeti
eşiği aşarsa (ör. Pro'da 60 TL) **havuz-only** servise düşer (kalite aynı, üretim
yok). Kota vaadi bozulmaz, marj korunur. **Faz 3 olmadan uygulanamaz** → sıra: 3 → 4d.

### Önerilen sıra

`Faz 2` (küçük, tek karar, ~%30) → `3a` (havuzu servise al) → `4a`+`4b` (ölçüm
ve görünürlük) → `3b` (batch ön-doldurma) → `3c` (kalite döngüsü) → `4c`+`4d`
(alarm + tavan). Ertelenen: `mixed` tek-çağrı birleştirme (§3.7 — soru-başına
zorluk etiketini modele bırakmak kalite riski; Faz 2 A/B'siyle birlikte bakılmalı).

## 5. Faz 0+1 SONRASI — aynı senaryolarla yeniden ölçüm

Aynı probe, aynı senaryolar, cache kapalı (20 soru, `single`):

| Senaryo | Önce | **Sonra** | Δ maliyet | Süre (önce→sonra) |
|---|--:|--:|--:|--:|
| sosyal g7 | 1.16 TL | (değişim beklenmez¹) | — | 74 s |
| matematik g5 | 3.00 TL | **1.02 TL** | **−%66** | 166 s → **58 s** |
| türkçe g8 | 3.64 TL | **1.65 TL** | **−%55** | 207 s → **98 s** |
| matematik g8 | 5.13 TL | **1.95 TL** | **−%62** | **361 s → 110 s** |
| matematik g7 geometri | 8.05 TL | 7.99 TL | ~0 | 94 s → 100 s |

¹ sosyal g7 zaten top-up/critic-taşması yaşamıyordu (tek üretim + tek critic
çağrısı) → Faz 1 kalemleri o senaryoda devreye girmiyor.

Geometri hariç ortalama: **4.20 → 1.45 TL** (−%65). Geometri dahil: 2.75 TL.
**Geometri artık tek başına baskın kalem** → Faz 2'nin hedefi net.

Ayrıca ölçümde yakalanan uç örnek (§3.2b): tavansız üretimde bir g5 kağıdı
**7.30 TL**'ye ve **469 saniyeye** çıkıp yalnız 18/20 soru teslim etmişti;
tavandan sonra aynı senaryo 0.87-1.17 TL / 55-62 sn / 20/20.

### Hedef tablo (güncel)

| Aşama | Maliyet/kağıt | Pro brüt marj |
|---|--:|--:|
| Başlangıç (ölçülen) | 4.20 TL | −%24 |
| **Faz 0+1 (ölçülen)** | **2.75 TL** (geometri hariç 1.45) | **%19** (geo hariç %57) |
| + Faz 2 (geometri modeli/thinking) | ~1.2 TL | %64 |
| + Faz 3 (havuz %70 isabet) | **~0.4 TL** | **%88** |

## 5b. Faz 1'de değişen dosyalar

| Dosya | Değişiklik |
|---|---|
| `app/services/agent.py` | `output_cap_for()`; yedek-önce doldurma (`_apply_post_filters`/`_accept`); critic bağlamı memoize; israf token'ı toplama |
| `app/services/llm_cache.py` | `SpareQuestionPool` + `SPARE_POOL` + `_pool_key` (soru-bazlı envanter) |
| `app/services/llm_providers.py` | `max_output_tokens`; `ProviderError.usage`; `ProviderResponse.wasted`/`wasted_cost_usd` |
| `app/services/critic.py` | gruplama + sonlu çıktı tavanı + çözüm kırpma + index öteleme |
| `app/routers/worksheets.py` | mixed/progressive 500 fix |
| `app/config.py` | `critic_batch_size`, `critic_max_solution_chars`, `enable_spare_pool`, `spare_pool_max_per_key`, `generation_output_cap_*`; fallback'ten `2.5-pro` çıkarıldı |
| `tests/test_cost_waste_fixes.py`, `tests/test_spare_pool.py` | 17 yeni test (mixed 500, critic gruplama, havuz, çıktı tavanı, israf defteri, kısa-çözüm geri-alma kilidi) |
| `.github/workflows/eval.yml` | pytest adımı eklendi — bu testler CI'da KOŞMUYORDU (pytest ne requirements'ta ne workflow'da vardı) |

Redeploy'suz geri alma: `ENABLE_SPARE_POOL=false`, `CRITIC_BATCH_SIZE=999`,
`GENERATION_OUTPUT_CAP_PER_QUESTION` büyük bir değer (tavanı etkisizleştirir).

## 6. Ölçüm araçları

Bu belgedeki sayılar `scratchpad/cost_probe.py` (SDK-seviyesi çağrı yakalayıcı)
ile üretildi. Kalıcı hâle getirilmesi önerilir: `scripts/eval/cost_probe.py` →
her PR'da bir senaryo matrisi koşup TL/kağıt regresyonunu raporlar.
