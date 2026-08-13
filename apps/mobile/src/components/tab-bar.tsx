/**
 * Özel yüzen alt navigasyon — COMPONENT library: "Rounded floating navigation.
 * Mascot can replace center tab. Navigation should feel premium."
 *
 * Düzen (hedef görsel): Ana · Çöz · [MASKOT FAB] · Kağıt · Gelişim.
 * FAB bir rota değil, hero kısayolu (PSYCHOLOGY: tek hero aksiyon) → Çöz akışını açar.
 *
 * expo-router <Tabs>'a `tabBar={(p) => <TabBar {...p} />}` ile bağlanır. Sistem-
 * varsayılan bar yerine bunu çizer; ikonlar özel SVG (icons.tsx), emoji değil.
 */
import type { BottomTabBarProps } from "@react-navigation/bottom-tabs";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import {
  IconHome,
  IconMagic,
  IconTrend,
  IconUser,
} from "@/components/icons";
import { Mascot } from "@/components/mascot";
import { colors, fonts, radius, shadow } from "@/theme/tokens";

type ItemDef = {
  name: string;
  label: string;
  render: (color: string) => React.ReactNode;
};

const ITEMS: Record<string, ItemDef> = {
  index: { name: "index", label: "Ana Sayfa", render: (c) => <IconHome size={25} color={c} /> },
  create: { name: "create", label: "Oluştur", render: (c) => <IconMagic size={25} color={c} /> },
  progress: { name: "progress", label: "Gelişim", render: (c) => <IconTrend size={25} color={c} /> },
  profile: { name: "profile", label: "Profil", render: (c) => <IconUser size={25} color={c} /> },
};

const LEFT = ["index", "create"];
const RIGHT = ["progress", "profile"];

export function TabBar({ state, navigation }: BottomTabBarProps) {
  const insets = useSafeAreaInsets();

  const activeName = state.routes[state.index]?.name;

  /**
   * `params` GEREKLİ: React Navigation `navigate` çağrısında parametre vermezsen
   * rotanın MEVCUT parametrelerini korur. Ana ekrandan "Alıştırma Çöz" ile bir kez
   * `/create?mode=solve`e gidildiğinde mod sekmeye yapışıyordu → "Ne yapmak
   * istersin?" adımı bir daha hiç görünmüyordu. Sekmeden/FAB'dan girişte modu
   * açıkça "ask"e çekiyoruz (= kullanıcı henüz seçmedi).
   */
  // `navigate`in tipi (rota adı × parametre) birleşimini çözemiyor; iki argümanlı
  // çağrı `never` çakışması veriyor. Tek noktada daraltıp çağırıyoruz.
  const navigateWithParams = (name: string, params?: Record<string, string>) =>
    (navigation.navigate as unknown as (n: string, p?: Record<string, string>) => void)(
      name,
      params,
    );

  const onPress = (name: string, params?: Record<string, string>) => {
    const route = state.routes.find((r) => r.name === name);
    if (!route) {
      navigateWithParams(name, params);
      return;
    }
    const isFocused = activeName === name;
    const event = navigation.emit({
      type: "tabPress",
      target: route.key,
      canPreventDefault: true,
    });
    if (event.defaultPrevented) return;
    // Parametre taşıyan sekmede (create) AYNI sekmeye tekrar basmak da akışı
    // sıfırlamalı: eskiden isFocused olunca hiç navigate edilmiyordu → mod
    // "solve"da takılı kalıyor ve "Ne yapmak istersin?" adımı yine açılmıyordu.
    if (!isFocused || params) {
      navigateWithParams(name, params);
    }
  };

  /** Sekme/FAB girişinde mod sıfırlanmalı; diğer sekmelerin parametresi yok. */
  const paramsFor = (name: string) => (name === "create" ? { mode: "ask" } : undefined);

  const renderTab = (name: string) => {
    const item = ITEMS[name];
    if (!item) return null;
    const focused = activeName === name;
    const color = focused ? colors.brand : colors.textMuted;
    return (
      <Pressable
        key={name}
        style={styles.tab}
        hitSlop={8}
        onPress={() => onPress(name, paramsFor(name))}
        accessibilityRole="button"
        accessibilityLabel={item.label}
        accessibilityState={{ selected: focused }}
      >
        <View style={[styles.iconWrap, focused && styles.iconWrapActive]}>
          {item.render(color)}
        </View>
        {/* "Ana Sayfa" iki kelime — dar sekmede sarmasın/kırpılmasın diye tek satır
            + gerekirse hafif küçülme. */}
        <Text
          style={[styles.label, { color }]}
          numberOfLines={1}
          adjustsFontSizeToFit
          minimumFontScale={0.8}
        >
          {item.label}
        </Text>
      </Pressable>
    );
  };

  return (
    <View style={[styles.host, { paddingBottom: Math.max(insets.bottom, 8) }]} pointerEvents="box-none">
      <View style={[styles.bar, shadow.floating]}>
        {LEFT.map(renderTab)}
        <View style={styles.fabSlot} />
        {RIGHT.map(renderTab)}
      </View>

      {/* Maskot FAB — bar üstüne taşan, hero kısayolu (Oluştur akışı). */}
      <Pressable
        style={[styles.fab, shadow.fab, { bottom: Math.max(insets.bottom, 8) + 22 }]}
        onPress={() => onPress("create", { mode: "ask" })}
        accessibilityRole="button"
        accessibilityLabel="Yeni oluştur"
      >
        <Mascot variant="wink" size={50} animated={false} />
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  host: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    paddingHorizontal: 16,
    alignItems: "center",
  },
  bar: {
    flexDirection: "row",
    alignItems: "center",
    width: "100%",
    height: 66,
    backgroundColor: colors.surface,
    borderRadius: radius.hero,
    paddingHorizontal: 8,
  },
  tab: { flex: 1, alignItems: "center", justifyContent: "center", gap: 2 },
  iconWrap: {
    width: 44,
    height: 30,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: radius.md,
  },
  iconWrapActive: { backgroundColor: colors.tintBlue },
  label: {
    fontFamily: fonts.bodyBold,
    fontSize: 11,
  },
  fabSlot: { width: 68 },
  fab: {
    position: "absolute",
    alignSelf: "center",
    width: 68,
    height: 68,
    borderRadius: 34,
    backgroundColor: colors.brand,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 4,
    borderColor: colors.bg,
    overflow: "hidden",
  },
});
