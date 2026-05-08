import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

// Login zorunlu route'lar — diğerleri (landing, sign-in/up) public.
const isProtectedRoute = createRouteMatcher(["/generate(.*)", "/history(.*)"]);

export default clerkMiddleware(async (auth, req) => {
  if (isProtectedRoute(req)) await auth.protect();
});

export const config = {
  matcher: [
    // Static asset, API, _next dışındaki tüm route'larda çalış
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};
