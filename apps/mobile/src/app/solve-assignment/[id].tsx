import { useAuth } from '@clerk/expo';
import type { AttemptResult, QuizPublic, SubmittedAnswer } from '@soruatolyesi/shared';
import { Stack, useLocalSearchParams, useRouter } from 'expo-router';
import { useCallback, useEffect, useRef, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { QuestionCard, ResultView } from '@/components/solve';
import { PrimaryButton } from '@/components/ui';
import { getAssignment, submitAssignmentAttempt } from '@/lib/api';
import { colors, fonts, fontSize, spacing } from '@/theme/tokens';

export default function SolveAssignmentScreen() {
  const { userId } = useAuth();
  const { id, title } = useLocalSearchParams<{ id: string; title?: string }>();
  const router = useRouter();

  const [quiz, setQuiz] = useState<QuizPublic | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<number, SubmittedAnswer>>({});
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<AttemptResult | null>(null);
  const startRef = useRef(0);

  const load = useCallback(async () => {
    if (!userId || !id) return;
    setLoading(true);
    setError(null);
    try {
      const q = await getAssignment(id, userId);
      setQuiz(q);
      startRef.current = Date.now();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [userId, id]);

  useEffect(() => {
    void load();
  }, [load]);

  const setAnswer = useCallback((n: number, patch: Partial<SubmittedAnswer>) => {
    setAnswers((prev) => ({ ...prev, [n]: { ...prev[n], ...patch, number: n } }));
  }, []);

  const onSubmit = useCallback(async () => {
    if (!quiz || !userId || !id || busy) return;
    setBusy(true);
    setError(null);
    try {
      const payload = quiz.questions.map((q) => answers[q.number] ?? { number: q.number });
      const res = await submitAssignmentAttempt(id, {
        tenant_id: userId,
        answers: payload,
        duration_seconds: Math.round((Date.now() - startRef.current) / 1000),
      });
      setResult(res);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }, [quiz, userId, id, busy, answers]);

  return (
    <View style={styles.root}>
      <Stack.Screen
        options={{
          headerShown: true,
          title: title || quiz?.title || 'Ödev',
          headerStyle: { backgroundColor: colors.bg },
          headerShadowVisible: false,
          headerTintColor: colors.brand,
          headerTitleStyle: { fontFamily: fonts.headingSemi, color: colors.text },
        }}
      />
      <SafeAreaView style={styles.safe} edges={['bottom']}>
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          {loading ? (
            <ActivityIndicator style={{ marginTop: spacing.xl }} color={colors.brand} />
          ) : error && !quiz ? (
            <Text style={styles.error}>{error}</Text>
          ) : result ? (
            <ResultView result={result} onRestart={() => router.back()} restartLabel="Ödevlerime dön" />
          ) : quiz ? (
            <>
              {quiz.questions.map((q) => (
                <QuestionCard
                  key={q.number}
                  q={q}
                  answer={answers[q.number]}
                  onChange={(patch) => setAnswer(q.number, patch)}
                />
              ))}
              {error ? <Text style={styles.error}>{error}</Text> : null}
              <PrimaryButton label="Bitir & Gönder" color={colors.success} busy={busy} onPress={onSubmit} />
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
});
