import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

// Login zorunlu route'lar — diğerleri (landing, sign-in/up, /generate) public.
// /generate ARTIK PUBLIC: anonim kullanıcı üretir + önizler (sorular + cevap
// anahtarı); PDF indirme QuestionPreview'da üyelik kapısında (aktivasyon: önce
// değer, sonra kayıt). /history (hesaba kayıtlı geçmiş) ve /practice login ister.
// /admin(.*) protected → middleware unauthenticated kullanıcıyı /sign-in'e
// gönderir. Layout ek olarak role check yapıp admin değilse notFound() çağırır
// (defense in depth). /api/admin/* route handler'ları kendi içinde de gate'lidir.
const isProtectedRoute = createRouteMatcher([
  "/history(.*)",
  "/practice(.*)",
  "/admin(.*)",
]);

// Clerk v7'de auth.protect() unauthenticated kullanıcıyı default olarak 404'e
// rewrite ediyor (X-Clerk-Auth-Reason: protect-rewrite). Bunun yerine
// /sign-in'e redirect olsun — ?redirect_url ile geri dönüş URL'i taşınır.
export default clerkMiddleware(async (auth, req) => {
  if (!isProtectedRoute(req)) return;
  const { userId, redirectToSignIn } = await auth();
  if (!userId) return redirectToSignIn({ returnBackUrl: req.url });
});

export const config = {
  matcher: [
    // Static asset, API, _next dışındaki tüm route'larda çalış
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};
