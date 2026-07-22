import { useEffect, useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import { SvgXml } from "react-native-svg";

import { renderMath, type MathSegment } from "@/lib/api";
import { colors, fonts, fontSize } from "@/theme/tokens";

/**
 * Soru gövdesini native render eder:
 *  - Metin içindeki <svg>…</svg> blokları (grafik/örüntü/tablo direktiflerinden
 *    üretilen) → gerçek SVG (react-native-svg SvgXml).
 *  - Matematik ($…$ / $$…$$): önce satır-içi LaTeX Unicode'a sadeleştirilir (anında),
 *    ardından backend `/api/render/math`'ten KESKİN SVG segmentleri çekilir ve
 *    yerine konur (progressive enhancement; ağ hatası → Unicode fallback'te kalır).
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

// Aynı ifadeyi tekrar tekrar çekmemek için basit modül-içi önbellek (font:text).
const MATH_FONT = 16;
const mathCache = new Map<string, MathSegment[]>();

/** Backend math SVG'sini font'a göre satır-içi boyutlandırır (viewBox oranı). */
function MathSvg({ svg, display }: { svg: string; display: boolean }) {
  const vb = svg.match(VIEWBOX_RE);
  const ratio = vb ? parseFloat(vb[3]) / parseFloat(vb[4]) : 3;
  const h = Math.round(fontSize.md * (display ? 2 : 1.3));
  const w = Math.round(h * (isFinite(ratio) && ratio > 0 ? ratio : 3));
  return <SvgXml xml={svg} width={w} height={h} />;
}

/**
 * Bir metin parçasını render eder. Matematik ($) varsa backend'den keskin SVG
 * segmentleri çeker; gelene dek (veya hata halinde) Unicode fallback gösterir.
 */
function MathText({ text, color }: { text: string; color: string }) {
  const hasMath = text.includes("$");
  const key = `${MATH_FONT}:${text}`;
  const [segs, setSegs] = useState<MathSegment[] | null>(
    hasMath ? mathCache.get(key) ?? null : null,
  );

  useEffect(() => {
    if (!hasMath || mathCache.has(key)) return;
    let alive = true;
    renderMath(text, MATH_FONT)
      .then((s) => {
        mathCache.set(key, s);
        if (alive) setSegs(s);
      })
      .catch(() => {}); // ağ hatası → Unicode fallback'te kal
    return () => {
      alive = false;
    };
  }, [text, hasMath, key]);

  if (!hasMath) {
    return <Text style={[styles.text, { color }]}>{text}</Text>;
  }
  if (segs) {
    return (
      <View style={styles.mathRow}>
        {segs.map((s, i) =>
          s.kind === "math" && s.svg ? (
            <View key={i} style={s.display ? styles.mathBlock : styles.mathItem}>
              <MathSvg svg={s.svg} display={s.display} />
            </View>
          ) : (
            <Text key={i} style={[styles.text, { color }]}>
              {s.text}
            </Text>
          ),
        )}
      </View>
    );
  }
  // Yükleniyor: anında okunur Unicode fallback
  return <Text style={[styles.text, { color }]}>{latexLite(text)}</Text>;
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
        if (!seg.value.trim()) return null;
        return <MathText key={i} text={seg.value} color={color} />;
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: 8 },
  text: { fontFamily: fonts.body, fontSize: fontSize.md, lineHeight: 22 },
  svgWrap: { alignItems: "flex-start", marginVertical: 4 },
  mathRow: { flexDirection: "row", flexWrap: "wrap", alignItems: "center" },
  mathItem: { marginHorizontal: 1 },
  mathBlock: { width: "100%", alignItems: "flex-start", marginVertical: 4 },
});
