import Image from "next/image";
import Link from "next/link";
import { Check } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-slate-800 bg-slate-900 text-slate-100">
      <div className="container py-12">
        <div className="grid gap-8 md:grid-cols-4">
          <div>
            <Image
              src="/logo-dark.svg"
              alt="Quiz Marketi"
              width={170}
              height={36}
              className="h-9 w-auto"
            />
            <p className="mt-4 max-w-xs text-sm opacity-70">
              MEB müfredatına %100 uyumlu matematik çalışma kağıdı üreticisi.
            </p>
          </div>
          <FooterColumn
            title="Ürün"
            links={[
              { label: "Üretici", href: "/generate" },
              { label: "Özellikler", href: "/features" },
              { label: "Fiyatlandırma", href: "/pricing" },
              { label: "SSS", href: "/faq" },
            ]}
          />
          <FooterColumn
            title="Hukuki"
            links={[
              { label: "KVKK Aydınlatma", href: "/legal/kvkk" },
              { label: "Kullanım Koşulları", href: "/legal/terms" },
              { label: "Gizlilik", href: "/legal/privacy" },
            ]}
          />
          <FooterColumn
            title="İletişim"
            links={[
              { label: "destek@quizmarketi.com", href: "mailto:destek@quizmarketi.com" },
              { label: "Twitter / X", href: "#" },
              { label: "Instagram", href: "#" },
            ]}
          />
        </div>
        <div className="mt-10 flex flex-col items-center justify-between gap-3 border-t border-slate-800 pt-6 text-xs opacity-60 sm:flex-row">
          <p>© 2026 Quiz Marketi · MEB müfredatına uyumlu, eğitim için.</p>
          <p className="inline-flex items-center gap-1.5">
            <Check className="h-3 w-3" />
            Türkiye&apos;de geliştirildi
          </p>
        </div>
      </div>
    </footer>
  );
}

function FooterColumn({
  title,
  links,
}: {
  title: string;
  links: { label: string; href: string }[];
}) {
  return (
    <div>
      <p className="text-sm font-semibold">{title}</p>
      <ul className="mt-4 space-y-2 text-sm opacity-70">
        {links.map((l, i) => (
          <li key={i}>
            <Link href={l.href} className="hover:opacity-100">
              {l.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
