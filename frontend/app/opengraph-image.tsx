/**
 * Otomatik OG image — Next.js bu dosyayı /opengraph-image olarak servis eder
 * ve metadata.openGraph.images olarak otomatik bağlar. Manuel PNG yüklemeye
 * gerek yok; sosyal paylaşımlarda (WhatsApp, Twitter, LinkedIn) bu görsel çıkar.
 *
 * Edge runtime'da ImageResponse ile render edilir, hızlı.
 */
import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "Soru Atölyesi — MEB matematik çalışma kağıdı üretici";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function OGImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          background:
            "linear-gradient(135deg, #1e3a8a 0%, #2563eb 50%, #3b82f6 100%)",
          color: "white",
          fontFamily: "system-ui, -apple-system, sans-serif",
          padding: "80px",
        }}
      >
        <div
          style={{
            fontSize: 28,
            opacity: 0.85,
            letterSpacing: 2,
            textTransform: "uppercase",
            marginBottom: 24,
          }}
        >
          1. → 8. sınıf · LGS hazırlık · MEB müfredatı
        </div>
        <div
          style={{
            fontSize: 84,
            fontWeight: 800,
            letterSpacing: -2,
            lineHeight: 1.05,
            textAlign: "center",
            maxWidth: 1000,
          }}
        >
          Soru Atölyesi
        </div>
        <div
          style={{
            fontSize: 36,
            fontWeight: 500,
            marginTop: 28,
            opacity: 0.95,
            textAlign: "center",
            maxWidth: 1000,
            lineHeight: 1.3,
          }}
        >
          MEB kazanım kodu bazlı
          <br />
          matematik çalışma kağıdı üretici
        </div>
        <div
          style={{
            position: "absolute",
            bottom: 50,
            display: "flex",
            gap: 28,
            fontSize: 22,
            opacity: 0.85,
          }}
        >
          <span>✓ PDF çıktı</span>
          <span>✓ Cevap anahtarı</span>
          <span>✓ Adım adım çözüm</span>
        </div>
      </div>
    ),
    { ...size },
  );
}
