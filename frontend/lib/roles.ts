/**
 * Kullanıcı rolleri (öğrenci / öğretmen / veli / admin) — ekranları role göre gösterir.
 *
 * Depolama (2026-07: kalıcılık için SUNUCU-SET publicMetadata'ya taşındı):
 *  - Rol → Clerk `publicMetadata.role` (student | teacher | parent | admin).
 *    Yalnız SUNUCU yazabilir (`/api/role` route → Clerk backend). Kullanıcı kendi
 *    rolünü değiştiremez; onboarding'de bir kez set edilir, sonra route 409 ile reddeder.
 *  - `admin` yine publicMetadata (elle/dashboard'dan verilir); /api/role admin set edemez.
 *  - LEGACY: eski kullanıcılarda rol `unsafeMetadata.role`'de olabilir → geçici fallback
 *    okunur; RoleSync bileşeni bunları bir kez publicMetadata'ya taşır (kalıcılaştırır).
 *
 * Etkin rol: publicMetadata > legacy unsafeMetadata. Rol yoksa → onboarding (RoleGate).
 */

export type Role = "student" | "teacher" | "parent" | "admin";
/** Kullanıcının onboarding'de seçebileceği roller (admin hariç). */
export type SelectableRole = "student" | "teacher" | "parent";

export interface RoleMeta {
  value: SelectableRole;
  label: string;
  emoji: string;
  desc: string;
}

export const ROLE_META: RoleMeta[] = [
  {
    value: "student",
    label: "Öğrenci",
    emoji: "🎒",
    desc: "Quiz çöz, ilerlemeni gör, eksiklerine göre haftalık çalışma programı al.",
  },
  {
    value: "teacher",
    label: "Öğretmen",
    emoji: "🎓",
    desc: "Sınıf aç, öğrencilerini davet et, ödev ata ve sonuçları tek ekrandan izle.",
  },
  {
    value: "parent",
    label: "Veli",
    emoji: "👨‍👩‍👧",
    desc: "Çocuğunu takip koduyla ekle, ilerlemesini ve eksiklerini takip et.",
  },
];

const SELECTABLE = new Set<string>(["student", "teacher", "parent"]);

/** Değer seçilebilir bir rol mü (student/teacher/parent)? */
export function isSelectableRole(value: unknown): value is SelectableRole {
  return typeof value === "string" && SELECTABLE.has(value);
}

/**
 * Clerk kullanıcısından etkin rolü çıkarır. `user` client'te `useUser().user`,
 * server'da `currentUser()` sonucu olabilir (ikisi de publicMetadata/unsafeMetadata taşır).
 * Öncelik: publicMetadata (sunucu-set, kalıcı) > legacy unsafeMetadata. Yoksa null.
 */
export function effectiveRole(user: {
  publicMetadata?: Record<string, unknown> | null;
  unsafeMetadata?: Record<string, unknown> | null;
} | null | undefined): Role | null {
  if (!user) return null;
  const pub = (user.publicMetadata as { role?: string } | null)?.role;
  if (pub === "admin") return "admin";
  if (pub && SELECTABLE.has(pub)) return pub as Role;
  // Legacy: eski unsafeMetadata rolleri (RoleSync publicMetadata'ya taşıyana dek).
  const legacy = (user.unsafeMetadata as { role?: string } | null)?.role;
  return legacy && SELECTABLE.has(legacy) ? (legacy as Role) : null;
}

export function roleLabel(role: Role | null): string {
  switch (role) {
    case "student":
      return "Öğrenci";
    case "teacher":
      return "Öğretmen";
    case "parent":
      return "Veli";
    case "admin":
      return "Yönetici";
    default:
      return "";
  }
}
