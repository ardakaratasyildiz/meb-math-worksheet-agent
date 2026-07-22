/**
 * Tasarım token'ları — mobil tema tek kaynağı. Ekranlar hardcoded renk/ölçü
 * yerine buradan okur. Ders renkleri web ile ortak (@soruatolyesi/shared).
 *
 * NOT: Marka fontları (Fredoka/Nunito) ve maskot sonraki adımda; tam görsel
 * kimlik (koyu tema, oyunsu paleti) tasarım turunda olgunlaşacak.
 */
import { SUBJECT_COLORS } from "@soruatolyesi/shared";

export const colors = {
  brand: "#2563eb", // marka primary (web primary'siyle hizalı)
  brandDark: "#1d4ed8",
  onBrand: "#ffffff",
  bg: "#ffffff",
  surface: "#f8fafc",
  border: "#e5e7eb",
  text: "#0f172a",
  textMuted: "#64748b",
  danger: "#ef4444",
  success: "#059669",
  subject: SUBJECT_COLORS,
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
} as const;

export const radius = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  pill: 999,
} as const;

export const fontSize = {
  xs: 12,
  sm: 14,
  md: 16,
  lg: 20,
  xl: 24,
  xxl: 28,
} as const;

export const fontWeight = {
  regular: "400",
  medium: "600",
  bold: "700",
  heavy: "800",
} as const;

/**
 * Marka fontları — başlık Fredoka (oyunsu), gövde Nunito (okunur). Aileler
 * _layout'ta useFonts ile yüklenir. Özel fontta fontWeight yerine aile adı belirler.
 */
export const fonts = {
  heading: "Fredoka_700Bold",
  headingSemi: "Fredoka_600SemiBold",
  body: "Nunito_400Regular",
  bodyMedium: "Nunito_600SemiBold",
  bodyBold: "Nunito_700Bold",
  bodyHeavy: "Nunito_800ExtraBold",
} as const;
