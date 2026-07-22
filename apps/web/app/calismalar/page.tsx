import Link from "next/link";
import { ArrowRight, GraduationCap } from "lucide-react";

import { Footer } from "@/components/Footer";
import { JsonLd } from "@/components/JsonLd";
import { PageHeader } from "@/components/PageHeader";
import { UNIT_PAGES } from "@/lib/units";
import { availableSubjects, subjectStyle } from "@/lib/subjects";
import { subjectUnitsByGrade } from "@/lib/subject-units";
import type { Subject } from "@/lib/types";

export const metadata = {
  title:
    "Sınıf ve Üniteye Göre Çalışma Kağıtları — Matematik, Türkçe, Fen, Sosyal, İngilizce",
  description:
    "1.-8. sınıf MEB müfredatı — Matematik, Türkçe, Fen Bilimleri, Sosyal Bilgiler ve İngilizce üniteleri (8. sınıf LGS hazırlık dahil). Sınıf, ders ve üniteyi seç; kazanım bazlı PDF çalışma kağıdı üret.",
  alternates: { canonical: "/calismalar" },
};

const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? "https://soruatolyesi.com";

// ── Ortak birim tipi (matematik + diğer dersler tek şablonda render edilir) ──
interface UnitLite {
  unit_id: string;
  no: number;
  name: string;
  firstKazanim: string;
  kazanimCount: number;
  href: string;
}

/** Matematik: UNIT_PAGES → sınıf gruplu, ünite linki /generate?grade&unit. */
function mathGrades(): [number, UnitLite[]][] {
  const m = new Map<number, UnitLite[]>();
  for (const u of UNIT_PAGES) {
    if (!m.has(u.grade)) m.set(u.grade, []);
    m.get(u.grade)!.push({
      unit_id: u.unit_id,
      no: u.no,
      name: u.name,
      firstKazanim: u.kazanimlar[0]?.metin ?? "MEB kazanımlarına uygun sorular.",
      kazanimCount: u.kazanimlar.length,
      href: `/generate?grade=${u.grade}&unit=${encodeURIComponent(u.unit_id)}`,
    });
  }
  for (const arr of m.values()) arr.sort((a, b) => a.no - b.no);
  return [...m.entries()].sort((a, b) => a[0] - b[0]);
}

/** Diğer dersler: subject-units → sınıf gruplu, ünite linki /generate?subject&grade&unit. */
function otherGrades(subject: Subject): [number, UnitLite[]][] {
  return subjectUnitsByGrade(subject).map(([grade, units]) => [
    grade,
    units.map((u) => ({
      unit_id: u.unit_id,
      no: u.no,
      name: u.name,
      firstKazanim: u.kazanimlar[0]?.metin ?? "MEB kazanımlarına uygun sorular.",
      kazanimCount: u.kazanimlar.length,
      href: `/generate?subject=${subject}&grade=${grade}&unit=${encodeURIComponent(u.unit_id)}`,
    })),
  ]);
}

/** Matematik sınıf başlığı SEO hub'ına, diğer dersler üretim deep-link'ine gider. */
function gradeHref(subject: Subject, grade: number): string {
  if (subject === "matematik") {
    return grade === 8 ? "/lgs-matematik" : `/${grade}-sinif-matematik`;
  }
  return `/generate?subject=${subject}&grade=${grade}`;
}

function collectionPageSchema(subjects: { value: Subject; label: string }[]) {
  return {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    name: "Sınıf ve derse göre MEB çalışma kağıtları",
    url: `${SITE_URL}/calismalar`,
    inLanguage: "tr-TR",
    isPartOf: { "@type": "WebSite", name: "Soru Atölyesi", url: SITE_URL },
    hasPart: subjects.map((s) => ({
      "@type": "LearningResource",
      name: `${s.label} çalışma kağıtları`,
      url: `${SITE_URL}/calismalar#${s.value}`,
      learningResourceType: "Worksheet",
      educationalLevel: "1.-8. sınıf",
    })),
  };
}

export default function CalismalarHubPage() {
  const subjects = availableSubjects();
  const multi = subjects.length > 1;

  return (
    <>
      <JsonLd
        id="collection-schema"
        data={collectionPageSchema(subjects.map((s) => ({ value: s.value, label: s.label })))}
      />
      <PageHeader
        eyebrow="Çalışma Kağıtları"
        title={
          multi
            ? "Sınıf ve derse göre çalışma kağıtları"
            : "Sınıf ve üniteye göre matematik çalışma kağıtları"
        }
        body={
          multi
            ? "MEB güncel müfredatına uygun tüm dersler ve üniteler (1.-8. sınıf, 8. sınıf LGS hazırlık dahil). Dersini, sınıfını ve üniteni seç; o üniteye özel, kazanım bazlı çalışma kağıdı üret."
            : "MEB güncel müfredatına uygun 1.-8. sınıf tüm üniteler (8. sınıf LGS hazırlık dahil). Sınıfını ve üniteni seç; o üniteye özel, kazanım bazlı çalışma kağıdı üret."
        }
      />

      {/* Ders navigasyonu — sticky renkli çipler (çok-ders açıkken) */}
      {multi ? (
        <div className="sticky top-16 z-20 border-b bg-background/85 backdrop-blur">
          <div className="container flex max-w-5xl flex-wrap gap-2 py-3">
            {subjects.map((s) => {
              const st = subjectStyle(s.value);
              return (
                <a
                  key={s.value}
                  href={`#${s.value}`}
                  className="inline-flex items-center gap-1.5 rounded-full border px-3.5 py-1.5 text-sm font-semibold transition-colors hover:bg-accent/50"
                  style={{ borderColor: `${st.hex}55`, color: st.hex }}
                >
                  <span aria-hidden>{st.emoji}</span>
                  {s.label}
                </a>
              );
            })}
          </div>
        </div>
      ) : null}

      <div className="container max-w-5xl space-y-16 py-14">
        {subjects.map((s) => {
          const st = subjectStyle(s.value);
          const grades =
            s.value === "matematik" ? mathGrades() : otherGrades(s.value);

          return (
            <section
              key={s.value}
              id={s.value}
              className="scroll-mt-32 space-y-10"
            >
              {/* Ders başlığı */}
              <div
                className="flex items-center gap-3 rounded-2xl border-l-4 bg-card p-5 shadow-pop"
                style={{ borderColor: st.hex }}
              >
                <span
                  className="flex h-12 w-12 items-center justify-center rounded-xl text-2xl"
                  style={{ background: `${st.hex}1a` }}
                  aria-hidden
                >
                  {st.emoji}
                </span>
                <div>
                  <h2
                    className="font-display text-2xl font-bold"
                    style={{ color: st.hex }}
                  >
                    {s.label}
                  </h2>
                  <p className="text-sm text-muted-foreground">{st.blurb}</p>
                </div>
              </div>

              {/* LGS callout — yalnız matematik */}
              {s.value === "matematik" ? (
                <Link
                  href="/lgs-matematik"
                  className="group flex flex-wrap items-center justify-between gap-3 rounded-xl border border-primary/30 bg-accent p-5 transition hover:border-primary/60"
                >
                  <div>
                    <p className="font-semibold text-accent-foreground">
                      8. sınıftaysan: LGS Matematik Hazırlık
                    </p>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Tüm LGS matematik konuları, en çok çıkan alt-başlıklar ve
                      sık sorulanlar tek sayfada.
                    </p>
                  </div>
                  <span className="inline-flex items-center gap-1 text-sm font-medium text-primary">
                    LGS sayfasına git <ArrowRight className="h-4 w-4" />
                  </span>
                </Link>
              ) : null}

              {/* Sınıf grupları */}
              {grades.map(([grade, units]) => (
                <div key={grade}>
                  <Link
                    href={gradeHref(s.value, grade)}
                    className="group mb-5 inline-flex items-center gap-2 text-xl font-semibold text-foreground transition hover:text-primary"
                  >
                    <GraduationCap className="h-5 w-5" style={{ color: st.hex }} />
                    {grade}. Sınıf {s.label}
                    <ArrowRight className="h-4 w-4 opacity-0 transition group-hover:opacity-100" style={{ color: st.hex }} />
                  </Link>
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    {units.map((u) => (
                      <Link
                        key={u.unit_id}
                        href={u.href}
                        className="group rounded-lg border bg-card p-4 transition hover:border-primary/50 hover:shadow-sm"
                      >
                        <h3 className="font-medium text-foreground group-hover:text-primary">
                          {u.no}. {u.name}
                        </h3>
                        <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">
                          {u.firstKazanim}
                        </p>
                        <div className="mt-3 flex items-center justify-between text-xs">
                          <span className="font-medium" style={{ color: st.hex }}>
                            {u.kazanimCount} kazanım
                          </span>
                          <span className="inline-flex items-center gap-1 font-medium opacity-0 transition group-hover:opacity-100" style={{ color: st.hex }}>
                            Çalışma kağıdı üret <ArrowRight className="h-3 w-3" />
                          </span>
                        </div>
                      </Link>
                    ))}
                  </div>
                </div>
              ))}
            </section>
          );
        })}
      </div>

      <Footer />
    </>
  );
}
