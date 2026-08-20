import { useAuth, useUser } from "@clerk/expo";
import { useFocusEffect, useRouter, type Href } from "expo-router";
import { useCallback, useEffect, useState, type ReactNode } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import type { ProgressResponse } from "@soruatolyesi/shared";

import {
  HexBadge,
  IconBell,
  IconChart,
  IconChevron,
  IconFire,
  IconGift,
  IconPencil,
  IconPlay,
  IconSpark,
  IconStar,
  IconTarget,
  IconWorksheet,
} from "@/components/icons";
import { AdultHome } from "@/components/home-adult";
import { Mascot } from "@/components/mascot";
import { Card, ProgressBar, SpeechBubble, StatChip } from "@/components/ui";
import { getGamification, getProgress, pingHealth, type GamificationResponse } from "@/lib/api";
import { badgeGlyph, badgeVariant, computeBadges, tierLabel } from "@/lib/badges";
import { displayName } from "@/lib/display-name";
import { requestGenEntry } from "@/lib/gen-entry";
import { getReminderPrefs, syncReminderOnLaunch } from "@/lib/notifications";
import { effectiveRole } from "@/lib/roles";
import { colors, fonts, fontSize, radius, shadow, spacing } from "@/theme/tokens";

/**
 * Ana ekran — "Neşeli Kağıt" kimliği. PSYCHOLOGY bible: ilk 5 saniyede kullanıcı
 * Karşılama + İlerleme + Amaç + Motivasyon görmeli; her ekranda tek hero aksiyon.
 *
 * VERİ: gerçek gamification ucu prod'da doğrulanmış token ister. Dev/Expo Go'da
 * pk_test → prod backend 401 verir (bkz. mobil handoff) → veri gelmezse DEMO
 * değerleriyle hedef tasarımı gösteririz; prod'da gerçek veri otomatik dolar.
 * Günlük hedef / Devam Et / Rozetler henüz uç YOK → görsel kabuk (TODO işaretli).
 */

// Token gelene dek hedef tasarımı canlı gösteren demo değerleri (prod'da override olur).
const DEMO: GamificationResponse = {
  xp: 120,
  level: 3,
  xp_in_level: 20,
  xp_for_next: 50,
  streak_current: 5,
  streak_longest: 5,
  total_active_days: 12,
};

// Günlük soru hedefi (motivasyon nudge'ı — sabit hedef, "çözülen" gerçek veriden).
const DAILY_GOAL = 15;

/** Cihazın yerel (Türkiye) günü — YYYY-MM-DD; daily_trend ile eşleşir. */
function todayStr(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function levelTitle(level: number): string {
  if (level <= 1) return "Acemi";
  if (level <= 3) return "Çırak";
  if (level <= 5) return "Kalfa";
  if (level <= 8) return "Usta";
  return "Üstat";
}

export default function HomeScreen() {
  const { userId } = useAuth();
  const { user } = useUser();
  const router = useRouter();
  const [game, setGame] = useState<GamificationResponse | null>(null);
  const [progress, setProgress] = useState<ProgressResponse | null>(null);
  // Kullanıcı bildirim tercihini hiç belirtmediyse çanda nokta göster (tek seferlik nudge).
  const [notifUndecided, setNotifUndecided] = useState(false);

  const load = useCallback(async () => {
    if (!userId) return;
    const [gg, pp] = await Promise.all([
      getGamification(userId).catch(() => null), // 401/hata → DEMO'ya düşer
      getProgress(userId).catch(() => null),
    ]);
    setGame(gg);
    setProgress(pp);
  }, [userId]);

  useEffect(() => {
    pingHealth();
    void load();
  }, [load]);

  // Tercih AÇIK ama planlama kaybolduysa (yeniden kurulum vb.) sessizce geri kur;
  // hiç seçim yapılmadıysa çandaki noktayı yak.
  useFocusEffect(
    useCallback(() => {
      void (async () => {
        await syncReminderOnLaunch();
        setNotifUndecided((await getReminderPrefs()).enabled === null);
      })();
    }, []),
  );

  const g = game ?? DEMO;
  // Onboarding adı zorunlu kılıyor (bkz. components/role-gate.tsx) ama yine de
  // savunmacı: ad yoksa isimsiz selamla — sabit bir yer tutucu ismi ASLA basma.
  const name = displayName(user);
  const go = (path: string) => () => router.push(path as Href);

  // Gerçek verilerden türet: bugün çözülen / devam et (en zayıf kazanım) / rozetler.
  const todayPoint = progress?.daily_trend?.find((d) => d.date === todayStr());
  const dailyDone = Math.min(todayPoint?.total ?? 0, DAILY_GOAL);
  const weakest = progress?.weak?.[0] ?? null;
  const weakPct = weakest ? Math.round((weakest.ratio <= 1 ? weakest.ratio : weakest.ratio / 100) * 100) : 0;
  const badges = progress ? computeBadges(progress.mastery).slice(0, 4) : [];

  // Öğretmen/veli → sade "yetişkin" ana ekran (oyunlaşma yok). Öğrenci → aşağıdaki oyunsu hub.
  const role = effectiveRole(user);
  if (role === "teacher" || role === "parent") {
    return <AdultHome role={role} name={name} />;
  }

  return (
    <View style={styles.root}>
      <SafeAreaView edges={["top"]} style={styles.safe}>
        <ScrollView
          contentContainerStyle={styles.content}
          showsVerticalScrollIndicator={false}
        >
          {/* ── Üst: selamlama + maskot + çan ─────────────────────────────── */}
          <View style={styles.headerRow}>
            <View style={styles.headerText}>
              <Text style={styles.hello}>{name ? `Merhaba, ${name} 👋` : "Merhaba 👋"}</Text>
              <Text style={styles.subtitle}>Bugün yeni şeyler öğrenme zamanı!</Text>
            </View>
            {/*
              Çan → bildirim ayarları. Nokta YALNIZ kullanıcı henüz seçim yapmadıysa
              yanar (kurulacak bir şey var demek); açıp kapattıktan sonra söner.
              Sürekli yanan sahte bildirim rozeti kullanmıyoruz.
            */}
            <Pressable
              style={styles.bell}
              hitSlop={10}
              accessibilityRole="button"
              accessibilityLabel="Bildirim ayarları"
              onPress={() => router.push('/notifications')}
            >
              <IconBell size={26} dot={notifUndecided} />
            </Pressable>

          </View>

          {/*
            Maskot + balon AYNI SATIRDA, yan yana: balon solda (üste hizalı, kuyruğu
            sağa bakıyor), maskot sağda. Böylece kuyruk maskotun baş hizasına denk
            gelir ve "maskot konuşuyor" okunur. Önceki iki deneme (çiplerin altında,
            sonra header içinde mutlak konumlu maskotun yanında) hizayı tutturamıyordu.
          */}
          <View style={styles.speechRow}>
            <SpeechBubble style={styles.bubble}>
              <Text style={styles.bubbleText}>
                {dailyDone >= DAILY_GOAL ? (
                  <>Bugünkü hedefini tamamladın! 🎉</>
                ) : (
                  <>
                    Hedefe <Text style={styles.bubbleAccent}>{DAILY_GOAL - dailyDone} soru</Text> kaldı! 🎯
                  </>
                )}
              </Text>
            </SpeechBubble>
            <Mascot variant="full" size={128} />
          </View>

          {/* ── Status chip'leri: seri / seviye / XP ──────────────────────── */}
          <View style={styles.chipRow}>
            <StatChip
              icon={<IconFire size={26} />}
              value={`${g.streak_current} gün`}
              label="Seri"
            />
            {/* "Seviye 3" üç çipin dar alanında "Seviy.." diye kırpılıyordu →
                kısa unvan üstte, seviye numarası altta. */}
            <StatChip
              icon={<IconStar size={26} />}
              value={levelTitle(g.level)}
              label={`Seviye ${g.level}`}
            />
            <StatChip
              icon={<IconSpark size={24} />}
              value={`${g.xp} XP`}
              label="Puanın"
            />
          </View>

          {/* ── Günlük Hedef + Serini koru ─────────────────────────────────── */}
          <View style={styles.dualRow}>
            <Card style={styles.goalCard}>
              <View style={styles.goalHead}>
                <Text style={styles.cardTitle}>Günlük Hedef</Text>
                <IconTarget size={22} />
              </View>
              <View style={styles.goalBarRow}>
                <View style={{ flex: 1 }}>
                  <ProgressBar progress={dailyDone / DAILY_GOAL} color={colors.success} />
                </View>
                <View style={styles.goalGift}>
                  <IconGift size={40} />
                </View>
              </View>
              <Text style={styles.goalCount}>
                <Text style={styles.goalCountStrong}>
                  {dailyDone} / {DAILY_GOAL}
                </Text>{" "}
                soru çözdün
              </Text>
              <Text style={styles.goalHint}>
                {dailyDone >= DAILY_GOAL
                  ? "Bugünkü hedefe ulaştın! 🎉"
                  : dailyDone > 0
                    ? "Harika gidiyorsun!"
                    : "Hadi bugüne başlayalım!"}
              </Text>
            </Card>

            <Card style={styles.streakCard}>
              <Text style={styles.streakTitle}>Serini koru!</Text>
              <View style={styles.streakFire}>
                <IconFire size={44} />
              </View>
              <Text style={styles.streakSub}>
                {g.streak_current} gün üst üste harika!
              </Text>
            </Card>
          </View>

          {/* ── Devam Et (hero) ────────────────────────────────────────────── */}
          {/*
            Hero "önce bunu çalış" diyor → yalnız çöz akışını değil, ÖNERİLEN KONUYU da
            taşır: ders/sınıf/ünite hazır gelir, kullanıcı tekrar seçmez. Öneri yoksa
            (weakest null) sade çöz akışı.
          */}
          <Pressable
            onPress={() => {
              requestGenEntry(
                "solve",
                weakest
                  ? {
                      subject: weakest.subject,
                      grade: weakest.grade,
                      kazanimKod: weakest.kazanim_kod,
                      topicName: weakest.topic_name,
                    }
                  : undefined,
              );
              router.push("/create");
            }}
          >
            <Card floating style={styles.continueCard}>
              <View style={styles.continueIcon}>
                <IconWorksheet size={40} tone="#FFFFFF" />
              </View>
              <View style={styles.continueBody}>
                <Text style={styles.continueKicker}>{weakest ? "Önce bunu çalış" : "Bugüne başla"}</Text>
                <Text style={styles.continueTopic}>
                  {weakest ? weakest.topic_name || weakest.kazanim_kod : "Yeni alıştırma"}
                </Text>
                <Text style={styles.continueSub}>
                  {weakest ? "Bu kazanımı geliştirmeye ne dersin?" : "Alıştırma çöz, gelişimini gör"}
                </Text>
                {weakest ? (
                  <>
                    <View style={styles.continueBarWrap}>
                      <ProgressBar progress={weakPct / 100} color="#FFFFFF" height={8} />
                    </View>
                    <Text style={styles.continuePct}>%{weakPct} doğruluk</Text>
                  </>
                ) : null}
              </View>
              <View style={styles.playBtn}>
                <IconPlay size={26} color={colors.success} />
              </View>
            </Card>
          </Pressable>

          {/* ── Aksiyon kartları: Çalışma Kağıdı + Alıştırma Çöz ──────────── */}
          <View style={styles.dualRow}>
            {/*
              Mod ÖNCE bildirilir, sonra gidilir (lib/gen-entry): route parametresi
              sekmeye yapışıp güncellenmediği için o yöntem cihazda çalışmadı.
            */}
            <ActionCard
              bg={colors.brand}
              icon={<IconWorksheet size={44} tone="#FFFFFF" />}
              title={"Çalışma\nKağıdı"}
              sub="Yapay zekâ ile kendi kağıdını üret"
              onPress={() => {
                requestGenEntry("pdf");
                router.push("/create");
              }}
            />
            <ActionCard
              bg={colors.success}
              icon={<IconPencil size={44} />}
              title={"Alıştırma\nÇöz"}
              sub="Alıştırma çöz, puan kazan!"
              onPress={() => {
                requestGenEntry("solve");
                router.push("/create");
              }}
            />
          </View>

          {/* ── Info kartları: Günün Sorusu + Gelişimini Gör ──────────────── */}
          <View style={styles.dualRow}>
            <InfoCard
              bg={colors.tintBlue}
              icon={<IconWorksheet size={34} tone={colors.brand} />}
              title="Ödevlerim"
              sub="Sınıfına katıl, ödevlerini çöz!"
              onPress={go("/assignments")}
            />
            <InfoCard
              bg={colors.tintPink}
              icon={<IconChart size={34} />}
              title="Gelişimini Gör"
              sub="Başarılarını ve gelişimini takip et!"
              onPress={go("/progress")}
            />
          </View>

          {/* ── Son kazanılan rozetler ─────────────────────────────────────── */}
          <Card style={styles.badgeCard}>
            <View style={styles.badgeHead}>
              <Text style={styles.cardTitle}>Son Kazandığın Rozet</Text>
              <Pressable style={styles.seeAll} onPress={go("/progress")} hitSlop={8}>
                <Text style={styles.seeAllText}>Tümünü Gör</Text>
                <IconChevron size={16} color={colors.brand} />
              </Pressable>
            </View>
            {badges.length > 0 ? (
              <View style={styles.badgeRow}>
                {badges.map((b, i) => (
                  <View key={i} style={styles.badgeItem}>
                    <HexBadge size={58} glyph={badgeGlyph(b.tier)} variant={badgeVariant(b.tier)} />
                    <Text style={styles.badgeTitle} numberOfLines={1}>
                      {b.topicName}
                    </Text>
                    <Text style={styles.badgeDesc} numberOfLines={1}>
                      {tierLabel(b.tier)}
                    </Text>
                  </View>
                ))}
              </View>
            ) : (
              <Text style={styles.badgeEmpty}>
                İlk rozetini kazanmak için çözmeye başla! 🎯
              </Text>
            )}
          </Card>
        </ScrollView>
      </SafeAreaView>
    </View>
  );
}

// ── Aksiyon kartı (renkli, büyük ikon sol-üst) ────────────────────────────────
function ActionCard({
  bg,
  icon,
  title,
  sub,
  onPress,
}: {
  bg: string;
  icon: ReactNode;
  title: string;
  sub: string;
  onPress: () => void;
}) {
  return (
    <Pressable style={styles.actionWrap} onPress={onPress}>
      <View style={[styles.actionCard, { backgroundColor: bg }, shadow.card]}>
        <View style={styles.actionIcon}>{icon}</View>
        <Text style={styles.actionTitle}>{title}</Text>
        <Text style={styles.actionSub}>{sub}</Text>
        <View style={styles.actionChevron}>
          <IconChevron size={16} color={bg} />
        </View>
      </View>
    </Pressable>
  );
}

// ── Info kartı (tint zemin, ikon sol) ─────────────────────────────────────────
function InfoCard({
  bg,
  icon,
  title,
  sub,
  onPress,
}: {
  bg: string;
  icon: ReactNode;
  title: string;
  sub: string;
  onPress: () => void;
}) {
  return (
    <Pressable style={styles.actionWrap} onPress={onPress}>
      <View style={[styles.infoCard, { backgroundColor: bg }, shadow.card]}>
        <View style={styles.infoTop}>
          {icon}
          <IconChevron size={16} color={colors.textMuted} />
        </View>
        <Text style={styles.infoTitle}>{title}</Text>
        <Text style={styles.infoSub}>{sub}</Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  safe: { flex: 1 },
  content: {
    padding: spacing.xl,
    paddingBottom: 120, // yüzen tab bar için pay
    gap: spacing.lg,
  },

  // Header (maskot sağda; chip satırı bunun altında → örtüşme yok)
  // Maskot artık header'ın üstünde yüzmüyor (kendi satırında) → yükseklik dayatması
  // ve geniş sağ boşluk gerekmiyor; sağda yalnız çan var.
  headerRow: { justifyContent: "flex-start" },
  headerText: { paddingRight: 56 },
  hello: {
    fontFamily: fonts.heading,
    fontSize: fontSize.display,
    color: colors.text,
  },
  subtitle: {
    fontFamily: fonts.body,
    fontSize: fontSize.md,
    color: colors.textMuted,
    marginTop: spacing.xs,
  },
  bell: {
    position: "absolute",
    top: 4,
    right: 0,
    width: 44,
    height: 44,
    alignItems: "center",
    justifyContent: "center",
  },
  // Balon üste hizalı: SpeechBubble'ın kuyruğu üstten 22px'te, maskotun baş
  // hizasına denk gelsin diye (alignItems: flex-start).
  speechRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: spacing.sm,
    marginTop: spacing.xs,
  },

  // Chips
  chipRow: { flexDirection: "row", gap: spacing.sm },

  // Bubble
  // Satırda kalan tüm genişliği kaplar; maskot sabit 128px.
  bubble: { flex: 1 },
  bubbleText: {
    fontFamily: fonts.bodyBold,
    fontSize: fontSize.md,
    color: colors.text,
  },
  bubbleAccent: { fontFamily: fonts.heading, color: colors.brand },

  // Ortak
  dualRow: { flexDirection: "row", gap: spacing.md },
  cardTitle: {
    fontFamily: fonts.heading,
    fontSize: fontSize.lg,
    color: colors.text,
  },

  // Günlük hedef
  goalCard: { flex: 1.5 },
  goalHead: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: spacing.md,
  },
  goalBarRow: { flexDirection: "row", alignItems: "center", gap: spacing.md },
  goalGift: { marginTop: -4 },
  goalCount: {
    fontFamily: fonts.body,
    fontSize: fontSize.sm,
    color: colors.text,
    marginTop: spacing.md,
  },
  goalCountStrong: { fontFamily: fonts.bodyHeavy, color: colors.text },
  goalHint: {
    fontFamily: fonts.body,
    fontSize: fontSize.sm,
    color: colors.textMuted,
    marginTop: 2,
  },

  // Serini koru
  streakCard: {
    flex: 1,
    backgroundColor: colors.tintPurple,
    alignItems: "center",
    justifyContent: "center",
  },
  streakTitle: {
    fontFamily: fonts.heading,
    fontSize: fontSize.md,
    color: colors.magicDark,
  },
  streakFire: { marginVertical: spacing.sm },
  streakSub: {
    fontFamily: fonts.body,
    fontSize: fontSize.xs,
    color: colors.magicDark,
    textAlign: "center",
    opacity: 0.85,
  },

  // Devam et
  continueCard: {
    backgroundColor: colors.success,
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.lg,
  },
  continueIcon: {
    width: 64,
    height: 64,
    borderRadius: radius.lg,
    backgroundColor: "rgba(255,255,255,0.16)",
    alignItems: "center",
    justifyContent: "center",
  },
  continueBody: { flex: 1 },
  continueKicker: {
    fontFamily: fonts.heading,
    fontSize: fontSize.lg,
    color: colors.onBrand,
  },
  continueTopic: {
    fontFamily: fonts.bodyBold,
    fontSize: fontSize.md,
    color: colors.onBrand,
    marginTop: -2,
  },
  continueSub: {
    fontFamily: fonts.body,
    fontSize: fontSize.xs,
    color: colors.onBrand,
    opacity: 0.9,
    marginTop: 2,
  },
  continueBarWrap: { marginTop: spacing.sm },
  continuePct: {
    fontFamily: fonts.bodyMedium,
    fontSize: fontSize.xs,
    color: colors.onBrand,
    opacity: 0.9,
    marginTop: spacing.xs,
  },
  playBtn: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: "#FFFFFF",
    alignItems: "center",
    justifyContent: "center",
  },

  // Aksiyon / info kart ortak sarmalayıcı
  actionWrap: { flex: 1 },
  actionCard: {
    borderRadius: radius.card,
    padding: spacing.xl,
    minHeight: 172,
  },
  actionIcon: { marginBottom: spacing.md },
  actionTitle: {
    fontFamily: fonts.heading,
    fontSize: fontSize.lg,
    color: colors.onBrand,
    lineHeight: fontSize.lg + 4,
  },
  actionSub: {
    fontFamily: fonts.body,
    fontSize: fontSize.sm,
    color: colors.onBrand,
    opacity: 0.92,
    marginTop: spacing.xs,
    marginBottom: spacing.sm, // ok ile metin arasında nefes payı
  },
  // Ok eskiden position:absolute ile sağ-alta sabitlenmişti → alt yazının son
  // satırının ÜSTÜNE biniyor ve "üret" yarım görünüyordu. Artık normal akışta,
  // marginTop:auto ile kartın altına itiliyor; metinle asla çakışmaz.
  actionChevron: {
    alignSelf: "flex-end",
    marginTop: "auto",
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: "#FFFFFF",
    alignItems: "center",
    justifyContent: "center",
  },

  infoCard: {
    borderRadius: radius.card,
    padding: spacing.xl,
    minHeight: 130,
  },
  infoTop: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: spacing.sm,
  },
  infoTitle: {
    fontFamily: fonts.heading,
    fontSize: fontSize.md,
    color: colors.text,
  },
  infoSub: {
    fontFamily: fonts.body,
    fontSize: fontSize.xs,
    color: colors.textMuted,
    marginTop: 2,
  },

  // Rozetler
  badgeCard: {},
  badgeHead: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: spacing.lg,
  },
  seeAll: { flexDirection: "row", alignItems: "center", gap: 2 },
  seeAllText: {
    fontFamily: fonts.bodyBold,
    fontSize: fontSize.sm,
    color: colors.brand,
  },
  badgeRow: { flexDirection: "row", justifyContent: "space-between" },
  badgeItem: { flex: 1, alignItems: "center", paddingHorizontal: 2 },
  badgeTitle: {
    fontFamily: fonts.bodyBold,
    fontSize: fontSize.xs,
    color: colors.text,
    marginTop: spacing.sm,
  },
  badgeDesc: {
    fontFamily: fonts.body,
    fontSize: 10,
    color: colors.textMuted,
    textAlign: "center",
    marginTop: 1,
  },
  badgeEmpty: {
    fontFamily: fonts.body,
    fontSize: fontSize.sm,
    color: colors.textMuted,
    textAlign: "center",
    paddingVertical: spacing.lg,
  },
});
