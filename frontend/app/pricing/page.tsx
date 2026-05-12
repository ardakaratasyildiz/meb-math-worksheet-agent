import Link from "next/link";
import { ArrowRight, Mail } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Footer } from "@/components/Footer";
import { PageHeader } from "@/components/PageHeader";

export const metadata = {
  title: "Fiyatlandırma · Soru Atölyesi",
  description:
    "Soru Atölyesi şu anda erken kullanım dönemindedir. Tüm kullanıcılar aylık 100 soru kotası ile ücretsiz kullanabilir.",
};

export default function PricingPage() {
  return (
    <>
      <PageHeader
        eyebrow="Fiyatlandırma"
        title="Erken kullanım dönemi"
        body="Soru Atölyesi şu anda erken kullanım dönemindedir. Tüm kullanıcılara aylık 100 soruluk ücretsiz kullanım hakkı tanınmaktadır. Ücretli abonelik seçenekleri ileriki aşamada duyurulacaktır."
      />

      <section className="container py-12">
        <div className="mx-auto max-w-2xl rounded-2xl border bg-card p-8 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-wider text-primary">
            Mevcut kullanım koşulları
          </p>
          <h2 className="mt-2 text-2xl font-bold tracking-tight">
            Aylık 100 soru — tüm özelliklere erişim
          </h2>
          <ul className="mt-6 space-y-3 text-sm text-foreground">
            <li>
              <span className="font-medium">Kapsam:</span> 1.→7. sınıf MEB
              matematik müfredatının tamamı, kazanım kodu bazlı üretim.
            </li>
            <li>
              <span className="font-medium">Kayıt:</span> E-posta adresi
              yeterlidir. Ödeme bilgisi alınmaz.
            </li>
            <li>
              <span className="font-medium">Çıktı:</span> Her üretimde A4 PDF
              dosyası — cevap anahtarı ve adım adım çözüm sayfası dahil.
            </li>
            <li>
              <span className="font-medium">Kota:</span> Hesap başına aylık 100
              soru. Aynı parametrelerle yapılan tekrar üretimler önbellekten
              gelir ve kotadan düşmez.
            </li>
          </ul>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Button asChild size="lg" className="gap-2">
              <Link href="/sign-up">
                Hesap aç <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline" className="gap-2">
              <Link href="mailto:destek@soruatolyesi.com?subject=Pro%20abonelik%20bildirimi">
                <Mail className="h-4 w-4" /> Pro plan bildirimi al
              </Link>
            </Button>
          </div>
        </div>

        <p className="mx-auto mt-8 max-w-2xl text-center text-xs text-muted-foreground">
          Pro abonelik bildirimini almak isteyenler için ön kayıt:{" "}
          <a
            href="mailto:destek@soruatolyesi.com"
            className="underline-offset-2 hover:underline"
          >
            destek@soruatolyesi.com
          </a>
        </p>
      </section>

      <Footer />
    </>
  );
}
