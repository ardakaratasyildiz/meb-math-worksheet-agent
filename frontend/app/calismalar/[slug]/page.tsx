import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowRight, BookOpen, CheckCircle2, FileText, GraduationCap, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Footer } from "@/components/Footer";
import { JsonLd, learningResourceSchema } from "@/components/JsonLd";
import { SampleQuestions } from "@/components/SampleQuestions";
import { CURRICULUM_PAGES, getCurriculumPageBySlug } from "@/lib/curriculum";
import { getKazanimlarByTopic } from "@/lib/kazanimlar";

const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? "https://soruatolyesi.com";

interface PageProps {
  params: Promise<{ slug: string }>;
}

/**
 * Tüm 38 sayfayı build-time'da statik render et. Vercel CDN'de cache'lenir,
 * Google ilk crawl'da hepsini görür. Yeni konu eklenince curriculum.ts'yi
 * güncelle, otomatik build'de sayfa açılır.
 */
export function generateStaticParams() {
  return CURRICULUM_PAGES.map((p) => ({ slug: p.slug }));
}

/**
 * SEO için per-page metadata — her landing page'in kendi title, description,
 * canonical ve og:image'ı olur. Long-tail arama sonuçlarında birbirini değil,
 * doğru sayfayı göstermek için kritik.
 */
export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const page = getCurriculumPageBySlug(slug);
  if (!page) return { title: "Bulunamadı" };

  const title = `${page.grade}. Sınıf ${page.topicName} — Çalışma Kağıdı`;
  const description = `${page.grade}. sınıf ${page.topicName.toLowerCase()} konusunda MEB kazanım kodu bazlı çalışma kağıdı üret. ${page.description}. ${page.kazanimCount} kazanım kapsanır; PDF + cevap anahtarı + adım adım çözüm.`;

  return {
    title,
    description,
    alternates: { canonical: `/calismalar/${slug}` },
    openGraph: {
      title: `${title} · Soru Atölyesi`,
      description,
      url: `${SITE_URL}/calismalar/${slug}`,
      type: "article",
    },
  };
}

export default async function CalismaDetailPage({ params }: PageProps) {
  const { slug } = await params;
  const page = getCurriculumPageBySlug(slug);
  if (!page) notFound();

  // Aynı sınıftaki diğer konular — internal linking için (SEO + UX).
  const sameGradeOthers = CURRICULUM_PAGES.filter(
    (p) => p.grade === page.grade && p.slug !== page.slug,
  );

  // Aynı konunun farklı sınıflardaki versiyonları — örn. "Geometri" 1.-7. sınıf
  // boyunca devam eder, vertical linking iyi olur.
  const sameTopicOtherGrades = CURRICULUM_PAGES.filter(
    (p) => p.topicId === page.topicId && p.grade !== page.grade,
  );

  // Bu konunun kazanımları — kazanım-seviyesi landing'lere iç link (SEO crawl).
  const kazanimlar = getKazanimlarByTopic(slug);

  const generateHref = `/generate?grade=${page.grade}&topic=${page.topicId}`;

  return (
    <>
      <JsonLd
        id="learning-resource-schema"
        data={learningResourceSchema({
          grade: page.grade,
          topicName: page.topicName,
          description: page.description,
          url: `${SITE_URL}/calismalar/${page.slug}`,
        })}
      />

      <section className="border-b bg-gradient-to-b from-primary/5 to-transparent py-16">
        <div className="container max-w-4xl">
          <Link
            href="/calismalar"
            className="mb-6 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
          >
            <GraduationCap className="h-4 w-4" />
            Tüm sınıflar ve konular
          </Link>
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-accent px-3 py-1 text-xs font-medium text-accent-foreground">
            <Sparkles className="h-3 w-3" />
            {page.grade}. Sınıf · {page.kazanimCount} kazanım
          </div>
          <h1 className="text-balance text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
            {page.grade}. Sınıf {page.topicName} —{" "}
            <span className="bg-gradient-to-r from-primary to-blue-500 bg-clip-text text-transparent">
              Çalışma Kağıdı
            </span>
          </h1>
          <p className="mt-5 text-lg text-muted-foreground">{page.description}</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button asChild size="lg" className="gap-2">
              <Link href={generateHref}>
                Çalışma kağıdı üret <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link href="/features">Sistem nasıl çalışır?</Link>
            </Button>
          </div>
        </div>
      </section>

      <section className="py-16">
        <div className="container max-w-4xl grid gap-8 md:grid-cols-2">
          <FeatureBlock
            icon={<BookOpen className="h-5 w-5 text-primary" />}
            title="MEB kazanım bazlı"
            body={`Bu kağıt, ${page.grade}. sınıf "${page.topicName}" başlığı altındaki ${page.kazanimCount} resmi MEB kazanım kodunu kapsar. Sorular kazanım metnine bağlı olarak üretilir.`}
          />
          <FeatureBlock
            icon={<FileText className="h-5 w-5 text-primary" />}
            title="Tam PDF çıktısı"
            body="Üretilen PDF üç bölümden oluşur: sorular, cevap anahtarı (kazanım kodu eşlenik) ve adım adım çözümler. A4 baskıya hazır."
          />
          <FeatureBlock
            icon={<CheckCircle2 className="h-5 w-5 text-primary" />}
            title="Çift denetimli"
            body="Üretilen her soru aritmetik denetim + kazanım uyumu denetiminden geçer. Geçemeyen sorular kullanıcıya gösterilmeden elenir."
          />
          <FeatureBlock
            icon={<Sparkles className="h-5 w-5 text-primary" />}
            title="Tekrar çakışmaz"
            body="Aynı parametrelerle yeniden üretim her seferinde farklı bir soru kümesi getirir; anlamsal benzerlik denetimi tekrarları engeller."
          />
        </div>
      </section>

      {/* Login'siz örnek soru önizlemesi — SEO için gerçek içerik + dönüşüm. */}
      <SampleQuestions
        slug={page.slug}
        grade={page.grade}
        topicId={page.topicId}
        topicName={page.topicName}
      />

      {kazanimlar.length > 0 && (
        <section className="py-16">
          <div className="container max-w-4xl">
            <h2 className="text-2xl font-bold tracking-tight text-foreground">
              Bu konunun MEB kazanımları
            </h2>
            <p className="mt-2 text-muted-foreground">
              Her kazanıma özel çalışma kağıdı üretebilirsin. Kazanıma tıkla,
              detayını gör ve o kazanıma hizalı soruları oluştur.
            </p>
            <div className="mt-8 grid gap-3 sm:grid-cols-2">
              {kazanimlar.map((k) => (
                <Link
                  key={k.kazanimSlug}
                  href={`/calismalar/${k.topicSlug}/${k.kazanimSlug}`}
                  className="rounded-lg border bg-card p-3 text-sm transition-colors hover:border-primary/50"
                >
                  <span className="font-mono text-xs text-primary">{k.kod}</span>
                  <span className="mt-1 block text-foreground">
                    {k.metin.length > 80 ? k.metin.slice(0, 80) + "…" : k.metin}
                  </span>
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      <section className="bg-card py-16">
        <div className="container max-w-3xl text-center">
          <h2 className="text-3xl font-bold tracking-tight text-foreground">
            {page.grade}. sınıf {page.topicName.toLowerCase()} çalışma kağıdını hemen üret
          </h2>
          <p className="mt-3 text-muted-foreground">
            Soru sayısı, zorluk seviyesi ve soru tipini sen belirle. PDF&apos;in birkaç saniyede hazır.
          </p>
          <Button asChild size="lg" className="mt-6 gap-2 px-8">
            <Link href={generateHref}>
              Şimdi üretmeye başla <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </section>

      {(sameGradeOthers.length > 0 || sameTopicOtherGrades.length > 0) && (
        <section className="py-16">
          <div className="container max-w-4xl space-y-10">
            {sameGradeOthers.length > 0 && (
              <div>
                <h2 className="mb-4 text-xl font-semibold text-foreground">
                  {page.grade}. Sınıfta diğer konular
                </h2>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {sameGradeOthers.map((p) => (
                    <Link
                      key={p.slug}
                      href={`/calismalar/${p.slug}`}
                      className="rounded-lg border bg-card p-3 text-sm font-medium hover:border-primary/50 hover:text-primary"
                    >
                      {p.topicName}
                    </Link>
                  ))}
                </div>
              </div>
            )}
            {sameTopicOtherGrades.length > 0 && (
              <div>
                <h2 className="mb-4 text-xl font-semibold text-foreground">
                  &quot;{page.topicName}&quot; konusu diğer sınıflarda
                </h2>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {sameTopicOtherGrades.map((p) => (
                    <Link
                      key={p.slug}
                      href={`/calismalar/${p.slug}`}
                      className="rounded-lg border bg-card p-3 text-sm font-medium hover:border-primary/50 hover:text-primary"
                    >
                      {p.grade}. Sınıf
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      <Footer />
    </>
  );
}

function FeatureBlock({
  icon,
  title,
  body,
}: {
  icon: React.ReactNode;
  title: string;
  body: string;
}) {
  return (
    <div className="rounded-lg border bg-card p-5">
      <div className="mb-2 flex items-center gap-2">
        {icon}
        <h3 className="font-semibold text-foreground">{title}</h3>
      </div>
      <p className="text-sm text-muted-foreground">{body}</p>
    </div>
  );
}
