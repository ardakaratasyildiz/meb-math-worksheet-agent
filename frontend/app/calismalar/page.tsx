import Link from "next/link";
import { ArrowRight, GraduationCap } from "lucide-react";

import { Footer } from "@/components/Footer";
import { JsonLd } from "@/components/JsonLd";
import { PageHeader } from "@/components/PageHeader";
import { CURRICULUM_PAGES } from "@/lib/curriculum";

export const metadata = {
  title: "Sınıf ve Konuya Göre Matematik Çalışma Kağıtları",
  description:
    "1.-8. sınıf MEB matematik müfredatı (8. sınıf LGS hazırlık dahil) kapsamındaki tüm konular için hazır çalışma kağıtları. Sınıfını ve konunu seç, kazanım kodu bazlı PDF üret.",
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
        body="MEB müfredatına uygun 1.-8. sınıf tüm konular (8. sınıf LGS hazırlık dahil). Sınıfını ve istediğin konuyu seçerek o konuya özel kazanım kodu bazlı çalışma kağıdı üretebilirsin."
      />

      <section className="pt-10">
        <div className="container max-w-5xl">
          <Link
            href="/lgs-matematik"
            className="group flex flex-wrap items-center justify-between gap-3 rounded-xl border border-primary/30 bg-accent p-5 transition hover:border-primary/60"
          >
            <div>
              <p className="font-semibold text-accent-foreground">
                8. sınıftaysan: LGS Matematik Hazırlık
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                Tüm LGS matematik konuları, en çok çıkan alt-başlıklar ve sık
                sorulanlar tek sayfada.
              </p>
            </div>
            <span className="inline-flex items-center gap-1 text-sm font-medium text-primary">
              LGS sayfasına git <ArrowRight className="h-4 w-4" />
            </span>
          </Link>
        </div>
      </section>

      <section className="py-16">
        <div className="container max-w-5xl space-y-12">
          {Array.from(byGrade.entries()).map(([grade, topics]) => (
            <div key={grade}>
              <Link
                href={grade === 8 ? "/lgs-matematik" : `/${grade}-sinif-matematik`}
                className="group mb-5 inline-flex items-center gap-2 text-xl font-semibold text-foreground transition hover:text-primary"
              >
                <GraduationCap className="h-5 w-5 text-primary" />
                {grade}. Sınıf Matematik
                <ArrowRight className="h-4 w-4 text-primary opacity-0 transition group-hover:opacity-100" />
              </Link>
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
                    <div className="mt-3 flex items-center justify-between text-xs">
                      <span className="font-medium text-primary">
                        {t.kazanimCount} kazanım
                      </span>
                      <span className="inline-flex items-center gap-1 font-medium text-primary opacity-0 transition group-hover:opacity-100">
                        Kazanımları gör <ArrowRight className="h-3 w-3" />
                      </span>
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
