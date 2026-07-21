import { useAuth, useUser } from '@clerk/expo';
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
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  safe: { flex: 1 },
  content: { padding: 20, gap: 12 },
  hello: { fontSize: 24, fontWeight: '800', marginTop: 8 },
  email: { fontSize: 14, opacity: 0.6 },
  card: {
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 16,
    padding: 16,
    gap: 12,
    marginTop: 8,
  },
  cardTitle: { fontSize: 13, fontWeight: '600', opacity: 0.7 },
  stats: { flexDirection: 'row', flexWrap: 'wrap', gap: 16 },
  stat: { minWidth: 64 },
  statValue: { fontSize: 22, fontWeight: '800' },
  statLabel: { fontSize: 12, opacity: 0.6 },
  error: { color: '#ef4444', fontSize: 14 },
  secondary: {
    borderWidth: 1,
    borderColor: '#208AEF',
    borderRadius: 10,
    paddingVertical: 10,
    alignItems: 'center',
  },
  secondaryText: { color: '#208AEF', fontWeight: '700' },
  signout: {
    paddingVertical: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  signoutText: { color: '#ef4444', fontWeight: '600' },
});
