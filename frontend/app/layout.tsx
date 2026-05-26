import type { Metadata } from "next";
import { Inter, Manrope } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import { trTR } from "@clerk/localizations";
import { Toaster } from "sonner";

import { Analytics } from "@/components/Analytics";
import { CookieConsent } from "@/components/CookieConsent";
import { ThemeProvider } from "@/components/theme-provider";
import TopNavBar from "@/components/TopNavBar";

import "./globals.css";
// Sprint 12-B / Phase C — KaTeX CSS (LaTeX math notation for salt_islem)
// Layout'ta tek seferlik yükleniyor; QuestionCard içinde rehype-katex parsed
// elementlerin doğru stilize olması için global gerekli.
import "katex/dist/katex.min.css";

const inter = Inter({
  subsets: ["latin", "latin-ext"],
  variable: "--font-inter",
  display: "swap",
});

const manrope = Manrope({
  subsets: ["latin", "latin-ext"],
  variable: "--font-manrope",
  display: "swap",
  weight: ["500", "600", "700", "800"],
});

// metadataBase — tüm relative OG/Twitter/canonical URL'lerin baz alacağı host.
// Vercel preview deploy'larda otomatik VERCEL_URL'e düşer (sosyal preview için OK).
const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ??
  (process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` : "https://soruatolyesi.com");

const SITE_NAME = "Soru Atölyesi";
const SITE_DESC =
  "MEB matematik müfredatı (1.→7. sınıf) için kazanım koduna göre çalışma kağıdı üreten otomatik sistem. PDF çıktı, cevap anahtarı ve adım adım çözüm dahil — öğretmenler ve veliler için.";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: `${SITE_NAME} — MEB matematik çalışma kağıdı üretici`,
    template: `%s · ${SITE_NAME}`,
  },
  description: SITE_DESC,
  keywords: [
    "MEB matematik",
    "çalışma kağıdı",
    "1. sınıf matematik",
    "2. sınıf matematik",
    "3. sınıf matematik",
    "4. sınıf matematik",
    "5. sınıf matematik",
    "6. sınıf matematik",
    "7. sınıf matematik",
    "matematik soru üretici",
    "kazanım kodu",
    "matematik PDF",
    "öğretmen kaynak",
    "ilkokul matematik",
    "ortaokul matematik",
  ],
  authors: [{ name: SITE_NAME, url: SITE_URL }],
  creator: SITE_NAME,
  publisher: SITE_NAME,
  applicationName: SITE_NAME,
  alternates: {
    canonical: "/",
  },
  // Sosyal paylaşımda (WhatsApp, Twitter, LinkedIn) zengin önizleme:
  openGraph: {
    type: "website",
    locale: "tr_TR",
    url: SITE_URL,
    siteName: SITE_NAME,
    title: `${SITE_NAME} — MEB matematik çalışma kağıdı üretici`,
    description: SITE_DESC,
    // og:image — frontend/app/opengraph-image.tsx Next.js tarafından otomatik
    // bu URL'e map edilir (manuel images: [...] belirtmeye gerek yok).
  },
  twitter: {
    card: "summary_large_image",
    title: `${SITE_NAME} — MEB matematik çalışma kağıdı üretici`,
    description: SITE_DESC,
  },
  // Default robots — public sayfalar index'lenir, admin/api ayrı robots.ts'te
  // disallow ediliyor.
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  icons: {
    icon: "/logo2.PNG",
    apple: "/logo2.PNG",
  },
  category: "education",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider
      localization={trTR}
      appearance={{
        variables: { colorPrimary: "hsl(224, 76%, 33%)" },
      }}
    >
      <html lang="tr" suppressHydrationWarning>
        <body
          className={`${inter.variable} ${manrope.variable} font-sans antialiased`}
        >
          <ThemeProvider
            attribute="class"
            defaultTheme="light"
            enableSystem={false}
            disableTransitionOnChange
          >
            <div className="flex min-h-screen flex-col">
              <TopNavBar />
              <main className="flex-1">{children}</main>
            </div>
            <Toaster richColors position="top-center" />
            <CookieConsent />
            <Analytics />
          </ThemeProvider>
        </body>
      </html>
    </ClerkProvider>
  );
}
