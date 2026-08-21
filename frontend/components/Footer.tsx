import Image from "next/image";
import Link from "next/link";
import { Check } from "lucide-react";

import { hasMultipleSubjects } from "@/lib/subjects";

export function Footer() {
  const multi = hasMultipleSubjects();
  return (
    <footer className="border-t border-white/10 bg-[#241a36] text-zinc-100">
      <div className="container py-12">
        <div className="grid gap-8 md:grid-cols-4">
          <div>
            <Image
              src="/logo.png"
              alt="Soru Atölyesi"
              width={706}
              height={173}
              className="h-9 w-auto rounded-md [filter:hue-rotate(32deg)_saturate(1.3)]"
            />
            <p className="mt-4 max-w-xs text-sm opacity-70">
              {multi
                ? "MEB müfredatı kapsamında otomatik çalışma kağıdı üretim sistemi — Matematik, Fen, Türkçe, Sosyal ve İngilizce. 1.→8. sınıf (LGS hazırlık dahil) kazanım kodu bazlı üretim."
                : "MEB matematik müfredatı kapsamında otomatik çalışma kağıdı üretim sistemi. 1.→8. sınıf (LGS hazırlık dahil) kazanım kodu bazlı üretim."}
            </p>
          </div>
          <FooterColumn
            title="Ürün"
            links={[
              { label: "Üretim", href: "/generate" },
              { label: "LGS Matematik Hazırlık", href: "/lgs-matematik" },
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
              { label: "Hesabımı Sil", href: "/hesap/sil" },
            ]}
          />
          <FooterColumn
            title="İletişim"
            links={[
              {
                label: "destek@soruatolyesi.com",
                href: "mailto:destek@soruatolyesi.com",
              },
              {
                label: "Instagram",
                href: "https://www.instagram.com/soruatolyesi.com2026",
                external: true,
              },
              {
                label: "Pinterest",
                href: "https://pin.it/34V3999cs",
                external: true,
              },
              {
                label: "YouTube",
                href: "https://www.youtube.com/@soruatolyesi-s2g",
                external: true,
              },
            ]}
          />
        </div>
        {/*
          Bağımsızlık bildirimi + müfredat bilgisinin resmi kaynakları.
          Google Play "Misleading Claims" politikası bunu mağaza açıklamasında ve
          uygulama içinde zorunlu tutuyor; web de aynı iddiayı ("MEB müfredatı")
          kurduğu için künye burada da durur. Mobil karşılığı:
          apps/mobile/src/lib/legal.ts + /about ekranı.
        */}
        <div className="mt-10 border-t border-white/10 pt-6 text-xs leading-relaxed opacity-60">
          <p>
            Soru Atölyesi bağımsız bir eğitim girişimidir. T.C. Millî Eğitim Bakanlığı
            (MEB) ile bağlantılı, ortaklı veya MEB tarafından onaylı değildir; MEB&apos;i
            temsil etmez. Ünite ve kazanım başlıkları MEB&apos;in kamuya açık öğretim
            programlarına dayanır; sorular ve çözümler yapay zekâ ile üretilir, resmi MEB
            yayını değildir.
          </p>
          <p className="mt-2">
            Resmî kaynaklar:{" "}
            {[
              { label: "meb.gov.tr", href: "https://www.meb.gov.tr" },
              { label: "tymm.meb.gov.tr", href: "https://tymm.meb.gov.tr" },
              { label: "mufredat.meb.gov.tr", href: "https://mufredat.meb.gov.tr" },
            ].map((s, i) => (
              <span key={s.href}>
                {i > 0 ? " · " : ""}
                <a
                  href={s.href}
                  target="_blank"
                  rel="noopener noreferrer nofollow"
                  className="underline hover:opacity-100"
                >
                  {s.label}
                </a>
              </span>
            ))}
          </p>
        </div>
        <div className="mt-6 flex flex-col items-center justify-between gap-3 border-t border-white/10 pt-6 text-xs opacity-60 sm:flex-row">
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

type FooterLink = {
  label: string;
  href: string;
  disabled?: boolean;
  external?: boolean;
};

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
            ) : l.external ? (
              <a
                href={l.href}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:opacity-100"
              >
                {l.label}
              </a>
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
