import { useAuth, useUser } from '@clerk/expo';
import { useRouter, type Href } from 'expo-router';
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

import { SignInForm } from '@/components/sign-in-form';
import { getGamification, pingHealth, type GamificationResponse } from '@/lib/api';
import { colors, fontSize, fontWeight, radius, spacing } from '@/theme/tokens';

export default function HomeScreen() {
  const { isLoaded, isSignedIn } = useAuth();

  if (!isLoaded) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" />
      </View>
    );
  }
  if (!isSignedIn) return <SignInForm />;
  return <AuthedHome />;
}

function AuthedHome() {
  const { userId, signOut } = useAuth();
  const { user } = useUser();
  const router = useRouter();
  const [data, setData] = useState<GamificationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    setError(null);
    try {
      setData(await getGamification(userId));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    pingHealth();
    void load();
  }, [load]);

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.hello}>
          Merhaba{user?.firstName ? `, ${user.firstName}` : ''} 👋
        </Text>
        <Text style={styles.email}>
          {user?.primaryEmailAddress?.emailAddress ?? userId}
        </Text>

        <Pressable style={styles.primaryBtn} onPress={() => router.push('/worksheet' as Href)}>
          <Text style={styles.primaryBtnText}>📄 Çalışma Kağıdı Oluştur</Text>
        </Pressable>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>Backend · /api/me/gamification</Text>
          {loading ? (
            <ActivityIndicator />
          ) : error ? (
            <Text style={styles.error}>{error}</Text>
          ) : data ? (
            <View style={styles.stats}>
              <Stat label="XP" value={data.xp} />
              <Stat label="Seviye" value={data.level} />
              <Stat label="Seri" value={data.streak_current} />
              <Stat label="En uzun" value={data.streak_longest} />
              <Stat label="Aktif gün" value={data.total_active_days} />
            </View>
          ) : null}
          <Pressable style={styles.secondary} onPress={() => void load()}>
            <Text style={styles.secondaryText}>Yenile</Text>
          </Pressable>
        </View>

        <Pressable style={styles.signout} onPress={() => void signOut()}>
          <Text style={styles.signoutText}>Çıkış Yap</Text>
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <View style={styles.stat}>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.bg },
  safe: { flex: 1, backgroundColor: colors.bg },
  content: { padding: spacing.xl, gap: spacing.md },
  primaryBtn: {
    backgroundColor: colors.brand,
    borderRadius: radius.md,
    paddingVertical: spacing.lg,
    alignItems: 'center',
    marginTop: spacing.sm,
  },
  primaryBtnText: { color: colors.onBrand, fontSize: fontSize.md, fontWeight: fontWeight.bold },
  hello: { fontSize: fontSize.xl, fontWeight: fontWeight.heavy, marginTop: spacing.sm, color: colors.text },
  email: { fontSize: fontSize.sm, color: colors.textMuted },
  card: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.lg,
    padding: spacing.lg,
    gap: spacing.md,
    marginTop: spacing.sm,
    backgroundColor: colors.surface,
  },
  cardTitle: { fontSize: fontSize.xs, fontWeight: fontWeight.medium, color: colors.textMuted },
  stats: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.lg },
  stat: { minWidth: 64 },
  statValue: { fontSize: fontSize.xl, fontWeight: fontWeight.heavy, color: colors.text },
  statLabel: { fontSize: fontSize.xs, color: colors.textMuted },
  error: { color: colors.danger, fontSize: fontSize.sm },
  secondary: {
    borderWidth: 1,
    borderColor: colors.brand,
    borderRadius: radius.sm,
    paddingVertical: spacing.md,
    alignItems: 'center',
  },
  secondaryText: { color: colors.brand, fontWeight: fontWeight.bold },
  signout: {
    paddingVertical: spacing.md,
    alignItems: 'center',
    marginTop: spacing.sm,
  },
  signoutText: { color: colors.danger, fontWeight: fontWeight.medium },
});
