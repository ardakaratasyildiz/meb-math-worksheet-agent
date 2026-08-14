import { ClerkProvider } from '@clerk/expo';
import { tokenCache } from '@clerk/expo/token-cache';
import { Fredoka_600SemiBold, Fredoka_700Bold } from '@expo-google-fonts/fredoka';
import {
  Nunito_400Regular,
  Nunito_600SemiBold,
  Nunito_700Bold,
  Nunito_800ExtraBold,
} from '@expo-google-fonts/nunito';
import { useFonts } from 'expo-font';
import { Stack } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { Component, type ReactNode, useEffect, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { AuthTokenBridge } from '@/components/auth-token-bridge';
import { ENV } from '@/lib/env';
import { colors } from '@/theme/tokens';

SplashScreen.preventAutoHideAsync().catch(() => {});

/** TEŞHİS: render hatasını beyaz ekran yerine görünür metne çevirir. */
class RootErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null };
  static getDerivedStateFromError(error: Error) {
    return { error };
  }
  componentDidCatch(error: Error) {
    console.error('[RootErrorBoundary]', error?.message, error?.stack);
  }
  render() {
    if (this.state.error) {
      return (
        <View style={styles.diag}>
          <Text style={styles.diagTitle}>Uygulama hatası</Text>
          <ScrollView style={styles.diagScroll}>
            <Text style={styles.diagText}>{this.state.error.message}</Text>
            <Text style={styles.diagStack}>{this.state.error.stack}</Text>
          </ScrollView>
        </View>
      );
    }
    return this.props.children;
  }
}

export default function RootLayout() {
  const [fontsLoaded, fontError] = useFonts({
    Fredoka_600SemiBold,
    Fredoka_700Bold,
    Nunito_400Regular,
    Nunito_600SemiBold,
    Nunito_700Bold,
    Nunito_800ExtraBold,
  });

  // TEŞHİS: fontlar takılsa bile 4 sn sonra devam et (beyaz ekranda kilitlenme).
  const [fontTimeout, setFontTimeout] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setFontTimeout(true), 4000);
    return () => clearTimeout(t);
  }, []);

  const ready = fontsLoaded || !!fontError || fontTimeout;

  useEffect(() => {
    if (ready) SplashScreen.hideAsync().catch(() => {});
  }, [ready]);

  // Hazır olana kadar GÖRÜNÜR yükleyici (eskiden `return null` → beyaz ekran).
  if (!ready) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" color={colors.brand} />
        <Text style={styles.loadingText}>Yükleniyor…</Text>
      </View>
    );
  }

  if (!ENV.clerkPublishableKey) {
    return (
      <View style={styles.diag}>
        <Text style={styles.diagTitle}>Yapılandırma eksik</Text>
        <Text style={styles.diagText}>
          EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY tanımlı değil. apps/mobile/.env dosyasına ekleyip
          Metro'yu yeniden başlatın.
        </Text>
      </View>
    );
  }

  return (
    <RootErrorBoundary>
      <ClerkProvider publishableKey={ENV.clerkPublishableKey} tokenCache={tokenCache}>
        <AuthTokenBridge />
        <SafeAreaProvider>
          {/*
            headerBackTitle: iOS geri düğmesi varsayılan olarak ÖNCEKİ ekranın
            başlığını yazar; sekme kabuğunun rota adı "(tabs)" olduğu için geri
            düğmesinde "(tabs)" görünüyordu. Sabit "Geri" ile her ekranda düzgün.
          */}
          <Stack
            screenOptions={{
              headerShown: false,
              headerBackTitle: 'Geri',
              // 'minimal' = geri düğmesinde HİÇBİR metin gösterilmez, yalnız ok.
              // headerBackTitle tek başına yetmiyordu (iOS önceki ekranın başlığını
              // alan-durumuna göre yazabiliyor) → "(tabs)" görünmeye devam etti.
              // Bu seçenek başlık çözümlemesinden tamamen bağımsız.
              headerBackButtonDisplayMode: 'minimal',
              contentStyle: { backgroundColor: colors.bg },
            }}
          >
            <Stack.Screen name="(tabs)" options={{ headerShown: false, title: 'Soru Atölyesi' }} />
          </Stack>
        </SafeAreaProvider>
      </ClerkProvider>
    </RootErrorBoundary>
  );
}

const styles = StyleSheet.create({
  loading: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.bg, gap: 12 },
  loadingText: { fontSize: 15, color: colors.textMuted },
  diag: { flex: 1, padding: 24, paddingTop: 60, backgroundColor: colors.bg, gap: 12 },
  diagTitle: { fontSize: 20, fontWeight: '700', color: colors.danger },
  diagScroll: { flex: 1 },
  diagText: { fontSize: 14, color: colors.text, marginBottom: 12 },
  diagStack: { fontSize: 11, color: colors.textMuted, fontFamily: 'monospace' },
});
