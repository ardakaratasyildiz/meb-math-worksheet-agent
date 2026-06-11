# Soru Atölyesi — Tasarım Sistemi

> **Bu, Soru Atölyesi'nin resmi tasarım dilidir (2026-06-11 itibarıyla standart).**
> Tüm yeni frontend geliştirme bu sistemi kullanmalı. İlk uygulaması: `/coz`
> (Çöz & Geliş) öğrenci alanı.

Sıcak, neşeli, çocuk-dostu ama güvenilir bir eğitim markası. "Neşeli çizgi ×
Memphis" harmanından çıkan, oyunsu-ama-temiz bir dil.

---

## 1. Tipografi

| Rol | Font | Kullanım |
|-----|------|----------|
| Başlık / display | **Fredoka** (500/600/700) | `font-display`, tüm h1–h6 |
| Gövde | **Nunito** (400/600/700/800) | `font-playful` / varsayılan gövde |

- `next/font/google` ile `app/layout.tsx`'te yüklü (`--font-fredoka`, `--font-nunito`).
- Eski Inter/Manrope yalnızca tema-dışı (eski) yüzeylerde kalır.

## 2. Renk paleti

| Token | Hex | Rol |
|-------|-----|-----|
| `cream` | `#FFF4EA` | Sıcak zemin (background) |
| ink | `#3A2C4A` | Metin (foreground) |
| `grape` | `#7C5BD6` | **Primary** (butonlar, vurgular) — AA kontrast |
| `coral` | `#FF6B6B` | Sıcak aksan / CTA |
| `sun` | `#FFC93C` | Seri/ödül/uyarı aksanı |
| `mint` | `#3DD9B3` | Başarı / doğru |
| sky | `sky-400/500` (tailwind) | İkincil aksan |

- Zemin düz değil: hafif çok-renkli radial gradient wash (sarı/grape/coral).
- `tailwind.config.ts` → `colors`: `coral, sun, mint, grape, cream` tanımlı.

## 3. Şekil & gölge

- **Köşe yarıçapı:** `--radius: 1.25rem` (belirgin yuvarlak, baloncuk his).
- **Gölgeler (yumuşak renkli "pop"):**
  - `shadow-pop` → `0 8px 0 0 rgba(58,44,74,.10)` (nötr)
  - `shadow-pop-coral`, `shadow-pop-grape`, `shadow-pop-sun`, `shadow-pop-mint`
- **Animasyon:** `animate-bob` (maskot süzülme), `animate-pop-in` (giriş).
- Maskot 🦊 + emoji öğrenci-yüzünde serbest; alıcı-yüzünde (landing) ölçülü.

## 4. Uygulama tekniği — scope'lu tema

shadcn CSS değişkenleri bir **scope class'ında** override edilir; böylece mevcut
`Card`/`Button` gibi bileşenler otomatik bu görünüme bürünür, başka yüzeyler
etkilenmez.

```css
/* app/globals.css */
.coz-theme {
  --background: 28 100% 96%;  /* krem */
  --primary: 258 60% 60%;     /* grape */
  --radius: 1.25rem;
  font-family: var(--font-nunito), system-ui, sans-serif;
  /* + sıcak zemin washı */
}
.coz-theme :is(h1,h2,h3,h4,h5,h6) { font-family: var(--font-fredoka), ...; }
```

```tsx
// İlgili route layout'u
<div className="coz-theme min-h-screen">{children}</div>
```

Yeni bir bölüm/sayfa eklerken: o route'u uygun tema scope'una sar, shadcn
bileşenlerini kullan, başlıklarda Fredoka otomatik gelir, kartlarda `shadow-pop`
ve yuvarlak köşe kullan, primary aksiyonları `grape` yap.

## 5. İkili ton stratejisi (önemli)

Ürün **iki kitleli**: parayı veren **veli/öğretmen** (alıcı) ve kullanan
**öğrenci**. Aynı tokenlar, farklı yoğunluk:

- **Landing & alıcı-yüzü sayfalar** → güven-forward / sakin: maskot/emoji ölçülü,
  yumuşak gölgeler, güven mesajları (iki kez denetim, MEB uyumlu) öne. Oyunsu
  Çöz & Geliş'i bir "vitrin" olarak göster.
- **/coz & öğrenci-yüzü** → tam oyunsu: maskot, emoji, renkli pop kartlar,
  oyunlaştırma (XP/seri/rozet) öne.

## 6. Referans demolar

`design-mockups/` klasöründe (tek-dosya HTML, node gerektirmez):
- `coz-demo-harman.html` → öğrenci alanı tonu
- `landing-demo-harman.html` → landing (güven-forward) tonu
- `15-harman-nese-memphis.html` → harman kaynağı
- `index.html` → 15 yön karşılaştırması
