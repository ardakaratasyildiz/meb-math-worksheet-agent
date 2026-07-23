import { useAuth } from '@clerk/expo';
import {
  SUBJECT_COLORS,
  type KazanimProgress,
  type ProgressResponse,
} from '@soruatolyesi/shared';
import { useRouter, type Href } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { IconCalendar, IconChevron, IconPencil } from '@/components/icons';
import { Mascot } from '@/components/mascot';
import { SkeletonList } from '@/components/skeleton';
import { Card, PrimaryButton, ProgressBar, ScreenHeader } from '@/components/ui';
import { getProgress } from '@/lib/api';
import { colors, fonts, fontSize, radius, shadow, spacing } from '@/theme/tokens';

function pct(v: number): number {
  return Math.round((v <= 1 ? v : v / 100) * 100);
}

function KazanimRow({ k }: { k: KazanimProgress }) {
  const ratio = k.ratio <= 1 ? k.ratio : k.ratio / 100;
  const barColor = k.subject ? SUBJECT_COLORS[k.subject] : colors.brand;
  return (
    <View style={styles.kRow}>
      <View style={styles.kHead}>
        <Text style={styles.kName} numberOfLines={1}>
          {k.topic_name || k.kazanim_kod}
        </Text>
        <Text style={styles.kCount}>
          {k.correct}/{k.total}
        </Text>
      </View>
      <ProgressBar progress={ratio} color={barColor} height={8} />
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
    <View style={styles.root}>
      <SafeAreaView style={styles.safe} edges={['top']}>
        <ScrollView contentContainerStyle={styles.content}>
          <ScreenHeader
            title="İlerlemem"
            subtitle="Başarılarını ve gelişimini takip et"
            right={<Mascot variant="reading" size={64} />}
          />

          {loading ? (
            <SkeletonList count={4} />
          ) : error ? (
            <Text style={styles.error}>{error}</Text>
          ) : empty ? (
            <Card style={styles.emptyCard}>
              <Mascot variant="wave" size={112} />
              <Text style={styles.emptyText}>Henüz çözülmüş alıştırma yok.</Text>
              <PrimaryButton
                label="İlk alıştırmanı çöz"
                color={colors.success}
                onPress={() => router.push('/create' as Href)}
                icon={<IconPencil size={22} />}
              />
            </Card>
          ) : data && summary ? (
            <>
              <View style={styles.statGrid}>
                <StatCard
                  bg={colors.tintBlue}
                  accent={colors.brand}
                  value={summary.quizzes_solved}
                  label="Çözülen"
                />
                <StatCard
                  bg={colors.tintGreen}
                  accent={colors.success}
                  value={summary.total_answered}
                  label="Toplam soru"
                />
                <StatCard
                  bg={colors.tintYellow}
                  accent={colors.onTintYellow}
                  value={`%${pct(summary.accuracy)}`}
                  label="Doğruluk"
                />
                <StatCard
                  bg={colors.tintPurple}
                  accent={colors.magic}
                  value={summary.kazanim_count}
                  label="Kazanım"
                />
              </View>

              <Pressable
                style={({ pressed }) => [styles.historyBtn, pressed && styles.historyBtnPressed]}
                onPress={() => router.push('/history' as Href)}
              >
                <View style={styles.historyIcon}>
                  <IconCalendar size={28} />
                </View>
                <View style={styles.historyBody}>
                  <Text style={styles.historyTitle}>Deneme geçmişin</Text>
                  <Text style={styles.historySub}>Tüm çözdüğün alıştırmaları gör</Text>
                </View>
                <IconChevron size={18} color={colors.textFaint} />
              </Pressable>

              {data.weak.length > 0 && (
                <Card>
                  <Text style={styles.sectionTitle}>Geliştirilecek kazanımlar</Text>
                  <View style={styles.kList}>
                    {data.weak.slice(0, 8).map((k) => (
                      <KazanimRow key={k.kazanim_kod} k={k} />
                    ))}
                  </View>
                </Card>
              )}

              {data.mastery.length > 0 && (
                <Card>
                  <Text style={styles.sectionTitle}>Tüm kazanımlar</Text>
                  <View style={styles.kList}>
                    {data.mastery.map((k) => (
                      <KazanimRow key={k.kazanim_kod} k={k} />
                    ))}
                  </View>
                </Card>
              )}
            </>
          ) : null}
        </ScrollView>
      </SafeAreaView>
    </View>
  );
}

function StatCard({
  bg,
  accent,
  value,
  label,
}: {
  bg: string;
  accent: string;
  value: number | string;
  label: string;
}) {
  return (
    <View style={[styles.stat, { backgroundColor: bg }]}>
      <Text style={[styles.statValue, { color: accent }]}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  safe: { flex: 1 },
  content: { padding: spacing.xl, gap: spacing.lg, paddingBottom: 120 }, // yüzen tab bar payı
  error: { color: colors.danger, fontSize: fontSize.sm, fontFamily: fonts.bodyMedium },
  sectionTitle: { fontSize: fontSize.lg, fontFamily: fonts.heading, color: colors.text },

  statGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md },
  stat: {
    flexGrow: 1,
    flexBasis: '45%',
    borderRadius: radius.card,
    padding: spacing.lg,
    ...shadow.card,
  },
  statValue: { fontSize: fontSize.xxl, fontFamily: fonts.heading },
  statLabel: { fontSize: fontSize.sm, color: colors.textMuted, fontFamily: fonts.bodyMedium, marginTop: 2 },

  historyBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    borderRadius: radius.card,
    backgroundColor: colors.surface,
    padding: spacing.lg,
    ...shadow.card,
  },
  historyBtnPressed: { transform: [{ scale: 0.99 }], opacity: 0.92 },
  historyIcon: {
    width: 48,
    height: 48,
    borderRadius: radius.md,
    backgroundColor: colors.tintYellow,
    alignItems: 'center',
    justifyContent: 'center',
  },
  historyBody: { flex: 1 },
  historyTitle: { fontSize: fontSize.md, fontFamily: fonts.heading, color: colors.text },
  historySub: { fontSize: fontSize.xs, fontFamily: fonts.body, color: colors.textMuted, marginTop: 1 },

  kList: { gap: spacing.md, marginTop: spacing.md },
  kRow: { gap: spacing.xs },
  kHead: { flexDirection: 'row', justifyContent: 'space-between', gap: spacing.sm },
  kName: { flex: 1, color: colors.text, fontSize: fontSize.sm, fontFamily: fonts.bodyMedium },
  kCount: { color: colors.textMuted, fontSize: fontSize.sm, fontFamily: fonts.bodyBold },

  emptyCard: { gap: spacing.md, alignItems: 'center', paddingVertical: spacing.xl },
  emptyText: { color: colors.textMuted, fontSize: fontSize.md, fontFamily: fonts.body },
});
