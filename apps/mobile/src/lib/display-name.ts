/**
 * Hitap adı — "Sana nasıl hitap edelim?" (onboarding'de sorulur, ekranlar selamlar).
 *
 * Neden ayrı bir kavram: e-posta ile kayıtta Clerk'in `firstName` alanı BOŞ kalır
 * (yalnız Google/Apple ile girenlerde dolu gelir). Ana ekran bunu sabit bir yer
 * tutucuyla dolduruyordu → e-posta ile kayıt olan HERKESE aynı isimle sesleniyordu.
 *
 * Depolama — iki katmanlı, rol ile aynı desen (bkz. lib/roles.ts):
 *  1. Clerk `firstName` (tercih edilen): Clerk panosunda görünür ve admin e-posta
 *     dökümü (frontend/app/api/admin/user-emails/route.ts) buradan okur. Şartı,
 *     Clerk instance'ında "Name" alanının AÇIK olması — kapalıysa update 422 döner.
 *  2. `unsafeMetadata.displayName` (yedek): hiçbir pano ayarı gerektirmez.
 *
 * Soyadı istemiyoruz: kitle 1-8. sınıf çocuklar, takma ad da kabul. Bu değer
 * selamlama dışında hiçbir yerde kullanılmıyor → toplanan veri asgari kalsın.
 */

/** Adı okumak için gereken minimum kullanıcı şekli (Clerk `useUser().user` bunu karşılar). */
export interface NamedUser {
  firstName?: string | null;
  unsafeMetadata?: Record<string, unknown> | null;
}

/** Adı yazabilmek için gereken şekil (Clerk UserResource bunu karşılar). */
export interface UpdatableUser extends NamedUser {
  update(params: {
    firstName?: string;
    unsafeMetadata?: Record<string, unknown>;
  }): Promise<unknown>;
}

/** En fazla bu kadar karakter saklanır (selamlama tek satıra sığsın). */
export const DISPLAY_NAME_MAX = 24;
/** Bu uzunluğun altı geçersiz sayılır. */
const DISPLAY_NAME_MIN = 2;

/** Hitap adı: Clerk `firstName` > `unsafeMetadata.displayName`. İkisi de yoksa null. */
export function displayName(user: NamedUser | null | undefined): string | null {
  if (!user) return null;
  const first = user.firstName?.trim();
  if (first) return first;
  const meta = (user.unsafeMetadata as { displayName?: unknown } | null)?.displayName;
  const stored = typeof meta === "string" ? meta.trim() : "";
  return stored || null;
}

/** Onboarding'de ad sorulmalı mı (kullanıcı var ama adı yok). */
export function needsDisplayName(user: NamedUser | null | undefined): boolean {
  return !!user && displayName(user) === null;
}

/** Girdiyi temizler: iç boşluklar teke iner, kenarlar kırpılır, uzunluk sınırlanır. */
export function normalizeDisplayName(raw: string): string {
  return raw.replace(/\s+/g, " ").trim().slice(0, DISPLAY_NAME_MAX);
}

/** Kaydedilebilir mi (temizlendikten sonra en az 2 karakter). */
export function isValidDisplayName(raw: string): boolean {
  return normalizeDisplayName(raw).length >= DISPLAY_NAME_MIN;
}

/**
 * Adı kaydeder: önce Clerk `firstName`, o yol kapalıysa `unsafeMetadata.displayName`.
 * Clerk instance'ında "Name" alanı kapalı olduğunda ilk yazım 422 atar — bu yüzden
 * yedek yol var; böylece kurulum panoda hangi ayarda olursa olsun onboarding tıkanmaz.
 * Yazımdan sonra çağıran `user.reload()` yapmalı (gate ancak o zaman kapanır).
 */
export async function saveDisplayName(user: UpdatableUser, raw: string): Promise<void> {
  const name = normalizeDisplayName(raw);
  try {
    await user.update({ firstName: name });
  } catch {
    await user.update({
      unsafeMetadata: { ...(user.unsafeMetadata ?? {}), displayName: name },
    });
  }
}
