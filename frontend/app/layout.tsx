import type { Metadata } from "next";
import { Inter } from "next/font/google";
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

export const metadata: Metadata = {
  title: "Quiz Marketi — MEB matematik çalışma kağıdı üretici",
  description:
    "MEB müfredatına %100 uyumlu (1-7. sınıf) matematik çalışma kağıtlarını yapay zekâ ile saniyeler içinde üret, PDF olarak indir.",
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
        variables: { colorPrimary: "hsl(244, 76%, 59%)" },
      }}
    >
      <html lang="tr" suppressHydrationWarning>
        <body className={`${inter.variable} font-sans antialiased`}>
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
