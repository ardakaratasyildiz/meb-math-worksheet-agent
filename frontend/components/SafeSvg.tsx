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
 *   - DOMPurify SVG profile: <script>, on* handler'ları, href javascript:
 *     gibi vektörleri keser. SVG primitive'leri (path, line, rect, circle,
 *     text, polygon, polyline, g, defs, marker, ...) korunur.
 *   - Sanitize sonrası boş çıkarsa hata mesajı gösterilir (LLM bozuk SVG
 *     üretmiş olabilir — fallback).
 *
 * Boyutlandırma:
 *   - viewBox SVG'de zaten tanımlıysa intrinsic; max-width ile yatay
 *     taşmayı önler. Mobile responsive — geniş ekrandan daralırsa scale eder.
 */
export function SafeSvg({ content, className }: SafeSvgProps) {
  const sanitized = React.useMemo(() => {
    if (typeof content !== "string" || !content.includes("<svg")) return null;
    const clean = DOMPurify.sanitize(content, {
      USE_PROFILES: { svg: true, svgFilters: true },
      // Inline event handler ve dış kaynak yükleme yasak
      FORBID_ATTR: ["onload", "onclick", "onerror", "onmouseover"],
      FORBID_TAGS: ["script", "foreignObject"],
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
      // Max-width ile parent'a fit, height auto SVG'nin oranını korur.
      className={`my-3 flex justify-center overflow-x-auto rounded-md border bg-white p-3 dark:bg-zinc-100 ${className ?? ""}`}
    >
      <div
        // SVG ham HTML olarak ekleniyor, sanitize edilmiş olduğu garantili.
        // Tailwind text-zinc-900 dark mode'da kontrastlı kalsın diye light bg.
        className="[&>svg]:max-w-full [&>svg]:h-auto"
        // eslint-disable-next-line react/no-danger
        dangerouslySetInnerHTML={{ __html: sanitized }}
      />
    </div>
  );
}
