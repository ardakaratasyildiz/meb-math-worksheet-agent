import { Stack } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { Linking, Pressable, ScrollView, StyleSheet, Switch, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Mascot } from '@/components/mascot';
import { Card, PrimaryButton } from '@/components/ui';
import {
  DEFAULT_HOUR,
  DEFAULT_MINUTE,
  REMINDER_SLOTS,
  getPermissionState,
  getReminderPrefs,
  notificationsSupported,
  setReminder,
  type PermissionState,
} from '@/lib/notifications';
import { colors, fonts, fontSize, radius, spacing } from '@/theme/tokens';

/**
 * Bildirim ayarları — çandan ve profildeki "Bildirimler" satırından açılır.
 *
 * Faz 1: yalnız CİHAZDA planlanan günlük çalışma hatırlatması (sunucu/push YOK).
 * Kullanıcıya ne göndereceğimizi açıkça yazıyoruz — izin isteme ekranı boş bir
 * sistem uyarısı olarak gelmesin, ne için izin verdiğini bilsin.
 */

const headerOpts = {
  headerShown: true,
  title: 'Bildirimler',
  headerStyle: { backgroundColor: colors.bg },
  headerShadowVisible: false,
  headerTintColor: colors.brand,
  headerTitleStyle: { fontFamily: fonts.headingSemi, color: colors.text },
} as const;

export default function NotificationsScreen() {
  const supported = notificationsSupported();
  const [enabled, setEnabled] = useState(false);
  const [hour, setHour] = useState(DEFAULT_HOUR);
  const [minute, setMinute] = useState(DEFAULT_MINUTE);
  const [permission, setPermission] = useState<PermissionState>('undetermined');
  const [busy, setBusy] = useState(false);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    void (async () => {
      const [prefs, perm] = await Promise.all([getReminderPrefs(), getPermissionState()]);
      setEnabled(prefs.enabled === true);
      setHour(prefs.hour);
      setMinute(prefs.minute);
      setPermission(perm);
      setLoaded(true);
    })();
  }, []);

  const apply = useCallback(
    async (next: boolean, h: number, m: number) => {
      setBusy(true);
      // İyimser güncelleme: anahtar anında dönsün, sonuç gelince gerçekle düzeltilir.
      setEnabled(next);
      setHour(h);
      setMinute(m);
      const actual = await setReminder(next, h, m);
      setEnabled(actual);
      setPermission(await getPermissionState());
      setBusy(false);
    },
    [],
  );

  // İzin sistem ayarlarından kapatılmışsa uygulama içinden açılamaz — Ayarlar'a yolla.
  const blocked = permission === 'denied';

  return (
    <View style={styles.root}>
      <Stack.Screen options={headerOpts} />
      <SafeAreaView style={styles.safe} edges={['bottom']}>
        <ScrollView contentContainerStyle={styles.content}>
          <Card floating style={styles.hero}>
            <Mascot variant="happy" size={64} />
            <View style={styles.heroText}>
              <Text style={styles.heroTitle}>Serini koruyalım</Text>
              <Text style={styles.heroSub}>
                Günde bir kez, seçtiğin saatte kısa bir hatırlatma göndeririz. Başka hiçbir
                şey için bildirim atmayız.
              </Text>
            </View>
          </Card>

          {!supported ? (
            <Card>
              <Text style={styles.note}>
                Bildirimler uygulamanın mağaza sürümünde çalışır. Şu anki ortamda
                planlama yapılamıyor.
              </Text>
            </Card>
          ) : null}

          <Card style={styles.card}>
            <View style={styles.row}>
              <View style={styles.rowText}>
                <Text style={styles.rowTitle}>Günlük çalışma hatırlatması</Text>
                <Text style={styles.rowSub}>
                  {enabled ? `Her gün ${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}` : 'Kapalı'}
                </Text>
              </View>
              <Switch
                value={enabled}
                disabled={!supported || busy || blocked || !loaded}
                onValueChange={(v) => void apply(v, hour, minute)}
                trackColor={{ true: colors.brand, false: colors.track }}
                thumbColor="#FFFFFF"
              />
            </View>

            {enabled ? (
              <>
                <View style={styles.divider} />
                <Text style={styles.slotsLabel}>Saat</Text>
                <View style={styles.slots}>
                  {REMINDER_SLOTS.map((s) => {
                    const active = s.hour === hour && s.minute === minute;
                    return (
                      <Pressable
                        key={s.label}
                        disabled={busy}
                        onPress={() => void apply(true, s.hour, s.minute)}
                        style={[styles.slot, active && styles.slotActive]}
                      >
                        <Text style={[styles.slotText, active && styles.slotTextActive]}>
                          {s.label}
                        </Text>
                      </Pressable>
                    );
                  })}
                </View>
              </>
            ) : null}
          </Card>

          {blocked ? (
            <Card style={styles.blockedCard}>
              <Text style={styles.blockedTitle}>Bildirim izni kapalı</Text>
              <Text style={styles.blockedText}>
                Hatırlatma gönderebilmemiz için cihaz ayarlarından Soru Atölyesi
                bildirimlerine izin vermen gerekiyor.
              </Text>
              <PrimaryButton
                label="Ayarları aç"
                variant="soft"
                onPress={() => void Linking.openSettings()}
              />
            </Card>
          ) : null}

          <Text style={styles.footnote}>
            Hatırlatma cihazında planlanır; kapattığında hemen durur. Ödev ve deneme
            bildirimleri ilerleyen sürümlerde eklenecek.
          </Text>
        </ScrollView>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  safe: { flex: 1 },
  content: { padding: spacing.xl, gap: spacing.lg, paddingBottom: spacing.xxl },

  hero: { flexDirection: 'row', alignItems: 'center', gap: spacing.lg, backgroundColor: colors.tintBlue },
  heroText: { flex: 1, gap: 4 },
  heroTitle: { fontFamily: fonts.heading, fontSize: fontSize.lg, color: colors.text },
  heroSub: { fontFamily: fonts.body, fontSize: fontSize.sm, color: colors.textMuted },

  card: { gap: spacing.md },
  row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: spacing.md },
  rowText: { flex: 1, gap: 2 },
  rowTitle: { fontFamily: fonts.bodyBold, fontSize: fontSize.md, color: colors.text },
  rowSub: { fontFamily: fonts.body, fontSize: fontSize.sm, color: colors.textMuted },
  divider: { height: 1, backgroundColor: colors.track },

  slotsLabel: { fontFamily: fonts.bodyMedium, fontSize: fontSize.sm, color: colors.textMuted },
  slots: { flexDirection: 'row', gap: spacing.sm, flexWrap: 'wrap' },
  slot: {
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    borderRadius: radius.pill,
    backgroundColor: colors.tintBlue,
  },
  slotActive: { backgroundColor: colors.brand },
  slotText: { fontFamily: fonts.bodyMedium, fontSize: fontSize.sm, color: colors.brandDark },
  slotTextActive: { color: '#FFFFFF' },

  blockedCard: { gap: spacing.md, backgroundColor: colors.tintYellow },
  blockedTitle: { fontFamily: fonts.bodyBold, fontSize: fontSize.md, color: colors.text },
  blockedText: { fontFamily: fonts.body, fontSize: fontSize.sm, color: colors.textMuted },

  note: { fontFamily: fonts.body, fontSize: fontSize.sm, color: colors.textMuted },
  footnote: {
    fontFamily: fonts.body,
    fontSize: fontSize.xs,
    color: colors.textFaint,
    textAlign: 'center',
    lineHeight: 17,
  },
});
