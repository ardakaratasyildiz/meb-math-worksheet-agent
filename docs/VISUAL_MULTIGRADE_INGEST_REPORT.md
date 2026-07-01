# 5–6–7. Sınıf Gerçek Soru + Görsel Çeşitlendirme — Derin Teknik Rapor

> Durum: **Teknik rapor — geliştirmeye hazır.** Tarih: 2026-06-28
> Kapsam: `knowledge_base/5.sınıf/`, `6.sınıf/`, `7.Sınıf/` altındaki gerçek soru PDF'leri
> Amaç: (1) eko-odasını kır (gerçek soru few-shot), (2) **görsel soru çeşitliliğini artır**.
> Önceki plan: `MULTIGRADE_QUESTION_INGEST_PLAN.md` — bu rapor onu kaynak envanteri + görsel
> eksenle somutlaştırır ve geliştirme sırasını sabitler.

---

## 0. Kaynak envanteri (gerçek durum — diskten okundu)

Klasörlerde **iki tür içerik** var; doğru track ataması başarının ön koşulu.

### 5.sınıf/ (en zengin — pilot adayı)
- **Çıkmış sorular (ALTIN):** `5.SINIF DOĞAL SAYI PROBLEMLERI ÇIKMIŞ SORULAR.pdf`,
  `... KESİRLER ...`, `... YÜZDELER ...`, `... ÜÇGEN VE DÖRTGENLER ...`,
  `... ÜSLÜ İFADELER ...`, `... TEMEL GEOMETRİK KAVRAMLAR ...` (10+ dosya, konu-etiketli).
- **Konu testleri (yaprak/kazanım):** `10-Kesirler Testi.pdf`, `2-5.Sınıf Açı Ölçme Testi.pdf`,
  `17-temel-geometrik-kavramlar...`, `15-yuzdeler.pdf` vb. — **dosya adı = konu sinyali**.
- **Soru bankası / yaprak test:** `5-sinif-matematik-soru-bankasi.pdf` (39MB),
  `5. Sınıf 1-40. Hafta Yaprak Testleri.pdf` (16MB).
- **Sınav/ÖDM:** `Isparta_ÖDM...`, `Nevşehir_ÖDM...`, `sınav1-4.pdf`.
- **Ders kitabı (textbook track):** `mat5.pdf`, `mat5_2.pdf`.
- **Skip:** `429025s05ma1_mat_tadimlikpdf.pdf` (tadımlık/tanıtım).

### 6.sınıf/ — benzer yapı
Çıkmış sorular (kesir, ondalık), konu testleri (çarpanlar, bölünebilme, cebirsel ifadeler,
üçgen/dörtgende açılar), `6-sinif-matematik-soru-bankasi.pdf` (66MB), `mat6.pdf` (textbook).
⚠️ Mükerrer: `mat6.pdf` = `mat6 (1).pdf`, `Cebirsel İfadelerin Anlamı.pdf` = `(1)` kopyası → skip.

### 7.Sınıf/ — görsel-ağırlıklı (geometri yoğun)
Tam sayılar, rasyonel sayılar, oran-orantı, denklem **+ ağır geometri**: açıortay, doğrular-açılar,
çokgenler, dörtgenler, **dörtgenlerde alan**, **çemberde açılar**, **çemberin uzunluğu**,
**dairenin alanı**. `7. Sınıf 1-40.Hafta Yaprak Testler.pdf` (41MB), `7bts1/2.pdf`, `7calisma.pdf`
(textbook, ~90-140MB devasa). Çıkmış sorular: cebirsel ifadeler, denklem, rasyonel.

**Sonuç:**
1. Kaynaklar **konu-bazlı parçalanmış** → dosya adından kazanım pre-mapping yapılabilir
   (vision'a "bu PDF muhtemelen M.7.3.x" ipucu verip etiket doğruluğunu artırır).
2. **Çıkmış sorular = altın çıpa** için ideal (gerçek MEB, doğru cevap güvenilir).
3. **6-7. sınıf görsel yoğun** (açı/çokgen/çember/alan) → görsel çeşitliliğin asıl kazanımı burada.
4. Devasa textbook PDF'leri (90MB+) ayrı, daha yavaş textbook hattına; **questions track önce**.

---

## 1. İki bağımsız "görsel" ekseni — kritik ayrım

Kullanıcı "görsel olarak da çeşitlendirme" istiyor. Sistemde görsel **iki ayrı yerde** yaşıyor;
ikisi de iyileştirilecek ama mekanizmaları farklı:

### Eksen A — Çıkarım-anı görsel (PDF → few-shot örneği)
PDF'deki şekil → `_reproduce_visual()` ikinci Gemini çağrısı → inline `<svg>` / Markdown tablo
(`extract_lgs_questions.py:271`). Başarısız → `*_visual_review.json` kuyruğu.
**Bu, modele "gerçek görsel soru nasıl olur" örneği besler.**

### Eksen B — Üretim-anı görsel (model SVG üretir)
Üretimde `gorsel_geometri`/`grafik_okuma`/`oruntu_sekil` tipleri model tarafından inline SVG
olarak üretilir; `app/services/svg_utils.is_valid_svg` ile parse + güvenlik kontrolü, PDF'te
`svglib` ile render edilir (`pdf_renderer.py`).
**Mevcut görsel few-shot'lar kısmen SENTETİK** (`generate_geometry_svg.py`,
`geometry_svg_examples.json`, `chart_pattern_svg_examples.json`) → **görselde de eko-odası var.**

> **Asıl içgörü:** Görsel çeşitliliği artırmanın yolu = Eksen A ile **gerçek görsel soruları**
> çıkarıp few-shot havuzuna koymak → Eksen B'de model artık sentetik SVG'yi değil, gerçek
> sınav şekillerinin tarzını taklit eder. 6-7. sınıf geometri PDF'leri tam bu boşluğu doldurur.

---

## 2. Hedef veri şeması (8. sınıfla uyumlu, çok-formatlı)

Çıkarılan her örnek 8. sınıf few-shot şemasına uyar (geriye dönük uyum):

```
{
  grade, topic_id, kazanim_kod, difficulty,
  question_type,        # coktan_secmeli | acik_uclu | bosluk_doldurma |
                        # dogru_yanlis | eslestirme | siralanan |
                        # gorsel_geometri | grafik_okuma | tablo_sorusu | oruntu_sekil
  question,             # stem + (görselse inline <svg>/Markdown) + (MCQ ise şıklar)
  answer, solution,     # solution HER örnekte (bkz. 3.1)
  source                # "questions/grade5/<dosya>.pdf"
}
```

MCQ olmayan formatlar için `options` opsiyonel; `correct_answer` her formatta dolar.
Görsel örnekte `<svg>` doğrudan `question` alanına gömülür (Eksen B render hattı zaten bunu bekler).

---

## 3. Kalite katmanı (işin %70'i — "çöp girerse çöp çıkar")

### 3.1 Çözüm izi — her örnekte
Kaynakta çözüm varsa vision yakalar (bedava). Sadece cevap anahtarı varsa modele çözüm ürettir +
3.2 ile doğrula. Çözümlü örnek modele "şöyle düşünüp kur" der; çözümsüz sadece "benzet" der.

### 3.2 Doğruluk doğrulaması
- Aritmetik (`SALT_ISLEM`, `ISLEM`) → `app/services/math_verifier.py` (SymPy, deterministik, ücretsiz).
- Sözel/görsel → `app/services/critic.py` (LLM judge). Hatalı/muğlak → ele veya review.
- ⚠️ Critic generator'la aynı aile (Gemini) → kör nokta paylaşır. Bu boşluğu **altın çıpalarda
  insan gözü** kapatır (3.4).

### 3.3 Görsel sadakat doğrulaması (Eksen A'ya özel — YENİ)
Çıkarılan inline SVG, ingest'ten ÖNCE `svg_utils.is_valid_svg`'den geçmeli (Eksen B ile aynı
kapı). Geçmeyen → review kuyruğu, asla havuza girmez. Böylece **bozuk SVG few-shot'a sızmaz**
(yoksa model bozuk SVG taklit eder). Ek bir hafif kontrol: viewBox var mı, `<text>` etiketleri
ölçü içeriyor mu — yoksa "şekil var ama anlamsız" örnek elenir.

### 3.4 İki katmanlı korpus
- **Altın çıpalar** (kazanım başına ~5: kolay/orta/zor + 2 format/görsel çeşidi) →
  `app/data/few_shot/grade_N.py`'deki **sentetik örnekleri değiştirir**. İnsan spot-check.
  **Kök neden çözümünün %70'i.** Görsel kazanımlarda (açı, çember, alan) en az 2 çıpa
  **gorsel_geometri** tipinde olmalı → görsel çeşitlilik garantisi.
- **Çekim havuzu** (büyük, ChromaDB) → otomatik doğrulama + semantik dedup (cosine>0.88).

---

## 4. Mimari değişiklikler (kod planı)

### 4.1 `extract_lgs_questions.py` → `extract_questions.py` (genelleştir)
LGS shim korunur (8. sınıf geriye dönük çalışır). Değişiklikler:

| # | Değişiklik | Detay |
|---|---|---|
| 1 | `--grade N` argümanı | grade-8 hardcode kalkar; `GRADE8_DIR` → `_resolve_grade_dir(grade)` |
| 2 | **Gürbüz folder çözümü** | `4.Sınıf`/`5.sınıf` casing + İ/ı tutarsızlığı → `glob` + `casefold` |
| 3 | `_stable_id` grade param | `lgs_` prefix → `q{grade}_` (LGS için shim'de `lgs_` kalır) |
| 4 | **Çok-formatlı şema** | `MCQQuestion` → `ExtractedQuestion`: `options` opsiyonel, `question_type` 10 değer |
| 5 | **Dosya-adı kazanım ipucu** | manifest'teki `kazanim_hint` → extraction prompt'a "muhtemel konu" |
| 6 | **Görsel sadakat kapısı** | `_reproduce_visual` çıktısı `is_valid_svg`'den geçer (3.3) |
| 7 | Çıktı yolu | `processed/questions_grade{N}.json` + `questions_visual_review_grade{N}.json` |

### 4.2 `manifest.json` — her sınıf klasörüne
Dosya adından track + kazanım otomatik öneri (insan onaylar):
```json
{
  "grade": 5,
  "files": [
    {"file": "5.SINIF KESİRLER ÇIKMIŞ SORULAR.pdf", "track": "questions", "kazanim_hint": "M.5.1.4", "gold": true},
    {"file": "2-5.Sınıf Açı Ölçme Testi.pdf",       "track": "questions", "kazanim_hint": "M.5.3.1", "visual_heavy": true},
    {"file": "mat5.pdf",                              "track": "textbook"},
    {"file": "429025s05ma1_mat_tadimlikpdf.pdf",      "track": "skip", "note": "tadımlık"}
  ]
}
```
`gold:true` → altın çıpa adayı önceliklendirilir. `visual_heavy:true` → görsel çıkarım batch'i
küçültülür (sayfa başına daha dikkatli vision).

### 4.3 `ingest_to_chroma.py` — `_load_questions(grade)` ekle
`_load_lgs` desenini izler. `content_type` SET ETME → retriever few-shot Q&A olarak görür
(textbook chunk'larından ayrışır). `source="questions/grade{N}/<dosya>"`.

### 4.4 Görsel few-shot önceliği (Eksen B iyileştirmesi)
`retriever.py` few-shot seçiminde görsel tipli gerçek örnekler, sentetik SVG örneklerine göre
**kaynak-önceliği** alır (`source` prefix `questions/` > `synthetic`). Böylece görsel kazanımlarda
gerçek şekiller few-shot'a daha sık girer. (Küçük skorlama ayarı, opsiyonel ilk turda.)

---

## 5. Fazlar ve geliştirme sırası

| Faz | İş | Çıktı | Doğrulama |
|---|---|---|---|
| **0** | manifest iskeletleri (5/6/7) + `_resolve_grade_dir` helper + `.gitignore` büyük PDF | 3 manifest | dosya adı→track elle teyit |
| **1** | `extract_questions.py` genelleme (4.1) + LGS shim regression | yeni script | grade-8 hâlâ çalışır (smoke) |
| **2** | **5. sınıf PİLOT** — `--grade 5 --limit 1` → tüm questions track | `questions_grade5.json` | maliyet + görsel başarı oranı ölç |
| **3** | Kalite katmanı: math_verifier + critic + `is_valid_svg` kapısı + kazanım doğrula | temiz JSON | review kuyruğu boyutu |
| **4** | Ingest + **altın çıpa küratörlüğü** (insan spot-check, görsel kazanımlarda ≥2 SVG çıpa) | `grade_5.py` güncellenir | retriever gerçek few-shot çekiyor mu (log) |
| **5** | **Önce/sonra kör kıyas** — 10 kazanım, 5'er soru, "sınavda çıkar gibi mi?" | kalite raporu | LaTeX + SVG render göz teyidi |
| **6** | 6, 7 paralel (pilot kanıtlanırsa) → ChromaDB commit → frontend-ci yeşil → merge | canlı | Vercel preview teyidi |

**Yürütme ilkesi:** her sınıf bağımsız resumable (`stable_id` ile mükerrer eleme); 5. sınıf
pilotu uçtan uca bitmeden 6-7'ye geçilmez (maliyet/kalite önce ölçülür).

---

## 6. Maliyet (5-6-7, tek temiz koşu)

> Flash giriş ~$0.30/1M, çıkış ~$2.50/1M; embedding ~$0.15/1M. ~400-500 soru/sınıf, %35-45 görselli (6-7 yoğun).

| Kalem | ~Maliyet |
|---|---|
| Vision soru çıkarımı (3 sınıf) | ~$15-20 |
| Görsel SVG 2. çağrı (%40, 6-7 ağır) | ~$10-12 |
| Çözüm sentezi (çözümsüzler) | ~$2-3 |
| Doğrulama (SymPy ücretsiz + critic) | ~$2-3 |
| Embedding ingest | ~$1 |
| **Compute toplam** | **~$30-39** |
| **+ iterasyon (resumable)** | **~$50-70** |
| **İnsan küratörlük (altın çıpa, Faz 4)** | **~5-7 saat** (görsel teyidi dahil) |

---

## 7. Riskler ve azaltma

1. **Görsel sadakat (en büyük risk, 6-7 geometri yoğun):** karmaşık şekil/fotoğraf SVG'ye
   çevrilemez → `is_valid_svg` kapısı + review kuyruğu; çevrilemeyen metin bağlamı olarak kalır.
2. **Bozuk SVG few-shot'a sızması:** 3.3 kapısı zorunlu (yoksa Eksen B model bozuk SVG taklit eder).
3. **Kazanım yanlış etiket:** dosya-adı `kazanim_hint` + `CURRICULUM[grade]` doğrulama; null → düşük confidence.
4. **Mükerrer dosyalar** (`mat6` = `mat6 (1)`): manifest `skip` + `stable_id` dedup.
5. **Devasa textbook PDF'ler** (90-140MB): questions track'ten ayrı, sonraya; bellek için sayfa-stream.
6. **Folder casing İ/ı:** Faz 0 `_resolve_grade_dir` şart (Windows + Türkçe locale).
7. **Telif:** açık-kaynak; few-shot örnek olarak öğretilir, diversity penalty + semantik dedup
   ile 1:1 üretim mimari olarak engellenir.

---

## 8. Geliştirmeye başlangıç — ilk somut adımlar
1. **Faz 0:** 5/6/7 klasörlerine `manifest.json` (dosya adından track + kazanim_hint önerisi, insan teyidi).
2. **Faz 1:** `extract_questions.py` (genelleme + çok-format şema + görsel kapısı + LGS shim).
3. **Faz 2:** 5. sınıf pilot `--limit 1` → çıktı + görsel başarı oranını incele → tam koşu kararı.
