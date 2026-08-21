import { Stack } from 'expo-router';
import { Linking, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Card } from '@/components/ui';
import { MEB_DISCLAIMER_LONG, MEB_SOURCES, type SourceLink } from '@/lib/legal';
import { colors, fonts, fontSize, radius, spacing } from '@/theme/tokens';

const headerOpts = {
  headerShown: true,
  title: 'Hakkında & Kaynaklar',
  headerStyle: { backgroundColor: colors.bg },
  headerShadowVisible: false,
  headerTintColor: colors.text,
  headerTitleStyle: { fontFamily: fonts.headingSemi, color: colors.text },
} as const;

/**
 * Bağımsızlık uyarısı + müfredat bilgisinin resmi kaynakları.
 * Google Play "Misleading Claims" politikasının uygulama içi ayağı (lib/legal.ts).
 */
export default function AboutScreen() {
  return (
    <View style={styles.root}>
      <Stack.Screen options={headerOpts} />
      <SafeAreaView style={styles.safe} edges={['bottom']}>
        <ScrollView contentContainerStyle={styles.content}>
          <Card>
            <Text style={styles.cardTitle}>Bağımsızlık bildirimi</Text>
            <Text style={styles.body}>{MEB_DISCLAIMER_LONG}</Text>
          </Card>

          <Card>
            <Text style={styles.cardTitle}>Resmi kaynaklar</Text>
            <Text style={styles.body}>
              Uygulamada geçen sınıf, ünite ve kazanım başlıklarının kaynağı MEB’in kamuya açık
              öğretim programlarıdır:
            </Text>
            <View style={styles.sourceList}>
              {MEB_SOURCES.map((s) => (
                <SourceRow key={s.url} source={s} />
              ))}
            </View>
          </Card>

          <Card>
            <Text style={styles.cardTitle}>İçerik nasıl üretiliyor?</Text>
            <Text style={styles.body}>
              Sorular, cevap anahtarları ve çözümler yapay zeka ile üretilir; seçtiğin kazanımla
              hizalanması için otomatik denetimlerden geçer. Buna rağmen hata içerebilir —
              üretilen içerik MEB’in resmi yayını, ders kitabı ya da sınav materyali değildir.
              Kullanmadan önce kontrol etmeni öneririz.
            </Text>
          </Card>

          <Text style={styles.version}>Soru Atölyesi · sürüm 1.0.0</Text>
        </ScrollView>
      </SafeAreaView>
    </View>
  );
}

function SourceRow({ source }: { source: SourceLink }) {
  return (
    <Pressable
      onPress={() => void Linking.openURL(source.url)}
      style={({ pressed }) => [styles.sourceRow, pressed && styles.pressed]}
      accessibilityRole="link"
      accessibilityLabel={`${source.label} — ${source.note}`}
    >
      <Text style={styles.sourceUrl}>{source.url}</Text>
      <Text style={styles.sourceNote}>{source.note}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  safe: { flex: 1 },
  content: { padding: spacing.xl, gap: spacing.lg, paddingBottom: 60 },
  cardTitle: { fontFamily: fonts.heading, fontSize: fontSize.lg, color: colors.text, marginBottom: spacing.sm },
  body: { fontFamily: fonts.body, fontSize: fontSize.sm, color: colors.textMuted, lineHeight: 21 },
  sourceList: { marginTop: spacing.md, gap: spacing.sm },
  sourceRow: {
    backgroundColor: colors.tintBlue,
    borderRadius: radius.card,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
    gap: 2,
  },
  sourceUrl: { fontFamily: fonts.bodyBold, fontSize: fontSize.sm, color: colors.brand },
  sourceNote: { fontFamily: fonts.body, fontSize: fontSize.xs, color: colors.textMuted },
  pressed: { opacity: 0.6 },
  version: { fontFamily: fonts.body, fontSize: fontSize.xs, color: colors.textFaint, textAlign: 'center' },
});
