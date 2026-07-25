import { useAuth } from '@clerk/expo';
import { Stack } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { IconChevron } from '@/components/icons';
import { Mascot } from '@/components/mascot';
import { SkeletonList } from '@/components/skeleton';
import { Card } from '@/components/ui';
import {
  getShareResults,
  listMyShares,
  type ShareResultsResponse,
  type ShareSummary,
} from '@/lib/api';
import { colors, fonts, fontSize, radius, spacing } from '@/theme/tokens';

const headerOpts = {
  headerShown: true,
  title: 'Paylaşımlarım',
  headerStyle: { backgroundColor: colors.bg },
  headerShadowVisible: false,
  headerTintColor: colors.brand,
  headerTitleStyle: { fontFamily: fonts.headingSemi, color: colors.text },
} as const;

export default function SharesScreen() {
  const { userId } = useAuth();
  const [items, setItems] = useState<ShareSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [openId, setOpenId] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, ShareResultsResponse>>({});

  const load = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    setError(null);
    try {
      setItems(await listMyShares(userId));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    void load();
  }, [load]);

  const toggle = useCallback(
    async (shareId: string) => {
      if (openId === shareId) {
        setOpenId(null);
        return;
      }
      setOpenId(shareId);
      if (!results[shareId] && userId) {
        try {
          const r = await getShareResults(shareId, userId);
          setResults((prev) => ({ ...prev, [shareId]: r }));
        } catch {
          /* sessiz — satır açık kalır, sonuç boş */
        }
      }
    },
    [openId, results, userId],
  );

  return (
    <View style={styles.root}>
      <Stack.Screen options={headerOpts} />
      <SafeAreaView style={styles.safe} edges={['bottom']}>
        <ScrollView contentContainerStyle={styles.content}>
          {loading ? (
            <SkeletonList count={4} />
          ) : error ? (
            <Text style={styles.error}>{error}</Text>
          ) : items.length === 0 ? (
            <Card style={styles.empty}>
              <Mascot variant="wave" size={112} />
              <Text style={styles.emptyText}>Henüz paylaşım yok.</Text>
              <Text style={styles.emptyHint}>
                Bir test çöz → "Paylaş" ile arkadaşlarına gönder. Çözenler burada görünür.
              </Text>
            </Card>
          ) : (
            items.map((s) => {
              const open = openId === s.share_id;
              const res = results[s.share_id];
              return (
                <Card key={s.share_id} style={styles.card}>
                  <Pressable style={styles.row} onPress={() => void toggle(s.share_id)}>
                    <View style={styles.rowBody}>
                      <Text style={styles.title} numberOfLines={1}>
                        {s.title}
                      </Text>
                      <Text style={styles.meta}>
                        {s.attempt_count} çözüm
                        {s.avg_score_pct != null ? ` · ort. %${s.avg_score_pct}` : ''}
                      </Text>
                    </View>
                    <IconChevron size={18} color={colors.textFaint} />
                  </Pressable>

                  {open ? (
                    <View style={styles.results}>
                      {res ? (
                        res.items.length > 0 ? (
                          res.items.map((it, i) => (
                            <View key={i} style={styles.resultRow}>
                              <Text style={styles.solver} numberOfLines={1}>
                                {it.solver_label || 'İsimsiz'}
                              </Text>
                              <Text style={styles.score}>
                                {it.score}/{it.total}
                              </Text>
                            </View>
                          ))
                        ) : (
                          <Text style={styles.emptyHint}>Henüz çözen yok.</Text>
                        )
                      ) : (
                        <Text style={styles.emptyHint}>Yükleniyor…</Text>
                      )}
                    </View>
                  ) : null}
                </Card>
              );
            })
          )}
        </ScrollView>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  safe: { flex: 1 },
  content: { padding: spacing.xl, gap: spacing.md, paddingBottom: spacing.xxl },
  error: { color: colors.danger, fontSize: fontSize.sm, fontFamily: fonts.bodyMedium },

  card: { padding: spacing.lg },
  row: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  rowBody: { flex: 1 },
  title: { fontFamily: fonts.heading, fontSize: fontSize.md, color: colors.text },
  meta: { fontFamily: fonts.body, fontSize: fontSize.sm, color: colors.textMuted, marginTop: 1 },

  results: { marginTop: spacing.md, gap: spacing.sm, borderTopWidth: 1, borderTopColor: colors.border, paddingTop: spacing.md },
  resultRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  solver: { flex: 1, fontFamily: fonts.bodyMedium, fontSize: fontSize.sm, color: colors.text },
  score: { fontFamily: fonts.bodyBold, fontSize: fontSize.sm, color: colors.brand },

  empty: { alignItems: 'center', gap: spacing.sm, paddingVertical: spacing.xl },
  emptyText: { fontFamily: fonts.heading, fontSize: fontSize.lg, color: colors.text },
  emptyHint: { fontFamily: fonts.body, fontSize: fontSize.sm, color: colors.textMuted, textAlign: 'center' },
});
