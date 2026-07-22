import { Image, type ImageStyle, type StyleProp } from "react-native";

/**
 * Marka maskotu (tilki) — şimdilik STATİK, çok pozlu.
 *
 * Varyantlar bağlama göre seçilir: hero (full) ana ekran/karşılama, yüz ifadeleri
 * (happy/wink/surprised/thinking) durum geri bildirimi, sticker'lar (wave/reading)
 * karşılama/boş-durum. Asset'ler şeffaf PNG (kaynak paketten PIL ile temizlendi:
 * kenar beyaz→şeffaf + en büyük bileşen + kırp). assets/images/mascot/*.png.
 *
 * Tasarım niyeti: çağrı yerleri <Mascot variant=".." size={..} /> SABİT kalsın;
 * animasyon (zıplama/göz kırpma) sonra YALNIZ bu bileşenin içinde eklenecek
 * (reanimated ile Image→Animated.Image + bob döngüsü) → hiçbir ekran değişmez.
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

export function Mascot({
  variant = "full",
  size = 96,
  style,
}: {
  /** Hangi poz/ifade. */
  variant?: MascotVariant;
  /** Maskotun yüksekliği (px). Genişlik varyantın en-boy oranından türetilir. */
  size?: number;
  style?: StyleProp<ImageStyle>;
}) {
  return (
    <Image
      source={SOURCES[variant]}
      style={[{ width: Math.round(size * ASPECT[variant]), height: size }, style]}
      resizeMode="contain"
      accessible
      accessibilityLabel="Maskot tilki"
    />
  );
}
