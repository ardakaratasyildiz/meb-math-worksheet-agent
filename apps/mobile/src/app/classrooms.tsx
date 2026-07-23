import { useAuth } from '@clerk/expo';
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

import { IconChevron, IconUser } from '@/components/icons';
import { Mascot } from '@/components/mascot';
import { Card, PrimaryButton } from '@/components/ui';
import { createClassroom, listClassrooms, type ClassroomSummary } from '@/lib/api';
import { colors, fonts, fontSize, radius, spacing } from '@/theme/tokens';

const headerOpts = {
  headerShown: true,
  title: 'Sınıflarım',
  headerStyle: { backgroundColor: colors.bg },
  headerShadowVisible: false,
  headerTintColor: colors.brand,
  headerTitleStyle: { fontFamily: fonts.headingSemi, color: colors.text },
} as const;

export default function ClassroomsScreen() {
  const { userId } = useAuth();
  const router = useRouter();
  const [teaching, setTeaching] = useState<ClassroomSummary[]>([]);
  const [enrolled, setEnrolled] = useState<ClassroomSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState('');
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    setError(null);
    try {
      const r = await listClassrooms(userId);
      setTeaching(r.teaching);
      setEnrolled(r.enrolled);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    void load();
  }, [load]);

  const onCreate = useCallback(async () => {
    if (!userId || creating || name.trim().length < 1) return;
    setCreating(true);
    setCreateError(null);
    try {
      await createClassroom(userId, name.trim());
      setName('');
      await load();
    } catch (e) {
      setCreateError((e as Error).message);
    } finally {
      setCreating(false);
    }
  }, [userId, creating, name, load]);

  const openClass = (id: string) => () => router.push(`/classroom/${encodeURIComponent(id)}` as Href);

  return (
    <View style={styles.root}>
      <Stack.Screen options={headerOpts} />
      <SafeAreaView style={styles.safe} edges={['bottom']}>
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          {/* Sınıf oluştur */}
          <Card style={styles.addCard}>
            <Text style={styles.addTitle}>Yeni sınıf oluştur</Text>
            <TextInput
              style={styles.input}
              placeholder="Sınıf adı (ör. 5-A Matematik)"
              placeholderTextColor={colors.textFaint}
              value={name}
              onChangeText={setName}
              maxLength={80}
            />
            {createError ? <Text style={styles.error}>{createError}</Text> : null}
            <PrimaryButton label="Oluştur" busy={creating} disabled={name.trim().length < 1} onPress={onCreate} />
          </Card>

          {loading ? (
            <ActivityIndicator style={{ marginTop: spacing.xl }} color={colors.brand} />
          ) : error ? (
            <Text style={styles.error}>{error}</Text>
          ) : teaching.length === 0 && enrolled.length === 0 ? (
            <View style={styles.empty}>
              <Mascot variant="wave" size={104} />
              <Text style={styles.emptyText}>Henüz sınıfın yok. Yukarıdan bir tane oluştur.</Text>
            </View>
          ) : (
            <>
              {teaching.length > 0 && (
                <View style={styles.section}>
                  <Text style={styles.sectionTitle}>Öğrettiğin sınıflar</Text>
                  {teaching.map((c) => (
                    <ClassRow key={c.id} c={c} onPress={openClass(c.id)} />
                  ))}
                </View>
              )}
              {enrolled.length > 0 && (
                <View style={styles.section}>
                  <Text style={styles.sectionTitle}>Katıldığın sınıflar</Text>
                  {enrolled.map((c) => (
                    <ClassRow key={c.id} c={c} onPress={openClass(c.id)} />
                  ))}
                </View>
              )}
            </>
          )}
        </ScrollView>
      </SafeAreaView>
    </View>
  );
}

function ClassRow({ c, onPress }: { c: ClassroomSummary; onPress: () => void }) {
  return (
    <Pressable onPress={onPress} style={({ pressed }) => [styles.row, pressed && styles.pressed]}>
      <View style={styles.rowIcon}>
        <IconUser size={24} color={colors.brand} />
      </View>
      <View style={styles.rowBody}>
        <Text style={styles.rowName} numberOfLines={1}>
          {c.name}
        </Text>
        <Text style={styles.rowMeta}>{c.member_count} öğrenci</Text>
      </View>
      <IconChevron size={18} color={colors.textFaint} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  safe: { flex: 1 },
  content: { padding: spacing.xl, gap: spacing.lg },
  addCard: { gap: spacing.md },
  addTitle: { fontFamily: fonts.bodyHeavy, fontSize: fontSize.md, color: colors.text },
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
  rowIcon: { width: 44, height: 44, borderRadius: radius.md, backgroundColor: colors.tintBlue, alignItems: 'center', justifyContent: 'center' },
  rowBody: { flex: 1 },
  rowName: { fontFamily: fonts.bodyBold, fontSize: fontSize.md, color: colors.text },
  rowMeta: { fontFamily: fonts.body, fontSize: fontSize.xs, color: colors.textMuted, marginTop: 1 },
});
