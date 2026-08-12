import Link from "next/link";
import {
  ArrowRight,
  BookOpen,
  Check,
  FileCheck,
  Hash,
  Minus,
  ShieldCheck,
  Sparkles,
  Zap,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Footer } from "@/components/Footer";
import { PageHeader, SectionHeader } from "@/components/PageHeader";
import { hasMultipleSubjects } from "@/lib/subjects";

export const metadata = {
  title: "Özellikler · Soru Atölyesi",
  description:
    "Soru Atölyesi'nin sistem özellikleri: kazanım kodu bazlı üretim, iki aşamalı denetim, anlamsal benzerlik denetimi, A4 PDF çıktı.",
};

function getFeatures(multi: boolean) {
  return [
  {
    icon: <BookOpen className="h-5 w-5" />,
    title: "Kazanım kodu bazlı üretim",
    body: multi
      ? "Üretim talebi ders, sınıf, konu ve kazanım kodu seçilerek yapılır. PDF'teki her sorunun yanında ilgili MEB kazanım kodu (örn. M.5.2.1, F.6.1.2) yer alır. 1.→8. sınıf MEB müfredatı — Matematik, Fen, Türkçe, Sosyal ve İngilizce (8. sınıf LGS hazırlık dahil) — kapsamındadır."
      : "Üretim talebi sınıf, konu ve kazanım kodu seçilerek yapılır. PDF'teki her sorunun yanında ilgili MEB kazanım kodu (örn. M.5.2.1.1) yer alır. 1.→8. sınıf MEB matematik müfredatı (8. sınıf LGS hazırlık dahil) kapsamındadır.",
  },
  {
    icon: <ShieldCheck className="h-5 w-5" />,
    title: "Üretim sonrası iki aşamalı denetim",
    body: multi
      ? "Üretilen her soru iki katmanlı denetimden geçer: önce içerik doğruluğu (matematikte sembolik hesap motoru SymPy ile aritmetik denetim), ardından ikinci bir model tarafından kazanım uyumu ve zorluk uyumu denetimi. Bu denetimleri geçemeyen sorular yeniden üretilir."
      : "Üretilen her soru iki katmanlı denetimden geçer: önce sembolik hesap motoru (SymPy) ile aritmetik denetim, ardından ikinci bir model tarafından kazanım uyumu ve zorluk uyumu denetimi. Bu denetimleri geçemeyen sorular yeniden üretilir.",
  },
  {
    icon: <Sparkles className="h-5 w-5" />,
    title: "Anlamsal benzerlik denetimi",
    body: "Aynı sınıf, konu, kazanım ve zorluk parametreleri ile yapılan tekrar üretimlerde, önceki üretimlerdeki sorulara yüksek cosine benzerliği gösteren adaylar üretim havuzundan elenir. Bu sayede tekrar üretim her seferinde farklı bir soru kümesi getirir.",
  },
  {
    icon: <FileCheck className="h-5 w-5" />,
    title: "Cevap anahtarı ve adım adım çözüm",
    body: "Üretilen her PDF'in son bölümünde cevap anahtarı (her sorunun yanında ilgili kazanım kodu) ve adım adım çözüm sayfası yer alır. Cevap anahtarı, öğretmenin değerlendirme süresini düşürmek üzere tasarlanmıştır.",
  },
  {
    icon: <Zap className="h-5 w-5" />,
    title: "Önbellek destekli yeniden indirme",
    body: "İlk üretim ortalama 30 saniye sürer. Aynı parametre setiyle yapılan tekrar talepler önbellekten döner ve aylık kotadan düşmez. PDF üretimi DejaVu yazı tipi ile yapılır; Türkçe karakterler eksiksiz işlenir.",
  },
  {
    icon: <Hash className="h-5 w-5" />,
    title: "İzlenebilir kazanım kodları",
    body: "Her soru çıktısında ilgili MEB kazanım kodu açıkça görünür. Bu sayede öğrencinin eksik kaldığı kazanımlar belge üzerinden takip edilebilir, sınıf bazında raporlanabilir.",
  },
  ];
}

const COMPARE = [
  {
    feature: "Üretilen sorunun yanında kazanım kodu görünür",
    classic: false,
    quiz: true,
  },
  {
    feature: "Cevap anahtarı PDF içinde",
    classic: "Genelde ayrı belge",
    quiz: true,
  },
  {
    feature: "Adım adım çözüm",
    classic: "Kısıtlı",
    quiz: true,
  },
  {
    feature: "Aynı kazanım için sürekli farklı yeni sorular",
    classic: false,
    quiz: true,
  },
  {
    feature: "Zorluk düzeyi seçimi",
    classic: "Sabit",
    quiz: true,
  },
  {
    feature: "Aritmetik doğruluk denetimi",
    classic: "Manuel",
    quiz: "Otomatik (SymPy)",
  },
  {
    feature: "PDF teslim süresi",
    classic: "Baskı/satın alma",
    quiz: "Ortalama 30 sn",
  },
];

export default function FeaturesPage() {
  const multi = hasMultipleSubjects();
  const FEATURES = getFeatures(multi);
  return (
    <>
      <PageHeader
        eyebrow="Özellikler"
        title="Sistem özellikleri"
        body={
          multi
            ? "Soru Atölyesi, MEB müfredatı kapsamında (Matematik, Fen, Türkçe, Sosyal ve İngilizce) kazanım kodu bazlı çalışma kağıdı üreten bir sistemdir. Aşağıda üretim akışını ve çıktıyı belirleyen temel özellikler yer almaktadır."
            : "Soru Atölyesi, MEB matematik müfredatı kapsamında kazanım kodu bazlı çalışma kağıdı üreten bir sistemdir. Aşağıda üretim akışını ve çıktıyı belirleyen temel özellikler yer almaktadır."
        }
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
            title="Basılı kaynaklarla karşılaştırma"
            body="Aşağıdaki tablo, basılı çalışma kitapları/dergiler ile Soru Atölyesi üretim sistemi arasındaki ölçülebilir farkları gösterir."
          />
          <div className="mt-12 overflow-hidden rounded-xl border">
            <table className="w-full text-sm">
              <thead className="bg-muted">
                <tr>
                  <th className="px-5 py-3 text-left font-semibold text-foreground">
                    Özellik
                  </th>
                  <th className="px-5 py-3 text-center font-semibold text-muted-foreground">
                    Basılı kaynak
                  </th>
                  <th className="px-5 py-3 text-center font-semibold text-primary">
                    Soru Atölyesi
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border bg-background">
                {COMPARE.map((c, i) => (
                  <tr key={i}>
                    <td className="px-5 py-3.5 text-foreground">{c.feature}</td>
                    <td className="px-5 py-3.5 text-center text-muted-foreground">
                      {c.classic === false ? (
                        <Minus className="mx-auto h-4 w-4 text-muted-foreground" />
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
              Sistemi denemek için
            </h2>
            <p className="text-base text-muted-foreground">
              Erken kullanım dönemindeki tüm hesaplara ayda 10 çalışma kağıdı
              kotası tanınmaktadır (günde en çok 2). Hesap açmak için yalnızca
              e-posta yeterlidir.
            </p>
            <Button asChild size="lg" className="gap-2 px-8">
              <Link href="/sign-up">
                Hesap aç <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
      </section>

      <Footer />
    </>
  );
}
