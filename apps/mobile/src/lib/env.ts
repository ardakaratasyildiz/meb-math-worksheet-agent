/**
 * Ortam değişkenleri — tek erişim noktası. EXPO_PUBLIC_* bundle'a gömülür.
 * Değerler apps/mobile/.env dosyasından gelir (bkz. .env.example).
 */
export const ENV = {
  clerkPublishableKey: process.env.EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY ?? "",
  apiUrl: process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000",
  apiKey: process.env.EXPO_PUBLIC_API_KEY ?? "",
} as const;
