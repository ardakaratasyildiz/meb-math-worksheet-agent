import { useAuth, useUser } from "@clerk/expo";
import { Tabs } from "expo-router";
import { ActivityIndicator, StyleSheet, View } from "react-native";

import { RoleGate } from "@/components/role-gate";
import { SignInForm } from "@/components/sign-in-form";
import { TabBar } from "@/components/tab-bar";
import { effectiveRole, type Role } from "@/lib/roles";
import { colors, fonts } from "@/theme/tokens";

/**
 * Uygulamanın kimlik-korumalı kabuğu + alt sekme navigasyonu.
 *
 * GATE (sekme kabuğunun tek giriş kapısı):
 *   yüklenmedi → spinner · giriş yok → SignInForm (tam ekran) ·
 *   rol yok → RoleGate (zorunlu onboarding) · aksi → <Tabs>.
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

function Splash() {
  return (
    <View style={styles.center}>
      <ActivityIndicator size="large" color={colors.brand} />
    </View>
  );
}

export default function TabsLayout() {
  const { isLoaded, isSignedIn } = useAuth();
  const { user } = useUser();

  if (!isLoaded) return <Splash />;
  if (!isSignedIn) return <SignInForm />;

  const role = effectiveRole(user);
  if (role === null) return <RoleGate />;

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
  },
});
