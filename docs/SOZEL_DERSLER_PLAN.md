# Sözel Dersler Genişleme Planı — Türkçe · Sosyal/İnkılap · İngilizce

> Durum: **Plan taslağı, onay bekliyor.** Tarih: 2026-07-10
> Kapsam: Matematik + Fen'den sonra **3 yeni ders** — Türkçe, Sosyal Bilgiler
> (+ Hayat Bilgisi + 8. sınıf T.C. İnkılap Tarihi), İngilizce.
> Temel: Fen dikey dilimi (`docs/FEN_BILIMLERI_PLAN.md`) uçtan uca **kanıtlandı**
> (subject ekseni + içerik hattı + görsel + pipeline + frontend). Bu 3 ders o
> şablonun tekrarıdır — ama her birinin **kendine özgü mimari yeniliği** var.
> İlke: her ders **flag arkasında**, **matematik/fen paritesine gelene kadar
> canlıda kapalı** (bkz. kalite kapısı). Aynı anda hepsini açmaya çalışma —
> sırayla dikey dilim.

## DURUM — Ortak altyapı + İngilizce TAMAM (2026-07-10)
- ✅ **Ortak altyapı:** SubjectId'e Türkçe/Sosyal/İngilizce; QuestionType'a 8 sözel tip;
  3 feature flag; registry genelleştirildi (`subject_enabled` settings-canlı +
  `get_content_module`); **agent.generate plugin-driven** (fen-özel → generic non-math,
  fen HTTP 200 ile doğrulandı); router'lar (worksheets/quizzes/curriculum/regenerate)
  generic non-math kapısı. Math/fen regresyonsuz (62/62).
- ✅ **İngilizce:** `derive_ingilizce_curriculum.py` → 2-8. sınıf, 49 tema, 1192
  beceri-çıktısı (ENG.{sınıf}.{tema}.{beceri}); prompt (İngilizce çıktı, CEFR A1-A2,
  QUESTION_ANALYSIS çeldirici desenleri) + critic (dilbilgisi+seviye) + plugin.
  difficulty_hints = generic seviye-bazlı (per-kazanım DEĞİL — 1192 çıktı). few-shot
  MVP boş. **Gerçek üretim doğrulandı:** grade 5 (A1) + grade 8 (A2), 6/6 soru
  dilbilgisel doğru + seviye-uygun + tek cevap; **özgün okuma pasajı üretimi çalışıyor**;
  Markdown tablo + NOT kalıbı. flag-gated (canlıda kapalı).
- ✅ **Sosyal Bilgiler TAMAM (2026-07-10):** `derive_sosyal_curriculum.py` → 3 program
  birleşik (Hayat Bilgisi 1-3 + Sosyal Bilgiler 4-7 + İnkılap 8), **46 ünite, 151
  kazanım** (HB/SB/İTA kodları; adlar+metinler temiz). prompt (tarihsel/coğrafi olgu
  doğruluğu + anakronizm yasağı) + critic (olgu doğruluğu) + plugin. difficulty_hints
  generic, few-shot MVP boş. **Gerçek üretim: 9/9 tarihsel/olgusal doğru** —
  Mondros (30 Ekim 1918), Amasya Genelgesi (22 Haziran 1919, gerçek maddeler),
  Tekalif-i Milliye (Kütahya-Eskişehir sonrası), Karadeniz Tahıl Girişimi (2022);
  kaynak_metin gerçek belge üretiyor. flag-gated.
- ✅ **Türkçe TAMAM (2026-07-10, PRAGMATİK MODEL A):** üniteler = temalar (çıkarıldı;
  ilkokul adlı, ortaokul "N. Tema"), kazanımlar = sınıf düzeyi çekirdek yetkinlikler
  (okuma-anlama/sözcük/cümle/yazım/noktalama/metin — kısmen elle) + DYS dil bilgisi
  (çıkarıldı). prompt (özgün pasaj + NESNELLİK + dil kuralı doğruluğu) + critic + plugin.
  **Gerçek üretim: 8/8 doğru** — özgün tutarlı pasajlar, nesnel cevaplar, doğru dil
  kuralları (belgisiz sıfat, edilgen çatı, mecaz, amaç-sonuç, deyim). flag-gated.

## SONUÇ: 3 SÖZEL DERS + FEN TAMAM
Matematik + Fen + **İngilizce + Sosyal + Türkçe** = **5 ders**, hepsi plugin-driven
motorda, flag-gated (canlıda kapalı). Her biri gerçek HTTP üretimiyle doğrulandı,
matematik regresyonsuz (62/62). Yeni ders eklemek = paket (uniform arayüz) + registry.
KALAN (her ders, opsiyonel/sonraki): gerçek few-shot, görsel realia, parite
karşılaştırması, frontend'de görünürlük (flag), kademeli go-live.

## 0. Ne HAZIR, ne YENİ

**HAZIR (Fen'den, tekrar kullanılacak — sıfır iş):**
- Ders ekseni: `SubjectId` enum + `app/subjects/` plugin registry + `get_subject`.
- İçerik hattı deseni: `curriculum.py` (üretici script) + `difficulty_hints.py`
  (paralel Claude alt-ajanı) + `prompt.py`/`critic.py`/`few_shot.py`.
- Pipeline threading: `agent.generate(subject=...)` dallanması; RAG/textbook/
  math_verifier ders-nötr atlama; router + curriculum endpoint subject param.
- Frontend: ders seçici (flag-gated) — **yeni ders enum'a girince otomatik listelenir.**
- Görselli üretim: inline SVG + `{{chart}}` + `is_valid_svg` doğrulama boru hattı.
- Kalite döngüsü + parite karşılaştırma yöntemi.

**KAYNAKLAR HAZIR (kullanıcı topladı, Fen yapısında):**
| Ders | PDF | Örnek soru | Müfredat (2024 TYMM) |
|---|---|---|---|
| Türkçe | 144 (708M) | 92 | ilkokul 1-4 + ortaokul 5-8 + soru yazım kılavuzu |
| Sosyal | 72 (392M) | 42 | Hayat Bilgisi + Sosyal Bilgiler + İnkılap Tarihi |
| İngilizce | 104 (2.2G) | 47 | öğretim programı + kılavuz + soru yazım kılavuzu |
| **Sozel_LGS** | 15 (57M) | — | **LGS sözel kitapçıkları = 8. sınıf ALTIN few-shot** |

Not: İngilizce'de hazır **`QUESTION_ANALYSIS.md`** var (MC yapısı, İngilizce
yönerge, çeldirici desenleri, crosswalk) — prompt/critic tasarımını besler.

**YENİ (Fen'de olmayan, bu derslerin gerektirdiği mimari eklemeler):**
1. **Okuma pasajı üretimi** (Türkçe, İngilizce reading, Sosyal kaynak-metin) —
   EN BÜYÜK yenilik. Model önce bir PASAJ üretmeli, sonra o pasaja bağlı N soru.
   Fen tek-soru üretiyordu; burada "paylaşılan uyaran + çoklu soru" gerekir.
2. **İngilizce-dili içerik** — prompt İngilizce çıktı üretmeli; seviye A1-A2 (sınıfa göre).
3. **Yeni soru tipleri** (enum) — sözel-özel tipler (aşağıda §4).
4. **Ders-özel doğruluk** — Sosyal: tarihsel olgu doğruluğu; Türkçe: dil kuralı +
   okuma-anlama tutarlılığı; İngilizce: dilbilgisi + seviye uygunluğu.

## 1. Ortak altyapı işi (bir kez, 3 dersi de açar)

- **Enum:** `SubjectId`'e `TURKCE`, `SOSYAL`, `INGILIZCE` ekle.
- **Plugin registry:** `app/subjects/{turkce,sosyal,ingilizce}/` paketleri + kayıt.
- **Feature flag'ler:** `Settings.{turkce,sosyal,ingilizce}_enabled` + frontend
  `NEXT_PUBLIC_*_ENABLED` (veya tek `NEXT_PUBLIC_SUBJECTS` listesi — refactor kararı).
- **Yeni soru tipleri** `QuestionType` enum'a (§4).
- **Okuma-pasajı desteği** (§5) — paylaşılan altyapı; 3 ders de kullanır.
- Curriculum endpoint + `available_subjects` bunları otomatik yansıtır.

## 2. Ders başına detaylı plan

### 2A. İNGİLİZCE (öncelik 1 — en yapılı, analiz hazır)
- **Sınıflar:** 2-8 (LGS = 8). MC ağırlıklı, İngilizce yönerge/kök.
- **Müfredat:** `ingilizce_ogretim_programi_2024_TYMM.pdf` → sınıf→ünite(tema)→
  öğrenme çıktısı; `derive_ingilizce_curriculum.py` (Fen script deseni).
- **Soru tipleri:** `coktan_secmeli` (boşluk tamamlama baskın), `diyalog_tamamlama`,
  `kelime_bilgisi`, `okuma_pasaji` (kısa metin + sorular), `gorsel_yorumlama`
  (poster/tablo/grafik realia). Dilbilgisi TERİMİ kullanma (işlev-temelli).
- **prompt.py:** İNGİLİZCE çıktı; seviye sınıfa göre (5-6: A1, 7-8: A2); yönerge
  İngilizce; çeldiriciler QUESTION_ANALYSIS'teki desenlerden (anlam-yakını,
  NOT/EXCEPT, aynı kategori). Türkçe yalnız görsel-içi realia'da çeldirici olabilir.
- **critic.py:** dilbilgisi doğruluğu + seviye uygunluğu + tek doğru cevap + İngilizce akıcılık.
- **few-shot:** 8. sınıf EBA (cevap anahtarlı) + Sozel_LGS İngilizce bölümü = altın.
  ⚠️ 5-7 eski (2018) tema adları → TYMM crosswalk (QUESTION_ANALYSIS §6).
- **Rendering:** metin + poster/chart (SVG/`{{chart}}`). Görsel realia orta.
- **Özel risk:** İngilizce üretimde dil hatası (critic + few-shot çıpası kritik);
  seviye kayması (A2'yi aşan kelime).

### 2B. SOSYAL BİLGİLER / İNKILAP (öncelik 2 — Fen'e en benzer: olgusal)
- **Sınıflar & 3 program:** Hayat Bilgisi 1-3, Sosyal Bilgiler 4-7, **8. sınıf
  T.C. İnkılap Tarihi ve Atatürkçülük (LGS)**. Üç ayrı 2024 TYMM programı.
  Karar: tek `sosyal` subject altında sınıfa göre program seç, VEYA `sosyal` +
  `inkilap` ayrı subject. **Öneri:** tek `sosyal` (sınıf→program otomatik).
- **Soru tipleri:** `coktan_secmeli` (olgu + neden-sonuç), `kronoloji` (sıralama),
  `harita_yorumlama`, `kaynak_metin` (tarihi metin/belge + soru), `tablo_grafik`.
- **prompt.py:** MEB tonunda; **tarihsel/coğrafi olgu doğruluğu MUTLAK** (Fen'in
  bilimsel doğruluğunun karşılığı); tarih/olay/kişi doğru; anakronizm yasak.
- **critic.py:** tarihsel olgu doğruluğu + kaynak-soru tutarlılığı + kazanım uyumu.
- **few-shot:** 8. sınıf İnkılap → Sozel_LGS + EBA örnek sorular = altın. 5-7 Sosyal
  EBA örnek soruları.
- **Rendering:** metin + **basit harita/zaman şeridi** (inline SVG) + tablo. Karmaşık
  detaylı harita → ERTELE (Fen'in karmaşık diyagram kararı gibi); metinle betimle.
- **Özel risk:** tarih hatası/anakronizm; harita SVG'nin coğrafi doğruluğu.

### 2C. TÜRKÇE (öncelik 3 — EN ZOR: okuma pasajı)
- **Sınıflar:** 1-8 (ortaokul 5-8 = LGS ağırlık). 2024 TYMM ilkokul + ortaokul.
- **Soru tipleri:** `okuma_pasaji` (paragraf — LGS'nin kalbi), `sozcukte_anlam`,
  `cumlede_anlam`, `yazim_noktalama`, `dil_bilgisi`, `sozel_mantik`,
  `gorsel_grafik_yorumlama`, `coktan_secmeli`.
- **EN KRİTİK yenilik — ÖZGÜN PASAJ ÜRETİMİ:** LGS Türkçe paragraf-yoğun; pasajlar
  telifli → KOPYALANAMAZ. Model **özgün, sınıf-seviyesine uygun paragraf** üretip
  üzerine soru sormalı. Bu, §5 okuma-pasajı altyapısının en yoğun kullanıcısı.
- **prompt.py:** MEB Türkçesi; pasaj tutarlı/özgün/seviyeye uygun; soru pasajdan
  cevaplanabilir; yazım-noktalama sorularında kural net.
- **critic.py:** dil kuralı doğruluğu + pasaj-soru tutarlılığı (cevap gerçekten
  pasajdan çıkıyor mu?) + tek doğru cevap + öznellik kontrolü (yoruma açık soru elenmeli).
- **few-shot:** 8. sınıf Sozel_LGS Türkçe bölümü + EBA örnek sorular. Pasaj-yoğun
  örnekler stil çıpası.
- **Rendering:** uzun metin (Markdown), tablo, bazı grafik/görsel. SVG az.
- **Özel risk:** pasaj özgünlüğü/kalitesi; okuma-anlama cevabının nesnelliği (en zor
  kalite kapısı); yazım-noktalama kurallarının hatasızlığı.

## 3. LGS Sözel altın kaynağı (`Sozel_LGS/`)
15 LGS kitapçığının **sözel bölümü** (Türkçe + İnkılap + Din + İngilizce). 8. sınıf
few-shot için altın (gerçek sınav kalitesi). İşleme:
- Metin-çıkarılabilir mi + görselli mi test et (Fen'deki gibi fitz render → oku).
- Ders bölümlerine ayır (Türkçe/İnkılap/İngilizce), kazanıma etiketle (crosswalk).
- Görselli sözel sorular (grafik/tablo/görsel yorumlama) → SVG/tablo reprodüksiyon;
  görsel-şıklı olanlar review kuyruğu (Fen deneyimi).

## 4. Yeni QuestionType enum eklemeleri
Ders-nötr adlandır (birden çok ders paylaşır):
`okuma_pasaji`, `diyalog_tamamlama`, `kelime_bilgisi` (sözcük/vocab),
`kronoloji` (sıralama zaten var → yeniden kullan), `harita_yorumlama`,
`kaynak_metin`, `dil_bilgisi`, `yazim_noktalama`, `gorsel_yorumlama`.
Mevcut genel tipler (`coktan_secmeli`, `dogru_yanlis`, `bosluk_doldurma`,
`eslestirme`, `tablo_sorusu`, `grafik_okuma`) tümünde yeniden kullanılır.

## 5. Okuma-pasajı altyapısı (yeni, paylaşılan) — EN BÜYÜK MİMARİ İŞ
Sorun: Türkçe/İngilizce/Sosyal'de birden çok soru AYNI pasaja/uyarana bağlı olabilir;
mevcut şema tek-soru bazlı (`Question` bağımsız). Seçenekler:
- **(A) Self-contained pasaj:** her `okuma_pasaji` sorusu KENDİ kısa pasajını
  `question` alanına gömer (pasaj + tek soru). En basit; mevcut şemayı bozmaz.
  **Öneri: MVP için A.**
- **(B) Paylaşılan uyaran:** `Worksheet`'e opsiyonel `passages[]` + soru→passage_id.
  Şema + PDF render + quiz + frontend değişikliği gerektirir (büyük). Faz 2.
- Karar: A ile başla (hızlı, izole), gerekirse B'ye geç.

## 6. Önerilen sıralama (dikey dilim, sırayla)
1. **Ortak altyapı** (enum + registry + flag + yeni tipler + okuma-pasajı A). ~2-3 gün.
2. **İngilizce** — en yapılı, analiz hazır, MC. Şablonu ilk burada tekrar et,
   sözel-özel akış (İngilizce prompt, okuma_pasajı) burada olgunlaşsın. ~1.5-2 hafta.
3. **Sosyal/İnkılap** — Fen'e en benzer (olgusal). ~1-1.5 hafta.
4. **Türkçe** — en zor (pasaj + nesnellik). En sona; önceki derslerden öğrenilen
   pasaj/critic olgunluğuyla. ~2-3 hafta.
Her ders: içerik hattı (curriculum→difficulty_hints→prompt/critic/few-shot) →
pipeline (zaten dallı) → kalite döngüsü → parite → flag-gated.

## 7. Ders başına içerik hattı (Fen şablonu — her ders tekrarlar)
1. `scripts/derive_<ders>_curriculum.py` → `app/subjects/<ders>/curriculum.py`
   (2024 TYMM'den, LLM'siz PyMuPDF). Ünite bazlı.
2. `difficulty_hints.py` — paralel Claude alt-ajanı (sınıf başına), merkezi doğrulama.
3. `prompt.py` + `critic.py` — ders-özel (yukarıdaki özellikler).
4. `few_shot.py` — GERÇEK MEB/LGS soruları (EBA + Sozel_LGS), kazanıma etiketli,
   cevap elle doğrulanmış; metin + görselli. Crosswalk gereken yerde uygula.
5. Görselli few-shot: fitz render → Claude okur → SVG/tablo/{{chart}} reprodüksiyon.

## 8. Kalite kapısı (her ders, Fen'le aynı ilke)
- `<ders>_enabled=False` → canlıda kapalı, flag arkasında.
- Metin + görsel **parite karşılaştırması** (matematik/fen ile) — üret, oku, kıyasla.
- Ders-özel parite ölçütü: İngilizce=dil doğruluğu; Sosyal=tarihsel doğruluk;
  Türkçe=pasaj kalitesi + cevap nesnelliği.
- Parite geçmeden go-live YOK. Kademeli açılış (flag → SEO).

## 9. Kaba efor
- Ortak altyapı: ~2-3 gün.
- İngilizce: ~1.5-2 hafta · Sosyal: ~1-1.5 hafta · Türkçe: ~2-3 hafta.
- Kalite döngüleri açık uçlu (parite hedefli).
- Toplam ~6-9 hafta (sıralı); ortak altyapı sonrası dersler kısmen paralelleşebilir.

## 10. Riskler (özet)
1. **Pasaj özgünlüğü/kalitesi** (Türkçe, İngilizce) — okuma-anlama üretiminin kalbi.
2. **Nesnellik** (Türkçe okuma-anlama) — yoruma açık soru = kötü kalite; critic elemeli.
3. **Tarihsel doğruluk** (Sosyal) — anakronizm/hata; critic + few-shot çıpası.
4. **İngilizce dil hatası / seviye kayması** — critic + seviye kuralları.
5. **Crosswalk** — 5-7 EBA eski müfredat üniteleri ↔ 2024 TYMM (İngilizce'de doğrulandı).
6. **Görsel-şıklı sözel sorular** — metne çevrilemez → review kuyruğu (Fen deneyimi).
7. **Kapsam dağılması** — 3 dersi paralel açma cazibesi; ANTI: sırayla dikey dilim.
