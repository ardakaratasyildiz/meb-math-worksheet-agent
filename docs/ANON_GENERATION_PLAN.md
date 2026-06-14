# Anonim Üretim Planı (Seçenek A)

**Tarih:** 2026-06-14
**Karar:** Anonim kullanıcı **üretir + önizler (serbest)**; **PDF indirme üyelik kapısında**.
**Amaç:** SEO ziyaretçisi üye olmadan değeri deneyimlesin (aktivasyon); indirme havuç olsun.
**Durum:** İNŞA EDİLDİ (feat/anon-generation). Kararlar: K1=Clerk modal, K2=sorular+cevap anahtarı görünür/PDF kapıda, K3=mevcut limitler (5/dk+30/saat) + identifier tenant/IP'ye çevrildi. Önkoşul PR #45 merge edildi.

---

## Mevcut durum (denetim özeti)

- **Backend anonim üretime hazır:** `require_api_key` (app/security.py) key yoksa `"anonymous"` döner; `tenant_id` body'de opsiyonel; `tenant_id` null ise history zaten atlanıyor.
- **Rate-limit var:** slowapi, `app/config.py` 5/dk + 30/saat. `_identifier` (security.py) X-API-Key varsa `key:<key>`, yoksa `ip:<ip>`.
- **Aylık kota YOK** (logged-in dahil enforce edilmiyor) → A seçeneği kota regresyonu yaratmaz.
- **PDF render** (`/api/worksheets/render.pdf`) LLM çağırmaz, sadece JSON→PDF; auth kontrolü yok.
- **Üretilen sonuç store'da persist edilmiyor** (store.ts partialize sadece form alanları) → signup round-trip'inde kağıt kaybolur.

---

## Değişiklikler

### Frontend

1. **middleware.ts** — `/generate(.*)` protected listesinden çıkar (anonim erişsin). `/history`, `/coz`, `/admin` korumalı kalır.

2. **GenerateForm.tsx** — `if (!userId) { toast.error("Oturum…"); return; }` bloğunu kaldır; anonim üretime izin ver. Backend'e giden `tenant_id` anonimde `null`/omit. (Auth henüz yüklenmediyse `isLoaded` beklenir, ama login zorunluluğu kalkar.)

3. **PDF indirme kapısı — `QuestionPreview.tsx`** (öneri: **Clerk modal**, navigasyonsuz):
   - Anonim (`!userId`) ise "PDF indir" yerine **"Üye ol ve PDF indir"** → `<SignUpButton mode="modal">` (Clerk modal, sayfadan çıkmadan). Üyelik tamamlanınca `userId` dolar, kağıt ekranda durur, indirme açılır.
   - Bu, üretilen kağıdı kaybetmeden indirmeyi havuç yapar (en düşük sürtünme).
   - *Alternatif (yedek):* `/sign-up`'a redirect + store'da `result`'ı persist edip dönüşte geri yükle. Modal tercih edilir çünkü kağıt hiç kaybolmaz.
   - Cevap anahtarı/çözüm önizlemesi de anonimde gösterilebilir (değeri artırır) ya da blur+gate — **karar noktası** (bkz. aşağı).

4. **GA4:** anonim üretim/indirme-gate event'leri — `worksheet_generate_success` zaten var; yeni `download_signup_gate_view` + `download_signup_gate_convert` (gate→üyelik dönüşümü ölçümü).

### Backend

5. **Anonim rate-limit'i IP'ye sabitle (abuse/maliyet):** Prod'da `NEXT_PUBLIC_API_KEY` set'liyse tüm anonimler tek `key:<key>` bucket'ını paylaşır (global 5/dk → herkes birbirini kilitler). Düzeltme: `_identifier`'ı **tenant_id varsa `tenant:<id>`, yoksa IP** olacak şekilde güncelle — ya da anonim çağrılarda frontend paylaşılan key'i göndermesin. Sonuç: logged-in = per-user, anon = per-IP bucket.
   - *Not:* tenant_id body'de; slowapi key_func body okuyamaz. Pratik yol: frontend anonim üretimde `X-Anon: 1` header'ı (veya key'i hiç göndermesin) → backend IP'ye düşer. Düşük riskli.

6. **Anonim için daha sıkı limit (opsiyonel, maliyet kalkanı):** anon’a örn. **3/dk + 10/gün** (yeni config), logged-in mevcut 5/dk+30/saat. LLM maliyetini bağlar.

---

## Karar noktaları (inşadan önce)

- **(K1) PDF gate UX:** Clerk **modal** (önerilen, kağıt kaybolmaz) — vs `/sign-up` redirect + result persist.
- **(K2) Önizleme derinliği:** Anonim, soruların TAMAMINI + cevap anahtarını görsün mü, yoksa cevap anahtarı/çözüm üyelik arkasında mı (blur)? Öneri: **sorular tam görünür, PDF + (ops.) çözüm üyelikte** — değeri göster, formatı/çözümü havuç yap.
- **(K3) Anonim rate-limit:** mevcut 5/dk+30/saat (IP) yeterli mi, yoksa anon’a özel daha sıkı (3/dk+10/gün) mı?

---

## Risk / sıra
1. Backend rate-limit identifier fix (per-IP/anon) — küçük, izole.
2. Frontend middleware + form gate kaldırma — küçük.
3. PDF gate modal — orta (yeni UX).
4. Ölçüm event'leri — küçük.
Tek PR; frontend-ci + backend test ile doğrula. Geri alınabilir (middleware tek satır).

## Beklenen etki
SEO→generate auth-duvarı kalkar; ziyaretçi değeri görür. Üyelik artık "PDF indir" anında, **değer görüldükten sonra** istenir → dönüşüm psikolojisi tersine döner (önce ver, sonra iste).
