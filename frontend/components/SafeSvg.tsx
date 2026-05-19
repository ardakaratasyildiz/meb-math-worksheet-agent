"use client";

import * as React from "react";
import DOMPurify from "isomorphic-dompurify";

interface SafeSvgProps {
  /** Ham SVG string'i — LLM çıktısından geliyor, XSS riski içerebilir. */
  content: string;
  className?: string;
}

/**
 * LLM tarafından üretilen ham SVG string'ini sanitize edip render eder.
 *
 * Güvenlik:
 *   - DOMPurify SVG profile + explicit ADD_ATTR/ADD_TAGS: <script>, on*
 *     handler'ları, href javascript: gibi vektörleri keser.
 *   - xmlns="http://www.w3.org/2000/svg" eksikse otomatik ekleniyor (LLM
 *     bazen unutuyor; xmlns yoksa browser SVG'yi HTML element gibi
 *     algılıyor → render edilemiyor).
 *
 * Boyutlandırma:
 *   - viewBox varsa intrinsic. width/height yoksa wrapper'a explicit
 *     boyut veriyoruz ki yer kaplasın (aksi halde 0×0 görünebilir).
 */
export function SafeSvg({ content, className }: SafeSvgProps) {
  const sanitized = React.useMemo(() => {
    if (typeof content !== "string" || !content.includes("<svg")) return null;

    // xmlns yoksa ekle — browser SVG'yi tanıması için kritik.
    let svg = content;
    if (!/<svg[^>]*xmlns/i.test(svg)) {
      svg = svg.replace(/<svg\b/i, '<svg xmlns="http://www.w3.org/2000/svg"');
    }

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

    if (!clean || !clean.includes("<svg")) return null;
    return clean;
  }, [content]);

  if (!sanitized) {
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
        // belirtmediği durumlarda 0×0 düşmesini engelliyor (intrinsic 300×150
        // browser default'una bırakıyor).
        className="w-full max-w-[420px] [&>svg]:block [&>svg]:h-auto [&>svg]:max-h-[320px] [&>svg]:w-full"
        // eslint-disable-next-line react/no-danger
        dangerouslySetInnerHTML={{ __html: sanitized }}
      />
    </div>
  );
}
