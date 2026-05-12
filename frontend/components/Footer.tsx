import Image from "next/image";
import Link from "next/link";
import { Check } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-zinc-800 bg-zinc-900 text-zinc-100">
      <div className="container py-12">
        <div className="grid gap-8 md:grid-cols-4">
          <div>
            <Image
              src="/logo.png"
              alt="Soru Atölyesi"
              width={386}
              height={256}
              className="h-9 w-auto brightness-0 invert"
            />
            <p className="mt-4 max-w-xs text-sm opacity-70">
              MEB matematik müfredatı kapsamında otomatik çalışma kağıdı üretim
              sistemi. 1.→7. sınıf kazanım kodu bazlı üretim.
            </p>
          </div>
          <FooterColumn
            title="Ürün"
            links={[
              { label: "Üretim", href: "/generate" },
              { label: "Özellikler", href: "/features" },
              { label: "Fiyatlandırma", href: "/pricing" },
              { label: "Sıkça Sorulanlar", href: "/faq" },
            ]}
          />
          <FooterColumn
            title="Hukuki"
            links={[
              { label: "KVKK Aydınlatma Metni", href: "/legal/kvkk" },
              { label: "Kullanım Koşulları", href: "/legal/terms" },
              { label: "Gizlilik Politikası", href: "/legal/privacy" },
            ]}
          />
          <FooterColumn
            title="İletişim"
            links={[
              {
                label: "destek@soruatolyesi.com",
                href: "mailto:destek@soruatolyesi.com",
              },
              { label: "Twitter / X", href: "#", disabled: true },
              { label: "Instagram", href: "#", disabled: true },
            ]}
          />
        </div>
        <div className="mt-10 flex flex-col items-center justify-between gap-3 border-t border-zinc-800 pt-6 text-xs opacity-60 sm:flex-row">
          <p>© 2026 Soru Atölyesi · Eğitim amaçlı kullanım için tasarlanmıştır.</p>
          <p className="inline-flex items-center gap-1.5">
            <Check className="h-3 w-3" />
            Türkiye&apos;de geliştirildi
          </p>
        </div>
      </div>
    </footer>
  );
}

type FooterLink = { label: string; href: string; disabled?: boolean };

function FooterColumn({
  title,
  links,
}: {
  title: string;
  links: FooterLink[];
}) {
  return (
    <div>
      <p className="text-sm font-semibold">{title}</p>
      <ul className="mt-4 space-y-2 text-sm opacity-70">
        {links.map((l, i) => (
          <li key={i}>
            {l.disabled ? (
              <span aria-disabled="true" className="cursor-not-allowed opacity-50">
                {l.label}
              </span>
            ) : (
              <Link href={l.href} className="hover:opacity-100">
                {l.label}
              </Link>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
