# Kullanıcı Bulguları — Çözüm Planı (2026-07)

> Durum: **PLAN** (onaylı netleştirmelerle güncellendi). Geliştirme henüz başlamadı.
> Kaynak: kullanıcı saha bulguları + 4 netleştirme cevabı.

Bulgular 3 doğaya ayrılır: **(a) hızlı copy/metin**, **(b) veri/müfredat doğruluğu**,
**(c) içerik-kalite & olgusal doğruluk + yeni özellikler**. Bu bir eğitim ürünü olduğu
için **olgusal doğruluk (WS-5) en yüksek önceliktir** — yanlış bilgi güveni bitirir.

Netleştirme cevapları (2026-07):
- **#A →** "Konular" sekmesindeki eşleştirme, **üretimde kullandığımız tema/kazanım verisiyle** hizalanacak (tek kaynak).
- **#B →** "Açık uçlu" tipi **Çöz & Geliş'e de** eklenecek; üretim yaklaşımı zaten doğru.
- **#C →** Sosyal Bilgiler'de **"beşerî" (î şapkalı)** cevabı sorun çıkarıyordu → şapka (circumflex) normalizasyonu.
- **#D →** Hesap başına **en fazla 3 cihaz** girişi (şimdilik yeterli).

---

## WS-1 — Marka & metin sadeleştirme (copy)
Bulgular: 1, 4, 5, 6, 7, 8, 9, 10, 14, 19, 20, 21, 22 · **Efor: ~yarım gün, tek PR, düşük risk**

| Bulgu | Değişim | Yer |
|---|---|---|
| 1 | "MEB **matematik** çalışma kağıdı üretici" → çok-ders (matematiği koruyup genişlet) | `app/layout.tsx` title/desc/keywords, `opengraph-image.tsx`, `manifest.ts` |
| 4/19 | "sınıf ve konu seçin" → **"sınıf, ders ve kazanımı seçin"** | `app/page.tsx` Hero + STEPS[0], `practice/new` |
| 5 | "Artık tek ders değil" kalksın → sıfırdan çok-ders üretiyoruz dili (ör. "Dersini seç, ürettiğimiz soruları gör") | `components/SubjectShowroom.tsx` |
| 6 | "Hazır PDF" → **"hazırlanan PDF"** (tüm geçişler) | `page.tsx`, features |
| 7 | Ucu açık ifadeler → somut ("sistemin ürettiklerinden **bir kesit**") | `page.tsx` Showroom/SystemSummary |
| 8/9/10 | "**test gibi çöz**" kavramı kalksın → sade **Üret & Çöz**; çöz bölümünde net üçlü akış (**Üret → Çöz → Geliş**) | `page.tsx` SolveAndGrow/SOLVE_FEATURES, `manifest.ts`, `practice/layout.tsx`, `q/layout.tsx` |
| 14/21/22 | Süre dili tek biçim: **"saniyeler içinde hazırlar"**; "30 saniye" ve "5 dakika" kalksın | `page.tsx` SystemSummary/STEPS[2]/FinalCta, SolveForm & QuestionPreview bekleme ekranı |
| 20 | "her birinin **matematiğini** kontrol eder" → **"içeriğini/doğruluğunu"** | `page.tsx` STEPS[1] (bunu ilk turda atlamıştım) |

**SEO notu:** `layout.tsx`/OG/manifest global SEO metnidir; ana sayfa hâlâ "matematik"te sıralanıyor.
Formül: "MEB çalışma kağıdı üretici — Matematik, Fen, Türkçe, Sosyal, İngilizce" (matematiği çıkarmadan). SEO turuyla koordine.

---

## WS-2 — Ana sayfa örnek/vitrin çeşitlendirme
Bulgular: 3, 16 · **Efor: ~1 gün (SEO route'ları hariç)**

- **3:** Örnek soru havuzunu **ders başına 3-5 gerçek örneğe** çıkar (`lib/subject-showcase.ts`). Çok-ders açıkken math-only `Showroom` fallback'i devre dışı.
- **16:** `BrowseByGrade`/`GRADE_HUBS` ders bazında çeşitlensin — **hedef route'lar (`/x-sinif-fen` vb.) SEO turunda açılınca** kartlar çoğalır (bağımlılık).

---

## WS-3 — "Konular" sekmesi ↔ üretim müfredatı hizalama  ⚠️ (netleştirildi: #A)
Bulgular: 17, 18 · **Efor: ~1-2 gün + denetim**

**Kök neden:** "Konular" sekmesi (`/calismalar`, `CURRICULUM_PAGES`/`kazanimlar.json` — eski `M.*` topic yapısı) ile
**üretimde kullanılan tema/kazanım verisi** (`units.json` `MAT.*` + `app/subjects/*/curriculum.py`) **birbirinden ayrık** ve kaymış.
Sonuç: konu ↔ sınıf eşleşmeleri ve detaylı anlatımlar yanlış görünüyor.

**Plan:**
1. "Konular" sekmesini **tek kaynaktan** besle: üretimin kullandığı **ünite/tema + kazanım** verisi (ders bazında).
2. Eski legacy topic listesini (drift kaynağı) bu kaynağa **köprüle veya emekliye ayır**.
3. Kod ↔ sınıf ↔ ad ↔ ders tutarlılığını denetleyen **doğrulama script'i** (CI'a bağlanabilir).
4. Not: SEO landing sayfaları da `CURRICULUM_PAGES`'ten besleniyor → bu birleştirme SEO turuyla ortak.

---

## WS-4 — Quiz/çöz akışı: "Açık uçlu" tipi  (netleştirildi: #B)
Bulgular: 23 + #B · **Efor: ~1-2 gün**

- "İşlem / Sayısal sonuç" (`salt_islem`) → **"Açık uçlu"** olarak yeniden konumlandır ve **Çöz & Geliş'e ekle** (üretim yaklaşımı zaten doğru).
- Açık uçlu otomatik puanlanamaz → **öz-değerlendirme akışı:** öğrenci çözer → "Cevabı gör" → kendisi **doğru/yanlış** işaretler.
- Gösterge ayrımı: öz-değerlendirmeli sonuçlar ilerleme/istatistikte **ayrı etiketlenir** (otomatik puanla karışmasın; mastery'ye "öz-beyan" olarak sayılır).
- Dokunulacak: `SolveForm` SOLVABLE_TYPES (etiket "Açık uçlu"), `QuizSolver` (öz-değerlendirme UI), `grading.py` (açık uçlu → öz-beyan), `schemas` (attempt alanı).

---

## WS-5 — İçerik kalitesi & OLGUSAL DOĞRULUK ⭐ (en yüksek öncelik)
Bulgular: 2 (#C), 25, 26, 27, 24

- **25 (saatler):** "Bunu biliyor musun?" Fen bilgisinde **ağırlık/kütle** karışıyor (ör. "Ay'da 60 kg → 10 kg" hatalı). `lib/subjectFacts.ts` FEN_FACTS'i bilimsel doğrulukla elden geçir; kütle (kg) ↔ ağırlık (N) ayrımını koru.
- **26 (asıl iş, birkaç gün):** Üretilen sorularda **olgusal hata** (ör. "hücre duvarı yalnız bitkilerde" — mantar/bakteride de var). Hedef: **sıfıra yakın**.
  1. **En güncel MEB ders kitaplarını RAG kaynağına** al (özellikle Fen); üretim + kritik bu bağlamı çeksin.
  2. **Olgusal doğruluk kritik pass'i** (kazanım-uyumu kritiğinden ayrı, ders-özel): "yaygın yanlış bilgi" kontrol listesiyle (hücre duvarı, kütle-ağırlık, fiziksel-kimyasal değişim, ısı-sıcaklık, iletken-yalıtkan…).
  3. Şüpheli soruyu **ele + yeniden üret** (mevcut over-generation + top-up hattına bağla).
  4. **Olgusal eval seti** (bilinen tuzaklar) kur; regresyonu ölç.
- **27:** "Öncüller I-II-III / 1-2-3-4" veya "yukarıdaki tabloya/görsele göre" diyen ama **o öğeyi içermeyen** sorular. **Bütünlük kontrolü** (enforcement + kritik): atıf yapılan öncül/tablo/görsel metinde **fiilen var mı**; yoksa ele. (Görsel için kural var → metinsel öncüle genişlet.)
- **2 / #C (şapka normalizasyonu):** Sosyal'de **"beşerî" (î şapkalı)** cevabı, kullanıcının "beşeri" girişiyle eşleşmiyordu. **Çözüm:** cevap karşılaştırmasında **circumflex kıvrımını kaldır** (î→i, â→a, û→u) + boşluk/büyük-küçük normalize (`grading.py::_normalize_text`, boşluk-doldurma & açık uçlu öz-değerlendirme). Gösterimde tutarlı biçim seç. Aynı normalizasyonu benzer kelimelerde de uygula.
- **24 (doğrulama + güvence):** "Örnekleri birebir kopyalamıyor değil mi?" → Hayır, few-shot **stil referansıdır**, prompt "kopyalama" der. **Güvence:** üretileni few-shot havuzuna karşı da **semantik benzerlik kontrolünden** geçir; çok benzerse ele.

**Efor:** 25 → saatler; 2 → saatler; 26/27 → birkaç gün (RAG + kritik + eval).

---

## WS-6 — Yeni özellikler
Bulgular: 11, 12, 15

- **11 — AI haftalık çalışma programı (eksiklere göre):** İlerleme panosundaki zayıf kazanımlardan gün-gün plan üret (ders/konu, soru sayısı, hedef) + tek-tıkla o kazanımda quiz. Girdi = mastery/weak (mevcut). **Efor: orta.** İlerleme paneline doğal ek.
- **12 — Rol-bazlı profiller (öğrenci/öğretmen/veli):** Rolü kullanıcı profiline (Clerk metadata) yaz; ekran/menü role göre. Öğrenci→çöz&geliş; Öğretmen→sınıf/ödev/rapor; Veli→çocuğun ilerlemesi (veli↔öğrenci bağı). **Efor: orta-yüksek**, mimari karar.
- **15 — Word (.docx) export (premium):** PDF yanına düzenlenebilir .docx; premium kapısı. **Efor: orta.** WS-7 premium modeline bağlı.

---

## WS-7 — Erişim kontrolü & premium  (netleştirildi: #D)
Bulgular: 13 + #D, 15

- **13 — Cihaz tavanı = 3:** Hesap başına **en fazla 3 farklı cihazdan** giriş. 4. cihaz gelince **en eski cihazı düşür** (ya da engelle + "cihaz limiti" uyarısı). Uygulama: tenant başına cihaz/oturum parmak-izi kaydı; Clerk oturum yönetimiyle veya kendi tablomuzla. Ağır DRM yok — 3 cihaz makul, paylaşımı sınırlar.
- **Premium/entitlement modeli:** WS-6 (word), WS-4, kota → hepsi bir **plan/entitlement** modeline dayanıyor; bu WS-6/7 önkoşulu. Ödeme sistemi konuşmasıyla birleşir.
- **Efor: yüksek** (kimlik/oturum + faturalama kancası).

---

## Önerilen faz sıralaması

1. **Faz A — Hızlı kazanım (~1 PR):** WS-1 (tüm copy) + WS-5.25 (fen fact) + WS-5.2 (şapka normalizasyonu). Görünür, düşük risk.
2. **Faz B — Kalite (kritik):** WS-5.26/27 (olgusal doğruluk + öncül bütünlüğü) + eval seti. Ürün güveni.
3. **Faz C — Doğruluk & akış:** WS-3 (Konular↔üretim hizalama) + WS-2 (vitrin) + WS-4 (açık uçlu çöz&geliş).
4. **Faz D — Özellikler:** WS-6 (çalışma programı → word → profiller) + WS-7 (cihaz tavanı + premium). Ödeme konuşmasıyla.

---

## Açık kalan (küçük) noktalar
- WS-3 denetimi somut yanlış örnekleri ortaya çıkaracak; büyük sürprizler çıkarsa faz revize edilir.
- WS-6/7 premium/ödeme modeli netleşmeden word-export ve cihaz-tavanı faturalama tarafı beklemede.
