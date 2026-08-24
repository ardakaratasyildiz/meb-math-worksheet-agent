import { useAuth } from '@clerk/expo';
import { useFocusEffect, useRouter, type Href } from 'expo-router';
import { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { IconChevron } from '@/components/icons';
import { Mascot } from '@/components/mascot';
import { Card, PrimaryButton } from '@/components/ui';
import { ApiError, listChildren, linkChild, type ChildItem } from '@/lib/api';
import { colors, fonts, fontSize, radius, spacing } from '@/theme/tokens';

/**
 * Bağlı çocuk listesi + takip koduyla çocuk ekleme — EKRANDAN BAĞIMSIZ gövde.
 *
 * İki yerde kullanılır: `app/children.tsx` (itilen ekran) ve veli rolünde üçüncü
 * SEKME (`(tabs)/progress.tsx`). Veliye kendi kişisel gelişim panosunu göstermek
 * anlamsızdı; sekme artık role göre bu gövdeyi render eder.
 */
export function ChildrenView({ header }: { header?: React.ReactNode }) {
  const { userId } = useAuth();
  const router = useRouter();
  const [items, setItems] = useState<ChildItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [code, setCode] = useState('');
  const [label, setLabel] = useState('');
  const [linking, setLinking] = useState(false);
  const [linkError, setLinkError] = useState<string | null>(null);
  // Plan sınırı (402 family_limit_reached) normal bir hata değil — kullanıcıya
  // yol gösterilir (paywall), kırmızı bir uyarıyla bırakılmaz.
  const [planBlocked, setPlanBlocked] = useState(false);

  const load = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    setError(null);
    try {
      setItems(await listChildren(userId));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  // Ekrana her dönüşte tazele — çocuk ekranından geri gelindiğinde liste eski kalmasın
  // (sınıf listesindeki senkron sorununun aynısı).
  useFocusEffect(
    useCallback(() => {
      void load();
    }, [load]),
  );

  const onLink = useCallback(async () => {
    if (!userId || linking || code.trim().length < 4) return;
    setLinking(true);
    setLinkError(null);
    setPlanBlocked(false);
    try {
      await linkChild(userId, code.trim(), label.trim() || undefined);
      setCode('');
      setLabel('');
      await load();
    } catch (e) {
      setLinkError((e as Error).message);
      if (e instanceof ApiError && e.status === 402) setPlanBlocked(true);
    } finally {
      setLinking(false);
    }
  }, [userId, linking, code, label, load]);

  return (
    <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
      {header}

      {/* Çocuk ekle */}
      <Card style={styles.addCard}>
        <Text style={styles.addTitle}>Çocuğunu ekle</Text>
        <Text style={styles.addSub}>
          Çocuğun uygulamada Profil ekranındaki takip kodunu buraya gir.
        </Text>
        <TextInput
          style={styles.input}
          placeholder="Takip kodu (ör. ABC123)"
          placeholderTextColor={colors.textFaint}
          autoCapitalize="characters"
          value={code}
          onChangeText={setCode}
        />
        <TextInput
          style={styles.input}
          placeholder="Etiket (opsiyonel — ör. Elif)"
          placeholderTextColor={colors.textFaint}
          value={label}
          onChangeText={setLabel}
        />
        {linkError ? <Text style={styles.error}>{linkError}</Text> : null}
        {planBlocked ? (
          <PrimaryButton
            label="Planları gör"
            variant="soft"
            color={colors.parent}
            onPress={() => router.push({ pathname: '/paywall', params: { reason: 'family' } })}
          />
        ) : null}
        <PrimaryButton
          label="Bağla"
          color={colors.parent}
          busy={linking}
          disabled={code.trim().length < 4}
          onPress={onLink}
        />
      </Card>

      {loading ? (
        <ActivityIndicator style={{ marginTop: spacing.xl }} color={colors.parent} />
      ) : error ? (
        <Text style={styles.error}>{error}</Text>
      ) : items.length === 0 ? (
        <View style={styles.empty}>
          <Mascot variant="reading" size={104} />
          <Text style={styles.emptyText}>Henüz bağlı çocuk yok.</Text>
        </View>
      ) : (
        <View style={styles.list}>
          {items.map((c) => (
            <Pressable
              key={c.student_id}
              onPress={() =>
                router.push(
                  `/child/${encodeURIComponent(c.student_id)}?label=${encodeURIComponent(c.label)}` as Href,
                )
              }
              style={({ pressed }) => [styles.childRow, pressed && styles.pressed]}
            >
              <View style={styles.childAvatar}>
                <Text style={styles.childInitial}>{(c.label || '?').charAt(0).toUpperCase()}</Text>
              </View>
              <View style={styles.childBody}>
                <Text style={styles.childName}>{c.label || 'Öğrenci'}</Text>
                <Text style={styles.childMeta}>İlerlemeyi gör</Text>
              </View>
              <IconChevron size={18} color={colors.textFaint} />
            </Pressable>
          ))}
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: { padding: spacing.xl, gap: spacing.lg, paddingBottom: spacing.xxl },
  addCard: { gap: spacing.md },
  addTitle: { fontFamily: fonts.bodyHeavy, fontSize: fontSize.md, color: colors.text },
  addSub: {
    fontFamily: fonts.body,
    fontSize: fontSize.sm,
    color: colors.textMuted,
    marginTop: -spacing.xs,
    lineHeight: 20,
  },
  input: {
    borderRadius: radius.lg,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    fontSize: fontSize.md,
    fontFamily: fonts.bodyMedium,
    color: colors.text,
    backgroundColor: colors.bgTint,
  },
  error: { color: colors.danger, fontSize: fontSize.sm, fontFamily: fonts.bodyMedium },
  empty: { alignItems: 'center', gap: spacing.md, paddingVertical: spacing.xl },
  emptyText: { fontFamily: fonts.body, fontSize: fontSize.md, color: colors.textMuted },
  list: { gap: spacing.sm },
  childRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.card,
    padding: spacing.lg,
  },
  pressed: { opacity: 0.9, transform: [{ scale: 0.99 }] },
  childAvatar: {
    width: 46,
    height: 46,
    borderRadius: 23,
    backgroundColor: colors.parentTint,
    alignItems: 'center',
    justifyContent: 'center',
  },
  childInitial: { fontFamily: fonts.bodyHeavy, fontSize: fontSize.lg, color: colors.parent },
  childBody: { flex: 1 },
  childName: { fontFamily: fonts.bodyBold, fontSize: fontSize.md, color: colors.text },
  childMeta: { fontFamily: fonts.body, fontSize: fontSize.xs, color: colors.textMuted, marginTop: 1 },
});
