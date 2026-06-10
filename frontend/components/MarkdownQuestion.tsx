"use client";

import * as React from "react";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";

import { SafeSvg } from "@/components/SafeSvg";

// Soru metni renderer — çözme ekranında (QuizSolver) kullanılır. QuestionCard'ın
// kendi (export edilmemiş) renderer'ını TEKRAR ETMEZ; mevcut PDF/önizleme akışına
// dokunmamak için ayrı, sade bir kopya. Inline math (KaTeX) + GFM tablo + inline
// <svg> bloklarını destekler. KaTeX CSS layout'ta global yüklü.

const SVG_BLOCK_RE = /(<svg\b[^>]*>[\s\S]*?<\/svg>)/gi;

function splitBySvg(
  text: string,
): Array<{ kind: "text" | "svg"; content: string }> {
  const out: Array<{ kind: "text" | "svg"; content: string }> = [];
  let lastIdx = 0;
  const re = new RegExp(SVG_BLOCK_RE);
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    if (m.index > lastIdx) {
      out.push({ kind: "text", content: text.slice(lastIdx, m.index) });
    }
    out.push({ kind: "svg", content: m[0] });
    lastIdx = m.index + m[0].length;
  }
  if (lastIdx < text.length) {
    out.push({ kind: "text", content: text.slice(lastIdx) });
  }
  return out;
}

const MD_COMPONENTS: Components = {
  p: ({ children }) => <p className="my-1 leading-relaxed">{children}</p>,
  table: ({ children }) => (
    <div className="my-2 overflow-x-auto">
      <table className="border-collapse text-sm">{children}</table>
    </div>
  ),
  th: ({ children }) => (
    <th className="border px-2 py-1 text-left font-semibold">{children}</th>
  ),
  td: ({ children }) => <td className="border px-2 py-1">{children}</td>,
  code: ({ children }) => (
    <code className="rounded bg-muted px-1 py-0.5 font-mono text-xs">
      {children}
    </code>
  ),
};

export function MarkdownQuestion({ text }: { text: string }) {
  const segments = React.useMemo(() => splitBySvg(text), [text]);
  return (
    <div className="text-sm">
      {segments.map((seg, i) =>
        seg.kind === "svg" ? (
          <SafeSvg key={i} content={seg.content} />
        ) : (
          <ReactMarkdown
            key={i}
            remarkPlugins={[remarkGfm, remarkMath]}
            rehypePlugins={[rehypeKatex]}
            components={MD_COMPONENTS}
          >
            {seg.content}
          </ReactMarkdown>
        ),
      )}
    </div>
  );
}
