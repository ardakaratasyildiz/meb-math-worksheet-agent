import { useAuth } from '@clerk/expo';
import {
  SUBJECT_COLORS,
  SUBJECT_EMOJI,
  SUBJECT_LABELS,
  SUBJECT_SLUGS,
  type Difficulty,
  type SubjectSlug,
  type UnitInfo,
  type Worksheet,
} from '@soruatolyesi/shared';
import { Stack } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { generateWorksheet, listUnits } from '@/lib/api';
import { colors, fontSize, fontWeight, radius, spacing } from '@/theme/tokens';

const GRADES = [1, 2, 3, 4, 5, 6, 7, 8];
const DIFFICULTIES: { value: Difficulty; label: string }[] = [
  { value: 'kolay', label: 'Kolay' },
  { value: 'orta', label: 'Orta' },
  { value: 'zor', label: 'Zor' },
];
const COUNTS = [5, 10, 15, 20];

function Chip({
  label,
  selected,
  onPress,
  color,
}: {
  label: string;
  selected: boolean;
  onPress: () => void;
  color?: string;
}) {
  const accent = color ?? colors.brand;
  return (
    <Pressable
      onPress={onPress}
      style={[
        styles.chip,
        selected && { backgroundColor: accent, borderColor: accent },
      ]}
    >
      <Text style={[styles.chipText, selected && styles.chipTextSelected]}>
        {label}
      </Text>
    </Pressable>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      <View style={styles.chipRow}>{children}</View>
    </View>
  );
}

export default function WorksheetScreen() {
  const { userId } = useAuth();
  const [subject, setSubject] = useState<SubjectSlug>('matematik');
  const [grade, setGrade] = useState(5);
  const [units, setUnits] = useState<UnitInfo[]>([]);
  const [unitsLoading, setUnitsLoading] = useState(false);
  const [unitId, setUnitId] = useState<string | null>(null);
  const [difficulty, setDifficulty] = useState<Difficulty>('orta');
  const [count, setCount] = useState(10);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [worksheet, setWorksheet] = useState<Worksheet | null>(null);

  // Ders/sınıf değişince üniteleri yükle.
  useEffect(() => {
    let cancelled = false;
    setUnitsLoading(true);
    setUnitId(null);
    setUnits([]);
    setError(null);
    listUnits(grade, subject)
      .then((u) => {
        if (!cancelled) setUnits(u);
      })
      .catch((e) => {
        if (!cancelled) setError((e as Error).message);
      })
      .finally(() => {
        if (!cancelled) setUnitsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [grade, subject]);

  const onGenerate = useCallback(async () => {
    if (!unitId || generating) return;
    setGenerating(true);
    setError(null);
    setWorksheet(null);
    try {
      const res = await generateWorksheet({
        grade,
        subject,
        unit_id: unitId,
        difficulty,
        question_count: count,
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
  }, [unitId, generating, grade, subject, difficulty, count, userId]);

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
      <Stack.Screen options={{ title: 'Çalışma Kağıdı' }} />
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.heading}>Çalışma Kağıdı Oluştur</Text>

        <Section title="Ders">
          {SUBJECT_SLUGS.map((s) => (
            <Chip
              key={s}
              label={`${SUBJECT_EMOJI[s]} ${SUBJECT_LABELS[s]}`}
              selected={subject === s}
              color={SUBJECT_COLORS[s]}
              onPress={() => setSubject(s)}
            />
          ))}
        </Section>

        <Section title="Sınıf">
          {GRADES.map((g) => (
            <Chip
              key={g}
              label={`${g}. sınıf`}
              selected={grade === g}
              onPress={() => setGrade(g)}
            />
          ))}
        </Section>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Ünite / Konu</Text>
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
                  style={[
                    styles.unitRow,
                    unitId === u.unit_id && styles.unitRowSelected,
                  ]}
                >
                  <Text style={styles.unitName}>
                    {u.no}. {u.name}
                  </Text>
                  <Text style={styles.muted}>{u.kazanim_count} kazanım</Text>
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
          style={[styles.generateBtn, (!unitId || generating) && styles.btnDisabled]}
          onPress={onGenerate}
          disabled={!unitId || generating}
        >
          {generating ? (
            <ActivityIndicator color={colors.onBrand} />
          ) : (
            <Text style={styles.generateBtnText}>Oluştur</Text>
          )}
        </Pressable>
        {generating ? (
          <Text style={styles.muted}>
            Sorular üretiliyor — bu 30-90 saniye sürebilir…
          </Text>
        ) : null}

        {worksheet ? (
          <View style={styles.result}>
            <Text style={styles.resultTitle}>{worksheet.title}</Text>
            <Text style={styles.muted}>
              {worksheet.question_count} soru · {worksheet.difficulty}
            </Text>
            {worksheet.questions.map((q) => (
              <View key={q.number} style={styles.questionCard}>
                <Text style={styles.questionNo}>{q.number}.</Text>
                <Text style={styles.questionText}>{q.question}</Text>
              </View>
            ))}
            <Text style={styles.muted}>
              PDF + WhatsApp paylaşımı sonraki adımda eklenecek.
            </Text>
          </View>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  content: { padding: spacing.lg, gap: spacing.lg, paddingBottom: spacing.xxl },
  heading: {
    fontSize: fontSize.xl,
    fontWeight: fontWeight.heavy,
    color: colors.text,
  },
  section: { gap: spacing.sm },
  sectionTitle: {
    fontSize: fontSize.sm,
    fontWeight: fontWeight.bold,
    color: colors.textMuted,
  },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  chip: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.pill,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    backgroundColor: colors.bg,
  },
  chipText: { color: colors.text, fontSize: fontSize.sm, fontWeight: fontWeight.medium },
  chipTextSelected: { color: colors.onBrand },
  unitRow: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    padding: spacing.md,
    backgroundColor: colors.surface,
  },
  unitRowSelected: { borderColor: colors.brand, borderWidth: 2 },
  unitName: { color: colors.text, fontSize: fontSize.md, fontWeight: fontWeight.medium },
  muted: { color: colors.textMuted, fontSize: fontSize.sm },
  error: { color: colors.danger, fontSize: fontSize.sm },
  generateBtn: {
    backgroundColor: colors.brand,
    borderRadius: radius.md,
    paddingVertical: spacing.lg,
    alignItems: 'center',
  },
  btnDisabled: { opacity: 0.4 },
  generateBtnText: {
    color: colors.onBrand,
    fontSize: fontSize.md,
    fontWeight: fontWeight.bold,
  },
  result: { gap: spacing.md, marginTop: spacing.sm },
  resultTitle: {
    fontSize: fontSize.lg,
    fontWeight: fontWeight.heavy,
    color: colors.text,
  },
  questionCard: {
    flexDirection: 'row',
    gap: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    padding: spacing.md,
    backgroundColor: colors.surface,
  },
  questionNo: { color: colors.brand, fontWeight: fontWeight.bold },
  questionText: { color: colors.text, flex: 1, fontSize: fontSize.sm, lineHeight: 20 },
});
