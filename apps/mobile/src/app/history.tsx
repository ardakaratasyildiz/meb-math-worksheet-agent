import { useAuth } from '@clerk/expo';
import { Stack, useRouter, type Href } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { SkeletonList } from '@/components/skeleton';
import { listAttempts, type AttemptHistoryItem } from '@/lib/api';
import { formatDate, scorePct, scoreTone } from '@/lib/format';
import { colors, fonts, fontSize, radius, spacing } from '@/theme/tokens';

const TONE: Record<'good' | 'mid' | 'low', string> = {
  good: colors.success,
  mid: '#d97706',
  low: colors.danger,
};

export default function HistoryScreen() {
  const { userId } = useAuth();
  const router = useRouter();
  const [items, setItems] = useState<AttemptHistoryItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!userId) return;
    setError(null);
    try {
      setItems(await listAttempts(userId));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Geçmiş yüklenemedi.');
      setItems([]);
    }
  }, [userId]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <SafeAreaView style={styles.safe} edges={['bottom']}>
      <Stack.Screen options={{ headerShown: true, title: 'Deneme Geçmişi' }} />
      <ScrollView contentContainerStyle={styles.content}>
        {items === null ? (
          <SkeletonList count={5} />
        ) : error ? (
          <Text style={styles.error}>{error}</Text>
        ) : items.length === 0 ? (
          <View style={styles.empty}>
            <Text style={styles.emptyEmoji}>📭</Text>
            <Text style={styles.emptyTitle}>Henüz çözülmüş deneme yok</Text>
            <Text style={styles.emptyText}>
              Bir alıştırma çözünce buraya düşer; geçmişini tek tek gözden geçirebilirsin.
            </Text>
            <Pressable
              style={styles.cta}
              onPress={() => router.push('/practice' as Href)}
            >
              <Text style={styles.ctaText}>✏️ Alıştırma Çöz</Text>
            </Pressable>
          </View>
        ) : (
          items.map((a) => {
            const pct = scorePct(a.score, a.total);
            const tone = TONE[scoreTone(pct)];
            return (
              <Pressable
                key={a.attempt_id}
                style={({ pressed }) => [styles.card, pressed && styles.cardPressed]}
                onPress={() => router.push(`/attempt/${a.attempt_id}` as Href)}
              >
                <View style={styles.cardMain}>
                  <Text style={styles.cardTitle} numberOfLines={1}>
                    {a.title}
                  </Text>
                  <Text style={styles.cardMeta}>
                    {a.grade ? `${a.grade}. sınıf · ` : ''}
                    {a.difficulty} · {formatDate(a.completed_at)}
                  </Text>
                </View>
                <View style={styles.scorePill}>
                  <Text style={[styles.scoreNum, { color: tone }]}>
                    {a.score}/{a.total}
                  </Text>
                  <Text style={[styles.scorePct, { color: tone }]}>%{pct}</Text>
                </View>
              </Pressable>
            );
          })
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  content: { padding: spacing.xl, gap: spacing.md },
  error: {
    color: colors.danger,
    fontFamily: fonts.bodyMedium,
    fontSize: fontSize.sm,
    textAlign: 'center',
    marginTop: spacing.xl,
  },
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    padding: spacing.lg,
  },
  cardPressed: { borderColor: colors.brand, backgroundColor: '#eff6ff' },
  cardMain: { flex: 1, gap: 2 },
  cardTitle: { fontSize: fontSize.md, fontFamily: fonts.heading, color: colors.text },
  cardMeta: { fontSize: fontSize.xs, fontFamily: fonts.body, color: colors.textMuted },
  scorePill: { alignItems: 'flex-end' },
  scoreNum: { fontSize: fontSize.md, fontFamily: fonts.bodyHeavy },
  scorePct: { fontSize: fontSize.xs, fontFamily: fonts.bodyMedium },
  empty: { alignItems: 'center', gap: spacing.sm, paddingTop: spacing.xxl },
  emptyEmoji: { fontSize: 44 },
  emptyTitle: { fontSize: fontSize.lg, fontFamily: fonts.heading, color: colors.text },
  emptyText: {
    fontSize: fontSize.sm,
    fontFamily: fonts.body,
    color: colors.textMuted,
    textAlign: 'center',
  },
  cta: {
    marginTop: spacing.md,
    backgroundColor: colors.success,
    borderRadius: radius.pill,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.xl,
  },
  ctaText: { color: colors.onBrand, fontFamily: fonts.bodyBold, fontSize: fontSize.md },
});
