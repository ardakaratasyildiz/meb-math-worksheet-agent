"""Play "ozellik grafigi" (1024x500) metnini politika-uyumlu haliyle yeniden yazar.

Neden: 18 Agu 2026'da Play, uygulamayi "Misleading Claims -> Missing Source Link
for Government Information" gerekcesiyle reddetti. Ayni mantik gorsellere de
isliyor: MEB'e atif yapan bir iddia (ornegin "MEB mufredatina uygun sorular")
kaynak + "kurumu temsil etmiyoruz" uyarisi istiyor. Ozellik grafiginde bu iki
seye yer yok -> iddiayi gorselden cikariyoruz ve kucuk bir bagimsizlik notu
ekliyoruz. Metin/kaynak ayagi: docs/PLAY_POLICY_FIX.md.

Betik kaynak gorseli sifirdan cizmez; maskotu ve zemini KORUR:
  1. Arka plandaki dogrusal mavi degrade iki asamali (aykiri-deger eleyen) en
     kucuk kareler ile modellenir.
  2. Yalniz alt baslik bandi bu modelle yeniden boyanir (maskot ve baslik
     dokunulmaz).
  3. Yeni alt baslik + bagimsizlik notu Nunito ile yazilir.

Kullanim:
    python scripts/make_play_feature.py                      # varsayilan yol
    python scripts/make_play_feature.py girdi.png cikti.png
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SRC = Path.home() / "Desktop" / "play-store" / "play-feature-1024x500.png"
DEFAULT_DST = Path.home() / "Desktop" / "play-store" / "play-feature-1024x500-v2.png"

FONT_DIR = ROOT / "node_modules" / "@expo-google-fonts" / "nunito"
FONT_REGULAR = FONT_DIR / "400Regular" / "Nunito_400Regular.ttf"
FONT_SEMIBOLD = FONT_DIR / "600SemiBold" / "Nunito_600SemiBold.ttf"

# Eski metin: "MEB mufredatina uygun sorular" / "1-8. sinif - 5 ders - kagit ve quiz"
# Yeni metin devlet/kurum iddiasi TASIMAZ.
SUBTITLE = ["1-8. sınıf · 5 ders · kazanım bazlı", "Çalışma kağıdı ve quiz · PDF + çözüm"]
# Gorsel artik hicbir devlet/kurum iddiasi tasimadigi icin uyari ZORUNLU DEGIL
# (Google uyariyi *aciklama* metninde ariyor — docs/PLAY_POLICY_FIX.md §3).
# Bos birakilirsa cizilmez; geri istenirse metni buraya yaz.
DISCLAIMER = ""

# Kaynak gorseldeki olculer (piksel). Baslik y=158..232, alt baslik satirlari
# y=257..289 ve y=307..339, metin sol kenari x=82 (probe ile olculdu).
TEXT_LEFT = 82
LINE_TOPS = (257, 307)
SUBTITLE_SIZE = 40
DISCLAIMER_TOP = 374
DISCLAIMER_SIZE = 22
# Yeniden boyanacak bant: alt baslik satirlarini kapsar, ama sol-alt dekoratif
# daireye (y >= ~350) girmez.
REPAINT = (56, 244, 640, 348)
MAX_TEXT_WIDTH = 560  # maskotun soluna tasmasin


def fit_gradient(im: Image.Image, box: tuple[int, int, int, int]) -> list[tuple[float, float, float]]:
    """color(x, y) = c0 + cx*x + cy*y — kanal basina duzlem katsayilari.

    Ornekler tuvalin sol yarisindan alinir; beyaz metin pikselleri ve dekoratif
    dairelerin acik mavisi ikinci gecisde artik (residual) esigiyle elenir.
    """
    px = im.load()
    samples = [
        (x, y, px[x, y])
        for y in range(0, im.height, 3)
        for x in range(0, 620, 3)
        if not (px[x, y][0] > 180 and px[x, y][1] > 190 and px[x, y][2] > 200)
    ]

    def solve(pts: list[tuple[int, int, tuple[int, int, int]]]) -> list[tuple[float, float, float]]:
        n = len(pts)
        sx = sum(p[0] for p in pts)
        sy = sum(p[1] for p in pts)
        sxx = sum(p[0] * p[0] for p in pts)
        syy = sum(p[1] * p[1] for p in pts)
        sxy = sum(p[0] * p[1] for p in pts)
        out = []
        for ch in range(3):
            sv = sum(p[2][ch] for p in pts)
            sxv = sum(p[0] * p[2][ch] for p in pts)
            syv = sum(p[1] * p[2][ch] for p in pts)
            # 3x3 normal denklemler (Cramer)
            a = [[n, sx, sy], [sx, sxx, sxy], [sy, sxy, syy]]
            b = [sv, sxv, syv]
            det = (
                a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1])
                - a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0])
                + a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0])
            )
            coef = []
            for col in range(3):
                m = [row[:] for row in a]
                for row in range(3):
                    m[row][col] = b[row]
                d = (
                    m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
                    - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
                    + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0])
                )
                coef.append(d / det)
            out.append((coef[0], coef[1], coef[2]))
        return out

    model = solve(samples)
    # Ikinci gecis: modele 3 birimden fazla uzak ornekleri (daireler) at.
    kept = []
    for x, y, c in samples:
        err = max(abs(model[ch][0] + model[ch][1] * x + model[ch][2] * y - c[ch]) for ch in range(3))
        if err <= 3.0:
            kept.append((x, y, c))
    return solve(kept) if len(kept) > 100 else model


def repaint(im: Image.Image, model, box: tuple[int, int, int, int]) -> None:
    px = im.load()
    x0, y0, x1, y1 = box
    for y in range(y0, y1):
        for x in range(x0, x1):
            px[x, y] = tuple(
                max(0, min(255, round(model[ch][0] + model[ch][1] * x + model[ch][2] * y)))
                for ch in range(3)
            ) + (255,)


def fitted_font(path: Path, size: int, text: str, draw: ImageDraw.ImageDraw) -> ImageFont.FreeTypeFont:
    """Metin MAX_TEXT_WIDTH'i asarsa punto kucultulur (maskota tasma korumasi)."""
    font = ImageFont.truetype(str(path), size)
    while size > 12:
        if draw.textlength(text, font=font) <= MAX_TEXT_WIDTH:
            return font
        size -= 1
        font = ImageFont.truetype(str(path), size)
    return font


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SRC
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_DST
    if not src.exists():
        raise SystemExit(f"Kaynak bulunamadi: {src}")
    for f in (FONT_REGULAR, FONT_SEMIBOLD):
        if not f.exists():
            raise SystemExit(f"Font bulunamadi: {f} (npm install calistir)")

    im = Image.open(src).convert("RGBA")
    if im.size != (1024, 500):
        raise SystemExit(f"Play ozellik grafigi 1024x500 olmali, gelen: {im.size}")

    model = fit_gradient(im, REPAINT)
    repaint(im, model, REPAINT)

    draw = ImageDraw.Draw(im)
    for text, top in zip(SUBTITLE, LINE_TOPS):
        font = fitted_font(FONT_REGULAR, SUBTITLE_SIZE, text, draw)
        # textbbox ust bosluguna gore hizala → satirlar eski yerlerinde dursun
        bbox = draw.textbbox((0, 0), text, font=font)
        draw.text((TEXT_LEFT, top - bbox[1]), text, font=font, fill=(255, 255, 255, 255))

    if DISCLAIMER:
        font = fitted_font(FONT_SEMIBOLD, DISCLAIMER_SIZE, DISCLAIMER, draw)
        bbox = draw.textbbox((0, 0), DISCLAIMER, font=font)
        draw.text(
            (TEXT_LEFT, DISCLAIMER_TOP - bbox[1]),
            DISCLAIMER,
            font=font,
            fill=(255, 255, 255, 214),  # zeminden ayrilsin ama baslikla yarismasin
        )

    dst.parent.mkdir(parents=True, exist_ok=True)
    im.convert("RGB").save(dst, "PNG", optimize=True)
    print(f"yazildi: {dst} ({dst.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
