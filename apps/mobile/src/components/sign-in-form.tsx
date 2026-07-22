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

import { colors, fontSize, fontWeight, radius, spacing } from "@/theme/tokens";

/**
 * E-posta + şifre ile giriş (Clerk klasik API: signIn.create → setActive).
 * İlk temel; e-posta kodu / OAuth / kayıt akışları sonraki iterasyonda.
 */
export function SignInForm() {
  // @clerk/expo v3 "Future" signals API: signIn.password() → finalize().
  const { signIn } = useSignIn();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit() {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      // Önceki yarım denemenin (ör. MFA) state'ini temizle → "identifier is
      // invalid" (bayat signIn) hatasını önler. reset() API çağrısı yapmaz.
      await signIn.reset();
      const { error: pwErr } = await signIn.password({
        identifier: email.trim(),
        password,
      });
      if (pwErr) {
        setError(pwErr.message ?? "Giriş başarısız.");
        return;
      }
      if (signIn.status === "complete") {
        const { error: finErr } = await signIn.finalize();
        if (finErr) setError(finErr.message ?? "Oturum başlatılamadı.");
      } else {
        // Teşhis: Clerk hangi ek adımı istiyor? (status'ü göster + logla)
        console.log("[signIn] status:", signIn.status);
        setError(`Giriş tamamlanamadı — Clerk status: ${signIn.status ?? "?"}`);
      }
    } catch (e: unknown) {
      setError((e as { message?: string })?.message ?? "Giriş başarısız.");
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
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>Giriş Yap</Text>
          )}
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
});
