/**
 * Mağaza bağlantıları — tek kaynak.
 *
 * iOS sürümü 1 Eylül 2026'da App Store'da yayına girdi (ASC App ID 6800827347).
 * Pro / Pro+ abonelikleri ve ek kağıt paketleri YALNIZCA mobil uygulama içinden,
 * Apple'ın uygulama içi satın alma akışıyla satılıyor; web tarafında ödeme akışı
 * YOK. Bu yüzden /pricing'deki ücretli plan CTA'ları mailto ön-kaydı yerine
 * doğrudan buraya çıkar.
 *
 * Android henüz yayında değil: Play "Misleading Claims" reddi sonrası yeniden
 * gönderim bekliyor (docs/PLAY_POLICY_FIX.md). Yayına girdiğinde ANDROID_APP_URL
 * doldurulup ANDROID_LIVE true yapılır — arayüzdeki "yakında" ifadeleri bu iki
 * sabite bakar, ayrıca metin düzenlemek gerekmez.
 */
export const IOS_APP_URL =
  "https://apps.apple.com/tr/app/soru-atolyesi/id6800827347";

export const ANDROID_APP_URL = "";

/** Play sürümü yayına girince true yap (ve ANDROID_APP_URL'i doldur). */
export const ANDROID_LIVE: boolean = false;
