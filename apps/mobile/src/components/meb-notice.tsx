import { useRouter, type Href } from 'expo-router';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { MEB_DISCLAIMER_SHORT } from '@/lib/legal';
import { colors, fonts, fontSize, radius, spacing } from '@/theme/tokens';

/**
 * Müfredat bilgisinin göründüğü ekranların altına konan kısa künye:
 * "MEB'i temsil etmiyoruz" + resmi kaynaklara giden Hakkında ekranı.
 * Gerekçe: lib/legal.ts başlığı.
 */
export function MebNotice() {
  const router = useRouter();
  return (
    <View style={styles.wrap}>
      <Text style={styles.text}>{MEB_DISCLAIMER_SHORT}</Text>
      <Pressable
        onPress={() => router.push('/about' as Href)}
        style={({ pressed }) => pressed && styles.pressed}
      >
        <Text style={styles.link}>Resmî MEB kaynakları ve künye →</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.lg,
    gap: spacing.xs,
  },
  text: { fontFamily: fonts.body, fontSize: fontSize.xs, color: colors.textMuted, lineHeight: 18 },
  link: { fontFamily: fonts.bodyBold, fontSize: fontSize.xs, color: colors.brand },
  pressed: { opacity: 0.6 },
});
