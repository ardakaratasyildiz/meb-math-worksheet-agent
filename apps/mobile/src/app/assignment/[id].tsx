import { useAuth } from '@clerk/expo';
import { Stack, useLocalSearchParams, useRouter, type Href } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { IconChevron } from '@/components/icons';
import { Card } from '@/components/ui';
import { getAssignmentResults, type AssignmentResultsResponse } from '@/lib/api';
import { colors, fonts, fontSize, radius, spacing } from '@/theme/tokens';

function scoreTone(ratio: number): string {
  if (ratio >= 0.7) return colors.success;
  if (ratio >= 0.4) return colors.reward;
  return colors.energy;
}

export default function AssignmentResultsScreen() {
  const { userId } = useAuth();
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [data, setData] = useState<AssignmentResultsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!userId || !id) return;
    setLoading(true);
    setError(null);
    try {
      setData(await getAssignmentResults(id, userId));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [userId, id]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <View style={styles.root}>
      <Stack.Screen
        options={{
          headerShown: true,
          title: 'Ödev Sonuçları',
          headerStyle: { backgroundColor: colors.bg },
          headerShadowVisible: false,
          headerTintColor: colors.brand,
          headerTitleStyle: { fontFamily: fonts.headingSemi, color: colors.text },
        }}
      />
      <SafeAreaView style={styles.safe} edges={['bottom']}>
        <ScrollView contentContainerStyle={styles.content}>
          {loading ? (
            <ActivityIndicator style={{ marginTop: spacing.xl }} color={colors.brand} />
          ) : error ? (
            <Text style={styles.error}>{error}</Text>
          ) : data ? (
            <>
              <Card style={styles.summary}>
                <Text style={styles.title} numberOfLines={2}>
                  {data.title}
                </Text>
                <Text style={styles.summaryLine}>
                  <Text style={styles.summaryStrong}>
                    {data.solved_count}/{data.member_count}
                  </Text>{' '}
                  öğrenci çözdü · {data.question_count} soru
                </Text>
              </Card>

              <View style={styles.list}>
                {data.items.map((it) => {
                  const ratio = it.solved && it.total ? (it.score ?? 0) / it.total : 0;
                  const openDetail = () =>
                    router.push(
                      `/student-attempt?aid=${encodeURIComponent(id)}&sid=${encodeURIComponent(it.student_tenant_id)}&name=${encodeURIComponent(it.display_name)}` as Href,
                    );
                  return (
                    <Pressable
                      key={it.student_tenant_id}
                      disabled={!it.solved}
                      onPress={openDetail}
                      style={({ pressed }) => [styles.row, pressed && it.solved && styles.pressed]}
                    >
                      <View style={styles.avatar}>
                        <Text style={styles.initial}>
                          {(it.display_name || '?').charAt(0).toUpperCase()}
                        </Text>
                      </View>
                      <Text style={styles.name} numberOfLines={1}>
                        {it.display_name}
                      </Text>
                      {it.solved ? (
                        <>
                          <View style={[styles.scorePill, { backgroundColor: scoreTone(ratio) }]}>
                            <Text style={styles.scorePillText}>
                              {it.score}/{it.total}
                            </Text>
                          </View>
                          <IconChevron size={16} color={colors.textFaint} />
                        </>
                      ) : (
                        <View style={styles.pendingPill}>
                          <Text style={styles.pendingText}>Bekliyor</Text>
                        </View>
                      )}
                    </Pressable>
                  );
                })}
              </View>
            </>
          ) : null}
        </ScrollView>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  safe: { flex: 1 },
  content: { padding: spacing.xl, gap: spacing.lg },
  error: { color: colors.danger, fontSize: fontSize.sm, fontFamily: fonts.bodyMedium },
  summary: { gap: spacing.xs },
  title: { fontFamily: fonts.heading, fontSize: fontSize.lg, color: colors.text },
  summaryLine: { fontFamily: fonts.body, fontSize: fontSize.sm, color: colors.textMuted },
  summaryStrong: { fontFamily: fonts.bodyHeavy, color: colors.text },
  list: { gap: spacing.sm },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.lg,
    padding: spacing.md,
  },
  pressed: { opacity: 0.9, transform: [{ scale: 0.99 }] },
  avatar: { width: 36, height: 36, borderRadius: 18, backgroundColor: colors.tintBlue, alignItems: 'center', justifyContent: 'center' },
  initial: { fontFamily: fonts.bodyHeavy, fontSize: fontSize.sm, color: colors.brand },
  name: { flex: 1, fontFamily: fonts.bodyMedium, fontSize: fontSize.md, color: colors.text },
  scorePill: { borderRadius: radius.pill, paddingHorizontal: spacing.md, paddingVertical: 4 },
  scorePillText: { fontFamily: fonts.bodyHeavy, fontSize: fontSize.sm, color: '#FFFFFF' },
  pendingPill: { borderRadius: radius.pill, paddingHorizontal: spacing.md, paddingVertical: 4, backgroundColor: colors.bgTint },
  pendingText: { fontFamily: fonts.bodyBold, fontSize: fontSize.xs, color: colors.textMuted },
});
