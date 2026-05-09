import Link from "next/link";
import {
  ArrowRight,
  BookOpen,
  Check,
  FileCheck,
  Hash,
  ShieldCheck,
  Sparkles,
  X,
  Zap,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Footer } from "@/components/Footer";
import { PageHeader, SectionHeader } from "@/components/PageHeader";

export const metadata = {
  title: "Özellikler · Quiz Marketi",
  description:
    "Quiz Marketi'nin sunduğu tüm özellikler — MEB müfredatı uyumu, iki katmanlı kalite kontrol, otomatik cevap anahtarı ve daha fazlası.",
};

const FEATURES = [
  {
    icon: <BookOpen className="h-5 w-5" />,
    title: "MEB müfredatı %100 uyum",
    body: "1.→7. sınıf tüm kazanımlar destekleniyor. Üretilen her sorunun yanında MEB kazanım kodu görünür — denetlenebilir, takip edilebilir.",
  },
  {
    icon: <ShieldCheck className="h-5 w-5" />,
    title: "İki katmanlı kalite kontrol",
    body: "Önce otomatik aritmetik denetim (matematiksel hatalar elenir), sonra ikinci bir yapay zekâ kontrolü (kazanım + zorluk uyumu denetlenir). Geçmeyen sorular yeniden üretilir.",
  },
  {
    icon: <Zap className="h-5 w-5" />,
    title: "Saniyeler içinde PDF",
    body: "İlk üretim ortalama 30 saniye; aynı kombinasyonu tekrar indirirken anında. Türkçe karakter problemi yok, A4 baskı için optimize edilmiş.",
  },
  {
    icon: <FileCheck className="h-5 w-5" />,
    title: "Cevap anahtarı + adım adım çözüm",
    body: "Her PDF'in sonunda otomatik cevap anahtarı ve adım adım çözüm sayfası. Düzeltme dakikalar değil saniyeler — öğretmenin zamanı geri verilir.",
  },
  {
    icon: <Hash className="h-5 w-5" />,
    title: "Kazanım kodu görünür",
    body: "Her sorunun yanında ilgili MEB kazanım kodu (örn. M.5.2.1.1). Hangi öğrencinin hangi kazanımda eksik olduğunu izlemek artık net.",
  },
  {
    icon: <Sparkles className="h-5 w-5" />,
    title: "Akıllı çeşitlilik",
    body: "Aynı sınıf+konu+kazanım+zorluk kombinasyonunu 10 kez ürettiğinde 10 farklı set alırsın. Tekrar yok — anlamsal benzerlik denetimi sayesinde.",
  },
];

const COMPARE = [
  {
    feature: "MEB kazanımına bire bir hizalama",
    classic: false,
    quiz: true,
  },
  {
    feature: "Otomatik cevap anahtarı",
    classic: false,
    quiz: true,
  },
  {
    feature: "Adım adım çözüm",
    classic: "Genelde yok",
    quiz: true,
  },
  {
    feature: "Aynı konuyu istediğin sayıda farklı varyantta üretim",
    classic: false,
    quiz: true,
  },
  {
    feature: "Zorluk seviyesi seçimi",
    classic: "Sınırlı",
    quiz: true,
  },
  {
    feature: "Aritmetik doğruluk garantisi",
    classic: "Manuel kontrol",
    quiz: "Otomatik",
  },
  {
    feature: "Anında PDF",
    classic: false,
    quiz: true,
  },
  {
    feature: "Maliyet (yıllık)",
    classic: "Birden fazla dergi/kitap",
    quiz: "Tek abonelik",
  },
];

export default function FeaturesPage() {
  return (
    <>
      <PageHeader
        eyebrow="Özellikler"
        title="Bir dergiden değil, üreticiden"
        body="Quiz Marketi sadece soru göstermez — üretir, denetler, hizalar, kanıtlar. Klasik kaynaklarla farkımız tek tek aşağıda."
      />

      <section className="py-20">
        <div className="container">
          <div className="grid gap-6 md:grid-cols-2">
            {FEATURES.map((f, i) => (
              <div
                key={i}
                className="flex flex-col gap-3 rounded-xl border bg-card p-6"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                  {f.icon}
                </div>
                <h3 className="text-lg font-semibold text-foreground">
                  {f.title}
                </h3>
                <p className="text-sm leading-relaxed text-muted-foreground">
                  {f.body}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-card py-20">
        <div className="container max-w-4xl">
          <SectionHeader
            eyebrow="Karşılaştırma"
            title="Klasik kaynak vs Quiz Marketi"
          />
          <div className="mt-12 overflow-hidden rounded-xl border">
            <table className="w-full text-sm">
              <thead className="bg-muted">
                <tr>
                  <th className="px-5 py-3 text-left font-semibold text-foreground">
                    Özellik
                  </th>
                  <th className="px-5 py-3 text-center font-semibold text-muted-foreground">
                    Klasik dergi/kitap
                  </th>
                  <th className="px-5 py-3 text-center font-semibold text-primary">
                    Quiz Marketi
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border bg-background">
                {COMPARE.map((c, i) => (
                  <tr key={i}>
                    <td className="px-5 py-3.5 text-foreground">{c.feature}</td>
                    <td className="px-5 py-3.5 text-center text-muted-foreground">
                      {c.classic === false ? (
                        <X className="mx-auto h-4 w-4 text-destructive" />
                      ) : c.classic === true ? (
                        <Check className="mx-auto h-4 w-4 text-primary" />
                      ) : (
                        <span className="text-xs">{c.classic}</span>
                      )}
                    </td>
                    <td className="px-5 py-3.5 text-center">
                      {c.quiz === true ? (
                        <Check className="mx-auto h-4 w-4 text-primary" />
                      ) : (
                        <span className="text-xs font-medium text-primary">
                          {c.quiz}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="py-20">
        <div className="container">
          <div className="mx-auto flex max-w-3xl flex-col items-center gap-6 rounded-2xl border bg-card p-12 text-center">
            <h2 className="text-3xl font-bold tracking-tight text-foreground">
              Şimdi ücretsiz dene.
            </h2>
            <p className="text-base text-muted-foreground">
              Kart bilgisi gerekmiyor. İlk kağıdını 30 saniyede üret.
            </p>
            <Button asChild size="lg" className="gap-2 px-8">
              <Link href="/generate">
                Ücretsiz başla <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
      </section>

      <Footer />
    </>
  );
}
