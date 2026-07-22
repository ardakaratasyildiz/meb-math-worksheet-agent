import {
  SUBJECT_COLORS,
  SUBJECT_EMOJI,
  SUBJECT_LABELS,
  SUBJECT_SLUGS,
  type Difficulty,
  type SubjectSlug,
} from '@soruatolyesi/shared';
import { useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { Chip } from '@/components/pickers';
import { useUnits } from '@/hooks/useUnits';
import { colors, fonts, fontSize, radius, spacing } from '@/theme/tokens';

const GRADES = [1, 2, 3, 4, 5, 6, 7, 8];
const DIFFICULTIES: { value: Difficulty; label: string }[] = [
  { value: 'kolay', label: 'Kolay' },
  { value: 'orta', label: 'Orta' },
  { value: 'zor', label: 'Zor' },
];

export interface GeneratorParams {
  subject: SubjectSlug;
  grade: number;
  unitId: string;
  unitName: string;
  difficulty: Difficulty;
  count: number;
}

const STEP_TITLES = ['Hangi ders?', 'Kaçıncı sınıf?', 'Hangi ünite?', 'Son ayarlar'];

/**
 * Adımlı üretim akışı (rehberli huni): ders → sınıf → ünite → ayarlar.
 * Tek ekran tek amaç. worksheet + practice ortak kullanır.
 */
export function GeneratorSetup({
  onSubmit,
  submitLabel,
  busy,
  counts = [5, 10, 15, 20],
}: {
  onSubmit: (p: GeneratorParams) => void;
  submitLabel: string;
  busy: boolean;
  counts?: number[];
}) {
  const [step, setStep] = useState(0);
  const [subject, setSubject] = useState<SubjectSlug>('matematik');
  const [grade, setGrade] = useState(5);
  const { units, loading: unitsLoading, error } = useUnits(grade, subject);
  const [unitId, setUnitId] = useState<string | null>(null);
  const [unitName, setUnitName] = useState('');
  const [difficulty, setDifficulty] = useState<Difficulty>('orta');
  const [count, setCount] = useState(counts[Math.min(1, counts.length - 1)]);

  function pickSubject(s: SubjectSlug) {
    setSubject(s);
    setUnitId(null);
    setStep(1);
  }
  function pickGrade(g: number) {
    setGrade(g);
    setUnitId(null);
    setStep(2);
  }
  function pickUnit(id: string, name: string) {
    setUnitId(id);
    setUnitName(name);
    setStep(3);
  }

  return (
    <View style={styles.wrap}>
      {/* Üst: geri + adım noktaları */}
      <View style={styles.topBar}>
        {step > 0 ? (
          <Pressable onPress={() => setStep(step - 1)} hitSlop={12}>
            <Text style={styles.back}>‹ Geri</Text>
          </Pressable>
        ) : (
          <View />
        )}
        <View style={styles.dots}>
          {STEP_TITLES.map((_, i) => (
            <View
              key={i}
              style={[styles.dot, i === step && styles.dotActive, i < step && styles.dotDone]}
            />
          ))}
        </View>
      </View>

      {/* Seçim özeti (breadcrumb) — tıkla, o adıma dön */}
      {step > 0 ? (
        <View style={styles.crumbs}>
          <Crumb label={`${SUBJECT_EMOJI[subject]} ${SUBJECT_LABELS[subject]}`} onPress={() => setStep(0)} />
          {step > 1 ? <Crumb label={`${grade}. sınıf`} onPress={() => setStep(1)} /> : null}
          {step > 2 && unitName ? <Crumb label={unitName} onPress={() => setStep(2)} /> : null}
        </View>
      ) : null}

      <Text style={styles.stepTitle}>{STEP_TITLES[step]}</Text>

      {step === 0 ? (
        <View style={styles.chipRow}>
          {SUBJECT_SLUGS.map((s) => (
            <Chip
              key={s}
              label={`${SUBJECT_EMOJI[s]} ${SUBJECT_LABELS[s]}`}
              selected={subject === s}
              color={SUBJECT_COLORS[s]}
              onPress={() => pickSubject(s)}
            />
          ))}
        </View>
      ) : step === 1 ? (
        <View style={styles.chipRow}>
          {GRADES.map((g) => (
            <Chip key={g} label={`${g}.`} selected={grade === g} onPress={() => pickGrade(g)} />
          ))}
        </View>
      ) : step === 2 ? (
        unitsLoading ? (
          <ActivityIndicator style={{ marginTop: spacing.md }} />
        ) : error ? (
          <Text style={styles.error}>{error}</Text>
        ) : units.length === 0 ? (
          <Text style={styles.muted}>Bu seçimde ünite bulunamadı. Geri dönüp değiştir.</Text>
        ) : (
          <View style={{ gap: spacing.sm }}>
            {units.map((u) => (
              <Pressable
                key={u.unit_id}
                onPress={() => pickUnit(u.unit_id, u.name)}
                style={styles.unitRow}
              >
                <Text style={styles.unitName}>
                  {u.no}. {u.name}
                </Text>
                <Text style={styles.muted}>{u.kazanim_count} kazanım</Text>
              </Pressable>
            ))}
          </View>
        )
      ) : (
        <View style={{ gap: spacing.lg }}>
          <View style={styles.field}>
            <Text style={styles.fieldLabel}>Zorluk</Text>
            <View style={styles.chipRow}>
              {DIFFICULTIES.map((d) => (
                <Chip
                  key={d.value}
                  label={d.label}
                  selected={difficulty === d.value}
                  onPress={() => setDifficulty(d.value)}
                />
              ))}
            </View>
          </View>
          <View style={styles.field}>
            <Text style={styles.fieldLabel}>Soru sayısı</Text>
            <View style={styles.chipRow}>
              {counts.map((c) => (
                <Chip key={c} label={String(c)} selected={count === c} onPress={() => setCount(c)} />
              ))}
            </View>
          </View>
          <Pressable
            style={[styles.submit, busy && styles.submitDisabled]}
            onPress={() =>
              unitId &&
              onSubmit({ subject, grade, unitId, unitName, difficulty, count })
            }
            disabled={busy || !unitId}
          >
            {busy ? (
              <ActivityIndicator color={colors.onBrand} />
            ) : (
              <Text style={styles.submitText}>{submitLabel}</Text>
            )}
          </Pressable>
        </View>
      )}
    </View>
  );
}

function Crumb({ label, onPress }: { label: string; onPress: () => void }) {
  return (
    <Pressable onPress={onPress} style={styles.crumb} hitSlop={6}>
      <Text style={styles.crumbText} numberOfLines={1}>
        {label}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: spacing.lg },
  topBar: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  back: { color: colors.brand, fontFamily: fonts.bodyBold, fontSize: fontSize.md },
  dots: { flexDirection: 'row', gap: 6 },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: colors.border },
  dotActive: { backgroundColor: colors.brand, width: 20 },
  dotDone: { backgroundColor: colors.brand },
  crumbs: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  crumb: {
    backgroundColor: colors.surface,
    borderRadius: radius.pill,
    paddingHorizontal: spacing.md,
    paddingVertical: 6,
    maxWidth: 180,
  },
  crumbText: { color: colors.textMuted, fontSize: fontSize.xs, fontFamily: fonts.bodyMedium },
  stepTitle: { fontSize: fontSize.xl, fontFamily: fonts.heading, color: colors.text },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  muted: { color: colors.textMuted, fontSize: fontSize.sm },
  error: { color: colors.danger, fontSize: fontSize.sm },
  unitRow: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    padding: spacing.md,
    backgroundColor: colors.surface,
  },
  unitName: { color: colors.text, fontSize: fontSize.md, fontFamily: fonts.bodyMedium },
  field: { gap: spacing.sm },
  fieldLabel: { fontSize: fontSize.sm, fontFamily: fonts.bodyBold, color: colors.textMuted },
  submit: {
    backgroundColor: colors.brand,
    borderRadius: radius.md,
    paddingVertical: spacing.lg,
    alignItems: 'center',
    marginTop: spacing.sm,
  },
  submitDisabled: { opacity: 0.4 },
  submitText: { color: colors.onBrand, fontSize: fontSize.md, fontFamily: fonts.bodyBold },
});
