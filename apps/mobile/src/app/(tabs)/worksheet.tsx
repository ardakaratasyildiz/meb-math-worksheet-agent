import { useAuth } from '@clerk/expo';
import type { Worksheet } from '@soruatolyesi/shared';
import { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { GeneratorSetup, type GeneratorParams } from '@/components/generator-setup';
import { Mascot } from '@/components/mascot';
import { QuestionText } from '@/components/question-text';
import { SkeletonList } from '@/components/skeleton';
import { generateWorksheet } from '@/lib/api';
import { shareWorksheetPdf } from '@/lib/pdf';
import { colors, fonts, fontSize, radius, spacing } from '@/theme/tokens';

export default function WorksheetScreen() {
  const { userId } = useAuth();
  const [generating, setGenerating] = useState(false);
  const [sharing, setSharing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [worksheet, setWorksheet] = useState<Worksheet | null>(null);

  const onGenerate = useCallback(
    async (p: GeneratorParams) => {
      setGenerating(true);
      setError(null);
      setWorksheet(null);
      try {
        const res = await generateWorksheet({
          grade: p.grade,
          subject: p.subject,
          unit_id: p.unitId,
          difficulty: p.difficulty,
          question_count: p.count,
          tenant_id: userId ?? null,
          include_answer_key: true,
          include_solutions: true,
        });
        setWorksheet(res.worksheet);
      } catch (e) {
        setError((e as Error).message);
      } finally {
        setGenerating(false);
      }
    },
    [userId],
  );

  const onSharePdf = useCallback(async () => {
    if (!worksheet || sharing) return;
    setSharing(true);
    setError(null);
    try {
      await shareWorksheetPdf(worksheet);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSharing(false);
    }
  }, [worksheet, sharing]);

  return (
    <SafeAreaView style={styles.safe} edges={['bottom']}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        {!worksheet ? (
          <>
            {error ? <Text style={styles.error}>{error}</Text> : null}
            <GeneratorSetup submitLabel="Oluştur" busy={generating} onSubmit={onGenerate} />
            {generating ? (
              <>
                <View style={styles.loadingWrap}>
                  <Mascot variant="thinking" size={72} />
                  <Text style={styles.muted}>Sorular üretiliyor — 30-90 saniye sürebilir…</Text>
                </View>
                <SkeletonList count={3} />
              </>
            ) : null}
          </>
        ) : (
          <View style={styles.result}>
            <Text style={styles.resultTitle}>{worksheet.title}</Text>
            <Text style={styles.muted}>
              {worksheet.question_count} soru · {worksheet.difficulty}
            </Text>
            {worksheet.questions.map((q) => (
              <View key={q.number} style={styles.questionCard}>
                <Text style={styles.questionNo}>{q.number}.</Text>
                <View style={styles.questionBody}>
                  <QuestionText text={q.question} />
                </View>
              </View>
            ))}
            {error ? <Text style={styles.error}>{error}</Text> : null}
            <Pressable
              style={[styles.btn, sharing && styles.btnDisabled]}
              onPress={onSharePdf}
              disabled={sharing}
            >
              {sharing ? (
                <ActivityIndicator color={colors.onBrand} />
              ) : (
                <Text style={styles.btnText}>📄 PDF oluştur & paylaş</Text>
              )}
            </Pressable>
            <Pressable
              style={styles.secondaryBtn}
              onPress={() => {
                setWorksheet(null);
                setError(null);
              }}
            >
              <Text style={styles.secondaryText}>Yeni kağıt</Text>
            </Pressable>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  content: { padding: spacing.lg, gap: spacing.lg, paddingBottom: spacing.xxl },
  muted: { color: colors.textMuted, fontSize: fontSize.sm, textAlign: 'center' },
  loadingWrap: { alignItems: 'center', gap: spacing.sm, paddingVertical: spacing.md },
  error: { color: colors.danger, fontSize: fontSize.sm },
  result: { gap: spacing.md },
  resultTitle: { fontSize: fontSize.lg, fontFamily: fonts.heading, color: colors.text },
  questionCard: {
    flexDirection: 'row',
    gap: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    padding: spacing.md,
    backgroundColor: colors.surface,
  },
  questionNo: { color: colors.brand, fontFamily: fonts.bodyBold },
  questionBody: { flex: 1 },
  btn: {
    backgroundColor: colors.brand,
    borderRadius: radius.md,
    paddingVertical: spacing.lg,
    alignItems: 'center',
  },
  btnDisabled: { opacity: 0.4 },
  btnText: { color: colors.onBrand, fontSize: fontSize.md, fontFamily: fonts.bodyBold },
  secondaryBtn: { alignItems: 'center', paddingVertical: spacing.md },
  secondaryText: { color: colors.brand, fontFamily: fonts.bodyBold },
});
