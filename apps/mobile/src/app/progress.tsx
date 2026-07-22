import { useAuth } from '@clerk/expo';
import {
  SUBJECT_COLORS,
  type KazanimProgress,
  type ProgressResponse,
} from '@soruatolyesi/shared';
import { Stack, useRouter, type Href } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { SkeletonList } from '@/components/skeleton';
import { getProgress } from '@/lib/api';
import { colors, fonts, fontSize, fontWeight, radius, spacing } from '@/theme/tokens';

function pct(v: number): number {
  return Math.round((v <= 1 ? v : v / 100) * 100);
}

function KazanimRow({ k }: { k: KazanimProgress }) {
  const ratioPct = pct(k.ratio);
  const barColor = k.subject ? SUBJECT_COLORS[k.subject] : colors.brand;
  return (
    <View style={styles.kRow}>
      <View style={styles.kHead}>
        <Text style={styles.kName} numberOfLines={1}>
          {k.topic_name || k.kazanim_kod}
        </Text>
        <Text style={styles.muted}>
          {k.correct}/{k.total}
        </Text>
      </View>
      <View style={styles.barBg}>
        <View style={[styles.barFill, { width: `${ratioPct}%`, backgroundColor: barColor }]} />
      </View>
    </View>
  );
}

export default function ProgressScreen() {
  const { userId } = useAuth();
  const router = useRouter();
  const [data, setData] = useState<ProgressResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    setError(null);
    try {
      setData(await getProgress(userId));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    void load();
  }, [load]);

  const summary = data?.summary;
  const empty = summary && summary.total_answered === 0;

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
      <Stack.Screen options={{ title: 'İlerlemem' }} />
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.heading}>İlerlemem</Text>

        {loading ? (
          <SkeletonList count={4} />
        ) : error ? (
          <Text style={styles.error}>{error}</Text>
        ) : empty ? (
          <View style={styles.emptyCard}>
            <Text style={styles.muted}>Henüz çözülmüş alıştırma yok.</Text>
            <Pressable
              style={styles.primaryBtn}
              onPress={() => router.push('/practice' as Href)}
            >
              <Text style={styles.primaryBtnText}>✏️ İlk alıştırmanı çöz</Text>
            </Pressable>
          </View>
        ) : data && summary ? (
          <>
            <View style={styles.statGrid}>
              <Stat label="Çözülen" value={summary.quizzes_solved} />
              <Stat label="Toplam soru" value={summary.total_answered} />
              <Stat label="Doğruluk" value={`%${pct(summary.accuracy)}`} />
              <Stat label="Kazanım" value={summary.kazanim_count} />
            </View>

            {data.weak.length > 0 && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Geliştirilecek kazanımlar</Text>
                {data.weak.slice(0, 8).map((k) => (
                  <KazanimRow key={k.kazanim_kod} k={k} />
                ))}
              </View>
            )}

            {data.mastery.length > 0 && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Tüm kazanımlar</Text>
                {data.mastery.map((k) => (
                  <KazanimRow key={k.kazanim_kod} k={k} />
                ))}
              </View>
            )}
          </>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <View style={styles.stat}>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  content: { padding: spacing.lg, gap: spacing.lg, paddingBottom: spacing.xxl },
  heading: { fontSize: fontSize.xl, fontFamily: fonts.heading, color: colors.text },
  muted: { color: colors.textMuted, fontSize: fontSize.sm },
  error: { color: colors.danger, fontSize: fontSize.sm },
  section: { gap: spacing.sm },
  sectionTitle: { fontSize: fontSize.sm, fontWeight: fontWeight.bold, color: colors.textMuted },
  statGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md },
  stat: {
    flexGrow: 1,
    minWidth: '45%',
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    padding: spacing.md,
    backgroundColor: colors.surface,
  },
  statValue: { fontSize: fontSize.xxl, fontFamily: fonts.heading, color: colors.brand },
  statLabel: { fontSize: fontSize.xs, color: colors.textMuted },
  kRow: { gap: spacing.xs, paddingVertical: spacing.xs },
  kHead: { flexDirection: 'row', justifyContent: 'space-between', gap: spacing.sm },
  kName: { flex: 1, color: colors.text, fontSize: fontSize.sm },
  barBg: { height: 8, borderRadius: radius.pill, backgroundColor: colors.border, overflow: 'hidden' },
  barFill: { height: 8, borderRadius: radius.pill },
  emptyCard: {
    gap: spacing.md,
    padding: spacing.xl,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    alignItems: 'center',
  },
  primaryBtn: {
    backgroundColor: colors.brand,
    borderRadius: radius.md,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.xl,
    alignItems: 'center',
  },
  primaryBtnText: { color: colors.onBrand, fontSize: fontSize.md, fontFamily: fonts.bodyBold },
});
