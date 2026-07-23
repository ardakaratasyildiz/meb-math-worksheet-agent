/**
 * Kullanıcı rolleri (öğrenci / öğretmen / veli / admin) — web'deki frontend/lib/roles.ts'in
 * mobil karşılığı. Ekranları/sekmeleri role göre gösterir.
 *
 * Depolama (kalıcılık):
 *  - Kanonik: Clerk `publicMetadata.role` — yalnız SUNUCU yazar (POST /api/me/role → backend).
 *    28 Tem pk_live + dev build sonrası tüm korumalı uçlar açılınca bu yol otoritatif olur.
 *  - Dev/Expo Go fallback: pk_test token'ı prod backend'te 401 olduğundan (bkz. mobil handoff),
 *    RoleGate rolü client-side `unsafeMetadata.role`'e de yazar → effectiveRole legacy path'ten
 *    okur → onboarding cihazda ŞİMDİ çalışır. Backend başarılı olursa publicMetadata kanonik kalır.
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
    desc: "Quiz çöz, ilerlemeni gör, eksiklerine göre çalış.",
  },
  {
    value: "teacher",
    label: "Öğretmen",
    emoji: "🎓",
    desc: "Sınıf aç, ödev ata, sonuçları izle. (Yakında)",
  },
  {
    value: "parent",
    label: "Veli",
    emoji: "👨‍👩‍👧",
    desc: "Çocuğunu takip koduyla ekle, ilerlemesini gör. (Yakında)",
  },
];

const SELECTABLE = new Set<string>(["student", "teacher", "parent"]);

/** Değer seçilebilir bir rol mü (student/teacher/parent)? */
export function isSelectableRole(value: unknown): value is SelectableRole {
  return typeof value === "string" && SELECTABLE.has(value);
}

/**
 * Clerk kullanıcısından etkin rolü çıkarır (`useUser().user`).
 * Öncelik: publicMetadata (sunucu-set, kalıcı) > legacy unsafeMetadata. Yoksa null.
 */
export function effectiveRole(
  user:
    | {
        publicMetadata?: Record<string, unknown> | null;
        unsafeMetadata?: Record<string, unknown> | null;
      }
    | null
    | undefined,
): Role | null {
  if (!user) return null;
  const pub = (user.publicMetadata as { role?: string } | null)?.role;
  if (pub === "admin") return "admin";
  if (pub && SELECTABLE.has(pub)) return pub as Role;
  const legacy = (user.unsafeMetadata as { role?: string } | null)?.role;
  return legacy && SELECTABLE.has(legacy) ? (legacy as Role) : null;
}

/**
 * Ton kararı: öğrenci = oyunsu (maskot, XP/seri, rozet, kutlama); öğretmen/veli/
 * admin = sade "yetişkin" (maskotsuz, nötr kopya, tek dingin vurgu). Rol henüz
 * yoksa (gate öncesi) öğrenci varsayılır. Ekranlar bununla ton seçer.
 */
export function isPlayfulRole(role: Role | null): boolean {
  return role === null || role === "student";
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
