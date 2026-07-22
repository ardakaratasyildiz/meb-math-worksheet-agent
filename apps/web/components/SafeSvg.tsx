"use client";

import * as React from "react";

interface SafeSvgProps {
  /** Ham SVG string'i — LLM çıktısından geliyor, XSS riski içerebilir. */
  content: string;
  className?: string;
}

/**
 * LLM tarafından üretilen ham SVG string'ini sanitize edip render eder.
 *
 * NEDEN CLIENT-ONLY DYNAMIC IMPORT:
 *   `isomorphic-dompurify` server'da jsdom çeker; jsdom → html-encoding-sniffer →
 *   @exodus/bytes (ESM-only) zinciri Vercel lambda runtime'ında `require()` ile
 *   yüklenince ERR_REQUIRE_ESM ile patlıyordu. Sayfa statikken (prerender) sorun
 *   görünmüyordu; /generate `searchParams` ile dynamic olunca runtime SSR'da
 *   çöktü (/practice gibi diğer dynamic + SVG sayfaları da etkiler).
 *
 *   SVG içeriği zaten yalnızca client'ta (üretimden sonra) var → sanitizasyonu
 *   client'a taşımak doğru mimari. DOMPurify useEffect içinde DYNAMIC import edilir
 *   → server'ın statik require graph'ına HİÇ girmez. Server/ilk render nötr bir
 *   "hazırlanıyor" yer tutucu gösterir, hidrasyondan sonra SVG dolar.
 *
 * Güvenlik: sanitize tarayıcıda (gerçek DOM) çalışır — server-side jsdom yerine.
 */
export function SafeSvg({ content, className }: SafeSvgProps) {
  const [state, setState] = React.useState<
    { status: "pending" } | { status: "ok"; svg: string } | { status: "fail" }
  >({ status: "pending" });

  React.useEffect(() => {
    let cancelled = false;
    if (typeof content !== "string" || !content.includes("<svg")) {
      setState({ status: "fail" });
      return;
    }

    // xmlns yoksa ekle — browser SVG'yi tanıması için kritik.
    let svg = content;
    if (!/<svg[^>]*xmlns/i.test(svg)) {
      svg = svg.replace(/<svg\b/i, '<svg xmlns="http://www.w3.org/2000/svg"');
    }

    void import("isomorphic-dompurify").then(({ default: DOMPurify }) => {
      if (cancelled) return;
      // Seçenekler inline — DOMPurify.sanitize overload'ı (dönüş tipi string)
      // ile uyum için (çıkarılmış `as const` obje overload'ı kırıyor).
      const clean = DOMPurify.sanitize(svg, {
        USE_PROFILES: { svg: true, svgFilters: true },
        // xmlns, viewBox ve diğer kritik attr'ları açıkça whitelist'le —
        // bazı DOMPurify versiyonlarında default'ta drop ediliyor.
        ADD_ATTR: [
          "xmlns",
          "xmlns:xlink",
          "viewBox",
          "preserveAspectRatio",
          "fill",
          "stroke",
          "stroke-width",
          "stroke-dasharray",
          "stroke-linecap",
          "stroke-linejoin",
          "font-size",
          "font-family",
          "font-weight",
          "text-anchor",
          "dominant-baseline",
          "transform",
          "opacity",
        ],
        FORBID_ATTR: ["onload", "onclick", "onerror", "onmouseover", "href"],
        FORBID_TAGS: ["script", "foreignObject", "iframe"],
      });
      setState(
        clean && clean.includes("<svg")
          ? { status: "ok", svg: clean }
          : { status: "fail" },
      );
    });

    return () => {
      cancelled = true;
    };
  }, [content]);

  // İlk render / SSR: nötr yer tutucu (uyarı değil) — client'ta dynamic import
  // tamamlanınca dolar. min-height layout shift'i azaltır.
  if (state.status === "pending") {
    return (
      <div
        className={`my-3 flex min-h-[120px] items-center justify-center rounded-md border bg-white p-3 dark:bg-zinc-100 ${className ?? ""}`}
      >
        <span className="text-xs text-muted-foreground">Görsel hazırlanıyor…</span>
      </div>
    );
  }

  if (state.status === "fail") {
    return (
      <div className="my-3 rounded-md border border-amber-300 bg-amber-50 p-3 text-xs text-amber-700 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-300">
        ⚠️ Görsel yüklenemedi (SVG sanitize başarısız).
      </div>
    );
  }

  return (
    <div
      className={`my-3 flex justify-center overflow-x-auto rounded-md border bg-white p-3 dark:bg-zinc-100 ${className ?? ""}`}
    >
      <div
        // Wrapper'a explicit max-width + min-height; SVG width/height
        // belirtmediği durumlarda 0×0 düşmesini engelliyor.
        className="w-full max-w-[420px] [&>svg]:block [&>svg]:h-auto [&>svg]:max-h-[320px] [&>svg]:w-full"
        // eslint-disable-next-line react/no-danger
        dangerouslySetInnerHTML={{ __html: state.svg }}
      />
    </div>
  );
}
