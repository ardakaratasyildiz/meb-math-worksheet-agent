# Mobil Bildirimler — Durum ve Plan

Kapsam: `apps/mobile` bildirim altyapısı. Faz 1 **yapıldı** (2026-08-13), Faz 2 dış
kimlik bilgilerini bekliyor.

---

## Neden

Ana ekrandaki bildirim çanı boş bir `onPress` taşıyordu ve üstünde sürekli yanan bir
"okunmamış" noktası vardı; profildeki "Bildirimler" anahtarı da yalnız kendi state'ini
değiştiriyordu, hiçbir yere bağlı değildi. Bu, mağaza incelemesinde "tamamlanmamış
işlevsellik" olarak değerlendirilebilecek bir yüzey (App Store 2.1). Kaldırmak yerine
gerçekten çalışır hale getirildi.

---

## Faz 1 — Cihazda planlanan hatırlatma (BİTTİ)

Sunucu, APNs veya FCM **gerektirmez**. Tamamen `expo-notifications`'ın yerel
planlama (scheduled local notification) yeteneğiyle çalışır.

| Parça | Yer |
|---|---|
| Guard'lı sarmalayıcı | `apps/mobile/src/lib/notifications.ts` |
| Ayar ekranı | `apps/mobile/src/app/notifications.tsx` |
| Çan (ana ekran) | `src/app/(tabs)/index.tsx` — `/notifications`'a gider |
| Profil anahtarı | `src/app/(tabs)/profile.tsx` — gerçek planlamayı kurar/kaldırır |

Davranış:
- **Günlük çalışma hatırlatması**, kullanıcının seçtiği saatte (16/18/20/21 seçenekleri).
- Metin 4 varyant arasında **gün numarasına göre** döner — aynı cümle her gün gelirse
  bildirim körlüğü oluşur.
- Tercih **cihazda** tutulur (`expo-secure-store`), sunucuda değil: planlama zaten cihaza
  özel, aynı hesap iki telefonda farklı saat isteyebilir.
- Çandaki nokta **yalnız kullanıcı hiç seçim yapmadıysa** yanar. Açıp kapattıktan sonra
  söner — sürekli yanan sahte rozet kullanmıyoruz.
- İzin sistem ayarlarından reddedilmişse (`canAskAgain=false`) uygulama içinden açılamaz;
  ayar ekranı bunu algılayıp **"Ayarları aç"** düğmesi gösterir.
- Uygulama açılışında `syncReminderOnLaunch()` çalışır: tercih açık ama planlama
  kaybolmuşsa (yeniden kurulum, cihaz güncellemesi) sessizce geri kurar.

`purchases.ts` ile aynı guard deseni: native modül yoksa (Expo Go / web) her çağrı
zararsızca no-op döner, ekranlar çalışmaya devam eder ve "mağaza sürümünde çalışır" der.

> **Yeni build gerekir.** `expo-notifications` NATIVE modüldür. Mevcut Android dev
> build'inde yoktur — bildirimler ancak bu değişiklikten sonra alınan build'de çalışır.
> Guard sayesinde eski build çökmez, yalnız "desteklenmiyor" durumuna düşer.

---

## Faz 2 — Uzaktan push (BEKLİYOR)

Gereken dış kurulum (kod tarafı değil):
- **iOS:** Apple Developer hesabında APNs anahtarı (`.p8`) → EAS credentials.
- **Android:** Firebase projesi + `google-services.json` → FCM sunucu kimliği.

Bunlar hazır olunca eklenecekler:
1. `POST /api/me/push-token` — Expo push token'ı tenant'a bağlar (yeni bir store,
   `billing_store` deseniyle: tenant_id, token, platform, updated_at).
2. Gönderim servisi — Expo Push API'ye toplu gönderim, hata/geçersiz token temizliği.
3. Tetikleyiciler:
   - **Ödev atandı** (öğretmen → öğrenci) — `app/routers/assignments.py`.
   - **Deneme bitiyor** (kalan 2 gün) — dönüşümün en güçlü anı.
   - **Seri kırılmak üzere** — bugün hiç aktivite yoksa akşam.
4. Tercih o zaman **sunucuya** da taşınır (push hesap bazlı, cihaz bazlı değil).

Sıra önemli: Faz 2'ye APNs + FCM kurulmadan başlanmamalı, yoksa test edilemeyen kod
birikir.

---

## Notlar

- Android bildirim kanalı (`study-reminder`) her planlamada idempotent kuruluyor;
  Android 8+ kanalsız bildirimi sessizce düşürür.
- `app.json`'daki eklenti ikonu `android-icon-monochrome.png` (siluet). Android küçük
  bildirim ikonunu tek renk ister; ayrı bir 96×96 varlık üretmeye gerek kalmadı.
- Bildirim izni **açılışta istenmiyor** — kullanıcı anahtarı açtığında isteniyor.
  Bağlamsız izin istekleri reddedilme oranını yükseltir.
