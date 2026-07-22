import { checkAdminAccess, proxyToBackend } from "@/lib/admin-proxy";

export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  const gate = await checkAdminAccess();
  if (!gate.ok) return gate.response;
  const url = new URL(req.url);
  const limit = url.searchParams.get("limit") ?? "100";
  const days = url.searchParams.get("days") ?? "30";
  return proxyToBackend(
    `/admin/costs/recent?limit=${encodeURIComponent(limit)}&days=${encodeURIComponent(days)}`,
    gate.userId,
  );
}
