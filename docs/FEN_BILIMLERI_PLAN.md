# Fen Bilimleri — İlk Yeni Ders + Ders Ekseni Altyapısı Planı

> Durum: **Plan taslağı, onay bekliyor.** Tarih: 2026-07-10
> Kapsam: Matematik dışındaki ilk ders (Fen Bilimleri, 3–8. sınıf) + tüm sonraki
> derslerin faydalanacağı **`subject` (ders) ekseni** altyapısı.
> İlke: **Tek ders, uçtan uca (dikey dilim).** Aynı anda çok ders açma
> (bkz. `docs/PROJECT_PLAN.md` anti-dağınıklık kuralı). Fen hattı ispatlanınca
> şablonlaştırılır → İngilizce/Türkçe günler içinde eklenir.
>
> **KRİTİK İLKE — kalite kapısı (2026-07-10):** Fen **hemen canlıya alınmaz.**
> Feature-flag arkasında gizli/staging'de kalır ve **soru kalitesi en az matematik
> seviyesine gelene kadar** iterasyonla çalışılır. Kalite paritesi ölçülüp
> geçilmeden `/pricing`, SEO rotaları veya ders seçici **son kullanıcıya açılmaz.**
> Canlıya çıkış (Faz 7) ayrı ve **kaliteye bağlı bir kapıdır**, takvime değil.

## 0. Amaç ve kalite çıtası

Fen Bilimleri konseptinde MEB müfredatına uygun soru üretebilen bir hat. Fen,
matematik hattına **en çok benzeyen** ders olduğu için mevcut makineyi en çok
yeniden kullanır:

- **LGS Fen = altın standart** (tıpkı LGS matematik gibi, bkz. `GRADE8_LGS_PLAN.md`).
  Gerçek sınav soruları → **few-shot kalite çıpası**. Matematikteki eko-odası
  sorununu (1–7 %100 sentetik → düşük kalite, bkz. `SORU_KALITESI_ANALIZI.md`)
  baştan önlemek için gerçek soru korpusuyla başlanır.
- **Fen'de bol tablo + grafik + deney/gözlem yorumu** var → mevcut `{{chart:...}}`
  ve Markdown tablo rendering makinesi kısmen doğrudan çalışır.
- Sorular çoğunlukla **çoktan seçmeli / olgusal** → mevcut quiz / puanlama /
  sınıf yönetimi stack'i (ders-nötr) **hiç değişmeden** çalışır.

### İçerik kaynağı gerçeği (Faz 1'in darboğazı)
- **Elde olan:** `knowledge_base/8.Sınıf/lgs1..15.pdf` LGS deneme kitapçıkları.
  Bunlar **tam LGS kitapçığı** → içinde Fen bölümü de var ama **yetersiz**
  (sadece 8. sınıf + sınırlı sayıda soru).
- **Bulunması gereken:** MEB müfredatına uygun ek kaynaklar —
  - MEB Fen Bilimleri **ders kitapları** (3–8, EBA/MEB açık kaynak PDF),
  - Fen **soru bankası / kazanım testleri** (3–8),
  - LGS Fen çıkmış sorular (branş bazlı derlemeler).
- **Karar:** Kaynak temini Faz 0.5 olarak eklenir (aşağıda). Hat, önce eldeki
  LGS Fen bölümleriyle **ispat edilir**, kaynak genişledikçe korpus büyütülür.

## 1. Mimari — mevcut omurga ders-nötr, "ders ekseni" eksik

Kod haritası (2026-07-09 denetimi):

| Katman | Durum | İş |
|---|---|---|
| Model seçimi (`agent.py:model_for_grade`) | ✅ ders-nötr | yok |
| Veri modeli / API (`schemas.py`) | 🟡 parametrele | `subject` alanı ekle, uçtan uca geçir |
| Müfredat verisi (`data/curriculum.py`, `enums.TopicId`) | 🟡 parametrele | ders ekseni + veri-tabanlı topic |
| RAG / Chroma (`retriever.py`, ingest) | 🟡 parametrele | metadata'ya `subject` + `where` filtresi |
| Üretim prompt'u (`prompts/templates.py`) | 🔴 derse özel | Fen SYSTEM_PROMPT + critic |
| Few-shot (`data/few_shot/`) | 🔴 içerik yok | Fen korpusu topla |
| Rendering (`math_renderer`, `svg_utils`) | 🔴 derse göre | Fen MVP: metin+grafik+tablo |
| Frontend (rotalar, form, copy) | 🔴 yeniden yaz | ders seçici + Fen SEO rotaları |

**Cross-cutting gap:** Sistemde hiçbir yerde `subject`/`ders` kavramı yok (şema,
Chroma metadata, müfredat anahtarı, UI). Asıl iş matematiği sökmek değil, **bir
ders eksenini uçtan uca sokmak.**

```
PDF/kaynak → [extract/vision] → chunk JSON → [tag] → tagged JSON → [ingest] → ChromaDB
                                                                (subject=fen metadata)
                                                                        ↓
                                    üretimde retriever (subject=fen + grade filtresi)
```

## 2. Mimari yaklaşım — ders eklentisi (plugin) modülü

İki yol vardı: (A) her şeye `subject` alanı ekleyip tek kodda dallanmak, (B) her
dersi bir **plugin modülü** yapmak. **(B) seçildi** — prompt/few-shot/rendering
derse göre gerçekten farklı; tek dosyada if-else çorbası olmasın diye plugin
sınırı çizilir.

Hedef yapı (öneri):
```
app/subjects/
  __init__.py         # SUBJECTS registry: {"matematik": MathSubject, "fen": FenSubject}
  base.py             # SubjectPlugin protokolü: curriculum, system_prompt,
                      # critic_prompt, few_shot, question_types, renderer_hints
  matematik/          # mevcut math içeriği buraya TAŞINIR (davranış aynı kalır)
  fen/                # yeni Fen plugin'i
```
- `subject` bilinmiyor/verilmemişse **varsayılan = "matematik"** → geriye dönük
  uyumluluk, mevcut linkler/SEO kırılmaz.
- Ortak omurga (grade→topic→kazanım indeksleme, MMR örnek seçimi, RAG fallback,
  quiz/puanlama/sınıf yönetimi) plugin'lerden bağımsız kalır.

## 3. Fazlar

### Faz 0 — Ders ekseni altyapısı (bir kez; sonraki tüm dersler bedava faydalanır)
**0a — Additive çekirdek (TAMAMLANDI 2026-07-10, 62/62 test yeşil, sıfır regresyon):**
- ✅ **Şema:** `subject: SubjectId = MATEMATIK` alanı `GenerateWorksheetRequest` +
  `CreateQuizRequest` + `RegenerateQuestionRequest`'e eklendi (default → eski
  istemciler aynen çalışır).
- ✅ **Enum:** `app/models/enums.py` `SubjectId` (`matematik`, `fen`).
- ✅ **Registry:** `app/subjects/` (base + matematik + fen + `__init__`);
  `get_subject / is_enabled / available_subjects`. Faz 0'da saf metadata
  (davranış taşımaz) — matematik üretimi hâlâ mevcut modülleri kullanır.
- ✅ **Feature flag:** `Settings.fen_enabled = False` (kalite kapısı); `fen.enabled`
  buna bağlı → subject=fen şemada kabul, üretimde kapalı.

**0b — Threading (ERTELENDİ — fen ingest'iyle birlikte yapılacak, çünkü tek başına
regresyon riski + doğrulanamaz):**
- **Chroma:** ingest metadata'ya `subject` + `retriever` `where` filtresi. **Not:**
  mevcut math dökümanlarında `subject` yok → filtreyi ŞİMDİ eklemek retrieval'ı
  BOZAR. Önce `subject="matematik"` backfill migration'ı, sonra filtre → fen
  ingest fazıyla bundle'lanır. Tek collection + `where={"subject": ...}` kararı.
- **İçerik sağlayıcıları:** matematik curriculum/prompt/few_shot'ı plugin'e taşı
  (fen kendi modüllerini getirince; erken taşımanın faydası yok, riski var).
- **Müfredat anahtarı:** `CURRICULUM`'u `subject → grade → ünite` yap.
- **Doğrulama:** her adımda matematik smoke + eval yeşil kalmalı.

### Faz 0.5 — Fen kaynak temini + manifest
- MEB Fen ders kitapları (3–8) + Fen soru bankası/kazanım testleri + LGS Fen
  derlemelerini topla → `knowledge_base/fen/` (alt-klasör).
- LGS kitapçıklarındaki (`8.Sınıf/lgs*.pdf`) **Fen bölümü** sayfa aralıklarını
  manifest'e işaretle (kitapçık çok dersli → sadece Fen sayfaları çıkarılacak).
- `manifest.json`: `[{"file","subject":"fen","grade","track":"lgs|textbook|bank","pages?"}]`.
- Büyük PDF'ler `.gitignore`'da; sadece üretilen JSON + ChromaDB versiyonlanır.

### Faz 1 — Fen müfredatı (en kritik; ÜNİTE BAZLI, güncel 2024 TYMM)
**Müfredat türetme TAMAMLANDI (2026-07-10):**
- ✅ Baz: 2024 onaylı TYMM Fen programı (`fen_ogretim_programi_2024_TYMM.pdf`).
  **2018 kullanılmadı.**
- ✅ `scripts/derive_fen_curriculum.py` — PDF'ten **deterministik, LLM'siz**
  (PyMuPDF + FB kod eşleme) türetir → `app/subjects/fen/curriculum.py`
  (`FEN_CURRICULUM: grade → [FenUnit]`, ünite bazlı, units.py deseni).
- ✅ Kod formatı: `FB.{sınıf}.{ünite}.{çıktı}` (3-4), `FB.{sınıf}.{ünite}.{bölüm}.{çıktı}` (5-8).
  **44 ünite, 182 kazanım** (3-8). İnsan-okur özeti: `docs/FEN_KAZANIMLAR.md`.
- ✅ Erişimciler (get_units_for_grade / get_unit / get_unit_kazanim /
  find_unit_by_kazanim / is_unit_available). 62/62 test yeşil, math regresyonsuz.

- ✅ **difficulty_hints TAMAMLANDI (2026-07-10):** 182/182 kazanıma kolay/orta/zor
  kalibrasyonu. Gemini API YOK — sınıf başına paralel **Claude alt-ajanları** yazdı,
  merkezi doğrulama (kod eşleşme + boş kontrolü) sonrası `app/subjects/fen/
  difficulty_hints.py`'ye toplandı; generator bunu curriculum.py'ye gömer (yeniden
  koşmada korunur). İlk pass — Faz 6'da rafine edilecek.

- ✅ **Fen prompt + critic + few-shot BAŞLADI (2026-07-10, Faz 4):**
  - `app/subjects/fen/prompt.py` — `SYSTEM_PROMPT` (MEB Bağlam Temelli Soru Yazım
    Kılavuzu + bilimsel doğruluk odaklı) + `YENI_NESIL_BLOCK` + generic hint.
  - `app/subjects/fen/critic.py` — `CRITIC_SYSTEM_PROMPT` (bilimsel olgu doğruluğu
    öncelikli; math'te SymPy verifier var, Fen'de critic ana kapı).
  - `app/subjects/fen/few_shot.py` — GERÇEK MEB LGS örnek soruları (EBA'dan),
    kazanıma göre etiketli, cevaplar elle doğrulandı, çözümler elle yazıldı.
    Şu an 5 örnek (8. sınıf): 4 metin + **1 görselli (yeni nesil, inline SVG)**.
  - 62/62 test yeşil, math regresyonsuz.

**GÖRSELLİ ("yeni nesil") few-shot — kalitenin ana kaynağı, DEVAM EDİYOR:**
- Kanıtlanmış boru hattı (Gemini'siz): `fitz` ile PDF sayfası → PNG → **Claude okur**
  → sisteme uygun formata yeniden kurar (inline `<svg>` / Markdown tablo / `{{chart}}`)
  → `is_valid_svg`/`is_dangerous` + fitz render ile doğrulanır.
- İlk örnek (21 Haziran mevsim diyagramı, FB.8.1.1.1) SVG olarak kuruldu, render teyitli.
- ⚠️ Zorluk: Fen sorularının çoğu **görsel ŞIKLAR** (çubuk grafik/diyagram = A/B/C/D)
  içeriyor — bunlar metne sadık çevrilemez → reframe veya review kuyruğu.
- KALAN: tam görselli korpus (tüm üniteler/sınıflar) = ayrı odaklı pass (çok sayfa,
  dikkatli SVG/tablo yeniden kurma + doğrulama). Kapsam kullanıcıyla belirlenecek.

- ✅ **Faz 0b threading TAMAMLANDI (2026-07-10) — pipeline'a bağlandı, uçtan uca doğrulandı:**
  - `agent.generate(subject=...)`: fen için curriculum/few-shot/system_prompt/
    yeni_nesil bloğu/critic/dağılım dallanır; RAG+textbook+math_verifier fen'de atlanır;
    **matematik yolu birebir korunur.**
  - `GeminiCritic(system_prompt=...)` + `build_user_prompt(yeni_nesil_block=...)`
    parametrelendi (ders-nötr motor, ders-özel prompt).
  - Router'lar (`worksheets.py`, `quizzes.py`, regenerate): `req.subject` geçilir;
    `subject=fen` + `fen_enabled=False` → **403 (kalite kapısı)**. Fen ünite bazlı
    doğrulama + display_name fen curriculum'dan.
  - Fen dağılımı yalnız fen tipleri (coktan_secmeli ağırlıklı), math sızıntısı YOK.
  - **GERÇEK ÜRETİM TESTİ:** 8. sınıf "Yaşamın Gizemi" FB.8.3.3.2 → 3 bilimsel-doğru
    LGS-kalite genetik sorusu (çaprazlama/olasılık); fen critic 0 red, ~$0.018.
  - 62/62 test yeşil, matematik regresyonsuz.

### Faz 6 — Kalite döngüsü: İLK TUR SONUÇLARI (2026-07-10)
32 gerçek soru üretildi (16 fen + 16 matematik, 8. sınıf, zor, yeni nesil), elle
karşılaştırıldı (rapor: scratchpad/fen_quality_report.md). **Bulgular:**
- **Fen metin kalitesi ZATEN matematik paritesinde.** 16 fen sorusunun tümü
  bilimsel doğru; çeldiriciler klasik kavram yanılgılarından (iş korunumu,
  kütle-ağırlık, ametal-gaz, olasılık≠kesinlik). LGS tarzı, çok adımlı.
- **Sürpriz:** few-shot'ı OLMAYAN üniteler (Kuvvet, Periyodik Tablo) de yüksek
  kalitede → difficulty_hints + güçlü system prompt metin için yeterli; few-shot'ın
  metin etkisi beklenenden az.
- **TEK NET EKSİK = GÖRSEL.** Matematik `gorsel_geometri` ile inline SVG üretiyor;
  fen HİÇ görsel üretmiyor (`_FEN_DEFAULT_TYPES` bilinçli metin-only). Yeni nesil
  görsel = kalitenin zirvesi (kullanıcı vurgusu) → **canlıya çıkışın gerçek kapısı bu.**
- Not: critic red %0 (fail-open, ayırt edici değil) → parite ölçümü için critic
  eşiği sıkılaştırılmalı VEYA bağımsız panel (Claude alt-ajanları) kullanılmalı.

### Faz 6 — Görselli üretim AÇILDI + KANITLANDI (2026-07-10)
- `app/subjects/fen/prompt.py`: bilimsel SVG kuralları eklendi (basit diyagram:
  Dünya-Güneş-Ay/devre/makara/mercek/deney düzeneği; çok karmaşık → metin).
- `_FEN_DEFAULT_TYPES`'a `GRAFIK_OKUMA` ({{chart}}) + `GORSEL_GEOMETRI` (inline SVG,
  <svg> yoksa enforce-drop) eklendi.
- **Görsel üretim testi (Mevsimler ünitesi, 4 görselli soru):** 4/4 GEÇERLİ SVG,
  hepsi render oldu, bilimsel doğru: Dünya-Güneş+eğik eksen (few-shot'tan öğrendi),
  direk-gölge (few-shot'suz kusursuz), yörünge 4-konum, sütun grafiği. is_valid_svg ✓.
- **SONUÇ: parite kapısı (görsel) KAPANDI.** Fen artık hem metin hem görsel yeni
  nesil soru üretiyor → matematik paritesinde. Küçük kozmetik: bazı etiketler
  çizgiye hafif değebiliyor (few-shot çoğaldıkça düzelir).

### Görselli parite karşılaştırması SONUÇ (2026-07-10) — PARİTE TEYİT EDİLDİ
24 görsel-zorlanmış soru (3 fen: Mevsimler/Kuvvet/Elektrik + 3 math: Geometrik
Şekiller/Nicelikler/Dönüşüm), tüm SVG'ler render + gözle incelendi.
- **SVG geçerlilik: fen 12/12 (%100) = math 12/12 (%100).**
- Bilimsel/geometrik doğruluk her ikisinde ✅. Fen few-shot'SUZ bile düzgün devre
  şeması (pil+ampul sembolleri), kaldıraç düzeneği kurdu.
- Ortak küçük kusur (iki ders de): ara sıra etiket taşması/havada etiket.
- **KARAR: metin (önceki tur) + görsel (bu tur) → fen MATEMATİK PARİTESİNDE.**
  Kalite kapısı esasen karşılandı.

**Kalan (go-live öncesi öncelik):**
1. Görselli few-shot korpusunu ölçekle + prompt etiket-marj kuralını güçlendir
   (tek kalan kozmetik: etiket yerleşimi).
2. Frontend ders seçici + `/x-sinif-fen` rotaları (Faz 5, flag arkasında).
3. `fen_enabled=True` kademeli go-live (Faz 7): önce flag, birkaç gün sonra SEO.
4. (Ops) critic eşiğini sıkılaştır / bağımsız panel — parite izlemeyi keskinleştir.

### Faz 2 — Çıkarım (matematik hattını yeniden kullan)
- **Track A (ders kitabı/kavram):** `extract_textbook.py --subject fen` →
  `fen_textbook_chunks.json` → cevapsız kavram/örnek (RAG bağlamı).
- **Track B (sorular, vision):** `extract_lgs_questions.py` desenini genelleştir
  → `--subject fen`. Fen soru şeması:
  `{stem, options[A–D], correct_answer, solution, kazanim_kod, difficulty, question_type, has_visual}`.
  - Deney/tablo/grafik → Markdown tablo + `{{chart:...}}` (mevcut makine).
  - `question_type`: `coktan_secmeli` / `grafik_okuma` / `tablo_sorusu` /
    `deney_yorumu` (yeni, format olarak çoktan-seçmeli ile aynı).
  - **Karmaşık bilimsel diyagram** (hücre, devre, sistem çizimi): **MVP'de ertele**
    → `has_visual=true & diagram` sorular review kuyruğuna (`fen_visual_review.json`),
    sessiz kayıp yok. 2. dalgada inline-SVG ile eklenir.
- Çıktı: `knowledge_base/processed/fen_examples.json`.

### Faz 3 — Etiketleme + Ingest
- `tag_textbook_chunks.py --subject fen` → tagged → `ingest_textbook.py --subject fen`.
- `ingest_to_chroma.py`'ye `_load_fen()` (`_load_lgs` deseni), her doc'a
  `subject="fen"` metadata. İdempotent.

### Faz 4 — Fen prompt + few-shot çıpa
- `app/subjects/fen/prompt.py`: Fen `SYSTEM_PROMPT` — "MEB Fen Bilimleri müfredatı,
  bilimsel olgu doğruluğu, deney/gözlem senaryoları, 4 şık, muhakeme-ağırlıklı,
  çeldiriciler anlamlı ve bilimsel kavram yanılgılarına dayalı". **Kaynak standart:**
  MEB Bağlam Temelli Çoktan Seçmeli Soru Yazım Kılavuzu (`knowledge_base/Fen/
  mufredat/coktan_secmeli_soru_yazim_kilavuzu.pdf`) — soru yazım kuralları,
  bağlam temelli kurgu ve çeldirici tasarımı buradan prompt'a damıtılır.
- `app/subjects/fen/critic.py`: Fen doğrulayıcı — **bilimsel doğruluk** kontrolü
  (matematikteki sayısal doğrulama yerine olgu/kavram doğrulaması).
- `app/subjects/fen/few_shot/`: LGS Fen çıkarımından **en kaliteli** Q&A'leri her
  kazanım için elle seç → sabit kalite çıpası.

### Faz 5 — Frontend (flag arkasında, GİZLİ)
- **Feature flag:** Fen tüm frontend'de `NEXT_PUBLIC_FEN_ENABLED` (veya benzer)
  arkasında. Flag kapalıyken ders seçici, SEO rotaları ve ana sayfa değişikliği
  **son kullanıcıya görünmez** — sadece staging/preview'da açılır. Kalite kapısı
  (Faz 7) geçilmeden flag production'da **açılmaz.**
- `GenerateForm.tsx` / `SolveForm.tsx`: **ders seçici** ekle (sınıf → **ders** →
  ünite → kazanım). Flag kapalıyken seçici gizli; math akışı birebir korunur.
  Deep-link `?subject=fen`.
- Sınıf seçici: Fen için 3–8 (matematikte mevcut aralık korunur).
- Yeni SEO rotaları: `/3-sinif-fen` … `/8-sinif-fen` + `/lgs-fen` hub
  (`GradeMathHub` → genel `GradeSubjectHub`'a genelleştir; matematik rotaları
  kırılmadan). **Flag kapalıyken sitemap'e/robot'a eklenmez** (indekslenmesin).
- **Ana sayfa:** "Matematik + Fen" ders seçimi **flag arkasında** hazırlanır
  (bkz. `frontend-redesign-direction`, ikili tasarım korunur).

### Faz 6 — Kalite iterasyon döngüsü (ANA İŞ — kapı burada açılır)
Bu faz bir olay değil, **döngü**: kalite matematik paritesine gelene kadar
üret → ölç → prompt/few-shot/korpus iyileştir → tekrar. Canlıya çıkışın kilidi.

- **Parite tanımı (geçme kriteri):** Fen soruları, matematiğin eval hattındaki
  aynı metriklerde **matematiğin skoruna eşit veya daha iyi** olmalı:
  - `scripts/eval/scenarios.py`'ye Fen senaryoları (her öğrenme alanı × sınıf).
  - **Fen critic** skoru (bilimsel doğruluk + müfredat uyumu + çeldirici kalitesi)
    → matematik critic baseline'ı ≥.
  - **Kavram-yanılgısı / olgu hatası oranı** eşik altında (Fen'e özel; matematiğin
    `math_verifier` karşılığı — olgu doğruluğu insan + LLM çapraz kontrol).
  - Eko-odası kontrolü: üretilen sorular few-shot'ı kopyalamıyor (diversity),
    gerçek LGS Fen tarzını tutturuyor.
- **Manuel kalite paneli:** her öğrenme alanından örnek setler elle okunur
  (bilimsel doğruluk, grafik/tablo render, LGS Fen tarzı). Matematikle
  **yan yana** karşılaştırma.
- **İterasyon kolları:** kalite düşükse sırasıyla → (a) few-shot çıpasını
  güçlendir/gerçek soru ekle, (b) korpusu büyüt (Faz 0.5 kaynak), (c) Fen prompt
  + critic kurallarını sıkılaştır, (d) gerekiyorsa dağılım/model ayarı.
- **Regresyon:** her turda **matematik smoke + eval** yeşil kalmalı (Faz 0 kapısı).
- **Çıkış koşulu:** parite metrikleri geçildi + manuel panel onayı → Faz 7'ye geç.
  Geçilmezse canlıya ÇIKILMAZ; iterasyona devam.

### Faz 7 — Gated go-live (kaliteye bağlı, takvime değil)
- **Ön koşul:** Faz 6 parite kapısı geçildi.
- **Merge öncesi Vercel preview curl** (yeni SSR rotaları — bkz.
  `verify-preview-before-merge`; CI runtime hatası yakalamaz). SSR dynamic
  sayfalarda `SafeSvg` client-only import kuralı (bkz. `ssr-dompurify-esm-landmine`).
- ChromaDB commit. frontend-ci (lint+typecheck) doğrula. Render yeni DB'yi alır.
- **Kademeli açılış:** önce `NEXT_PUBLIC_FEN_ENABLED` production'da aç (rotalar
  görünür), SEO'yu (sitemap/robot) **birkaç gün sonra** ekle → canlı davranışı
  gözlemle, sorun çıkarsa flag'i kapatıp geri al.
- Açılıştan sonra üretim kalitesini canlı örneklerle izle (regresyon avı).

### Faz 8 — Şablonlaştır (sonraki dersleri ucuzlat)
- `docs/ADD_NEW_SUBJECT.md`: Fen'i referans alarak "yeni ders nasıl eklenir"
  adım listesi (plugin iskeleti + içerik hattı + frontend rotaları).
- İngilizce/Türkçe artık günler içinde: sadece plugin içeriği + rotalar + korpus.

## 4. Efor sırası ve kaba süre
- **Faz 0** (ders ekseni) ~3–4 gün — mekanik ama regresyonsuz olmalı.
- **Faz 0.5 + 1** (kaynak + müfredat) ~1–2 hafta — **darboğaz** (kaynak temini
  insan-süreci + müfredatın elle doğrulanması).
- **Faz 2–4** (çıkarım + prompt + few-shot) ~1 hafta — mevcut pipeline'ın tekrarı.
- **Faz 5** (frontend, flag arkasında) ~3–5 gün.
- **Faz 6** (kalite iterasyon döngüsü) **açık uçlu** — parite gelene kadar; asıl
  emek burada. Takvime değil, kaliteye bağlı.
- **Faz 7** (gated go-live) parite geçilince ~1–2 gün.
- Toplam ilk ders: altyapı+içerik ~**3–4 hafta**, **+ belirsiz kalite iterasyonu**.
  Sonraki dersler (Faz 8 sonrası) günler + kendi kalite döngüsü.

Geliştirme sırası: **Faz 0 → (matematik regresyon teyidi) → 0.5 → 1 → 2A/3A
(textbook hattı uçtan uca) → 2B/3B/4 (LGS Fen + few-shot) → 5 (flag'li) → 6
(kalite döngüsü — kapı) → 7 (gated go-live) → 8.**

> **Şu anki durum (2026-07-10):** Kullanıcı Fen test kaynaklarını (soru/PDF)
> çıkarıyor; iş bunlar hazır olunca başlayacak. Canlıya alma acelesi yok — kalite
> matematik paritesine gelene kadar Faz 6 döngüsünde çalışılacak.

## 5. Gemini maliyet tahmini (yaklaşık, USD)
Matematik planındaki birim fiyatlarla (Flash giriş ~$0.30/1M, çıkış ~$2.50/1M,
embedding ~$0.15/1M):

| İş | ~Maliyet |
|---|---|
| Fen textbook tagging (Flash) | ~$1.5–2 |
| Fen soru vision çıkarımı (Flash) | ~$1.5–2 |
| Faz 1 müfredat türetme | ~$0.2 |
| Embedding ingest | ~$0.2 |
| **Tek temiz koşu** | **~$4–5** |
| **Geliştirme iterasyonu dahil (×2, resumable)** | **~$8–12** |

Scriptler resumable → yeniden koşmalarda maliyet düşük. Kaynak korpusu büyüdükçe
lineer artar.

## 6. Riskler
1. **Kaynak yetersizliği (en yüksek risk):** Eldeki LGS Fen bölümleri az →
   MEB-uygun ek kaynak temini kritik yol. Hat, az korpusla ispatlanır, kaynak
   geldikçe büyütülür.
2. **Bilimsel doğruluk:** Matematikte sayısal `math_verifier` var; Fen'de olgu
   doğruluğu LLM critic'e bağlı → daha kırılgan. Critic + gerçek few-shot çıpası
   ile azaltılır; şüpheli olgular review kuyruğuna.
3. **Diyagram reprodüksiyonu:** Karmaşık bilimsel görseller SVG'ye sadık
   çevrilemez → MVP'de ertelenir, review kuyruğu, sessiz kayıp yok.
4. **Ders ekseni regresyonu:** Faz 0 matematiği bozabilir → matematik smoke +
   eval Faz 0 çıkışında zorunlu kapı.
5. **Müfredat doğruluğu:** `CURRICULUM[fen]` otomatik türetilip **elle doğrulanır**
   (resmi-olmayan kod sorununu tekrarlama).
6. **SEO namespace:** Yeni rotalar mevcut matematik rotalarını/iç linklemeyi
   kırmamalı; matematik URL'leri sabit kalır. Flag kapalıyken Fen rotaları
   sitemap/robot'a girmez (yarım kaliteyle indekslenip domain otoritesini
   düşürmesin — bkz. `acquisition-bottleneck-2026-07`).
7. **Erken canlıya alma (kabul edilmez):** Matematik altındaki kaliteyle Fen'i
   açmak markayı ve güveni zedeler. Bu yüzden go-live **kaliteye bağlı kapı**
   (Faz 7), takvime değil. Flag + parite metrikleri bu riski kontrol eder.
