import { auth, clerkClient } from "@clerk/nextjs/server";

export const dynamic = "force-dynamic";

// Onboarding'de seçilebilir roller. `admin` bu route ile ATANAMAZ (elle/dashboard).
const SELECTABLE = new Set(["student", "teacher", "parent"]);

/**
 * Rolü SUNUCU tarafında publicMetadata'ya yazar (kalıcı, kullanıcı değiştiremez).
 *
 * - Oturum zorunlu (auth). Rol ∈ {student, teacher, parent}.
 * - KALICILIK: publicMetadata.role zaten set ise değiştirilemez → aynıysa idempotent 200,
 *   farklıysa 409. (Admin dahil mevcut rol korunur; kullanıcı rolünü değiştiremez.)
 * - Yalnız Clerk backend (CLERK_SECRET_KEY) yazabilir → client unsafeMetadata gibi
 *   müdahale edemez. RoleGate onboarding + RoleSync legacy migrasyon bunu çağırır.
 *
 * POST { role } → { ok, role } | 400/401/409
 */
export async function POST(req: Request) {
  const { userId } = await auth();
  if (!userId) {
    return Response.json({ error: "Oturum gerekli." }, { status: 401 });
  }

  let role: unknown;
  try {
    role = ((await req.json()) as { role?: unknown }).role;
  } catch {
    return Response.json({ error: "Geçersiz gövde." }, { status: 400 });
  }
  if (typeof role !== "string" || !SELECTABLE.has(role)) {
    return Response.json({ error: "Geçersiz rol." }, { status: 400 });
  }

  try {
    const client = await clerkClient();
    const user = await client.users.getUser(userId);
    const existing = (user.publicMetadata as { role?: string } | null)?.role;

    if (existing) {
      // Rol zaten belirlenmiş → değiştirilemez (kalıcı). Aynıysa no-op başarı.
      if (existing === role) return Response.json({ ok: true, role: existing });
      return Response.json(
        { error: "Rol zaten belirlenmiş ve değiştirilemez.", role: existing },
        { status: 409 },
      );
    }

    await client.users.updateUserMetadata(userId, {
      publicMetadata: { ...user.publicMetadata, role },
    });
    return Response.json({ ok: true, role });
  } catch (err) {
    return Response.json(
      { error: err instanceof Error ? err.message : "Rol kaydedilemedi." },
      { status: 500 },
    );
  }
}
