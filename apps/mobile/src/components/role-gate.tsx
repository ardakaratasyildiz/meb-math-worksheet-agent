import { useUser } from "@clerk/expo";
import { useState } from "react";
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { Mascot } from "@/components/mascot";
import { PrimaryButton } from "@/components/ui";
import { setRole as setRoleOnServer } from "@/lib/api";
import {
  DISPLAY_NAME_MAX,
  isValidDisplayName,
  needsDisplayName,
  saveDisplayName,
} from "@/lib/display-name";
import { ROLE_META, type SelectableRole } from "@/lib/roles";
import { colors, fonts, fontSize, radius, spacing } from "@/theme/tokens";

type ClerkUser = NonNullable<ReturnType<typeof useUser>["user"]>;

/**
 * Zorunlu onboarding — iki adım: hitap adı, sonra rol.
 * (tabs)/_layout bunu "adı yok VEYA rolü yok" iken render eder; ikisi de dolunca
 * sekmeler açılır. Adım seçimi state'te TUTULMAZ, her render'da kullanıcıdan
 * türetilir → kayıt + `user.reload()` sonrası sıradaki adım kendiliğinden gelir.
 *
 * Ad neden burada sorulur (kayıt formunda değil): kayıt akışına dördüncü bir alan
 * eklemek dönüşümü düşürür, ayrıca bu ekran ZATEN mevcut kullanıcıların önüne de
 * çıkıyor → e-posta ile kaydolmuş eski hesaplar da adını bir kez girip geçer.
 *
 * Rol kalıcılığı — iki yönlü (bkz. lib/roles.ts):
 *  1. Client-side `user.update({ unsafeMetadata.role })` — pk_test/Expo Go'da GÜVENİLİR çalışır,
 *     effectiveRole legacy path'ten okur → gate hemen kapanır.
 *  2. Best-effort backend POST /api/me/role — publicMetadata'ya kanonik yazım (28 Tem pk_live
 *     sonrası otoritatif). Dev'de 401 olursa sessizce yutulur; unsafeMetadata fallback taşır.
 */
export function RoleGate() {
  const { user } = useUser();

  return (
    <SafeAreaView style={styles.safe}>
      {/* iOS'ta klavye içeriğin ÜSTÜNE biner; dikeyde ortalanmış ad alanını kapatmasın. */}
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          <Mascot variant="wave" size={132} style={styles.mascot} />
          {user && needsDisplayName(user) ? <NameStep user={user} /> : <RoleStep user={user} />}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

/** 1. adım — hitap adı. Soyadı istemiyoruz, takma ad da geçerli. */
function NameStep({ user }: { user: ClerkUser }) {
  const [name, setName] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function save() {
    if (saving) return;
    if (!isValidDisplayName(name)) {
      setError("En az 2 harf yaz.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await saveDisplayName(user, name);
      // Tazele → needsDisplayName false olur → gate sıradaki adıma/sekmelere geçer.
      await user.reload();
    } catch {
      setError("Kaydedilemedi. Bağlantını kontrol edip tekrar dene.");
      setSaving(false);
    }
  }

  return (
    <>
      <Text style={styles.title}>Hoş geldin!</Text>
      <Text style={styles.subtitle}>Sana nasıl hitap edelim?</Text>

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <TextInput
        style={styles.input}
        placeholder="Adın ya da takma adın"
        placeholderTextColor={colors.textFaint}
        value={name}
        onChangeText={(t) => {
          setName(t);
          if (error) setError(null);
        }}
        maxLength={DISPLAY_NAME_MAX}
        autoCapitalize="words"
        autoCorrect={false}
        returnKeyType="done"
        onSubmitEditing={() => void save()}
        editable={!saving}
      />
      <Text style={styles.hint}>Uygulama seni bu adla selamlar. Soyadına gerek yok.</Text>

      <View style={styles.buttonWrap}>
        <PrimaryButton label="Devam" onPress={() => void save()} busy={saving} />
      </View>
    </>
  );
}

/** 2. adım — rol seçimi. */
function RoleStep({ user }: { user: ClerkUser | null | undefined }) {
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
    <>
      <Text style={styles.title}>Kimsin?</Text>
      <Text style={styles.subtitle}>Sana doğru ekranları göstermemiz için profilini seç.</Text>

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
    </>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  flex: { flex: 1 },
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
  input: {
    borderRadius: radius.lg,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    fontSize: fontSize.md,
    fontFamily: fonts.bodyMedium,
    color: colors.text,
    backgroundColor: colors.bgTint,
    textAlign: "center",
  },
  hint: {
    fontSize: fontSize.xs,
    fontFamily: fonts.body,
    color: colors.textFaint,
    textAlign: "center",
    marginTop: spacing.sm,
  },
  buttonWrap: { marginTop: spacing.lg },
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
