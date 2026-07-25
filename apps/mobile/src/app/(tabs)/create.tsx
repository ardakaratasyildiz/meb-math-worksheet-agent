import { useAuth, useUser } from '@clerk/expo';
import type { AttemptResult, QuizPublic, SubmittedAnswer, Worksheet } from '@soruatolyesi/shared';
import { useRouter } from 'expo-router';
import { useCallback, useRef, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { GeneratorSetup, type GeneratorParams } from '@/components/generator-setup';
import { IconDocSimple, IconSpark, IconWorksheet } from '@/components/icons';
import { Mascot } from '@/components/mascot';
import { QuestionText } from '@/components/question-text';
import { ShareSheet } from '@/components/share-sheet';
import { SkeletonList } from '@/components/skeleton';
import { QuestionCard, ResultView, stripInlineOptions } from '@/components/solve';
import { Card, PrimaryButton, ScreenHeader } from '@/components/ui';
import { useEntitlements } from '@/hooks/useEntitlements';
import { createQuiz, generateWorksheet, submitAttempt } from '@/lib/api';
import { previewWorksheetPdf, shareWorksheetPdf } from '@/lib/pdf';
import { effectiveRole, isPlayfulRole } from '@/lib/roles';
import { colors, fonts, fontSize, radius, spacing } from '@/theme/tokens';

type Phase = 'setup' | 'solving' | 'result' | 'sheet';

/**
 * Birleşik üretim ekranı ("Oluştur"). Çöz + Kağıt tek akışta: çıktı BAŞTA seçilir
 * (öğrenci: Çöz/PDF · öğretmen/veli: yalnız PDF). Çözme UI'ı components/solve.tsx'te
 * ORTAK (ödev çözme ekranı da aynı bileşenleri kullanır).
 */
export default function CreateScreen() {
  const { userId } = useAuth();
  const { user } = useUser();
  const router = useRouter();
  const { entitlements, quotaExhausted, refresh: refreshEntitlements } = useEntitlements();
  const sober = !isPlayfulRole(effectiveRole(user));
  const [phase, setPhase] = useState<Phase>('setup');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [params, setParams] = useState<GeneratorParams | null>(null);

  const [quiz, setQuiz] = useState<QuizPublic | null>(null);
  const [answers, setAnswers] = useState<Record<number, SubmittedAnswer>>({});
  const startRef = useRef(0);
  const [result, setResult] = useState<AttemptResult | null>(null);

  const [worksheet, setWorksheet] = useState<Worksheet | null>(null);
  const [sharing, setSharing] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [shareOpen, setShareOpen] = useState(false);

  const setAnswer = useCallback((n: number, patch: Partial<SubmittedAnswer>) => {
    setAnswers((prev) => ({ ...prev, [n]: { ...prev[n], ...patch, number: n } }));
  }, []);

  const onGenerate = useCallback(
    async (p: GeneratorParams) => {
      if (p.mode === 'solve' && !userId) {
        setError('Çözmek için giriş gerekli.');
        return;
      }
      // Soft-gate: kota bittiyse paywall'a yönlendir (gerçek enforce sunucuda).
      if (quotaExhausted) {
        router.push({ pathname: '/paywall', params: { reason: 'quota' } });
        return;
      }
      setParams(p);
      setBusy(true);
      setError(null);
      try {
        if (p.mode === 'solve') {
          const q = await createQuiz({
            grade: p.grade,
            subject: p.subject,
            unit_id: p.unitId,
            kazanim_kod: p.kazanimKod,
            difficulty: p.difficulty,
            difficulty_mode: p.difficultyMode,
            question_count: p.count,
            question_types: p.questionTypes,
            tenant_id: userId!,
          });
          setQuiz(q);
          setAnswers({});
          startRef.current = Date.now();
          setPhase('solving');
        } else {
          const res = await generateWorksheet({
            grade: p.grade,
            subject: p.subject,
            unit_id: p.unitId,
            kazanim_kod: p.kazanimKod,
            difficulty: p.difficulty,
            difficulty_mode: p.difficultyMode,
            question_count: p.count,
            question_types: p.questionTypes,
            include_answer_key: p.includeAnswerKey,
            include_solutions: p.includeSolutions,
            tenant_id: userId ?? null,
          });
          setWorksheet(res.worksheet);
          setPhase('sheet');
        }
      } catch (e) {
        setError((e as Error).message);
      } finally {
        setBusy(false);
        void refreshEntitlements(); // kota tüketildi → göstergeyi güncelle
      }
    },
    [userId, quotaExhausted, router, refreshEntitlements],
  );

  const onSubmitQuiz = useCallback(async () => {
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
      setPhase('result');
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }, [quiz, userId, busy, answers]);

  const pdfOpts = useCallback(
    () => ({
      includeAnswerKey: params?.includeAnswerKey ?? true,
      includeSolutions: params?.includeSolutions ?? true,
    }),
    [params],
  );

  const onPreviewPdf = useCallback(async () => {
    if (!worksheet || previewing) return;
    setPreviewing(true);
    setError(null);
    try {
      await previewWorksheetPdf(worksheet, pdfOpts());
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setPreviewing(false);
    }
  }, [worksheet, previewing, pdfOpts]);

  const onSharePdf = useCallback(async () => {
    if (!worksheet || sharing) return;
    setSharing(true);
    setError(null);
    try {
      await shareWorksheetPdf(worksheet, pdfOpts());
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSharing(false);
    }
  }, [worksheet, sharing, pdfOpts]);

  const restart = useCallback(() => {
    setPhase('setup');
    setQuiz(null);
    setResult(null);
    setAnswers({});
    setWorksheet(null);
    setError(null);
  }, []);

  return (
    <View style={styles.root}>
      <SafeAreaView style={styles.safe} edges={['top']}>
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          {phase === 'setup' && (
            <>
              {error ? <Text style={styles.error}>{error}</Text> : null}
              {userId && entitlements.quota.limit !== null ? (
                <Pressable onPress={() => router.push('/paywall')} style={styles.quotaChip}>
                  <Text style={styles.quotaChipText}>
                    Bu ay: {entitlements.quota.used}/{entitlements.quota.limit} kağıt
                  </Text>
                  <Text style={styles.quotaChipCta}>Yükselt</Text>
                </Pressable>
              ) : null}
              <GeneratorSetup busy={busy} onSubmit={onGenerate} sober={sober} pdfOnly={sober} />
              {busy ? (
                <>
                  <View style={styles.loadingWrap}>
                    {sober ? null : <Mascot variant="thinking" size={80} />}
                    <Text style={styles.muted}>Sorular hazırlanıyor — 30-90 saniye sürebilir…</Text>
                  </View>
                  <SkeletonList count={3} />
                </>
              ) : null}
            </>
          )}

          {phase === 'solving' && quiz && (
            <>
              <ScreenHeader title={quiz.title} subtitle={`${quiz.questions.length} soru`} />
              {quiz.questions.map((q) => (
                <QuestionCard
                  key={q.number}
                  q={q}
                  answer={answers[q.number]}
                  onChange={(patch) => setAnswer(q.number, patch)}
                />
              ))}
              {error ? <Text style={styles.error}>{error}</Text> : null}
              <PrimaryButton label="Bitir & Puanla" color={colors.success} busy={busy} onPress={onSubmitQuiz} />
              <PrimaryButton
                label="Testi paylaş"
                variant="soft"
                onPress={() => setShareOpen(true)}
                icon={<IconSpark size={20} />}
              />
            </>
          )}

          {phase === 'result' && result && (
            <>
              <ResultView result={result} onRestart={restart} sober={sober} />
              {quiz ? (
                <PrimaryButton
                  label="Bu testi arkadaşlarınla paylaş"
                  variant="soft"
                  color={colors.magic}
                  onPress={() => setShareOpen(true)}
                  icon={<IconSpark size={20} />}
                />
              ) : null}
            </>
          )}

          {phase === 'sheet' && worksheet && (
            <>
              <ScreenHeader
                title={worksheet.title}
                subtitle={`${worksheet.question_count} soru · ${worksheet.difficulty}`}
                right={<Mascot variant="happy" size={64} />}
              />
              {worksheet.questions.map((q) => {
                const isMc = q.question_type === 'coktan_secmeli' && !!q.options?.length;
                return (
                  <Card key={q.number} style={styles.qCard}>
                    <View style={styles.qNo}>
                      <Text style={styles.qNoText}>{q.number}</Text>
                    </View>
                    <View style={styles.qBody}>
                      <QuestionText text={isMc ? stripInlineOptions(q.question) : q.question} />
                      {isMc ? (
                        <View style={styles.optList}>
                          {q.options!.map((opt, i) => (
                            <View key={i} style={styles.optRow}>
                              <Text style={styles.optLetter}>{String.fromCharCode(65 + i)})</Text>
                              <View style={styles.optText}>
                                <QuestionText text={opt} />
                              </View>
                            </View>
                          ))}
                        </View>
                      ) : null}
                    </View>
                  </Card>
                );
              })}
              {error ? <Text style={styles.error}>{error}</Text> : null}
              <PrimaryButton
                label="PDF önizle"
                busy={previewing}
                onPress={onPreviewPdf}
                icon={<IconWorksheet size={22} tone="#FFFFFF" />}
              />
              <PrimaryButton
                label="Paylaş"
                variant="soft"
                busy={sharing}
                onPress={onSharePdf}
                icon={<IconDocSimple size={20} color={colors.brand} />}
              />
              <PrimaryButton
                label="Yeni oluştur"
                variant="soft"
                color={colors.textMuted}
                onPress={restart}
              />
            </>
          )}

          <ShareSheet
            quizId={quiz?.id ?? null}
            tenantId={userId ?? null}
            visible={shareOpen}
            onClose={() => setShareOpen(false)}
          />
        </ScrollView>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  safe: { flex: 1 },
  content: { padding: spacing.xl, gap: spacing.lg, paddingBottom: 120 }, // yüzen tab bar payı
  muted: { color: colors.textMuted, fontSize: fontSize.sm, fontFamily: fonts.body, textAlign: 'center' },
  error: { color: colors.danger, fontSize: fontSize.sm, fontFamily: fonts.bodyMedium },
  quotaChip: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: colors.tintBlue,
    borderRadius: radius.pill,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
  },
  quotaChipText: { fontFamily: fonts.bodyMedium, fontSize: fontSize.sm, color: colors.brand },
  quotaChipCta: { fontFamily: fonts.bodyBold, fontSize: fontSize.sm, color: colors.brandDark },
  loadingWrap: { alignItems: 'center', gap: spacing.sm, paddingVertical: spacing.md },

  // PDF soru kartı
  qCard: { flexDirection: 'row', gap: spacing.md, padding: spacing.lg },
  qNo: { width: 32, height: 32, borderRadius: radius.md, backgroundColor: colors.tintBlue, alignItems: 'center', justifyContent: 'center' },
  qNoText: { color: colors.brand, fontFamily: fonts.heading, fontSize: fontSize.md },
  qBody: { flex: 1 },
  optList: { marginTop: spacing.sm, gap: spacing.xs },
  optRow: { flexDirection: 'row', gap: spacing.sm, alignItems: 'flex-start' },
  optLetter: { fontFamily: fonts.bodyBold, fontSize: fontSize.sm, color: colors.brand, marginTop: 1 },
  optText: { flex: 1 },
});
