# Engagement & Sınıf UX Planı (öğretmen davet + bildirim + bülten)

> Durum: 2026-06-18. Kaynak: kullanıcı isteği — öğretmen soru üretip sınıf paylaşımı,
> 3-gün-inaktif bildirimi, genel bülten. **Kritik:** bir kısmı sıfır altyapı (kod),
> e-posta/bülten + re-engagement **e-posta altyapısı + KVKK izni** gerektirir.
> "Girmeyen kullanıcıya bildirim" uygulama-içi olamaz (kişi sitede değil) → e-posta/push.

---

## Track 1 — Sıfır altyapı (kod) — ✅ YAPILDI (PR: feat/class-share-and-picker-hint)
- **1a. Sınıf kodu Paylaş butonu + katılma linki** ✅ — `ClassroomDetailView` kod kartında
  "Paylaş" (navigator.share / WhatsApp fallback); link `/practice/classes?join=KOD`.
  `ClassesView` `initialJoinCode` prop'uyla kodu ön-doldurur (sunucu sayfası `?join=` okur).
- **1b. Atama picker açıklaması** ✅ — picker'da kaynak (Quiz/PDF) altında not: liste =
  "senin ürettiğin quizler / çalışma kağıtların", yeni üretmek için Üret linki. Öğretmen
  listenin nereden geldiğini anlar.
- **1c. Öğretmen istediği sınıf/konuda üretim** — zaten mevcut (`/practice/new` + `/generate`,
  her sınıf/konu/kazanım). İsteğe bağlı ileride: sınıf detayından "üret ve ata" tek akış.

## Track 2 — E-posta (re-engagement + bülten) — provider + KVKK gerektirir
Sıra: önce izin/altyapı, sonra mailler.

1. **Email provider** — öneri **Resend** (basit, cömert free tier). API key → `RESEND_API_KEY`
   env (kullanıcı sağlar).
2. **Kullanıcı e-postası** — Clerk'te var; backend'e **Clerk webhook** (`user.created`/`updated`)
   ile e-posta + tenant_id kendi tablona yazılır (`users` veya `email_subscribers`).
3. **Son-aktiflik** — her tenant'ın son aktivitesi `attempts.completed_at` +
   `worksheet_history` + `mastery.last_seen_at`'ten türetilir (veri zaten var).
4. **KVKK (zorunlu):**
   - **Bülten = açık opt-in** (kayıt/profilde onay kutusu) + her mailde **unsubscribe** linki.
   - Re-engagement (transactional-ish) için de opt-out saygısı; izinsiz pazarlama maili YOK.
5. **Zamanlanmış iş (cron):**
   - **Re-engagement:** 3 gündür inaktif + opt-in kullanıcılara hatırlatma maili
     (Render cron / GitHub Action). Frekans sınırı (örn. haftada 1) — spam olmasın.
   - **Bülten:** manuel tetikli ya da haftalık broadcast (opt-in listesine).

**Açık kararlar (kullanıcı verecek):** (a) provider = Resend mi? (b) bülten opt-in
kutusunu kayıt akışına ekleyelim mi?

## Track 3 — PWA Web Push (opsiyonel, e-postasız re-engagement)
- §6 mobil planındaki push. Provider gerekmez ama kullanıcı izni (abonelik) + iOS sınırları
  → erişim e-postadan dar. E-postayı tamamlayıcı; sonraya.

---

## Sıra
**Track 1 ✅ → Track 2 (kararlar + provider sonrası) → Track 3 (opsiyonel).**
KVKK izin altyapısı kurulmadan tek bülten/pazarlama maili atılmaz.
