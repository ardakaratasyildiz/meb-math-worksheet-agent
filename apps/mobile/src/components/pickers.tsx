import { Pressable, StyleSheet, Text, View } from "react-native";

import { colors, fonts, fontSize, radius, shadow, spacing } from "@/theme/tokens";

/** Seçilebilir yuvarlak etiket (ders/sınıf/zorluk seçicileri). */
export function Chip({
  label,
  selected,
  onPress,
  color,
}: {
  label: string;
  selected: boolean;
  onPress: () => void;
  color?: string;
}) {
  const accent = color ?? colors.brand;
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.chip,
        selected ? [{ backgroundColor: accent }, shadow.card] : styles.chipIdle,
        pressed && styles.chipPressed,
      ]}
    >
      <Text style={[styles.chipText, selected && styles.chipTextSelected]}>{label}</Text>
    </Pressable>
  );
}

/** Başlıklı, yatay saran chip satırı. */
export function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      <View style={styles.chipRow}>{children}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  section: { gap: spacing.sm },
  sectionTitle: {
    fontSize: fontSize.sm,
    fontFamily: fonts.bodyBold,
    color: colors.textMuted,
  },
  chipRow: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  chip: {
    borderRadius: radius.pill,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm + 2,
  },
  chipIdle: {
    backgroundColor: colors.surface,
    borderWidth: 1.5,
    borderColor: colors.border,
  },
  chipPressed: { transform: [{ scale: 0.96 }] },
  chipText: {
    color: colors.text,
    fontSize: fontSize.sm,
    fontFamily: fonts.bodyBold,
  },
  chipTextSelected: { color: colors.onBrand },
});
