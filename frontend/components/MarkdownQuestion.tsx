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

// Çoktan seçmeli şıklar "... soru? A) x B) y C) z D) w" formatında gömülü gelir.
// Markdown boşluk olarak işlediği için şıklar soruyla aynı satıra akıyor.
// Bu fonksiyon stemden şıkları ayırır; her şık kendi satırında render edilir.
function splitInlineOptions(
  text: string,
): { stem: string; options: string[] } | null {
  const re = /(^|[^A-Za-z0-9])([A-D])[)\.]/g;
  const idxs: number[] = [];
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    idxs.push(m.index + m[1].length);
    if (m.index === re.lastIndex) re.lastIndex++;
  }
  if (idxs.length < 2) return null;
  const stem = text.slice(0, idxs[0]).trim();
  if (!stem) return null;
  const options: string[] = [];
  for (let i = 0; i < idxs.length; i++) {
    const to = i + 1 < idxs.length ? idxs[i + 1] : text.length;
    options.push(text.slice(idxs[i], to).trim());
  }
  return { stem, options };
}

export function MarkdownQuestion({ text }: { text: string }) {
  const segments = React.useMemo(() => splitBySvg(text), [text]);
  const parsed = React.useMemo(() => splitInlineOptions(text), [text]);

  // Gömülü A) B) C) D) şıkları varsa ayrı satırlara böl.
  if (parsed) {
    return (
      <div className="space-y-1">
        <div className="text-sm">
          {splitBySvg(parsed.stem).map((seg, i) =>
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
        <div className="space-y-0.5 pl-2 text-sm">
          {parsed.options.map((opt, i) => (
            <div key={i}>
              {splitBySvg(opt).map((seg, j) =>
                seg.kind === "svg" ? (
                  <SafeSvg key={j} content={seg.content} />
                ) : (
                  <ReactMarkdown
                    key={j}
                    remarkPlugins={[remarkGfm, remarkMath]}
                    rehypePlugins={[rehypeKatex]}
                    components={MD_COMPONENTS}
                  >
                    {seg.content}
                  </ReactMarkdown>
                ),
              )}
            </div>
          ))}
        </div>
      </div>
    );
  }

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
