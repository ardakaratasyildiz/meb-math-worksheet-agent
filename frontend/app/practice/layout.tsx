import * as React from "react";

export const metadata = {
  title: "Çöz & Geliş · Soru Atölyesi",
  description:
    "Soru üret, site içinde test gibi çöz, kaç doğru kaç yanlış yaptığını gör ve eksik kazanımlarına göre pratik yap.",
};

// /practice nested layout — kişisel öğrenme alanı. Login zorunlu (middleware).
// Mevcut /generate (PDF) akışından tamamen ayrı yüzey.
export default function CozLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // .practice-theme → öğrenci alanına özel sıcak/oyunsu tema (bkz. globals.css).
  return (
    <div className="practice-theme min-h-screen">
      <div className="container py-8">{children}</div>
    </div>
  );
}
