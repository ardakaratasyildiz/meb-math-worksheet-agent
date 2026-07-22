import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowRight, ChevronRight, GraduationCap, Target } from "lucide-react";

import { Footer } from "@/components/Footer";
import { JsonLd, learningResourceSchema } from "@/components/JsonLd";
import { TrackedGenerateLink } from "@/components/TrackedGenerateLink";
import { AltKonuLanding } from "@/components/AltKonuLanding";
import { ALTKONU_PAGES, getAltKonu } from "@/lib/altkonular";
import { getCurriculumPageBySlug } from "@/lib/curriculum";
import {
  KAZANIM_PAGES,
  getKazanim,
  getKazanimlarByTopic,
} from "@/lib/kazanimlar";

const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? "https://soruatolyesi.com";

interface PageProps {
  params: Promise<{ slug: string; kazanim: string }>;
}

/**
 * İkinci seviye sayfaları build-time'da statik üret (Vercel CDN, Google ilk crawl).
 * İki tür: kazanım-kodu sayfaları (KAZANIM_PAGES) + alt-konu sayfaları
 * (ALTKONU_PAGES). Aynı route'u paylaşırlar; slug uzayları çakışmaz (kazanım =
 * "m-5-2-3", alt-konu = "kesirlerle-toplama-cikarma").
 */
export function generateStaticParams() {
  return [
    ...KAZANIM_PAGES.map((k) => ({ slug: k.topicSlug, kazanim: k.kazanimSlug })),
    ...ALTKONU_PAGES.map((a) => ({ slug: a.topicSlug, kazanim: a.slug })),
  ];
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug, kazanim } = await params;

  // Alt-konu sayfası mı? (doğal-dil sorgu odaklı title/description)
  const ak = getAltKonu(slug, kazanim);
  if (ak) {
    const akTitle = `${ak.grade}. Sınıf ${ak.title} Çalışma Kağıdı`;
    return {
      title: akTitle,
      description: ak.description,
      alternates: { canonical: `/calismalar/${slug}/${kazanim}` },
      openGraph: {
        title: `${akTitle} · Soru Atölyesi`,
        description: ak.description,
        url: `${SITE_URL}/calismalar/${slug}/${kazanim}`,
        type: "article",
      },
    };
  }

  const k = getKazanim(slug, kazanim);
  if (!k) return { title: "Bulunamadı" };

  // Title doğal-dil kazanım metninden başlar (kod ikincil) — arama-amaçlı SEO.
  const shortMetin = k.metin.length > 60 ? k.metin.slice(0, 60) + "…" : k.metin;
  const title = `${shortMetin} — ${k.grade}. Sınıf ${k.topicName} (${k.kod})`;
  const description = `${k.kod} kazanımı: ${k.metin} ${k.grade}. sınıf ${k.topicName.toLowerCase()} konusunda bu kazanıma özel çalışma kağıdı üret — PDF, cevap anahtarı ve adım adım çözüm dahil.`;

  return {
    title,
    description,
    alternates: { canonical: `/calismalar/${slug}/${kazanim}` },
    openGraph: {
      title: `${title} · Soru Atölyesi`,
      description,
      url: `${SITE_URL}/calismalar/${slug}/${kazanim}`,
      type: "article",
    },
  };
}

export default async function KazanimDetailPage({ params }: PageProps) {
  const { slug, kazanim } = await params;

  // Önce alt-konu (SEO-only landing); bulamazsa kazanım-kodu sayfası.
  const ak = getAltKonu(slug, kazanim);
  if (ak) return <AltKonuLanding ak={ak} />;

  const k = getKazanim(slug, kazanim);
  if (!k) notFound();

  const topic = getCurriculumPageBySlug(slug);
  const siblings = getKazanimlarByTopic(slug).filter(
    (s) => s.kazanimSlug !== k.kazanimSlug,
  );
  const generateHref = `/generate?grade=${k.grade}&topic=${k.topicId}&kazanim=${encodeURIComponent(k.kod)}`;

  const hintRows: { label: string; value?: string }[] = [
    { label: "Kolay", value: k.hints.kolay },
    { label: "Orta", value: k.hints.orta },
    { label: "Zor", value: k.hints.zor },
  ].filter((h) => h.value);

  return (
    <>
      <JsonLd
        id="kazanim-schema"
        data={learningResourceSchema({
          grade: k.grade,
          topicName: `${k.topicName} (${k.kod})`,
          description: k.metin,
          url: `${SITE_URL}/calismalar/${slug}/${kazanim}`,
        })}
      />

      <section className="border-b bg-gradient-to-b from-primary/5 to-transparent py-16">
        <div className="container max-w-4xl">
          {/* Breadcrumb — SEO + gezinme */}
          <nav className="mb-6 flex flex-wrap items-center gap-1 text-sm text-muted-foreground">
            <Link href="/calismalar" className="inline-flex items-center gap-1 hover:text-foreground">
              <GraduationCap className="h-4 w-4" /> Konular
            </Link>
            <ChevronRight className="h-3.5 w-3.5" />
            <Link href={`/calismalar/${slug}`} className="hover:text-foreground">
              {k.grade}. Sınıf {k.topicName}
            </Link>
            <ChevronRight className="h-3.5 w-3.5" />
            <span className="font-mono text-foreground">{k.kod}</span>
          </nav>

          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-accent px-3 py-1 text-xs font-medium text-accent-foreground">
            <Target className="h-3 w-3" />
            {k.grade}. Sınıf · MEB Kazanımı {k.kod}
          </div>
          <h1 className="text-balance text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            {k.metin}
          </h1>
          <p className="mt-5 text-lg text-muted-foreground">
            <span className="font-mono text-primary">{k.kod}</span> kazanımına özel,{" "}
            {k.grade}. sınıf {k.topicName.toLowerCase()} çalışma kağıdını saniyeler
            içinde hazırla — PDF, cevap anahtarı ve adım adım çözüm dahil.
          </p>
          <div className="mt-8">
            <TrackedGenerateLink
              href={generateHref}
              source="kazanim"
              grade={k.grade}
              topic={k.topicId}
              size="lg"
              className="gap-2"
            >
              Bu kazanıma özel kağıt üret <ArrowRight className="h-4 w-4" />
            </TrackedGenerateLink>
          </div>
        </div>
      </section>

      {hintRows.length > 0 && (
        <section className="py-16">
          <div className="container max-w-4xl">
            <h2 className="text-2xl font-bold tracking-tight text-foreground">
              Zorluk seviyelerine göre ne sorulur?
            </h2>
            <p className="mt-2 text-muted-foreground">
              Bu kazanımda kolay, orta ve zor seviyelerde tipik olarak şu beceriler
              ölçülür:
            </p>
            <div className="mt-8 grid gap-4 md:grid-cols-3">
              {hintRows.map((h) => (
                <div key={h.label} className="rounded-xl border bg-card p-5">
                  <span className="text-xs font-semibold uppercase tracking-wider text-primary">
                    {h.label}
                  </span>
                  <p className="mt-2 text-sm leading-relaxed text-foreground">
                    {h.value}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      <section className="bg-card py-16">
        <div className="container max-w-3xl text-center">
          <h2 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            {k.kod} için çalışma kağıdını hemen üret
          </h2>
          <p className="mt-3 text-muted-foreground">
            Soru sayısı, zorluk ve soru tipini sen seç; sistem bu kazanıma hizalı
            soruları üretir, denetimden geçirir ve PDF olarak hazırlar.
          </p>
          <TrackedGenerateLink
            href={generateHref}
            source="kazanim_footer"
            grade={k.grade}
            topic={k.topicId}
            size="lg"
            className="mt-6 gap-2 px-8"
          >
            Şimdi üret <ArrowRight className="h-4 w-4" />
          </TrackedGenerateLink>
        </div>
      </section>

      {(siblings.length > 0 || topic) && (
        <section className="py-16">
          <div className="container max-w-4xl space-y-8">
            {siblings.length > 0 && (
              <div>
                <h2 className="mb-4 text-xl font-semibold text-foreground">
                  {k.grade}. Sınıf {k.topicName} — diğer kazanımlar
                </h2>
                <div className="grid gap-3 sm:grid-cols-2">
                  {siblings.map((s) => (
                    <Link
                      key={s.kazanimSlug}
                      href={`/calismalar/${s.topicSlug}/${s.kazanimSlug}`}
                      className="rounded-lg border bg-card p-3 text-sm hover:border-primary/50"
                    >
                      <span className="font-mono text-xs text-primary">{s.kod}</span>
                      <span className="mt-1 block text-foreground">
                        {s.metin.length > 70 ? s.metin.slice(0, 70) + "…" : s.metin}
                      </span>
                    </Link>
                  ))}
                </div>
              </div>
            )}
            <Link
              href={`/calismalar/${slug}`}
              className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
            >
              ← {k.grade}. Sınıf {k.topicName} konusunun tüm çalışma kağıtları
            </Link>
          </div>
        </section>
      )}

      <Footer />
    </>
  );
}
