# Soru Atölyesi — Büyüme & Ürün Yol Haritası (fazlı)

> Durum: **planlama** (2026-06). Canlı ürün üzerine sıralı büyüme planı.
> Kaynak: ChatGPT (conversion) + Gemini (büyüme) incelemeleri, **gerçek duruma göre
> filtrelendi** (zaten yapılmış/erken olanlar elendi). Öğrenme-platformu
> (çöz/puanla) ayrı, rafta bir track'tir → `LEARNING_PLATFORM_PLAN.md`.

## Yönlendirici ilkeler
1. **Önce traction, sonra breadth.** Mevcut kullanım küçük (~33 kayıtlı kağıt). Eksik
   olan özellik değil, **kullanım**. Var olan güçlü ürünü önce insanlara ulaştır.
2. **Ölç-yönlendir.** GA4 funnel kurulu (PR #6). Her değişikliğin dönüşüm/retention
   etkisi ölçülür — körlemesine değil.
3. **Kapasite-bilinçli.** Free-tier Gemini kota tavanı her "genişleme" fikrinin
   önünde. Scale-up öncesi cache warming + billing çözülmeli.

---

## FAZ 1 — Dönüşüm & Edinim (ŞİMDİ) · düşük efor, ölçülebilir
**Amaç:** "Güçlü motor ama showroom yok." Var olan ürünü görünür + 5 saniyede
anlaşılır kıl, dönüşümü artır.

| # | İş | Efor | Nasıl ölçülür |
|---|---|---|---|
| 1.1 | **Ana sayfa showroom revizyonu** — hero (sonuç-odaklı + öğretmen dili), 3 adım görsel (kazanım seç → üret → indir), **ana sayfaya gerçek örnek/PDF önizleme**, güçlü CTA, teknik→kullanıcı dili | S-M | GA4: ziyaret → ilk üretim dönüşümü |
| 1.2 | **Search Console'u bitir** (env meta VEYA DNS) + sitemap submit + indeks takibi | S | SC: gösterim/tıklama, indekslenen sayfa |
| 1.3 | **Gerçek-metrik social proof** (uydurma YOK; "N soru üretildi" doğruysa) | S | bounce / dönüşüm farkı |
| 1.4 | **GA4 dönüşüm baseline** (DebugView doğrula, funnel oturt) | S | baseline conversion kaydı |

**Çıkış kapısı:** funnel görünür + ziyaret→ilk-üretim oranı ölçülüyor + organik trafik
(SC) izleniyor. **Not:** 1.2 SEO ölçümünün önkoşulu, ilk bitir.

---

## FAZ 2 — Ucuz Ürün Kazanımları (Faz 1 ile paralel olabilir) · etkileşim ~$0
**Amaç:** retention + B2B'ye zemin + UX. Gemini'nin listesindeki "3 mücevher".

| # | İş | Efor | Neden |
|---|---|---|---|
| 2.1 | **White-label PDF** — header'a logo/okul/sınıf adı (footer mekanizması hazır) | S-M | Kurumsal üyeliğin kapısı; öğretmen/kurum gerçekten istiyor |
| 2.2 | **"Soruyu Değiştir"** — önizleme + soru-bazlı yeniden üret (tüm kağıdı baştan üretme) | M | UX kazancı + üretim israfını azaltır; hat zaten kazanım/tip hedefliyor |
| 2.3 | **PWA** (native değil) — kurulabilir, "WhatsApp'a at" senaryosu | S-M | PDF büyüme döngüsüyle örtüşür; düşük efor |

**Çıkış kapısı:** white-label canlı + per-question regen kullanılıyor (GA4 event).

---

## ÇAPRAZ KESİT — Kapasite & Maliyet (FAZ 3 ÖNKOŞULU)
| İş | Durum |
|---|---|
| Cache warming gerçek-popüler veriyle (GA4'ten) | script hazır (PR #7), veri bekliyor |
| Gemini billing/kota planı (free-tier tavanı) | açık |
| Cost-meter doğruluğu | düzeltildi (PR #5) → izlenebilir |

**Kapı:** Bu çözülmeden Faz 3'e (breadth/monetization) **geçme** — yoksa kota duvarı / sürpriz maliyet.

---

## FAZ 3 — Traction Sonrası Genişleme (METRİK KAPISI arkasında)
**Açılış koşulu:** anlamlı tekrarlayan kullanım (ör. haftalık aktif öğretmen eşiği +
retention trendi) **VE** kapasite çözülmüş. Koşul sağlanmadan başlama.

| # | İş | Efor | Not |
|---|---|---|---|
| 3a | **Dikey genişleme:** 8. sınıf + LGS (içerik-ağır) → sonra sözel branşlar (Türkçe okuma-anlama LLM'e çok uygun) | L | ⚠️ Sözel branşlarda SymPy aritmetik doğrulaması yok → çift-denetim moat'ının yarısı gider; critic güçlendirilmeli |
| 3b | **Monetization:** white-label üzerine B2B kurumsal/zümre paketi → pay-as-you-go kredi → (çok sonra) AI API kiralama | M-L | API kiralama ayrı bir iş; büyük sapma, en sona |
| 3c | **Öğretmen marketplace:** kamuya açık paylaşılan kağıt kütüphanesi (oylama) | L | Organik içerik + SEO + topluluk moat; **network effect ister** (boş marketplace ölü); paylaşım mekanizmasıyla örtüşür |

**Başarı metriği:** gelir, kurumsal müşteri sayısı, içerik havuzu/organik trafik.

---

## Özet — tek bakışta
- **Şimdi:** Faz 1 (dönüşüm) + Faz 2 (ucuz ürün kazanımları) paralel.
- **Sonra (kapasite çözülünce + traction gelince):** Faz 3 (genişleme/monetization).
- **Ayrı track (rafta):** öğrenme platformu (çöz/puanla/paylaş) — `LEARNING_PLATFORM_PLAN.md`.

## Açık operasyonel borçlar (faz-bağımsız)
- 🔒 **PAT revoke** (güvenlik — memory'de launch-gap).
- 📄 Legal placeholder'ları doldur.
- 🧩 `7-sinif-kesirler` örnek önizlemesi (KaTeX render — küçük tamamlama).
