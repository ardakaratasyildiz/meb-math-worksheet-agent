/**
 * Tasarım token'ları — mobil tema tek kaynağı. Ekranlar hardcoded renk/ölçü
 * yerine buradan okur. Kimlik = "Neşeli Kağıt": sıcak krem zemin, yumuşak gölgeli
 * yüzen kartlar, oyunsu yuvarlak formlar, gamification renk sistemi.
 *
 * Kaynak spec'ler: UI Design Bible + COMPONENT library + PSYCHOLOGY bible.
 *  - Zemin ASLA saf beyaz → sıcak krem.
 *  - Renk anlamları: mavi=öğrenme/güven · yeşil=başarı · sarı=ödül · turuncu=enerji/maskot
 *    · mor=premium/sihir · kırmızı=YALNIZ hata.
 *  - Tek gölge sistemi: çok yumuşak, geniş blur, düşük opaklık.
 *
 * KOYU TEMA: bu turda ışık-teması olgunlaştırıldı; token'lar anlamsal adlandırıldığı
 * için koyu tema sonradan bir `useThemeColors()` hook'uyla temiz eklenebilir (renk
 * değerleri tek yerden gelir, ekran kodu değişmez).
 */
import { SUBJECT_COLORS } from "@soruatolyesi/shared";

export const colors = {
  // ── Zemin / yüzey (sıcak krem — asla saf beyaz) ──────────────────────────
  bg: "#FBF4E9", // ana krem zemin
  bgTint: "#F5ECDD", // hafif daha koyu krem (bölüm ayrımı)
  surface: "#FFFFFF", // yüzen kart (krem üstünde beyaz)
  surfaceAlt: "#FFFDF8", // çok hafif sıcak beyaz

  // ── Metin ────────────────────────────────────────────────────────────────
  text: "#242A38", // koyu lacivert-gri (saf siyah değil)
  textMuted: "#8A8797", // yumuşak gri
  textFaint: "#B7B3C0",

  // ── Marka / gamification paleti ───────────────────────────────────────────
  brand: "#2F6BF6", // mavi — öğrenme/güven (Çalışma Kağıdı)
  brandDark: "#1E4FD0",
  onBrand: "#FFFFFF",

  success: "#1FA463", // yeşil — başarı/büyüme (Devam Et, Alıştırma)
  successDark: "#158049",

  reward: "#F5B93B", // sarı — ödül/XP/yıldız/coin
  rewardDark: "#E29B14",

  energy: "#F97A3D", // turuncu — maskot/enerji/ateş
  energyDark: "#E85F1E",

  magic: "#7C4DFF", // mor — premium/sihir/AI
  magicDark: "#6234E0",

  pink: "#E4589B", // pembe — gelişim/keşif vurgusu
  pinkDark: "#C93C81",

  danger: "#EF5350", // kırmızı — YALNIZ hata

  // Rol vurguları — öğretmen mavi (brand), veli sakin teal (yetişkin/sade ton)
  parent: "#2C8C86",
  parentTint: "#E4F1EF",

  // ── Yumuşak tint zeminler (info/status kartları) ──────────────────────────
  tintBlue: "#E7EEFF",
  tintGreen: "#E1F5EB",
  tintYellow: "#FCEFC9",
  tintOrange: "#FDE7DA",
  tintPurple: "#ECE4FF",
  tintPink: "#FBE3F0",

  // ── Metin-üstü tint renkleri (tint zemin üstünde okunur koyu ton) ──────────
  onTintYellow: "#B4791A",
  onTintPurple: "#6234E0",
  onTintPink: "#C93C81",

  // ── Yapısal ────────────────────────────────────────────────────────────────
  border: "#EEE7DB", // krem üstü ince ayraç
  track: "#ECE6DB", // progress bar boş kanalı

  subject: SUBJECT_COLORS,
} as const;

// COMPONENT library ölçeği: 8 / 16 / 24 / 32 / 48 / 64 (ara değerler geriye uyum için).
export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
  xxxl: 48,
  huge: 64,
} as const;

export const radius = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 22, // buton
  card: 24, // aksiyon/status kart
  xxl: 28,
  hero: 32, // hero kart
  pill: 999,
} as const;

export const fontSize = {
  xs: 12,
  sm: 14,
  md: 16,
  lg: 20,
  xl: 24,
  xxl: 28,
  display: 34, // büyük selamlama
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

/**
 * Tek gölge sistemi (COMPONENT library): çok yumuşak, geniş blur, düşük opaklık.
 * iOS shadow* + Android elevation birlikte. Yüzen kart hissini bunlar verir.
 */
export const shadow = {
  // Yüzen kart — hafif kalkık.
  card: {
    shadowColor: "#3A2E1E",
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.08,
    shadowRadius: 16,
    elevation: 3,
  },
  // Vurgulu / renkli hero kart — biraz daha derin.
  floating: {
    shadowColor: "#2A2110",
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.14,
    shadowRadius: 22,
    elevation: 6,
  },
  // Maskot FAB — belirgin kalkık.
  fab: {
    shadowColor: "#1E3A8A",
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.28,
    shadowRadius: 14,
    elevation: 10,
  },
} as const;
