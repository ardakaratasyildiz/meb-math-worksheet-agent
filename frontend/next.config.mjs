// Sprint 12-B cache-bust 2026-05-19 — tüm route'lar (/generate, /history, /features)
// Vercel'de 404 dönüyordu; trivial config touch ile rebuild zorla.
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Backend (FastAPI) için proxy — Codespaces ve prod'da
  // NEXT_PUBLIC_API_URL üzerinden direkt çağrılır (CORS ile).
  async rewrites() {
    const apiUrl = process.env.BACKEND_INTERNAL_URL;
    if (!apiUrl) return [];
    return [
      {
        source: "/api/backend/:path*",
        destination: `${apiUrl}/:path*`,
      },
    ];
  },
  // SEO: eski vercel.app domain'inden gelen istekleri yeni domain'e kalıcı (301)
  // yönlendir. Google'da indexlenmiş eski URL'ler varsa otoriteyi yeniye taşır
  // ve duplicate content cezasını önler. Host bazlı match → tüm path'leri taşır.
  async redirects() {
    return [
      {
        source: "/:path*",
        has: [
          {
            type: "host",
            value: "meb-math-worksheet-agent.vercel.app",
          },
        ],
        destination: "https://soruatolyesi.com/:path*",
        permanent: true,
      },
      // www → apex (consistency + SEO canonical net)
      {
        source: "/:path*",
        has: [
          {
            type: "host",
            value: "www.soruatolyesi.com",
          },
        ],
        destination: "https://soruatolyesi.com/:path*",
        permanent: true,
      },
    ];
  },
};

export default nextConfig;
