# Soru Atölyesi — Etkileşimli Öğrenme Platformu Planı

> Durum: **Tasarım / hizalama** (2026-06). Henüz inşa başlamadı.
> Bu doküman, "çalışma kağıdı üreteci" → "etkileşimli öğrenme/değerlendirme
> platformu" evriminin tek doğru kaynağıdır. Kararlar birlikte alındı (aşağıda).

---

## 1. Vizyon — kapalı öğrenme döngüsü

Bugün ürün tek halkalı: **üret → (PDF) çıktı**. Hedef, döngüyü kapatmak:

```
üret  →  çöz (platformda)  →  otomatik puanla  →  kazanım-bazlı eksik göster
  ↑                                                          │
  └──────────────  hedefli yeniden üretim  ←─────────────────┘
```

Bu, tek seferlik aracı **günlük kullanılan öğrenme ortamına** çevirir; retention
ve kazanım-bazlı öğrenme verisi (kopyalanamaz veri hendeği) yaratır.

---

## 2. Birlikte alınan kararlar (bağlayıcı)

1. **Otomatik puanlama, öz-değerlendirme YOK.** Öğrenci cevabı sistemce doğru/yanlış
   olarak ölçülür; "kendin işaretle" yaklaşımı kullanılmaz.
2. **Sonucu: çözülebilir quiz'ler yalnız otomatik-puanlanabilir tiplerden oluşur**
   (çoktan seçmeli, doğru/yanlış, boşluk doldurma, sayısal/salt işlem, eşleştirme,
   sıralama). Açık-uçlu sözel sorular **PDF kağıt** modunda kalır (çözme modunda
   sunulmaz).
3. **Puanlama LLM'siz**: normalizasyon + SymPy denkliği + yapısal eşleşme.
   Etkileşim başına maliyet ~$0.
4. **Öğrenci hem kendi ürettiğini hem kendisine paylaşılanı çözebilir.**
5. **Paylaşım: önce link/kod, hemen ardından uygulama-içi (kullanıcı→kullanıcı).**
   Paylaşan, kime paylaştığını ve sonuçlarını profil/liste olarak görür.
6. **Eksik analizi = kazanım-bazlı doğru/yanlış sayımı** (LLM gerektirmez).
   Gelişmiş AI "kavram yanılgısı" raporu opsiyonel üst-katman, sonraya bırakıldı.
7. **Hesap modeli: birleşik** — her kullanıcı hem üretir/paylaşır hem çözer.
   "Öğretmen yüzü" (paylaştıklarım + sonuçlar) ve "öğrenci yüzü" (bana
   paylaşılanlar + puan/seviye) aynı hesabın iki görünümüdür. (İleride sertleşmiş
   rol gerekirse Clerk metadata ile eklenir.)

---

## 3. Yeniden kullanılabilir mevcut altyapı (pivotun kolaylığı)

| Mevcut | Bu plana katkısı |
|---|---|
| Her soruda `kazanim_kod` | Kazanım-bazlı eksik/ustalık izleme — doğuştan |
| Otomatik-puanlanabilir tipler (`coktan_secmeli`, `dogru_yanlis`, `bosluk_doldurma`, `eslestirme`, `siralama`, `salt_islem`) | Çözülebilir quiz arzı |
| Her soruda `answer` + `solution_steps` | Anında geri bildirim + çözüm gösterimi |
| `math_verifier` (SymPy) | Sayısal cevap denkliği — LLM'siz puanlama |
| Üretim hattı `kazanim_kod` hedefleyebiliyor | Hedefli yeniden üretim (öneri aktüatörü) |
| Clerk kullanıcı + Turso kalıcı | Kullanıcı, attempt, sonuç saklama |
| Generation cache + warming | Soru arzı maliyeti ~$0 |

**Eksik olan tek katman:** çözme + puanlama + paylaşım + sonuç izleme. Greenfield.

---

## 4. Çekirdek kavramlar

- **Quiz (Assignment):** üretilmiş, çözülebilir bir soru kümesi. Kaynağı: kullanıcının
  kendi ürettiği VEYA kendisine paylaşılan. Yalnız otomatik-puanlanabilir tipler.
- **Share (Paylaşım):** bir quiz'in link/kod ile veya uygulama-içi belirli
  kullanıcı(lar)la paylaşılması.
- **Attempt (Çözüm denemesi):** bir kullanıcının bir quiz'i çözmesi; soru-soru
  verdiği cevap, doğru/yanlış, süre.
- **Result (Sonuç):** bir quiz için toplu skor (doğru/toplam, süre, kazanım kırılımı).
  Paylaşan kullanıcı, paylaştığı herkesin sonuçlarını görür.
- **Mastery-lite:** kullanıcı × kazanım bazında doğru oranı (saf sayım).
- **Gamification:** XP/puan, seviye, günlük streak, kazanım/konu rozetleri.

---

## 5. Otomatik puanlama tasarımı (LLM yok)

Soru tipi → puanlama stratejisi:

| Tip | Strateji |
|---|---|
| `coktan_secmeli` | Seçilen şık == doğru şık (yapısal) |
| `dogru_yanlis` | Normalize string eşleşme (Doğru/Yanlış) |
| `bosluk_doldurma` | Boşluk(lar) normalize eşleşme (çoklu boşluk sıralı) |
| `salt_islem` / sayısal | **SymPy denkliği** + normalizasyon (1/2 ≡ 0.5 ≡ 0,5) |
| `eslestirme` | Çift kümesi eşitliği (yapısal) |
| `siralama` | Sıra eşitliği (yapısal) |

**Normalizasyon kuralları:** boşluk/büyük-küçük harf, Türkçe ondalık virgül↔nokta,
birim ekleri ("5 elma"→"5"), kesir/ondalık denkliği (SymPy). Hedef: doğru cevabın
makul varyasyonlarını doğru saymak (false-negative = güven kaybı).

### ⚠️ Kritik teknik iş: yapısal cevap şeması
Şu an soru `question: str` (şıklar metne gömülü) + `answer: str`. Etkileşimli çözme
+ güvenilir otomatik puanlama için **yapısal alanlar** gerekir:
- `coktan_secmeli` → `options: [str]`, `correct_index: int`
- `bosluk_doldurma` → `blanks: [str]`
- `eslestirme` → `pairs: [[sol, sağ]]`
- `siralama` → `correct_order: [str]`

İki seçenek: **(A)** çözme anında metinden parse et (kırılgan), **(B)** üretim çıktı
şemasını bu alanlarla genişlet (sağlam, önerilen). → **(B)**: `GeneratedQuestion`
şemasına opsiyonel yapısal alanlar eklenir; sadece çözme modu için üretimde
doldurulur. PDF akışı etkilenmez.

---

## 6. Veri modeli (Turso / libSQL — `db_connection.connect`, `worksheet_history` deseni)

```
quizzes
  id, owner_tenant_id, title, grade, topic_id, difficulty,
  questions_json (yapısal sorular+cevaplar), created_at

shares
  id, quiz_id, owner_tenant_id,
  share_type ('link' | 'user'), share_code (link için),
  target_tenant_id (user paylaşımı için, nullable), created_at

attempts
  id, quiz_id, share_id (nullable), solver_tenant_id,
  answers_json (soru→verilen cevap), score, total,
  duration_seconds, per_kazanim_json, completed_at

mastery_state
  tenant_id, kazanim_kod, correct, total, last_seen_at
  (PK: tenant_id+kazanim_kod)

gamification
  tenant_id, xp, level, streak_days, last_active_date, badges_json
```

Tümü `threading.Lock` + `check_same_thread=False` ile thread-safe (mevcut desen).

---

## 7. API yüzeyi (yeni endpoint'ler)

```
POST /api/quizzes                 # üret+kaydet (çözülebilir, yapısal)
GET  /api/quizzes/{id}            # çözmek için getir (cevapsız varyant)
POST /api/quizzes/{id}/share      # link veya user paylaşımı oluştur
GET  /api/quizzes/shared-with-me  # bana paylaşılanlar (gelen kutusu)
GET  /api/shares/mine             # paylaştıklarım + alıcılar
POST /api/quizzes/{id}/attempt    # cevapları gönder → otomatik puanla → sonuç
GET  /api/shares/{id}/results     # paylaşanın gördüğü sonuç panosu
GET  /api/me/progress             # öğrenci: xp/seviye/streak + kazanım eksikleri
```

Puanlama `/attempt` içinde sunucuda yapılır (cevaplar istemciye sızmaz → kopya önlenir).

---

## 8. Frontend yüzeyler

- **Çöz ekranı:** tek tek soru, cevap gir/seç, gönder → anında doğru/yanlış +
  `solution_steps`. Sonda skor + kazanım kırılımı.
- **Öğrenci profili:** XP/seviye/streak, rozetler, "zayıf kazanımlar", geçmiş quiz'ler.
- **Gelen kutusu:** bana paylaşılan quiz'ler (çöz/çözüldü durumu).
- **Paylaşım:** quiz'ten "Paylaş" → link kopyala VEYA kullanıcı seç (uygulama-içi).
- **Sonuç panosu (paylaşan):** kim, kaç doğru, ne sürede; soru-bazlı doğruluk;
  kazanım kırılımı.
- Üretim formuna mod: **"Çözülebilir quiz"** (otomatik-puanlanabilir tipler) vs
  **"PDF kağıt"** (mevcut, açık-uçlu dahil).

---

## 9. Oyunlaştırma (hafif → genişleyebilir)

- **Puan/XP:** doğru cevap başına; zorlukla ağırlıklı.
- **Seviye:** kümülatif XP eşikleri.
- **Streak:** ardışık aktif gün; "günün quiz'i" kancası.
- **Rozet:** kazanım/konu ustalığı (ör. "Kesirler ustası").
- (İleride) **liderlik tablosu** — opt-in, sınıf/genel.

Pedagojik çapa: mastery learning + düzenli pratik. Salt süs değil.

---

## 10. Eksik analizi (LLM'siz, MVP)

`mastery_state`'ten: kullanıcının doğru oranı düşük / çok hatalı kazanımları listele
→ "Şu kazanımlarda zorlanıyorsun" + **hedefli quiz öner** (üretim hattı kazanım
alır). Saf sayım, anında, bedava.

**Opsiyonel üst-katman (sonra):** yanlış cevapları LLM'e verip *kavram yanılgısı*
çıkaran haftalık AI rapor. Batch → maliyet kontrollü. MVP'de yok.

---

## 11. Maliyet & kapasite

- Üretim: cache + warming → ~$0 (popüler kombolar ısıtılır).
- Puanlama: lokal (normalize + SymPy) → $0.
- Ustalık/eksik/oyunlaştırma: saf matematik → $0.
- LLM yalnız yeni soru üretiminde (mevcut maliyet). Etkileşim başına ek maliyet yok.
→ Free-tier'da ölçeklenebilir; büyüme push'undan önce cache warming yeterli.

---

## 12. Fazlı yol haritası

**Faz 0 — Yapısal cevap şeması** (önkoşul): üretim çıktısına gradeable yapısal alanlar.

**Faz 1 — Çöz + otomatik puanla + veri** (MVP çekirdeği):
quizzes/attempts modeli, çöz ekranı, otomatik puanlama, anında geri bildirim,
"kendi quiz'ini çöz" + skor. *(Bu, tüm zekânın beslendiği attempt verisini toplar.)*

**Faz 2 — Paylaşım (link) + sonuç panosu:** link paylaşımı, paylaşanın sonuç görünümü.

**Faz 3 — Oyunlaştırma:** XP/seviye/streak/rozet + öğrenci profili + kazanım eksikleri.

**Faz 4 — Uygulama-içi paylaşım:** kullanıcı→kullanıcı paylaşım, gelen kutusu,
"kime paylaştım" profil listesi.

**Faz 5 (opsiyonel) — AI rapor:** kavram yanılgısı analizi + haftalık rapor.

> Sıra ilkesi: **önce çözme + veri, sonra zekâ.** Veri olmadan eksik/öneri boş kalır.

---

## 13. Riskler & açık sorular

- **Kopya/cevap paylaşımı:** cevaplar sunucuda tutulur (istemciye sızmaz);
  üretim çeşitliliği + randomizasyon farklı set verir. Yine de link'le yayılan
  quiz'de risk var → not edildi.
- **Yapısal şema kalitesi:** LLM'in `options/correct_index` vb. tutarlı üretmesi
  critic ile doğrulanmalı (yanlış işaretli doğru cevap felaket).
- **Cold-start:** eksik analizi için yeterli attempt gerekir (ilk kullanımlarda
  "veri topluyoruz").
- **Rol modeli:** birleşik hesapla başlıyoruz; okul/sınıf senaryosu sertleşmiş rol
  isterse sonra.
- **Açık soru:** uygulama-içi paylaşımda kullanıcı bulma (kullanıcı adı mı,
  e-posta mı, davet mi?) — Faz 4'te netleşecek.

---

## 14. Başarı metrikleri (GA4 funnel'a bağlanır)

- Aktivasyon: ilk quiz çözme.
- Retention: streak gün sayısı, haftalık aktif çözen.
- Döngü: paylaşılan quiz → çözülme oranı.
- Öğrenme: kazanım ustalık artışı (tekrar çözümlerde doğru oranı yükseliyor mu).
- Mevcut `worksheet_generate_*` event'lerine `quiz_solve_*`, `quiz_share_*` eklenir.

---

## 15. v1 kapsam kararı (2026-06-10, bağlayıcı)

Plan sahibiyle yapılan ikinci hizalama turunda v1 kapsamı **"Kişisel Öğrenme
Döngüsü"** olarak daraltıldı. Bağlayıcı kararlar:

1. **Önce kişisel döngü, paylaşım ertelendi.** v1 = çöz → puanla → kazanım-bazlı
   eksik → hedefli öneri → ilerleme. Paylaşım (link + uygulama-içi, eski Faz 2/4)
   v1 dışında; veri/değer toplandıktan sonra eklenecek.
2. **Değerlendirme sayım-bazlı, LLM'siz.** Kazanım doğru-oranı + hedefli quiz
   önerisi. AI kavram-yanılgısı raporu (Faz 5) v1 dışında.
3. **Gelişim ekranı sade ilerleme panosu.** Kazanım ustalık %, çözülen quiz
   geçmişi, zayıf konular. XP/seviye/streak/rozet (Faz 3 oyunlaştırma) v1 dışında.

### v1 inşa sırası (her adım = ayrı PR, tek başına test edilebilir)

- **Adım 0 — Yapısal cevap şeması (ön koşul).** `Question`'a opsiyonel
  `options`/`correct_index`, `blanks`, `pairs`, `correct_order`. Yalnız çözülebilir
  tiplerde doldurulur; PDF/açık-uçlu akışı etkilenmez. Critic'e doğru-cevap
  tutarlılık kontrolü. (Bkz. §5 "yapısal cevap şeması", seçenek B.)
- **Adım 1 — Veri modeli + üret/kaydet.** Turso `quizzes`, `attempts`,
  `mastery_state` (shares/gamification YOK). `POST /api/quizzes`,
  `GET /api/quizzes/{id}` (cevapsız).
- **Adım 2 — Çöz ekranı + otomatik puanlama.** `POST /api/quizzes/{id}/attempt`
  (sunucu-taraflı normalize+SymPy+yapısal puanlama). Frontend çöz ekranı + skor +
  kazanım kırılımı. Üretim formuna "PDF kağıt" / "Site içinde çöz" modu.
- **Adım 3 — İlerleme + eksik + öneri.** `GET /api/me/progress`, ilerleme panosu,
  zayıf-kazanım → hedefli üretim önerisi.

> Ertelenenler (v1 sonrası): link/uygulama-içi paylaşım + sonuç panosu,
> oyunlaştırma (XP/seviye/streak/rozet), AI kavram-yanılgısı raporu. §7-§12'deki
> ilgili endpoint/tablolar o zaman devreye alınır.

---

## 16. Bilgi mimarisi — yüzey ayrımı (2026-06-10, bağlayıcı)

Karar: öğrenme döngüsü mevcut PDF akışına **karışmaz**; ayrı bir rotada yaşar.
"İki kapı, ortak motor": her iki yüzey aynı üretim hattını çağırır, ama zihinsel
model / çıktı / veri tabloları ayrıdır.

| | `/generate` (MEVCUT) | `/coz` (YENİ) |
|---|---|---|
| Amaç | Üret → PDF indir | Üret → Çöz → Geliş |
| Tipler | Tümü (açık-uçlu dahil) | Yalnız çözülebilir |
| Çıktı | PDF | Ekranda quiz + skor |
| Kullanım | Gel-al, tek seferlik | Kişisel, login zorunlu, kalıcı |

**Rota haritası (yeni):**
```
/coz              → hub (login zorunlu): "Yeni quiz çöz" + "İlerlemem" kartları
/coz/yeni         → sade çözülebilir-quiz üretim formu (PDF/markalama/gelişmiş ayar YOK)
/coz/quiz/[id]    → çözme ekranı: soru soru → anlık doğru/yanlış + çözüm → skor + kazanım kırılımı
/coz/ilerleme     → gelişim panosu: kazanım ustalık %, geçmiş, zayıf konular → hedefli öneri
```
`app/coz/layout.tsx` nested layout + sekme çubuğu (Çöz · İlerleme), Clerk
`<SignedIn>` ile sarılı. `app/layout.tsx`'e dokunulmaz.

**Navigasyon:** `TopNavBar.NAV_LINKS`'e `{ href: "/coz", label: "Çöz & Geliş" }`.
Landing'e ikincil CTA "Çözerek çalış →" (ana "Üret" CTA korunur). `/history`
(PDF geçmişi) ve `/coz/ilerleme` (öğrenme geçmişi) ayrı kalır.

**Form kararı: ayrı `SolveForm` — GenerateForm'a SIFIR dokunuş.** /coz için yeni,
sade bir form yazılır; sınıf/konu/kazanım seçiciyi lokal `getGradesLocal/
getTopicsLocal/getKazanimlarLocal` (curriculum.ts) besler. Ortak komponente
refactor REDDEDİLDİ (regresyon riski).

**Mevcutu bozmama sınırları (somut):** `app/generate/page.tsx`, `GenerateForm.tsx`,
`/api/worksheets/*`, `worksheet_history`, PDF render → **sıfır değişiklik**. Tek
geriye-uyumlu dokunuş: `Question`'a *opsiyonel* yapısal alanlar (eski kod/PDF
görmezden gelir). Yeni her şey izole: `/coz/*` rotaları, yeni komponentler, yeni
Turso tabloları, `/api/quizzes/*` + `/api/me/progress` endpoint'leri. `/coz`
tümüyle silinse `/generate` etkilenmez.

---

## Ek: bu doküman `implementation_plan.md`'nin ötesinde yeni bir bölümdür
Eski plan "web frontend / PDF kapsam dışı" diyordu; ikisi de artık canlı. Bu plan,
canlı ürünün üzerine **öğrenme döngüsü** katmanını tarif eder.
