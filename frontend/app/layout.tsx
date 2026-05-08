import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import { trTR } from "@clerk/localizations";
import { dark } from "@clerk/themes";
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
  title: "SheetGen — MEB Matematik Üretici",
  description:
    "MEB müfredatına %100 uyumlu (1-7. sınıf) matematik çalışma kağıtlarını saniyeler içinde üretin.",
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
        baseTheme: dark,
        variables: { colorPrimary: "hsl(161, 84%, 42%)" },
      }}
    >
      <html lang="tr" suppressHydrationWarning>
        <body className={`${inter.variable} font-sans antialiased`}>
          <ThemeProvider
            attribute="class"
            defaultTheme="dark"
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
