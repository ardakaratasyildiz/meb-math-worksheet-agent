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
import { useEffect } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { AuthTokenBridge } from '@/components/auth-token-bridge';
import { ENV } from '@/lib/env';
import { colors, fonts } from '@/theme/tokens';

SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const [fontsLoaded, fontError] = useFonts({
    Fredoka_600SemiBold,
    Fredoka_700Bold,
    Nunito_400Regular,
    Nunito_600SemiBold,
    Nunito_700Bold,
    Nunito_800ExtraBold,
  });

  useEffect(() => {
    if (fontsLoaded || fontError) SplashScreen.hideAsync().catch(() => {});
  }, [fontsLoaded, fontError]);

  // Fontlar yüklenene kadar splash'te bekle (hata olursa sistem fontuyla devam).
  if (!fontsLoaded && !fontError) return null;

  // Anahtar yoksa ClerkProvider patlar → yardımcı yapılandırma ekranı göster.
  if (!ENV.clerkPublishableKey) {
    return (
      <View style={styles.configScreen}>
        <Text style={styles.configTitle}>Yapılandırma eksik</Text>
        <Text style={styles.configText}>
          EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY tanımlı değil.{"\n"}
          apps/mobile/.env dosyasına ekleyip yeniden başlatın.
        </Text>
      </View>
    );
  }

  return (
    <ClerkProvider publishableKey={ENV.clerkPublishableKey} tokenCache={tokenCache}>
      <AuthTokenBridge />
      <SafeAreaProvider>
        <Stack
          screenOptions={{
            headerTitleStyle: { fontFamily: fonts.headingSemi, color: colors.text },
            headerTintColor: colors.brand,
            headerShadowVisible: false,
            contentStyle: { backgroundColor: colors.bg },
          }}
        />
      </SafeAreaProvider>
    </ClerkProvider>
  );
}

const styles = StyleSheet.create({
  configScreen: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    gap: 8,
  },
  configTitle: { fontSize: 18, fontWeight: '700' },
  configText: { fontSize: 14, textAlign: 'center', opacity: 0.7 },
});
