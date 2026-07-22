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
import { colors, fonts, fontSize, fontWeight, radius, spacing } from "@/theme/tokens";

type ClerkErrLike = {
  code?: string;
  message?: string;
  longMessage?: string;
  errors?: { code?: string; message?: string; longMessage?: string }[];
};

/**
 * Giriş (Clerk @clerk/expo v3 Future API):
 *  1. password({ emailAddress, password }) — şifre birinci faktör.
 *  2. status 'complete' → finalize().
 *  3. status 'needs_second_factor' → bu instance e-posta kodunu 2. faktör istiyor →
 *     mfa.sendEmailCode() → kod ekranı → mfa.verifyEmailCode({code}) → finalize().
 */
export function SignInForm() {
  const { signIn } = useSignIn();
  const [phase, setPhase] = useState<"password" | "mfa">("password");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function showError(e: unknown) {
    const x = (e ?? {}) as ClerkErrLike;
    const first = x.errors?.[0] ?? x;
    const c = first.code ? `[${first.code}] ` : "";
    setError(`${c}${first.longMessage ?? first.message ?? "Bir hata oluştu."}`);
  }

  async function finalizeIfComplete(): Promise<boolean> {
    if (signIn.status === "complete") {
      const { error: finErr } = await signIn.finalize();
      if (finErr) {
        showError(finErr);
        return false;
      }
      return true; // useAuth().isSignedIn → true → ekran değişir
    }
    return false;
  }

  async function onPassword() {
    if (busy || !email.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const { error } = await signIn.password({
        emailAddress: email.trim(),
        password,
      });
      if (error) {
        showError(error);
        return;
      }
      if (await finalizeIfComplete()) return;
      if (signIn.status === "needs_second_factor") {
        // Bu instance 2. faktör = e-posta kodu. Kodu gönder → kod ekranına geç.
        const { error: sendErr } = await signIn.mfa.sendEmailCode();
        if (sendErr) {
          showError(sendErr);
          return;
        }
        setPhase("mfa");
        return;
      }
      setError(`Beklenmedik durum: ${signIn.status ?? "?"}`);
    } catch (e) {
      showError(e);
    } finally {
      setBusy(false);
    }
  }

  async function onVerifyMfa() {
    if (busy || !code.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const { error } = await signIn.mfa.verifyEmailCode({ code: code.trim() });
      if (error) {
        showError(error);
        return;
      }
      if (!(await finalizeIfComplete())) {
        setError(`Doğrulama sonrası durum: ${signIn.status ?? "?"}`);
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

        {phase === "password" ? (
          <>
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
              onPress={onPassword}
              disabled={busy}
            >
              {busy ? (
                <ActivityIndicator color={colors.onBrand} />
              ) : (
                <Text style={styles.buttonText}>Giriş Yap</Text>
              )}
            </Pressable>
            <Pressable
              onPress={() => void clearClerkStateAndReload()}
              disabled={busy}
            >
              <Text style={styles.resetLink}>Giriş takıldıysa: durumu sıfırla</Text>
            </Pressable>
          </>
        ) : (
          <>
            <Text style={styles.subtitle}>
              {email} adresine gönderilen 6 haneli doğrulama kodunu gir
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
              onPress={onVerifyMfa}
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
                setPhase("password");
                setCode("");
                setError(null);
              }}
              disabled={busy}
            >
              <Text style={styles.resetLink}>Geri</Text>
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
    fontFamily: fonts.heading,
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
    fontFamily: fonts.bodyBold,
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
