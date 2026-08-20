import type { SolutionStep, SubmittedAnswer } from '@soruatolyesi/shared';
import { StyleSheet, Text, View } from 'react-native';

import { hasMathNotation, QuestionText } from '@/components/question-text';
import type { AttemptDetail, AttemptReviewItem } from '@/lib/api';
import { formatDate, scorePct, scoreTone } from '@/lib/format';
import { colors, fonts, fontSize, radius, spacing } from '@/theme/tokens';

const TONE: Record<'good' | 'mid' | 'low', string> = {
  good: colors.success,
  mid: '#d97706',
  low: colors.danger,
};

/** Cevabı soru tipine göre okunur metne çevirir. */
function formatSubmitted(item: AttemptReviewItem): string {
  const s: SubmittedAnswer | null | undefined = item.submitted;
  if (!s) return 'Boş bırakıldı';
  if (item.question_type === 'coktan_secmeli') {
    const i = s.selected_index;
    if (i == null) return 'Boş bırakıldı';
    const opt = item.options?.[i];
    return `${String.fromCharCode(65 + i)}) ${opt ?? ''}`.trim();
  }
  if (item.question_type === 'dogru_yanlis') {
    if (s.bool_answer == null) return 'Boş bırakıldı';
    return s.bool_answer ? 'Doğru' : 'Yanlış';
  }
  const texts = (s.texts ?? []).filter((t) => t && t.trim());
  return texts.length ? texts.join(', ') : 'Boş bırakıldı';
}

function solutionText(steps: string | SolutionStep[]): string {
  if (typeof steps === 'string') return steps.trim();
  return steps
    .map((st) => {
      const comp = st.computation ? ` ${st.computation}` : '';
      return `${st.step_no}. ${st.description}${comp}`;
    })
    .join('\n');
}

/**
 * Bir denemenin tam gözden geçirmesi (skor + kazanım + soru-soru cevap/çözüm).
 * Öğrencinin kendi denemesi ve öğretmenin öğrenci detayı ORTAK kullanır;
 * `answerLabel` ile "Senin cevabın" / "Öğrencinin cevabı" ayrışır.
 */
export function AttemptDetailView({
  detail,
  answerLabel = 'Senin cevabın',
}: {
  detail: AttemptDetail;
  answerLabel?: string;
}) {
  const pct = scorePct(detail.score, detail.total);
  const tone = TONE[scoreTone(pct)];
  return (
    <>
      <Text style={styles.title}>{detail.title}</Text>
      <Text style={styles.meta}>
        {detail.grade ? `${detail.grade}. sınıf · ` : ''}
        {detail.difficulty} · {formatDate(detail.completed_at)}
      </Text>

      <View style={styles.scoreCard}>
        <Text style={[styles.scoreBig, { color: tone }]}>
          {detail.score}/{detail.total}
        </Text>
        <Text style={styles.muted}>%{pct} başarı</Text>
      </View>

      {detail.per_kazanim.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Kazanım kırılımı</Text>
          {detail.per_kazanim.map((k) => (
            <View key={k.kazanim_kod} style={styles.kRow}>
              <Text style={styles.kKod} numberOfLines={1}>
                {k.kazanim_kod}
              </Text>
              <Text style={styles.muted}>
                {k.correct}/{k.total}
              </Text>
            </View>
          ))}
        </View>
      )}

      {!detail.has_detail ? (
        <Text style={styles.note}>
          Bu denemenin soru detayı artık mevcut değil (yalnız skor özeti).
        </Text>
      ) : (
        detail.review.map((item) => (
          <ReviewCard key={item.number} item={item} answerLabel={answerLabel} />
        ))
      )}
    </>
  );
}

function ReviewCard({ item, answerLabel }: { item: AttemptReviewItem; answerLabel: string }) {
  const yours = formatSubmitted(item);
  const solution = solutionText(item.solution_steps);
  return (
    <View style={[styles.qCard, item.is_correct ? styles.qCorrect : styles.qWrong]}>
      <View style={styles.qHead}>
        <Text style={styles.qNum}>Soru {item.number}</Text>
        <Text style={[styles.badge, item.is_correct ? styles.badgeOk : styles.badgeNo]}>
          {item.is_correct ? '✓ Doğru' : '✕ Yanlış'}
        </Text>
      </View>

      <QuestionText text={item.question} />

      <View style={styles.answerRow}>
        <Text style={styles.answerLabel}>{answerLabel}</Text>
        <AnswerVal value={yours} tone={item.is_correct ? 'plain' : 'wrong'} />
      </View>
      {!item.is_correct && (
        <View style={styles.answerRow}>
          <Text style={styles.answerLabel}>Doğru cevap</Text>
          <AnswerVal value={item.correct_answer} tone="ok" />
        </View>
      )}

      {solution ? (
        <View style={styles.solutionBox}>
          <Text style={styles.solutionLabel}>Çözüm</Text>
          {/* Çözüm adımları da soru gövdesi gibi matematik taşır ("$\sqrt{75}$",
              "$2^6$"). Düz <Text> ile basılınca ham LaTeX görünüyordu — köklü/üslü
              ifadeler okunamıyordu (saha bildirimi, 2026-08-20). */}
          {hasMathNotation(solution) ? (
            <QuestionText text={solution} width={280} />
          ) : (
            <Text style={styles.solutionText}>{solution}</Text>
          )}
        </View>
      ) : null}
    </View>
  );
}

function AnswerVal({ value, tone }: { value: string; tone: 'wrong' | 'ok' | 'plain' }) {
  const color = tone === 'wrong' ? colors.danger : tone === 'ok' ? colors.success : colors.text;
  if (hasMathNotation(value)) {
    return <QuestionText text={value} color={color} width={260} />;
  }
  return (
    <Text style={[styles.answerVal, tone === 'wrong' && styles.answerWrong, tone === 'ok' && styles.answerOk]}>
      {value}
    </Text>
  );
}

const styles = StyleSheet.create({
  title: { fontSize: fontSize.xl, fontFamily: fonts.heading, color: colors.text },
  meta: { fontSize: fontSize.xs, fontFamily: fonts.body, color: colors.textMuted },
  scoreCard: { alignItems: 'center', backgroundColor: colors.surface, borderRadius: radius.lg, paddingVertical: spacing.xl, gap: spacing.xs },
  scoreBig: { fontSize: 40, fontFamily: fonts.heading },
  muted: { fontSize: fontSize.sm, fontFamily: fonts.bodyMedium, color: colors.textMuted },
  section: { gap: spacing.sm, marginTop: spacing.sm },
  sectionTitle: { fontSize: fontSize.md, fontFamily: fonts.headingSemi, color: colors.text },
  kRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: spacing.md },
  kKod: { flex: 1, fontSize: fontSize.sm, fontFamily: fonts.body, color: colors.text },
  note: { fontSize: fontSize.sm, fontFamily: fonts.body, color: colors.textMuted, fontStyle: 'italic', marginTop: spacing.sm },
  qCard: { borderRadius: radius.lg, borderWidth: 1, padding: spacing.lg, gap: spacing.sm, marginTop: spacing.sm },
  qCorrect: { borderColor: '#a7f3d0', backgroundColor: '#f0fdf4' },
  qWrong: { borderColor: '#fecaca', backgroundColor: '#fef2f2' },
  qHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  qNum: { fontSize: fontSize.sm, fontFamily: fonts.bodyBold, color: colors.textMuted },
  badge: { fontSize: fontSize.xs, fontFamily: fonts.bodyBold, paddingVertical: 2, paddingHorizontal: spacing.sm, borderRadius: radius.pill, overflow: 'hidden' },
  badgeOk: { color: '#065f46', backgroundColor: '#d1fae5' },
  badgeNo: { color: '#991b1b', backgroundColor: '#fee2e2' },
  answerRow: { gap: 2 },
  answerLabel: { fontSize: fontSize.xs, fontFamily: fonts.bodyMedium, color: colors.textMuted },
  answerVal: { fontSize: fontSize.sm, fontFamily: fonts.bodyBold, color: colors.text },
  answerWrong: { color: colors.danger },
  answerOk: { color: colors.success },
  solutionBox: { backgroundColor: colors.bg, borderRadius: radius.md, padding: spacing.md, gap: spacing.xs, marginTop: spacing.xs },
  solutionLabel: { fontSize: fontSize.xs, fontFamily: fonts.bodyBold, color: colors.textMuted },
  solutionText: { fontSize: fontSize.sm, fontFamily: fonts.body, color: colors.text, lineHeight: 20 },
});
