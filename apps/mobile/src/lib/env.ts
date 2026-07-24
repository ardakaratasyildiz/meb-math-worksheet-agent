/**
 * Ortam değişkenleri — tek erişim noktası. EXPO_PUBLIC_* bundle'a gömülür.
 * Değerler apps/mobile/.env dosyasından gelir (bkz. .env.example).
 */
export const ENV = {
  clerkPublishableKey: process.env.EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY ?? "",
  apiUrl: process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000",
  apiKey: process.env.EXPO_PUBLIC_API_KEY ?? "",
  // RevenueCat genel SDK anahtarları (platform-bazlı; RevenueCat panosundan).
  // Boşsa satın-alma devre dışı (Expo Go / dev-client key'siz → paywall "yakında").
  revenueCatIosKey: process.env.EXPO_PUBLIC_REVENUECAT_IOS_KEY ?? "",
  revenueCatAndroidKey: process.env.EXPO_PUBLIC_REVENUECAT_ANDROID_KEY ?? "",
} as const;
