import { useAuth } from '@clerk/expo';
import {
  SUBJECT_COLORS,
  SUBJECT_EMOJI,
  SUBJECT_LABELS,
  SUBJECT_SLUGS,
  type AttemptResult,
  type Difficulty,
  type QuizPublic,
  type QuizQuestionPublic,
  type SubjectSlug,
  type SubmittedAnswer,
} from '@soruatolyesi/shared';
import { Stack } from 'expo-router';
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

import { Chip, Section } from '@/components/pickers';
import { createQuiz, submitAttempt } from '@/lib/api';
import { useUnits } from '@/hooks/useUnits';
import { colors, fontSize, fontWeight, radius, spacing } from '@/theme/tokens';

const GRADES = [1, 2, 3, 4, 5, 6, 7, 8];
const DIFFICULTIES: { value: Difficulty; label: string }[] = [
  { value: 'kolay', label: 'Kolay' },
  { value: 'orta', label: 'Orta' },
  { value: 'zor', label: 'Zor' },
];
const COUNTS = [5, 10, 15];

type Step = 'setup' | 'solving' | 'result';

export default function PracticeScreen() {
  const { userId } = useAuth();
  const [step, setStep] = useState<Step>('setup');

  // setup
  const [subject, setSubject] = useState<SubjectSlug>('matematik');
  const [grade, setGrade] = useState(5);
  const { units, loading: unitsLoading } = useUnits(grade, subject);
  const [unitId, setUnitId] = useState<string | null>(null);
  const [difficulty, setDifficulty] = useState<Difficulty>('orta');
  const [count, setCount] = useState(5);

  // shared
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // solving
  const [quiz, setQuiz] = useState<QuizPublic | null>(null);
  const [answers, setAnswers] = useState<Record<number, SubmittedAnswer>>({});
  const startRef = useRef(0);

  // result
  const [result, setResult] = useState<AttemptResult | null>(null);

  const setAnswer = useCallback((n: number, patch: Partial<SubmittedAnswer>) => {
    setAnswers((prev) => ({ ...prev, [n]: { ...prev[n], ...patch, number: n } }));
  }, []);

  const onStart = useCallback(async () => {
    if (!unitId || busy) return;
    if (!userId) {
      setError('Alıştırma için giriş gerekli.');
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const q = await createQuiz({
        grade,
        subject,
        unit_id: unitId,
        difficulty,
        question_count: count,
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
  }, [unitId, busy, userId, grade, subject, difficulty, count]);

  const onSubmit = useCallback(async () => {
    if (!quiz || !userId || busy) return;
    setBusy(true);
    setError(null);
    try {
      const payload = quiz.questions.map(
        (q) => answers[q.number] ?? { number: q.number },
      );
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
    <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
      <Stack.Screen options={{ title: 'Alıştırma' }} />
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        {step === 'setup' && (
          <>
            <Text style={styles.heading}>Alıştırma Çöz</Text>
            <Section title="Ders">
              {SUBJECT_SLUGS.map((s) => (
                <Chip
                  key={s}
                  label={`${SUBJECT_EMOJI[s]} ${SUBJECT_LABELS[s]}`}
                  selected={subject === s}
                  color={SUBJECT_COLORS[s]}
                  onPress={() => {
                    setSubject(s);
                    setUnitId(null);
                  }}
                />
              ))}
            </Section>
            <Section title="Sınıf">
              {GRADES.map((g) => (
                <Chip
                  key={g}
                  label={`${g}.`}
                  selected={grade === g}
                  onPress={() => {
                    setGrade(g);
                    setUnitId(null);
                  }}
                />
              ))}
            </Section>
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Ünite</Text>
              {unitsLoading ? (
                <ActivityIndicator style={{ marginTop: spacing.sm }} />
              ) : units.length === 0 ? (
                <Text style={styles.muted}>Bu seçimde ünite bulunamadı.</Text>
              ) : (
                <View style={{ gap: spacing.sm }}>
                  {units.map((u) => (
                    <Pressable
                      key={u.unit_id}
                      onPress={() => setUnitId(u.unit_id)}
                      style={[styles.unitRow, unitId === u.unit_id && styles.unitRowSelected]}
                    >
                      <Text style={styles.unitName}>
                        {u.no}. {u.name}
                      </Text>
                    </Pressable>
                  ))}
                </View>
              )}
            </View>
            <Section title="Zorluk">
              {DIFFICULTIES.map((d) => (
                <Chip
                  key={d.value}
                  label={d.label}
                  selected={difficulty === d.value}
                  onPress={() => setDifficulty(d.value)}
                />
              ))}
            </Section>
            <Section title="Soru sayısı">
              {COUNTS.map((c) => (
                <Chip
                  key={c}
                  label={String(c)}
                  selected={count === c}
                  onPress={() => setCount(c)}
                />
              ))}
            </Section>
            {error ? <Text style={styles.error}>{error}</Text> : null}
            <Pressable
              style={[styles.primaryBtn, (!unitId || busy) && styles.btnDisabled]}
              onPress={onStart}
              disabled={!unitId || busy}
            >
              {busy ? (
                <ActivityIndicator color={colors.onBrand} />
              ) : (
                <Text style={styles.primaryBtnText}>Başla</Text>
              )}
            </Pressable>
            {busy ? (
              <Text style={styles.muted}>Alıştırma hazırlanıyor (30-90 sn)…</Text>
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
      <Text style={styles.qText}>
        {q.number}. {q.question}
      </Text>
      {q.question_type === 'coktan_secmeli' && q.options ? (
        <View style={{ gap: spacing.sm }}>
          {q.options.map((opt, i) => (
            <Pressable
              key={i}
              onPress={() => onChange({ selected_index: i })}
              style={[styles.option, answer?.selected_index === i && styles.optionSelected]}
            >
              <Text
                style={[
                  styles.optionText,
                  answer?.selected_index === i && styles.optionTextSelected,
                ]}
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
                style={[
                  styles.optionText,
                  answer?.bool_answer === o.v && styles.optionTextSelected,
                ]}
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
  heading: { fontSize: fontSize.xl, fontWeight: fontWeight.heavy, color: colors.text },
  section: { gap: spacing.sm },
  sectionTitle: { fontSize: fontSize.sm, fontWeight: fontWeight.bold, color: colors.textMuted },
  muted: { color: colors.textMuted, fontSize: fontSize.sm },
  error: { color: colors.danger, fontSize: fontSize.sm },
  unitRow: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    padding: spacing.md,
    backgroundColor: colors.surface,
  },
  unitRowSelected: { borderColor: colors.brand, borderWidth: 2 },
  unitName: { color: colors.text, fontSize: fontSize.md, fontWeight: fontWeight.medium },
  primaryBtn: {
    backgroundColor: colors.brand,
    borderRadius: radius.md,
    paddingVertical: spacing.lg,
    alignItems: 'center',
  },
  btnDisabled: { opacity: 0.4 },
  primaryBtnText: { color: colors.onBrand, fontSize: fontSize.md, fontWeight: fontWeight.bold },
  qCard: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    padding: spacing.md,
    gap: spacing.md,
    backgroundColor: colors.surface,
  },
  qText: { color: colors.text, fontSize: fontSize.md, lineHeight: 22 },
  option: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.sm,
    padding: spacing.md,
    backgroundColor: colors.bg,
  },
  optionSelected: { borderColor: colors.brand, backgroundColor: '#eff6ff', borderWidth: 2 },
  optionText: { color: colors.text, fontSize: fontSize.sm },
  optionTextSelected: { color: colors.brand, fontWeight: fontWeight.bold },
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
  scoreBig: { fontSize: 44, fontWeight: fontWeight.heavy, color: colors.brand },
  kazanimRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  kazanimKod: { color: colors.text, fontSize: fontSize.sm, flex: 1 },
});
