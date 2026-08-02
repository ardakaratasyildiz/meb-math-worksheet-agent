import Link from "next/link";

import { Footer } from "@/components/Footer";
import { PageHeader } from "@/components/PageHeader";

// Hukuki sayfalar (KVKK / Kullanım Koşulları / Gizlilik) için ortak yerleşim.
// İçerik veri olarak `sections` ile gelir; her sayfa yalnızca metni sağlar.

export type LegalSection = {
  heading: string;
  paragraphs?: string[];
  bullets?: string[];
  /** Bölüm sonunda gösterilecek dahili link (ör. hesap silme sayfasına). */
  linkHref?: string;
  linkLabel?: string;
};

export function LegalDocument({
  eyebrow,
  title,
  intro,
  updated,
  sections,
}: {
  eyebrow: string;
  title: string;
  intro: string;
  updated: string;
  sections: LegalSection[];
}) {
  return (
    <>
      <PageHeader eyebrow={eyebrow} title={title} body={intro} />

      <section className="py-16">
        <div className="container max-w-3xl space-y-10">
          <p className="text-xs text-muted-foreground">
            Son güncelleme: {updated}
          </p>

          {sections.map((s, i) => (
            <div key={i} className="space-y-3">
              <h2 className="text-base font-semibold text-foreground">
                {i + 1}. {s.heading}
              </h2>
              {s.paragraphs?.map((p, j) => (
                <p
                  key={j}
                  className="text-sm leading-relaxed text-muted-foreground"
                >
                  {p}
                </p>
              ))}
              {s.bullets ? (
                <ul className="ml-5 list-disc space-y-1.5 text-sm leading-relaxed text-muted-foreground">
                  {s.bullets.map((b, j) => (
                    <li key={j}>{b}</li>
                  ))}
                </ul>
              ) : null}
              {s.linkHref ? (
                <p className="text-sm leading-relaxed">
                  <Link
                    href={s.linkHref}
                    className="font-medium text-foreground underline-offset-2 hover:underline"
                  >
                    {s.linkLabel ?? s.linkHref}
                  </Link>
                </p>
              ) : null}
            </div>
          ))}

          <p className="border-t pt-6 text-xs text-muted-foreground">
            Bu metinle ilgili sorular için{" "}
            <a
              href="mailto:destek@soruatolyesi.com"
              className="underline-offset-2 hover:underline"
            >
              destek@soruatolyesi.com
            </a>{" "}
            adresine yazabilirsiniz.
          </p>
        </div>
      </section>

      <Footer />
    </>
  );
}
