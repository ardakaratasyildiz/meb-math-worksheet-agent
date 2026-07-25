import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Modal, Pressable, Share, StyleSheet, Text, View } from 'react-native';
import QRCode from 'react-native-qrcode-svg';

import { IconSpark } from '@/components/icons';
import { PrimaryButton } from '@/components/ui';
import { createShare, WEB_ORIGIN } from '@/lib/api';
import { colors, fonts, fontSize, radius, spacing } from '@/theme/tokens';

const SHARE_TEXT = 'Bu testi çözebilir misin? 👇 (giriş gerekmez)';

/**
 * Quiz paylaşım sayfası (alt-sayfa modal): createShare → tam URL + QR + native paylaş.
 * Paylaşılan link login'siz çözülür (/q/{code}) — viral döngü buradan başlar.
 */
export function ShareSheet({
  quizId,
  tenantId,
  visible,
  onClose,
}: {
  quizId: string | null;
  tenantId: string | null;
  visible: boolean;
  onClose: () => void;
}) {
  const [url, setUrl] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const create = useCallback(async () => {
    if (!tenantId || !quizId) return;
    setBusy(true);
    setError(null);
    try {
      const r = await createShare(quizId, tenantId);
      setUrl(`${WEB_ORIGIN}${r.share_url}`);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }, [quizId, tenantId]);

  // Modal açılınca (ve link henüz yoksa) paylaşımı oluştur.
  useEffect(() => {
    if (visible && !url && !busy) void create();
  }, [visible, url, busy, create]);

  const share = useCallback(async () => {
    if (!url) return;
    try {
      await Share.share({ message: `${SHARE_TEXT} ${url}` });
    } catch {
      /* kullanıcı iptal etti — sessiz */
    }
  }, [url]);

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <Pressable style={styles.backdrop} onPress={onClose}>
        <Pressable style={styles.sheet} onPress={() => {}}>
          <View style={styles.handle} />
          <Text style={styles.title}>Testi paylaş</Text>
          <Text style={styles.sub}>Arkadaşların linkle ya da QR ile çözsün — giriş gerekmez.</Text>

          {busy ? (
            <View style={styles.center}>
              <ActivityIndicator size="large" color={colors.brand} />
              <Text style={styles.muted}>Paylaşım linki hazırlanıyor…</Text>
            </View>
          ) : error ? (
            <View style={styles.center}>
              <Text style={styles.error}>{error}</Text>
              <PrimaryButton label="Tekrar dene" variant="soft" onPress={() => void create()} />
            </View>
          ) : url ? (
            <>
              <View style={styles.qrWrap}>
                <QRCode value={url} size={180} color={colors.text} backgroundColor="#FFFFFF" />
              </View>
              <Text style={styles.url} numberOfLines={2}>
                {url}
              </Text>
              <PrimaryButton
                label="Paylaş"
                onPress={() => void share()}
                icon={<IconSpark size={20} />}
              />
            </>
          ) : null}

          <PrimaryButton label="Kapat" variant="soft" color={colors.textMuted} onPress={onClose} />
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, backgroundColor: 'rgba(0,0,0,0.4)', justifyContent: 'flex-end' },
  sheet: {
    backgroundColor: colors.bg,
    borderTopLeftRadius: radius.hero,
    borderTopRightRadius: radius.hero,
    padding: spacing.xl,
    gap: spacing.md,
    alignItems: 'center',
  },
  handle: { width: 40, height: 4, borderRadius: 2, backgroundColor: colors.border, marginBottom: spacing.sm },
  title: { fontFamily: fonts.heading, fontSize: fontSize.xl, color: colors.text },
  sub: { fontFamily: fonts.body, fontSize: fontSize.sm, color: colors.textMuted, textAlign: 'center' },
  center: { alignItems: 'center', gap: spacing.md, paddingVertical: spacing.lg },
  muted: { fontFamily: fonts.body, fontSize: fontSize.sm, color: colors.textMuted },
  error: { fontFamily: fonts.bodyMedium, fontSize: fontSize.sm, color: colors.danger, textAlign: 'center' },
  qrWrap: {
    backgroundColor: '#FFFFFF',
    padding: spacing.lg,
    borderRadius: radius.card,
    marginTop: spacing.sm,
  },
  url: {
    fontFamily: fonts.body,
    fontSize: fontSize.xs,
    color: colors.brand,
    textAlign: 'center',
    paddingHorizontal: spacing.lg,
  },
});
