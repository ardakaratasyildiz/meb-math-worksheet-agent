/**
 * JSON-LD structured data render'ı.
 *
 * Google'a sayfa hakkında makine-okunabilir bilgi verir → rich snippet,
 * sitelinks search box, FAQ accordion gibi zenginleştirilmiş arama sonuçları.
 *
 * Kullanım:
 *   <JsonLd data={organizationSchema()} />
 *   <JsonLd data={faqSchema(items)} />
 *
 * Birden fazla schema tek sayfada olabilir — her biri ayrı <JsonLd /> tag'i.
 */
import Script from "next/script";

interface JsonLdProps {
  data: Record<string, unknown>;
  id?: string;
}

export function JsonLd({ data, id }: JsonLdProps) {
  return (
    <Script
      id={id ?? "json-ld"}
      type="application/ld+json"
      strategy="afterInteractive"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }}
    />
  );
}

// ─── Schema fabrikaları ──────────────────────────────────────────────────────

const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? "https://soruatolyesi.com";

/**
 * Organization — site sahibi/markası hakkında. Google Knowledge Panel için
 * gerekli temel. Sosyal hesaplar eklenince sameAs'ı genişlet.
 */
export function organizationSchema() {
  return {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: "Soru Atölyesi",
    url: SITE_URL,
    logo: `${SITE_URL}/logo.png`,
    description:
      "MEB matematik müfredatı (1.-8. sınıf, 8. sınıf LGS hazırlık dahil) için kazanım koduna göre otomatik çalışma kağıdı üretim sistemi.",
    email: "destek@soruatolyesi.com",
    sameAs: [
      "https://www.instagram.com/soruatolyesi.com2026",
      "https://pin.it/34V3999cs",
      "https://www.youtube.com/@soruatolyesi-s2g",
    ],
    contactPoint: {
      "@type": "ContactPoint",
      contactType: "customer support",
      email: "destek@soruatolyesi.com",
      availableLanguage: ["Turkish"],
    },
  };
}

/**
 * WebSite — site genelinde kimliği belirler. potentialAction ile Google'da
 * marka aramasında "sitelinks search box" gösterilebilir (zaman içinde
 * otomatik aktive olur).
 */
export function websiteSchema() {
  return {
    "@context": "https://schema.org",
    "@type": "WebSite",
    name: "Soru Atölyesi",
    url: SITE_URL,
    inLanguage: "tr-TR",
    publisher: {
      "@type": "Organization",
      name: "Soru Atölyesi",
    },
  };
}

/**
 * FAQPage — FAQ sayfası için. Google bunu görünce arama sonuçlarında soruları
 * accordion olarak gösterir (rich result), tıklama oranı belirgin artar.
 */
export function faqPageSchema(items: Array<{ q: string; a: string }>) {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: items.map((it) => ({
      "@type": "Question",
      name: it.q,
      acceptedAnswer: {
        "@type": "Answer",
        text: it.a,
      },
    })),
  };
}

/**
 * EducationalOccupationalProgram / Course-benzeri — programmatic landing page
 * için. "5. sınıf kesirler" gibi sayfada Google'a "bu sayfa matematik
 * eğitim içeriği sunuyor" der.
 */
export function learningResourceSchema(opts: {
  grade: number;
  topicName: string;
  description: string;
  url: string;
}) {
  return {
    "@context": "https://schema.org",
    "@type": "LearningResource",
    name: `${opts.grade}. Sınıf ${opts.topicName} — Çalışma Kağıdı`,
    description: opts.description,
    url: opts.url,
    inLanguage: "tr-TR",
    learningResourceType: "Worksheet",
    educationalLevel: `Grade ${opts.grade}`,
    audience: {
      "@type": "EducationalAudience",
      educationalRole: ["student", "teacher", "parent"],
    },
    provider: {
      "@type": "Organization",
      name: "Soru Atölyesi",
      url: SITE_URL,
    },
  };
}
