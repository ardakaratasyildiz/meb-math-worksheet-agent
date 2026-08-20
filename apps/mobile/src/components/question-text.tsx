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
  if (s.includes("$")) {
    return s.replace(/\${1,2}([^$]+)\${1,2}/g, (_m, e: string) => simplifyMath(e));
  }
  // Sınırlayıcısız kalan LaTeX komutları ("\sqrt{75}", "\frac{1}{2}") de sadeleşsin —
  // aksi halde çözüm adımlarında ham komut olarak görünüyordu.
  return /\\[a-zA-Z]+/.test(s) ? simplifyMath(s) : s;
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
    return <Text style={[styles.text, { color }]}>{latexLite(text)}</Text>;
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

// ── GFM tablo (eşleştirme / tablo_sorusu — {{table}} direktifi q.question'a gömülür) ──
const TABLE_ROW_RE = /^\s*\|.*\|\s*$/;

function parseCells(line: string): string[] {
  return line.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((c) => c.trim());
}
function isSeparatorRow(cells: string[]): boolean {
  return cells.length > 0 && cells.every((c) => /^:?-{2,}:?$/.test(c.replace(/\s/g, "")));
}

type TextPart = { kind: "text"; value: string } | { kind: "table"; rows: string[][] };

/** Düz metni GFM tablo bloklarından ayırır (başlık + `|---|` ayraç + satırlar). */
function splitByTable(text: string): TextPart[] {
  const lines = text.split("\n");
  const parts: TextPart[] = [];
  let buf: string[] = [];
  const flush = () => {
    if (buf.length) {
      parts.push({ kind: "text", value: buf.join("\n") });
      buf = [];
    }
  };
  let i = 0;
  while (i < lines.length) {
    const isTableStart =
      TABLE_ROW_RE.test(lines[i]) &&
      i + 1 < lines.length &&
      TABLE_ROW_RE.test(lines[i + 1]) &&
      isSeparatorRow(parseCells(lines[i + 1]));
    if (isTableStart) {
      flush();
      const rows: string[][] = [parseCells(lines[i])]; // başlık
      i += 2; // başlık + ayraç satırı atlanır
      while (i < lines.length && TABLE_ROW_RE.test(lines[i])) {
        rows.push(parseCells(lines[i]));
        i++;
      }
      parts.push({ kind: "table", rows });
    } else {
      buf.push(lines[i]);
      i++;
    }
  }
  flush();
  return parts;
}

function TableView({ rows, color }: { rows: string[][]; color: string }) {
  return (
    <View style={styles.table}>
      {rows.map((cells, r) => (
        <View key={r} style={styles.tableRow}>
          {cells.map((c, ci) => (
            <View key={ci} style={[styles.tableCell, r === 0 && styles.tableHeadCell]}>
              <Text style={[styles.cellText, { color }, r === 0 && styles.cellHeadText]}>
                {latexLite(c)}
              </Text>
            </View>
          ))}
        </View>
      ))}
    </View>
  );
}

/** Bir metin parçasını GFM tablolara böler; tablo → TableView, gerisi → MathText. */
function TextOrTable({ text, color }: { text: string; color: string }) {
  const parts = splitByTable(text);
  if (parts.length === 1 && parts[0].kind === "text") {
    return <MathText text={text} color={color} />;
  }
  return (
    <View style={styles.wrap}>
      {parts.map((p, i) =>
        p.kind === "table" ? (
          <TableView key={i} rows={p.rows} color={color} />
        ) : p.value.trim() ? (
          <MathText key={i} text={p.value} color={color} />
        ) : null,
      )}
    </View>
  );
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
        return <TextOrTable key={i} text={seg.value} color={color} />;
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
  table: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 8,
    overflow: "hidden",
    marginVertical: 4,
    alignSelf: "stretch",
  },
  tableRow: { flexDirection: "row" },
  tableCell: {
    flex: 1,
    borderWidth: 0.5,
    borderColor: colors.border,
    paddingHorizontal: 8,
    paddingVertical: 6,
  },
  tableHeadCell: { backgroundColor: colors.bgTint },
  cellText: { fontFamily: fonts.body, fontSize: fontSize.sm, lineHeight: 18 },
  cellHeadText: { fontFamily: fonts.bodyBold },
});

/**
 * Metin matematik notasyonu taşıyor mu? (`$…$` sınırlayıcı ya da çıplak LaTeX
 * komutu). Cevap/çözüm gibi kısa alanlarda "düz Text mi, QuestionText mi"
 * kararını verir — ham `$\sqrt{18}$` kullanıcıya gösterilmesin diye.
 */
export function hasMathNotation(text: string | null | undefined): boolean {
  return !!text && (text.includes("$") || /\\[a-zA-Z]+/.test(text));
}
