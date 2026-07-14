/**
 * Kullanıcı rolleri (öğrenci / öğretmen / veli / admin) — ekranları role göre gösterir.
 *
 * Depolama:
 *  - Kullanıcının SEÇTİĞİ profil → Clerk `unsafeMetadata.role` (kullanıcı kendi set eder,
 *    onboarding'de). student | teacher | parent.
 *  - `admin` → Clerk `publicMetadata.role === "admin"` (SUNUCU tarafında verilir; kullanıcı
 *    kendine admin atayamaz). Admin TÜM görünümleri görür.
 *
 * Etkin rol: admin > seçilen profil. Rol yoksa (yeni/mevcut kullanıcı) → onboarding (RoleGate).
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

/**
 * Clerk kullanıcısından etkin rolü çıkarır. `user` client'te `useUser().user`,
 * server'da `currentUser()` sonucu olabilir (ikisi de publicMetadata/unsafeMetadata taşır).
 * Rol yoksa null (→ onboarding gerekir).
 */
export function effectiveRole(user: {
  publicMetadata?: Record<string, unknown> | null;
  unsafeMetadata?: Record<string, unknown> | null;
} | null | undefined): Role | null {
  if (!user) return null;
  if ((user.publicMetadata as { role?: string } | null)?.role === "admin") {
    return "admin";
  }
  const r = (user.unsafeMetadata as { role?: string } | null)?.role;
  return r && SELECTABLE.has(r) ? (r as Role) : null;
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
