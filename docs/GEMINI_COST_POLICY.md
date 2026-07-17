# Gemini Maliyet Politikası

_Son güncelleme: 2026-07-17. Kaynak: Cloud Monitoring (gerçek token verisi) + A/B evaluasyonları._

Bu belge, Gemini üretim maliyetini düşürmek için alınan **model + thinking + yeni_nesil**
kararlarının gerekçesini, dayandığı ölçümleri ve uygulanan politikayı tek yerde tutar.

## 1. Problem

- Admin panelindeki iç maliyet defteri bir gün için **~$0.07** gösterirken Google faturası
  **~45 TL (~$1.3)** çıktı — ~18× fark.
- İki kök neden: (a) **thinking (düşünme) token'ları sayılmıyordu** — Gemini 2.5/3 faturayı
  `candidates + thoughts_token_count` üzerinden keser, kod yalnız `candidates`'ı sayıyordu;
  (b) **quiz üretimi deftere hiç yazılmıyordu** (tek `USAGE_LEDGER.record` worksheet'teydi).
  → PR #115 ile kapatıldı.

## 2. Gerçek maliyet verisi (Cloud Monitoring, 8 gün: 2026-07-09→17)

`metrics-reader` benzeri bir SA + `generativelanguage.googleapis.com/generate_content_usage_output_token_count`
(çıktı, **thinking dahil**), `.../paid_tier_input_token_count` (girdi), `serviceruntime/request_count`.

| Model | Girdi tok | Çıktı tok | Çıktının thinking'i | ~Maliyet | Pay |
|---|--:|--:|--:|--:|--:|
| gemini-3.5-flash | 1.08M | 1.13M | %100 | **$11.78** | **%86** |
| gemini-2.5-flash | 800K | 534K | %100 | $1.58 | %12 |
| gemini-2.5-flash-lite | 886K | 388K | %0 | $0.24 | %2 |
| gemini-2.5-pro | 14K | 8.5K | %100 | $0.10 | <%1 |
| **TOPLAM** | **2.78M** | **2.06M** | | **$13.70 (~480 TL)** | |

**Bulgular:**
- **gemini-3.5-flash maliyetin %86'sı** (5-8. sınıf varsayılan modeliydi).
- **Çıktının ~%100'ü thinking'li** → thinking, maliyetin baş sürücüsü.
- İsraf/retry DEĞİL: 2785 istekte 6×503 + 2×400 (%99.7 başarı).
- Günlük zirve: **2026-07-10 = $9.06 (~317 TL)** — tek günde patlama (alarm ihtiyacı).

## 3. A/B evaluasyonları (özet)

**Thinking, 1-4 (2.5-flash):** kapatmak güvenli.
- g2 kolay: çıktı token **−%76** (5870→1422), teslim 4/4 aynı, 0 eleme.
- g3 orta: çıktı token **−%49** (5938→3020), teslim 4/4.

**Thinking, 5-7 (2.5-flash):** düşük(512) tatlı nokta, kapalı riskli.
- g7 cebir: 512 → **−%41 token, 0 eleme** (kalite birebir). Kapalı → 2 eleme, maliyet ARTTI.
- g6 kesir: 512 → −%10 token, 2 critic elemesi (teslim yine 5/5). Kapalı → 1 math+3 critic.

**Model, görsel (2.5 vs 3.5):**
- Geometri (g6): ikisi de 5/5 SVG; 2.5 **1 retry + 2.5× token** yaktı → maliyet 3.5'in %72'si (küçük kazanç).
- Grafik (g7): ikisi de 5/5; 2.5 = 3.5'in **%46'sı** (net kazanç).
- **Örüntü (g5/g6): iki model de güvenilmez** — teslim 1-5/5 arası, yüksek token. g6'da 3.5 **1/5, 88K tok, $0.83**. → Model sorunu değil; örüntü SVG üretiminin kendisi sorunlu (bkz. §6).

**Sonuç:** geometri → güçlü model (2.5 zorlanıyor); grafik/genel içerik → ucuz model (2.5 yeterli);
thinking 1-4 kapalı / 5-7 düşük.

## 4. Uygulanan politika

### Model seçimi — `app/services/agent.py::model_for(grade, is_geometry, difficulty, is_premium)`

| Plan | 1-4 | 5-7 | 8 |
|---|---|---|---|
| **Ücretsiz** | 2.5-flash | geometri→3.5 · gerisi→2.5 | geometri→3.5 · gerisi→2.5 |
| **Premium** | 2.5-flash | geometri→3.5 · **ZOR bucket→3.5** · kolay/orta→2.5 | **komple 3.5** |

Öncelik sırası: 1-4→ucuz · geometri→güçlü · 8+premium→güçlü · 5-7+premium+ZOR→güçlü · diğer→ucuz.

**Kritik:** `is_premium` = **GERÇEK abonelik/trial** (`entitlements.is_premium_for_model`,
`billing_store`), `premium_all` dark-launch bayrağı **DEĞİL**. Ödeyen ~0 olduğu sürece herkes
ucuz-model kurallarını alır (maksimum tasarruf); billing canlı olunca premium ayrımı otomatik devreye girer.

Model seçimi zorluğa bağlı → **her difficulty bucket kendi modelini seçer** (mevcut bucket
mimarisine biner, **ekstra LLM çağrısı yok**).

### Thinking bütçesi — `agent.py::thinking_for_model(grade, model)`

| Durum | Bütçe |
|---|---|
| Güçlü model (3.5, geometri/premium) | -1 (dinamik — kaliteyi koru) |
| Ucuz model, 1-4 | 0 (kapalı) |
| Ucuz model, 5-7 | 512 (düşük) |
| Ucuz model, 8 | -1 (dinamik) |

> `gemini-2.5-pro` düşünmeyi kapatamaz → `llm_providers` `budget=0`'ı pro modelde dinamiğe çevirir.

### yeni_nesil (beceri-temelli mod) — `entitlements.yeni_nesil_for_bucket(tenant, difficulty)`

- **Premium** → full (her bucket yeni_nesil).
- **Ücretsiz** → TEASER: yalnız `free_yeni_nesil_bucket` (varsayılan "orta") zorluğundaki bucket.
- Soru-başına bölme YOK → mevcut zorluk bucket'ına biner (ekstra çağrı yok).
- Hem worksheet hem **quiz** (quiz'e PR #118 ile bağlandı; önceden yoktu).
- Dark-launch: `premium_all=True` herkesi premium yapar → teaser dormant, herkes full alır (UX düşmez).

## 5. Config anahtarları (redeploy'suz tune)

```
gemini_model_grade_1_4 = "gemini-2.5-flash"   # ucuz kutup
gemini_model_grade_5_8 = "gemini-3.5-flash"   # güçlü kutup
gemini_thinking_budget_grade_1_4 = 0
gemini_thinking_budget_grade_5_7 = 512
gemini_thinking_budget_grade_8   = -1
gemini_thinking_budget_strong    = -1
free_yeni_nesil_enabled = True
free_yeni_nesil_bucket  = "orta"
```

## 6. Örüntü (oruntu_sekil) — bilinen sorun + plan

Örüntü iki modelde de düşük-yield + yüksek-token. Kök sebep: **`grafik_okuma` bir `{{chart:...}}`
direktifi kullanıp SVG'yi KOD deterministik üretiyor (güvenilir), ama `oruntu_sekil` modelin
ham `<svg>`'yi ELLE yazmasını istiyor** → tutturamıyor, eleniyor, top-up yakıyor.

**Plan:** örüntüye de direktif + deterministik renderer ekle (`{{pattern:...}}` → `svg_utils`).
→ örüntü de grafik gibi ~%100 güvenilir + ucuz + model-bağımsız olur (3.5'e gerek kalmaz).

## 7. Nasıl ölçülür / doğrulanır

- `usage_ledger` artık **grade + model** kaydediyor → admin panelindeki "Gemini maliyeti" kartı
  birkaç gün sonra gerçek düşüşü gösterir. (Yapılacak: `plan` alanı + panelde TL + günlük alarm.)
- Cloud Monitoring: SA ile `generate_content_usage_output_token_count` (model+gün) haftalık karşılaştırma.

## 8. Beklenen etki

Dark-launch (ödeyen ~0): herkes ücretsiz-model → 5-8 geometri-dışı 3.5→2.5. Toplam Gemini
maliyeti tahmini **~%55-70 ↓** (~$51/ay → ~$15-23/ay). Kalite A/B'lerle korundu.

## İlgili PR'lar
- #115 — defter doğruluğu (thinking sayımı + quiz kaydı)
- #117 — model + thinking politikası
- #118 — yeni_nesil teaser + quiz'e bağlama
