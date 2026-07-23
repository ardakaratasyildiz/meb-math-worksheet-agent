import { useAuth } from '@clerk/expo';
import { Stack, useLocalSearchParams } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { AttemptDetailView } from '@/components/attempt-detail-view';
import { SkeletonList } from '@/components/skeleton';
import { getStudentAttemptDetail, type AttemptDetail } from '@/lib/api';
import { colors, fonts, fontSize, spacing } from '@/theme/tokens';

/** Öğretmen: bir öğrencinin ödevdeki denemesinin soru-soru detayı. */
export default function StudentAttemptScreen() {
  const { userId } = useAuth();
  const { aid, sid, name } = useLocalSearchParams<{ aid: string; sid: string; name?: string }>();
  const [detail, setDetail] = useState<AttemptDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!userId || !aid || !sid) return;
    setError(null);
    try {
      setDetail(await getStudentAttemptDetail(aid, sid, userId));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Deneme yüklenemedi.');
    }
  }, [userId, aid, sid]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <SafeAreaView style={styles.safe} edges={['bottom']}>
      <Stack.Screen
        options={{
          headerShown: true,
          title: name || 'Öğrenci Denemesi',
          headerStyle: { backgroundColor: colors.bg },
          headerShadowVisible: false,
          headerTintColor: colors.brand,
          headerTitleStyle: { fontFamily: fonts.headingSemi, color: colors.text },
        }}
      />
      <ScrollView contentContainerStyle={styles.content}>
        {!detail ? (
          error ? (
            <Text style={styles.error}>{error}</Text>
          ) : (
            <SkeletonList count={4} />
          )
        ) : (
          <AttemptDetailView detail={detail} answerLabel="Öğrencinin cevabı" />
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  content: { padding: spacing.xl, gap: spacing.md },
  error: {
    color: colors.danger,
    fontFamily: fonts.bodyMedium,
    fontSize: fontSize.sm,
    textAlign: 'center',
    marginTop: spacing.xl,
  },
});
