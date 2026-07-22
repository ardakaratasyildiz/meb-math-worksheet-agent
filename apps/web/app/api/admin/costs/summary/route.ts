import { checkAdminAccess, proxyToBackend } from "@/lib/admin-proxy";

export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  const gate = await checkAdminAccess();
  if (!gate.ok) return gate.response;
  const days = new URL(req.url).searchParams.get("days") ?? "30";
  return proxyToBackend(
    `/admin/costs/summary?days=${encodeURIComponent(days)}`,
    gate.userId,
  );
}
