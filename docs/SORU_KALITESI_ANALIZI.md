# Soru Kalitesi & Yeni Nesil Soru — Analiz ve Yol Haritası

> Durum: Analiz tamamlandı, geliştirme başlıyor · Tarih: 2026-07-02
> Kapsam: 1-8. sınıf matematik soru üretim hattının kalite ve "yeni nesil" karakteri.
> İlgili planlar: [[GRADE8_LGS_PLAN.md]] (canlı), [[MULTIGRADE_QUESTION_INGEST_PLAN.md]] (bekliyor),
> [[VISUAL_MULTIGRADE_INGEST_REPORT.md]] (bekliyor), [[PROJECT_PLAN.md]] (master).

---

## 0. Tek cümlelik teşhis

Sorun altyapı/kabuk **değil** — kabuk (16 soru tipi, SVG/grafik/LaTeX, critic, dedup, RAG) zaten var.
Sorun **içeriğin kaynağı** (1-7 few-shot'ları %100 sentetik = eko-odası) ve **"yeni nesil"i yanlış
eksende tanımlamak** (zorluk = daha çok aritmetik, oysa yeni nesil = daha çok bağlam + yorumlama).

---

## 1. Mevcut sistem haritası (referans)

### Üretim hattı
- API giriş: `app/routers/worksheets.py` → `_build_worksheet()` → `GeminiAgent.generate()`.
- Çekirdek motor: `app/services/agent.py:299` — seed/temperature jitter → kazanım seçimi →
  over-generation (1.3×) → tip dağılımı → cache → few-shot toplama → textbook context →
  prompt inşası → LLM → batch işleme → dedup → math verifier → critic → top-up.
- LLM: `gemini-2.5-flash` (ana), fallback `flash-lite`/`pro`, critic `flash-lite`. Anthropic fallback kapalı.
- Prompt'lar: `app/prompts/templates.py` (system `:5-74`, user `:221`, retry `:179`, few-shot format `:105`).
- Critic: `app/services/critic.py:37` (LLM judge, temp 0.1).
- Çeşitlilik/dağıtım: `app/services/diversity.py` (`distribute_question_types :99`,
  `DIFFICULTY_DISTRIBUTIONS :14`, `TOPIC_VISUAL_BIAS :70`, dedup).
- Few-shot seçimi: `app/services/examples.py:71` (greedy MMR).
- RAG: `app/services/retriever.py` (ChromaDB, dense+BM25 hibrit, katmanlı fallback).
- Math verifier: `app/services/math_verifier.py` (SymPy, deterministik).
- Görsel: `app/services/svg_utils.py` (inline SVG parse/validate, `{{chart:...}}` → deterministik SVG).

### Soru tipleri (16, `app/models/enums.py:10`)
- Metin: `islem, sozel_problem, kavram_sorusu, akil_yurutme, modelleme, gunluk_hayat`
- Görsel/yapısal: `salt_islem, tablo_sorusu, gorsel_geometri, grafik_okuma, oruntu_sekil`
- Format: `coktan_secmeli, bosluk_doldurma, dogru_yanlis, eslestirme, siralama`

### Müfredat
- `app/data/curriculum.py:58` — `CURRICULUM[sınıf][topic_id]`, 1-8. sınıf, her kazanımda `difficulty_hints`.

### Few-shot / soru havuzu kaynakları
- Elle: `app/data/few_shot/grade_{1-7}.py` (kazanım kodu → örnek listesi). 8. sınıf yok (RAG/LGS'ten gelir).
- Üretilmiş/çıkarılmış (`knowledge_base/processed/`): `synthetic_examples.json` (1.6MB),
  `lgs_examples.json` (457 gerçek LGS sorusu, hepsi 8. sınıf), `geometry_svg_examples.json` (39),
  `salt_islem_latex_examples.json` (40), `chart_pattern_svg_examples.json` (30), `visual_examples.json`,
  `format_examples.json`, `questions_grade{5,6,7}.json` (+ validated/rejected).
- Gerçek vs sentetik ayrımı: `source` alanı (`lgs/...` vs `synthetic/...`).

### Kalite hendekleri (canlı)
String dedup → semantic dedup (embedding) → math verifier (SymPy) → critic (LLM judge) → post-filter top-up.

---

## 2. "Yeni nesil soru" gerçekte nedir (yanılgı düzeltmesi)

Yaygın yanılgı: "yeni nesil = görsel soru". **Yanlış.** Yeni nesil (2018 MEB reformu, PISA/TIMSS tarzı)
bir **ayaklı sehpadır**; görsel yalnızca bir ayak:

| Ayak | Ne demek | Sistemdeki durum |
|---|---|---|
| **Bağlam (context)** | Uzun paragraf, gerçek senaryo, hikâye içinde matematik | 🔴 En zayıf |
| **Beceri/muhakeme** | Bilgi hatırlama değil, yorumlama + çok adım | 🟡 Orta |
| **Görsel/veri okuma** | Grafik, tablo, infografik, bileşik şekil | 🟡 Var ama sığ |
| **Anlamlı çeldirici** | Her yanlış şık belirli bir yanılgıyı yakalar | 🔴 Yok |

**Kritik içgörü:** Ayırt edici özellik çoğu zaman görsel değil, **uzun bağlam + yorumlama**dır.
"40'ın %25'i kaç?" ile "Ayşe'nin 40 TL harçlığının %25'ini... [3 paragraf senaryo]" aynı aritmetiği
içerir; fark **okuma/çıkarım yükünde.**

---

## 3. Üç kök neden

### KN-1: 1-7 few-shot'ları %100 sentetik ("eko-odası")
Fine-tuning yok; "öğretme" RAG few-shot ile oluyor. 1-7 örnekleri Gemini'nin kendi ürettiği örnekler →
model kendi tarzını çoğaltıyor. 8. sınıf kaliteli çünkü few-shot'ı **457 gerçek LGS sorusu.**
→ Kaliteyi artırmanın **#1 kaldıracı**; plan hazır (`MULTIGRADE_QUESTION_INGEST_PLAN.md`), inşa bekliyor.

### KN-2: Zorluk ekseni "yeni nesil"i ölçmüyor
`templates.py` kalibrasyonu: Kolay = "bağlam **yalın**", Orta = "**kısa** bağlam", Zor = "çok adım + büyük sayı".
Yani **"zor" = daha çetrefil aritmetik**, yeni nesil ise = **daha zengin bağlam + yorumlama.** Sistem bağlamı
bilinçli KISA tutuyor — yeni nesilin tam tersi. Ayrıca `diversity.py`'de kolay seviyede `islem` ağırlığı 0.30
→ varsayılan üretim hesap-ağırlıklı. **Sonuç:** "zorluğu artır" demek daha yeni nesil değil, daha zor aritmetik
getiriyor. Yeni nesil, zorluktan **bağımsız yeni bir eksen** olmalı.

### KN-3: Çeldiriciler mühendislik ürünü değil
Yeni nesil MCQ'nun kalbi çeldiricilerdir (her yanlış şık = belirli bir kavram yanılgısı). Pipeline'da çeldirici
için özel talimat/kontrol yok → model rastgele "yakın sayı" üretiyor. Sorular "test kitabı" değil "alıştırma" gibi.

---

## 4. Öncelikli kaldıraçlar (etki sırasına göre)

### 🥇 K1 — Gerçek soru havuzunu inşa et (1-7), 5. sınıf pilotuyla
- Kalite ≫ nicelik: kazanım başına ~5 "altın çıpa" (insan onaylı, gerçek, kolay/orta/zor + format çeşidi)
  → sentetik eko-odasını *değiştirir*.
- Kaynak: 7. sınıf çıkmış soru PDF'leri, **MEB örnek soru kitapçıkları (ÖDSGM)** (birebir yeni nesil), LGS.
- `scripts/extract_lgs_questions.py`'yi `--grade N` ile genelleştir (plan bunu diyor).
- Etki: algılanan kaliteyi en çok yükselten hamle.

### 🥈 K2 — "Yeni nesil / senaryo" modunu birinci sınıf eksen yap
- Bağımsız `yeni_nesil` bayrağı / üretim profili. Açıkken:
  - Tip dağılımı `sozel_problem + gunluk_hayat + modelleme + grafik_okuma + tablo_sorusu`'ya kayar
    (`diversity.py`'de yeni `DIFFICULTY_DISTRIBUTIONS` profili).
  - Prompt: "2-3 paragraf gerçek yaşam senaryosu; veriyi metin/görselden ayıkla; en az bir gereksiz bilgi
    (çeldirici veri); çok adımlı çözüm."
- Zorluk ile yeni nesli ayırır → kullanıcı ikisini ayrı isteyebilir.
- Mimariye (profil + prompt) az dokunuşla oturur, en yüksek "hissedilir yenilik".

### 🥉 K3 — Görseli derinleştir (çoğaltma değil)
- Görsel few-shot'lar da kısmen sentetik (`generate_geometry_svg.py`) → görselde de eko-odası.
- Görseller çoğunlukla tek-şekil geometri. Yeni nesil görsel = çok-veri grafik, bağlamlı tablo, infografik, bileşik figür.
- Gerçek görsel soruları çıkar (Eksen A), `retriever.py`'de sentetik SVG'ye karşı **kaynak-önceliği** ver.
- Grafik repertuarını genişlet (çift seri sütun, çizgi grafik, karşılaştırma).

### K4 — Çeldirici mühendisliği
- `coktan_secmeli` prompt'una: "her çeldirici belirli bir hatadan doğsun; çıktıda `distractor_rationale`
  ile hangi yanılgıyı temsil ettiğini yaz." Critic'e "çeldiriciler ayırt edici mi?" kontrolü ekle.
- Eğitsel değer + otomatik puanlama (öğrenme platformu) için altın.

### K5 — "Yeni nesil skoru"nu ölç
- `knowledge_base/eval/` şu an: çeşitlilik + critic pass + kazanım uyumu ölçüyor; "ne kadar yeni nesil"i ölçmüyor.
- Ekle: ortalama bağlam uzunluğu, okuma düzeyi, çözüm adım sayısı, görsel oranı, çeldirici kalitesi.

---

## 5. Öncelik özeti

| Bulgu | Aksiyon | Öncelik |
|---|---|---|
| 1-7 few-shot = sentetik eko-odası | Gerçek soru ingest, 5. sınıf pilot | 🔴 Şimdi |
| Zorluk ≠ yeni nesil | Bağımsız "senaryo/yeni nesil" profili + prompt | 🔴 Şimdi |
| Görselde de eko-odası, sığ | Gerçek görsel çıkarımı + grafik çeşidi | 🟡 Sonra |
| Çeldiriciler rastgele | Yanılgı-temelli çeldirici + critic kontrolü | 🟡 Sonra |
| "Yeni nesil"i ölçmüyoruz | Eval'e yeni nesil metrikleri | 🟢 Paralel |

**En yüksek getirili ikili:** K1 (gerçek havuz) + K2 (yeni nesil profili). K1 içeriğin karakterini gerçeğe çeker;
K2 o karakteri "uzun bağlam + yorumlama" eksenine oturtur — asıl "yeni nesil" hissi oradan gelir.

---

## 6. Sıradaki adımlar (bu oturum)

1. [ ] Paralel session'da eklenen 5-6-7 yeni sorularını bul, kalitesini değerlendir (gerçekten işe yarar mı?).
2. [ ] Değerlendirmeye göre: ya gerçek havuz ingest'ini (K1) ya da yeni nesil profilini (K2) kodlamaya başla.
3. [ ] Küçük, test edilebilir PR'larla ilerle; her adımı eval ile doğrula.

---

## 7. Değerlendirme: 5-6-7 gerçek soru havuzu (PR #64-#71)

**Bağlam:** Paralel oturumda K1 (gerçek soru havuzu ingest) fiilen hayata geçirilmiş — PR #64-#71,
"sıfır Gemini / sıfır vision maliyeti" ile elle çözülmüş/çıkarılmış GERÇEK sorular.
Dosyalar: `knowledge_base/processed/questions_grade{5,6,7}.json` (+ grade5 için `_validated`/`_rejected`).

### Hüküm: İçerik gerçek ve değerli ✅ — ama veri hijyeni sorunları etkisini köreltiyor 🟡

**Kaynaklar gerçek ve kaliteli** (örnekle doğrulandı): 5. sınıf soru bankası/yaprak test,
6-7. sınıf SZM fasikülleri + "MEB ÇIKMIŞ SORULAR". Okunan örnekler (G7 çember/merkez açı I-II-III
çoktan seçmeli, G6 kesir bölme, G5 basamak değeri) doğru ve yeni nesil tarzında. Bu tam istediğimiz kaldıraç.

**Havuz büyüklüğü:** G5 = 1325 ham → 888 validated / 437 rejected (%33 red — doğrulama iş görüyor).
G6 = 151, G7 = 132.

### Tespit edilen sorunlar (öncelik sırasıyla)

| # | Sorun | Kanıt | Etki | Düzeltme |
|---|---|---|---|---|
| **S1** | **G6 & G7 doğrulanmamış ingest ediliyor** | `_validated` dosyaları yok → `ingest_to_chroma.py:152` ham dosyaya düşüp uyarı basıyor | Çelişkili/hatalı sorular canlı few-shot'a sızıyor | `validate_questions.py` grade 6 ve 7 için çalıştır |
| **S2** | **G5 validated'ın %62'si etiketsiz** | validated 888 sorunun 547'sinde `kazanim_kod` boş; ham G5'te topic_id %100 boş | Etiketsiz sorular RAG'de hedefli (grade+kazanım) yolla çekilemez → "ölü ağırlık" | `tag_questions_by_keyword.py` ile kazanım etiketle (sıfır LLM maliyeti) |
| **S3** | **Tip enum tutarsızlığı** | G6/G7'de `multiple_choice` (34+36) ve `open_ended` (7) var; `_QTYPE_INGEST_MAP` (`ingest:137`) bunları eşlemiyor → enum dışı tiple Chroma'ya giriyor | Tip-filtreli retrieval/çeşitlilik bu ~113 soruyu tanımıyor | Haritaya ekle: `multiple_choice→coktan_secmeli`, `open_ended→sozel_problem` |
| **S4** | **Çelişkili çözümler doğrulamadan sızıyor** | G5 validated'ta 45 soruda "cevap anahtarı X dediği için..." kalıbı (çözüm ≠ cevap). Örn ham #700: çözüm 32 hesaplıyor ama cevap 28 (bu #700 red edilmiş ama benzerleri geçmiş) | Model tutarsız Q/A üretmeyi öğrenir; otomatik puanlama bozulur | Ucuz regex ön-eleme (çelişki kalıbı) + critic'e tutarlılık kontrolü |
| **S5** | **Aşırı büyük sorular** | En uzun 3 soru 12-14 bin karakter (tek dev SVG); ikisi validated=True | Embedding şişer, few-shot prompt bütçesini patlatır | Ingest'te uzunluk/SVG boyut tavanı + fazlasını incelemeye ayır |

### Kök neden özeti
Doğrulama pipeline'ı (`validate_questions.py`) yalnız **grade 5'e** uygulanmış; matematik-dışı (görsel/örüntü)
sorularda **cevap-çözüm tutarlılığını** yakalamıyor; ve **etiketleme adımı** çoğu G5 sorusunda atlanmış.
Yani içerik altın, ama ingest hattının hijyen kapıları eksik kapatılmış.

### Yapılanlar (bu oturum, 2026-07-02)
1. [x] **S3 — Tip normalizasyonu** (`ingest_to_chroma.py:_QTYPE_INGEST_MAP` + `validate_questions.py:_TYPE_MAP`):
   `multiple_choice→coktan_secmeli`, `open_ended→sozel_problem` eklendi. Sıfır maliyet.
2. [x] **S4+S5 — Sezgisel ön-eleme** (`validate_questions.py:_heuristic_reject`): çözüm-cevap çelişkisi
   (regex) + aşırı büyük soru (>6000 kar) + boş cevap/soru redderi. Sıfır maliyet, LLM'siz.
3. [x] **Zero-cost re-validation** (`validate_questions.py:--reuse-rejects`): önceki critic redlerini
   taşır → G5'te 437 critic emeği korunarak yeni heuristic uygulandı (critic'i yeniden çağırmadan).
4. [x] **G5/G6/G7 doğrulandı** (`--no-critic`):
   - G5: 1325 → **865 kabul** (437 critic-prev + 71 heuristic red; sızmış 23 çelişki/dev soru ayıklandı).
   - G6: 151 → 151, G7: 132 → 132 (elle çözülmüş, yüksek güven; heuristic temiz). Artık `_validated` var (S1 ✅).
5. [x] **S2 — Kısmi etiketleme** (`tag_questions_by_keyword.py` grade-5 kuralları genişletildi):
   G5'te +34 kazanım atandı. **Sınır:** keyword yöntemi bu içerikte düşük isabetli (soru metinleri
   "sonucu kaçtır" gibi konu-kelimesiz) → 795 hâlâ kodsuz. Bunlar grade-seviyesinde ingest olur (kaybolmaz),
   ama kazanım-hedefli çekilemez.

### Kararlar (onaylandı + uygulandı)
- **D3 ✅ — Müfredat boşluğu kapatıldı:** `CURRICULUM[5]` KESIRLER topic'ine ondalık kazanımları eklendi:
  `M.5.2.6` (ondalık gösterim tanır/okur/yazar/çözümler + basamak adları) ve `M.5.2.7` (karşılaştırır,
  sıralar, toplama-çıkarma), difficulty_hints ile. (`app/data/curriculum.py`)
- **D2 ✅ — Kalan sorular Claude ile etiketlendi (Gemini'siz):** `tag_questions_by_keyword.py`'a regex/notasyon
  desteği eklendi (ondalık `\d+,\d+`, derece `°`, `[×÷]`, `%`) + grade-5 kuralları kapsamlı yeniden yazıldı.
  Isabet-öncelikli: jenerik "toplamı/farkı" çıkarıldı (geometri/basamak sorularını yanlış yakalıyordu),
  Türkçe yumuşama (bölük→bölüğ) eklendi, geometri terimleri (çokgen/doğrusal/kesişen) genişletildi.
  Sonuç: G5'te **+201 kazanım etiketi** (34 + 167), spot-check ile isabet doğrulandı. Kalan ~628 gerçekten
  belirsiz (bağlamsız sözel / salt görsel) → grade-seviyesinde ingest (kaybolmaz, sadece kazanım-hedefsiz).
- **D1 ✅ — Chroma rebuild:** `--stable_id` kazanım+tip içerdiği için değişen sorular yeni id alır → artımlı
  ingest mükerrer yaratır. Bu yüzden `ingest_to_chroma.py --rebuild` (koleksiyon sıfırdan) çalıştırıldı.
  Toplam 4115 örnek yeniden embed edildi (Gemini embedding, ~$0.25). Loader'lar `_validated` dosyalarını
  okuyor: G5=865, G6=151, G7=132.

### Uçtan uca doğrulama (2026-07-02)
Rebuild sonrası Chroma'da **4103 kayıt**. Retriever testi:
- `M.5.2.6` (ondalık, YENİ kazanım): 3 gerçek ondalık sorusu döndü (`questions/grade5/13-ondalik-gosterim`)
  → müfredat + etiketleme + rebuild birlikte çalışıyor.
- `M.6.2.1` (G6 kesir): SZM grade-6 gerçek sorusu döndü → validated havuz canlı.
- `M.5.3.5` (geometri): sonuç döndü (gerçek + sentetik harman).

### Faz A ÖZET (tamamlandı ✅)
S1 (G6/G7 doğrulandı), S2 (+201 etiket, kalan grade-seviyesi), S3 (tip normalizasyonu),
S4/S5 (çelişki+boyut heuristic), D1 (rebuild), D2 (Claude etiketleme), D3 (ondalık müfredat). Hepsi sıfır-Gemini
(sadece ingest embedding ~$0.25). Değişen: `scripts/{validate_questions,tag_questions_by_keyword,ingest_to_chroma}.py`,
`app/data/curriculum.py`, `knowledge_base/processed/questions_grade{5,6,7}*.json`, `knowledge_base/chroma_db/*`.

## 8. Faz B — K2 "Yeni Nesil / Senaryo" profili (tamamlandı ✅, 2026-07-02)

Zorluktan **bağımsız** bir `yeni_nesil` ekseni eklendi. Aktifken uzun gerçek yaşam senaryosu,
veri ayıklama, çeldirici veri, çok adımlı çözüm üretir.

- `diversity.py`: `YENI_NESIL_DISTRIBUTION` (gunluk_hayat/sozel/akil_yurutme/modelleme/coktan_secmeli
  + grafik/tablo ağırlıklı; salt_islem hariç) + `distribute_question_types(..., yeni_nesil=)`.
- `templates.py`: `_YENI_NESIL_BLOCK` senaryo talimatı + `build_user_prompt(..., yeni_nesil=)`. Retry
  prompt `original_user_prompt`'u kapsadığı için bloğu otomatik miras alır.
- `agent.py`: `generate(..., yeni_nesil=)`; yeni nesil modda cache lookup+write ATLANIR (normal havuzla
  karışmasın; cache anahtarı yeni_nesil taşımıyor).
- `schemas.py`: `GenerateWorksheetRequest.yeni_nesil: bool`. `worksheets.py`: `_gen` + `_gen_bucket`'a geçirildi.

**Uçtan uca doğrulama (gerçek üretim):** grade 5, ondalık `M.5.2.7`, yeni_nesil=True →
① "Elif 50 TL ile kırtasiye (18,75 + 24,90...)" — çeldirici veri (almadığı silgi/kalem ucu) + 2 adım,
② atletizm ondalık sıralama+fark — çeldirici (rekor 4,5 m). İkisi de senaryo tabanlı, çok adımlı,
YENİ eklenen ondalık kazanımını hedefliyor → Faz A + Faz B birlikte çalışıyor.

## 9. Faz C — Gizli kalite kaldıracı + harman modu (tamamlandı ✅, 2026-07-02)

Karar: yeni nesil ÖNYÜZDE görünmez (toggle yok). Kullanıcı sadece kalite farkını hisseder.
Karar sunucuda, premium yetkiye göre verilir; client bir bayrak gönderemez.

- **Entitlement seam** (`app/services/entitlements.py`): `is_premium(tenant_id)` + `wants_yeni_nesil(tenant_id)`.
  Gerçek billing yok → bugün `config.py` allowlist/flag'lerinden okunur, ileride Clerk/billing'e bağlanır.
  `config.py`: `premium_yeni_nesil` (özellik anahtarı), `premium_all`, `premium_tenant_ids` (+`premium_tenant_id_set`).
- **Client'tan kaldırıldı:** `GenerateWorksheetRequest.yeni_nesil` silindi → ücretsiz kullanıcı istekle bypass edemez.
  `worksheets.py`: `_yeni_nesil = wants_yeni_nesil(req.tenant_id)` sunucuda hesaplanıp `_gen`/`_gen_bucket`'a geçer.
- **Harman (blend) modu:** Kullanıcı isteğiyle yeni nesil artık %100 senaryo DEĞİL, KARIŞIK:
  `diversity.py` yeni nesil dağılımı normal ile 50/50 harmanlanır (hem hızlı pratik islem/salt_islem hem
  senaryo bir arada; salt_islem korunur). `templates._YENI_NESIL_BLOCK` "harman" diline çevrildi
  (senaryo tiplerini yeni nesil yaz, pratik tiplerini kısa bırak).
- **Şimdilik herkes:** `premium_all=True` → ücretsiz dahil herkes harman yeni nesil alıyor. Abonelik/billing
  canlı olunca `premium_all=False` + `premium_tenant_ids` doldur → ücretsiz=normal, premium=yeni nesil FARKI devreye girer.

**Doğrulandı (gerçek üretim, anonim, grade5 kesirler 6 soru):** #1,2,6 hızlı kesir pratiği (salt_islem),
#3 fırıncı senaryosu, #4 koşu yarışı (ondalık), #5 manav çok-adımlı → gerçek harman.

## 10. Model kararı — yeni nesil yolu için gemini-3.5-flash (2026-07-02)

**Test bulgusu:** Şekilli+bağlamsal üretim — veri işleme mükemmel (5/5, chart direktifi deterministik),
geometri zayıftı (model SVG'yi elle çizmekte zorlanıyor). Bu yapısal-çıktı (kod) meselesi → güçlü model çözer.

**Ampirik A/B (geometri, 6 soru, yeni_nesil):**
| Model | Süre | Şekilli | Fiyat (girdi/çıktı /1M) |
|---|---|---|---|
| gemini-2.5-flash (eski gen) | ~30s | 1/6 | $0.30/$2.50 |
| gemini-2.5-pro | 63s | 2/6 | $1.25/$10 |
| **gemini-3.5-flash** ✅ | 48s | 2/6 | $1.50/$9 |

gemini-3.5-flash = Pro seviyesi kalite/şekilli, Pro'dan hızlı, kodlama-optimize (SVG güvenilirliği).
Gemini 3.x GA değil ama `-flash`/`-pro` erişilebilir; `gemini-3-flash` (preview-siz) yok.

**Karar:** Yeni nesil (kalite) yolu → `gemini-3.5-flash`; normal yol → `gemini-2.5-flash` (hız/maliyet).
- `config.py`: `gemini_model_yeni_nesil = "gemini-3.5-flash"`.
- `worksheets.py`: `_agent_yeni_nesil()` + `_gen_bucket` model seçimi `_yeni_nesil`'e bağlı.
- Fiyat: worksheet başına ~$0.02-0.05 (2.5-flash'ın ~4-5 katı ama mutlak değer kuruşlar; değere göre
  fiyatlama + ~%85 marj ile ihmal edilebilir). ŞİMDİLİK herkes yeni nesil (premium_all=True) → herkes
  3.5-flash. Billing ayrışınca ücretsiz=2.5-flash, premium=3.5-flash otomatik.
- Uçtan uca doğrulandı: router yolu gemini-3.5-flash kullanıyor, geometri şekilli+bağlamsal (nişangah/havuz SVG).

## 11. Faz E — Görselli soru havuzu: Claude vision + 7 paralel subagent (2026-07-03)

Kullanıcı isteği: şekilli sorular sadece geometride değil TÜM konularda üretilebilsin. Çözüm:
gerçek çıkmış/LGS örnek PDF'lerindeki görselli soruları **Claude'un kendi görme yetenegiyle** (sıfır Gemini)
çıkarıp şekli elle geçerli inline SVG'ye çevirmek → few-shot havuzuna gerçek görsel örnekler.

**Hat (tekrarlanabilir):** pymupdf PDF→PNG → Claude okur → görselli soru çıkarır + şekli SVG/`{{chart}}`/Markdown
→ cevabı çözer → belirsiz figürü ATLAR (kalite barı) → `is_valid_svg` → `add_manual_questions.py`.

**7 paralel subagent** (general-purpose, her biri sıfır Gemini): g8 lgsornek1/2/3, g6 geometri+karışık, g5 geometri+karışık.
**Sonuç: 111 gerçek görselli soru** (hepsi şema+SVG doğrulandı, cevaplar elle çözüldü, belirsizler atlandı):
- Grade 8: 25 (lgsornek1-3) — asal, üslü, karekök, cebir, olasılık, grafik, silindir, benzerlik.
- Grade 6: 43 (açılar 29 + karışık 14) — doğru/dörtgen/üçgen açı, çarpanlar, bölünebilme, ondalık, cebir, veri.
- Grade 5: 43 (geometri 18 + karışık 25) — üçgen/dörtgen/açı, yüzde modelleri, ondalık, kesir modeli, grafik.
- question_type dağılımı: gorsel_geometri çoğunluk + grafik_okuma + tablo_sorusu + oruntu_sekil (tüm görsel tipler).

**Grade-8 topic fix:** `_load_lgs` artık kazanımdan topic_id türetiyor (188 mevcut LGS SVG sorusu + 25 yeni
topic-hedefli retrieval'da). `ingest_to_chroma._QUESTIONS_GRADES`'e 8 eklendi (questions_grade8 artık ingest ediliyor).

**Doğrulama:** grade5=906 (43 yeni, 460 critic emeği korundu), grade6=194, grade8=25, grade7=140. Chroma --rebuild.

### Sıradaki (Faz D — opsiyonel)
- [ ] Abonelik/billing entegrasyonu (Clerk publicMetadata → `entitlements.is_premium`), sonra `premium_all=False`.
- [ ] K5: eval'e "yeni nesil skoru" (bağlam uzunluğu, adım sayısı, görsel oranı, çeldirici kalitesi).
- [ ] K4: yanılgı-temelli çeldirici (`coktan_secmeli` prompt + `distractor_rationale` + critic kontrolü).

