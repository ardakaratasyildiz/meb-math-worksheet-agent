import type { MetadataRoute } from "next";

// PWA manifest — Next.js bunu /manifest.webmanifest olarak servis eder ve
// <link rel="manifest"> ekler. Kurulabilir uygulama + "ana ekrana ekle".
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Soru Atölyesi — MEB matematik",
    short_name: "Soru Atölyesi",
    description:
      "MEB matematik çalışma kağıdı üret, site içinde test gibi çöz, gelişimini gör.",
    start_url: "/",
    scope: "/",
    display: "standalone",
    orientation: "portrait",
    background_color: "#ffffff",
    theme_color: "#2563eb",
    lang: "tr",
    categories: ["education"],
    icons: [
      { src: "/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
      { src: "/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
      {
        src: "/icon-maskable-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ],
  };
}
