import { useAuth } from '@clerk/expo';
import { Stack, useLocalSearchParams, useRouter, type Href } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { IconChevron } from '@/components/icons';
import { Card, PrimaryButton } from '@/components/ui';
import {
  assignQuiz,
  deleteClassroom,
  getClassroom,
  leaveClassroom,
  listMyQuizzes,
  type ClassroomDetail,
  type MyQuizItem,
} from '@/lib/api';
import { colors, fonts, fontSize, radius, spacing } from '@/theme/tokens';

export default function ClassroomDetailScreen() {
  const { userId } = useAuth();
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();

  const [detail, setDetail] = useState<ClassroomDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showAssign, setShowAssign] = useState(false);
  const [myQuizzes, setMyQuizzes] = useState<MyQuizItem[] | null>(null);
  const [assigning, setAssigning] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [leaving, setLeaving] = useState(false);

  const load = useCallback(async () => {
    if (!userId || !id) return;
    setLoading(true);
    setError(null);
    try {
      setDetail(await getClassroom(id, userId));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [userId, id]);

  useEffect(() => {
    void load();
  }, [load]);

  const openAssign = useCallback(async () => {
    setShowAssign((v) => !v);
    if (myQuizzes === null && userId) {
      try {
        setMyQuizzes(await listMyQuizzes(userId));
      } catch {
        setMyQuizzes([]);
      }
    }
  }, [myQuizzes, userId]);

  const onAssign = useCallback(
    async (quizId: string) => {
      if (!userId || !id || assigning) return;
      setAssigning(quizId);
      try {
        await assignQuiz(id, userId, quizId);
        setShowAssign(false);
        await load();
      } catch (e) {
        setError((e as Error).message);
      } finally {
        setAssigning(null);
      }
    },
    [userId, id, assigning, load],
  );

  const onDelete = useCallback(async () => {
    if (!userId || !id || deleting) return;
    setDeleting(true);
    try {
      await deleteClassroom(id, userId);
      router.back();
    } catch (e) {
      setError((e as Error).message);
      setDeleting(false);
    }
  }, [userId, id, deleting, router]);

  const onLeave = useCallback(async () => {
    if (!userId || !id || leaving) return;
    setLeaving(true);
    try {
      await leaveClassroom(id, userId);
      router.back();
    } catch (e) {
      setError((e as Error).message);
      setLeaving(false);
    }
  }, [userId, id, leaving, router]);

  return (
    <View style={styles.root}>
      <Stack.Screen
        options={{
          headerShown: true,
          title: detail?.name || 'Sınıf',
          headerStyle: { backgroundColor: colors.bg },
          headerShadowVisible: false,
          headerTintColor: colors.brand,
          headerTitleStyle: { fontFamily: fonts.headingSemi, color: colors.text },
        }}
      />
      <SafeAreaView style={styles.safe} edges={['bottom']}>
        <ScrollView contentContainerStyle={styles.content}>
          {loading ? (
            <ActivityIndicator style={{ marginTop: spacing.xl }} color={colors.brand} />
          ) : error ? (
            <Text style={styles.error}>{error}</Text>
          ) : detail ? (
            <>
              {/* Katılma kodu */}
              {detail.join_code ? (
                <Card style={styles.codeCard}>
                  <Text style={styles.codeLabel}>Katılma kodu</Text>
                  <Text style={styles.code}>{detail.join_code}</Text>
                  <Text style={styles.codeHint}>Öğrenciler bu kodla sınıfa katılır.</Text>
                </Card>
              ) : null}

              {/* Üyeler */}
              <Card>
                <Text style={styles.sectionTitle}>Öğrenciler ({detail.member_count})</Text>
                {detail.members.length === 0 ? (
                  <Text style={styles.muted}>Henüz katılan yok.</Text>
                ) : (
                  <View style={styles.memberList}>
                    {detail.members.map((m) => (
                      <View key={m.student_tenant_id} style={styles.memberRow}>
                        <View style={styles.memberAvatar}>
                          <Text style={styles.memberInitial}>
                            {(m.display_name || '?').charAt(0).toUpperCase()}
                          </Text>
                        </View>
                        <Text style={styles.memberName} numberOfLines={1}>
                          {m.display_name}
                        </Text>
                      </View>
                    ))}
                  </View>
                )}
              </Card>

              {/* Ödevler */}
              <Card>
                <View style={styles.assignHead}>
                  <Text style={styles.sectionTitle}>Ödevler</Text>
                  <Pressable onPress={openAssign} hitSlop={8}>
                    <Text style={styles.assignLink}>{showAssign ? 'Kapat' : '+ Ödev ata'}</Text>
                  </Pressable>
                </View>

                {showAssign ? (
                  <View style={styles.quizPicker}>
                    <Text style={styles.pickerHint}>Ödev atamak için kendi quizlerinden birini seç:</Text>
                    {myQuizzes === null ? (
                      <ActivityIndicator color={colors.brand} />
                    ) : myQuizzes.length === 0 ? (
                      <Text style={styles.muted}>
                        Atanacak quiz yok. Önce Oluştur'dan bir alıştırma (Çöz modu) üret.
                      </Text>
                    ) : (
                      myQuizzes.map((q) => (
                        <Pressable
                          key={q.id}
                          disabled={assigning !== null}
                          onPress={() => void onAssign(q.id)}
                          style={({ pressed }) => [styles.quizRow, pressed && styles.pressed]}
                        >
                          <View style={styles.quizBody}>
                            <Text style={styles.quizTitle} numberOfLines={1}>
                              {q.title}
                            </Text>
                            <Text style={styles.quizMeta}>
                              {q.grade ? `${q.grade}. sınıf · ` : ''}
                              {q.difficulty}
                            </Text>
                          </View>
                          {assigning === q.id ? (
                            <ActivityIndicator color={colors.brand} />
                          ) : (
                            <Text style={styles.assignBtn}>Ata</Text>
                          )}
                        </Pressable>
                      ))
                    )}
                  </View>
                ) : null}

                {detail.assignments.length === 0 ? (
                  <Text style={[styles.muted, { marginTop: spacing.sm }]}>Henüz ödev yok.</Text>
                ) : (
                  <View style={styles.assignList}>
                    {detail.assignments.map((a) => (
                      <Pressable
                        key={a.id}
                        onPress={() => router.push(`/assignment/${encodeURIComponent(a.id)}` as Href)}
                        style={({ pressed }) => [styles.assignRow, pressed && styles.pressed]}
                      >
                        <View style={styles.assignBody}>
                          <Text style={styles.assignTitle} numberOfLines={1}>
                            {a.title}
                          </Text>
                          <Text style={styles.assignMeta}>
                            {a.assignment_type === 'pdf' ? 'PDF' : 'Quiz'} · sonuçları gör
                          </Text>
                        </View>
                        <IconChevron size={16} color={colors.textFaint} />
                      </Pressable>
                    ))}
                  </View>
                )}
              </Card>

              {detail.is_owner ? (
                <PrimaryButton label="Sınıfı sil" variant="soft" color={colors.danger} busy={deleting} onPress={onDelete} />
              ) : (
                <PrimaryButton label="Sınıftan ayrıl" variant="soft" color={colors.danger} busy={leaving} onPress={onLeave} />
              )}
            </>
          ) : null}
        </ScrollView>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  safe: { flex: 1 },
  content: { padding: spacing.xl, gap: spacing.lg },
  error: { color: colors.danger, fontSize: fontSize.sm, fontFamily: fonts.bodyMedium },
  muted: { color: colors.textMuted, fontSize: fontSize.sm, fontFamily: fonts.body },
  sectionTitle: { fontSize: fontSize.lg, fontFamily: fonts.heading, color: colors.text, marginBottom: spacing.md },

  codeCard: { alignItems: 'center', gap: spacing.xs, backgroundColor: colors.tintBlue },
  codeLabel: { fontFamily: fonts.bodyBold, fontSize: fontSize.xs, color: colors.brand, letterSpacing: 0.5, textTransform: 'uppercase' },
  code: { fontFamily: fonts.heading, fontSize: 40, color: colors.brand, letterSpacing: 4 },
  codeHint: { fontFamily: fonts.body, fontSize: fontSize.xs, color: colors.textMuted },

  memberList: { gap: spacing.sm },
  memberRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  memberAvatar: { width: 36, height: 36, borderRadius: 18, backgroundColor: colors.tintBlue, alignItems: 'center', justifyContent: 'center' },
  memberInitial: { fontFamily: fonts.bodyHeavy, fontSize: fontSize.sm, color: colors.brand },
  memberName: { flex: 1, fontFamily: fonts.bodyMedium, fontSize: fontSize.md, color: colors.text },

  assignHead: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: spacing.md },
  assignLink: { fontFamily: fonts.bodyBold, fontSize: fontSize.sm, color: colors.brand },
  quizPicker: { gap: spacing.sm, backgroundColor: colors.bgTint, borderRadius: radius.lg, padding: spacing.md, marginBottom: spacing.md },
  pickerHint: { fontFamily: fonts.body, fontSize: fontSize.xs, color: colors.textMuted },
  quizRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: spacing.md,
  },
  quizBody: { flex: 1 },
  quizTitle: { fontFamily: fonts.bodyBold, fontSize: fontSize.sm, color: colors.text },
  quizMeta: { fontFamily: fonts.body, fontSize: fontSize.xs, color: colors.textMuted, marginTop: 1 },
  assignBtn: { fontFamily: fonts.bodyBold, fontSize: fontSize.sm, color: colors.brand },

  assignList: { gap: spacing.sm },
  assignRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    backgroundColor: colors.bgTint,
    borderRadius: radius.lg,
    padding: spacing.md,
  },
  assignBody: { flex: 1 },
  assignTitle: { fontFamily: fonts.bodyBold, fontSize: fontSize.md, color: colors.text },
  assignMeta: { fontFamily: fonts.body, fontSize: fontSize.xs, color: colors.textMuted, marginTop: 1 },
  pressed: { opacity: 0.9, transform: [{ scale: 0.99 }] },
});
