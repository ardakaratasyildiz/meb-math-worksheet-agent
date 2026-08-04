import { useAuth } from '@clerk/expo';
import { Stack, useRouter, type Href } from 'expo-router';
import { useCallback, useMemo, useState } from 'react';
import { ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Card, PrimaryButton } from '@/components/ui';
import { DeleteAccountError, deleteAccount } from '@/lib/api';
import { colors, fonts, fontSize, radius, spacing } from '@/theme/tokens';

const CONFIRM_PHRASE = 'HESABIMI SIL';

const WHAT_GETS_DELETED = [
  'Ürettiğin çalışma kağıtları ve quizler',
  'Çözüm geçmişin',
  'İlerlemen ve rozetlerin',
  'Oluşturduğun sınıflar ve ödevler',
  'Veli-öğrenci bağlantıların',
  'Hesap bilgilerin',
];

const headerOpts = {
  headerShown: true,
  title: 'Hesabımı Sil',
  headerStyle: { backgroundColor: colors.bg },
  headerShadowVisible: false,
  headerTintColor: colors.danger,
  headerTitleStyle: { fontFamily: fonts.headingSemi, color: colors.text },
} as const;

function errorMessage(e: unknown): string {
  if (e instanceof DeleteAccountError) {
    switch (e.status) {
      case 401:
        return 'Oturumun sona ermiş görünüyor. Tekrar giriş yapıp dene.';
      case 502:
        return 'Verilerin silindi ama hesabı kapatma adımı tamamlanamadı. Lütfen tekrar dene.';
      case 503:
        return 'Sunucu şu anda bu işlemi yapamıyor. Birazdan tekrar dene.';
      case 400:
        return e.message || 'Onay metni eşleşmedi. Lütfen tam olarak yazdığından emin ol.';
      default:
        return e.message || 'Hesap silinemedi. Lütfen tekrar dene.';
    }
  }
  return e instanceof Error ? e.message : 'Hesap silinemedi. Lütfen tekrar dene.';
}

export default function DeleteAccountScreen() {
  const { signOut } = useAuth();
  const router = useRouter();
  const [confirmText, setConfirmText] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = useMemo(
    () => confirmText.trim() === CONFIRM_PHRASE && !busy,
    [confirmText, busy],
  );

  const onDelete = useCallback(async () => {
    if (!canSubmit || busy) return;
    setBusy(true);
    setError(null);
    try {
      await deleteAccount();
      await signOut();
      router.replace('/' as Href);
    } catch (e) {
      setError(errorMessage(e));
      setBusy(false);
    }
  }, [canSubmit, busy, signOut, router]);

  return (
    <View style={styles.root}>
      <Stack.Screen options={headerOpts} />
      <SafeAreaView style={styles.safe} edges={['bottom']}>
        <ScrollView contentContainerStyle={styles.content}>
          <Card style={styles.warnCard}>
            <Text style={styles.warnTitle}>Bu işlem geri alınamaz</Text>
            <Text style={styles.warnText}>
              Hesabını sildiğinde tüm verilerin kalıcı olarak kaybolur. Bu işlemi geri
              alma imkanı yoktur.
            </Text>
          </Card>

          <Card>
            <Text style={styles.sectionTitle}>Silinecekler</Text>
            {WHAT_GETS_DELETED.map((line) => (
              <View key={line} style={styles.bulletRow}>
                <Text style={styles.bulletDot}>•</Text>
                <Text style={styles.bulletText}>{line}</Text>
              </View>
            ))}
          </Card>

          <View style={styles.subBanner}>
            <Text style={styles.subBannerText}>
              Aboneliğin varsa App Store / Google Play üzerinden ayrıca iptal etmelisin —
              hesabını silmek aboneliği durdurmaz.
            </Text>
          </View>

          <Card>
            <Text style={styles.sectionTitle}>Onayla</Text>
            <Text style={styles.confirmHint}>
              Devam etmek için aşağıya tam olarak <Text style={styles.confirmPhrase}>{CONFIRM_PHRASE}</Text> yaz.
            </Text>
            <TextInput
              value={confirmText}
              onChangeText={setConfirmText}
              placeholder={CONFIRM_PHRASE}
              placeholderTextColor={colors.textFaint}
              autoCapitalize="characters"
              autoCorrect={false}
              editable={!busy}
              style={styles.input}
            />

            {error ? <Text style={styles.error}>{error}</Text> : null}

            <PrimaryButton
              label="Hesabımı kalıcı olarak sil"
              color={colors.danger}
              disabled={!canSubmit}
              busy={busy}
              onPress={() => void onDelete()}
            />
          </Card>
        </ScrollView>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  safe: { flex: 1 },
  content: { padding: spacing.xl, gap: spacing.lg, paddingBottom: spacing.xxl },

  warnCard: { backgroundColor: '#FDECEC', gap: spacing.xs },
  warnTitle: { fontFamily: fonts.heading, fontSize: fontSize.lg, color: colors.danger },
  warnText: { fontFamily: fonts.body, fontSize: fontSize.sm, color: colors.text },

  sectionTitle: {
    fontFamily: fonts.heading,
    fontSize: fontSize.md,
    color: colors.text,
    marginBottom: spacing.sm,
  },
  bulletRow: { flexDirection: 'row', gap: spacing.sm, marginBottom: spacing.xs },
  bulletDot: { fontFamily: fonts.bodyBold, fontSize: fontSize.md, color: colors.textMuted },
  bulletText: { flex: 1, fontFamily: fonts.body, fontSize: fontSize.sm, color: colors.text },

  subBanner: {
    backgroundColor: colors.tintYellow,
    borderRadius: radius.card,
    padding: spacing.lg,
  },
  subBannerText: {
    fontFamily: fonts.bodyMedium,
    fontSize: fontSize.sm,
    color: colors.rewardDark,
  },

  confirmHint: {
    fontFamily: fonts.body,
    fontSize: fontSize.sm,
    color: colors.textMuted,
    marginBottom: spacing.md,
  },
  confirmPhrase: { fontFamily: fonts.bodyBold, color: colors.text },
  input: {
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surfaceAlt,
    borderRadius: radius.lg,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
    fontFamily: fonts.bodyMedium,
    fontSize: fontSize.md,
    color: colors.text,
    marginBottom: spacing.lg,
  },
  error: {
    fontFamily: fonts.bodyMedium,
    fontSize: fontSize.sm,
    color: colors.danger,
    marginBottom: spacing.md,
  },
});
