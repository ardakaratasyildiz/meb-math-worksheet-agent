import { Stack, useLocalSearchParams, useRouter } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { Linking, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { IconSpark, IconStar } from '@/components/icons';
import { Mascot } from '@/components/mascot';
import { Card, PrimaryButton } from '@/components/ui';
import { useEntitlements } from '@/hooks/useEntitlements';
import { trialDaysLeft, trialLeftLabel } from '@/lib/format';
import {
  PurchasesUnavailableError,
  fetchProducts,
  lastPurchasesError,
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
    sku: 'com.soruatolyesi.app.pro_aylik',
    plan: 'pro',
    name: 'Pro',
    price: '₺199',
    papers: 50,
    color: colors.brand,
    tint: colors.tintBlue,
    popular: false,
  },
  {
    sku: 'com.soruatolyesi.app.proplus_aylik',
    plan: 'pro-plus',
    name: 'Pro+',
    price: '₺349',
    papers: 120,
    color: colors.magic,
    tint: colors.tintPurple,
    popular: true,
  },
] as const;

/**
 * Yasal sayfalar — mağaza incelemesi bu linkleri TIKLAR, kırık olamaz.
 * (Eski `/gizlilik` ve `/kosullar` yolları sitede yok, 404 dönüyordu.)
 */
const LEGAL = {
  terms: 'https://soruatolyesi.com/legal/terms',
  privacy: 'https://soruatolyesi.com/legal/privacy',
} as const;

/**
 * Ücretli planın ücretsizden farkları — hepsi SUNUCUDA fiilen uygulanan farklar.
 * Doğrulanamayan pazarlama vaadi eklenmez (bkz. paywall'daki yorum).
 */
const DIFFERENCES = [
  {
    title: 'Çok daha fazla çalışma kağıdı',
    sub: 'Ücretsizde ayda 10; Pro’da 50, Pro+’ta 120.',
  },
  {
    title: 'Günlük sınır yok',
    sub: 'Ücretsiz planda günde en çok 2 kağıt üretilebilir; abonelikte tavan kalkar.',
  },
  {
    title: 'Yeni nesil soru kalitesi',
    sub: 'Senaryo bazlı, gerçek hayattan sorular her zorlukta açık.',
  },
  {
    title: 'Filigransız PDF',
    sub: 'Kağıdın altındaki “Soru Atölyesi ile üretildi” etiketi ve QR kalkar.',
  },
  {
    title: 'Ek kağıt paketi alabilme',
    sub: 'Kotan biterse +25 veya +75 kağıtlık paket ekleyebilirsin.',
  },
] as const;

/**
 * Pro+'a ÖZEL farklar — Pro'da kapalı, sunucuda enforce edilir.
 * (`entitlements.classroom_limit` / `family_children_limit`; sınırlar
 * `classrooms.create_classroom` ve `me.link_child` uçlarında 402 döner.)
 *
 * Kağıt sayısı tek fark olduğu sürece Pro+ cezbedici değildi. Seçim ölçütü
 * MARJİNAL MALİYET — hesap NET gelirle yapılır, etiket fiyatıyla değil
 * (docs/MONETIZATION_PLAN.md §2.1: etiketten cebe ≈%60 kalıyor). Pro ₺2,40/kağıt ·
 * Pro+ ₺1,75/kağıt · maliyet ~₺1,50 → Pro+'ta kağıt başına yalnız ~₺0,25. O yüzden
 * ayrıcalıklar üretim maliyetini artırmayanlardan: kaç kişi/sınıf havuzu paylaşıyor.
 */
const PLUS_ONLY = [
  {
    title: 'Aile paylaşımı: 3 çocuk',
    sub: 'Çocukların planını devralır, kota tek havuzdan paylaşılır (Pro’da 1 çocuk).',
  },
  {
    title: 'Çoklu sınıf yönetimi',
    sub: '5 sınıf açabilir, ödev verip sonuç panosundan takip edebilirsin (Pro’da 1 sınıf).',
  },
  {
    title: 'Öncelikli destek',
    sub: 'Sorunların sıranın önünde yanıtlanır.',
  },
] as const;

/** Ek kağıt paketleri (tüketilebilir; yalnız aktif aboneye) — top-up. */
const TOPUPS = [
  { sku: 'com.soruatolyesi.app.topup_25', papers: 25, price: '₺89' },
  { sku: 'com.soruatolyesi.app.topup_75', papers: 75, price: '₺199' },
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
  /** Gerçek abonelik/deneme kaydı var mı (dark-launch `premium_all` bunu doldurmaz). */
  const hasRealSubscription = !!entitlements.status;
  const trialLeft = currentPlan === 'trial' ? trialDaysLeft(entitlements.trial_end) : null;

  /**
   * Mağaza ürünleri çekilemediyse sebebi. Fiyatlar sessizce koda gömülü yedeğe
   * düşüyordu → "her şey normal" görünüp satın almaya basınca patlıyordu. Kurulum
   * ayıklamasını körlemesine yapmak zorunda kaldığımız için sebep artık ekranda.
   */
  const [storeIssue, setStoreIssue] = useState<string | null>(null);

  useEffect(() => {
    if (!supported) return;
    const skus = [...TIERS.map((t) => t.sku), ...TOPUPS.map((t) => t.sku)];
    void fetchProducts(skus).then((ps) => {
      if (!ps.length) {
        setStoreIssue(lastPurchasesError() ?? "mağaza ürünleri okunamadı");
        return;
      }
      setStoreIssue(null);
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

          {/*
            Deneme durumu — kullanıcı kartsız 7g denemede olduğunu bilmiyorsa yükseltme
            kararını da veremez. Kalan gün + kalan kağıt açıkça yazılır.
          */}
          {trialLeft !== null ? (
            <View style={styles.trialBanner}>
              {/* Ücretsiz planın rakamları burada TEKRARLANMAZ — sunucu ayarı değişince
                  metin sessizce yanlışa döner. Kalan gün/kağıt zaten yeterli bilgi. */}
              <Text style={styles.trialText}>
                Denemen {trialLeftLabel(trialLeft)} · {entitlements.quota.remaining ?? 0} kağıt
                hakkın kaldı. Bitince ücretsiz plana dönersin.
              </Text>
            </View>
          ) : null}

          {/* Günlük tavan GEÇİCİ (yarın yenilenir), aylık kota kalıcı → ayrı mesaj. */}
          {reason === 'quota' ? (
            <View style={styles.quotaBanner}>
              <Text style={styles.quotaText}>
                Bu ayki kotan doldu. Devam etmek için bir plan seç ya da ek paket al.
              </Text>
            </View>
          ) : reason === 'daily' ? (
            <View style={styles.quotaBanner}>
              <Text style={styles.quotaText}>
                Bugünlük ücretsiz hakkın doldu — yarın yenilenir. Beklemek istemezsen
                planlardan biriyle hemen devam edebilirsin (günlük sınır yok).
              </Text>
            </View>
          ) : reason === 'family' ? (
            <View style={styles.quotaBanner}>
              <Text style={styles.quotaText}>
                Çocuk hesabı bağlamak için ücretli bir plan gerekiyor: Pro'da 1 çocuk,
                Pro+'ta 3 çocuk aynı kota havuzunu paylaşır. Çocuk kendi hesabıyla
                girer, planı senden devralır.
              </Text>
            </View>
          ) : null}

          {/* Kademeler */}
          {TIERS.map((t) => {
            // "Mevcut planın" YALNIZ gerçek abonelikte gösterilir. Sunucuda dark-launch
            // bayrağı (premium_all) herkesi pro-plus sayıyor; buna bakılsaydı hiç kimse
            // satın alma düğmesine basamazdı (cihazda görüldü: plan Pro+, düğmeler kapalı).
            // Gerçek abonelikte `status` dolu gelir (trialing/active/…), dark-launch'ta null.
            const isCurrent = hasRealSubscription && currentPlan === t.plan;
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
                  label={isCurrent ? 'Mevcut planın' : `${t.name} ol · ${price}/ay`}
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

          {/* Mağaza ürünleri okunamadıysa sebebini GÖSTER. Fiyatlar sessizce yedeğe
              düşüp her şey normal görünüyordu; kullanıcı ancak satın almaya basınca
              hata alıyordu ve sebep hiçbir yere yazılmıyordu. */}
          {storeIssue ? (
            <Text style={styles.storeIssue}>
              Mağaza bağlantısı hazır değil: {storeIssue}. Fiyatlar geçici olarak
              gösterim amaçlıdır, satın alma şu an tamamlanamaz.
            </Text>
          ) : null}

          {/*
            "Ücretsizden farkı ne?" — kullanıcı neye para verdiğini görmeden karar
            veremiyordu. YALNIZ sunucuda gerçekten uygulanan farklar listeleniyor
            (kota/günlük tavan: entitlements.daily_limit · yeni nesil kalite:
            wants_yeni_nesil · filigran: render.pdf show_footer_promo ·
            ek paket: yalnız abone).

            Bu kural bir denetimde işe yaradı (2026-08-21): plan sayfasına yazılan
            "sistemde öncelikli soru üretimi" maddesi ÇIKARILDI — öyle bir kuyruk
            mekanizması yok. "Sınırsız pratik" de düzeltildi: Çöz&Geliş quiz'i
            `quizzes.enforce_quota` ile AYNI kağıt havuzundan harcıyor.
            Doğrulanamayan vaat eklenmez; ekleneni buradan çıkarırız.
          */}
          <Card style={styles.diffCard}>
            <Text style={styles.diffTitle}>Ücretsiz plandan farkı</Text>
            {DIFFERENCES.map((d) => (
              <View key={d.title} style={styles.diffRow}>
                <View style={styles.diffCheck}>
                  <Text style={styles.diffCheckText}>✓</Text>
                </View>
                <View style={styles.diffBody}>
                  <Text style={styles.diffRowTitle}>{d.title}</Text>
                  <Text style={styles.diffRowSub}>{d.sub}</Text>
                </View>
              </View>
            ))}
            <Text style={styles.diffFree}>
              Ücretsiz plan: ayda 10 çalışma kağıdı, günde en çok 2.
            </Text>
          </Card>

          {/* Pro+ farkı — kağıt sayısı tek ayrım olduğu sürece Pro+ cezbedici
              değildi. Buradaki maddeler Pro'da KAPALI ve sunucuda enforce ediliyor
              (classroom_limit / family_children_limit → 402). */}
          <Card style={[styles.diffCard, styles.plusCard]}>
            <Text style={styles.diffTitle}>Pro+ ile ayrıca</Text>
            {PLUS_ONLY.map((d) => (
              <View key={d.title} style={styles.diffRow}>
                <View style={[styles.diffCheck, styles.plusCheck]}>
                  <Text style={[styles.diffCheckText, styles.plusCheckText]}>★</Text>
                </View>
                <View style={styles.diffBody}>
                  <Text style={styles.diffRowTitle}>{d.title}</Text>
                  <Text style={styles.diffRowSub}>{d.sub}</Text>
                </View>
              </View>
            ))}
          </Card>

          {/* Ek paket — yalnız GERÇEK abone (dark-launch premium'a gösterilmez:
              sunucu ek paketi yalnız abonelik kaydı olana kredi olarak yazıyor). */}
          {hasRealSubscription && isPremium ? (
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
            <Trust icon={<IconSpark size={16} />} text="Reklamsız" />
            <Trust icon={<IconStar size={16} />} text="İstediğin an iptal" />
          </View>
          <Text style={styles.trustFine}>Ödeme App Store / Google Play üzerinden</Text>

          {/*
            Otomatik yenileme beyanı + yasal linkler — App Store 3.1.2 ve Play abonelik
            politikası bunları ÖDEME EKRANINDA görünür ister; yoksa inceleme reddeder.
          */}
          <Text style={styles.legalNote}>
            Abonelikler aylıktır ve otomatik yenilenir. Ödeme, satın almayı onayladığında App
            Store / Google Play hesabından tahsil edilir; dönem bitiminden en az 24 saat önce
            iptal etmezsen aynı ücretle yenilenir. Aboneliğini cihazının mağaza hesabı
            ayarlarından yönetebilir ya da iptal edebilirsin. Ek kağıt paketleri tek seferlik
            ödemedir, otomatik yenilenmez.
          </Text>
          <View style={styles.legalRow}>
            <Pressable hitSlop={8} onPress={() => void Linking.openURL(LEGAL.terms)}>
              <Text style={styles.legalLink}>Kullanım Koşulları</Text>
            </Pressable>
            <Text style={styles.legalSep}>·</Text>
            <Pressable hitSlop={8} onPress={() => void Linking.openURL(LEGAL.privacy)}>
              <Text style={styles.legalLink}>Gizlilik Politikası</Text>
            </Pressable>
          </View>

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

  trialBanner: { backgroundColor: colors.tintPurple, borderRadius: radius.card, padding: spacing.lg },
  trialText: { fontFamily: fonts.bodyMedium, fontSize: fontSize.sm, color: colors.magic, lineHeight: 19 },

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
  storeIssue: {
    fontFamily: fonts.body,
    fontSize: fontSize.xs,
    color: colors.danger,
    textAlign: 'center',
    paddingHorizontal: spacing.md,
    marginTop: spacing.xs,
  },

  diffCard: { gap: spacing.md },
  diffTitle: { fontFamily: fonts.heading, fontSize: fontSize.lg, color: colors.text },
  diffRow: { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.md },
  diffCheck: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: colors.tintGreen,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 1,
  },
  diffCheckText: { fontFamily: fonts.bodyBold, fontSize: fontSize.sm, color: colors.success },
  // Pro+ kartı: "en popüler" kademenin rengiyle (magic) hizalı → hangi planın
  // ayrıcalığı olduğu okumadan anlaşılsın.
  plusCard: { borderWidth: 1, borderColor: colors.magic },
  plusCheck: { backgroundColor: colors.tintPurple },
  plusCheckText: { color: colors.magic },
  diffBody: { flex: 1, gap: 1 },
  diffRowTitle: { fontFamily: fonts.bodyBold, fontSize: fontSize.md, color: colors.text },
  diffRowSub: { fontFamily: fonts.body, fontSize: fontSize.sm, color: colors.textMuted, lineHeight: 19 },
  diffFree: {
    fontFamily: fonts.body,
    fontSize: fontSize.xs,
    color: colors.textFaint,
    borderTopWidth: 1,
    borderTopColor: colors.track,
    paddingTop: spacing.sm,
  },

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

  legalNote: {
    fontFamily: fonts.body,
    fontSize: fontSize.xs,
    lineHeight: 17,
    color: colors.textFaint,
    textAlign: 'center',
  },
  legalRow: { flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: spacing.sm },
  legalLink: {
    fontFamily: fonts.bodyMedium,
    fontSize: fontSize.xs,
    color: colors.brand,
    textDecorationLine: 'underline',
  },
  legalSep: { fontFamily: fonts.body, fontSize: fontSize.xs, color: colors.textFaint },

  msg: { fontFamily: fonts.bodyMedium, fontSize: fontSize.sm, textAlign: 'center' },
  msgOk: { color: colors.success },
  msgErr: { color: colors.danger },
  devNote: { fontFamily: fonts.body, fontSize: fontSize.xs, color: colors.textMuted, textAlign: 'center', fontStyle: 'italic' },
});
