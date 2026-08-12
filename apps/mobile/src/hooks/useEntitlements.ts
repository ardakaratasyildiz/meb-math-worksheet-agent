import { useAuth } from "@clerk/expo";
import { useCallback, useEffect, useState } from "react";

import { getEntitlements, type Entitlements } from "@/lib/api";
import { configurePurchases } from "@/lib/purchases";

/** Giriş yok / uç 401 / ağ hatası → güvenli varsayım: Ücretsiz 10 kağıt/ay, günde 2. */
const FREE_FALLBACK: Entitlements = {
  plan: "free",
  is_premium: false,
  status: null,
  trial_end: null,
  current_period_end: null,
  cancel_at_period_end: false,
  quota: { limit: 10, used: 0, remaining: 10, daily_limit: 2, used_today: 0, daily_remaining: 2 },
};

export interface UseEntitlements {
  entitlements: Entitlements;
  loading: boolean;
  /** Aylık kotası bitmiş mi (kotasız/fair-use ise asla true). Free→yükselt, Pro→top-up. */
  quotaExhausted: boolean;
  /**
   * Bugünkü ücretsiz hak bitmiş mi (aylık hak dururken de olabilir). Ayrı tutulur:
   * bu engel GEÇİCİ → kullanıcıya "yarın devam" denir, "hakkın bitti" değil.
   */
  dailyExhausted: boolean;
  isSignedIn: boolean;
  refresh: () => Promise<void>;
}

/**
 * Kullanıcının abonelik/kota durumu (GÖSTERİM + soft-gate için). Backend karar verir;
 * gating yine sunucuda enforce edilir. Ayrıca RevenueCat'i Clerk userId ile yapılandırır
 * (Expo Go'da no-op). Expo Go pk_test → 401 → FREE_FALLBACK (paywall erişilebilir kalır).
 */
export function useEntitlements(): UseEntitlements {
  const { userId } = useAuth();
  const [ent, setEnt] = useState<Entitlements | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    if (!userId) {
      setEnt(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      setEnt(await getEntitlements(userId));
    } catch {
      setEnt(null); // 401 / ağ → free varsayımı
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  // RevenueCat'i kullanıcı kimliğiyle yapılandır (satın-alma → aynı tenant webhook'u).
  useEffect(() => {
    if (userId) configurePurchases(userId);
  }, [userId]);

  const entitlements = ent ?? FREE_FALLBACK;
  const rem = entitlements.quota.remaining;
  const dailyRem = entitlements.quota.daily_remaining;
  return {
    entitlements,
    loading,
    quotaExhausted: rem !== null && rem <= 0,
    dailyExhausted: dailyRem !== null && dailyRem !== undefined && dailyRem <= 0,
    isSignedIn: !!userId,
    refresh,
  };
}
