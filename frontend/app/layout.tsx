import type { Metadata } from "next";
import { Inter, Manrope } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import { trTR } from "@clerk/localizations";
import { Toaster } from "sonner";

import { ThemeProvider } from "@/components/theme-provider";
import TopNavBar from "@/components/TopNavBar";

import "./globals.css";

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

export const metadata: Metadata = {
  title: "Quiz Marketi — MEB matematik çalışma kağıdı üretim sistemi",
  description:
    "MEB matematik müfredatı (1.→7. sınıf) kapsamında, seçilen kazanım koduna göre çalışma kağıdı üreten otomatik sistem. PDF çıktı, cevap anahtarı ve adım adım çözüm dahil.",
  icons: { icon: "/favicon.svg" },
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
            enableSystem
            disableTransitionOnChange
          >
            <div className="flex min-h-screen flex-col">
              <TopNavBar />
              <main className="flex-1">{children}</main>
            </div>
            <Toaster richColors position="top-center" />
          </ThemeProvider>
        </body>
      </html>
    </ClerkProvider>
  );
}
