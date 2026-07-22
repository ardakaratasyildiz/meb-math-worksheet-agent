import { StyleSheet, Text, View } from "react-native";
import { SvgXml } from "react-native-svg";

import { colors, fonts, fontSize } from "@/theme/tokens";

/**
 * Soru gövdesini native render eder:
 *  - Metin içindeki <svg>…</svg> blokları (grafik/örüntü/tablo direktiflerinden
 *    üretilen) → gerçek SVG (react-native-svg SvgXml).
 *  - Satır-içi LaTeX ($…$) → okunur Unicode'a sadeleştirilir (tam matematik
 *    render'ı backend→SVG ile sonra; şimdilik kesir/üs/sembol yaklaşık).
 */
const SVG_RE = /<svg[\s\S]*?<\/svg>/gi;
const VIEWBOX_RE = /viewBox=["']\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)["']/i;

const SYMBOLS: Record<string, string> = {
  "\\times": "×", "\\div": "÷", "\\cdot": "·", "\\pm": "±", "\\mp": "∓",
  "\\leq": "≤", "\\geq": "≥", "\\neq": "≠", "\\le": "≤", "\\ge": "≥",
  "\\approx": "≈", "\\rightarrow": "→", "\\to": "→", "\\leftarrow": "←",
  "\\circ": "°", "\\degree": "°", "\\infty": "∞", "\\ldots": "…", "\\dots": "…",
  "\\pi": "π", "\\alpha": "α", "\\beta": "β", "\\gamma": "γ", "\\theta": "θ",
  "\\Delta": "Δ", "\\mu": "µ",
};
const SUP: Record<string, string> = {
  "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
  "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
};

function simplifyMath(expr: string): string {
  let x = expr;
  x = x.replace(/\\[dt]?frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}/g, "$1/$2");
  x = x.replace(/\\sqrt\s*\{([^{}]*)\}/g, "√($1)");
  x = x.replace(/\^\{?([0-9]+)\}?/g, (_m, p: string) =>
    p.split("").map((c) => SUP[c] ?? `^${c}`).join(""),
  );
  for (const [k, v] of Object.entries(SYMBOLS)) x = x.split(k).join(v);
  x = x.replace(/\\left|\\right/g, "").replace(/[{}]/g, "");
  return x.trim();
}

function latexLite(s: string): string {
  if (!s.includes("$")) return s;
  return s.replace(/\${1,2}([^$]+)\${1,2}/g, (_m, e: string) => simplifyMath(e));
}

type Seg = { kind: "text"; value: string } | { kind: "svg"; value: string };

function splitBySvg(text: string): Seg[] {
  const out: Seg[] = [];
  let last = 0;
  for (const m of text.matchAll(SVG_RE)) {
    const idx = m.index ?? 0;
    if (idx > last) out.push({ kind: "text", value: text.slice(last, idx) });
    out.push({ kind: "svg", value: m[0] });
    last = idx + m[0].length;
  }
  if (last < text.length) out.push({ kind: "text", value: text.slice(last) });
  return out;
}

export function QuestionText({
  text,
  width = 300,
  color = colors.text,
}: {
  text: string;
  width?: number;
  color?: string;
}) {
  const segments = splitBySvg(text);
  return (
    <View style={styles.wrap}>
      {segments.map((seg, i) => {
        if (seg.kind === "svg") {
          const vb = seg.value.match(VIEWBOX_RE);
          const w = Math.min(width, 320);
          const h = vb ? (w * parseFloat(vb[4])) / parseFloat(vb[3]) : 160;
          return (
            <View key={i} style={styles.svgWrap}>
              <SvgXml xml={seg.value} width={w} height={h} />
            </View>
          );
        }
        const clean = latexLite(seg.value).trim();
        if (!clean) return null;
        return (
          <Text key={i} style={[styles.text, { color }]}>
            {clean}
          </Text>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: 8 },
  text: { fontFamily: fonts.body, fontSize: fontSize.md, lineHeight: 22 },
  svgWrap: { alignItems: "flex-start", marginVertical: 4 },
});
