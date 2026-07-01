# 1–7. Sınıf — Gerçek Soru Havuzu (Vision) Besleme Planı

> Durum: **Plan — kararlar netleşti, geliştirme bekliyor.** Tarih: 2026-06-28
> Yöntem: **Vision soru çıkarma** (8. sınıf LGS pipeline'ı baz alınarak genelleniyor).
> Kaynak: kullanıcının vereceği yeni PDF'ler (açık-kaynak, çok sayıda farklı yayın) →
> `knowledge_base/4.Sınıf/`, `5.sınıf/`, `6.sınıf/`, `7.Sınıf/` (+ ileride 1-3).

## 0. Neden bu iş — kalite kök nedeni

Hafıza notu [[question-quality-fewshot-rootcause]]: **1-7. sınıf few-shot'ı %100
sentetik** (Gemini'nin kendi ürettiği örnekler) → model kendi tarzını taklit eden
bir **eko-odası**. 8. sınıf yüksek kaliteli çünkü few-shot'ı **gerçek LGS soruları**.

→ **Çözüm = 1-7 için de gerçek soru havuzu kurmak.** Kullanıcı 4-7. sınıf klasörlerine
gerçek soru kaynakları koydu (soru bankası, yaprak test, kazanım testi, sınav). Kaynaklar
**genel bir yapıya uymuyor** (her yayın farklı) ve **açık-kaynak** (telif sorunu yok;
örnek olarak öğretiliyor, asla 1:1 üretilmiyor).

## 1. "Modeli eğitmek" bu sistemde ne demek? (mimari gerçeklik)

**Fine-tuning YOK.** (Kod tabanında doğrulandı — hiçbir yerde tuning/training yok.)
Gemini'nin ağırlıkları hiç değişmiyor. "Öğretmek" = **RAG few-shot**:

> Sorular ChromaDB'de gömülü durur. Üretim anında sistem o kazanım/zorluk için **en
> alakalı 2-N örneği** çeker, prompt'a "işte böyle sorular" diye koyar; model o an
> bunların **tarzını** taklit eder. (`agent.py:_collect_few_shot_rag` → `select_diverse`
> MMR çeşitlilik cezası → prompt.)

Üç sonuç (tüm stratejiyi belirler):
1. **"Asla 1:1 üretmeme" hedefi mimari olarak garanti.** Model ezberlemez; her üretimde
   bir avuç örneğin desenini alıp çeşitlilik cezası + semantik dedup (cosine>0.88) +
   bağlam-token rotasyonu (`used_tokens`) + sıcaklık ile yeniden harmanlar.
2. **Kalite ≫ nicelik.** Model her üretimde sadece ~2-5 örnek görür. **5.000 vasat soru
   < 200 mükemmel, doğru-etiketli, çeşitli soru.** Hedef "çok soru yükle" değil,
   "her çekimde harika bir öğretmen örneği çıksın" küratörlüğü.
3. **Heterojenlik sorun değil — varsayım bu.** Vision sayfayı insan gibi okuyup tek
   kanonik şemaya indirger; kaynak dağınıklığı çıkarımda erir. Bu yüzden vision (regex
   değil) doğru araç. Karşılığında **kalite de heterojen** → doğrulama katmanı şart.

**Fine-tuning kararı:** Şimdilik **HAYIR.** Daha pahalı, esnek değil (yeni kazanım =
baştan tune) ve ezberleme riskini artırıp "1:1 üretmeme" hedefine ters düşer. RAG kalitesi
platoya vurursa tekrar değerlendirilir.

## 2. Öğretim birimi: "soru" değil, tam yapı çıkar

Sorunun metni tek başına az şey öğretir. Modele *iyi soru üretmeyi* öğreten, her örneğin
tam yapısıdır. Çıkardığımız kanonik **öğretim birimi**:

| Alan | Modele ne öğretir | Karar |
|---|---|---|
| **stem** | senaryo kurma, ifade tarzı | hep çıkar |
| **answer** | geçerli cevap neye benzer | hep çıkar |
| **solution_steps** | **en değerli sinyal** — çözülebilir problem nasıl kurulur | **her örnekte olacak** (bkz. 3.1) |
| **distractors** (yanlış şıklar) | iyi çeldirici mantığı | MCQ'lerde çıkar |
| **kazanim_kod** | **çekilebilirlik** — yanlış etiket = ya hiç çıkmaz ya yanlış konuyu kirletir | çıkar + doğrula (3.3) |
| **difficulty / question_type / visual** | kalibrasyon, çeşitlilik, görsel kurma | çıkar |

Şema 8. sınıfla birebir uyumlu (few-shot formatı):
`{grade, topic_id, kazanim_kod, difficulty, question_type, question, answer, solution, source}`
— görsel soru `question` alanının içine inline `<svg>` / Markdown tablo gömer.

## 3. Kalite katmanı (kararlaştırılan — işin asıl değeri buradadır)

Çıkarım işin **~%30'u**; **doğrulama + çözüm + küratörlük + çıpalama %70'i.**

### 3.1 Çözüm izi — HER örnekte
- Kaynakta çözüm **varsa** → vision çağrısında yakala (bedava).
- Sadece **cevap anahtarı** (harf/sayı) varsa → modele **çözümü ürettir**, sonra 3.2 ile
  **doğrula**. Çözümsüz örnek "benzet" der; çözümlü örnek "şöyle düşünüp kur" der.

### 3.2 Doğruluk doğrulaması — açık (çöp girerse çöp çıkar)
- Aritmetik tipler (`SALT_ISLEM`, `ISLEM`) → mevcut **`app/services/math_verifier.py`
  (SymPy, deterministik, ÜCRETSİZ)**.
- Sözel/görsel sorular → **`critic`** (LLM judge). "Söylenen cevap problemi gerçekten
  çözüyor mu?" Hatalı/muğlak → elenir veya review kuyruğuna düşer (sessiz kayıp yok).
- *Kod eforu (orta, tek seferlik):* verifier/critic bizim ürettiğimiz `Question` şeması
  için yazıldı → dışarıdan çıkarılan soruyu skorlamak için hafif uyarlama gerekir.

### 3.3 Kazanım etiketle + doğrula
Extractor kazanım kodunu döndürür; `CURRICULUM[grade]`'e karşı doğrulanır. Geçersiz/null
kod → `confidence=low` ile gürültü elenir (mevcut tagging deseni). MEB 2024 yeni konuları
→ `curriculum_expansion`/null (mevcut desen).

### 3.4 İki katmanlı korpus — kalite barı
- **Altın çıpalar** (kazanım başına **5**: kolay/orta/zor + 2 format çeşidi): tarzın
  belkemiği, model en sık bunları görür. → `app/data/few_shot/grade_N.py`'deki
  **sentetik eko-odasını** doğrulanmış gerçeklerle **değiştirir**. **Kök neden çözümünün
  ~%70'i burada.** Kalite barı: **insan spot-check** (sistem en iyi ~5 adayı önerir,
  kabul/ret) — küçük bir review kuyruğuyla.
- **Çekim havuzu** (büyük, ChromaDB): çeşitlilik için, dinamik çekilir. Kalite barı:
  **otomatik** (3.2 + semantik dedup). İnsan review imkânsız, gerekli de değil.

## 4. İçerik track'leri (her sınıf klasöründe `manifest.json`)

| Track | Hangi PDF'ler | İşleme | Hedef |
|---|---|---|---|
| **`questions`** | soru bankası, yaprak test, kazanım testi, sınav, çıkmış soru | **vision extractor** → kalite katmanı → `ingest_to_chroma` | **Gerçek few-shot Q+A** (asıl kazanım) |
| **`textbook`** | ders kitabı, konu özeti, çalışma kitabı | `extract_textbook` → `tag` → `ingest_textbook` | Cevapsız kavram/örnek bağlamı |
| **`skip`** | kopya / tanıtım / mükerrer baskı | işlenmez | — |

> Kodda `lgs` track'i `questions`'ın **alias'ı** olur (8. sınıf geriye dönük uyum).

**`manifest.json` şablonu** (dosya isimleri değiştirilmeden):
```json
{
  "grade": 5,
  "description": "5. sınıf — soru bankası, yaprak test, kazanım testi, sınav",
  "files": [
    {"file": "5-sinif-matematik-soru-bankasi.pdf", "track": "questions"},
    {"file": "5. Sınıf Matematik Yaprak Test_Ornek.pdf", "track": "questions"},
    {"file": "04193346_5.sYnYf_matematik_kazanYm_testi.pdf", "track": "questions"},
    {"file": "sınav1.pdf", "track": "questions"},
    {"file": "mat5.pdf", "track": "textbook"},
    {"file": "429025s05ma1_mat_tadimlikpdf.pdf", "track": "skip", "note": "tanıtım/tadımlık"}
  ]
}
```

## 5. Fazlar

### Faz 0 — Klasör + manifest + repo hijyeni
- Her sınıf klasörüne `manifest.json` (PDF'ler gelince track atanır).
- Gürbüz folder çözümü: `4.Sınıf`/`5.sınıf` casing tutarsızlığı (İ/ı) → `_resolve_grade_dir(grade)`
  (`glob` + casefold).
- Büyük PDF'leri `.gitignore`'a ekle; sadece **üretilen JSON + ChromaDB** versiyonlanır.
  Kod node'da build edilemediği için [[frontend-build-ci]] geçerli → değişiklik CI ile doğrulanır.

### Faz 1 — Vision extractor'ı genelleştir (en kritik kod işi)
`scripts/extract_lgs_questions.py` → `scripts/extract_questions.py` (LGS shim korunur):
1. **`--grade N`** + gürbüz folder/manifest çözümü (grade-8 hardcode kalkar).
2. **Çok-formatlı Pydantic şeması:** `question_type` = `coktan_secmeli | acik_uclu |
   bosluk_doldurma | dogru_yanlis | eslestirme | siralanan` (+ görselli türler).
   `options` opsiyonel; `correct_answer` her formatta dolar.
3. **Vision akışı korunur:** sayfa→`get_pixmap`→Flash vision → cevap anahtarı tespiti →
   görselli sorularda 2. çağrı ile inline `<svg>`/Markdown.
4. **Çözüm izi (3.1):** kaynakta yoksa çözümü ürettir.
5. **Görsel sadakat kuyruğu** korunur: reproduce edilemeyen → `questions_visual_review_grade{N}.json` + log.
6. Çıktı: `processed/questions_grade{N}.json`; `stable_id` ile **mükerrer eleme**.

### Faz 2 — Çıkarım (kullanıcı PDF'leri verince)
```bash
python scripts/extract_questions.py --grade 5 --limit 1   # pilot: 1 PDF, doğrula
python scripts/extract_questions.py --grade 5             # tüm questions-track
python scripts/extract_textbook.py  --grade 5             # textbook-track (mevcut hat)
```

### Faz 3 — Kalite katmanı + Ingest
- **Doğrulama (3.2):** `math_verifier` (SymPy) + `critic` ile her çıkarılan soruyu skorla;
  hatalı/muğlak → ele/review.
- **Kazanım doğrula (3.3):** `CURRICULUM[grade]`'e karşı.
- **Ingest:** `ingest_to_chroma.py`'ye `_load_questions()` ekle (`_load_lgs` deseni),
  `source="questions/grade{N}/<dosya>"`, `content_type` set ETME → retriever few-shot
  Q&A olarak görür. textbook-track: `tag_textbook_chunks.py` → `ingest_textbook.py`.
```bash
python scripts/ingest_to_chroma.py        # idempotent
```

### Faz 4 — Altın çıpa küratörlüğü (kök neden çözümü, 3.4)
- Sistem her kazanım için en iyi ~5 adayı önerir (review kuyruğu).
- **İnsan spot-check** → onaylananlar `app/data/few_shot/grade_N.py`'ye yazılır,
  **sentetik örnekleri değiştirir**. `EXAMPLES_BY_GRADE` güncellenir.

### Faz 5 — Doğrulama (önce/sonra)
- `scripts/eval/scenarios.py` + `math_verifier` + `critic` ile **çıpa öncesi/sonrası kıyas.**
- Smoke: her sınıf + her öğrenme alanından 1 soru; retriever'ın gerçek few-shot çektiğini logla.
- Manuel göz: LaTeX render (kesir/üslü), görsel sorular (SVG render), format çeşitliliği.
- Merge öncesi Vercel preview teyidi [[verify-preview-before-merge]].

### Faz 6 — Deploy
- ChromaDB commit (`chroma.sqlite3` versiyonlu) → Render API yeni DB'yi alır.
- frontend-ci (lint+typecheck) yeşil → merge.

## 6. Önerilen yürütme sırası
"Tüm sınıflar" hedefi olsa da tek seferde değil:
1. **Faz 0 + 1** (manifest + extractor genelleme) — bir kez.
2. **5. sınıf PILOT** (en çok kaynak) → Faz 2→3→4→5 uçtan uca → kaliteyi/maliyeti ölç.
3. Pilot iyiyse **4, 6, 7** paralel → ardından **1-3** (kaynak gelince).
4. Her sınıf bağımsız resumable → bir sınıfta hata diğerlerini etkilemez.

## 7. Maliyet (1-7, tek temiz koşu)

> Flash: giriş ~$0.30/1M, çıkış ~$2.50/1M; embedding ~$0.15/1M. Hacim: ~400 soru/sınıf ≈ ~2.800, ~%30 görselli.

| Kalem | Yöntem | ~Maliyet |
|---|---|---|
| Vision soru çıkarımı | Flash | ~$15-20 |
| Görsel SVG 2. çağrı (~%30) | Flash | ~$8 |
| Çözüm sentezi (çözümsüzler) | Flash | ~$2-3 |
| Doğruluk doğrulaması | SymPy (bedava) + critic | ~$1-2 |
| Embedding ingest | embedding-001 | ~$1 |
| **Compute toplam (temiz)** | | **~$27-34** |
| **+ geliştirme iterasyonu (resumable)** | | **~$45-65** |
| **İnsan küratörlük (altın çıpalar, Faz 4)** | — | **~5-7 saat** (para $0) |

**Öz:** Para olarak asıl iş vision çıkarımı (~$23-28); doğrulama+çözüm+küratörlük katmanı
paraya sadece **~$3-5 ekler** ama kaliteyi asıl yükselten budur. Gerçek maliyet para değil,
**~5-7 saatlik insan çıpa küratörlüğü** — kök nedeni (sentetik eko-odası) çözen de o.

## 8. Riskler
1. **Format çeşitliliği:** çok-formatlı şema + esnek `correct_answer`; çıkarılamayan → review.
2. **Görsel sadakat:** fotoğraf/karmaşık şekil SVG'ye çevrilemez → review kuyruğu.
3. **Telif:** kaynaklar açık-kaynak; few-shot **örnek**, üretim kopyalamaz (diversity penalty
   + mimari garanti, bkz. 1). 1:1 üretim hedeflenmez.
4. **Kazanım eşleşmesi:** MEB 2024 yeni konuları → `curriculum_expansion`/null.
5. **Folder casing:** İ/ı tutarsızlığı → Faz 0 normalize helper'ı şart.
6. **Doğrulama kapsamı:** SymPy yalnız aritmetik; sözel/görselde `critic`'e güveniriz
   (mükemmel değil) → altın çıpalarda insan gözü bu boşluğu kapatır.

## 9. Onay sonrası ilk somut adımlar
1. Faz 0: 4 klasöre `manifest.json` iskeleti.
2. Faz 1: `extract_questions.py` (genelleme + çok-format şema + çözüm izi).
3. Kullanıcı 5. sınıf PDF'lerini verir → pilot koşu → kalite raporu → karar.
