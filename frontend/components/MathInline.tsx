"use client";

import * as React from "react";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";

// Kısa, satır-içi metinler için KaTeX renderer (cevap anahtarı, çözüm adımı).
// MarkdownQuestion blok seviyesindedir ve gömülü A)/B) şıklarını ayırır — cevap
// rozeti gibi tek satırlık alanlarda kullanılamaz. Burada yalnız matematik
// çevrilir, paragraf <span> olarak akar.
//
// Neden gerekti: "Doğru cevap" ve yapılandırılmış çözüm adımları düz metin
// basılıyordu → kullanıcı ham "$100 \times 2^6$" / "$\sqrt{18}$" görüyordu
// (saha bildirimi, 2026-08-20).

const INLINE_COMPONENTS: Components = {
  p: ({ children }) => <span>{children}</span>,
};

/** Metin matematik notasyonu taşıyor mu? ($…$ sınırlayıcı ya da çıplak LaTeX komutu) */
export function hasMathNotation(text: string | null | undefined): boolean {
  return !!text && (text.includes("$") || /\\[a-zA-Z]+/.test(text));
}

export function MathInline({ text }: { text: string }) {
  if (!hasMathNotation(text)) return <>{text}</>;
  return (
    <span className="[&_p]:inline">
      <ReactMarkdown
        remarkPlugins={[remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={INLINE_COMPONENTS}
      >
        {text}
      </ReactMarkdown>
    </span>
  );
}
