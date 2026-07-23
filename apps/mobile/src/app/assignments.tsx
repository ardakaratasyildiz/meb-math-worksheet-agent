import { useAuth, useUser } from '@clerk/expo';
import { Stack, useRouter, type Href } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
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

import { IconChevron } from '@/components/icons';
import { Mascot } from '@/components/mascot';
import { Card, PrimaryButton } from '@/components/ui';
import {
  getAssignmentWorksheet,
  joinClassroom,
  listClassrooms,
  listMyAssignments,
  type ClassroomSummary,
  type MyAssignmentItem,
} from '@/lib/api';
import { shareWorksheetPdf } from '@/lib/pdf';
import { colors, fonts, fontSize, radius, spacing } from '@/theme/tokens';

const headerOpts = {
  headerShown: true,
  title: 'Ödevlerim',
  headerStyle: { backgroundColor: colors.bg },
  headerShadowVisible: false,
  headerTintColor: colors.brand,
  headerTitleStyle: { fontFamily: fonts.headingSemi, color: colors.text },
} as const;

export default function AssignmentsScreen() {
  const { userId } = useAuth();
  const { user } = useUser();
  const router = useRouter();

  const [items, setItems] = useState<MyAssignmentItem[]>([]);
  const [enrolled, setEnrolled] = useState<ClassroomSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [code, setCode] = useState('');
  const [name, setName] = useState(user?.firstName ?? '');
  const [joining, setJoining] = useState(false);
  const [joinError, setJoinError] = useState<string | null>(null);
  const [sharing, setSharing] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    setError(null);
    try {
      const [asg, classes] = await Promise.all([
        listMyAssignments(userId),
        listClassrooms(userId).catch(() => ({ teaching: [], enrolled: [] })),
      ]);
      setItems(asg);
      setEnrolled(classes.enrolled);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    void load();
  }, [load]);

  const onJoin = useCallback(async () => {
    if (!userId || joining || code.trim().length < 4 || name.trim().length < 1) return;
    setJoining(true);
    setJoinError(null);
    try {
      await joinClassroom(userId, code.trim(), name.trim());
      setCode('');
      await load();
    } catch (e) {
      setJoinError((e as Error).message);
    } finally {
      setJoining(false);
    }
  }, [userId, joining, code, name, load]);

  const onOpen = useCallback(
    async (a: MyAssignmentItem) => {
      if (a.assignment_type === 'pdf') {
        if (!userId || sharing) return;
        setSharing(a.assignment_id);
        setError(null);
        try {
          const ws = await getAssignmentWorksheet(a.assignment_id, userId);
          await shareWorksheetPdf(ws, { includeAnswerKey: false, includeSolutions: false });
        } catch (e) {
          setError((e as Error).message);
        } finally {
          setSharing(null);
        }
      } else {
        router.push(
          `/solve-assignment/${encodeURIComponent(a.assignment_id)}?title=${encodeURIComponent(a.title)}` as Href,
        );
      }
    },
    [userId, sharing, router],
  );

  return (
    <View style={styles.root}>
      <Stack.Screen options={headerOpts} />
      <SafeAreaView style={styles.safe} edges={['bottom']}>
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          {/* Sınıfa katıl */}
          <Card style={styles.joinCard}>
            <Text style={styles.joinTitle}>Sınıfa katıl</Text>
            <Text style={styles.joinSub}>Öğretmeninin verdiği katılma kodunu gir.</Text>
            <TextInput
              style={styles.input}
              placeholder="Katılma kodu"
              placeholderTextColor={colors.textFaint}
              autoCapitalize="characters"
              value={code}
              onChangeText={setCode}
            />
            <TextInput
              style={styles.input}
              placeholder="Görünen adın (öğretmenin görür)"
              placeholderTextColor={colors.textFaint}
              value={name}
              onChangeText={setName}
              maxLength={80}
            />
            {joinError ? <Text style={styles.error}>{joinError}</Text> : null}
            <PrimaryButton
              label="Katıl"
              busy={joining}
              disabled={code.trim().length < 4 || name.trim().length < 1}
              onPress={onJoin}
            />
          </Card>

          {enrolled.length > 0 ? (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Katıldığın sınıflar</Text>
              {enrolled.map((c) => (
                <Pressable
                  key={c.id}
                  onPress={() => router.push(`/classroom/${encodeURIComponent(c.id)}` as Href)}
                  style={({ pressed }) => [styles.row, pressed && styles.pressed]}
                >
                  <View style={styles.rowBody}>
                    <Text style={styles.rowTitle} numberOfLines={1}>
                      {c.name}
                    </Text>
                    <Text style={styles.rowMeta}>{c.member_count} öğrenci</Text>
                  </View>
                  <IconChevron size={16} color={colors.textFaint} />
                </Pressable>
              ))}
            </View>
          ) : null}

          {loading ? (
            <ActivityIndicator style={{ marginTop: spacing.xl }} color={colors.brand} />
          ) : error ? (
            <Text style={styles.error}>{error}</Text>
          ) : items.length === 0 ? (
            <View style={styles.empty}>
              <Mascot variant="reading" size={104} />
              <Text style={styles.emptyText}>Henüz ödevin yok. Bir sınıfa katılınca ödevler burada görünür.</Text>
            </View>
          ) : (
            <View style={styles.list}>
              {items.map((a) => {
                const busy = sharing === a.assignment_id;
                return (
                  <Pressable
                    key={a.assignment_id}
                    onPress={() => void onOpen(a)}
                    disabled={busy}
                    style={({ pressed }) => [styles.row, pressed && styles.pressed]}
                  >
                    <View style={styles.rowBody}>
                      <Text style={styles.rowTitle} numberOfLines={1}>
                        {a.title}
                      </Text>
                      <Text style={styles.rowMeta} numberOfLines={1}>
                        {a.classroom_name} · {a.assignment_type === 'pdf' ? 'PDF' : 'Quiz'}
                      </Text>
                    </View>
                    {a.solved ? (
                      <View style={styles.donePill}>
                        <Text style={styles.donePillText}>
                          {a.score}/{a.total}
                        </Text>
                      </View>
                    ) : busy ? (
                      <ActivityIndicator color={colors.brand} />
                    ) : (
                      <View style={styles.todoPill}>
                        <Text style={styles.todoPillText}>{a.assignment_type === 'pdf' ? 'İndir' : 'Çöz'}</Text>
                      </View>
                    )}
                    <IconChevron size={16} color={colors.textFaint} />
                  </Pressable>
                );
              })}
            </View>
          )}
        </ScrollView>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  safe: { flex: 1 },
  content: { padding: spacing.xl, gap: spacing.lg },
  joinCard: { gap: spacing.md },
  joinTitle: { fontFamily: fonts.heading, fontSize: fontSize.lg, color: colors.text },
  joinSub: { fontFamily: fonts.body, fontSize: fontSize.sm, color: colors.textMuted, marginTop: -spacing.xs },
  input: {
    borderRadius: radius.lg,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    fontSize: fontSize.md,
    fontFamily: fonts.bodyMedium,
    color: colors.text,
    backgroundColor: colors.bgTint,
  },
  error: { color: colors.danger, fontSize: fontSize.sm, fontFamily: fonts.bodyMedium },
  empty: { alignItems: 'center', gap: spacing.md, paddingVertical: spacing.xl },
  emptyText: { fontFamily: fonts.body, fontSize: fontSize.md, color: colors.textMuted, textAlign: 'center' },
  section: { gap: spacing.sm },
  sectionTitle: { fontFamily: fonts.bodyHeavy, fontSize: fontSize.sm, color: colors.textMuted, letterSpacing: 0.3 },
  list: { gap: spacing.sm },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.card,
    padding: spacing.lg,
  },
  pressed: { opacity: 0.9, transform: [{ scale: 0.99 }] },
  rowBody: { flex: 1 },
  rowTitle: { fontFamily: fonts.bodyBold, fontSize: fontSize.md, color: colors.text },
  rowMeta: { fontFamily: fonts.body, fontSize: fontSize.xs, color: colors.textMuted, marginTop: 1 },
  donePill: { backgroundColor: colors.tintGreen, borderRadius: radius.pill, paddingHorizontal: spacing.md, paddingVertical: 4 },
  donePillText: { fontFamily: fonts.bodyHeavy, fontSize: fontSize.sm, color: colors.success },
  todoPill: { backgroundColor: colors.tintBlue, borderRadius: radius.pill, paddingHorizontal: spacing.md, paddingVertical: 4 },
  todoPillText: { fontFamily: fonts.bodyBold, fontSize: fontSize.xs, color: colors.brand },
});
