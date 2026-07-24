import { useAuth, useUser } from '@clerk/expo';
import { useRouter } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { Linking, Pressable, ScrollView, StyleSheet, Switch, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { IconChevron, IconFire, IconSpark, IconStar } from '@/components/icons';
import { Mascot } from '@/components/mascot';
import { Card, PrimaryButton, ScreenHeader } from '@/components/ui';
import { useEntitlements } from '@/hooks/useEntitlements';
import { getGamification, getParentCode, type GamificationResponse } from '@/lib/api';
import { effectiveRole, isPlayfulRole, roleLabel } from '@/lib/roles';
import { colors, fonts, fontSize, radius, shadow, spacing } from '@/theme/tokens';

/** Plan kodu → görünen ad. */
const PLAN_LABEL: Record<string, string> = {
  free: 'Ücretsiz',
  trial: 'Deneme (Pro+)',
  pro: 'Pro',
  'pro-plus': 'Pro+',
};

const DEMO: GamificationResponse = {
  xp: 120,
  level: 3,
  xp_in_level: 20,
  xp_for_next: 50,
  streak_current: 5,
  streak_longest: 5,
  total_active_days: 12,
};

function levelTitle(level: number): string {
  if (level <= 1) return 'Acemi';
  if (level <= 3) return 'Çırak';
  if (level <= 5) return 'Kalfa';
  if (level <= 8) return 'Usta';
  return 'Üstat';
}

const SITE = 'https://soruatolyesi.com';

export default function ProfileScreen() {
  const { userId, signOut } = useAuth();
  const { user } = useUser();
  const router = useRouter();
  const { entitlements } = useEntitlements();
  const [game, setGame] = useState<GamificationResponse | null>(null);
  const [notify, setNotify] = useState(true);
  const [parentCode, setParentCode] = useState<string | null>(null);
  const [codeBusy, setCodeBusy] = useState(false);
  const [codeError, setCodeError] = useState(false);

  useEffect(() => {
    if (!userId) return;
    getGamification(userId)
      .then(setGame)
      .catch(() => setGame(null));
  }, [userId]);

  const g = game ?? DEMO;
  const role = effectiveRole(user);
  const playful = isPlayfulRole(role);
  const name = user?.firstName ?? user?.username ?? 'Kullanıcı';
  const email = user?.primaryEmailAddress?.emailAddress ?? '';
  const initial = name.charAt(0).toUpperCase();

  const open = useCallback((path: string) => () => void Linking.openURL(`${SITE}${path}`), []);

  const revealCode = useCallback(async () => {
    if (!userId || codeBusy) return;
    setCodeBusy(true);
    setCodeError(false);
    try {
      setParentCode(await getParentCode(userId));
    } catch {
      setCodeError(true);
    } finally {
      setCodeBusy(false);
    }
  }, [userId, codeBusy]);

  return (
    <View style={styles.root}>
      <SafeAreaView style={styles.safe} edges={['top']}>
        <ScrollView contentContainerStyle={styles.content}>
          <ScreenHeader title="Profil" subtitle="Hesabın ve ayarların" />

          {/* Hero: maskot avatar + ad + rol */}
          <Card style={styles.hero}>
            <View style={styles.avatar}>
              {playful ? (
                <Mascot variant="happy" size={64} animated={false} />
              ) : (
                <Text style={styles.avatarInitial}>{initial}</Text>
              )}
            </View>
            <View style={styles.heroBody}>
              <Text style={styles.heroName} numberOfLines={1}>
                {name}
              </Text>
              {email ? (
                <Text style={styles.heroEmail} numberOfLines={1}>
                  {email}
                </Text>
              ) : null}
              {role ? (
                <View style={styles.roleBadge}>
                  <Text style={styles.roleBadgeText}>{roleLabel(role)}</Text>
                </View>
              ) : null}
            </View>
          </Card>

          {/* Gamification özeti — yalnız öğrenci (yetişkinde oyunlaşma yok) */}
          {playful ? (
            <View style={styles.statRow}>
              <MiniStat icon={<IconStar size={24} />} value={`Sv. ${g.level}`} label={levelTitle(g.level)} />
              <MiniStat icon={<IconSpark size={22} />} value={`${g.xp}`} label="XP" />
              <MiniStat icon={<IconFire size={24} />} value={`${g.streak_current}`} label="gün seri" />
            </View>
          ) : null}

          {/* Veli takip kodu — yalnız öğrenci (veliye verilir) */}
          {playful ? (
            <Card>
              <Text style={styles.codeTitle}>Veli takip kodu</Text>
              <Text style={styles.codeHint}>Velin bu kodla seni ekleyip gelişimini görebilir.</Text>
              {parentCode ? (
                <Text style={styles.parentCode}>{parentCode}</Text>
              ) : codeError ? (
                <Text style={styles.codeErr}>Kod alınamadı. Bağlantını kontrol edip tekrar dene.</Text>
              ) : null}
              {!parentCode ? (
                <PrimaryButton
                  label={codeError ? 'Tekrar dene' : 'Kodu göster'}
                  variant="soft"
                  busy={codeBusy}
                  onPress={revealCode}
                />
              ) : null}
            </Card>
          ) : null}

          {/* Abonelik */}
          <Card>
            <Text style={styles.cardTitle}>Abonelik</Text>
            <View style={styles.planRow}>
              <View style={styles.planInfo}>
                <Text style={styles.planName}>{PLAN_LABEL[entitlements.plan] ?? 'Ücretsiz'}</Text>
                <Text style={styles.planSub}>
                  {entitlements.quota.limit !== null
                    ? `${entitlements.quota.used}/${entitlements.quota.limit} kağıt · bu ay`
                    : 'Sınırsız · fair-use'}
                </Text>
              </View>
              {entitlements.is_premium ? (
                <View style={styles.planPill}>
                  <Text style={styles.planPillText}>Aktif</Text>
                </View>
              ) : null}
            </View>
            <PrimaryButton
              label={entitlements.is_premium ? 'Planı yönet' : 'Premium’a yükselt'}
              variant={entitlements.is_premium ? 'soft' : 'solid'}
              color={colors.magic}
              onPress={() => router.push('/paywall')}
            />
          </Card>

          {/* Ayarlar */}
          <Card style={styles.listCard}>
            <View style={styles.settingRow}>
              <Text style={styles.settingLabel}>Bildirimler</Text>
              <Switch
                value={notify}
                onValueChange={setNotify}
                trackColor={{ true: colors.brand, false: colors.track }}
                thumbColor="#FFFFFF"
              />
            </View>
            <View style={styles.divider} />
            <LinkRow label="Gizlilik & KVKK" onPress={open('/gizlilik')} />
            <View style={styles.divider} />
            <LinkRow label="Kullanım Koşulları" onPress={open('/kosullar')} />
            <View style={styles.divider} />
            <LinkRow label="Yardım & İletişim" onPress={open('/iletisim')} />
          </Card>

          <PrimaryButton label="Çıkış Yap" variant="soft" color={colors.danger} onPress={() => void signOut()} />

          <Text style={styles.version}>Soru Atölyesi · sürüm 1.0.0</Text>
        </ScrollView>
      </SafeAreaView>
    </View>
  );
}

function MiniStat({ icon, value, label }: { icon: React.ReactNode; value: string; label: string }) {
  return (
    <View style={styles.miniStat}>
      {icon}
      <Text style={styles.miniValue}>{value}</Text>
      <Text style={styles.miniLabel}>{label}</Text>
    </View>
  );
}

function LinkRow({ label, onPress }: { label: string; onPress: () => void }) {
  return (
    <Pressable onPress={onPress} style={({ pressed }) => [styles.linkRow, pressed && styles.pressed]}>
      <Text style={styles.linkLabel}>{label}</Text>
      <IconChevron size={16} color={colors.textFaint} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  safe: { flex: 1 },
  content: { padding: spacing.xl, gap: spacing.lg, paddingBottom: 120 }, // yüzen tab bar payı
  cardTitle: { fontSize: fontSize.lg, fontFamily: fonts.heading, color: colors.text, marginBottom: spacing.md },
  pressed: { opacity: 0.6 },

  hero: { flexDirection: 'row', alignItems: 'center', gap: spacing.lg },
  avatar: {
    width: 76,
    height: 76,
    borderRadius: 38,
    backgroundColor: colors.tintOrange,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  avatarInitial: { fontFamily: fonts.bodyHeavy, fontSize: 30, color: colors.brand },
  heroBody: { flex: 1, gap: 2 },
  heroName: { fontFamily: fonts.heading, fontSize: fontSize.xl, color: colors.text },
  heroEmail: { fontFamily: fonts.body, fontSize: fontSize.sm, color: colors.textMuted },
  roleBadge: {
    alignSelf: 'flex-start',
    backgroundColor: colors.tintBlue,
    borderRadius: radius.pill,
    paddingHorizontal: spacing.md,
    paddingVertical: 4,
    marginTop: spacing.xs,
  },
  roleBadgeText: { fontFamily: fonts.bodyBold, fontSize: fontSize.xs, color: colors.brand },

  statRow: { flexDirection: 'row', gap: spacing.md },
  miniStat: {
    flex: 1,
    alignItems: 'center',
    gap: 4,
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    paddingVertical: spacing.lg,
    ...shadow.card,
  },
  miniValue: { fontFamily: fonts.heading, fontSize: fontSize.md, color: colors.text },
  miniLabel: { fontFamily: fonts.body, fontSize: fontSize.xs, color: colors.textMuted },

  planRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: spacing.lg },
  planInfo: { flex: 1 },
  planName: { fontFamily: fonts.bodyHeavy, fontSize: fontSize.md, color: colors.text },
  planSub: { fontFamily: fonts.body, fontSize: fontSize.xs, color: colors.textMuted, marginTop: 1 },
  planPill: { backgroundColor: colors.tintGreen, borderRadius: radius.pill, paddingHorizontal: spacing.md, paddingVertical: 5 },
  planPillText: { fontFamily: fonts.bodyBold, fontSize: fontSize.xs, color: colors.success },

  codeTitle: { fontFamily: fonts.heading, fontSize: fontSize.lg, color: colors.text },
  codeHint: { fontFamily: fonts.body, fontSize: fontSize.sm, color: colors.textMuted, marginTop: 2, marginBottom: spacing.md },
  parentCode: { fontFamily: fonts.heading, fontSize: 34, color: colors.brand, letterSpacing: 4, textAlign: 'center', marginVertical: spacing.sm },
  codeErr: { fontFamily: fonts.bodyMedium, fontSize: fontSize.sm, color: colors.danger, marginBottom: spacing.sm },

  listCard: { paddingVertical: spacing.xs },
  settingRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: spacing.md },
  settingLabel: { fontFamily: fonts.bodyMedium, fontSize: fontSize.md, color: colors.text },
  divider: { height: 1, backgroundColor: colors.border },
  linkRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: spacing.md },
  linkLabel: { fontFamily: fonts.bodyMedium, fontSize: fontSize.md, color: colors.text },

  version: { fontFamily: fonts.body, fontSize: fontSize.xs, color: colors.textFaint, textAlign: 'center', marginTop: spacing.sm },
});
