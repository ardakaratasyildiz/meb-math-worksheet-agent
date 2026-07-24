import { Stack, useLocalSearchParams, useRouter } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { IconSpark, IconStar } from '@/components/icons';
import { Mascot } from '@/components/mascot';
import { Card, PrimaryButton } from '@/components/ui';
import { useEntitlements } from '@/hooks/useEntitlements';
import {
  PurchasesUnavailableError,
  fetchProducts,
  purchaseSku,
  purchasesSupported,
  restorePurchases,
} from '@/lib/purchases';
import { colors, fonts, fontSize, radius, shadow, spacing } from '@/theme/tokens';

const headerOpts = {
  headerShown: true,
  title: 'Yükselt',
  headerStyle: { backgroundColor: colors.bg },
  headerShadowVisible: false,
  headerTintColor: colors.brand,
  headerTitleStyle: { fontFamily: fonts.headingSemi, color: colors.text },
} as const;

/** Abonelik kademeleri — fiyat/kota docs/MONETIZATION_PLAN.md §2 (KESİN 2026-07-24). */
const TIERS = [
  {
    sku: 'pro-aylik',
    plan: 'pro',
    name: 'Pro',
    price: '₺199',
    papers: 50,
    color: colors.brand,
    tint: colors.tintBlue,
    popular: false,
  },
  {
    sku: 'proplus-aylik',
    plan: 'pro-plus',
    name: 'Pro+',
    price: '₺349',
    papers: 120,
    color: colors.magic,
    tint: colors.tintPurple,
    popular: true,
  },
] as const;

/** Ek kağıt paketleri (tüketilebilir; yalnız aktif aboneye) — top-up. */
const TOPUPS = [
  { sku: 'topup-25', papers: 25, price: '₺89' },
  { sku: 'topup-75', papers: 75, price: '₺199' },
] as const;

export default function PaywallScreen() {
  const router = useRouter();
  const { reason } = useLocalSearchParams<{ reason?: string }>();
  const { entitlements, refresh } = useEntitlements();
  const supported = purchasesSupported();

  const [busySku, setBusySku] = useState<string | null>(null);
  const [restoring, setRestoring] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [msgOk, setMsgOk] = useState(false);
  // Mağaza yerelleştirilmiş fiyatları (varsa statik ₺'yi ezer).
  const [storePrice, setStorePrice] = useState<Record<string, string>>({});

  const currentPlan = entitlements.plan;
  const isPremium = entitlements.is_premium;

  useEffect(() => {
    if (!supported) return;
    const skus = [...TIERS.map((t) => t.sku), ...TOPUPS.map((t) => t.sku)];
    void fetchProducts(skus).then((ps) => {
      if (!ps.length) return;
      setStorePrice(Object.fromEntries(ps.map((p) => [p.productId, p.priceString])));
    });
  }, [supported]);

  const buy = useCallback(
    async (sku: string) => {
      setMsg(null);
      setBusySku(sku);
      try {
        const ok = await purchaseSku(sku);
        if (ok) {
          await refresh();
          setMsgOk(true);
          setMsg('Satın alma tamamlandı! 🎉');
        }
      } catch (e) {
        setMsgOk(false);
        setMsg(
          e instanceof PurchasesUnavailableError
            ? 'Satın alma, uygulamanın mağaza sürümünde aktif olur.'
            : (e as Error).message,
        );
      } finally {
        setBusySku(null);
      }
    },
    [refresh],
  );

  const restore = useCallback(async () => {
    setMsg(null);
    setRestoring(true);
    try {
      const active = await restorePurchases();
      await refresh();
      setMsgOk(active);
      setMsg(active ? 'Aboneliğin geri yüklendi.' : 'Geri yüklenecek aktif abonelik bulunamadı.');
    } catch (e) {
      setMsgOk(false);
      setMsg(
        e instanceof PurchasesUnavailableError
          ? 'Geri yükleme, uygulamanın mağaza sürümünde aktif olur.'
          : (e as Error).message,
      );
    } finally {
      setRestoring(false);
    }
  }, [refresh]);

  return (
    <View style={styles.root}>
      <Stack.Screen options={headerOpts} />
      <SafeAreaView style={styles.safe} edges={['bottom']}>
        <ScrollView contentContainerStyle={styles.content}>
          {/* Hero */}
          <Card floating style={styles.hero}>
            <Mascot variant="happy" size={72} />
            <View style={styles.heroText}>
              <Text style={styles.heroTitle}>Daha çok üret, aynı kalite</Text>
              <Text style={styles.heroSub}>
                Ayda daha fazla çalışma kağıdı ve alıştırma — sınırların sana yeter.
              </Text>
            </View>
          </Card>

          {reason === 'quota' ? (
            <View style={styles.quotaBanner}>
              <Text style={styles.quotaText}>
                Bu ayki kotan doldu. Devam etmek için bir plan seç ya da ek paket al.
              </Text>
            </View>
          ) : null}

          {/* Kademeler */}
          {TIERS.map((t) => {
            const isCurrent = currentPlan === t.plan;
            const price = storePrice[t.sku] ?? t.price;
            return (
              <Card key={t.sku} floating={t.popular} style={[styles.tier, t.popular && { borderColor: t.color, borderWidth: 2 }]}>
                {t.popular ? (
                  <View style={[styles.badge, { backgroundColor: t.color }]}>
                    <IconStar size={12} />
                    <Text style={styles.badgeText}>En popüler</Text>
                  </View>
                ) : null}
                <View style={styles.tierHead}>
                  <View>
                    <Text style={[styles.tierName, { color: t.color }]}>{t.name}</Text>
                    <Text style={styles.tierPapers}>{t.papers} kağıt / ay</Text>
                  </View>
                  <View style={styles.tierPriceWrap}>
                    <Text style={[styles.tierPrice, { color: t.color }]}>{price}</Text>
                    <Text style={styles.tierPeriod}>/ay</Text>
                  </View>
                </View>
                <PrimaryButton
                  label={isCurrent ? 'Mevcut planın' : '7 gün ücretsiz dene'}
                  color={t.color}
                  variant={isCurrent ? 'soft' : 'solid'}
                  disabled={isCurrent}
                  busy={busySku === t.sku}
                  onPress={() => void buy(t.sku)}
                />
              </Card>
            );
          })}

          <Text style={styles.allNote}>
            Tüm özellikler her iki kademede de açık — fark yalnız aylık kağıt sayısı.
          </Text>

          {/* Ek paket — yalnız aktif abone */}
          {isPremium ? (
            <Card style={styles.topupCard}>
              <Text style={styles.topupTitle}>Kağıdın mı bitti?</Text>
              <Text style={styles.topupHint}>Ek paket bu ay geçerli (30 gün).</Text>
              <View style={styles.topupRow}>
                {TOPUPS.map((tp) => (
                  <View key={tp.sku} style={styles.topup}>
                    <Text style={styles.topupPapers}>+{tp.papers}</Text>
                    <Text style={styles.topupPapersLabel}>kağıt</Text>
                    <PrimaryButton
                      label={storePrice[tp.sku] ?? tp.price}
                      variant="soft"
                      color={colors.reward}
                      busy={busySku === tp.sku}
                      onPress={() => void buy(tp.sku)}
                    />
                  </View>
                ))}
              </View>
            </Card>
          ) : null}

          {/* Güven şeridi */}
          <View style={styles.trustRow}>
            <Trust icon={<IconSpark size={16} />} text="7 gün ücretsiz" />
            <Trust icon={<IconStar size={16} />} text="İstediğin an iptal" />
          </View>
          <Text style={styles.trustFine}>Ödeme App Store / Google Play üzerinden · reklamsız</Text>

          {msg ? (
            <Text style={[styles.msg, msgOk ? styles.msgOk : styles.msgErr]}>{msg}</Text>
          ) : null}

          {!supported ? (
            <Text style={styles.devNote}>
              Satın alma, uygulamanın mağaza sürümünde (dev/prod build) aktif olur.
            </Text>
          ) : null}

          <PrimaryButton
            label="Satın almaları geri yükle"
            variant="soft"
            busy={restoring}
            onPress={() => void restore()}
          />
          <PrimaryButton
            label="Şimdilik kalsın"
            variant="soft"
            color={colors.textMuted}
            onPress={() => router.back()}
          />
        </ScrollView>
      </SafeAreaView>
    </View>
  );
}

function Trust({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <View style={styles.trust}>
      {icon}
      <Text style={styles.trustText}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  safe: { flex: 1 },
  content: { padding: spacing.xl, gap: spacing.lg, paddingBottom: spacing.xxl },

  hero: { flexDirection: 'row', alignItems: 'center', gap: spacing.lg, backgroundColor: colors.tintPurple },
  heroText: { flex: 1, gap: 4 },
  heroTitle: { fontFamily: fonts.heading, fontSize: fontSize.xl, color: colors.text },
  heroSub: { fontFamily: fonts.body, fontSize: fontSize.sm, color: colors.textMuted },

  quotaBanner: { backgroundColor: colors.tintYellow, borderRadius: radius.card, padding: spacing.lg },
  quotaText: { fontFamily: fonts.bodyMedium, fontSize: fontSize.sm, color: colors.rewardDark },

  tier: { gap: spacing.lg },
  badge: {
    position: 'absolute',
    top: -10,
    right: spacing.lg,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    borderRadius: radius.pill,
    paddingHorizontal: spacing.md,
    paddingVertical: 4,
    ...shadow.card,
  },
  badgeText: { fontFamily: fonts.bodyBold, fontSize: fontSize.xs, color: '#FFFFFF' },
  tierHead: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  tierName: { fontFamily: fonts.heading, fontSize: fontSize.xl },
  tierPapers: { fontFamily: fonts.body, fontSize: fontSize.sm, color: colors.textMuted, marginTop: 2 },
  tierPriceWrap: { flexDirection: 'row', alignItems: 'baseline' },
  tierPrice: { fontFamily: fonts.heading, fontSize: 30 },
  tierPeriod: { fontFamily: fonts.body, fontSize: fontSize.sm, color: colors.textMuted, marginLeft: 2 },

  allNote: { fontFamily: fonts.body, fontSize: fontSize.sm, color: colors.textMuted, textAlign: 'center' },

  topupCard: { gap: spacing.sm },
  topupTitle: { fontFamily: fonts.heading, fontSize: fontSize.lg, color: colors.text },
  topupHint: { fontFamily: fonts.body, fontSize: fontSize.xs, color: colors.textMuted },
  topupRow: { flexDirection: 'row', gap: spacing.md, marginTop: spacing.sm },
  topup: {
    flex: 1,
    alignItems: 'center',
    gap: 2,
    backgroundColor: colors.tintYellow,
    borderRadius: radius.card,
    padding: spacing.md,
  },
  topupPapers: { fontFamily: fonts.heading, fontSize: fontSize.xl, color: colors.rewardDark },
  topupPapersLabel: { fontFamily: fonts.body, fontSize: fontSize.xs, color: colors.textMuted, marginBottom: spacing.xs },

  trustRow: { flexDirection: 'row', justifyContent: 'center', gap: spacing.xl },
  trust: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  trustText: { fontFamily: fonts.bodyMedium, fontSize: fontSize.sm, color: colors.text },
  trustFine: { fontFamily: fonts.body, fontSize: fontSize.xs, color: colors.textFaint, textAlign: 'center' },

  msg: { fontFamily: fonts.bodyMedium, fontSize: fontSize.sm, textAlign: 'center' },
  msgOk: { color: colors.success },
  msgErr: { color: colors.danger },
  devNote: { fontFamily: fonts.body, fontSize: fontSize.xs, color: colors.textMuted, textAlign: 'center', fontStyle: 'italic' },
});
