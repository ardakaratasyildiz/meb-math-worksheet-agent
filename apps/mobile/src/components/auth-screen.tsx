import { useSSO, useSignIn, useSignUp } from '@clerk/expo';
import * as Linking from 'expo-linking';
import * as WebBrowser from 'expo-web-browser';
import { useCallback, useState } from 'react';
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
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { IconSpark } from '@/components/icons';
import { Mascot } from '@/components/mascot';
import { PrimaryButton } from '@/components/ui';
import { clearClerkStateAndReload } from '@/lib/clerk-reset';
import { colors, fonts, fontSize, radius, shadow, spacing } from '@/theme/tokens';

// OAuth redirect'inin tarayıcı oturumunu tamamlaması için (Expo öneri).
WebBrowser.maybeCompleteAuthSession();

type Mode = 'signIn' | 'signUp' | 'forgot';
/** Her modun alt-adımları (kod/şifre doğrulama fazları). */
type Phase = 'form' | 'code';

type ClerkErrLike = {
  code?: string;
  message?: string;
  longMessage?: string;
  errors?: { code?: string; message?: string; longMessage?: string }[];
};

function humanError(e: unknown): string {
  const x = (e ?? {}) as ClerkErrLike;
  const first = x.errors?.[0] ?? x;
  return first.longMessage ?? first.message ?? 'Bir şeyler ters gitti. Tekrar dene.';
}

/**
 * Birleşik kimlik ekranı: Giriş · Kayıt · Şifre sıfırlama + Google/Apple OAuth.
 * Tasarım sistemine (krem + maskot + Fredoka + PrimaryButton) çekilmiş hali.
 * @clerk/expo v3 Future API (signIn/signUp future resource'ları doğrudan).
 */
export function AuthScreen() {
  const { signIn } = useSignIn();
  const { signUp } = useSignUp();
  const { startSSOFlow } = useSSO();

  const [mode, setMode] = useState<Mode>('signIn');
  const [phase, setPhase] = useState<Phase>('form');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [code, setCode] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  const reset = useCallback((m: Mode) => {
    setMode(m);
    setPhase('form');
    setPassword('');
    setCode('');
    setError(null);
    setInfo(null);
  }, []);

  async function finalizeSignIn(): Promise<boolean> {
    if (signIn.status === 'complete') {
      const { error } = await signIn.finalize();
      if (error) {
        setError(humanError(error));
        return false;
      }
      return true;
    }
    return false;
  }

  // ── GİRİŞ ──────────────────────────────────────────────────────────────────
  const onSignIn = useCallback(async () => {
    if (busy || !email.trim() || !password) return;
    setBusy(true);
    setError(null);
    try {
      const { error } = await signIn.password({ emailAddress: email.trim(), password });
      if (error) return setError(humanError(error));
      if (await finalizeSignIn()) return;
      if (signIn.status === 'needs_second_factor') {
        const { error: sendErr } = await signIn.mfa.sendEmailCode();
        if (sendErr) return setError(humanError(sendErr));
        setInfo(`${email} adresine doğrulama kodu gönderildi.`);
        setPhase('code');
      }
    } catch (e) {
      setError(humanError(e));
    } finally {
      setBusy(false);
    }
  }, [busy, email, password, signIn]);

  const onVerifySignInMfa = useCallback(async () => {
    if (busy || !code.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const { error } = await signIn.mfa.verifyEmailCode({ code: code.trim() });
      if (error) return setError(humanError(error));
      if (!(await finalizeSignIn())) setError('Doğrulama tamamlanamadı, tekrar dene.');
    } catch (e) {
      setError(humanError(e));
    } finally {
      setBusy(false);
    }
  }, [busy, code, signIn]);

  // ── KAYIT ──────────────────────────────────────────────────────────────────
  const onSignUp = useCallback(async () => {
    if (busy || !email.trim() || password.length < 8) {
      if (password.length < 8) setError('Şifre en az 8 karakter olmalı.');
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const { error } = await signUp.password({ emailAddress: email.trim(), password });
      if (error) return setError(humanError(error));
      // E-posta doğrulaması: kod gönder → kod fazına geç.
      const { error: sendErr } = await signUp.verifications.sendEmailCode();
      if (sendErr) return setError(humanError(sendErr));
      setInfo(`${email} adresine doğrulama kodu gönderildi.`);
      setPhase('code');
    } catch (e) {
      setError(humanError(e));
    } finally {
      setBusy(false);
    }
  }, [busy, email, password, signUp]);

  const onVerifySignUp = useCallback(async () => {
    if (busy || !code.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const { error } = await signUp.verifications.verifyEmailCode({ code: code.trim() });
      if (error) return setError(humanError(error));
      if (signUp.status === 'complete') {
        const { error: finErr } = await signUp.finalize();
        if (finErr) setError(humanError(finErr));
      } else {
        setError(`Kayıt tamamlanamadı (durum: ${signUp.status ?? '?'}).`);
      }
    } catch (e) {
      setError(humanError(e));
    } finally {
      setBusy(false);
    }
  }, [busy, code, signUp]);

  // ── ŞİFRE SIFIRLAMA ─────────────────────────────────────────────────────────
  const onForgotSend = useCallback(async () => {
    if (busy || !email.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const { error: createErr } = await signIn.create({ identifier: email.trim() });
      if (createErr) return setError(humanError(createErr));
      const { error } = await signIn.resetPasswordEmailCode.sendCode();
      if (error) return setError(humanError(error));
      setInfo(`${email} adresine sıfırlama kodu gönderildi. Kodu ve yeni şifreni gir.`);
      setPassword('');
      setPhase('code');
    } catch (e) {
      setError(humanError(e));
    } finally {
      setBusy(false);
    }
  }, [busy, email, signIn]);

  const onForgotSubmit = useCallback(async () => {
    if (busy || !code.trim() || password.length < 8) {
      if (password.length < 8) setError('Yeni şifre en az 8 karakter olmalı.');
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const { error: vErr } = await signIn.resetPasswordEmailCode.verifyCode({ code: code.trim() });
      if (vErr) return setError(humanError(vErr));
      const { error: pErr } = await signIn.resetPasswordEmailCode.submitPassword({ password });
      if (pErr) return setError(humanError(pErr));
      if (!(await finalizeSignIn())) setError('Şifre sıfırlandı ama giriş tamamlanamadı, tekrar dene.');
    } catch (e) {
      setError(humanError(e));
    } finally {
      setBusy(false);
    }
  }, [busy, code, password, signIn]);

  // ── OAUTH ───────────────────────────────────────────────────────────────────
  const onOAuth = useCallback(
    async (strategy: 'oauth_google' | 'oauth_apple') => {
      if (busy) return;
      setBusy(true);
      setError(null);
      try {
        const { createdSessionId, setActive } = await startSSOFlow({
          strategy,
          redirectUrl: Linking.createURL('/sso-callback'),
        });
        if (createdSessionId && setActive) {
          await setActive({ session: createdSessionId });
        }
        // createdSessionId yoksa: kullanıcı iptal etti / ek adım gerekli — sessiz.
      } catch (e) {
        setError(humanError(e));
      } finally {
        setBusy(false);
      }
    },
    [busy, startSSOFlow],
  );

  // ── Render yardımcıları ──────────────────────────────────────────────────────
  const title = mode === 'signUp' ? 'Aramıza katıl' : mode === 'forgot' ? 'Şifreni sıfırla' : 'Tekrar hoş geldin';
  const subtitle =
    phase === 'code'
      ? mode === 'forgot'
        ? 'Kodu ve yeni şifreni gir'
        : 'E-postana gelen 6 haneli kodu gir'
      : mode === 'signUp'
        ? 'Ücretsiz hesap oluştur, çalışmaya başla'
        : mode === 'forgot'
          ? 'E-postanı gir, kod gönderelim'
          : 'Devam etmek için giriş yap';

  const primary =
    phase === 'code'
      ? mode === 'signUp'
        ? { label: 'Doğrula & Başla', onPress: onVerifySignUp }
        : mode === 'forgot'
          ? { label: 'Şifreyi güncelle', onPress: onForgotSubmit }
          : { label: 'Doğrula & Giriş', onPress: onVerifySignInMfa }
      : mode === 'signUp'
        ? { label: 'Hesap oluştur', onPress: onSignUp }
        : mode === 'forgot'
          ? { label: 'Kod gönder', onPress: onForgotSend }
          : { label: 'Giriş Yap', onPress: onSignIn };

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.flex}
      >
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          <View style={styles.header}>
            <Mascot variant={mode === 'signUp' ? 'happy' : 'wave'} size={96} />
            <Text style={styles.brand}>Soru Atölyesi</Text>
            <Text style={styles.title}>{title}</Text>
            <Text style={styles.subtitle}>{subtitle}</Text>
          </View>

          {/* OAuth — yalnız form fazında (kod fazında gizli) */}
          {phase === 'form' && mode !== 'forgot' ? (
            <View style={styles.oauthWrap}>
              <OAuthButton label="Google ile devam et" onPress={() => onOAuth('oauth_google')} disabled={busy} />
              {Platform.OS === 'ios' ? (
                <OAuthButton label="Apple ile devam et" onPress={() => onOAuth('oauth_apple')} disabled={busy} dark />
              ) : null}
              <View style={styles.divider}>
                <View style={styles.line} />
                <Text style={styles.dividerText}>veya e-posta ile</Text>
                <View style={styles.line} />
              </View>
            </View>
          ) : null}

          {/* Form alanları */}
          {phase === 'form' ? (
            <>
              <Field
                placeholder="E-posta"
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                autoComplete="email"
                editable={!busy}
              />
              {mode !== 'forgot' ? (
                <Field
                  placeholder={mode === 'signUp' ? 'Şifre (en az 8 karakter)' : 'Şifre'}
                  value={password}
                  onChangeText={setPassword}
                  secureTextEntry
                  editable={!busy}
                />
              ) : null}
            </>
          ) : (
            <>
              <Field
                placeholder="Doğrulama kodu"
                value={code}
                onChangeText={setCode}
                keyboardType="number-pad"
                maxLength={6}
                editable={!busy}
              />
              {mode === 'forgot' ? (
                <Field
                  placeholder="Yeni şifre (en az 8 karakter)"
                  value={password}
                  onChangeText={setPassword}
                  secureTextEntry
                  editable={!busy}
                />
              ) : null}
            </>
          )}

          {info ? <Text style={styles.info}>{info}</Text> : null}
          {error ? <Text style={styles.error}>{error}</Text> : null}

          <PrimaryButton label={primary.label} onPress={primary.onPress} busy={busy} color={colors.brand} />

          {/* Alt bağlantılar */}
          {phase === 'form' ? (
            <View style={styles.links}>
              {mode === 'signIn' ? (
                <>
                  <LinkText label="Şifreni mi unuttun?" onPress={() => reset('forgot')} />
                  <LinkText label="Hesabın yok mu? Kayıt ol" onPress={() => reset('signUp')} bold />
                </>
              ) : (
                <LinkText
                  label={mode === 'signUp' ? 'Zaten hesabın var mı? Giriş yap' : 'Girişe dön'}
                  onPress={() => reset('signIn')}
                  bold
                />
              )}
            </View>
          ) : (
            <LinkText label="Geri" onPress={() => setPhase('form')} />
          )}

          <Pressable onPress={() => void clearClerkStateAndReload()} disabled={busy} style={styles.resetWrap}>
            <Text style={styles.resetLink}>Giriş takıldıysa: durumu sıfırla</Text>
          </Pressable>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

function Field(props: React.ComponentProps<typeof TextInput>) {
  return (
    <TextInput
      style={styles.input}
      placeholderTextColor={colors.textFaint}
      autoCapitalize="none"
      {...props}
    />
  );
}

function OAuthButton({
  label,
  onPress,
  disabled,
  dark,
}: {
  label: string;
  onPress: () => void;
  disabled?: boolean;
  dark?: boolean;
}) {
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      style={({ pressed }) => [
        styles.oauthBtn,
        dark && styles.oauthBtnDark,
        pressed && !disabled && styles.pressed,
        disabled && styles.dim,
      ]}
    >
      <IconSpark size={18} />
      <Text style={[styles.oauthText, dark && styles.oauthTextDark]}>{label}</Text>
    </Pressable>
  );
}

function LinkText({ label, onPress, bold }: { label: string; onPress: () => void; bold?: boolean }) {
  return (
    <Pressable onPress={onPress} hitSlop={8}>
      <Text style={[styles.link, bold && styles.linkBold]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  flex: { flex: 1 },
  content: { flexGrow: 1, justifyContent: 'center', padding: spacing.xl, gap: spacing.md },
  header: { alignItems: 'center', gap: 4, marginBottom: spacing.md },
  brand: { fontFamily: fonts.heading, fontSize: fontSize.xl, color: colors.brand },
  title: { fontFamily: fonts.heading, fontSize: fontSize.xxl, color: colors.text, marginTop: spacing.sm },
  subtitle: { fontFamily: fonts.body, fontSize: fontSize.sm, color: colors.textMuted, textAlign: 'center' },

  oauthWrap: { gap: spacing.sm },
  oauthBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    backgroundColor: colors.surface,
    borderRadius: radius.pill,
    paddingVertical: 14,
    ...shadow.card,
  },
  oauthBtnDark: { backgroundColor: colors.text },
  oauthText: { fontFamily: fonts.bodyBold, fontSize: fontSize.md, color: colors.text },
  oauthTextDark: { color: '#FFFFFF' },
  divider: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, marginVertical: spacing.sm },
  line: { flex: 1, height: 1, backgroundColor: colors.border },
  dividerText: { fontFamily: fonts.body, fontSize: fontSize.xs, color: colors.textFaint },

  input: {
    borderWidth: 1.5,
    borderColor: colors.border,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    paddingHorizontal: spacing.lg,
    paddingVertical: 14,
    fontSize: fontSize.md,
    fontFamily: fonts.body,
    color: colors.text,
  },
  info: { color: colors.brand, fontSize: fontSize.sm, fontFamily: fonts.bodyMedium, textAlign: 'center' },
  error: { color: colors.danger, fontSize: fontSize.sm, fontFamily: fonts.bodyMedium, textAlign: 'center' },

  links: { alignItems: 'center', gap: spacing.md, marginTop: spacing.sm },
  link: { color: colors.textMuted, fontSize: fontSize.sm, fontFamily: fonts.bodyMedium },
  linkBold: { color: colors.brand, fontFamily: fonts.bodyBold },

  pressed: { opacity: 0.7 },
  dim: { opacity: 0.5 },
  resetWrap: { marginTop: spacing.lg },
  resetLink: {
    color: colors.textFaint,
    fontSize: fontSize.xs,
    textAlign: 'center',
    textDecorationLine: 'underline',
  },
});
