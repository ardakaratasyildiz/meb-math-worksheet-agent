import { useAuth } from '@clerk/expo';
import { Stack, useRouter, type Href } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { IconSpark } from '@/components/icons';
import { Mascot } from '@/components/mascot';
import { Card, PrimaryButton } from '@/components/ui';
import { SkeletonList } from '@/components/skeleton';
import { createStudyPlan, getStudyPlan, type StudyPlanDay, type StudyPlanResponse } from '@/lib/api';
import { colors, fonts, fontSize, radius, spacing } from '@/theme/tokens';

const headerOpts = {
  headerShown: true,
  title: 'Çalışma Programım',
  headerStyle: { backgroundColor: colors.bg },
  headerShadowVisible: false,
  headerTintColor: colors.brand,
  headerTitleStyle: { fontFamily: fonts.headingSemi, color: colors.text },
} as const;

/** Gün türü → etiket + renk (focus=eksik, review=tekrar, mixed=karışık). */
function kindMeta(kind: string): { label: string; color: string; tint: string } {
  if (kind === 'review') return { label: 'Tekrar', color: colors.brand, tint: colors.tintBlue };
  if (kind === 'mixed') return { label: 'Karışık', color: colors.magic, tint: colors.tintPurple };
  return { label: 'Eksik', color: colors.energy, tint: colors.tintOrange };
}

export default function StudyPlanScreen() {
  const { userId } = useAuth();
  const router = useRouter();
  const [plan, setPlan] = useState<StudyPlanResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    setError(null);
    try {
      setPlan(await getStudyPlan(userId));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    void load();
  }, [load]);

  const generate = useCallback(async () => {
    if (!userId || generating) return;
    setGenerating(true);
    setError(null);
    try {
      setPlan(await createStudyPlan(userId));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setGenerating(false);
    }
  }, [userId, generating]);

  const hasPlan = !!plan && plan.days.length > 0;

  return (
    <View style={styles.root}>
      <Stack.Screen options={headerOpts} />
      <SafeAreaView style={styles.safe} edges={['bottom']}>
        <ScrollView contentContainerStyle={styles.content}>
          {loading ? (
            <SkeletonList count={4} />
          ) : error ? (
            <Card style={styles.center}>
              <Text style={styles.error}>{error}</Text>
              <PrimaryButton label="Tekrar dene" variant="soft" onPress={() => void load()} />
            </Card>
          ) : hasPlan ? (
            <>
              <Card floating style={styles.hero}>
                <Mascot variant="reading" size={64} />
                <View style={styles.heroText}>
                  <Text style={styles.heroTitle}>Bu haftanın planı</Text>
                  <Text style={styles.heroSummary}>{plan!.summary}</Text>
                </View>
              </Card>

              {plan!.days.map((d) => (
                <DayCard key={d.day_no} day={d} onSolve={() => router.push('/create' as Href)} />
              ))}

              <PrimaryButton
                label="Programı yenile"
                variant="soft"
                busy={generating}
                onPress={() => void generate()}
                icon={<IconSpark size={18} />}
              />
              <Text style={styles.note}>
                Program eksik kazanımlarına göre hazırlanır; çözdükçe güncellenir.
              </Text>
            </>
          ) : (
            <Card style={styles.center}>
              <Mascot variant="happy" size={112} />
              <Text style={styles.emptyTitle}>Sana özel haftalık plan</Text>
              <Text style={styles.emptyText}>
                Eksik kazanımlarına göre 7 günlük çalışma programı oluşturalım.
              </Text>
              <PrimaryButton
                label="Programımı oluştur"
                color={colors.magic}
                busy={generating}
                onPress={() => void generate()}
                icon={<IconSpark size={20} />}
              />
            </Card>
          )}
        </ScrollView>
      </SafeAreaView>
    </View>
  );
}

function DayCard({ day, onSolve }: { day: StudyPlanDay; onSolve: () => void }) {
  const meta = kindMeta(day.kind);
  return (
    <Card style={styles.day}>
      <View style={styles.dayHead}>
        <View style={styles.dayNo}>
          <Text style={styles.dayNoText}>{day.day_no}</Text>
        </View>
        <View style={styles.dayHeadText}>
          <Text style={styles.dayWeekday}>{day.weekday || `${day.day_no}. gün`}</Text>
          <Text style={styles.dayTitle} numberOfLines={2}>
            {day.title}
          </Text>
        </View>
        <View style={[styles.kindPill, { backgroundColor: meta.tint }]}>
          <Text style={[styles.kindText, { color: meta.color }]}>{meta.label}</Text>
        </View>
      </View>

      {day.topic_name ? <Text style={styles.dayTopic}>{day.topic_name}</Text> : null}
      {day.tip ? <Text style={styles.dayTip}>💡 {day.tip}</Text> : null}

      <View style={styles.dayFoot}>
        <Text style={styles.dayCount}>{day.question_count} soru</Text>
        <PrimaryButton label="Çöz" variant="soft" color={meta.color} onPress={onSolve} />
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  safe: { flex: 1 },
  content: { padding: spacing.xl, gap: spacing.lg, paddingBottom: spacing.xxl },
  center: { alignItems: 'center', gap: spacing.md, paddingVertical: spacing.xl },
  error: { color: colors.danger, fontSize: fontSize.sm, fontFamily: fonts.bodyMedium, textAlign: 'center' },
  note: { fontFamily: fonts.body, fontSize: fontSize.xs, color: colors.textMuted, textAlign: 'center' },

  hero: { flexDirection: 'row', alignItems: 'center', gap: spacing.lg, backgroundColor: colors.tintPurple },
  heroText: { flex: 1, gap: 2 },
  heroTitle: { fontFamily: fonts.heading, fontSize: fontSize.lg, color: colors.text },
  heroSummary: { fontFamily: fonts.body, fontSize: fontSize.sm, color: colors.textMuted },

  emptyTitle: { fontFamily: fonts.heading, fontSize: fontSize.xl, color: colors.text },
  emptyText: { fontFamily: fonts.body, fontSize: fontSize.sm, color: colors.textMuted, textAlign: 'center' },

  day: { gap: spacing.sm },
  dayHead: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  dayNo: {
    width: 36,
    height: 36,
    borderRadius: radius.md,
    backgroundColor: colors.tintBlue,
    alignItems: 'center',
    justifyContent: 'center',
  },
  dayNoText: { fontFamily: fonts.heading, fontSize: fontSize.md, color: colors.brand },
  dayHeadText: { flex: 1 },
  dayWeekday: { fontFamily: fonts.bodyBold, fontSize: fontSize.xs, color: colors.textMuted },
  dayTitle: { fontFamily: fonts.heading, fontSize: fontSize.md, color: colors.text },
  kindPill: { borderRadius: radius.pill, paddingHorizontal: spacing.md, paddingVertical: 4 },
  kindText: { fontFamily: fonts.bodyBold, fontSize: fontSize.xs },
  dayTopic: { fontFamily: fonts.bodyMedium, fontSize: fontSize.sm, color: colors.text },
  dayTip: { fontFamily: fonts.body, fontSize: fontSize.sm, color: colors.textMuted },
  dayFoot: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: spacing.xs },
  dayCount: { fontFamily: fonts.bodyBold, fontSize: fontSize.sm, color: colors.textMuted },
});
