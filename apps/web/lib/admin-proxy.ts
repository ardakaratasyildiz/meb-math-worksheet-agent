/**
 * Admin paneli için server-side proxy helper'ları.
 *
 * Güvenlik garantileri:
 * 1. ADMIN_API_KEY browser bundle'a ASLA girmez (NEXT_PUBLIC_ prefix YOK).
 *    Bu dosya yalnızca server context'te (route handlers, server components)
 *    import edilmelidir — client component'ten import = build-time hata.
 * 2. Üç katmanlı gate: ADMIN_ENABLED flag → Clerk session → publicMetadata.role.
 * 3. Her başarısızlık 404 — endpoint'in varlığını gizler (403 yerine).
 * 4. Backend'e giderken X-Admin-Actor header'ında Clerk user ID gönderilir,
 *    audit log'da "kim baktı" net görünür.
 *
 * NOT: Bu modül `@clerk/nextjs/server` import eder → Next.js bunu client
 * component'lere bundle'lamaz (build-time hata verir). Ek `server-only`
 * paketine gerek yok.
 */
import { auth, currentUser } from "@clerk/nextjs/server";

const BACKEND_URL =
  process.env.BACKEND_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const ADMIN_API_KEY = process.env.ADMIN_API_KEY ?? "";
const ADMIN_ENABLED = process.env.ADMIN_ENABLED === "true";

export type AdminGate =
  | { ok: true; userId: string }
  | { ok: false; response: Response };

/**
 * Üç katmanlı admin erişim kontrolü.
 * - ADMIN_ENABLED=false → 404 (preview deploy'larda kazara açılmasın)
 * - Session yok → 404
 * - Role admin değil → 404
 *
 * Hepsi aynı status → endpoint dışarıdan tahmin edilemez.
 */
export async function checkAdminAccess(): Promise<AdminGate> {
  if (!ADMIN_ENABLED) {
    return { ok: false, response: new Response(null, { status: 404 }) };
  }
  const { userId } = await auth();
  if (!userId) {
    return { ok: false, response: new Response(null, { status: 404 }) };
  }
  const user = await currentUser();
  const role = (user?.publicMetadata as { role?: string } | null)?.role;
  if (role !== "admin") {
    return { ok: false, response: new Response(null, { status: 404 }) };
  }
  return { ok: true, userId };
}

/**
 * Backend admin endpoint'ine server-to-server proxy.
 * Sadece checkAdminAccess() başarılı olduktan sonra çağrılmalı.
 *
 * `path` backend yolu (ör. "/admin/cache/stats", "/readyz"). Slash başında.
 */
export async function proxyToBackend(path: string, userId: string): Promise<Response> {
  if (!ADMIN_API_KEY) {
    return Response.json(
      { error: "ADMIN_API_KEY env değişkeni Vercel'de set değil." },
      { status: 500 },
    );
  }
  try {
    const res = await fetch(`${BACKEND_URL}${path}`, {
      headers: {
        "X-Admin-Key": ADMIN_API_KEY,
        "X-Admin-Actor": userId,
      },
      // Admin verisi canlı görünmeli — Next.js fetch cache'i bypass.
      cache: "no-store",
    });
    if (!res.ok) {
      let detail = `${res.status} ${res.statusText}`;
      try {
        const j = (await res.json()) as { detail?: string };
        if (j?.detail) detail = j.detail;
      } catch {
        // ignore
      }
      return Response.json({ error: detail }, { status: res.status });
    }
    const data = await res.json();
    return Response.json(data);
  } catch (err) {
    return Response.json(
      { error: `Backend erişilemedi: ${(err as Error).message}` },
      { status: 502 },
    );
  }
}

/**
 * Server component'lerde role kontrolü için convenience helper.
 * Layout'lardan çağrılır, admin değilse `notFound()` çağırması beklenir.
 */
export async function isAdminUser(): Promise<boolean> {
  if (!ADMIN_ENABLED) return false;
  const { userId } = await auth();
  if (!userId) return false;
  const user = await currentUser();
  const role = (user?.publicMetadata as { role?: string } | null)?.role;
  return role === "admin";
}
