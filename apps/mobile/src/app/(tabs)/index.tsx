import { useAuth, useUser } from '@clerk/expo';
import { useRouter, type Href } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Mascot } from '@/components/mascot';
import { getGamification, pingHealth, type GamificationResponse } from '@/lib/api';
import { colors, fonts, fontSize, radius, spacing } from '@/theme/tokens';

// Auth + rol kapısı (tabs)/_layout'ta → bu ekran yalnız girişli + rollü kullanıcıya render olur.
export default function HomeScreen() {
  const { userId, signOut } = useAuth();
  const { user } = useUser();
  const router = useRouter();
  const [game, setGame] = useState<GamificationResponse | null>(null);

  const load = useCallback(async () => {
    if (!userId) return;
    try {
      setGame(await getGamification(userId));
    } catch {
      setGame(null); // dev'de 401 olabilir → ödül şeridini sessizce gizle
    }
  }, [userId]);

  useEffect(() => {
    pingHealth();
    void load();
  }, [load]);

  const firstName = user?.firstName;

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <View style={styles.headerText}>
            <Text style={styles.hello}>Merhaba{firstName ? `, ${firstName}` : ''} 👋</Text>
            {game ? (
              <View style={styles.rewardStrip}>
                <Text style={styles.reward}>🔥 {game.streak_current} günlük seri</Text>
                <Text style={styles.rewardDot}>·</Text>
                <Text style={styles.reward}>Seviye {game.level}</Text>
                <Text style={styles.rewardDot}>·</Text>
                <Text style={styles.reward}>{game.xp} XP</Text>
              </View>
            ) : null}
          </View>
          <Mascot size={92} />
        </View>

        <Text style={styles.question}>Bugün ne çalışacaksın?</Text>

        <BigTile
          emoji="📄"
          title="Çalışma Kağıdı"
          subtitle="Üret · PDF · WhatsApp'tan paylaş"
          accent={colors.brand}
          onPress={() => router.push('/worksheet' as Href)}
        />
        <BigTile
          emoji="✏️"
          title="Alıştırma Çöz"
          subtitle="Çöz · puanla · eksiğini gör"
          accent={colors.success}
          onPress={() => router.push('/practice' as Href)}
        />

        <Pressable style={styles.signout} onPress={() => void signOut()}>
          <Text style={styles.signoutText}>Çıkış Yap</Text>
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

function BigTile({
  emoji,
  title,
  subtitle,
  accent,
  onPress,
}: {
  emoji: string;
  title: string;
  subtitle: string;
  accent: string;
  onPress: () => void;
}) {
  return (
    <Pressable style={[styles.tile, { backgroundColor: accent }]} onPress={onPress}>
      <Text style={styles.tileEmoji}>{emoji}</Text>
      <View style={styles.tileTextWrap}>
        <Text style={styles.tileTitle}>{title}</Text>
        <Text style={styles.tileSub}>{subtitle}</Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  content: { padding: spacing.xl, gap: spacing.lg },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
  },
  headerText: { flex: 1, gap: spacing.sm },
  hello: {
    fontSize: fontSize.xxl,
    fontFamily: fonts.heading,
    color: colors.text,
  },
  rewardStrip: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  reward: { fontSize: fontSize.sm, fontFamily: fonts.bodyMedium, color: colors.textMuted },
  rewardDot: { color: colors.border },
  question: {
    fontSize: fontSize.lg,
    fontFamily: fonts.headingSemi,
    color: colors.text,
    marginTop: spacing.sm,
  },
  tile: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.lg,
    borderRadius: radius.xl,
    padding: spacing.xl,
  },
  tileEmoji: { fontSize: 34 },
  tileTextWrap: { flex: 1 },
  tileTitle: {
    fontSize: fontSize.lg,
    fontFamily: fonts.heading,
    color: colors.onBrand,
  },
  tileSub: {
    fontSize: fontSize.sm,
    fontFamily: fonts.body,
    color: colors.onBrand,
    opacity: 0.9,
    marginTop: 2,
  },
  signout: { alignItems: 'center', paddingVertical: spacing.md },
  signoutText: {
    color: colors.textMuted,
    fontFamily: fonts.bodyMedium,
  },
});
