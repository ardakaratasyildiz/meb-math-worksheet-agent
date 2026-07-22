import { useAuth } from '@clerk/expo';
import type {
  AttemptResult,
  QuizPublic,
  QuizQuestionPublic,
  SubmittedAnswer,
} from '@soruatolyesi/shared';
import { useCallback, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { GeneratorSetup, type GeneratorParams } from '@/components/generator-setup';
import { Mascot } from '@/components/mascot';
import { QuestionText } from '@/components/question-text';
import { SkeletonList } from '@/components/skeleton';
import { createQuiz, submitAttempt } from '@/lib/api';
import { colors, fonts, fontSize, radius, spacing } from '@/theme/tokens';

type Step = 'setup' | 'solving' | 'result';

export default function PracticeScreen() {
  const { userId } = useAuth();
  const [step, setStep] = useState<Step>('setup');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [quiz, setQuiz] = useState<QuizPublic | null>(null);
  const [answers, setAnswers] = useState<Record<number, SubmittedAnswer>>({});
  const startRef = useRef(0);
  const [result, setResult] = useState<AttemptResult | null>(null);

  const setAnswer = useCallback((n: number, patch: Partial<SubmittedAnswer>) => {
    setAnswers((prev) => ({ ...prev, [n]: { ...prev[n], ...patch, number: n } }));
  }, []);

  const onStart = useCallback(
    async (p: GeneratorParams) => {
      if (!userId) {
        setError('Alıştırma için giriş gerekli.');
        return;
      }
      setBusy(true);
      setError(null);
      try {
        const q = await createQuiz({
          grade: p.grade,
          subject: p.subject,
          unit_id: p.unitId,
          difficulty: p.difficulty,
          question_count: p.count,
          tenant_id: userId,
        });
        setQuiz(q);
        setAnswers({});
        startRef.current = Date.now();
        setStep('solving');
      } catch (e) {
        setError((e as Error).message);
      } finally {
        setBusy(false);
      }
    },
    [userId],
  );

  const onSubmit = useCallback(async () => {
    if (!quiz || !userId || busy) return;
    setBusy(true);
    setError(null);
    try {
      const payload = quiz.questions.map((q) => answers[q.number] ?? { number: q.number });
      const res = await submitAttempt(quiz.id, {
        tenant_id: userId,
        answers: payload,
        duration_seconds: Math.round((Date.now() - startRef.current) / 1000),
      });
      setResult(res);
      setStep('result');
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }, [quiz, userId, busy, answers]);

  const restart = useCallback(() => {
    setStep('setup');
    setQuiz(null);
    setResult(null);
    setAnswers({});
    setError(null);
  }, []);

  return (
    <SafeAreaView style={styles.safe} edges={['bottom']}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        {step === 'setup' && (
          <>
            {error ? <Text style={styles.error}>{error}</Text> : null}
            <GeneratorSetup
              submitLabel="Başla"
              busy={busy}
              counts={[5, 10, 15]}
              onSubmit={onStart}
            />
            {busy ? (
              <>
                <View style={styles.loadingWrap}>
                  <Mascot variant="thinking" size={72} />
                  <Text style={styles.muted}>Alıştırma hazırlanıyor (30-90 sn)…</Text>
                </View>
                <SkeletonList count={3} />
              </>
            ) : null}
          </>
        )}

        {step === 'solving' && quiz && (
          <>
            <Text style={styles.heading}>{quiz.title}</Text>
            {quiz.questions.map((q) => (
              <QuestionCard
                key={q.number}
                q={q}
                answer={answers[q.number]}
                onChange={(patch) => setAnswer(q.number, patch)}
              />
            ))}
            {error ? <Text style={styles.error}>{error}</Text> : null}
            <Pressable
              style={[styles.primaryBtn, busy && styles.btnDisabled]}
              onPress={onSubmit}
              disabled={busy}
            >
              {busy ? (
                <ActivityIndicator color={colors.onBrand} />
              ) : (
                <Text style={styles.primaryBtnText}>Bitir & Puanla</Text>
              )}
            </Pressable>
          </>
        )}

        {step === 'result' && result && (
          <>
            <Text style={styles.heading}>Sonuç</Text>
            <View style={styles.resultMascotWrap}>
              <Mascot
                variant={result.score / Math.max(result.total, 1) >= 0.5 ? 'happy' : 'thinking'}
                size={104}
              />
            </View>
            <View style={styles.scoreCard}>
              <Text style={styles.scoreBig}>
                {result.score}/{result.total}
              </Text>
              <Text style={styles.muted}>
                %{Math.round((result.score / Math.max(result.total, 1)) * 100)} başarı
              </Text>
            </View>
            {result.per_kazanim.length > 0 && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Kazanım kırılımı</Text>
                {result.per_kazanim.map((k) => (
                  <View key={k.kazanim_kod} style={styles.kazanimRow}>
                    <Text style={styles.kazanimKod}>{k.kazanim_kod}</Text>
                    <Text style={styles.muted}>
                      {k.correct}/{k.total}
                    </Text>
                  </View>
                ))}
              </View>
            )}
            <Pressable style={styles.primaryBtn} onPress={restart}>
              <Text style={styles.primaryBtnText}>Yeni Alıştırma</Text>
            </Pressable>
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function QuestionCard({
  q,
  answer,
  onChange,
}: {
  q: QuizQuestionPublic;
  answer?: SubmittedAnswer;
  onChange: (patch: Partial<SubmittedAnswer>) => void;
}) {
  return (
    <View style={styles.qCard}>
      <QuestionText text={`${q.number}. ${q.question}`} />
      {q.question_type === 'coktan_secmeli' && q.options ? (
        <View style={{ gap: spacing.sm }}>
          {q.options.map((opt, i) => (
            <Pressable
              key={i}
              onPress={() => onChange({ selected_index: i })}
              style={[styles.option, answer?.selected_index === i && styles.optionSelected]}
            >
              <Text
                style={[styles.optionText, answer?.selected_index === i && styles.optionTextSelected]}
              >
                {String.fromCharCode(65 + i)}) {opt}
              </Text>
            </Pressable>
          ))}
        </View>
      ) : q.question_type === 'dogru_yanlis' ? (
        <View style={styles.trueFalseRow}>
          {[
            { v: true, label: 'Doğru' },
            { v: false, label: 'Yanlış' },
          ].map((o) => (
            <Pressable
              key={o.label}
              onPress={() => onChange({ bool_answer: o.v })}
              style={[styles.tfBtn, answer?.bool_answer === o.v && styles.optionSelected]}
            >
              <Text
                style={[styles.optionText, answer?.bool_answer === o.v && styles.optionTextSelected]}
              >
                {o.label}
              </Text>
            </Pressable>
          ))}
        </View>
      ) : q.blank_count && q.blank_count > 0 ? (
        <View style={{ gap: spacing.sm }}>
          {Array.from({ length: q.blank_count }).map((_, i) => (
            <TextInput
              key={i}
              style={styles.input}
              placeholder={`Boşluk ${i + 1}`}
              value={answer?.texts?.[i] ?? ''}
              onChangeText={(t) => {
                const texts = [...(answer?.texts ?? [])];
                texts[i] = t;
                onChange({ texts });
              }}
            />
          ))}
        </View>
      ) : (
        <TextInput
          style={styles.input}
          placeholder="Cevabın"
          value={answer?.texts?.[0] ?? ''}
          onChangeText={(t) => onChange({ texts: [t] })}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  content: { padding: spacing.lg, gap: spacing.lg, paddingBottom: spacing.xxl },
  heading: { fontSize: fontSize.xl, fontFamily: fonts.heading, color: colors.text },
  section: { gap: spacing.sm },
  sectionTitle: { fontSize: fontSize.sm, fontFamily: fonts.bodyBold, color: colors.textMuted },
  muted: { color: colors.textMuted, fontSize: fontSize.sm },
  error: { color: colors.danger, fontSize: fontSize.sm },
  loadingWrap: { alignItems: 'center', gap: spacing.sm, paddingVertical: spacing.md },
  resultMascotWrap: { alignItems: 'center' },
  primaryBtn: {
    backgroundColor: colors.brand,
    borderRadius: radius.md,
    paddingVertical: spacing.lg,
    alignItems: 'center',
  },
  btnDisabled: { opacity: 0.4 },
  primaryBtnText: { color: colors.onBrand, fontSize: fontSize.md, fontFamily: fonts.bodyBold },
  qCard: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    padding: spacing.md,
    gap: spacing.md,
    backgroundColor: colors.surface,
  },
  option: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.sm,
    padding: spacing.md,
    backgroundColor: colors.bg,
  },
  optionSelected: { borderColor: colors.brand, backgroundColor: '#eff6ff', borderWidth: 2 },
  optionText: { color: colors.text, fontSize: fontSize.sm, fontFamily: fonts.body },
  optionTextSelected: { color: colors.brand, fontFamily: fonts.bodyBold },
  trueFalseRow: { flexDirection: 'row', gap: spacing.sm },
  tfBtn: {
    flex: 1,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.sm,
    padding: spacing.md,
    alignItems: 'center',
    backgroundColor: colors.bg,
  },
  input: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    fontSize: fontSize.md,
    color: colors.text,
    backgroundColor: colors.bg,
  },
  scoreCard: {
    alignItems: 'center',
    gap: spacing.xs,
    paddingVertical: spacing.xl,
    borderRadius: radius.lg,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  scoreBig: { fontSize: 44, fontFamily: fonts.heading, color: colors.brand },
  kazanimRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  kazanimKod: { color: colors.text, fontSize: fontSize.sm, flex: 1 },
});
