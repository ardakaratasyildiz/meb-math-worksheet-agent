/**
 * GEÇİCİ DEBUG endpoint'i — admin paneli neden 404 dönüyor onu görmek için.
 *
 * Güvenlik: yalnızca giriş yapmış kullanıcı sonuç görür. ADMIN_API_KEY veya
 * başka secret bilgi sızdırmaz; sadece "senin için gate hangi adımda kapanıyor"
 * sorusunun cevabını verir. İş bittiğinde silinmesi öneren.
 */
import { auth, currentUser } from "@clerk/nextjs/server";

export const dynamic = "force-dynamic";

export async function GET() {
  const { userId } = await auth();
  if (!userId) {
    return Response.json({
      session: false,
      hint: "Giriş yapmadın. /sign-in'e git, sonra bu URL'i tekrar aç.",
    });
  }
  const user = await currentUser();
  const role = (user?.publicMetadata as { role?: string } | null)?.role;
  const adminEnabled = process.env.ADMIN_ENABLED === "true";
  const adminKeySet = Boolean(process.env.ADMIN_API_KEY);
  const backendUrl = process.env.BACKEND_URL ?? process.env.NEXT_PUBLIC_API_URL ?? null;

  return Response.json({
    session: true,
    userId,
    primaryEmail: user?.primaryEmailAddress?.emailAddress ?? null,
    role: role ?? null,
    publicMetadata: user?.publicMetadata ?? null,
    env: {
      ADMIN_ENABLED: adminEnabled,
      ADMIN_API_KEY_set: adminKeySet,
      BACKEND_URL: backendUrl,
    },
    gateChecks: {
      "1_admin_enabled": adminEnabled,
      "2_session": true,
      "3_role_admin": role === "admin",
    },
    isAdmin: adminEnabled && role === "admin",
  });
}
