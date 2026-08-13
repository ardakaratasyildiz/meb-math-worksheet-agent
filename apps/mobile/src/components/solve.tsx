import type {
  AttemptResult,
  QuestionResult,
  QuizQuestionPublic,
  SubmittedAnswer,
} from '@soruatolyesi/shared';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { IconSpark } from '@/components/icons';
import { Mascot } from '@/components/mascot';
import { QuestionText } from '@/components/question-text';
import { Card, PrimaryButton, ProgressBar } from '@/components/ui';
import { colors, fonts, fontSize, radius, spacing } from '@/theme/tokens';

/** Gömülü "A) .. B) .." şıklarını soru KÖKÜNDEN ayıklar (web QuestionReview deseni).
 * D1 sonrası backend şıkları hem `.options` alanına hem metne gömüyor → çoktan seçmeli
 * çözme ekranında şıklar buton olarak render edilirken metinde İKİNCİ KEZ görünmesin. */
export function stripInlineOptions(text: string): string {
  const re = /(^|[^A-Za-z0-9])([A-D])[)\.]/g;
  const marks: number[] = [];
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    marks.push(m.index + m[1].length);
    if (m.index === re.lastIndex) re.lastIndex++;
  }
  if (marks.length < 2) return text; // tek işaretçi cümle-içi olabilir → dokunma
  return marks[0] > 0 ? text.slice(0, marks[0]).trim() : text;
}

/** Skor/kazanım oranına göre geri-bildirim rengi (çöz + ödev ortak). */
export function toneFor(ratio: number): string {
  if (ratio >= 0.7) return colors.success;
  if (ratio >= 0.4) return colors.reward;
  return colors.energy;
}

// ── Çöz sonuç ekranı (öğrenci: gamification'lı · yetişkin: sade) ───────────────
export function ResultView({
  result,
  onRestart,
  restartLabel = 'Yeni Oluştur',
  sober = false,
  onReview,
}: {
  result: AttemptResult;
  onRestart: () => void;
  restartLabel?: string;
  sober?: boolean;
  /** "Soru soru incele" — verilmezse düğme gizlenir (ör. detay ucu yoksa). */
  onReview?: () => void;
}) {
  const ratio = result.score / Math.max(result.total, 1);
  const passed = ratio >= 0.5;
  const pct = Math.round(ratio * 100);
  const wrong = result.results.filter((r) => !r.is_correct);
  return (
    <>
      {sober ? (
        <Card style={styles.scoreCardSober}>
          <Text style={styles.scoreKickerSober}>Sonuç</Text>
          <Text style={styles.scoreBigSober}>
            {result.score}
            <Text style={styles.scoreTotalSober}>/{result.total}</Text>
          </Text>
          <View style={styles.scoreBarWrap}>
            <ProgressBar progress={ratio} color={toneFor(ratio)} height={10} />
          </View>
          <Text style={styles.scorePctSober}>%{pct} doğruluk</Text>
        </Card>
      ) : (
        <>
          <View style={styles.resultMascotWrap}>
            <Mascot variant={passed ? 'happy' : 'thinking'} size={120} />
          </View>
          <Card floating style={[styles.scoreCard, { backgroundColor: toneFor(ratio) }]}>
            <Text style={styles.scoreKicker}>{passed ? 'Harika iş!' : 'İyi deneme!'}</Text>
            <Text style={styles.scoreBig}>
              {result.score}
              <Text style={styles.scoreTotal}>/{result.total}</Text>
            </Text>
            <View style={styles.scoreBarWrap}>
              <ProgressBar progress={ratio} color="#FFFFFF" height={10} />
            </View>
            <Text style={styles.scorePct}>%{pct} başarı</Text>
          </Card>
        </>
      )}

      {result.per_kazanim.length > 0 && (
        <Card>
          <Text style={styles.cardTitle}>Kazanım kırılımı</Text>
          <View style={styles.kazanimList}>
            {result.per_kazanim.map((k) => {
              const r = k.correct / Math.max(k.total, 1);
              return (
                <View key={k.kazanim_kod} style={styles.kazanimRow}>
                  <View style={styles.kazanimHead}>
                    <Text style={styles.kazanimKod} numberOfLines={1}>
                      {k.kazanim_kod}
                    </Text>
                    <Text style={styles.kazanimCount}>
                      {k.correct}/{k.total}
                    </Text>
                  </View>
                  <ProgressBar progress={r} color={toneFor(r)} height={8} />
                </View>
              );
            })}
          </View>
        </Card>
      )}

      {/*
        "Hangi soruları yanlış yaptım?" — skor tek başına öğretmiyordu. Burada kısa
        özet var; soru metni + kendi cevabın + çözüm zaten /attempt/[id] ekranında
        (AttemptDetailView) duruyor, oraya bağlanıyoruz — ikinci bir kopya yazmıyoruz.
      */}
      {wrong.length > 0 ? (
        <Card>
          <Text style={styles.cardTitle}>Yanlış yaptıkların ({wrong.length})</Text>
          <View style={styles.wrongList}>
            {wrong.map((r) => (
              <View key={r.number} style={styles.wrongRow}>
                <View style={styles.wrongNo}>
                  <Text style={styles.wrongNoText}>{r.number}</Text>
                </View>
                <View style={styles.wrongBody}>
                  <Text style={styles.wrongLabel}>Doğru cevap</Text>
                  <Text style={styles.wrongAnswer} numberOfLines={3}>
                    {correctAnswerText(r)}
                  </Text>
                </View>
              </View>
            ))}
          </View>
          {onReview ? (
            <PrimaryButton label="Soru soru incele" variant="soft" onPress={onReview} />
          ) : null}
        </Card>
      ) : (
        <Card style={styles.allRightCard}>
          <Text style={styles.allRightText}>Hepsi doğru! 🎉</Text>
        </Card>
      )}

      <PrimaryButton label={restartLabel} onPress={onRestart} icon={<IconSpark size={22} />} />
    </>
  );
}

/** Doğru cevabı okunur metne çevirir (çoktan seçmelide harf + şık metni). */
function correctAnswerText(r: QuestionResult): string {
  if (r.options?.length && r.correct_index != null && r.correct_index >= 0) {
    const opt = r.options[r.correct_index];
    return `${String.fromCharCode(65 + r.correct_index)}) ${opt ?? ''}`.trim();
  }
  if (r.question_type === 'dogru_yanlis') {
    const a = (r.correct_answer || '').toLowerCase();
    if (a === 'true' || a === 'doğru') return 'Doğru';
    if (a === 'false' || a === 'yanlış') return 'Yanlış';
  }
  return r.correct_answer || '—';
}

// ── Çözülebilir soru kartı (çoktan seçmeli / doğru-yanlış / boşluk / metin) ────
export function QuestionCard({
  q,
  answer,
  onChange,
}: {
  q: QuizQuestionPublic;
  answer?: SubmittedAnswer;
  onChange: (patch: Partial<SubmittedAnswer>) => void;
}) {
  return (
    <Card style={styles.qcCard}>
      <View style={styles.qcHead}>
        <View style={styles.qNo}>
          <Text style={styles.qNoText}>{q.number}</Text>
        </View>
        <View style={styles.qBody}>
          <QuestionText
            text={
              q.question_type === 'coktan_secmeli' && q.options?.length
                ? stripInlineOptions(q.question)
                : q.question
            }
          />
        </View>
      </View>

      {q.question_type === 'coktan_secmeli' && q.options ? (
        <View style={styles.optList}>
          {q.options.map((opt, i) => {
            const sel = answer?.selected_index === i;
            const letter = String.fromCharCode(65 + i);
            return (
              <Pressable
                key={i}
                onPress={() => onChange({ selected_index: i })}
                style={[styles.option, sel && styles.optionSelected]}
              >
                <View style={[styles.optLetter, sel && styles.optLetterSel]}>
                  <Text style={[styles.optLetterText, sel && styles.optLetterTextSel]}>{letter}</Text>
                </View>
                {opt.includes('$') ? (
                  <QuestionText text={opt} color={sel ? colors.brand : colors.text} width={230} />
                ) : (
                  <Text style={[styles.optionText, sel && styles.optionTextSelected]}>{opt}</Text>
                )}
              </Pressable>
            );
          })}
        </View>
      ) : q.question_type === 'dogru_yanlis' ? (
        <View style={styles.trueFalseRow}>
          {[
            { v: true, label: 'Doğru' },
            { v: false, label: 'Yanlış' },
          ].map((o) => {
            const sel = answer?.bool_answer === o.v;
            return (
              <Pressable
                key={o.label}
                onPress={() => onChange({ bool_answer: o.v })}
                style={[styles.tfBtn, sel && styles.optionSelected]}
              >
                <Text style={[styles.optionText, sel && styles.optionTextSelected]}>{o.label}</Text>
              </Pressable>
            );
          })}
        </View>
      ) : q.blank_count && q.blank_count > 0 ? (
        <View style={styles.optList}>
          {Array.from({ length: q.blank_count }).map((_, i) => (
            <TextInput
              key={i}
              style={styles.input}
              placeholder={`Boşluk ${i + 1}`}
              placeholderTextColor={colors.textFaint}
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
          placeholderTextColor={colors.textFaint}
          value={answer?.texts?.[0] ?? ''}
          onChangeText={(t) => onChange({ texts: [t] })}
        />
      )}
    </Card>
  );
}

const styles = StyleSheet.create({
  cardTitle: { fontSize: fontSize.lg, fontFamily: fonts.heading, color: colors.text },

  wrongList: { gap: spacing.sm, marginTop: spacing.sm, marginBottom: spacing.md },
  wrongRow: { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.md },
  wrongNo: {
    width: 28,
    height: 28,
    borderRadius: 14,
    // Tema paletinde danger için tint yok (danger "yalnız hata" rengi) → yumuşak zemin.
    backgroundColor: '#FDECEC',
    alignItems: 'center',
    justifyContent: 'center',
  },
  wrongNoText: { fontFamily: fonts.bodyBold, fontSize: fontSize.sm, color: colors.danger },
  wrongBody: { flex: 1 },
  wrongLabel: { fontFamily: fonts.body, fontSize: fontSize.xs, color: colors.textMuted },
  wrongAnswer: { fontFamily: fonts.bodyMedium, fontSize: fontSize.sm, color: colors.text },
  allRightCard: { alignItems: 'center' },
  allRightText: { fontFamily: fonts.bodyBold, fontSize: fontSize.md, color: colors.success },

  qcCard: { gap: spacing.md, padding: spacing.lg },
  qcHead: { flexDirection: 'row', gap: spacing.md },
  qNo: { width: 32, height: 32, borderRadius: radius.md, backgroundColor: colors.tintBlue, alignItems: 'center', justifyContent: 'center' },
  qNoText: { color: colors.brand, fontFamily: fonts.heading, fontSize: fontSize.md },
  qBody: { flex: 1, paddingTop: 4 },

  optList: { gap: spacing.sm },
  option: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    borderRadius: radius.lg,
    padding: spacing.md,
    backgroundColor: colors.bgTint,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  optionSelected: { borderColor: colors.brand, backgroundColor: colors.tintBlue },
  optLetter: { width: 28, height: 28, borderRadius: 14, backgroundColor: colors.surface, alignItems: 'center', justifyContent: 'center' },
  optLetterSel: { backgroundColor: colors.brand },
  optLetterText: { color: colors.textMuted, fontFamily: fonts.heading, fontSize: fontSize.sm },
  optLetterTextSel: { color: colors.onBrand },
  optionText: { color: colors.text, fontSize: fontSize.md, fontFamily: fonts.bodyMedium, flex: 1 },
  optionTextSelected: { color: colors.brand, fontFamily: fonts.bodyBold },
  trueFalseRow: { flexDirection: 'row', gap: spacing.md },
  tfBtn: {
    flex: 1,
    borderRadius: radius.lg,
    paddingVertical: spacing.lg,
    alignItems: 'center',
    backgroundColor: colors.bgTint,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  input: {
    borderRadius: radius.lg,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    fontSize: fontSize.md,
    fontFamily: fonts.bodyMedium,
    color: colors.text,
    backgroundColor: colors.bgTint,
  },

  resultMascotWrap: { alignItems: 'center', marginBottom: -spacing.sm },
  scoreCard: { alignItems: 'center', gap: spacing.xs, paddingVertical: spacing.xl },
  scoreKicker: { fontFamily: fonts.heading, fontSize: fontSize.md, color: colors.onBrand, opacity: 0.95 },
  scoreBig: { fontFamily: fonts.heading, fontSize: 56, color: colors.onBrand, lineHeight: 62 },
  scoreTotal: { fontSize: fontSize.xxl, opacity: 0.8 },
  scoreBarWrap: { width: '70%', marginTop: spacing.sm },
  scorePct: { fontFamily: fonts.bodyBold, fontSize: fontSize.sm, color: colors.onBrand, opacity: 0.95, marginTop: spacing.xs },
  scoreCardSober: { alignItems: 'center', gap: spacing.xs, paddingVertical: spacing.xl },
  scoreKickerSober: { fontFamily: fonts.bodyHeavy, fontSize: fontSize.sm, color: colors.textMuted, letterSpacing: 0.5 },
  scoreBigSober: { fontFamily: fonts.bodyHeavy, fontSize: 52, color: colors.text, lineHeight: 58 },
  scoreTotalSober: { fontSize: fontSize.xxl, color: colors.textMuted },
  scorePctSober: { fontFamily: fonts.bodyBold, fontSize: fontSize.sm, color: colors.textMuted, marginTop: spacing.xs },
  kazanimList: { gap: spacing.md, marginTop: spacing.md },
  kazanimRow: { gap: spacing.xs },
  kazanimHead: { flexDirection: 'row', justifyContent: 'space-between', gap: spacing.sm },
  kazanimKod: { color: colors.text, fontSize: fontSize.sm, fontFamily: fonts.bodyMedium, flex: 1 },
  kazanimCount: { color: colors.textMuted, fontSize: fontSize.sm, fontFamily: fonts.bodyBold },
});
