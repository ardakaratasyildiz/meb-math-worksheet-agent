import { useAuth } from '@clerk/expo';
import { SUBJECT_COLORS, type KazanimProgress, type ProgressResponse } from '@soruatolyesi/shared';
import { Stack, useLocalSearchParams } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Mascot } from '@/components/mascot';
import { Card, ProgressBar } from '@/components/ui';
import { getChildProgress } from '@/lib/api';
import { colors, fonts, fontSize, radius, shadow, spacing } from '@/theme/tokens';

function pct(v: number): number {
  return Math.round((v <= 1 ? v : v / 100) * 100);
}

function KazanimRow({ k }: { k: KazanimProgress }) {
  const ratio = k.ratio <= 1 ? k.ratio : k.ratio / 100;
  const barColor = k.subject ? SUBJECT_COLORS[k.subject] : colors.parent;
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

export default function ChildProgressScreen() {
  const { userId } = useAuth();
  const { id, label } = useLocalSearchParams<{ id: string; label?: string }>();
  const [data, setData] = useState<ProgressResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!userId || !id) return;
    setLoading(true);
    setError(null);
    try {
      setData(await getChildProgress(userId, id));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [userId, id]);

  useEffect(() => {
    void load();
  }, [load]);

  const summary = data?.summary;
  const empty = summary && summary.total_answered === 0;

  return (
    <View style={styles.root}>
      <Stack.Screen
        options={{
          headerShown: true,
          title: label || 'Çocuğun İlerlemesi',
          headerStyle: { backgroundColor: colors.bg },
          headerShadowVisible: false,
          headerTintColor: colors.parent,
          headerTitleStyle: { fontFamily: fonts.headingSemi, color: colors.text },
        }}
      />
      <SafeAreaView style={styles.safe} edges={['bottom']}>
        <ScrollView contentContainerStyle={styles.content}>
          {loading ? (
            <ActivityIndicator style={{ marginTop: spacing.xl }} color={colors.parent} />
          ) : error ? (
            <Text style={styles.error}>{error}</Text>
          ) : empty ? (
            <View style={styles.empty}>
              <Mascot variant="reading" size={104} />
              <Text style={styles.emptyText}>Bu öğrenci henüz alıştırma çözmemiş.</Text>
            </View>
          ) : data && summary ? (
            <>
              <View style={styles.statGrid}>
                <Stat bg={colors.parentTint} accent={colors.parent} value={summary.total_answered} label="Toplam soru" />
                <Stat bg={colors.tintGreen} accent={colors.success} value={`%${pct(summary.accuracy)}`} label="Doğruluk" />
                <Stat bg={colors.tintBlue} accent={colors.brand} value={summary.quizzes_solved} label="Çözülen" />
                <Stat bg={colors.tintYellow} accent={colors.onTintYellow} value={summary.kazanim_count} label="Kazanım" />
              </View>

              {data.weak.length > 0 && (
                <Card>
                  <Text style={styles.sectionTitle}>Geliştirilecek konular</Text>
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

function Stat({ bg, accent, value, label }: { bg: string; accent: string; value: number | string; label: string }) {
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
  content: { padding: spacing.xl, gap: spacing.lg },
  error: { color: colors.danger, fontSize: fontSize.sm, fontFamily: fonts.bodyMedium },
  sectionTitle: { fontSize: fontSize.lg, fontFamily: fonts.heading, color: colors.text },
  empty: { alignItems: 'center', gap: spacing.md, paddingVertical: spacing.xl },
  emptyText: { fontFamily: fonts.body, fontSize: fontSize.md, color: colors.textMuted },

  statGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md },
  stat: { flexGrow: 1, flexBasis: '45%', borderRadius: radius.card, padding: spacing.lg, ...shadow.card },
  statValue: { fontSize: fontSize.xxl, fontFamily: fonts.heading },
  statLabel: { fontSize: fontSize.sm, color: colors.textMuted, fontFamily: fonts.bodyMedium, marginTop: 2 },

  kList: { gap: spacing.md, marginTop: spacing.md },
  kRow: { gap: spacing.xs },
  kHead: { flexDirection: 'row', justifyContent: 'space-between', gap: spacing.sm },
  kName: { flex: 1, color: colors.text, fontSize: fontSize.sm, fontFamily: fonts.bodyMedium },
  kCount: { color: colors.textMuted, fontSize: fontSize.sm, fontFamily: fonts.bodyBold },
});
