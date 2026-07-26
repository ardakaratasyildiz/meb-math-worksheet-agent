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

### Faz 2 — model/thinking kalibrasyonu (tahmini −%30, A/B şart)
8. **Geometri A/B'sini YENİLE** (§3.3): geometrinin 3.5-flash'a alınma gerekçesi
   "2.5 SVG'yi tutturamıyor"du. Artık şekiller `{{geo:...}}` direktifiyle
   **deterministik** üretiliyor → gerekçe büyük ölçüde geçersiz. 2.5-flash +
   direktif vs 3.5-flash karşılaştırılsın; 2.5 geçerse o kalemde **−%72**.
9. **Güçlü modelde thinking'e tavan** (§3.3): dinamik (−1) yerine 4096-8192.
   NOT: 2026-07-23 A/B'sinde tavan REDDEDİLMİŞTİ, ama o deney *ucuz* modeli
   512/1024/2048 ile test etti; güçlü modelde 17K thinking'e 6-8K tavan farklı
   bir rejim. Kalite eşiği tutmazsa geri alınır.

### Faz 3 — yapısal çözüm: soru havuzu (asıl kaldıraç, −%70+)
10. **Soru-bazlı havuz (question bank)** — `llm_cache`'in set-bazlı yapısını
    (§3.9) soru-bazlı envanterle değiştir: her critic'ten geçmiş soru
    (ders, sınıf, ünite, kazanım, zorluk, tip, kalite skoru, kullanım sayısı)
    tek tek saklanır. Kağıt = havuzdan kompozisyon (kullanıcı-bazlı tekrar
    engeli için mevcut `GENERATION_HISTORY` zaten var) + yalnız **eksik kadar**
    üretim.
    - Overshoot fazlaları, top-up fazlaları, iptal edilen kağıtlar → hepsi stok.
    - Doluluk arttıkça maliyet/kağıt **0'a** yaklaşır; %70 isabetle ~1.2 TL.
11. **Havuzu gece Batch API ile doldur** (Gemini Batch = **%50 indirim**):
    (sınıf × ünite × zorluk) başına N soru bir kez üretilir. Bu, kaliteyi
    **yükselten** hamle: pahalı model + yüksek thinking + sıkı critic yalnız
    havuz inşasında kullanılır (bir kez, ucuza, çevrimdışı), kullanıcıya servis
    bedava olur. "Kaliteyi düşürmeden ucuzlatmak" yerine **kaliteyi artırıp
    ucuzlatmak** bu maddeyle olur.
12. **Havuz kalite döngüsü**: /coz cevap istatistikleri + kullanıcı "soruyu
    bildir" sinyali ile kötü soruları ayıkla → havuz zamanla iyileşir
    (bugün her istek sıfırdan kumar atıyor).

### Faz 4 — koruma bandı
13. **Defter zenginleştirme**: ders, `difficulty_mode`, plan, thinking token'ı,
    üretilen-vs-teslim sayısı, başarısız çağrı token'ı → plan başına gerçek
    "TL/kağıt" panosu.
14. **Günlük harcama alarmı** (2026-07-10'da tek günde $9.06 patlaması olmuştu)
    + **tenant başına aylık maliyet tavanı**: eşiği aşan kullanıcı havuz-only
    servise düşer (kota vaadi bozulmaz, marj korunur).

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
