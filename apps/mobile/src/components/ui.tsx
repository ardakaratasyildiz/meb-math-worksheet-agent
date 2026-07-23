/**
 * Yeniden kullanılabilir UI primitifleri — COMPONENT library'nin RN karşılığı.
 * "Never invent new component styles. Always reuse this system."
 *
 *  - Card: yüzen beyaz kart (radius.card + tek gölge sistemi).
 *  - StatChip: kompakt status pill (ikon + değer + etiket) — seri/seviye/XP.
 *  - ProgressBar: yuvarlak, mount'ta dolan (animasyon hissi — PSYCHOLOGY: "progress must move").
 *  - SpeechBubble: maskot konuşma balonu (kuyruklu, sıcak tint).
 */
import { useEffect, type ReactNode } from "react";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  View,
  type StyleProp,
  type ViewStyle,
} from "react-native";
import Animated, {
  Easing,
  useAnimatedStyle,
  useSharedValue,
  withTiming,
} from "react-native-reanimated";

import { colors, fonts, fontSize, radius, shadow, spacing } from "@/theme/tokens";

// ── Card ────────────────────────────────────────────────────────────────────
export function Card({
  children,
  style,
  floating = false,
}: {
  children: ReactNode;
  style?: StyleProp<ViewStyle>;
  /** Daha derin gölge (renkli/hero kartlar). */
  floating?: boolean;
}) {
  return (
    <View style={[styles.card, floating ? shadow.floating : shadow.card, style]}>
      {children}
    </View>
  );
}

// ── StatChip (seri / seviye / XP) ─────────────────────────────────────────────
export function StatChip({
  icon,
  value,
  label,
}: {
  icon: ReactNode;
  value: string;
  label: string;
}) {
  return (
    <View style={[styles.chip, shadow.card]}>
      {icon}
      <View style={styles.chipText}>
        <Text style={styles.chipValue} numberOfLines={1}>
          {value}
        </Text>
        <Text style={styles.chipLabel} numberOfLines={1}>
          {label}
        </Text>
      </View>
    </View>
  );
}

// ── ProgressBar (mount'ta dolar) ──────────────────────────────────────────────
export function ProgressBar({
  progress,
  color = colors.success,
  height = 14,
}: {
  /** 0..1 */
  progress: number;
  color?: string;
  height?: number;
}) {
  const p = Math.max(0, Math.min(1, progress));
  const w = useSharedValue(0);

  useEffect(() => {
    w.value = withTiming(p, { duration: 900, easing: Easing.out(Easing.cubic) });
  }, [p, w]);

  const fillStyle = useAnimatedStyle(() => ({
    width: `${w.value * 100}%`,
  }));

  return (
    <View style={[styles.track, { height, borderRadius: height / 2 }]}>
      <Animated.View
        style={[
          styles.fill,
          { backgroundColor: color, borderRadius: height / 2 },
          fillStyle,
        ]}
      >
        {/* Üstte hafif parlaklık şeridi — "canlı/parlak" his. */}
        <View style={[styles.fillGloss, { borderRadius: height / 2 }]} />
      </Animated.View>
    </View>
  );
}

// ── SpeechBubble (maskot konuşması) ───────────────────────────────────────────
export function SpeechBubble({
  children,
  style,
}: {
  children: ReactNode;
  style?: StyleProp<ViewStyle>;
}) {
  return (
    <View style={[styles.bubbleWrap, style]}>
      <View style={styles.bubble}>{children}</View>
      {/* Sağa bakan kuyruk (maskota doğru). */}
      <View style={styles.bubbleTail} />
    </View>
  );
}

// ── ScreenHeader (sekme ekranı başlığı — ana ekranla aynı tipografi) ──────────
export function ScreenHeader({
  title,
  subtitle,
  right,
}: {
  title: string;
  subtitle?: string;
  /** Sağda küçük dekoratif öğe (maskot/ikon). */
  right?: ReactNode;
}) {
  return (
    <View style={styles.headerRow}>
      <View style={styles.headerText}>
        <Text style={styles.headerTitle}>{title}</Text>
        {subtitle ? <Text style={styles.headerSubtitle}>{subtitle}</Text> : null}
      </View>
      {right ? <View style={styles.headerRight}>{right}</View> : null}
    </View>
  );
}

// ── PrimaryButton (yuvarlak, renkli, gölgeli CTA — ikon opsiyonlu) ────────────
export function PrimaryButton({
  label,
  onPress,
  busy = false,
  disabled = false,
  color = colors.brand,
  icon,
  variant = "solid",
}: {
  label: string;
  onPress: () => void;
  busy?: boolean;
  disabled?: boolean;
  color?: string;
  icon?: ReactNode;
  /** solid = dolu renk · soft = tint zemin + renkli metin (ikincil). */
  variant?: "solid" | "soft";
}) {
  const soft = variant === "soft";
  const isOff = busy || disabled;
  return (
    <Pressable
      onPress={onPress}
      disabled={isOff}
      style={({ pressed }) => [
        styles.btn,
        soft
          ? { backgroundColor: colors.surface }
          : [{ backgroundColor: color }, shadow.card],
        isOff && styles.btnOff,
        pressed && !isOff && styles.btnPressed,
      ]}
    >
      {busy ? (
        <ActivityIndicator color={soft ? color : colors.onBrand} />
      ) : (
        <>
          {icon ? <View style={styles.btnIcon}>{icon}</View> : null}
          <Text style={[styles.btnText, { color: soft ? color : colors.onBrand }]}>
            {label}
          </Text>
        </>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    padding: spacing.xl,
  },

  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: spacing.md,
  },
  headerText: { flex: 1 },
  headerTitle: {
    fontFamily: fonts.heading,
    fontSize: fontSize.xxl,
    color: colors.text,
  },
  headerSubtitle: {
    fontFamily: fonts.body,
    fontSize: fontSize.sm,
    color: colors.textMuted,
    marginTop: 2,
  },
  headerRight: { marginLeft: spacing.sm },

  btn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.sm,
    borderRadius: radius.pill,
    paddingVertical: spacing.lg,
    paddingHorizontal: spacing.xl,
  },
  btnPressed: { transform: [{ scale: 0.98 }] },
  btnOff: { opacity: 0.45 },
  btnIcon: { marginRight: 2 },
  btnText: { fontFamily: fonts.heading, fontSize: fontSize.md },

  chip: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    paddingVertical: spacing.sm + 2,
    paddingHorizontal: spacing.md,
  },
  chipText: { flex: 1 },
  chipValue: {
    fontFamily: fonts.heading,
    fontSize: fontSize.md,
    color: colors.text,
  },
  chipLabel: {
    fontFamily: fonts.body,
    fontSize: fontSize.xs,
    color: colors.textMuted,
    marginTop: -1,
  },

  track: {
    width: "100%",
    backgroundColor: colors.track,
    overflow: "hidden",
  },
  fill: {
    height: "100%",
    minWidth: 14,
    overflow: "hidden",
  },
  fillGloss: {
    position: "absolute",
    top: 2,
    left: 4,
    right: 4,
    height: 3,
    backgroundColor: "rgba(255,255,255,0.45)",
  },

  bubbleWrap: { alignSelf: "flex-start" },
  bubble: {
    backgroundColor: colors.tintOrange,
    borderRadius: radius.xxl,
    borderBottomLeftRadius: radius.md,
    paddingVertical: spacing.lg,
    paddingHorizontal: spacing.xl,
  },
  bubbleTail: {
    position: "absolute",
    right: -8,
    top: 22,
    width: 20,
    height: 20,
    backgroundColor: colors.tintOrange,
    borderRadius: 6,
    transform: [{ rotate: "45deg" }],
  },
});
