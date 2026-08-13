import {
  SUBJECT_COLORS,
  SUBJECT_EMOJI,
  SUBJECT_LABELS,
  SUBJECT_SLUGS,
  type Difficulty,
  type DifficultyMode,
  type KazanimInfo,
  type QuestionType,
  type SubjectSlug,
} from '@soruatolyesi/shared';
import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  View,
} from 'react-native';

import { IconChevron, IconPencil, IconWorksheet } from '@/components/icons';
import { Mascot } from '@/components/mascot';
import { Chip } from '@/components/pickers';
import { PrimaryButton } from '@/components/ui';
import { useUnits } from '@/hooks/useUnits';
import { listKazanimlarByUnit } from '@/lib/api';
import { colors, fonts, fontSize, radius, shadow, spacing } from '@/theme/tokens';

export type GenMode = 'solve' | 'pdf';

const GRADES = [1, 2, 3, 4, 5, 6, 7, 8];
const DIFFICULTIES: { value: Difficulty; label: string }[] = [
  { value: 'kolay', label: 'Kolay' },
  { value: 'orta', label: 'Orta' },
  { value: 'zor', label: 'Zor' },
];
const DIFFICULTY_MODES: { value: DifficultyMode; label: string }[] = [
  { value: 'single', label: 'Tek seviye' },
  { value: 'mixed', label: 'Karışık' },
  { value: 'progressive', label: 'Progresyon' },
];

// Web QUESTION_TYPE_GROUPS ile birebir. "visual" grubu kullanıcıya gösterilmez —
// sunucu konuya göre otomatik ekler; kısıtlama yapılınca havuzda hep bulunur.
const TYPE_GROUPS = {
  open_ended: ['islem', 'sozel_problem', 'kavram_sorusu', 'akil_yurutme', 'modelleme', 'gunluk_hayat'],
  visual: ['salt_islem', 'tablo_sorusu', 'gorsel_geometri', 'grafik_okuma', 'oruntu_sekil'],
  multiple_choice: ['coktan_secmeli'],
  other_format: ['bosluk_doldurma', 'dogru_yanlis', 'eslestirme', 'siralama'],
} as const satisfies Record<string, QuestionType[]>;

type UserGroupKey = 'open_ended' | 'multiple_choice' | 'other_format';
const USER_GROUPS: { key: UserGroupKey; label: string }[] = [
  { key: 'open_ended', label: 'Açık uçlu' },
  { key: 'multiple_choice', label: 'Çoktan seçmeli' },
  { key: 'other_format', label: 'Diğer tipler' },
];

/** Seçili gruplardan backend question_types listesi (tümü açıksa null = kısıt yok). */
function flattenTypes(groups: Record<UserGroupKey, boolean>): QuestionType[] | null {
  const on = USER_GROUPS.map((g) => g.key).filter((k) => groups[k]);
  if (on.length === USER_GROUPS.length) return null;
  // Görsel tipler (salt_islem/tablo/grafik/örüntü) cevap formatı olarak AÇIK UÇLUDUR,
  // şıkları yoktur. Eskiden kullanıcı ne seçerse seçsin havuza ekleniyorlardı →
  // "Çoktan seçmeli" seçen kullanıcıya şıksız sorular geliyordu (canlı ölçüm: 6
  // sorunun 3'ü şıksız). Artık yalnız açık uçlu da isteniyorsa ekleniyorlar.
  const out: QuestionType[] = groups.open_ended ? [...TYPE_GROUPS.visual] : [];
  for (const k of on) out.push(...TYPE_GROUPS[k]);
  return out.length ? out : null;
}

export interface GeneratorParams {
  mode: GenMode;
  subject: SubjectSlug;
  grade: number;
  unitId: string;
  unitName: string;
  kazanimKod: string | null;
  difficulty: Difficulty;
  difficultyMode: DifficultyMode;
  count: number;
  questionTypes: QuestionType[] | null;
  includeAnswerKey: boolean;
  includeSolutions: boolean;
}

type StepKey = 'mode' | 'subject' | 'grade' | 'unit' | 'settings';

const QUESTION: Record<StepKey, string> = {
  mode: 'Ne yapmak istersin?',
  subject: 'Hangi ders?',
  grade: 'Kaçıncı sınıf?',
  unit: 'Hangi üniteye bakalım?',
  settings: 'Son ayarlar',
};
const MASCOT_FOR: Record<StepKey, 'wave' | 'thinking' | 'happy'> = {
  mode: 'wave',
  subject: 'wave',
  grade: 'thinking',
  unit: 'thinking',
  settings: 'happy',
};

/**
 * "Sihirbaz Kart" üretim akışı (B yönü). Öğrenci: çıktı başta seçilir (Çöz / PDF)
 * → ders → sınıf → ünite → ayarlar. Öğretmen/veli (`pdfOnly`): mod adımı YOK,
 * doğrudan PDF çalışma kağıdı üretir (çöz/geliş onlara kapalı). Her adım tek beyaz
 * kartın içinde; öğrenci maskotla, yetişkin sade adım rozetiyle (`sober`).
 */
export function GeneratorSetup({
  onSubmit,
  busy,
  counts = [5, 10, 15, 20],
  sober = false,
  pdfOnly = false,
  initialMode,
}: {
  onSubmit: (p: GeneratorParams) => void;
  busy: boolean;
  counts?: number[];
  /** Yetişkin tonu: maskot yerine sade adım rozeti. */
  sober?: boolean;
  /** Öğretmen/veli: yalnız PDF üretimi; mod seçme adımı atlanır. */
  pdfOnly?: boolean;
  /**
   * Mod dışarıdan seçilmişse (ana ekrandaki "Alıştırma Çöz" / "Çalışma Kağıdı"
   * kartları) mod adımı atlanır — kullanıcı zaten kararını vermiş, tekrar sormak
   * "butona bastım ama bir yere gitmedim" hissi yaratıyordu. Ekmek kırıntısındaki
   * moda basarak yine değiştirebilir.
   */
  initialMode?: GenMode;
}) {
  // Mod dışarıdan geldiyse (initialMode) ya da pdfOnly ise mod adımı listeden çıkar.
  // DONDURULUR: prop akış ortasında değişirse stepKeys uzunluğu kayar ve stepIdx
  // yanlış adımı gösterir. Giriş modu değişince ekran zaten `key` ile remount ediliyor.
  const [modePreset] = useState(() => pdfOnly || !!initialMode);
  const stepKeys: StepKey[] = modePreset
    ? ['subject', 'grade', 'unit', 'settings']
    : ['mode', 'subject', 'grade', 'unit', 'settings'];

  const [stepIdx, setStepIdx] = useState(0);
  const [mode, setMode] = useState<GenMode>(pdfOnly ? 'pdf' : (initialMode ?? 'solve'));
  const [modeChosen, setModeChosen] = useState(modePreset);
  const [subject, setSubject] = useState<SubjectSlug>('matematik');
  const [grade, setGrade] = useState(5);
  const { units, loading: unitsLoading, error } = useUnits(grade, subject);
  const [unitId, setUnitId] = useState<string | null>(null);
  const [unitName, setUnitName] = useState('');
  const [kazanimKod, setKazanimKod] = useState<string | null>(null);
  const [difficulty, setDifficulty] = useState<Difficulty>('orta');
  const [difficultyMode, setDifficultyMode] = useState<DifficultyMode>('single');
  const [count, setCount] = useState(counts[Math.min(1, counts.length - 1)]);
  const [groups, setGroups] = useState<Record<UserGroupKey, boolean>>({
    open_ended: true,
    multiple_choice: true,
    other_format: true,
  });
  const [includeAnswerKey, setIncludeAnswerKey] = useState(true);
  const [includeSolutions, setIncludeSolutions] = useState(true);
  const [advanced, setAdvanced] = useState(false);
  const [kazanimlar, setKazanimlar] = useState<KazanimInfo[]>([]);

  const key = stepKeys[stepIdx];

  // Ünite seçilince o ünitenin kazanımlarını yükle (gelişmiş → kazanım seçimi).
  useEffect(() => {
    if (!unitId) {
      setKazanimlar([]);
      return;
    }
    let cancelled = false;
    listKazanimlarByUnit(grade, unitId, subject)
      .then((k) => !cancelled && setKazanimlar(k))
      .catch(() => !cancelled && setKazanimlar([]));
    return () => {
      cancelled = true;
    };
  }, [grade, unitId, subject]);

  const anyGroupOn = groups.open_ended || groups.multiple_choice || groups.other_format;
  const next = () => setStepIdx((i) => Math.min(i + 1, stepKeys.length - 1));

  function pickMode(m: GenMode) {
    setMode(m);
    setModeChosen(true);
    next();
  }
  function pickSubject(s: SubjectSlug) {
    setSubject(s);
    setUnitId(null);
    setKazanimKod(null);
    next();
  }
  function pickGrade(g: number) {
    setGrade(g);
    setUnitId(null);
    setKazanimKod(null);
    next();
  }
  function pickUnit(id: string, name: string) {
    setUnitId(id);
    setUnitName(name);
    setKazanimKod(null);
    next();
  }
  function toggleGroup(k: UserGroupKey) {
    setGroups((g) => {
      const nextG = { ...g, [k]: !g[k] };
      if (!nextG.open_ended && !nextG.multiple_choice && !nextG.other_format) return g;
      return nextG;
    });
  }

  function submit() {
    if (!modeChosen || !unitId) return;
    onSubmit({
      mode,
      subject,
      grade,
      unitId,
      unitName,
      kazanimKod,
      difficulty,
      difficultyMode,
      count,
      questionTypes: flattenTypes(groups),
      includeAnswerKey,
      includeSolutions,
    });
  }

  return (
    <View style={[styles.card, shadow.card]}>
      {/* Üst: geri + adım göstergesi */}
      <View style={styles.top}>
        {stepIdx > 0 ? (
          <Pressable onPress={() => setStepIdx(stepIdx - 1)} hitSlop={12} style={styles.backBtn}>
            <Text style={styles.back}>‹</Text>
          </Pressable>
        ) : (
          <View style={styles.backBtn} />
        )}
        <View style={styles.stepper}>
          {stepKeys.map((k, i) => (
            <View key={k} style={[styles.sdot, i === stepIdx && styles.sdotOn, i < stepIdx && styles.sdotDone]} />
          ))}
        </View>
        <View style={styles.backBtn} />
      </View>

      {/* Maskot (öğrenci) / sade adım rozeti (yetişkin) + soru */}
      <View style={styles.qRow}>
        {sober ? (
          <View style={styles.stepBadge}>
            <Text style={styles.stepBadgeText}>{stepIdx + 1}</Text>
          </View>
        ) : (
          <MascotThumb variant={MASCOT_FOR[key]} />
        )}
        <Text style={styles.q}>{QUESTION[key]}</Text>
      </View>

      {/* Seçim özeti (breadcrumb) */}
      {stepIdx > 0 ? (
        <View style={styles.crumbs}>
          {!pdfOnly ? (
            <Crumb
              label={mode === 'solve' ? '✏️ Çöz' : '📄 PDF'}
              // Mod adımı listede yoksa (dışarıdan seçildi) o adıma dönemeyiz —
              // kırıntıya basmak modu doğrudan çevirir.
              onPress={
                modePreset
                  ? () => setMode((m) => (m === 'solve' ? 'pdf' : 'solve'))
                  : () => setStepIdx(0)
              }
            />
          ) : null}
          {stepKeys.indexOf('subject') < stepIdx ? (
            <Crumb
              label={`${SUBJECT_EMOJI[subject]} ${SUBJECT_LABELS[subject]}`}
              onPress={() => setStepIdx(stepKeys.indexOf('subject'))}
            />
          ) : null}
          {stepKeys.indexOf('grade') < stepIdx ? (
            <Crumb label={`${grade}. sınıf`} onPress={() => setStepIdx(stepKeys.indexOf('grade'))} />
          ) : null}
          {stepKeys.indexOf('unit') < stepIdx && unitName ? (
            <Crumb label={unitName} onPress={() => setStepIdx(stepKeys.indexOf('unit'))} />
          ) : null}
        </View>
      ) : null}

      {/* ── Adım gövdeleri ─────────────────────────────────────────────── */}
      {key === 'mode' ? (
        <View style={styles.modeList}>
          <ModeCard
            color={colors.success}
            tint={colors.tintGreen}
            icon={<IconPencil size={34} />}
            title="Çöz"
            sub="Uygulamada çöz, anında puanla, gelişimini gör"
            onPress={() => pickMode('solve')}
          />
          <ModeCard
            color={colors.brand}
            tint={colors.tintBlue}
            icon={<IconWorksheet size={34} tone="#FFFFFF" />}
            iconOnColor
            title="Çalışma Kağıdı (PDF)"
            sub="Yazdır ya da WhatsApp'tan paylaş"
            onPress={() => pickMode('pdf')}
          />
        </View>
      ) : key === 'subject' ? (
        <View style={styles.list}>
          {SUBJECT_SLUGS.map((s) => (
            <ListRow
              key={s}
              emoji={SUBJECT_EMOJI[s]}
              label={SUBJECT_LABELS[s]}
              accent={SUBJECT_COLORS[s]}
              selected={subject === s}
              onPress={() => pickSubject(s)}
            />
          ))}
        </View>
      ) : key === 'grade' ? (
        <View style={styles.gradeGrid}>
          {GRADES.map((g) => (
            <Pressable
              key={g}
              onPress={() => pickGrade(g)}
              style={({ pressed }) => [
                styles.gradeTile,
                grade === g && styles.gradeTileSel,
                pressed && styles.pressed,
              ]}
            >
              <Text style={[styles.gradeNum, grade === g && styles.gradeNumSel]}>{g}</Text>
              <Text style={[styles.gradeSuffix, grade === g && styles.gradeNumSel]}>sınıf</Text>
            </Pressable>
          ))}
        </View>
      ) : key === 'unit' ? (
        unitsLoading ? (
          <ActivityIndicator style={{ marginTop: spacing.md }} color={colors.brand} />
        ) : error ? (
          <Text style={styles.error}>{error}</Text>
        ) : units.length === 0 ? (
          <Text style={styles.muted}>Bu seçimde ünite yok. Geri dönüp değiştir.</Text>
        ) : (
          <View style={styles.list}>
            {units.map((u) => (
              <ListRow
                key={u.unit_id}
                no={u.no}
                label={u.name}
                meta={`${u.kazanim_count} kazanım`}
                selected={unitId === u.unit_id}
                onPress={() => pickUnit(u.unit_id, u.name)}
              />
            ))}
          </View>
        )
      ) : (
        <View style={styles.settings}>
          {difficultyMode === 'single' ? (
            <View style={styles.field}>
              <Text style={styles.fieldLabel}>Zorluk</Text>
              <View style={styles.chipRow}>
                {DIFFICULTIES.map((d) => (
                  <Chip key={d.value} label={d.label} selected={difficulty === d.value} onPress={() => setDifficulty(d.value)} />
                ))}
              </View>
            </View>
          ) : null}

          <View style={styles.field}>
            <Text style={styles.fieldLabel}>Kaç soru?</Text>
            <View style={styles.chipRow}>
              {counts.map((c) => (
                <Chip key={c} label={String(c)} selected={count === c} onPress={() => setCount(c)} />
              ))}
            </View>
          </View>

          {/* Gelişmiş ayarlar (varsayılan kapalı) */}
          <Pressable
            onPress={() => setAdvanced((v) => !v)}
            style={({ pressed }) => [styles.advToggle, pressed && styles.pressed]}
          >
            <Text style={styles.advToggleText}>Gelişmiş ayarlar</Text>
            <View style={{ transform: [{ rotate: advanced ? '90deg' : '0deg' }] }}>
              <IconChevron size={16} color={colors.brand} />
            </View>
          </Pressable>

          {advanced ? (
            <View style={styles.advBody}>
              {/* Kazanım */}
              <View style={styles.field}>
                <Text style={styles.fieldLabel}>Kazanım</Text>
                <View style={styles.chipRow}>
                  <Chip label="Tümü (otomatik)" selected={kazanimKod === null} onPress={() => setKazanimKod(null)} />
                  {kazanimlar.map((k) => (
                    <Chip key={k.kod} label={k.kod} selected={kazanimKod === k.kod} onPress={() => setKazanimKod(k.kod)} />
                  ))}
                </View>
              </View>

              {/* Zorluk modu */}
              <View style={styles.field}>
                <Text style={styles.fieldLabel}>Zorluk modu</Text>
                <View style={styles.chipRow}>
                  {DIFFICULTY_MODES.map((m) => (
                    <Chip key={m.value} label={m.label} selected={difficultyMode === m.value} onPress={() => setDifficultyMode(m.value)} />
                  ))}
                </View>
              </View>

              {/* Soru tipleri */}
              <View style={styles.field}>
                <Text style={styles.fieldLabel}>Soru tipleri</Text>
                <View style={styles.chipRow}>
                  {USER_GROUPS.map((g) => (
                    <Chip key={g.key} label={g.label} selected={groups[g.key]} onPress={() => toggleGroup(g.key)} />
                  ))}
                </View>
                {!anyGroupOn ? <Text style={styles.warn}>En az bir tip açık olmalı.</Text> : null}
              </View>

              {/* PDF çıktı içeriği (yalnız PDF modu) */}
              {mode === 'pdf' ? (
                <View style={styles.field}>
                  <Text style={styles.fieldLabel}>PDF içeriği</Text>
                  <ToggleRow label="Cevap anahtarı sayfası" value={includeAnswerKey} onValueChange={setIncludeAnswerKey} />
                  <ToggleRow label="Çözüm adımları sayfası" value={includeSolutions} onValueChange={setIncludeSolutions} />
                </View>
              ) : null}
            </View>
          ) : null}

          <PrimaryButton
            label={mode === 'solve' ? 'Çözmeye Başla' : 'Oluştur & PDF'}
            color={mode === 'solve' ? colors.success : colors.brand}
            busy={busy}
            disabled={!unitId || !anyGroupOn}
            onPress={submit}
          />
        </View>
      )}
    </View>
  );
}

// ── Alt bileşenler ────────────────────────────────────────────────────────────
function MascotThumb({ variant }: { variant: 'wave' | 'thinking' | 'happy' }) {
  return (
    <View style={styles.mThumb}>
      <Mascot variant={variant} size={46} animated={false} />
    </View>
  );
}

function ModeCard({
  color,
  tint,
  icon,
  iconOnColor,
  title,
  sub,
  onPress,
}: {
  color: string;
  tint: string;
  icon: React.ReactNode;
  iconOnColor?: boolean;
  title: string;
  sub: string;
  onPress: () => void;
}) {
  return (
    <Pressable onPress={onPress} style={({ pressed }) => [styles.modeCard, pressed && styles.pressed]}>
      <View style={[styles.modeIcon, { backgroundColor: iconOnColor ? color : tint }]}>{icon}</View>
      <View style={styles.modeBody}>
        <Text style={styles.modeTitle}>{title}</Text>
        <Text style={styles.modeSub}>{sub}</Text>
      </View>
      <IconChevron size={18} color={color} />
    </Pressable>
  );
}

function ListRow({
  emoji,
  no,
  label,
  meta,
  accent,
  selected,
  onPress,
}: {
  emoji?: string;
  no?: number;
  label: string;
  meta?: string;
  accent?: string;
  selected: boolean;
  onPress: () => void;
}) {
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.row, selected && styles.rowSel, pressed && styles.pressed]}
    >
      <View style={[styles.rowIc, selected && accent ? { backgroundColor: accent } : null]}>
        {emoji ? (
          <Text style={styles.rowEmoji}>{emoji}</Text>
        ) : (
          <Text style={[styles.rowNo, selected && styles.rowNoSel]}>{no}</Text>
        )}
      </View>
      <View style={styles.rowBody}>
        <Text style={[styles.rowLabel, selected && styles.rowLabelSel]} numberOfLines={2}>
          {label}
        </Text>
        {meta ? <Text style={styles.rowMeta}>{meta}</Text> : null}
      </View>
      <IconChevron size={16} color={colors.textFaint} />
    </Pressable>
  );
}

function ToggleRow({
  label,
  value,
  onValueChange,
}: {
  label: string;
  value: boolean;
  onValueChange: (v: boolean) => void;
}) {
  return (
    <View style={styles.toggleRow}>
      <Text style={styles.toggleLabel}>{label}</Text>
      <Switch
        value={value}
        onValueChange={onValueChange}
        trackColor={{ true: colors.brand, false: colors.track }}
        thumbColor="#FFFFFF"
      />
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
  card: { backgroundColor: colors.surface, borderRadius: radius.hero, padding: spacing.xl, gap: spacing.lg },

  top: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  backBtn: { width: 30, height: 30, alignItems: 'center', justifyContent: 'center' },
  back: { color: colors.textMuted, fontFamily: fonts.heading, fontSize: 26, lineHeight: 28 },
  stepper: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  sdot: { width: 8, height: 8, borderRadius: 4, backgroundColor: colors.border },
  sdotOn: { backgroundColor: colors.brand, width: 24 },
  sdotDone: { backgroundColor: colors.brand },

  qRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  mThumb: {
    width: 54,
    height: 54,
    borderRadius: 27,
    backgroundColor: colors.tintOrange,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  q: { flex: 1, fontFamily: fonts.heading, fontSize: fontSize.lg, color: colors.text },
  stepBadge: {
    width: 44,
    height: 44,
    borderRadius: radius.md,
    backgroundColor: colors.tintBlue,
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepBadgeText: { fontFamily: fonts.bodyHeavy, fontSize: fontSize.lg, color: colors.brand },

  crumbs: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginTop: -spacing.xs },
  crumb: { backgroundColor: colors.bgTint, borderRadius: radius.pill, paddingHorizontal: spacing.md, paddingVertical: 6, maxWidth: 170 },
  crumbText: { color: colors.textMuted, fontSize: fontSize.xs, fontFamily: fonts.bodyBold },

  pressed: { transform: [{ scale: 0.98 }], opacity: 0.92 },

  // Mod kartları
  modeList: { gap: spacing.md },
  modeCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    borderRadius: radius.lg,
    padding: spacing.md,
    backgroundColor: colors.bgTint,
  },
  modeIcon: { width: 54, height: 54, borderRadius: radius.md, alignItems: 'center', justifyContent: 'center' },
  modeBody: { flex: 1 },
  modeTitle: { fontFamily: fonts.heading, fontSize: fontSize.md, color: colors.text },
  modeSub: { fontFamily: fonts.body, fontSize: fontSize.xs, color: colors.textMuted, marginTop: 1 },

  // Liste satırları (ders/ünite)
  list: { gap: spacing.sm },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    borderRadius: radius.lg,
    padding: spacing.md,
    backgroundColor: colors.bgTint,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  rowSel: { backgroundColor: colors.tintBlue, borderColor: colors.brand },
  rowIc: { width: 40, height: 40, borderRadius: radius.md, backgroundColor: colors.surface, alignItems: 'center', justifyContent: 'center' },
  rowEmoji: { fontSize: 20 },
  rowNo: { fontFamily: fonts.heading, fontSize: fontSize.md, color: colors.brand },
  rowNoSel: { color: colors.brand },
  rowBody: { flex: 1 },
  rowLabel: { fontFamily: fonts.bodyBold, fontSize: fontSize.md, color: colors.text },
  rowLabelSel: { color: colors.brand },
  rowMeta: { fontFamily: fonts.body, fontSize: fontSize.xs, color: colors.textMuted, marginTop: 1 },

  // Sınıf grid
  gradeGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  gradeTile: {
    width: '22%',
    flexGrow: 1,
    aspectRatio: 1,
    borderRadius: radius.lg,
    backgroundColor: colors.bgTint,
    borderWidth: 2,
    borderColor: 'transparent',
    alignItems: 'center',
    justifyContent: 'center',
  },
  gradeTileSel: { backgroundColor: colors.tintBlue, borderColor: colors.brand },
  gradeNum: { fontFamily: fonts.heading, fontSize: fontSize.xl, color: colors.text },
  gradeNumSel: { color: colors.brand },
  gradeSuffix: { fontFamily: fonts.body, fontSize: 10, color: colors.textMuted, marginTop: -2 },

  // Ayarlar
  settings: { gap: spacing.lg },
  field: { gap: spacing.sm },
  fieldLabel: { fontSize: fontSize.sm, fontFamily: fonts.bodyBold, color: colors.textMuted },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  muted: { color: colors.textMuted, fontSize: fontSize.sm, fontFamily: fonts.body },
  error: { color: colors.danger, fontSize: fontSize.sm, fontFamily: fonts.bodyMedium },
  warn: { color: colors.energyDark, fontSize: fontSize.xs, fontFamily: fonts.bodyMedium },

  advToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: colors.bgTint,
    borderRadius: radius.lg,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
  },
  advToggleText: { fontFamily: fonts.bodyBold, fontSize: fontSize.sm, color: colors.brand },
  advBody: { gap: spacing.lg },

  toggleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: spacing.md,
    paddingVertical: spacing.xs,
  },
  toggleLabel: { flex: 1, fontFamily: fonts.bodyMedium, fontSize: fontSize.sm, color: colors.text },
});
