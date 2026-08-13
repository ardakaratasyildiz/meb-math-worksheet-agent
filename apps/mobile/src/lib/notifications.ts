/**
 * Bildirimler — GUARD'LI sarmalayıcı (expo-notifications).
 *
 * `purchases.ts` ile aynı desen: expo-notifications NATIVE modüldür, Expo Go'da
 * (SDK 53+) kısıtlıdır ve web'de hiç yoktur. Her erişim lazy-require + try/catch ile
 * korunur; modül yoksa `available=false` olur ve tüm çağrılar zararsızca no-op döner.
 * Böylece ekranlar her ortamda çalışır, yalnız gerçek build'de bildirim planlanır.
 *
 * KAPSAM (Faz 1 — sunucu bağımlılığı YOK): cihazda planlanan GÜNLÜK ÇALIŞMA
 * HATIRLATMASI. Uzaktan push (ödev atandı, deneme bitiyor) APNs + FCM kimlik
 * bilgileri kurulunca Faz 2'de eklenir — bkz. docs/MOBIL_BILDIRIM_PLANI.md.
 *
 * Tercih cihazda tutulur (expo-secure-store): bildirim planlaması zaten cihaza
 * özel — aynı hesap iki telefonda farklı saat isteyebilir, sunucuda tutmak yanlış olur.
 */
import * as SecureStore from "expo-secure-store";

/** Native modül JS sarmalayıcısı (varsa). Tipler pakete bağlanmasın diye `any`. */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let Notifications: any = null;
let nativeLoaded = false;

function loadNative(): boolean {
  if (nativeLoaded) return !!Notifications;
  nativeLoaded = true;
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    Notifications = require("expo-notifications");
  } catch {
    Notifications = null;
  }
  return !!Notifications;
}

/** Bildirim bu ortamda kurulabilir mi (native modül var). */
export function notificationsSupported(): boolean {
  return loadNative();
}

// ── Tercih deposu ────────────────────────────────────────────────────────────

const KEY_ENABLED = "notif_daily_enabled";
const KEY_HOUR = "notif_daily_hour";
const KEY_MINUTE = "notif_daily_minute";

/** Hatırlatma kimliği — tek bir günlük hatırlatma tutuyoruz (çoğaltma olmasın). */
const DAILY_ID = "daily-study-reminder";

/** Varsayılan hatırlatma saati: okul sonrası çalışma saati. */
export const DEFAULT_HOUR = 18;
export const DEFAULT_MINUTE = 0;

/** Kullanıcının seçebileceği saatler (ayrı bir tarih-saat seçici paketi eklemeden). */
export const REMINDER_SLOTS = [
  { hour: 16, minute: 0, label: "16:00" },
  { hour: 18, minute: 0, label: "18:00" },
  { hour: 20, minute: 0, label: "20:00" },
  { hour: 21, minute: 0, label: "21:00" },
] as const;

async function getItem(key: string): Promise<string | null> {
  try {
    return await SecureStore.getItemAsync(key);
  } catch {
    return null;
  }
}

async function setItem(key: string, value: string): Promise<void> {
  try {
    await SecureStore.setItemAsync(key, value);
  } catch {
    // depo yazılamadı — tercih kalıcı olmaz ama akış kırılmaz
  }
}

export interface ReminderPrefs {
  /** null = kullanıcı henüz seçim YAPMADI (ilk kurulum nudge'ı bunu kullanır). */
  enabled: boolean | null;
  hour: number;
  minute: number;
}

export async function getReminderPrefs(): Promise<ReminderPrefs> {
  const [raw, h, m] = await Promise.all([
    getItem(KEY_ENABLED),
    getItem(KEY_HOUR),
    getItem(KEY_MINUTE),
  ]);
  return {
    enabled: raw === null ? null : raw === "1",
    hour: h === null ? DEFAULT_HOUR : Number(h),
    minute: m === null ? DEFAULT_MINUTE : Number(m),
  };
}

// ── İzin ─────────────────────────────────────────────────────────────────────

export type PermissionState = "granted" | "denied" | "undetermined" | "unsupported";

export async function getPermissionState(): Promise<PermissionState> {
  if (!loadNative()) return "unsupported";
  try {
    const res = await Notifications.getPermissionsAsync();
    if (res?.granted) return "granted";
    // iOS: canAskAgain=false → kullanıcı reddetti, yalnız Ayarlar'dan açılır
    return res?.canAskAgain === false ? "denied" : "undetermined";
  } catch {
    return "unsupported";
  }
}

/** İzin ister. Zaten verilmişse tekrar sormaz. Verildi mi döner. */
export async function requestPermission(): Promise<boolean> {
  if (!loadNative()) return false;
  try {
    const cur = await Notifications.getPermissionsAsync();
    if (cur?.granted) return true;
    const res = await Notifications.requestPermissionsAsync();
    return !!res?.granted;
  } catch {
    return false;
  }
}

// ── Planlama ─────────────────────────────────────────────────────────────────

/**
 * Android'de bildirim kanalı ZORUNLU (Android 8+); kanalsız bildirim sessizce
 * düşer. Kanal oluşturma idempotenttir, her planlamada güvenle çağrılır.
 */
async function ensureAndroidChannel(): Promise<void> {
  try {
    const { Platform } = require("react-native"); // eslint-disable-line @typescript-eslint/no-require-imports
    if (Platform.OS !== "android") return;
    await Notifications.setNotificationChannelAsync("study-reminder", {
      name: "Çalışma hatırlatması",
      importance: Notifications.AndroidImportance?.DEFAULT ?? 3,
      lightColor: "#2679E7",
    });
  } catch {
    // kanal kurulamadı — planlama yine denenir
  }
}

/** Hatırlatma metni — hep aynı cümle bildirim körlüğü yapar, sırayla döner. */
const MESSAGES = [
  { title: "Bugün çalıştın mı? 🦊", body: "Kısa bir çalışma kağıdı yeter, serini koru." },
  { title: "Serini kaybetme! 🔥", body: "Bugünlük hakkın hazır — birkaç soru çözelim." },
  { title: "Yeni bir kağıt hazırlayalım 📄", body: "Eksik kazanımlarına göre hemen üretebilirsin." },
  { title: "Günün sorusu seni bekliyor ✨", body: "5 dakikalık bir çalışma bile seriyi sürdürür." },
];

function pickMessage(): { title: string; body: string } {
  // Gün numarasına göre döner → aynı gün içinde sabit, günler arası değişir.
  const day = Math.floor(Date.now() / 86_400_000);
  return MESSAGES[day % MESSAGES.length];
}

/** Planlanmış günlük hatırlatmayı iptal eder (varsa). */
export async function cancelDailyReminder(): Promise<void> {
  if (!loadNative()) return;
  try {
    await Notifications.cancelScheduledNotificationAsync(DAILY_ID);
  } catch {
    // planlanmış bildirim yoktu — sorun değil
  }
}

/**
 * Günlük hatırlatmayı kurar. İzin yoksa ister; kullanıcı vermezse false döner
 * (çağıran UI'da "Ayarlardan izin ver" yolunu göstermeli).
 * Önce iptal eder → aynı kimlikle tek kayıt kalır, saat değişince çoğalmaz.
 */
export async function scheduleDailyReminder(hour: number, minute: number): Promise<boolean> {
  if (!loadNative()) return false;
  const ok = await requestPermission();
  if (!ok) return false;
  await ensureAndroidChannel();
  await cancelDailyReminder();
  try {
    const msg = pickMessage();
    await Notifications.scheduleNotificationAsync({
      identifier: DAILY_ID,
      content: { title: msg.title, body: msg.body, sound: false },
      trigger: {
        type: "daily", // SchedulableTriggerInputTypes.DAILY
        hour,
        minute,
        channelId: "study-reminder",
      },
    });
    return true;
  } catch {
    return false;
  }
}

/**
 * Tercihi kaydeder ve planlamayı ona göre günceller. Dönen = hatırlatmanın
 * gerçekten AÇIK olup olmadığı (izin reddedilirse açık sayılmaz).
 */
export async function setReminder(enabled: boolean, hour: number, minute: number): Promise<boolean> {
  if (!enabled) {
    await cancelDailyReminder();
    await setItem(KEY_ENABLED, "0");
    return false;
  }
  const scheduled = await scheduleDailyReminder(hour, minute);
  await setItem(KEY_ENABLED, scheduled ? "1" : "0");
  if (scheduled) {
    await setItem(KEY_HOUR, String(hour));
    await setItem(KEY_MINUTE, String(minute));
  }
  return scheduled;
}

/**
 * Uygulama açılışında çağrılır: tercih AÇIK ama planlama kaybolmuşsa yeniden kurar.
 * (Kullanıcı uygulamayı sildi/yeniden kurdu, cihaz güncellendi vb.)
 */
export async function syncReminderOnLaunch(): Promise<void> {
  if (!loadNative()) return;
  const prefs = await getReminderPrefs();
  if (prefs.enabled !== true) return;
  try {
    const scheduled: { identifier: string }[] =
      await Notifications.getAllScheduledNotificationsAsync();
    if (scheduled?.some((s) => s.identifier === DAILY_ID)) return;
  } catch {
    // listelenemedi → yine de kurmayı dene
  }
  await scheduleDailyReminder(prefs.hour, prefs.minute);
}
