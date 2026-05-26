import Link from "next/link";
import { ArrowRight, GraduationCap } from "lucide-react";

import { Footer } from "@/components/Footer";
import { JsonLd } from "@/components/JsonLd";
import { PageHeader } from "@/components/PageHeader";
import { CURRICULUM_PAGES } from "@/lib/curriculum";

export const metadata = {
  title: "Sınıf ve Konuya Göre Matematik Çalışma Kağıtları",
  description:
    "1.-7. sınıf MEB matematik müfredatı kapsamındaki tüm konular için hazır çalışma kağıtları. Sınıfını ve konunu seç, kazanım kodu bazlı PDF üret.",
  alternates: { canonical: "/calismalar" },
};

const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? "https://soruatolyesi.com";

// İçindekiler list schema — Google'a "bu hub sayfası" diyor.
function collectionPageSchema() {
  return {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    name: "Sınıf ve konuya göre matematik çalışma kağıtları",
    url: `${SITE_URL}/calismalar`,
    inLanguage: "tr-TR",
    isPartOf: {
      "@type": "WebSite",
      name: "Soru Atölyesi",
      url: SITE_URL,
    },
    hasPart: CURRICULUM_PAGES.map((p) => ({
      "@type": "LearningResource",
      name: `${p.grade}. Sınıf ${p.topicName}`,
      url: `${SITE_URL}/calismalar/${p.slug}`,
      educationalLevel: `Grade ${p.grade}`,
    })),
  };
}

export default function CalismalarHubPage() {
  // Sınıf bazlı grupla — UI'da sınıf headerları altında konular listelensin.
  const byGrade = new Map<number, typeof CURRICULUM_PAGES>();
  for (const page of CURRICULUM_PAGES) {
    if (!byGrade.has(page.grade)) byGrade.set(page.grade, []);
    byGrade.get(page.grade)!.push(page);
  }

  return (
    <>
      <JsonLd id="collection-schema" data={collectionPageSchema()} />
      <PageHeader
        eyebrow="Çalışma Kağıtları"
        title="Sınıf ve konuya göre matematik çalışma kağıtları"
        body="MEB müfredatına uygun 1.-7. sınıf tüm konular. Sınıfını ve istediğin konuyu seçerek o konuya özel kazanım kodu bazlı çalışma kağıdı üretebilirsin."
      />

      <section className="py-16">
        <div className="container max-w-5xl space-y-12">
          {Array.from(byGrade.entries()).map(([grade, topics]) => (
            <div key={grade}>
              <h2 className="mb-5 flex items-center gap-2 text-xl font-semibold text-foreground">
                <GraduationCap className="h-5 w-5 text-primary" />
                {grade}. Sınıf Matematik
              </h2>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {topics.map((t) => (
                  <Link
                    key={t.slug}
                    href={`/calismalar/${t.slug}`}
                    className="group rounded-lg border bg-card p-4 transition hover:border-primary/50 hover:shadow-sm"
                  >
                    <h3 className="font-medium text-foreground group-hover:text-primary">
                      {t.topicName}
                    </h3>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {t.description}
                    </p>
                    <div className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-primary opacity-0 transition group-hover:opacity-100">
                      Detay <ArrowRight className="h-3 w-3" />
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      <Footer />
    </>
  );
}
