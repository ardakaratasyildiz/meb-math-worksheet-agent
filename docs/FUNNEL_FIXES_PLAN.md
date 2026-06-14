# Huni (Funnel) Sızıntı Düzeltmeleri

**Tarih:** 2026-06-14
**Bağlam:** LGS SEO trafiği çekmeye başladık (PR #44). Trafiği büyütmeden önce huniyi sızdırmadığından emin olmak için kod-tarafı funnel denetimi yapıldı.

---

## Denetim bulguları (3 kayıp + 1 ölçüm boşluğu)

1. **Deep-link param yok sayılıyor** — SEO CTA'larındaki `?grade=8&topic=...` `/generate` akışında hiç okunmuyordu (`useSearchParams` yok). Store default'u `grade 5, cebir` → her SEO ziyaretçisi yanlış sınıf/konu formuna düşüyordu.
2. **Değer görülmeden auth duvarı** — `/generate` middleware'de tamamen login arkasında. Anonim ziyaretçi aracı denemeden üye olmak zorunda.
3. **Clerk Turnstile CAPTCHA** — kodda izi yok, Clerk dashboard'ta açık; üyeliğin kendisini engelliyor. (Pano aksiyonu, kod değil.)
4. **Ölçüm boşluğu** — landing/CTA-tık'ta GA4 event'i yoktu → SEO→generate düşüşü görünmüyordu.

---

## Bu PR'da yapılanlar (#1 + #2)

**#1 Deep-link param fix**
- `app/generate/page.tsx` artık server-side `searchParams`'ı okuyup (`grade`/`topic`/`kazanim`) `GenerateForm`'a prop geçiyor.
- `GenerateForm` mount'ta store'u bu değerlerle hidratlıyor (URL niyeti, persist edilmiş seçimi ezer). useSearchParams/Suspense karmaşası yok.

**#2 Funnel GA4 event'leri**
- `components/TrackedGenerateLink.tsx` (yeni client wrapper) → tıklamada `cta_generate_click` { source, grade, topic }.
- SEO landing CTA'ları bu bileşene geçirildi: LGS hub, alt-konu (14 LGS + tüm alt-konular), müfredat `[slug]`, kazanım sayfası.
- `GenerateForm` mount'ta `generate_page_view` { grade, topic_id, deeplink }.
- **Yeni funnel:** `cta_generate_click` → `generate_page_view` → `worksheet_generate_start` → `worksheet_generate_success` → `pdf_download`. `cta` vs `page_view` farkı = auth-duvarı kaybını sayısallaştırır.

**Pano aksiyonu (kod değil): #3-CAPTCHA**
- Clerk Dashboard → User & Authentication → Attack Protection → Bot sign-up protection (Turnstile) kapat ya da invisible moda al. Üyelik blokörü bu.

---

## #3 Anonim "ilk kağıt" — KARAR BEKLİYOR (bu PR'da değil)

En büyük aktivasyon kaldıracı: SEO ziyaretçisinin üye olmadan **değeri deneyimlemesi**. Ama backend kota/maliyet/abuse'a dokunur, yanlış kurulması pahalı (her anonim üretim = LLM maliyeti). Açmadan önce tek kritik karar:

**Kapıyı nereye koyalım?**
- **(A) Üret + önizle serbest, PDF indir kapıda** — anonim 1 kağıt üretip ekranda görür; PDF indirmek/2. üretim için üye olur. *Değeri gösterir, indirmeyi havuç yapar.* (Önerilen)
- **(B) N serbest üretim, sonra üyelik** — anonim N (örn. 1-2) kağıt, sonra duvar. Daha cömert, abuse riski biraz daha yüksek.
- **(C) Tam açık + rate-limit** — login hiç zorunlu değil, sadece IP/oturum bazlı hız sınırı. En düşük sürtünme, en yüksek maliyet/abuse.

**Her durumda gereken backend işi:** anonim kota takibi (IP/oturum), rate-limit, abuse koruması. Karar verince ayrı plan + PR.

---

## Kapsam dışı (sıradaki adaylar)
- Ana sayfa hero CTA'sına da `cta_generate_click` (şu an SEO landing'ler kapsandı).
- Kota görünürlüğü: formda "kalan aylık hak" + limit uyarısı + upgrade CTA (şu an sessiz 429).
