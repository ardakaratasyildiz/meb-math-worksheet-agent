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
};

export default nextConfig;
