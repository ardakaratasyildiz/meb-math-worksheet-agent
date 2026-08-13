import { useAuth } from '@clerk/expo';
import { Stack, useRouter, type Href } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Mascot } from '@/components/mascot';
import { SkeletonList } from '@/components/skeleton';
import {
  deleteWorksheetHistoryItem,
  listAttempts,
  listWorksheetHistory,
  type AttemptHistoryItem,
  type WorksheetHistoryItem,
} from '@/lib/api';
import { shareWorksheetPdf } from '@/lib/pdf';
import { formatDate, scorePct, scoreTone } from '@/lib/format';
import { colors, fonts, fontSize, radius, spacing } from '@/theme/tokens';

const TONE: Record<'good' | 'mid' | 'low', string> = {
  good: colors.success,
  mid: '#d97706',
  low: colors.danger,
};

type Tab = 'quiz' | 'sheet';

/**
 * Geçmişim — iki sekme: çözülen QUİZLER ve üretilen ÇALIŞMA KAĞITLARI.
 *
 * Kağıt geçmişi backend'de vardı (`/api/worksheets/history`) ama mobilde ucu yoktu;
 * kullanıcı ürettiği PDF'e bir daha ulaşamıyordu. Kayıt kağıdın TAMAMINI taşıdığı
 * için PDF yeniden üretilebiliyor — model çağrısı yok, yani kota/maliyet harcamıyor.
 */
export default function HistoryScreen() {
  const { userId } = useAuth();
  const router = useRouter();
  const [tab, setTab] = useState<Tab>('quiz');
  const [items, setItems] = useState<AttemptHistoryItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!userId) return;
    setError(null);
    try {
      setItems(await listAttempts(userId));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Geçmiş yüklenemedi.');
      setItems([]);
    }
  }, [userId]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <SafeAreaView style={styles.safe} edges={['bottom']}>
      <Stack.Screen options={{ headerShown: true, title: 'Geçmişim' }} />
      <View style={styles.tabs}>
        <Pressable
          style={[styles.tab, tab === 'quiz' && styles.tabActive]}
          onPress={() => setTab('quiz')}
        >
          <Text style={[styles.tabText, tab === 'quiz' && styles.tabTextActive]}>
            Çözdüğüm quizler
          </Text>
        </Pressable>
        <Pressable
          style={[styles.tab, tab === 'sheet' && styles.tabActive]}
          onPress={() => setTab('sheet')}
        >
          <Text style={[styles.tabText, tab === 'sheet' && styles.tabTextActive]}>
            Çalışma kağıtlarım
          </Text>
        </Pressable>
      </View>

      {tab === 'sheet' ? (
        <WorksheetHistoryList />
      ) : (
      <ScrollView contentContainerStyle={styles.content}>
        {items === null ? (
          <SkeletonList count={5} />
        ) : error ? (
          <Text style={styles.error}>{error}</Text>
        ) : items.length === 0 ? (
          <View style={styles.empty}>
            <Mascot variant="reading" size={128} />
            <Text style={styles.emptyTitle}>Henüz çözülmüş quiz yok</Text>
            <Text style={styles.emptyText}>
              Bir alıştırma çözünce buraya düşer; geçmişini tek tek gözden geçirebilirsin.
            </Text>
            <Pressable
              style={styles.cta}
              onPress={() => router.push('/create' as Href)}
            >
              <Text style={styles.ctaText}>✏️ Alıştırma Çöz</Text>
            </Pressable>
          </View>
        ) : (
          items.map((a) => {
            const pct = scorePct(a.score, a.total);
            const tone = TONE[scoreTone(pct)];
            return (
              <Pressable
                key={a.attempt_id}
                style={({ pressed }) => [styles.card, pressed && styles.cardPressed]}
                onPress={() => router.push(`/attempt/${a.attempt_id}` as Href)}
              >
                <View style={styles.cardMain}>
                  <Text style={styles.cardTitle} numberOfLines={1}>
                    {a.title}
                  </Text>
                  <Text style={styles.cardMeta}>
                    {a.grade ? `${a.grade}. sınıf · ` : ''}
                    {a.difficulty} · {formatDate(a.completed_at)}
                  </Text>
                </View>
                <View style={styles.scorePill}>
                  <Text style={[styles.scoreNum, { color: tone }]}>
                    {a.score}/{a.total}
                  </Text>
                  <Text style={[styles.scorePct, { color: tone }]}>%{pct}</Text>
                </View>
              </Pressable>
            );
          })
        )}
      </ScrollView>
      )}
    </SafeAreaView>
  );
}

/** Üretilen çalışma kağıtları — dokununca PDF önizleme / paylaşım. */
function WorksheetHistoryList() {
  const { userId } = useAuth();
  const router = useRouter();
  const [items, setItems] = useState<WorksheetHistoryItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!userId) return;
    setError(null);
    try {
      setItems(await listWorksheetHistory(userId));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Geçmiş yüklenemedi.');
      setItems([]);
    }
  }, [userId]);

  useEffect(() => {
    void load();
  }, [load]);

  const share = useCallback(async (item: WorksheetHistoryItem) => {
    setBusyId(item.id);
    setError(null);
    try {
      // Kayıt tam kağıdı taşıyor → PDF yeniden ÜRETİLMEZ, yeniden ÇİZİLİR (maliyet yok).
      await shareWorksheetPdf(item.response.worksheet);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'PDF hazırlanamadı.');
    } finally {
      setBusyId(null);
    }
  }, []);

  const remove = useCallback(
    async (item: WorksheetHistoryItem) => {
      if (!userId) return;
      setBusyId(item.id);
      try {
        await deleteWorksheetHistoryItem(item.id, userId);
        setItems((prev) => (prev ?? []).filter((i) => i.id !== item.id));
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Silinemedi.');
      } finally {
        setBusyId(null);
      }
    },
    [userId],
  );

  if (items === null) {
    return (
      <ScrollView contentContainerStyle={styles.content}>
        <SkeletonList count={5} />
      </ScrollView>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.content}>
      {error ? <Text style={styles.error}>{error}</Text> : null}
      {items.length === 0 ? (
        <View style={styles.empty}>
          <Mascot variant="wave" size={128} />
          <Text style={styles.emptyTitle}>Henüz çalışma kağıdın yok</Text>
          <Text style={styles.emptyText}>
            Ürettiğin kağıtlar burada birikir; PDF'ini istediğin zaman yeniden alabilirsin.
          </Text>
          <Pressable style={styles.cta} onPress={() => router.push('/create' as Href)}>
            <Text style={styles.ctaText}>📄 Çalışma Kağıdı Oluştur</Text>
          </Pressable>
        </View>
      ) : (
        items.map((item) => {
          const w = item.response.worksheet;
          const busy = busyId === item.id;
          return (
            <View key={item.id} style={styles.card}>
              <View style={styles.cardMain}>
                <Text style={styles.cardTitle} numberOfLines={2}>
                  {w.title || w.topic}
                </Text>
                <Text style={styles.cardMeta}>
                  {w.grade}. sınıf · {w.question_count} soru · {formatDate(item.saved_at)}
                </Text>
                <View style={styles.sheetActions}>
                  <Pressable disabled={busy} onPress={() => void share(item)} hitSlop={6}>
                    <Text style={styles.sheetAction}>{busy ? 'Hazırlanıyor…' : 'PDF paylaş'}</Text>
                  </Pressable>
                  <Pressable disabled={busy} onPress={() => void remove(item)} hitSlop={6}>
                    <Text style={styles.sheetDelete}>Sil</Text>
                  </Pressable>
                </View>
              </View>
            </View>
          );
        })
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  content: { padding: spacing.xl, gap: spacing.md, paddingBottom: spacing.xxl },

  tabs: {
    flexDirection: 'row',
    gap: spacing.sm,
    paddingHorizontal: spacing.xl,
    paddingTop: spacing.md,
  },
  tab: {
    flex: 1,
    paddingVertical: spacing.sm,
    borderRadius: radius.pill,
    backgroundColor: colors.bgTint,
    alignItems: 'center',
  },
  tabActive: { backgroundColor: colors.brand },
  tabText: { fontFamily: fonts.bodyMedium, fontSize: fontSize.sm, color: colors.textMuted },
  tabTextActive: { color: '#FFFFFF' },

  sheetActions: { flexDirection: 'row', gap: spacing.lg, marginTop: spacing.sm },
  sheetAction: { fontFamily: fonts.bodyBold, fontSize: fontSize.sm, color: colors.brand },
  sheetDelete: { fontFamily: fonts.bodyMedium, fontSize: fontSize.sm, color: colors.danger },
  error: {
    color: colors.danger,
    fontFamily: fonts.bodyMedium,
    fontSize: fontSize.sm,
    textAlign: 'center',
    marginTop: spacing.xl,
  },
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    padding: spacing.lg,
  },
  cardPressed: { borderColor: colors.brand, backgroundColor: '#eff6ff' },
  cardMain: { flex: 1, gap: 2 },
  cardTitle: { fontSize: fontSize.md, fontFamily: fonts.heading, color: colors.text },
  cardMeta: { fontSize: fontSize.xs, fontFamily: fonts.body, color: colors.textMuted },
  scorePill: { alignItems: 'flex-end' },
  scoreNum: { fontSize: fontSize.md, fontFamily: fonts.bodyHeavy },
  scorePct: { fontSize: fontSize.xs, fontFamily: fonts.bodyMedium },
  empty: { alignItems: 'center', gap: spacing.sm, paddingTop: spacing.xxl },
  emptyTitle: { fontSize: fontSize.lg, fontFamily: fonts.heading, color: colors.text },
  emptyText: {
    fontSize: fontSize.sm,
    fontFamily: fonts.body,
    color: colors.textMuted,
    textAlign: 'center',
  },
  cta: {
    marginTop: spacing.md,
    backgroundColor: colors.success,
    borderRadius: radius.pill,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.xl,
  },
  ctaText: { color: colors.onBrand, fontFamily: fonts.bodyBold, fontSize: fontSize.md },
});
