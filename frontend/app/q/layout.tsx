import * as React from "react";

export const metadata = {
  title: "Quiz Çöz · Soru Atölyesi",
  description:
    "Sana paylaşılan quiz'i site içinde çöz, anında kaç doğru kaç yanlış yaptığını gör.",
};

// Paylaşılan quiz çözme yüzeyi — PUBLIC (login GEREKMEZ; middleware'de /q korumalı
// değil). /practice'un kişisel/login-gated alanından ayrı; aynı sıcak/oyunsu temayı kullanır.
export default function SharedQuizLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="practice-theme min-h-screen">
      <div className="container py-8">{children}</div>
    </div>
  );
}
