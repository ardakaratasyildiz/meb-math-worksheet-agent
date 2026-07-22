import { checkAdminAccess, proxyToBackend } from "@/lib/admin-proxy";

export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  const gate = await checkAdminAccess();
  if (!gate.ok) return gate.response;
  const url = new URL(req.url);
  const limit = url.searchParams.get("limit") ?? "20";
  return proxyToBackend(`/admin/cache/recent?limit=${encodeURIComponent(limit)}`, gate.userId);
}
