import { useEffect, useState } from "react";
import { AccessibilityInfo, type ImageStyle, type StyleProp } from "react-native";
import Animated, {
  cancelAnimation,
  Easing,
  useAnimatedStyle,
  useSharedValue,
  withRepeat,
  withTiming,
} from "react-native-reanimated";

/**
 * Marka maskotu (tilki) — çok pozlu + hafif animasyonlu.
 *
 * Varyantlar bağlama göre: hero (full) ana ekran/karşılama, yüz ifadeleri
 * (happy/wink/surprised/thinking) durum geri bildirimi, sticker'lar (wave/reading)
 * karşılama/boş-durum. Asset'ler şeffaf PNG (assets/images/mascot/*.png).
 *
 * Animasyon: sürekli, yumuşak "bob" (yukarı-aşağı süzülme) — web'deki animate-bob
 * karşılığı. YALNIZ bu bileşenin içinde; çağrı yerleri <Mascot .../> değişmez.
 * `animated={false}` ile kapatılır; sistem "hareketi azalt" açıksa otomatik kapanır.
 */

const SOURCES = {
  full: require("../../assets/images/mascot/full.png"),
  happy: require("../../assets/images/mascot/happy.png"),
  wink: require("../../assets/images/mascot/wink.png"),
  surprised: require("../../assets/images/mascot/surprised.png"),
  thinking: require("../../assets/images/mascot/thinking.png"),
  wave: require("../../assets/images/mascot/wave.png"),
  reading: require("../../assets/images/mascot/reading.png"),
} as const;

export type MascotVariant = keyof typeof SOURCES;

// Asset'lerin gerçek en-boy oranları (genişlik/yükseklik) — doğru ölçekleme için.
const ASPECT: Record<MascotVariant, number> = {
  full: 0.62,
  happy: 0.97,
  wink: 0.98,
  surprised: 0.99,
  thinking: 0.94,
  wave: 0.73,
  reading: 0.74,
};

const BOB_PX = 5; // süzülme genliği (px)
const BOB_MS = 1700; // yarım döngü süresi

export function Mascot({
  variant = "full",
  size = 96,
  animated = true,
  style,
}: {
  /** Hangi poz/ifade. */
  variant?: MascotVariant;
  /** Maskotun yüksekliği (px). Genişlik varyantın en-boy oranından türetilir. */
  size?: number;
  /** Hafif bob animasyonu (varsayılan açık; reduce-motion'da otomatik kapanır). */
  animated?: boolean;
  style?: StyleProp<ImageStyle>;
}) {
  const [reduceMotion, setReduceMotion] = useState(false);
  const bob = useSharedValue(0);

  useEffect(() => {
    let active = true;
    AccessibilityInfo.isReduceMotionEnabled()
      .then((v) => active && setReduceMotion(v))
      .catch(() => {});
    return () => {
      active = false;
    };
  }, []);

  const play = animated && !reduceMotion;

  useEffect(() => {
    if (!play) {
      cancelAnimation(bob);
      bob.value = 0;
      return;
    }
    // 0→1 gidiş-dönüş, sonsuz tekrar; sinüs easing → yumuşak süzülme.
    bob.value = withRepeat(
      withTiming(1, { duration: BOB_MS, easing: Easing.inOut(Easing.sin) }),
      -1,
      true,
    );
    return () => cancelAnimation(bob);
  }, [play, bob]);

  const animStyle = useAnimatedStyle(() => ({
    transform: [{ translateY: -BOB_PX * bob.value }],
  }));

  return (
    <Animated.Image
      source={SOURCES[variant]}
      style={[
        { width: Math.round(size * ASPECT[variant]), height: size },
        animStyle,
        style,
      ]}
      resizeMode="contain"
      accessible
      accessibilityLabel="Maskot tilki"
    />
  );
}
