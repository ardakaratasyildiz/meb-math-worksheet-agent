import type { MetadataRoute } from "next";

import { CURRICULUM_PAGES } from "@/lib/curriculum";

const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? "https://soruatolyesi.com";

/**
 * Otomatik üretilen sitemap.xml.
 * Google Search Console'a `${SITE_URL}/sitemap.xml` olarak submit edilir.
 *
 * Üç katman:
 * 1. Static marketing/legal sayfalar
 * 2. Programmatic landing pages (1.-7. sınıf × konu = 38 sayfa)
 *
 * Auth gerekli sayfalar (/generate, /history, /admin) sitemap'e GİRMEZ —
 * Google'ın index'lemesinin anlamı yok, robots.ts'te disallow.
 */
export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();

  const staticPages: MetadataRoute.Sitemap = [
    { url: `${SITE_URL}/`, lastModified: now, changeFrequency: "weekly", priority: 1.0 },
    { url: `${SITE_URL}/features`, lastModified: now, changeFrequency: "monthly", priority: 0.8 },
    { url: `${SITE_URL}/pricing`, lastModified: now, changeFrequency: "monthly", priority: 0.8 },
    { url: `${SITE_URL}/faq`, lastModified: now, changeFrequency: "monthly", priority: 0.7 },
    { url: `${SITE_URL}/calismalar`, lastModified: now, changeFrequency: "weekly", priority: 0.9 },
    { url: `${SITE_URL}/legal/kvkk`, lastModified: now, changeFrequency: "yearly", priority: 0.3 },
    { url: `${SITE_URL}/legal/terms`, lastModified: now, changeFrequency: "yearly", priority: 0.3 },
    { url: `${SITE_URL}/legal/privacy`, lastModified: now, changeFrequency: "yearly", priority: 0.3 },
  ];

  const curriculumPages: MetadataRoute.Sitemap = CURRICULUM_PAGES.map((p) => ({
    url: `${SITE_URL}/calismalar/${p.slug}`,
    lastModified: now,
    changeFrequency: "weekly" as const,
    priority: 0.7,
  }));

  return [...staticPages, ...curriculumPages];
}
