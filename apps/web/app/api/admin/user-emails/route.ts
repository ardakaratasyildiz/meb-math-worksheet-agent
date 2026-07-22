import { clerkClient } from "@clerk/nextjs/server";

import { checkAdminAccess } from "@/lib/admin-proxy";

export const dynamic = "force-dynamic";

/**
 * Admin — tenant (Clerk userId) → e-posta/ad çözümü. Tenant listesindeki ham userId'leri
 * okunur kimliğe çevirir. Sadece admin (checkAdminAccess). Clerk backend'den TOPLU çeker
 * (getUserList), N+1 çağrı yok. 'anon' ve Clerk olmayan id'ler atlanır.
 *
 * POST { ids: string[] } → { users: { [id]: { email, name } } }
 */
export async function POST(req: Request) {
  const gate = await checkAdminAccess();
  if (!gate.ok) return gate.response;

  let ids: string[] = [];
  try {
    const body = (await req.json()) as { ids?: unknown };
    if (Array.isArray(body.ids)) {
      ids = body.ids.filter((x): x is string => typeof x === "string");
    }
  } catch {
    return Response.json({ error: "Geçersiz gövde" }, { status: 400 });
  }

  // Yalnız Clerk userId'leri (user_...); anon/diğerleri çözülemez. Dedupe + tavan.
  const clerkIds = Array.from(new Set(ids.filter((id) => id.startsWith("user_")))).slice(0, 300);
  if (clerkIds.length === 0) return Response.json({ users: {} });

  try {
    const client = await clerkClient();
    const res = await client.users.getUserList({ userId: clerkIds, limit: clerkIds.length });
    const users: Record<string, { email: string; name: string }> = {};
    for (const u of res.data) {
      const email =
        u.emailAddresses.find((e) => e.id === u.primaryEmailAddressId)?.emailAddress ??
        u.emailAddresses[0]?.emailAddress ??
        "";
      const name = [u.firstName, u.lastName].filter(Boolean).join(" ") || u.username || "";
      users[u.id] = { email, name };
    }
    return Response.json({ users });
  } catch (err) {
    return Response.json(
      { error: `Clerk erişilemedi: ${(err as Error).message}` },
      { status: 502 },
    );
  }
}
