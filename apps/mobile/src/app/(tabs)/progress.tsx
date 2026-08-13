import { useAuth, useUser } from '@clerk/expo';
import {
  SUBJECT_COLORS,
  type KazanimProgress,
  type ProgressResponse,
} from '@soruatolyesi/shared';
import { useRouter, type Href } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ChildrenView } from '@/components/children-view';
import { ClassroomsView } from '@/components/classrooms-view';
import { HexBadge, IconCalendar, IconChevron, IconFire, IconPencil, IconSpark, IconStar } from '@/components/icons';
import { Mascot } from '@/components/mascot';
import { SkeletonList } from '@/components/skeleton';
import { Card, PrimaryButton, ProgressBar, ScreenHeader } from '@/components/ui';
import { getGamification, getProgress, type GamificationResponse } from '@/lib/api';
import { badgeGlyph, badgeVariant, computeBadges, tierLabel, type TopicBadge } from '@/lib/badges';
import { effectiveRole } from '@/lib/roles';
import { colors, fonts, fontSize, radius, shadow, spacing } from '@/theme/tokens';

function pct(v: number): number {
  return Math.round((v <= 1 ? v : v / 100) * 100);
}

function levelTitle(level: number): string {
  if (level <= 1) return 'Acemi';
  if (level <= 3) return 'Çırak';
  if (level <= 5) return 'Kalfa';
  if (level <= 8) return 'Usta';
  return 'Üstat';
}

/**
 * Üçüncü sekme ROLE GÖRE değişir (2026-08-13 kararı):
 *   öğrenci → kişisel gelişim panosu (aşağıdaki StudentProgress)
 *   öğretmen → Sınıfım · veli → Çocuklarım
 * Öncesinde herkese öğrencinin kişisel panosu gösteriliyordu; öğretmene kendi XP'sini
 * göstermek anlamsızdı ve sınıf yönetimi yalnız ana ekrandaki karttan ulaşılabiliyordu.
 */
export default function ProgressTab() {
  const { user } = useUser();
  const role = effectiveRole(user);

  if (role === 'teacher') {
    return (
      <View style={styles.root}>
        <SafeAreaView style={styles.safe} edges={['top']}>
          <ClassroomsView
            header={
              <ScreenHeader
                title="Sınıfım"
                subtitle="Sınıflarını yönet, ödev ata, sonuçları izle"
              />
            }
          />
        </SafeAreaView>
      </View>
    );
  }

  if (role === 'parent') {
    return (
      <View style={styles.root}>
        <SafeAreaView style={styles.safe} edges={['top']}>
          <ChildrenView
            header={
              <ScreenHeader
                title="Çocuklarım"
                subtitle="Çocuğunu ekle, gelişimini takip et"
              />
            }
          />
        </SafeAreaView>
      </View>
    );
  }

  return <StudentProgress />;
}

function StudentProgress() {
  const { userId } = useAuth();
  const router = useRouter();
  const [data, setData] = useState<ProgressResponse | null>(null);
  const [game, setGame] = useState<GamificationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    setError(null);
    try {
      const [p, g] = await Promise.all([
        getProgress(userId),
        getGamification(userId).catch(() => null), // gamification opsiyonel (401→gizle)
      ]);
      setData(p);
      setGame(g);
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
  const badges = data ? computeBadges(data.mastery) : [];
  const trend = (data?.daily_trend ?? []).filter((d) => d.attempts > 0).slice(-14);

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
              {/* Gamification hero — seviye / XP / seri */}
              {game ? <GamificationHero g={game} /> : null}

              {/* Özet stat kartları */}
              <View style={styles.statGrid}>
                <StatCard bg={colors.tintBlue} accent={colors.brand} value={summary.quizzes_solved} label="Çözülen" />
                <StatCard bg={colors.tintGreen} accent={colors.success} value={summary.total_answered} label="Toplam soru" />
                <StatCard bg={colors.tintYellow} accent={colors.onTintYellow} value={`%${pct(summary.accuracy)}`} label="Doğruluk" />
                <StatCard bg={colors.tintPurple} accent={colors.magic} value={summary.kazanim_count} label="Kazanım" />
              </View>

              {/* Doğru / yanlış kırılımı */}
              <CorrectWrongBar correct={summary.total_correct} total={summary.total_answered} />

              {/* 14 günlük trend */}
              {trend.length >= 2 ? <TrendCard trend={trend} /> : null}

              {/* Rozetler */}
              {badges.length > 0 ? <BadgesCard badges={badges} /> : null}

              {/* Çalışma programı girişi */}
              <Pressable
                style={({ pressed }) => [styles.linkCard, styles.planCard, pressed && styles.linkPressed]}
                onPress={() => router.push('/study-plan' as Href)}
              >
                <View style={[styles.linkIcon, { backgroundColor: colors.tintPurple }]}>
                  <IconSpark size={26} />
                </View>
                <View style={styles.linkBody}>
                  <Text style={styles.linkTitle}>Çalışma programım</Text>
                  <Text style={styles.linkSub}>Eksiklerine göre haftalık plan</Text>
                </View>
                <IconChevron size={18} color={colors.textFaint} />
              </Pressable>

              {/* Deneme geçmişi */}
              <Pressable
                style={({ pressed }) => [styles.linkCard, pressed && styles.linkPressed]}
                onPress={() => router.push('/history' as Href)}
              >
                <View style={[styles.linkIcon, { backgroundColor: colors.tintYellow }]}>
                  <IconCalendar size={26} />
                </View>
                <View style={styles.linkBody}>
                  <Text style={styles.linkTitle}>Geçmişim</Text>
                  <Text style={styles.linkSub}>Çözdüğün quizler ve ürettiğin kağıtlar</Text>
                </View>
                <IconChevron size={18} color={colors.textFaint} />
              </Pressable>

              {/* Paylaşımlarım */}
              <Pressable
                style={({ pressed }) => [styles.linkCard, pressed && styles.linkPressed]}
                onPress={() => router.push('/shares' as Href)}
              >
                <View style={[styles.linkIcon, { backgroundColor: colors.tintGreen }]}>
                  <IconSpark size={26} />
                </View>
                <View style={styles.linkBody}>
                  <Text style={styles.linkTitle}>Paylaşımlarım</Text>
                  <Text style={styles.linkSub}>Paylaştığın testleri kimler çözdü?</Text>
                </View>
                <IconChevron size={18} color={colors.textFaint} />
              </Pressable>

              {/* Geliştirilecek kazanımlar (zayıf) — "tüm kazanımlar" kaldırıldı */}
              {data.weak.length > 0 && (
                <Card>
                  <Text style={styles.sectionTitle}>Geliştirilecek kazanımlar</Text>
                  <Text style={styles.sectionHint}>Önce bunları kapatalım</Text>
                  <View style={styles.kList}>
                    {data.weak.slice(0, 8).map((k) => (
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

function GamificationHero({ g }: { g: GamificationResponse }) {
  const toNext = g.xp_for_next > 0 ? g.xp_in_level / g.xp_for_next : 0;
  return (
    <Card floating style={styles.hero}>
      <View style={styles.heroTop}>
        <View style={styles.levelRing}>
          <IconStar size={30} />
          <Text style={styles.levelNo}>{g.level}</Text>
        </View>
        <View style={styles.heroInfo}>
          <Text style={styles.heroLevel}>Seviye {g.level} · {levelTitle(g.level)}</Text>
          <View style={styles.streakRow}>
            <IconFire size={18} />
            <Text style={styles.streakText}>{g.streak_current} gün seri</Text>
          </View>
        </View>
        <View style={styles.xpPill}>
          <Text style={styles.xpValue}>{g.xp}</Text>
          <Text style={styles.xpLabel}>XP</Text>
        </View>
      </View>
      <ProgressBar progress={toNext} color={colors.reward} height={10} />
      <Text style={styles.xpToNext}>
        Sonraki seviyeye {Math.max(0, g.xp_for_next - g.xp_in_level)} XP
      </Text>
    </Card>
  );
}

function CorrectWrongBar({ correct, total }: { correct: number; total: number }) {
  const wrong = Math.max(0, total - correct);
  const cPct = total > 0 ? (correct / total) * 100 : 0;
  return (
    <Card>
      <Text style={styles.sectionTitle}>Doğru & Yanlış</Text>
      <View style={styles.cwBar}>
        <View style={[styles.cwFill, { flex: correct || 0.001, backgroundColor: colors.success }]} />
        <View style={[styles.cwFill, { flex: wrong || 0.001, backgroundColor: colors.danger }]} />
      </View>
      <View style={styles.cwLegend}>
        <Text style={[styles.cwText, { color: colors.success }]}>✓ {correct} doğru</Text>
        <Text style={styles.cwPct}>%{Math.round(cPct)}</Text>
        <Text style={[styles.cwText, { color: colors.danger }]}>{wrong} yanlış</Text>
      </View>
    </Card>
  );
}

function TrendCard({ trend }: { trend: { date: string; ratio: number }[] }) {
  return (
    <Card>
      <Text style={styles.sectionTitle}>Son günler</Text>
      <View style={styles.trendRow}>
        {trend.map((d, i) => {
          const h = 8 + Math.round((d.ratio <= 1 ? d.ratio : d.ratio / 100) * 56);
          const color = d.ratio >= 0.7 ? colors.success : d.ratio >= 0.4 ? colors.reward : colors.danger;
          return <View key={i} style={[styles.trendBar, { height: h, backgroundColor: color }]} />;
        })}
      </View>
      <Text style={styles.sectionHint}>Günlük doğruluk (son {trend.length} gün)</Text>
    </Card>
  );
}

function BadgesCard({ badges }: { badges: TopicBadge[] }) {
  return (
    <Card>
      <Text style={styles.sectionTitle}>Rozetlerim</Text>
      <Text style={styles.sectionHint}>{badges.length} rozet kazandın</Text>
      <View style={styles.badgeGrid}>
        {badges.slice(0, 12).map((b, i) => (
          <View key={i} style={styles.badge}>
            <HexBadge size={58} glyph={badgeGlyph(b.tier)} variant={badgeVariant(b.tier)} />
            <Text style={styles.badgeName} numberOfLines={1}>
              {b.topicName}
            </Text>
            <Text style={styles.badgeTier}>{tierLabel(b.tier)}</Text>
          </View>
        ))}
      </View>
    </Card>
  );
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

function StatCard({ bg, accent, value, label }: { bg: string; accent: string; value: number | string; label: string }) {
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
  content: { padding: spacing.xl, gap: spacing.lg, paddingBottom: 120 },
  error: { color: colors.danger, fontSize: fontSize.sm, fontFamily: fonts.bodyMedium },
  sectionTitle: { fontSize: fontSize.lg, fontFamily: fonts.heading, color: colors.text },
  sectionHint: { fontSize: fontSize.xs, fontFamily: fonts.body, color: colors.textMuted, marginTop: 1 },

  // Hero
  hero: { gap: spacing.md },
  heroTop: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  levelRing: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.tintYellow,
    alignItems: 'center',
    justifyContent: 'center',
  },
  levelNo: { position: 'absolute', fontFamily: fonts.heading, fontSize: fontSize.sm, color: colors.rewardDark, marginTop: 20 },
  heroInfo: { flex: 1, gap: 4 },
  heroLevel: { fontFamily: fonts.heading, fontSize: fontSize.md, color: colors.text },
  streakRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  streakText: { fontFamily: fonts.bodyMedium, fontSize: fontSize.sm, color: colors.energy },
  xpPill: { alignItems: 'center', backgroundColor: colors.tintPurple, borderRadius: radius.md, paddingHorizontal: spacing.md, paddingVertical: 6 },
  xpValue: { fontFamily: fonts.heading, fontSize: fontSize.md, color: colors.magic },
  xpLabel: { fontFamily: fonts.body, fontSize: 10, color: colors.textMuted },
  xpToNext: { fontFamily: fonts.body, fontSize: fontSize.xs, color: colors.textMuted },

  statGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md },
  stat: { flexGrow: 1, flexBasis: '45%', borderRadius: radius.card, padding: spacing.lg, ...shadow.card },
  statValue: { fontSize: fontSize.xxl, fontFamily: fonts.heading },
  statLabel: { fontSize: fontSize.sm, color: colors.textMuted, fontFamily: fonts.bodyMedium, marginTop: 2 },

  // Doğru/yanlış
  cwBar: { flexDirection: 'row', height: 16, borderRadius: 8, overflow: 'hidden', marginTop: spacing.md, gap: 2 },
  cwFill: { borderRadius: 8 },
  cwLegend: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: spacing.sm },
  cwText: { fontFamily: fonts.bodyBold, fontSize: fontSize.sm },
  cwPct: { fontFamily: fonts.heading, fontSize: fontSize.md, color: colors.text },

  // Trend
  trendRow: { flexDirection: 'row', alignItems: 'flex-end', gap: 4, height: 68, marginTop: spacing.md },
  trendBar: { flex: 1, borderRadius: 3, minHeight: 8 },

  // Rozetler
  badgeGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md, marginTop: spacing.md },
  badge: { width: 72, alignItems: 'center', gap: 2 },
  badgeName: { fontFamily: fonts.bodyMedium, fontSize: 10, color: colors.text, textAlign: 'center' },
  badgeTier: { fontFamily: fonts.body, fontSize: 9, color: colors.textMuted },

  // Link kartları
  linkCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    borderRadius: radius.card,
    backgroundColor: colors.surface,
    padding: spacing.lg,
    ...shadow.card,
  },
  planCard: {},
  linkPressed: { transform: [{ scale: 0.99 }], opacity: 0.92 },
  linkIcon: { width: 48, height: 48, borderRadius: radius.md, alignItems: 'center', justifyContent: 'center' },
  linkBody: { flex: 1 },
  linkTitle: { fontSize: fontSize.md, fontFamily: fonts.heading, color: colors.text },
  linkSub: { fontSize: fontSize.xs, fontFamily: fonts.body, color: colors.textMuted, marginTop: 1 },

  kList: { gap: spacing.md, marginTop: spacing.md },
  kRow: { gap: spacing.xs },
  kHead: { flexDirection: 'row', justifyContent: 'space-between', gap: spacing.sm },
  kName: { flex: 1, color: colors.text, fontSize: fontSize.sm, fontFamily: fonts.bodyMedium },
  kCount: { color: colors.textMuted, fontSize: fontSize.sm, fontFamily: fonts.bodyBold },

  emptyCard: { gap: spacing.md, alignItems: 'center', paddingVertical: spacing.xl },
  emptyText: { color: colors.textMuted, fontSize: fontSize.md, fontFamily: fonts.body },
});
