# Güvenlik Backlog — Soru Atölyesi

> Kaynak: 2026-07-16 kapsamlı güvenlik + kullanım testi (statik denetim + canlı kara-kutu).
> **İlk 3 kritik madde `fix/security-idor-cors-ratelimit` PR'ında kapatıldı.** Kalanlar aşağıda,
> öncelik sırasıyla. Bir madde kapatıldıkça işaretle.

## ✅ Kapatıldı (PR: fix/security-idor-cors-ratelimit)

- [x] **IDOR / tenant spoofing** — `classrooms`, `assignments`, `quizzes`, `worksheets` history
  uçları `tenant_id`'yi client'tan doğrulamadan alıyordu. Artık hepsi `me.py` desenini
  (`Depends(verified_tenant_id)` + `require_tenant`) kullanıyor; Clerk açıkken Bearer yoksa 401.
  Canlı doğrulandı: `/api/classrooms` ve `/api/worksheets/history` Bearer'sız veri döndürüyordu.
- [x] **CORS wildcard + credentials** — `allow_origins=["*"]` ile `allow_credentials=True`
  birlikteydi; Starlette Origin'i yansıtıp her siteye kimlik-doğrulamalı okuma açıyordu.
  Canlı doğrulandı (`evil.example.com` yansıdı). Fix: credentials yalnız explicit (non-wildcard)
  origin listesinde etkin. **Kalıcı çözüm için Render'da `CORS_ORIGINS` env'ini açıkça set et.**
- [x] **Rate-limit spoof (maliyet-DoS)** — limiter anahtarı spoof-edilebilen `X-Tenant-Id`
  header'ındandı; rastgele header ile limit tamamen aşılabiliyordu. Fix: anahtar artık
  doğrulanmış Clerk oturumundan (`Authorization: Bearer`), yoksa IP'den türetiliyor.
- [x] **H2 — Ödev cevap-tekrarı** — pano/skor `MAX(att.score)` kullanıyordu; öğrenci bir kez
  gönderip anahtarı okuduktan sonra tam puanla yeniden gönderiyordu. Karar (kullanıcı):
  **tekrar serbest ama İLK deneme sayılır**. Fix `app/services/classroom_store.py`:
  `assignment_results` + `list_my_assignments` artık en erken `completed_at` denemesini
  gösteriyor (MAX değil). Regresyon: `tests/test_assignment.py::test_first_attempt_counts_not_max`.
  Kalıntı (düşük): attempts FIFO trim'i tenant başına 200; teorik olarak 200+ gönderimle honest
  ilk deneme trim'lenebilir — absürt eşik, ihtiyaç olursa "ilk skoru dondur" ile sağlamlaştır.

## 🟠 Sırada (bakılacak — UNUTMA)
- [ ] **H1 — Kota bypass** (latent; `BILLING_ENABLED=false` iken uyumuyor):
  kota doğrulanmış kimliğe göre uygulanıyor ama `usage_ledger` kaydı `req.tenant_id`'ye yazılıyor
  (`app/routers/worksheets.py` ~340). Not: bu PR quiz sahipliğini doğrulanmış kimliğe bağladı;
  worksheet üretim uçlarında `USAGE_LEDGER.record(tenant_id=...)` hâlâ client-supplied tenant
  kullanıyorsa doğrulanmış kimliğe çevir. Billing açılmadan önce kapat.
- [ ] **M — `render.pdf` SSRF** (`app/services/svg_utils.py` `_DANGEROUS_PATTERNS`):
  SVG `<image href="http://169.254.169.254/...">` engellenmiyor; svglib render'da fetch ediyor.
  Fix: `<image>` href için şema allowlist (`data:` only) / external kaynak yüklemeyi kapat.
- [ ] **M — `render.pdf` sınırsız girdi + throttle yok** (`app/routers/worksheets.py:510`,
  `app/models/schemas.py` `Worksheet.questions`): 100k soruluk worksheet → bellek/CPU DoS.
  Fix: `questions` liste uzunluğu + soru/çözüm string uzunluğu sınırı; uca `@limiter.limit`.
- [ ] **M — Admin key sabit-zamanlı değil** (`app/routers/admin.py:38`): `!=` timing yan-kanalı.
  Fix: `hmac.compare_digest(x_admin_key or "", settings.admin_api_key)`.
- [ ] **M — Sınıf/veli katılım kodları brute-force'lanabilir, throttle yok**
  (`app/services/classroom_store.py` ~31, `app/routers/classrooms.py` join; `parent_link_store.py`):
  Fix: `join` + `link-child` uçlarına per-IP/tenant rate-limit; kodu uzat / N denemede kilit.

## 🟡 Düşük / hijyen

- [ ] **Gemini API key rotasyonu** — yerel `.env`'deki key test sırasında düz metin görüldü
  (git'e girmemiş ama). Rotate et + GCP'de HTTP-referrer/API kısıtı uygula.
- [ ] **Clerk JWT `azp` doğrulaması** (`app/services/clerk_auth.py:97`): tek-app için kabul
  edilebilir; aynı Clerk instance'ında başka app token'ı geçerli sayılmasın diye `azp`'yi
  frontend origin'ine karşı doğrulamayı düşün.
- [ ] **Public API key hijyeni** — `NEXT_PUBLIC_API_KEY` (`ak_yk_...`) tasarım gereği tarayıcıda
  açık; güvenlik değeri sınırlı. Gerçek yetki Clerk Bearer'da. Rate-limit/kota artık Bearer'a
  dayandığı için kabul edilebilir; ileride tümüyle kaldırılabilir.

## Notlar
- Frontend güvenliği (admin triple-gate, rol yükseltme, XSS/SafeSvg, secret sızıntısı,
  açık redirect) denetlendi — **kritik bulgu yok**.
- SQL enjeksiyon yok (tüm sorgular parametreli), XXE hardened, anti-hile cevap-soyma +
  sunucu-tarafı puanlama sağlam.
