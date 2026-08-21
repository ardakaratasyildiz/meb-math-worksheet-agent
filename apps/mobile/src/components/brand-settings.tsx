import * as ImagePicker from 'expo-image-picker';
import { useCallback, useEffect, useState } from 'react';
import { Image, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import {
  EMPTY_BRANDING,
  MAX_LOGO_CHARS,
  loadBranding,
  saveBranding,
  type Branding,
} from '@/lib/branding';
import { colors, fonts, fontSize, radius, spacing } from '@/theme/tokens';

/**
 * PDF üst bilgisine kurum/öğretmen markası (ad + alt satır + logo).
 *
 * Backend `render.pdf` bunu zaten destekliyordu ve ücretli plan kapısı SUNUCUDA
 * (`has_paid_access` → ücretsizde alanlar yok sayılır). Web'de arayüz vardı,
 * mobilde YOKTU → "Filigransız PDF — kendi logonuzu ekleyin" vaadi mobilde
 * karşılıksız kalıyordu (2026-08-21 plan denetimi).
 *
 * Ayarlar cihazda saklanır (lib/branding.ts) → kullanıcı bir kez girer, her
 * kağıtta otomatik uygulanır. `paid=false` iken bölüm yine görünür ama neden
 * uygulanmadığı yazılır — gizlemek "logo nerede" sorusuna yol açıyor.
 */
export function BrandSettings({
  paid,
  onChange,
}: {
  /** Ücretli plan mı (gösterim amaçlı; asıl kapı sunucuda). */
  paid: boolean;
  /** Her değişiklikte üst bileşene bildir → PDF isteğine geçsin. */
  onChange: (b: Branding) => void;
}) {
  const [brand, setBrand] = useState<Branding>(EMPTY_BRANDING);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    void loadBranding().then((b) => {
      setBrand(b);
      onChange(b);
    });
    // onChange kimliği her render'da değişebilir → yalnız ilk açılışta oku.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const update = useCallback(
    (patch: Partial<Branding>) => {
      setBrand((prev) => {
        const next = { ...prev, ...patch };
        void saveBranding(next);
        onChange(next);
        return next;
      });
    },
    [onChange],
  );

  const pickLogo = useCallback(async () => {
    setErr(null);
    setBusy(true);
    try {
      // iOS'ta kütüphane izni istenmeli; reddedilirse seçici hiç açılmaz.
      const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!perm.granted) {
        setErr('Logo seçmek için galeri izni gerekiyor.');
        return;
      }
      const res = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        allowsEditing: true,
        aspect: [1, 1],
        // Kalite düşürülüyor: logo üst bilgide ~1 cm basılıyor, tam kalite
        // gövde tavanını (render.pdf 8 MB) boşa harcar.
        quality: 0.7,
        base64: true,
      });
      if (res.canceled || !res.assets?.length) return;
      const a = res.assets[0];
      if (!a.base64) {
        setErr('Görsel okunamadı, başka bir dosya dener misin?');
        return;
      }
      const dataUri = a.base64.startsWith('data:')
        ? a.base64
        : `data:image/jpeg;base64,${a.base64}`;
      if (dataUri.length > MAX_LOGO_CHARS) {
        // Sessizce kırpmak "logom neden bozuk" sorusuna yol açar → açıkça söyle.
        setErr('Görsel çok büyük. Daha küçük bir logo (kare, ~500 px) seç.');
        return;
      }
      update({ logo: dataUri });
    } catch {
      setErr('Logo seçilemedi.');
    } finally {
      setBusy(false);
    }
  }, [update]);

  return (
    <View style={styles.field}>
      <Text style={styles.fieldLabel}>PDF markası</Text>
      <Text style={styles.hint}>
        Kağıdın üstünde kurum/öğretmen adın ve logon görünür.
      </Text>

      <TextInput
        style={styles.input}
        placeholder="Kurum / öğretmen adı"
        placeholderTextColor={colors.textFaint}
        value={brand.name}
        maxLength={80}
        onChangeText={(t) => update({ name: t })}
      />
      <TextInput
        style={styles.input}
        placeholder="Alt satır (şube, ders, iletişim)"
        placeholderTextColor={colors.textFaint}
        value={brand.subtitle}
        maxLength={60}
        onChangeText={(t) => update({ subtitle: t })}
      />

      <View style={styles.logoRow}>
        {brand.logo ? (
          <Image source={{ uri: brand.logo }} style={styles.logoPreview} resizeMode="contain" />
        ) : (
          <View style={[styles.logoPreview, styles.logoEmpty]}>
            <Text style={styles.logoEmptyText}>logo</Text>
          </View>
        )}
        <View style={styles.logoBtns}>
          <Pressable
            onPress={pickLogo}
            disabled={busy}
            style={({ pressed }) => [styles.btn, pressed && styles.pressed]}
          >
            <Text style={styles.btnText}>{brand.logo ? 'Logoyu değiştir' : 'Logo seç'}</Text>
          </Pressable>
          {brand.logo ? (
            <Pressable
              onPress={() => update({ logo: '' })}
              style={({ pressed }) => [styles.btnGhost, pressed && styles.pressed]}
            >
              <Text style={styles.btnGhostText}>Kaldır</Text>
            </Pressable>
          ) : null}
        </View>
      </View>

      {err ? <Text style={styles.err}>{err}</Text> : null}
      {!paid ? (
        <Text style={styles.hint}>
          Marka yalnız abonelikte PDF&apos;e basılır. Ayarların kaydedilir, Pro&apos;ya
          geçtiğinde otomatik uygulanır.
        </Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  field: { gap: spacing.sm },
  fieldLabel: { fontFamily: fonts.bodyBold, fontSize: fontSize.sm, color: colors.text },
  hint: { fontFamily: fonts.body, fontSize: fontSize.xs, color: colors.textMuted },
  input: {
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    fontSize: fontSize.sm,
    fontFamily: fonts.body,
    color: colors.text,
    backgroundColor: colors.bgTint,
  },
  logoRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  logoPreview: {
    width: 56,
    height: 56,
    borderRadius: radius.md,
    backgroundColor: colors.bgTint,
  },
  logoEmpty: { alignItems: 'center', justifyContent: 'center' },
  logoEmptyText: { fontFamily: fonts.body, fontSize: fontSize.xs, color: colors.textFaint },
  logoBtns: { flex: 1, gap: spacing.xs },
  btn: {
    borderRadius: radius.md,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    backgroundColor: colors.tintBlue,
    alignItems: 'center',
  },
  btnText: { fontFamily: fonts.bodyBold, fontSize: fontSize.sm, color: colors.brand },
  btnGhost: { paddingVertical: spacing.xs, alignItems: 'center' },
  btnGhostText: { fontFamily: fonts.body, fontSize: fontSize.xs, color: colors.textMuted },
  pressed: { opacity: 0.7 },
  err: { fontFamily: fonts.body, fontSize: fontSize.xs, color: colors.danger },
});
