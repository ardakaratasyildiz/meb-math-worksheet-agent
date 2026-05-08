import Link from "next/link";
import { ArrowRight, BookOpen, Sparkles, Zap } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function LandingPage() {
  return (
    <div className="flex flex-col">
      {/* Hero */}
      <section className="relative overflow-hidden border-b">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,_hsl(var(--primary)/0.15),transparent_60%)]"
        />
        <div className="container flex flex-col items-center gap-6 py-24 text-center sm:py-32">
          <Badge variant="outline" className="border-primary/40 text-primary">
            <Sparkles className="mr-1 h-3 w-3" /> 1.→7. sınıf · MEB müfredatı
          </Badge>
          <h1 className="max-w-3xl text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
            Matematik çalışma kağıtları,{" "}
            <span className="bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
              30 saniyede
            </span>
            .
          </h1>
          <p className="max-w-2xl text-balance text-lg text-muted-foreground sm:text-xl">
            Sınıfı, kazanımı ve zorluğu seç — MEB müfredatına %100 uyumlu PDF
            çalışma kağıdını anında indir. 7000+ örnekle eğitilmiş üretim,
            yapay zekâ destekli kalite kontrol.
          </p>
          <div className="flex flex-col items-center gap-3 sm:flex-row">
            <Button asChild size="lg" className="gap-2">
              <Link href="/generate">
                Ücretsiz başla <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link href="#features">Nasıl çalışıyor?</Link>
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">
            Kayıt 30 saniye · Kredi kartı yok · İlk 100 kağıt ücretsiz
          </p>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="container py-20">
        <div className="grid gap-8 md:grid-cols-3">
          <FeatureCard
            icon={<BookOpen className="h-6 w-6" />}
            title="MEB müfredatı bire bir"
            body="1.→7. sınıf tüm kazanımlar; her kağıt belirlediğin kazanım koduna göre üretilir. Türkçe, KVKK uyumlu."
          />
          <FeatureCard
            icon={<Sparkles className="h-6 w-6" />}
            title="Kalite garantili üretim"
            body="Her soru SymPy ile aritmetik doğrulamadan, ardından LLM-as-judge ile kazanım/zorluk uyumundan geçer. Geçmeyen elenir."
          />
          <FeatureCard
            icon={<Zap className="h-6 w-6" />}
            title="Saniyeler içinde PDF"
            body="Üretim ortalama 30sn; cache hit'te 1sn. Tek tıkla A4 çalışma kağıdı + cevap anahtarı PDF olarak indir."
          />
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t bg-muted/30">
        <div className="container flex flex-col items-center justify-between gap-2 py-6 text-sm text-muted-foreground sm:flex-row">
          <p>© 2026 MEB Matematik Üretici · Eğitim için yapıldı.</p>
          <div className="flex gap-4">
            <Link href="/" className="hover:text-foreground">
              Gizlilik
            </Link>
            <Link href="/" className="hover:text-foreground">
              İletişim
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  body,
}: {
  icon: React.ReactNode;
  title: string;
  body: string;
}) {
  return (
    <div className="flex flex-col gap-3 rounded-xl border bg-card p-6 text-card-foreground transition-shadow hover:shadow-md">
      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent text-accent-foreground">
        {icon}
      </div>
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="text-sm text-muted-foreground">{body}</p>
    </div>
  );
}
