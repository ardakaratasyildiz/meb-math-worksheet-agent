# Maliyet + Kalite V2 — Plan

_2026-07-28. `docs/COST_REDUCTION_PLAN.md`'nin (Faz 0/1 canlı, Faz 2/3/4 açık) ÜSTÜNE
gelir; onu iptal etmez, sırasını ve kapsamını kullanıcı kararlarıyla revize eder._

## 0. Neden bu belge var

Faz 0+1 kağıt maliyetini 4.20 → 2.75 TL'ye indirdi (ölçülmüş). Ama iş "havada"
kaldı, çünkü **iki eksen asimetrik ölçülüyor**:

| Eksen | Alet | Durum |
|---|---|---|
| Maliyet | `scratchpad/cost_probe.py` — SDK-seviyesi token yakalama, TL/kağıt, senaryo matrisi | **sağlam** |
| Kalite | `critic_pass_rate` + `delivered_ratio` (`scripts/eval/thresholds.json`) | **bozuk** |

Kalite göstergesinin neden bozuk olduğu (üçü birlikte):

1. **Kendi ödevini kendi not veriyor.** `critic_pass_rate`, critic'in KENDİ red
   oranı. Critic üreticiyle aynı model ailesi (`gemini-2.5-flash-lite`) ve
   **fail-open** (`critic.py:5` — erişilemez/parse edilemezse soruları GEÇİRİR).
2. **Doygun.** `thresholds.json`'da gözlenen değer `1.0000`, eşik `0.85`. 1.0'da
   duran metrik regresyon göstermez.
3. **Maliyet için ayarlandı.** `critic_min_confidence` 0.6 → **0.75**'e çıkarıldı;
   gerekçe kağıt maliyetini ~%50 düşürmekti (`config.py`). Yani kalite göstergesini
   maliyet uğruna gevşettik ve sonra o göstergeye bakıp "kalite korundu" dedik.

**Kanıt:** projedeki iki gerçek kalite kırılmasını da gate DEĞİL kullanıcı yakaladı —
(a) #117 sonrası sözel derslerin bozulması, (b) `eslestirme`/`siralama` sorularının
gövdesiz üretilmesi (commit `ee86598`). İkisi de "kalite %100" raporlanırken canlıdaydı.

Sonuç: her maliyet kararı (thinking kısma, model düşürme, overshoot, confidence
eşiği) kalite ekseninde **kör** alınıyor. Bu belgenin 1. maddesi bu körlüğü kapatır.

## 0b. Mimari teşhis — neden tavan burada değil

Soru uzayı **sonlu**: ders × sınıf × ünite × kazanım × tip × zorluk ≈ 500-700 kova.
Bir çalışma kağıdı bu uzaydan bir *örneklem*. Ama bugün her istek sıfırdan üretiyor:

- `generation_cache` anahtarında soru sayısı var (`q20`) → 10'luk set 20'lik isteğe
  hizmet etmiyor, isabet oranı ~0.
- `SPARE_POOL` (Faz 1) yalnız **post-filter eksiğini** kapatıyor; birincil yol değil.
- Canlı üretim mümkün olan **en pahalı ve en kalitesiz** kip: kullanıcı ekranda
  beklediği için ucuz model, kısık thinking, tek geçiş, insan denetimi yok.

Yani her müşteride fırın yeniden kurulup tek ekmek pişiriliyor.

**Bunun sonucu maliyet–kalite takası gibi görünüyor, ama değil.** Üretim çevrimdışına
alındığında bağ kopar: soru başına 3× harcayıp (güçlü model, uzun thinking, çift
denetim, göz denetimi) **servis edilen kağıt başına** 10× ucuz olmak mümkün, çünkü
bir soru yüzlerce kağıda hizmet eder. Bu yüzden depo (madde 2) hem maliyet hem
kalite hamlesidir.

## 1. Kullanıcı kararları (2026-07-28) — plan bunlara uyar

| # | Konu | Karar |
|---|---|---|
| 1 | Kalite terazisi | **ONAY** — ilk iş |
| 2 | Soru deposu | **KESİN YAPILACAK.** Çapraz-kullanıcı yeniden kullanım İSTENEN davranış ("birine ürettiğimiz soruyu başkası için de kullanabilmeliyiz"); tek kısıt: **aynı kullanıcıya aynı soru tekrar gitmesin** |
| 3 | Depoyu gece Batch API ile doldurma | **ERTELENDİ** — sonra detaylı konuşulacak, gündeme geri getirilecek |
| 4 | Parametrik soru kalıbı | **YALNIZ 1-4. sınıf matematik.** Yeni nesil ve geometri kalıplanMAZ (kalıp, yeni nesil sorunun değerini öldürür). 1-4 bile **tam kalıp değil** — kalıp + LLM karışık, kalıp oranı tavanlı |
| 5 | Geometri | **DOKUNMA.** Bu haliyle kalsın (3.5-flash + dinamik thinking). `COST_REDUCTION_PLAN` Faz 2 A/B'si **askıya alındı** |

### 5. kararın sonucu — açıkça yazılıyor

Geometri kağıt başına ~8 TL ile **en pahalı tek kalem** ve artık iki çıkış yolu da
kapalı: kalıplanmıyor (karar 4) ve model/thinking'i değiştirilmiyor (karar 5).

→ Geometrinin maliyeti **yalnız depo (madde 2) üzerinden** düşer. İyi haber: depo
kazancı üretim maliyetiyle **doğru orantılı** — 8 TL'lik bir soru 20 kağıtta
kullanılırsa kağıt başına 0.40 TL'ye iner. Yani "dokunmama" kararı depoyu
*daha* önemli hale getirir, alternatifsiz kılar.

## 2. MADDE 1 — Kalite terazisi (ilk iş)

**Amaç:** "denetleyicimiz işini yapıyor mu?" sorusunu ölçülebilir hale getirmek.
Para harcamayan, kendi verimizle çalışan bir sınav.

Terazi **iki** soruyu birlikte cevaplar — biri kalite, biri maliyet:

- **S1 (kalite):** Denetleyici bozuk soruyu yakalıyor mu? → *bozuk sette recall*
- **S2 (maliyet):** Denetleyici iyi soruyu boşuna eliyor mu? → *altın sette yanlış-alarm oranı*

S2 doğrudan paraya bağlı: her haksız red soruyu düşürür → top-up turu → yeniden
üretim. `critic_min_confidence` 0.6→0.75 kararı tam olarak bu ekseni gevşetmişti,
ama ölçülmemişti. Terazi bu kararı geriye dönük **denetleyebilir** hale getirir.

### 2a. Altın set (doğru cevabı bilinen gerçek sorular)

Kaynak repoda hazır — sentetik üretim YOK:

| Kaynak | Adet | Notu |
|---|--:|---|
| `app/subjects/turkce/few_shot.py` | 42 | MEB ÖDSGM + LGS, cevaplar resmî anahtarla doğrulanmış |
| `app/subjects/sosyal/few_shot.py` | 53 | aynı |
| `app/subjects/ingilizce/few_shot.py` | 38 | aynı |
| `app/subjects/fen/few_shot.py` | 5 | aynı |
| ChromaDB `questions/grade5/5-sinif-matematik-soru-bankasi.pdf` | 358 chunk | gerçek soru bankası; `answer` metadata'sı var → matematik pozitifleri buradan |
| **TOPLAM kullanılabilir** | **~200 seçilecek** | ders/sınıf dengeli örneklem |

⚠️ **`app/data/few_shot.py` (EXAMPLES_BY_GRADE, 1-7, 259 örnek) altın sete GİRMEZ** —
hiçbirinde `source` alanı yok, yani %100 sentetik (eko-odası). Bunlar ölçüt değil,
madde 4'ün *sebebi*.

### 2b. Bozuk set (~40 soru) — asıl kıymetli parça

Altın sorulardan **kod ile üretilen mutasyonlar**. Neden mutasyon: ground truth
kesin (hangi kusuru enjekte ettiğimizi biliyoruz), tekrar üretilebilir, elle
etiketleme gerekmez. Kusur tipleri **gerçek arızalardan** alınır:

| Kusur tipi | Kaynak arıza | Enjeksiyon |
|---|---|---|
| `empty_matching_body` | commit `ee86598` — "eşleştiriniz" yazıp öğe listesi vermeme | eşleştirme/sıralama gövdesinden öğe+şık listesini sil, yönergeyi bırak |
| `inline_duplicated_options` | commit `417d639` — şıklar hem metinde hem `.options`'ta | şıkları stem'e de kopyala |
| `wrong_answer_key` | genel güven riski | `answer`/`correct_index`'i başka bir şıkka kaydır |
| `solution_contradicts_answer` | critic'in 1. görevi | çözüm adımlarındaki sonucu değiştir, cevabı bırak |
| `kazanim_mismatch` | critic'in 3. görevi | `kazanim_kod`'u ilgisiz bir kodla değiştir |
| `difficulty_mismatch` | critic'in 4. görevi | tek adımlık soruyu `zor` etiketle |
| `truncated_stem` | format-drop belirtisi (§3.2b) | gövdeyi cümle ortasında kes |
| `dangling_reference` | `reference_integrity_issue` alanı | "yukarıdaki tabloya göre" ekle, tablo koyma |

Her tip için ~5 örnek → ~40 soru. Her kayıt: `defect_type`, `source_gold_id`,
`should_be_caught_by` (`deterministic` | `critic` | `both`).

### 2c. Sınav arabası

`scripts/eval/quality_bench.py` — iki katmanı ayrı ayrı ölçer:

1. **Deterministik doğrulayıcılar** (bedava, LLM yok): `structured.structured_content_issue`,
   `reference_integrity_issue`, `math_verifier`. Bunlar hangi kusuru yakalıyor?
2. **LLM critic** (`GeminiCritic`, flash-lite, gruplu): kalanları yakalıyor mu?

Rapor **tek sayı değil, kusur-tipi × katman matrisi**:

```
kusur tipi                  det.  critic  toplam
empty_matching_body         5/5   -       5/5   ✓
wrong_answer_key            0/5   3/5     3/5   ⚠ %40 kaçak
kazanim_mismatch            0/5   1/5     1/5   ✗ kör nokta
...
ALTIN SET yanlış-alarm      0/200 7/200   %3.5
```

Maliyeti: 240 soru, 10'luk gruplar → ~24 flash-lite çağrısı ≈ **$0.02**. Her
değişiklikte koşulabilir.

### 2d. Kabul kriterleri (madde 1 bitti sayılır)

- `knowledge_base/eval/gold/gold_questions.json` — ≥180 gerçek soru, ders+sınıf dağılımı raporlu
- `knowledge_base/eval/gold/broken_questions.json` — ≥40 mutasyon, 8 kusur tipi kapsanmış
- `scripts/eval/quality_bench.py` — yukarıdaki matrisi basar, `--no-llm` ile LLM'siz koşar
- `tests/test_quality_bench.py` — mutasyon üreticileri deterministik, altın set şemaya uyuyor
- **Çıktı: bugünkü critic'in gerçek karnesi** (bu belgeye eklenecek)

### 2e. ÖLÇÜLEN KARNE — bugünkü denetleyicinin gerçek durumu (2026-07-28)

Terazi kuruldu ve koşuldu. Altın set 200 gerçek soru (44 kaynak, sentetik sızıntı yok —
testle kilitli), bozuk set 40 mutasyon (8 tip × 5). Aşağıdaki tablo **iki temiz
LLM'li koşunun** sonucu (`gemini-2.5-flash-lite`, `critic_min_confidence=0.75`,
`critic_batch_size=10`):

Aşağıdaki tablo **fail-open ayrımı yapılan, `•` fix'i sonrası, 2 iterasyonlu**
temiz koşunun sonucu (`--iters 2`; "ölçülemedi" hücreleri paydadan düşülmüş):

| Kusur tipi | Deterministik | Critic (ort.) | Kararlılık | Karar |
|---|--:|--:|---|---|
| `wrong_answer_key` | 0/5 | **%100** | 100-100 | critic güçlü |
| `solution_contradicts_answer` | 0/5 | **%100** | 100-100 | critic güçlü |
| `empty_matching_body` | **5/5** | — | stabil | det. güçlü (`ee86598` fix'i çalışıyor) |
| `dangling_reference` | **5/5** | — | stabil | det. güçlü |
| `truncated_stem` | 0/5 | %70 | **40-100** | kararsız — güvenilmez |
| `inline_duplicated_options` | 0/5 | %20 | 20-20 | **KÖR NOKTA** |
| `kazanim_mismatch` | 0/5 | **%0** | 0-0 | **KÖR NOKTA** |
| `difficulty_mismatch` | 0/5 | **%0** | 0-0 | **KÖR NOKTA** |

**Altın sette yanlış-alarm:** deterministik **0/200** (`•` fix'i sonrası — önce
2/200'dü) + critic ~**%3** (min 2.5 – max 3.5). Yani cevabı resmî anahtarla
doğrulanmış GERÇEK MEB sorularının ~%3'ü critic tarafından eleniyor; her eleme bir
top-up turu açıyor (= doğrudan para).

**`truncated_stem` kararsızlığı ayrıca önemli:** aynı 5 mutasyonda recall %40 ile
%100 arasında oynadı. Yani critic'in bu eksendeki kararı tesadüfe bağlı — tek
koşuya bakıp "yakalıyor" demek yanlış olurdu. Terazinin `--iters` özelliği tam
bunun için var.

**Yorum — "kalite %100" ne ölçüyormuş:**

1. Critic kendi sistem prompt'undaki **4 görevden 2'sini** yapıyor: matematiksel
   doğruluk (görev 1) ve çözüm tutarlılığı (görev 2) → 10/10.
2. **Diğer 2 görevi hiç yapmıyor:** kazanım uyumu (görev 3) ve zorluk uyumu
   (görev 4) → **0/10**. Prompt'ta yazıyor, pratikte sıfır.
3. Üstüne, iyi sorunun %3-4'ünü haksız eliyor.

Yani `critic_pass_rate = 1.00`, "bozuk soru yok" demek DEĞİL; "critic'in baktığı
2 eksende bozuk yok, bakmadığı 2 eksende bilgi yok" demek. Kağıtta yanlış kazanım
etiketi veya yanlış zorluk kalibrasyonu varsa hiçbir kapı onu tutmuyor.

### 2e-1. EN ÖNEMLİ OPERASYONEL BULGU — fail-open oranı ~%15 ve görünmez

Terazi fail-open'ı ayrı sayacak hâle getirilince ortaya çıktı: **2 iterasyonda 8
fail-open grubu, retry sonrası hâlâ 20 soru ölçülemedi.** İterasyon başına ~26
critic çağrısı → toplam ~52 çağrının **~%15'i** fail-open'a düştü (Google tarafı
`503 UNAVAILABLE — model is currently experiencing high demand`, `flash-lite`).

`critic.py` bugün 503'te 2 kez retry ediyor, sonra pes edip **sessizce tüm grubu
geçiriyor**. Terazi'ye eklenen 1 ekstra retry bir kısmını kurtardı → yani retry
politikası yetersiz, arıza kalıcı değil.

**Sonuçları:**
1. **Kalite:** üretimde critic çağrılarının ~%15'i hiç denetim yapmıyor ve bu
   HİÇBİR yerde görünmüyor. `critic_pass_rate=1.00`'ın bir kısmı fiilen budur.
2. **Maliyet (deponun tabanı):** depo damgası fail-CLOSED olduğu için (§3c, doğru
   karar) fail-open olan sorular **damgasız** kalır → her serviste yeniden
   denetlenir → deponun marjinal maliyeti sıfıra inmez. Yani critic
   güvenilirliği artık **doğrudan bir maliyet kalemi**.
3. `§3.2`'de belgelenen arıza modu teorik değil; 26 çağrılık minik bir koşuda bile
   sistematik olarak görülüyor.

**Yapılacak (yeni iş kalemi, Faz 2'den sonra):** critic dayanıklılığı —
(a) retry sayısı/backoff artışı + jitter, (b) 503'te daha küçük gruba bölerek
tekrar deneme, (c) ısrarlı 503'te ikinci modele düşme (`flash-lite` → `flash`;
critic ucuz olduğu için maliyet etkisi küçük), (d) fail-open olaylarını
`usage_ledger`'a/Sentry'ye yazma (bugün yalnız `logger.warning`). Kabul kriteri
teraziyle ölçülür: `--iters 3` koşusunda fail-open grubu ~0.

### 2e-2. Karnenin doğurduğu işler

- **KÖR NOKTA `kazanim_mismatch` + `difficulty_mismatch`:** critic prompt'u bu iki
  ekseni istiyor ama model yapmıyor. Muhtemel sebepler: flash-lite'ın kapasitesi,
  10'luk grupta 4 eksenin sulanması, ya da kazanım metninin prompt'ta yeterince
  belirgin olmaması. Deney: bu iki ekseni **ayrı ve ucuz** bir geçişe almak
  (ör. yalnız kazanım-uyumu soran tek amaçlı çağrı) vs prompt'u sıkılaştırmak.
  Terazi artık kararı ölçebilir.
- **KÖR NOKTA `inline_duplicated_options`:** hiçbir katman yakalamıyor. Bu arıza
  `417d639`'da yalnız RENDER tarafında maskelendi (`stripInlineOptions`), üretim
  tarafında hâlâ serbest → deterministik bir doğrulayıcı yazılmalı (ucuz, LLM'siz).
- **Yanlış-alarm %4-5:** ilk kök neden bulundu ve düzeltiliyor (aşağı, 2e-3).
  Kalanı `critic_min_confidence` kalibrasyonuyla ölçülecek.

### 2e-3. Terazinin ilk koşusunda bulunan ÜRETİM HATASI — `•` madde imi

Deterministik yanlış-alarmların (2/200) kök nedeni: `app/services/structured.py`
içindeki `_has_enum_items` / `_NUM_ITEM_RE` / `_ROMAN_ITEM_RE` yalnız **numaralı**
(`1.`, `2)`) ve **Roman** (`I.`, `II.`) madde imini tanıyor; **`•` bullet'ı
tanımıyor.** Ama `•` gerçek MEB/ÖDSGM formatı.

Ölçüm: **kendi few-shot havuzumuzun %11'i (138 örneğin 15'i) `•` kullanıyor**, ve
2 few-shot örneği doğrudan kendi doğrulayıcımız tarafından reddediliyor.

→ Modele `•` formatını **öğretiyoruz**, ürettiğinde **eliyoruz**, sonra eksiği
kapatmak için **top-up parası ödüyoruz**. Kapalı devre israf. Fix: madde imi
tanımına bullet karakterleri eklenir; kabul kriteri hem `det` yanlış-alarmın
2/200 → 0/200 inmesi HEM `empty_matching_body`/`dangling_reference`'ın 5/5
kalması (yakalama gevşemeden).

### 2f. Madde 1'in sonrasına etkisi

Terazi kurulduktan sonra bugüne kadar körlemesine alınmış üç karar **geriye dönük
denetlenir** ve gerekiyorsa geri alınır:

- `critic_min_confidence = 0.75` — yanlış-alarm ne kadar düştü, kaçak ne kadar arttı?
- `critic_batch_size = 10` — gruplama yakalama oranını düşürdü mü?
- `gemini_thinking_budget_grade_1_4 = 0` / `_5_7 = 512` — kısma neyi kaybettirdi?

## 3. MADDE 2 — Soru deposu (üç parça)

### 3a. Kalıcı görülmüş-seti (ÖNKOŞUL — bugün bozuk)

**Bulgu:** `app/services/history.py:69` `capacity_per_key=30` + `deque(maxlen=30)`.
Veritabanı her soruyu saklıyor, ama `seen_questions()` yalnız **son 30**'unu görüyor
(`_load_from_db` tüm satırları okuyup 30'luk deque'e dolduruyor → gerisi düşüyor).

Anahtar = (kullanıcı, sınıf, ünite, kazanım, zorluk). Pratikte:

- 20 soruluk kağıt → 20 kayıt
- Aynı üniteden 2. kağıt → ilk 10 soru hafızadan düşer
- 3. kağıt → **1. kağıdın soruları "hiç görülmemiş" sayılır ve tekrar gelebilir**

Kullanıcının "en başından beri kurmaya çalıştığı" şeyin eksik parçası tam olarak bu.
Depo devreye girmeden önce düzeltilmeli — depo tekrar riskini büyütür.

**Yapılacak:** kullanıcı-bazlı görülmüş-seti kalıcı ve tavansız olsun. Soru metnini
RAM'de tutmadan: `norm_question` hash'i (ör. sha1[:16]) + DB indeksli sorgu, ya da
anahtar başına `set[str]` lazy yükleme. Veri zaten DB'de → migrasyon gerekmez.

### 3b. Depoyu birincil servis yolu yapmak

Bugünkü akış: `cache → LLM üret → filtre → (yedek/havuz) → top-up`
Hedef akış: `cache → DEPO (istenen sayının tamamı) → yalnız eksik kadar LLM`

**Kullanıcı kararı (2026-07-28, netleştirildi):**

> "İki öğretmen aynı kağıdı alabilir, sonuçta kullanıcı bazlı ayırıyoruz — aynı
> kullanıcı bir önceki ürettiğini görmesin yeter."
> "LLM 10 üretirken 18 üretiyorsa ve 8'i depolanıyor 10'u sadece gösteriliyorsa o da
> yanlış, komple 18'ini de depolamamız lazım."

→ Politika **sade**:

- Çapraz-kullanıcı tekrar **serbest**. Doluluk eşiği / karışım oranı kuralı **YOK** —
  depoda ne varsa verilir (reddedilen "3× doluluk" önerisi plana girmedi).
- Aynı kullanıcıya tekrar **yasak** → 3a'nın kalıcı görülmüş-seti (`exclude_norms`).
  Deponun TEK kısıtı bu.
- Seçim `used_count ASC` + rastgele karıştırma (hep aynı sıra ve hep aynı ilk 10 olmasın).

**3b-1. Teslim edilenler de depolanacak (bugün EKSİK — senaryonun kilidi bu).**
Bugün `agent.py:894` yalnız `spare_candidates = questions[question_count:]`'ı, yani
KIRPILAN artığı depoya yazıyor. Teslim edilen sorular depoya HİÇ girmiyor (yalnız
`GENERATION_HISTORY`'ye kullanıcı-bazlı "gördü" kaydı olarak yazılıyor).
→ Sonuç: X'e verilen 10 soru Y'ye asla servis edilemiyor; kullanıcının istediği
çapraz kullanım bugün fiilen çalışmıyor.

**Yapılacak:** üretilen ve **geçerli olan** soruların TAMAMI depoya yazılır
(10 teslim + artanlar). Elenenler (math_verifier / critic / yapısal doğrulayıcı
reddi) depoya **girmez** — depo çöp biriktirmemeli, aksi halde her serviste yeniden
elenip para yakar.

### 3c. Damga — depo isabetinin gizli maliyeti

**Bulgu:** `agent.py:1103` — depodan çekilen sorular her serviste
`_apply_post_filters`'tan geçiyor, yani **her depo isabeti yine bir critic çağrısı
ödüyor**. Tasarrufun tabanı bu yüzden ~0.1-0.2 TL'de kilitli.

**Yapılacak:** denetim sonucu soruya bir kez yazılır (`critic_pass`,
`critic_confidence`, `verified_at`, `verifier_model`); damgalı soru serviste **hiç
LLM görmez** → depo isabetinin marjinal maliyeti ~0.

Damga ne zaman vurulur (maliyet-optimal, iki yol birlikte):

1. **Bedava damga:** teslim edilen sorular üretim sırasında ZATEN critic'ten geçiyor →
   o verdict'i depoya yaz. Ek maliyet **sıfır**.
2. **Tembel damga:** hiç denetlenmemiş artanlar depoya damgasız girer; **ilk kez
   servis edilirken** denetlenir ve damgalanır. Sonraki servisler bedava.

Neden hepsini yazarken damgalamıyoruz: artanların bir kısmı hiç servis edilmeyebilir
→ peşin damga hiç kullanılmayacak soruya para öder. Tembel damga yalnız gerçekten
kullanılana öder.

### 3d. Şema (kalıcı kimlik + sorgulanabilir alanlar)

`spare_questions` bugün: `pool_key, norm_question, question_json, used_count, created_at`.
`pool_key` bir string ve ders/sınıf/tip **içine gömülü** → sorgulanamıyor.

Eklenecek: `question_id` (içerik hash'i, kalıcı kimlik), `subject`, `grade`,
`unit_id`, `kazanim_kod`, `question_type`, `difficulty`, `critic_pass`,
`quality_score`, `flagged_count`, `source` (`live-overshoot` | `batch-prewarm` |
`template`).

`question_id`'nin kalite değeri: quiz cevapları (`attempts.answers_json`) soru-bazlı
doğru/yanlış taşıyor. Kimlik olunca **bir sorunun sınıfta kaç kez yanlış
cevaplandığı** görülür → herkesin yanlış yaptığı soru = cevap anahtarı bozuk şüphesi
→ **soru kendini ihbar eder.** Veri bugün elimizde ama soruyla bağlanamıyor.

### 3e. Beklenen etki

Kağıt 2.75 → **~0.40 TL** (%70 depo isabeti varsayımıyla). En pahalı sorular
(geometri) en çok kazandırır. `COST_REDUCTION_PLAN §3.7`'deki riskli "mixed modu tek
çağrıda birleştirme" işi **gereksizleşir** (bucket'lar depodan beslenir) → o risk
alınmadan kazancı elde edilir.

### 3f. DEPO, CRITIC'İN KÖR NOKTALARINI KALICI HÂLE GETİRİR (sıralamayı değiştirir)

Faz 2 denetiminde ortaya çıkan, iki iş kolunu birbirine bağlayan sonuç:

Terazi ölçtü ki critic **kazanım uyumu ve zorluk uyumunda %0** yakalıyor (§2e).
Depo mimarisi ise şunu yapıyor: critic'ten geçen soruya `critic_pass=1` damgası
basılır, damgalı soru **bir daha ASLA denetlenmez** ve `used_count`'tan bağımsız
olarak trim'de **korunur** (§3c + trim politikası).

→ Yanlış kazanım etiketli ya da yanlış zorluk kalibrasyonlu bir soru:
1. critic'ten geçer (o eksende kör),
2. `critic_pass=1` damgalanır,
3. depoda kalıcı olur ve **birçok kullanıcıya** servis edilir.

**Depo öncesi** böyle bir soru tek kağıda zarar veriyordu; **depo sonrası** aynı
soru yüzlerce kağıda dağılıyor. Yani depo maliyeti düşürürken **mevcut kalite kör
noktalarını çoğaltıyor.**

Bu bir "depoyu yapmayalım" gerekçesi DEĞİL (kazanç çok büyük ve kör noktalar depo
olmadan da vardı); ama iki işin **önceliğini yükseltiyor**:

1. **Kazanım/zorluk körlüğünü kapatmak** (§2e-2) — artık "iyi olurdu" değil,
   deponun ön koşulu. Damga ne kadar güvenilirse depo o kadar güvenli.
2. **Havuz kalite döngüsü** (`quality_score`, `flagged_count` → eşik altını
   havuzdan çıkarma, `COST_REDUCTION_PLAN` Faz 3c) — damganın tek yönlü
   olmasının panzehiri. Bugün bir soru damgalandıktan sonra depodan çıkmasının
   TEK yolu trim'de ötelenmek. "Soruyu bildir" ucu + yanlış-oranı anomalisi
   (`attempts.answers_json` × `question_id`) bu döngüyü kapatır.

**Sıra revizyonu:** `Madde 2 (depo)` → **kazanım/zorluk körlüğü deneyi** →
`havuz kalite döngüsü` → `Madde 4 (kalıp)` → `Madde 3 (gece, park)`.
Kalıp ve gece işleri, damga güvenilir olmadan depoya daha çok stok basmak
anlamına gelir — yani hatayı ölçekler.

## 3g. KÖRLÜK DENEYİ — önce ölç, sonra doğru kapat

Kullanıcı kararı (2026-07-28): *"körlüğü kapatmak için ölçüm yapalım, ona göre
doğru şekilde kapatalım, yaptığımız iş işe yarasın."*

### 3g-0. Deneyi kurarken bulunan ÖN BULGU — yanlış şeyi ölçüyoruz

Critic'in gerçekten ne gördüğünü okudum (`critic.py::_evaluate_chunk`): kazanım
**metni** prompt'ta var (`kazanim_block` → `- KOD: metin`), her soru kendi
`kazanim_kod`'uyla etiketli. Yani bilgi eksikliği (en olası hipotez) **elendi**.

Ama daha önemlisi ortaya çıktı — **`agent.py:1758`**:

```python
kod = raw.kazanim_kod if raw.kazanim_kod in valid_kazanim_codes else fallback_kazanim
```

Model geçersiz bir kazanım kodu üretirse kod **sessizce `kazanimlar[0]` ile
değiştiriliyor.** İki sonucu var:

1. **Terazinin `kazanim_mismatch` mutasyonu ÜRETİMDE İMKÂNSIZ bir senaryoyu
   ölçüyor.** Mutasyon kodu *başka bir dersten* alıyor; üretimde böyle bir kod
   asla hayatta kalmaz, `_process_batch` onu yeniden yazar. Yani "%0 recall"
   gerçek riski değil, olamayacak bir kusuru ölçüyor.
2. **Gerçek risk bunun tam tersi ve onarım mekanizmasının KENDİSİ üretiyor:**
   içeriği kazanım A'ya ait olan bir soru, kodu geçersiz olduğu için
   `kazanimlar[0]` (= B) etiketiyle damgalanıyor. Kod artık "geçerli" olduğu için
   hiçbir kontrol takılmıyor. Bu, sessiz bir **yanlış etiketleme fabrikası**.

Yan etki (kapsam dışı ama kayda geçsin): `KazanimProgress`, ilerleme panosu ve
çalışma programı bu kodları okuyor → öğrencinin "kazanım bazlı eksiği" yanlış
kazanıma yazılıyor olabilir. Ve depo (§3f) bu etiketi kalıcı hâle getiriyor.

### 3g-1. Aşama 1 — Teşhis (~$0.05)

| # | İş | Neden |
|---|---|---|
| 1a | `kazanim_mismatch` + `difficulty_mismatch` mutasyonları için **HAM verdict dökümü** (`is_valid`, `confidence`, `issues`) | Üç ayrı teşhis: (i) critic "geçerli" diyor → gerçekten kör; (ii) "geçersiz" diyor ama `confidence < 0.75` → **kör olan critic değil, EŞİĞİMİZ**; (iii) başka bir şeyden şikâyet ediyor → yanlış atıf |
| 1b | `kazanim_mismatch`'i **gerçekçileştir**: kodu AYNI isteğin geçerli kazanım listesinden başka bir kodla değiştir | Üretimde mümkün olan tek senaryo bu; critic'i gerçek işe zorlar (kod-üyeliği değil, metin-içerik uyumu) |
| 1c | **Yeni kusur tipi `kazanim_silent_repair`**: içerik kazanım A'ya ait, etiket geçerli-ama-yanlış B | `agent.py:1758`'in ürettiği gerçek kusuru birebir taklit eder |
| 1d | Onarım yolunu **say**: `agent.py:1758` fallback'i kaç kez tetikledi → sayaç + `GenerationTrace` alanı (`kazanim_repaired_count`) | LLM harcaması YOK. Üretimde bu oran yüksekse yanlış etiketleme salgını var demektir — deneyin gerçek büyüklüğünü bu belirler |
| 1e | İki eksende örneklemi **5 → 15** mutasyona çıkar | 5 örnekle %80 ile %60'ı ayırt edilemez (§3.5 dersi: varyans) |

### 3g-2. Aşama 2 — A/B kolları (teşhisten SONRA, ona göre budanır)

| Kol | Ne | Ek maliyet |
|---|---|--:|
| A | kontrol: bugünkü (flash-lite, 4-görev tek `is_valid`, batch 10, eşik 0.75) | — |
| B | **eksen-bazlı eşik** (kazanım/zorluk verdict'i daha düşük confidence'ta kabul) | ~0 |
| C | **eksen-bazlı ŞEMA**: tek `is_valid` yerine `matematik_ok` / `kazanim_ok` / `zorluk_ok` ayrı boolean | ~0 (aynı çağrı) |
| D | ayrı, **tek amaçlı** kazanım+zorluk geçişi (küçük prompt: kök + kazanım metni + hedef zorluk) | +1 ucuz çağrı |
| E | model yükseltme: critic `flash-lite` → `2.5-flash` | ~4× critic (kağıdın küçük payı) |

**Hipotez (önceden yazılı):** C kazanır. Tek `is_valid` boolean'ı modeli 4 yargıyı
bire indirmeye zorluyor ve en somut/kontrol edilebilir eksen (aritmetik) diğerlerini
bastırıyor. Eksen ayrılırsa model her birine cevap vermek ZORUNDA kalır. C ayrıca
B'yi mümkün kılar (eksen-bazlı eşik ancak eksen-bazlı çıktıyla anlamlı).

### 3g-3. Karar eşikleri — ÖNCEDEN yazılı, sonradan esnetilmeyecek

Bir kol "kazandı" sayılmak için **dördünü birlikte** geçmeli:
1. `kazanim_mismatch` (gerçekçi hâli) + `kazanim_silent_repair` + `difficulty_mismatch`
   recall **≥ %80**, en az **3 iterasyon** ortalamasında (min değer ≥ %60).
2. Altın sette yanlış-alarm **ARTMAMALI** (≤ %3 — bugünkü seviye). Her şeyi
   "uyumsuz" diyen bir critic 1. maddeyi geçer ama burada elenir; bu madde o
   yüzden zorunlu.
3. Çalışan iki eksen (`wrong_answer_key`, `solution_contradicts_answer`)
   **%100 KALMALI**.
4. Critic maliyeti kontrole göre **≤ 1.3×**.

Hiçbir kol geçmezse: `agent.py:1758`'in sessiz onarımını **kaldır** — geçersiz kod
üreten soruyu fallback'le etiketlemek yerine ELE (top-up ile değiştir). Kalite
kararı burada critic'ten bağımsız ve deterministik olarak alınır.

## 4. MADDE 3 — Gece doldurma (PARK)

Kullanıcı: *"sonra detaylı konuşalım, unutma bu kısmı."*

Hatırlatma notu: Gemini Batch API asenkron ve **yarı fiyat**; kullanıcı beklemediği
için orada pahalı/kaliteli ayarlar kullanılabilir (güçlü model + yüksek thinking +
çift critic + göz denetimi). Detay `COST_REDUCTION_PLAN §Faz 3b`. Bu maddeye
geçmeden önce madde 2 bitmiş ve `usage_ledger` zenginleştirilmiş olmalı (hangi
kovaları önce dolduracağımızı veri söylesin, kör doldurma olmasın).

## 5. MADDE 4 — Soru kalıbı, yalnız 1-4 matematik, KARIŞIK

**Rolü değişti: bu bir maliyet hamlesi değil, kalite hamlesi.**

Gerekçe: `app/data/few_shot.py` EXAMPLES_BY_GRADE'de 1-7 için 259 örnek var ve
**hiçbirinde kaynak yok** → %100 sentetik. Model kendi ürettiğini kopyalıyor
(eko-odası, `docs/SORU_KALITESI_ANALIZI.md`). 1-4'te gerçek MEB sorusu bulunamadı
(EBA kazanım testleri 5. sınıftan başlıyor). Kalıp, yankıyı kesip **yazılmış**
(yankılanmamış) içerik koyar ve cevabı SymPy hesaplar → anahtar kanıtlanabilir doğru.

**Kullanıcı kısıtı — tam kalıp YASAK:** 1-4 kağıtlarında kalıp ve LLM üretimi
**karışık** servis edilir; kalıp oranı tavanlı (öneri: kağıdın ≤%50'si, config'den
ayarlanabilir `template_ratio_max`). Gerekçe: kalıp tek başına monotonlaştırır,
"arada farklı sorular" olmalı.

Kapsam dışı (net): yeni nesil, geometri, 5-8, sözel dersler.

Para kazancı küçük (1-4 zaten en ucuz kağıt: ucuz model + thinking kapalı).
Sıralamada madde 2'den sonra gelir.

## 6. Sıra ve beklenen tablo

| Adım | Kağıt maliyeti | Kalite |
|---|--:|---|
| Bugün (ölçülmüş) | 2.75 TL | **ölçülemiyor** |
| **1. Terazi** | 2.75 TL | **ölçülebilir olur** (critic'in karnesi çıkar) |
| **2. Depo** (3a→3c→3d→3b) | **~0.40 TL** | aynı + bozuk anahtar ihbarı + kullanıcı tekrarı biter |
| **4. Kalıp** (1-4, karışık) | ~0.38 TL | 1-4'te eko-odası kırılır |
| 3. Gece (park) | ~0.40 TL | **yükselir** |
| 5. Geometri | dokunulmuyor | — |

Abonelik etkisi (Pro ₺199/50 kağıt, %15 store kesintisi): kotasını dolduran abonede
brüt marj **%19 → ~%88** (madde 2 sonrası).

## 7. Ölçüm disiplini (her maddede uygulanır)

- Madde bitince **hem** `cost_probe` (TL/kağıt) **hem** `quality_bench` (kusur matrisi)
  koşulur; ikisi birlikte raporlanmadan "bitti" denmez.
- Koşu-arası varyans **±%15** (§3.5 dersi) → tek koşuyla %8'lik fark iddia edilmez.
- Kalite göstergesi olarak `critic_pass_rate` **artık tek başına kullanılmaz**;
  yerine `quality_bench` matrisi + yanlış-alarm oranı.

## 8. Model rolleri (kullanıcı kararı)

Planlama/mimari/denetim **Opus 5**; geliştirme **Sonnet 5**; iş bitince **Opus 5
denetler**. `.claude/CLAUDE.md`'ye yazıldı.
