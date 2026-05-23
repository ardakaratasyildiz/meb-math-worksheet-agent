import { checkAdminAccess, proxyToBackend } from "@/lib/admin-proxy";

export const dynamic = "force-dynamic";

export async function GET() {
  const gate = await checkAdminAccess();
  if (!gate.ok) return gate.response;
  return proxyToBackend("/admin/worksheet-history/_summary", gate.userId);
}
