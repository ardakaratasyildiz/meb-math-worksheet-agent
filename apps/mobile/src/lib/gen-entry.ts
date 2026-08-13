/**
 * Üretim akışına GİRİŞ NİYETİ — navigasyon parametresinden bağımsız küçük paylaşımlı durum.
 *
 * NEDEN PARAMETRE DEĞİL: mod bilgisi önce `/create?mode=solve` şeklinde route parametresiyle
 * taşınıyordu. React Navigation `navigate(name)` çağrısında parametre vermezsen ROTANIN
 * MEVCUT parametrelerini koruyor; sekme zaten odaktayken de yeniden navigate etmiyor.
 * Sonuç: mod bir kez "solve" olunca sekmeye yapışıyor ve "Ne yapmak istersin?" adımı
 * bir daha hiç açılmıyordu (cihazda iki ayrı denemede doğrulandı). Bu modül niyeti
 * doğrudan ekrana bildirir — sekme odakta olsa da, ekran zaten bağlı olsa da çalışır.
 *
 * Kullanım:
 *   requestGenEntry('solve')  → ana ekran "Alıştırma Çöz" kartı
 *   requestGenEntry('pdf')    → ana ekran "Çalışma Kağıdı" kartı
 *   requestGenEntry('ask')    → sekme / maskot düğmesi (kullanıcı henüz seçmedi)
 */

/** 'ask' = mod sorusu sorulsun (ön seçim yok). */
export type GenEntry = 'solve' | 'pdf' | 'ask';

let pending: GenEntry | null = null;
const listeners = new Set<() => void>();

/** Girişi kaydeder ve bağlı ekrana haber verir (ekran henüz yoksa mount'ta okunur). */
export function requestGenEntry(entry: GenEntry): void {
  pending = entry;
  // Kopya üzerinde gez: dinleyici içinde abonelik değişirse döngü bozulmasın.
  [...listeners].forEach((l) => l());
}

/** Bekleyen girişi alır ve temizler (tek seferlik tüketim). */
export function consumeGenEntry(): GenEntry | null {
  const p = pending;
  pending = null;
  return p;
}

/** Değişiklikleri dinler; dönen fonksiyon aboneliği kaldırır. */
export function subscribeGenEntry(fn: () => void): () => void {
  listeners.add(fn);
  return () => {
    listeners.delete(fn);
  };
}
