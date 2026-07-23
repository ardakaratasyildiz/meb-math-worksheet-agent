/**
 * Özel SVG ikon seti — Soru Atölyesi görsel kimliği.
 *
 * COMPONENT library kuralı: "Never outline only. Use colorful icons. Rounded.
 * Cute. 3D feeling. Icon size 32/48/64." → burada ikonlar dolgulu, renkli,
 * yuvarlak köşeli; hafif 3D hissi için gradyan/highlight kullanılır.
 *
 * Emoji DEĞİL, ince-outline DEĞİL. İleride Pixar-kalite raster asset gelirse
 * çağrı yerleri (icon boyutu/hizası) korunarak tek tek değiştirilebilir.
 *
 * Her ikon `size` prop'u alır (kare). Tab bar ikonları ayrıca `active` rengiyle
 * çalışır (aktif=renkli dolgu, pasif=gri).
 */
import Svg, {
  Circle,
  Defs,
  G,
  Line,
  LinearGradient,
  Path,
  Polygon,
  Rect,
  Stop,
} from "react-native-svg";

import { colors } from "@/theme/tokens";

type IconProps = { size?: number };

// ── Ateş / seri (turuncu→kırmızı alev) ──────────────────────────────────────
export function IconFire({ size = 32 }: IconProps) {
  return (
    <Svg width={size} height={size} viewBox="0 0 48 48">
      <Defs>
        <LinearGradient id="fireG" x1="0" y1="0" x2="0" y2="1">
          <Stop offset="0" stopColor="#FBBF24" />
          <Stop offset="0.55" stopColor="#F97316" />
          <Stop offset="1" stopColor="#EF4444" />
        </LinearGradient>
      </Defs>
      <Path
        d="M25 4c1.5 6.5 8.5 9 8.5 17.5A9.5 9.5 0 0 1 14.5 22c0-4 1.6-6.5 4-9 .2 2.4 1.3 3.8 2.6 4.7C19.8 12.4 20.5 8 25 4z"
        fill="url(#fireG)"
      />
      <Path
        d="M24 20c1 2.6 3.8 3.6 3.8 6.8a3.9 3.9 0 0 1-7.8 0c0-1.8 1-3 2.4-4 0 1 .5 1.6 1.1 2C22.9 23 22.4 21.6 24 20z"
        fill="#FFE9A8"
      />
    </Svg>
  );
}

// ── Yıldız / seviye (altın yıldız) ──────────────────────────────────────────
export function IconStar({ size = 32 }: IconProps) {
  return (
    <Svg width={size} height={size} viewBox="0 0 48 48">
      <Defs>
        <LinearGradient id="starG" x1="0" y1="0" x2="0" y2="1">
          <Stop offset="0" stopColor="#FCD34D" />
          <Stop offset="1" stopColor="#F59E0B" />
        </LinearGradient>
      </Defs>
      <Path
        d="M24 5.5l5.3 10.8 11.9 1.7-8.6 8.4 2 11.9L24 32.6l-10.6 5.6 2-11.9L6.8 18l11.9-1.7z"
        fill="url(#starG)"
        stroke="#E29B14"
        strokeWidth={1.2}
        strokeLinejoin="round"
      />
    </Svg>
  );
}

// ── XP kıvılcımı (yeşil 4-uçlu parıltı) ──────────────────────────────────────
export function IconSpark({ size = 32 }: IconProps) {
  return (
    <Svg width={size} height={size} viewBox="0 0 48 48">
      <Defs>
        <LinearGradient id="sparkG" x1="0" y1="0" x2="1" y2="1">
          <Stop offset="0" stopColor="#34D399" />
          <Stop offset="1" stopColor="#059669" />
        </LinearGradient>
      </Defs>
      <Path
        d="M24 4c1.6 9 5 12.4 14 14-9 1.6-12.4 5-14 14-1.6-9-5-12.4-14-14 9-1.6 12.4-5 14-14z"
        fill="url(#sparkG)"
      />
    </Svg>
  );
}

// ── Hedef / günlük hedef (kırmızı-beyaz nişan) ───────────────────────────────
export function IconTarget({ size = 32 }: IconProps) {
  return (
    <Svg width={size} height={size} viewBox="0 0 48 48">
      <Circle cx="24" cy="24" r="19" fill="#EF4444" />
      <Circle cx="24" cy="24" r="13" fill="#FFF7ED" />
      <Circle cx="24" cy="24" r="7.5" fill="#EF4444" />
      <Circle cx="24" cy="24" r="2.6" fill="#FFF7ED" />
    </Svg>
  );
}

// ── Hediye kutusu (yeşil kutu + turuncu kurdele) ─────────────────────────────
export function IconGift({ size = 32 }: IconProps) {
  return (
    <Svg width={size} height={size} viewBox="0 0 48 48">
      <Defs>
        <LinearGradient id="giftG" x1="0" y1="0" x2="0" y2="1">
          <Stop offset="0" stopColor="#34D399" />
          <Stop offset="1" stopColor="#10B981" />
        </LinearGradient>
      </Defs>
      <Rect x="9" y="20" width="30" height="20" rx="3.5" fill="url(#giftG)" />
      <Rect x="7" y="15" width="34" height="7.5" rx="3" fill="#059669" />
      <Rect x="21" y="15" width="6" height="25" fill="#FB923C" />
      <Path
        d="M24 15c-3-6-11-4-7 0zM24 15c3-6 11-4 7 0z"
        fill="#FB923C"
      />
      <Circle cx="24" cy="14" r="2.4" fill="#F97316" />
    </Svg>
  );
}

// ── Kitap / defter (Devam Et — kesir ½ kitabı) ───────────────────────────────
export function IconBook({ size = 32 }: IconProps) {
  return (
    <Svg width={size} height={size} viewBox="0 0 48 48">
      <Rect x="10" y="8" width="26" height="32" rx="4" fill="#FFFFFF" />
      <Rect x="10" y="8" width="7" height="32" rx="3.5" fill="#F97316" />
      <Line x1="24" y1="21" x2="31" y2="21" stroke="#2F6BF6" strokeWidth="2.4" strokeLinecap="round" />
      <Line x1="24" y1="27" x2="31" y2="27" stroke="#EF4444" strokeWidth="2.4" strokeLinecap="round" />
    </Svg>
  );
}

// ── Çalışma kağıdı / doküman (renkli dolgu, katlı köşe) ───────────────────────
export function IconWorksheet({ size = 32, tone = "#FFFFFF" }: IconProps & { tone?: string }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 48 48">
      <Path d="M13 6h16l8 8v25a3 3 0 0 1-3 3H13a3 3 0 0 1-3-3V9a3 3 0 0 1 3-3z" fill={tone} />
      <Path d="M29 6l8 8h-6a2 2 0 0 1-2-2z" fill="#C9D6F5" />
      <Line x1="16" y1="20" x2="31" y2="20" stroke="#2F6BF6" strokeWidth="2.4" strokeLinecap="round" />
      <Line x1="16" y1="26" x2="31" y2="26" stroke="#9DB6F0" strokeWidth="2.4" strokeLinecap="round" />
      <Line x1="16" y1="32" x2="26" y2="32" stroke="#9DB6F0" strokeWidth="2.4" strokeLinecap="round" />
    </Svg>
  );
}

// ── Kalem (sarı kalem, çapraz) ────────────────────────────────────────────────
export function IconPencil({ size = 32 }: IconProps) {
  return (
    <Svg width={size} height={size} viewBox="0 0 48 48">
      <G rotation="0" origin="24, 24">
        <Path d="M32 6l10 10-20 20-10 2 2-10z" fill="#F5B93B" />
        <Path d="M32 6l10 10-3.5 3.5-10-10z" fill="#F97316" />
        <Path d="M14 38l-2 2 4-.8 6-6-2-2z" fill="#F4E3C1" />
        <Path d="M12 40l1-4 3 3z" fill="#3B3226" />
      </G>
    </Svg>
  );
}

// ── Takvim (Günün Sorusu — kırmızı üst) ──────────────────────────────────────
export function IconCalendar({ size = 32 }: IconProps) {
  return (
    <Svg width={size} height={size} viewBox="0 0 48 48">
      <Rect x="7" y="10" width="34" height="31" rx="5" fill="#FFFFFF" stroke="#F2D9A0" strokeWidth="1.5" />
      <Path d="M7 15a5 5 0 0 1 5-5h24a5 5 0 0 1 5 5v4H7z" fill="#EF4444" />
      <Rect x="14" y="6" width="4" height="9" rx="2" fill="#B4791A" />
      <Rect x="30" y="6" width="4" height="9" rx="2" fill="#B4791A" />
      <Circle cx="16" cy="27" r="2.4" fill="#F5B93B" />
      <Circle cx="24" cy="27" r="2.4" fill="#F5B93B" />
      <Circle cx="32" cy="27" r="2.4" fill="#E4E0D5" />
      <Circle cx="16" cy="34" r="2.4" fill="#E4E0D5" />
      <Circle cx="24" cy="34" r="2.4" fill="#F5B93B" />
    </Svg>
  );
}

// ── Bar grafik (Gelişimini Gör — renkli çubuklar) ─────────────────────────────
export function IconChart({ size = 32 }: IconProps) {
  return (
    <Svg width={size} height={size} viewBox="0 0 48 48">
      <Rect x="8" y="24" width="8" height="16" rx="3" fill="#2F6BF6" />
      <Rect x="20" y="14" width="8" height="26" rx="3" fill="#1FA463" />
      <Rect x="32" y="19" width="8" height="21" rx="3" fill="#E4589B" />
    </Svg>
  );
}

// ── Çan / bildirim ────────────────────────────────────────────────────────────
export function IconBell({ size = 26, dot = false }: IconProps & { dot?: boolean }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 48 48">
      <Path
        d="M24 5a3 3 0 0 1 3 3v1.2c5.2 1.3 9 6 9 11.8v6l2.6 4.2A2 2 0 0 1 36 35H12a2 2 0 0 1-1.6-3.8L13 27v-6c0-5.8 3.8-10.5 9-11.8V8a3 3 0 0 1 2-3z"
        fill="#F5B93B"
        stroke="#E29B14"
        strokeWidth="1.2"
        strokeLinejoin="round"
      />
      <Path d="M20 37a4 4 0 0 0 8 0z" fill="#E29B14" />
      {dot ? <Circle cx="35" cy="12" r="6" fill="#EF5350" stroke="#FFFFFF" strokeWidth="2" /> : null}
    </Svg>
  );
}

// ── Oynat üçgeni (Devam Et dairesi içinde beyaz) ─────────────────────────────
export function IconPlay({ size = 24, color = "#1FA463" }: IconProps & { color?: string }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24">
      <Path d="M8 5.5l11 6.5-11 6.5z" fill={color} />
    </Svg>
  );
}

// ── Sağ ok (chevron) ─────────────────────────────────────────────────────────
export function IconChevron({ size = 20, color = colors.textMuted }: IconProps & { color?: string }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24">
      <Path
        d="M9 5l7 7-7 7"
        fill="none"
        stroke={color}
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </Svg>
  );
}

// ── Tab bar ikonları (aktif=renkli, pasif=gri) ────────────────────────────────
export function IconHome({ size = 26, color }: IconProps & { color?: string }) {
  const c = color ?? colors.textMuted;
  return (
    <Svg width={size} height={size} viewBox="0 0 48 48">
      <Path
        d="M24 6l17 14v20a3 3 0 0 1-3 3h-8V30h-12v13h-8a3 3 0 0 1-3-3V20z"
        fill={c}
      />
    </Svg>
  );
}

export function IconTrend({ size = 26, color }: IconProps & { color?: string }) {
  const c = color ?? colors.textMuted;
  return (
    <Svg width={size} height={size} viewBox="0 0 48 48">
      <Path
        d="M8 32l10-10 7 7 12-13"
        fill="none"
        stroke={c}
        strokeWidth="4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <Path d="M30 16h9v9" fill="none" stroke={c} strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
    </Svg>
  );
}

/** Tab bar için sade doküman ikonu (tek renk, aktif/pasif). */
export function IconDocSimple({ size = 26, color }: IconProps & { color?: string }) {
  const c = color ?? colors.textMuted;
  return (
    <Svg width={size} height={size} viewBox="0 0 48 48">
      <Path
        d="M14 5h16l8 8v27a2 2 0 0 1-2 2H14a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2z"
        fill="none"
        stroke={c}
        strokeWidth="3.4"
        strokeLinejoin="round"
      />
      <Path d="M29 5v9h9" fill="none" stroke={c} strokeWidth="3.4" strokeLinejoin="round" />
    </Svg>
  );
}

/** Tab bar için sade kalem ikonu (tek renk, aktif/pasif). */
export function IconPencilSimple({ size = 26, color }: IconProps & { color?: string }) {
  const c = color ?? colors.textMuted;
  return (
    <Svg width={size} height={size} viewBox="0 0 48 48">
      <Path
        d="M31 7l10 10-22 22-11 1 1-11z"
        fill="none"
        stroke={c}
        strokeWidth="3.4"
        strokeLinejoin="round"
      />
      <Line x1="27" y1="11" x2="37" y2="21" stroke={c} strokeWidth="3.4" strokeLinecap="round" />
    </Svg>
  );
}

/** Tab bar için sade kullanıcı ikonu (tek renk, aktif/pasif). */
export function IconUser({ size = 26, color }: IconProps & { color?: string }) {
  const c = color ?? colors.textMuted;
  return (
    <Svg width={size} height={size} viewBox="0 0 48 48">
      <Circle cx="24" cy="16" r="8.5" fill={c} />
      <Path d="M7 41c0-9 8-14 17-14s17 5 17 14z" fill={c} />
    </Svg>
  );
}

/** Tab bar için sade "oluştur" (kıvılcım) ikonu (tek renk, aktif/pasif). */
export function IconMagic({ size = 26, color }: IconProps & { color?: string }) {
  const c = color ?? colors.textMuted;
  return (
    <Svg width={size} height={size} viewBox="0 0 48 48">
      <Path d="M22 4c1.4 8.5 4.1 11.2 12.5 12.5C26.1 17.8 23.4 20.5 22 29c-1.4-8.5-4.1-11.2-12.5-12.5C17.9 15.2 20.6 12.5 22 4z" fill={c} />
      <Path d="M37 27c.7 3.6 1.7 4.6 5.3 5.3-3.6.7-4.6 1.7-5.3 5.3-.7-3.6-1.7-4.6-5.3-5.3 3.6-.7 4.6-1.7 5.3-5.3z" fill={c} />
    </Svg>
  );
}

// ── Hexagon rozet (madalya) ───────────────────────────────────────────────────
export type BadgeGlyph = "trophy" | "target" | "fire" | "star";

const BADGE_COLORS: Record<
  string,
  { fill: string; ring: string; inner: string }
> = {
  bronze: { fill: "#B0763E", ring: "#8A5A2B", inner: "#F4C77B" },
  teal: { fill: "#2C8C86", ring: "#1F6C67", inner: "#8FD8D2" },
  ember: { fill: "#8A4636", ring: "#6E3427", inner: "#F5A15E" },
  royal: { fill: "#7C4DFF", ring: "#5E2FD6", inner: "#C9B4FF" },
};

/** Altıgen madalya + iç sembol. Rozetler "koleksiyon" hissi vermeli (COMPONENT). */
export function HexBadge({
  size = 60,
  glyph,
  variant = "bronze",
}: {
  size?: number;
  glyph: BadgeGlyph;
  variant?: keyof typeof BADGE_COLORS;
}) {
  const c = BADGE_COLORS[variant] ?? BADGE_COLORS.bronze;
  // Altıgen köşe noktaları (48x48 viewBox).
  const hex = "24,3 42,13.5 42,34.5 24,45 6,34.5 6,13.5";
  const hexInner = "24,9 37,16.5 37,31.5 24,39 11,31.5 11,16.5";
  return (
    <Svg width={size} height={size} viewBox="0 0 48 48">
      <Polygon points={hex} fill={c.ring} />
      <Polygon points={hexInner} fill={c.fill} />
      <G>
        {glyph === "trophy" ? (
          <Path
            d="M17 14h14v4a7 7 0 0 1-14 0zM20 26h8v4h-8zM18 31h12v3H18z"
            fill={c.inner}
          />
        ) : null}
        {glyph === "target" ? (
          <>
            <Circle cx="24" cy="24" r="9" fill={c.inner} />
            <Circle cx="24" cy="24" r="5" fill={c.fill} />
            <Circle cx="24" cy="24" r="2" fill={c.inner} />
          </>
        ) : null}
        {glyph === "fire" ? (
          <Path
            d="M25 13c1 4 5 5.5 5 10.5a6 6 0 0 1-12 0c0-2.6 1-4 2.6-5.6.1 1.6.9 2.5 1.7 3.1C21.7 17.6 22.2 15 25 13z"
            fill={c.inner}
          />
        ) : null}
        {glyph === "star" ? (
          <Path
            d="M24 13l3 6.3 6.9 1-5 4.9 1.2 6.9L24 28.8l-6.1 3.2 1.2-6.9-5-4.9 6.9-1z"
            fill={c.inner}
          />
        ) : null}
      </G>
    </Svg>
  );
}
