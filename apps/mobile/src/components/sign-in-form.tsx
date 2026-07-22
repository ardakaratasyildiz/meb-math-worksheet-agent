import { useSignIn } from "@clerk/expo";
import { useState } from "react";
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { clearClerkStateAndReload } from "@/lib/clerk-reset";
import { colors, fontSize, fontWeight, radius, spacing } from "@/theme/tokens";

type ClerkErrLike = {
  code?: string;
  message?: string;
  longMessage?: string;
  errors?: { code?: string; message?: string; longMessage?: string }[];
};

/**
 * E-posta + şifre ile giriş (Clerk @clerk/expo v3 Future API).
 * create({ identifier, password }) tek adım → status complete → finalize().
 */
export function SignInForm() {
  const { signIn } = useSignIn();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function showError(e: unknown) {
    const x = (e ?? {}) as ClerkErrLike;
    const first = x.errors?.[0] ?? x;
    const c = first.code ? `[${first.code}] ` : "";
    setError(`${c}${first.longMessage ?? first.message ?? "Bir hata oluştu."}`);
  }

  async function onSubmit() {
    if (busy || !email.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const { error } = await signIn.create({
        identifier: email.trim(),
        password,
      });
      if (error) {
        console.log("[signIn] create error:", JSON.stringify(error, null, 2));
        showError(error);
        return;
      }
      if (signIn.status === "complete") {
        const { error: finErr } = await signIn.finalize();
        if (finErr) showError(finErr);
      } else {
        setError(`Giriş tamamlanamadı — durum: ${signIn.status ?? "?"}`);
      }
    } catch (e) {
      showError(e);
    } finally {
      setBusy(false);
    }
  }

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        style={styles.container}
      >
        <Text style={styles.title}>Soru Atölyesi</Text>
        <Text style={styles.subtitle}>Devam etmek için giriş yap</Text>

        <TextInput
          style={styles.input}
          placeholder="E-posta"
          autoCapitalize="none"
          keyboardType="email-address"
          autoComplete="email"
          value={email}
          onChangeText={setEmail}
          editable={!busy}
        />
        <TextInput
          style={styles.input}
          placeholder="Şifre"
          secureTextEntry
          value={password}
          onChangeText={setPassword}
          editable={!busy}
        />

        {error ? <Text style={styles.error}>{error}</Text> : null}

        <Pressable
          style={[styles.button, busy && styles.buttonDisabled]}
          onPress={onSubmit}
          disabled={busy}
        >
          {busy ? (
            <ActivityIndicator color={colors.onBrand} />
          ) : (
            <Text style={styles.buttonText}>Giriş Yap</Text>
          )}
        </Pressable>

        <Pressable onPress={() => void clearClerkStateAndReload()} disabled={busy}>
          <Text style={styles.resetLink}>
            Giriş takıldıysa: durumu sıfırla
          </Text>
        </Pressable>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  container: {
    flex: 1,
    justifyContent: "center",
    paddingHorizontal: spacing.xl,
    gap: spacing.md,
  },
  title: {
    fontSize: fontSize.xxl,
    fontWeight: fontWeight.heavy,
    textAlign: "center",
    color: colors.text,
  },
  subtitle: {
    fontSize: fontSize.sm,
    textAlign: "center",
    color: colors.textMuted,
    marginBottom: spacing.md,
  },
  input: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    paddingHorizontal: spacing.lg,
    paddingVertical: 14,
    fontSize: fontSize.md,
    color: colors.text,
  },
  button: {
    backgroundColor: colors.brand,
    borderRadius: radius.md,
    paddingVertical: spacing.lg,
    alignItems: "center",
    marginTop: spacing.sm,
  },
  buttonDisabled: { opacity: 0.5 },
  buttonText: {
    color: colors.onBrand,
    fontSize: fontSize.md,
    fontWeight: fontWeight.bold,
  },
  error: { color: colors.danger, fontSize: fontSize.sm, textAlign: "center" },
  resetLink: {
    color: colors.textMuted,
    fontSize: fontSize.xs,
    textAlign: "center",
    marginTop: spacing.md,
    textDecorationLine: "underline",
  },
});
