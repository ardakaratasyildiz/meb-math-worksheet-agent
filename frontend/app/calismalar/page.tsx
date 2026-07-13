import Link from "next/link";
import { ArrowRight, GraduationCap } from "lucide-react";

import { Footer } from "@/components/Footer";
import { JsonLd } from "@/components/JsonLd";
import { PageHeader } from "@/components/PageHeader";
import { UNIT_PAGES } from "@/lib/units";

export const metadata = {
  title: "Sınıf ve Üniteye Göre Matematik Çalışma Kağıtları",
  description:
    "1.-8. sınıf MEB matematik müfredatı (8. sınıf LGS hazırlık dahil) — üretimde kullanılan güncel ünite/tema yapısı. Sınıfını ve üniteni seç, kazanım bazlı PDF üret.",
  alternates: { canonical: "/calismalar" },
};

const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? "https://soruatolyesi.com";

// Sınıf → üniteler (üretimin kullandığı units.json ile BİREBİR; eski konu
// listesinden değil → Konular sekmesi ile üretim artık tutarlı).
function _byGrade() {
  const m = new Map<number, typeof UNIT_PAGES>();
  for (const u of UNIT_PAGES) {
    if (!m.has(u.grade)) m.set(u.grade, []);
    m.get(u.grade)!.push(u);
  }
  for (const arr of m.values()) arr.sort((a, b) => a.no - b.no);
  return new Map([...m.entries()].sort((a, b) => a[0] - b[0]));
}

function collectionPageSchema() {
  return {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    name: "Sınıf ve üniteye göre matematik çalışma kağıtları",
    url: `${SITE_URL}/calismalar`,
    inLanguage: "tr-TR",
    isPartOf: {
      "@type": "WebSite",
      name: "Soru Atölyesi",
      url: SITE_URL,
    },
    hasPart: [...new Set(UNIT_PAGES.map((u) => u.grade))].map((grade) => ({
      "@type": "LearningResource",
      name: `${grade}. Sınıf Matematik`,
      url: `${SITE_URL}/${grade === 8 ? "lgs-matematik" : `${grade}-sinif-matematik`}`,
      educationalLevel: `Grade ${grade}`,
    })),
  };
}

export default function CalismalarHubPage() {
  const byGrade = _byGrade();

  return (
    <>
      <JsonLd id="collection-schema" data={collectionPageSchema()} />
      <PageHeader
        eyebrow="Çalışma Kağıtları"
        title="Sınıf ve üniteye göre matematik çalışma kağıtları"
        body="MEB güncel müfredatına uygun 1.-8. sınıf tüm üniteler (8. sınıf LGS hazırlık dahil). Sınıfını ve üniteni seç; o üniteye özel, kazanım bazlı çalışma kağıdı üret."
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
          {Array.from(byGrade.entries()).map(([grade, units]) => (
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
                {units.map((u) => (
                  <Link
                    key={u.unit_id}
                    href={`/generate?grade=${grade}&unit=${encodeURIComponent(u.unit_id)}`}
                    className="group rounded-lg border bg-card p-4 transition hover:border-primary/50 hover:shadow-sm"
                  >
                    <h3 className="font-medium text-foreground group-hover:text-primary">
                      {u.no}. {u.name}
                    </h3>
                    <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">
                      {u.kazanimlar[0]?.metin ?? "MEB kazanımlarına uygun sorular."}
                    </p>
                    <div className="mt-3 flex items-center justify-between text-xs">
                      <span className="font-medium text-primary">
                        {u.kazanimlar.length} kazanım
                      </span>
                      <span className="inline-flex items-center gap-1 font-medium text-primary opacity-0 transition group-hover:opacity-100">
                        Çalışma kağıdı üret <ArrowRight className="h-3 w-3" />
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
