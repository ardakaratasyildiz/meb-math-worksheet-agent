import type { MetadataRoute } from "next";

const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? "https://soruatolyesi.com";

/**
 * Otomatik üretilen robots.txt. Next.js bu dosyayı /robots.txt olarak servis eder.
 *
 * Disallow listesi:
 * - /admin     → admin paneli (Clerk role-gated, ama yine de index'lenmesin)
 * - /api       → JSON endpoint'leri (Google'a verecek değer yok, crawl bütçesi yeme)
 * - /sign-in,
 *   /sign-up   → auth sayfaları (canonical home'da, duplicate önle)
 * - /generate  → auth gerekli, login ekranına redirect olur (boş kabuk index'lenir)
 * - /history   → kullanıcıya özel veri
 */
export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: [
          "/admin",
          "/admin/",
          "/api/",
          "/sign-in",
          "/sign-up",
          "/generate",
          "/history",
        ],
      },
    ],
    sitemap: `${SITE_URL}/sitemap.xml`,
    host: SITE_URL,
  };
}
