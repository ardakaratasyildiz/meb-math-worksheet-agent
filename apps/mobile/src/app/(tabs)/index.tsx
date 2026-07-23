import { useAuth, useUser } from "@clerk/expo";
import { useRouter, type Href } from "expo-router";
import { useCallback, useEffect, useState, type ReactNode } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

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
  type BadgeGlyph,
} from "@/components/icons";
import { AdultHome } from "@/components/home-adult";
import { Mascot } from "@/components/mascot";
import { Card, ProgressBar, SpeechBubble, StatChip } from "@/components/ui";
import { getGamification, pingHealth, type GamificationResponse } from "@/lib/api";
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

// TODO(backend): "bugün çözülen soru" ucu yok → şimdilik görsel kabuk değerleri.
const DAILY_DONE = 7;
const DAILY_GOAL = 15;

// TODO(backend): "devam et" (son yarım kalan konu) ucu yok → görsel kabuk.
const CONTINUE = { topic: "Kesirler", sub: "Kesirlerde Toplama İşlemi", pct: 65 };

// TODO(backend): mobilde rozet ucu yok (web lib/badges.ts port edilecek) → görsel kabuk.
const BADGES: { title: string; desc: string; glyph: BadgeGlyph; variant: string }[] = [
  { title: "İlk Adım", desc: "5 soru çözdün", glyph: "trophy", variant: "bronze" },
  { title: "Odaklı", desc: "10 doğru yaptın", glyph: "target", variant: "teal" },
  { title: "Azimli", desc: "5 gün seri yaptın", glyph: "fire", variant: "ember" },
  { title: "Başarılı", desc: "Seviye 3 oldun", glyph: "star", variant: "royal" },
];

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

  const load = useCallback(async () => {
    if (!userId) return;
    try {
      setGame(await getGamification(userId));
    } catch {
      setGame(null); // dev'de 401 → DEMO'ya düşer
    }
  }, [userId]);

  useEffect(() => {
    pingHealth();
    void load();
  }, [load]);

  const g = game ?? DEMO;
  const firstName = user?.firstName ?? "Arda";
  const go = (path: string) => () => router.push(path as Href);

  // Öğretmen/veli → sade "yetişkin" ana ekran (oyunlaşma yok). Öğrenci → aşağıdaki oyunsu hub.
  const role = effectiveRole(user);
  if (role === "teacher" || role === "parent") {
    return <AdultHome role={role} name={firstName} />;
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
              <Text style={styles.hello}>Merhaba, {firstName} 👋</Text>
              <Text style={styles.subtitle}>Bugün yeni şeyler öğrenme zamanı!</Text>
            </View>
            <Pressable style={styles.bell} hitSlop={10} onPress={() => {}}>
              <IconBell size={26} dot />
            </Pressable>
            <View style={styles.mascotWrap} pointerEvents="none">
              <Mascot variant="full" size={150} />
            </View>
          </View>

          {/* ── Status chip'leri: seri / seviye / XP ──────────────────────── */}
          <View style={styles.chipRow}>
            <StatChip
              icon={<IconFire size={26} />}
              value={`${g.streak_current} gün`}
              label="Seri"
            />
            <StatChip
              icon={<IconStar size={26} />}
              value={`Seviye ${g.level}`}
              label={levelTitle(g.level)}
            />
            <StatChip
              icon={<IconSpark size={24} />}
              value={`${g.xp} XP`}
              label="Puanın"
            />
          </View>

          {/* ── Maskot konuşma balonu ─────────────────────────────────────── */}
          <SpeechBubble style={styles.bubble}>
            <Text style={styles.bubbleText}>
              Bugün seni bekleyen <Text style={styles.bubbleAccent}>3 görev</Text> var! 🎉
            </Text>
          </SpeechBubble>

          {/* ── Günlük Hedef + Serini koru ─────────────────────────────────── */}
          <View style={styles.dualRow}>
            <Card style={styles.goalCard}>
              <View style={styles.goalHead}>
                <Text style={styles.cardTitle}>Günlük Hedef</Text>
                <IconTarget size={22} />
              </View>
              <View style={styles.goalBarRow}>
                <View style={{ flex: 1 }}>
                  <ProgressBar progress={DAILY_DONE / DAILY_GOAL} color={colors.success} />
                </View>
                <View style={styles.goalGift}>
                  <IconGift size={40} />
                </View>
              </View>
              <Text style={styles.goalCount}>
                <Text style={styles.goalCountStrong}>
                  {DAILY_DONE} / {DAILY_GOAL}
                </Text>{" "}
                soru çözdün
              </Text>
              <Text style={styles.goalHint}>Harika gidiyorsun!</Text>
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
          <Pressable onPress={go("/create")}>
            <Card floating style={styles.continueCard}>
              <View style={styles.continueIcon}>
                <IconWorksheet size={40} tone="#FFFFFF" />
              </View>
              <View style={styles.continueBody}>
                <Text style={styles.continueKicker}>Devam Et</Text>
                <Text style={styles.continueTopic}>{CONTINUE.topic}</Text>
                <Text style={styles.continueSub}>{CONTINUE.sub}</Text>
                <View style={styles.continueBarWrap}>
                  <ProgressBar progress={CONTINUE.pct / 100} color="#FFFFFF" height={8} />
                </View>
                <Text style={styles.continuePct}>%{CONTINUE.pct} tamamlandı</Text>
              </View>
              <View style={styles.playBtn}>
                <IconPlay size={26} color={colors.success} />
              </View>
            </Card>
          </Pressable>

          {/* ── Aksiyon kartları: Çalışma Kağıdı + Alıştırma Çöz ──────────── */}
          <View style={styles.dualRow}>
            <ActionCard
              bg={colors.brand}
              icon={<IconWorksheet size={44} tone="#FFFFFF" />}
              title={"Çalışma\nKağıdı"}
              sub="Yapay zekâ ile kendi kağıdını üret"
              onPress={go("/create")}
            />
            <ActionCard
              bg={colors.success}
              icon={<IconPencil size={44} />}
              title={"Alıştırma\nÇöz"}
              sub="Alıştırma çöz, puan kazan!"
              onPress={go("/create")}
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
            <View style={styles.badgeRow}>
              {BADGES.map((b) => (
                <View key={b.title} style={styles.badgeItem}>
                  <HexBadge size={58} glyph={b.glyph} variant={b.variant as never} />
                  <Text style={styles.badgeTitle} numberOfLines={1}>
                    {b.title}
                  </Text>
                  <Text style={styles.badgeDesc} numberOfLines={2}>
                    {b.desc}
                  </Text>
                </View>
              ))}
            </View>
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
  headerRow: { minHeight: 158, justifyContent: "flex-start" },
  headerText: { paddingRight: 120 },
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
  mascotWrap: {
    position: "absolute",
    right: -14,
    top: 8,
  },

  // Chips
  chipRow: { flexDirection: "row", gap: spacing.sm },

  // Bubble
  bubble: { maxWidth: "82%", marginTop: spacing.xs },
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
  },
  actionChevron: {
    position: "absolute",
    right: spacing.lg,
    bottom: spacing.lg,
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
});
