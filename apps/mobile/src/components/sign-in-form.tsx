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

type ClerkErrLike = {
  code?: string;
  message?: string;
  longMessage?: string;
  errors?: { code?: string; message?: string; longMessage?: string }[];
};

/**
 * E-posta kodu ile giriş (Clerk @clerk/expo v3 Future API).
 * İki adım: e-posta → sendCode → kod → verifyCode → finalize.
 * (Şifre akışı bu dev instance'ta identifier'ı reddettiği için e-posta kodu.)
 */
export function SignInForm() {
  const { signIn } = useSignIn();
  const [phase, setPhase] = useState<"email" | "code">("email");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function showError(e: unknown) {
    const x = (e ?? {}) as ClerkErrLike;
    const first = x.errors?.[0] ?? x;
    const c = first.code ? `[${first.code}] ` : "";
    setError(`${c}${first.longMessage ?? first.message ?? "Bir hata oluştu."}`);
  }

  async function onSendCode() {
    if (busy || !email.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const { error } = await signIn.emailCode.sendCode({
        emailAddress: email.trim(),
      });
      if (error) {
        console.log("[signIn] sendCode error:", JSON.stringify(error, null, 2));
        showError(error);
        return;
      }
      setPhase("code");
    } catch (e) {
      showError(e);
    } finally {
      setBusy(false);
    }
  }

  async function onVerify() {
    if (busy || !code.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const { error } = await signIn.emailCode.verifyCode({ code: code.trim() });
      if (error) {
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

        {phase === "email" ? (
          <>
            <Text style={styles.subtitle}>Giriş için e-postanı gir</Text>
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
            {error ? <Text style={styles.error}>{error}</Text> : null}
            <Pressable
              style={[styles.button, busy && styles.buttonDisabled]}
              onPress={onSendCode}
              disabled={busy}
            >
              {busy ? (
                <ActivityIndicator color={colors.onBrand} />
              ) : (
                <Text style={styles.buttonText}>Kod Gönder</Text>
              )}
            </Pressable>
          </>
        ) : (
          <>
            <Text style={styles.subtitle}>
              {email} adresine gönderilen 6 haneli kodu gir
            </Text>
            <TextInput
              style={styles.input}
              placeholder="Doğrulama kodu"
              keyboardType="number-pad"
              value={code}
              onChangeText={setCode}
              editable={!busy}
              maxLength={6}
            />
            {error ? <Text style={styles.error}>{error}</Text> : null}
            <Pressable
              style={[styles.button, busy && styles.buttonDisabled]}
              onPress={onVerify}
              disabled={busy}
            >
              {busy ? (
                <ActivityIndicator color={colors.onBrand} />
              ) : (
                <Text style={styles.buttonText}>Doğrula & Giriş</Text>
              )}
            </Pressable>
            <Pressable
              onPress={() => {
                setPhase("email");
                setCode("");
                setError(null);
              }}
              disabled={busy}
            >
              <Text style={styles.link}>E-postayı değiştir</Text>
            </Pressable>
          </>
        )}
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
  link: {
    color: colors.brand,
    fontSize: fontSize.sm,
    textAlign: "center",
    marginTop: spacing.sm,
    fontWeight: fontWeight.medium,
  },
});
