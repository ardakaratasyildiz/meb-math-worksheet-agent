import { reloadAppAsync } from "expo";
import * as SecureStore from "expo-secure-store";

/**
 * Clerk'in secure-store'da tuttuğu client/environment/session önbelleğini siler
 * ve uygulamayı yeniden başlatır. Cihazda "takılı" (bayat) bir sign-in denemesi
 * (ör. yanlış görünen needs_second_factor) kaldığında temiz başlangıç sağlar.
 *
 * Not: Bu bir bypass DEĞİL — sadece önbellek temizliği. Yeniden başlatınca Clerk
 * client'ı FAPI'den taze çeker; aktif oturum yoksa (giriş yapılmamışsa) kayıp olmaz.
 * Anahtarlar @clerk/expo cache implementasyonundan (dist/cache).
 */
const CLERK_CACHE_KEYS = [
  "__clerk_cache_client",
  "__clerk_cache_environment",
  "__clerk_cache_session_jwt",
];

export async function clearClerkStateAndReload(): Promise<void> {
  await Promise.all(
    CLERK_CACHE_KEYS.map((k) =>
      SecureStore.deleteItemAsync(k).catch(() => {
        /* anahtar yoksa yok say */
      }),
    ),
  );
  await reloadAppAsync();
}
