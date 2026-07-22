import { useUser } from "@clerk/expo";
import { useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { Mascot } from "@/components/mascot";
import { setRole as setRoleOnServer } from "@/lib/api";
import { ROLE_META, type SelectableRole } from "@/lib/roles";
import { colors, fonts, fontSize, radius, spacing } from "@/theme/tokens";

/**
 * Zorunlu rol seçimi (onboarding) — web'deki RoleGate'in mobil karşılığı.
 * Giriş yapmış ama rolü OLMAYAN kullanıcıya atlanamayan tam-ekran seçim gösterir.
 * (tabs)/_layout bunu effectiveRole === null iken render eder; rol dolunca sekmeler açılır.
 *
 * Kalıcılık — iki yönlü (bkz. lib/roles.ts):
 *  1. Client-side `user.update({ unsafeMetadata.role })` — pk_test/Expo Go'da GÜVENİLİR çalışır,
 *     effectiveRole legacy path'ten okur → gate hemen kapanır.
 *  2. Best-effort backend POST /api/me/role — publicMetadata'ya kanonik yazım (28 Tem pk_live
 *     sonrası otoritatif). Dev'de 401 olursa sessizce yutulur; unsafeMetadata fallback taşır.
 */
export function RoleGate() {
  const { user } = useUser();
  const [saving, setSaving] = useState<SelectableRole | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function choose(role: SelectableRole) {
    if (!user || saving) return;
    setSaving(role);
    setError(null);
    try {
      // 1) Client-side yazım (birincil, cihazda güvenilir).
      await user.update({ unsafeMetadata: { ...user.unsafeMetadata, role } });
      // 2) Backend'e kanonik yazım (best-effort; dev'de 401 olabilir → yut).
      await setRoleOnServer(role).catch(() => {});
      // 3) Tazele → effectiveRole dolar → (tabs)/_layout sekmeleri gösterir.
      await user.reload();
    } catch {
      setError("Kaydedilemedi. Bağlantını kontrol edip tekrar dene.");
      setSaving(null);
    }
  }

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.content}>
        <Mascot variant="wave" size={132} style={styles.mascot} />
        <Text style={styles.title}>Hoş geldin! Kimsin?</Text>
        <Text style={styles.subtitle}>
          Sana doğru ekranları göstermemiz için profilini seç.
        </Text>

        {error ? <Text style={styles.error}>{error}</Text> : null}

        <View style={styles.list}>
          {ROLE_META.map((r) => {
            const busy = saving === r.value;
            return (
              <Pressable
                key={r.value}
                disabled={saving !== null}
                onPress={() => void choose(r.value)}
                style={({ pressed }) => [
                  styles.card,
                  pressed && styles.cardPressed,
                  saving !== null && !busy && styles.cardDim,
                ]}
              >
                <View style={styles.emojiWrap}>
                  {busy ? (
                    <ActivityIndicator color={colors.brand} />
                  ) : (
                    <Text style={styles.emoji}>{r.emoji}</Text>
                  )}
                </View>
                <View style={styles.cardText}>
                  <Text style={styles.cardTitle}>{r.label}</Text>
                  <Text style={styles.cardDesc}>{r.desc}</Text>
                </View>
              </Pressable>
            );
          })}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  content: { padding: spacing.xl, gap: spacing.sm, flexGrow: 1, justifyContent: "center" },
  mascot: { alignSelf: "center" },
  title: {
    fontSize: fontSize.xl,
    fontFamily: fonts.heading,
    color: colors.text,
    textAlign: "center",
    marginTop: spacing.sm,
  },
  subtitle: {
    fontSize: fontSize.sm,
    fontFamily: fonts.body,
    color: colors.textMuted,
    textAlign: "center",
    marginBottom: spacing.lg,
  },
  error: {
    fontSize: fontSize.sm,
    fontFamily: fonts.bodyMedium,
    color: colors.danger,
    textAlign: "center",
    marginBottom: spacing.sm,
  },
  list: { gap: spacing.md },
  card: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.lg,
    borderRadius: radius.xl,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    padding: spacing.lg,
  },
  cardPressed: { borderColor: colors.brand, backgroundColor: "#eff6ff" },
  cardDim: { opacity: 0.5 },
  emojiWrap: {
    width: 48,
    height: 48,
    borderRadius: radius.lg,
    backgroundColor: colors.bg,
    alignItems: "center",
    justifyContent: "center",
  },
  emoji: { fontSize: 26 },
  cardText: { flex: 1 },
  cardTitle: {
    fontSize: fontSize.md,
    fontFamily: fonts.heading,
    color: colors.text,
  },
  cardDesc: {
    fontSize: fontSize.sm,
    fontFamily: fonts.body,
    color: colors.textMuted,
    marginTop: 2,
  },
});
