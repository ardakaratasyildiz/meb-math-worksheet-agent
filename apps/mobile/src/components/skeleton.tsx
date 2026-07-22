import { useEffect, useRef } from "react";
import { Animated, type DimensionValue, StyleSheet, View } from "react-native";

import { colors, radius, spacing } from "@/theme/tokens";

/** Nabız atan iskelet blok (yükleniyor placeholder'ı — spinner yerine). */
export function SkeletonBlock({
  width = "100%",
  height = 16,
  style,
}: {
  width?: DimensionValue;
  height?: number;
  style?: object;
}) {
  const opacity = useRef(new Animated.Value(0.4)).current;

  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(opacity, { toValue: 1, duration: 650, useNativeDriver: true }),
        Animated.timing(opacity, { toValue: 0.4, duration: 650, useNativeDriver: true }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [opacity]);

  return (
    <Animated.View
      style={[
        { width, height, borderRadius: radius.sm, backgroundColor: colors.border, opacity },
        style,
      ]}
    />
  );
}

/** Kart görünümlü iskelet satırı (soru/liste öğesi placeholder'ı). */
export function SkeletonCard() {
  return (
    <View style={styles.card}>
      <SkeletonBlock width="70%" height={14} />
      <SkeletonBlock width="90%" height={14} />
      <SkeletonBlock width="45%" height={14} />
    </View>
  );
}

/** Birden çok iskelet kart. */
export function SkeletonList({ count = 3 }: { count?: number }) {
  return (
    <View style={{ gap: spacing.md }}>
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    padding: spacing.md,
    gap: spacing.sm,
    backgroundColor: colors.surface,
  },
});
