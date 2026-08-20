import { useAuth, useUser } from "@clerk/expo";
import { Tabs } from "expo-router";
import { useEffect, useState } from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";

import { AuthScreen } from "@/components/auth-screen";
import { RoleGate } from "@/components/role-gate";
import { TabBar } from "@/components/tab-bar";
import { needsDisplayName } from "@/lib/display-name";
import { effectiveRole, type Role } from "@/lib/roles";
import { colors, fonts } from "@/theme/tokens";

/**
 * Uygulamanın kimlik-korumalı kabuğu + alt sekme navigasyonu.
 *
 * GATE (sekme kabuğunun tek giriş kapısı):
 *   yüklenmedi → spinner · giriş yok → SignInForm (tam ekran) ·
 *   adı yok VEYA rolü yok → RoleGate (zorunlu onboarding: ad + rol) · aksi → <Tabs>.
 * ClerkProvider kökte (_layout.tsx) olduğu için hook'lar burada güvenle kullanılır.
 *
 * ROLE-AWARE: her sekmenin bir `roles` izin listesi var. Role dahil değilse `href: null`
 * ile gizlenir. v1'de tüm roller çekirdek 4 sekmeyi görür (öğrenci deneyimi herkese
 * faydalı); öğretmen "Sınıfım" (v2) / veli "Çocuklarım" (v1.5) sekmeleri buraya eklenip
 * roles listesiyle açılacak — mekanizma hazır, yarım ekran shipping yok.
 */

const ALL: Role[] = ["student", "teacher", "parent", "admin"];

type TabDef = {
  name: string;
  title: string;
  roles: Role[];
  headerShown?: boolean;
};

// v1: 4 çekirdek sekme tüm rollere açık. Öğretmen "Sınıfım"/veli "Çocuklarım"
// sekmeleri buraya eklenip roles ile açılacak (ikon/etiket TabBar'da tanımlı).
const TAB_DEFS: TabDef[] = [
  { name: "index", title: "Ana Sayfa", roles: ALL, headerShown: false },
  { name: "create", title: "Oluştur", roles: ALL, headerShown: false },
  { name: "progress", title: "Gelişim", roles: ALL, headerShown: false },
  { name: "profile", title: "Profil", roles: ALL, headerShown: false },
];

function Splash({ slow }: { slow?: boolean }) {
  return (
    <View style={styles.center}>
      <ActivityIndicator size="large" color={colors.brand} />
      {slow ? (
        <Text style={styles.slowText}>
          Giriş servisi (Clerk) yüklenemiyor.{"\n"}İnternet bağlantısını ve anahtarı kontrol et.
        </Text>
      ) : null}
    </View>
  );
}

export default function TabsLayout() {
  const { isLoaded, isSignedIn } = useAuth();
  const { user } = useUser();

  // Clerk 8sn'de yüklenmezse infinite spinner yerine yardımcı uyarı göster.
  const [slow, setSlow] = useState(false);
  useEffect(() => {
    if (isLoaded) return;
    const t = setTimeout(() => setSlow(true), 8000);
    return () => clearTimeout(t);
  }, [isLoaded]);

  if (!isLoaded) return <Splash slow={slow} />;
  if (!isSignedIn) return <AuthScreen />;

  const role = effectiveRole(user);
  // Ad eksikse de aynı kapı: e-posta ile kaydolanlarda Clerk firstName boş gelir ve
  // ekranlar selamlayacak bir şey bulamaz (bkz. lib/display-name.ts).
  if (role === null || needsDisplayName(user)) return <RoleGate />;

  return (
    <Tabs
      tabBar={(props) => <TabBar {...props} />}
      screenOptions={{
        headerTitleStyle: { fontFamily: fonts.headingSemi, color: colors.text },
        headerTintColor: colors.brand,
        headerShadowVisible: false,
        sceneStyle: { backgroundColor: colors.bg },
      }}
    >
      {TAB_DEFS.map((t) => (
        <Tabs.Screen
          key={t.name}
          name={t.name}
          options={{
            title: t.title,
            headerShown: t.headerShown ?? true,
            // Role izin listesinde yoksa sekmeyi gizle (rota yine var, bar'da görünmez).
            href: t.roles.includes(role) ? undefined : null,
          }}
        />
      ))}
    </Tabs>
  );
}

const styles = StyleSheet.create({
  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.bg,
    gap: 16,
    padding: 24,
  },
  slowText: { fontSize: 13, color: colors.textMuted, textAlign: "center" },
});
