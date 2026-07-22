/**
 * Admin panelinde tenant (Clerk userId) → okunur etiket. TEK kaynak: tenantId'nin
 * göründüğü her yer (kullanıcı listesi, detay, Gemini maliyet tablosu) bunu kullanır.
 *
 * Öncelik: **ad soyad varsa AD SOYAD** (email gösterilmez), yoksa e-posta, yoksa fallback.
 */

export interface TenantUser {
  email: string;
  name: string;
}

/** id → ad soyad | e-posta | Anonim | yükleniyor(…) | bilinmeyen. */
export function tenantDisplay(
  id: string,
  users: Record<string, TenantUser>,
  loaded: boolean,
): string {
  if (id === "anon") return "Anonim (giriş yapmamış)";
  const u = users[id];
  if (u) return u.name || u.email || "—"; // isim öncelikli; yoksa e-posta
  if (!id.startsWith("user_")) return "—"; // Clerk olmayan id
  return loaded ? "(bilinmeyen / silinmiş)" : "…";
}

/**
 * Verilen tenant id'leri için Clerk kullanıcılarını (ad/e-posta) TOPLU çözer.
 * Admin-gated /api/admin/user-emails route'una POST. Hata → boş obje (çağıran fallback).
 */
export async function fetchTenantUsers(
  ids: string[],
): Promise<Record<string, TenantUser>> {
  try {
    const res = await fetch("/api/admin/user-emails", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ids }),
      cache: "no-store",
    });
    const d = (await res.json()) as { users?: Record<string, TenantUser> };
    return d.users ?? {};
  } catch {
    return {};
  }
}
