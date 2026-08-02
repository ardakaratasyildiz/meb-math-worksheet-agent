"""Mobil ikon/splash varliklarini kaynak marka gorselinden uretir.

Kaynak: apps/mobile/assets/brand/icon-source.png — tilki maskotunun kare ikon
kompozisyonu (3B render). Bu dosya elle hazirlanan TEK dogruluk kaynagidir;
asagidaki tureviler ondan uretilir, elle duzenlenmez.

Kaynak gorsel bir "sunum" gorseli olabilir (beyaz kenar bosluğu, golge, onceden
yuvarlatilmis kose, sahte 3B kenar parlamasi). Magaza kurallari bunlari kabul
etmez: iOS ikonu KARE ve saydamsiz olmali, koseleri isletim sistemi yuvarlar.
Bu betik onlari temizler:

  1. Beyaz kagit + golgeyi kenardan flood-fill ile ayirir (ic beyazlar korunur).
  2. Sahte kenar parlamasini asindirip cekirdek rengi disa genisletir
     → tuval tamamen dolu, kose bosluğu/beyazlik kalmaz.
  3. Mavi zemini saydamlastirip maskot kesimini cikarir (Android on katmani,
     splash marki, monokrom siluet).

Kullanim:
    python scripts/make_mobile_icons.py                      # varsayilan kaynak
    python scripts/make_mobile_icons.py /yol/yeni-ikon.png   # kaynagi degistir (kopyalanir)

Uretilenler (apps/mobile/assets/images/):
    icon.png                      1024, saydamsiz  — ana ikon (iOS + Android legacy)
    android-icon-foreground.png   1024, saydam     — adaptive on katman (%60 guvenli alan)
    android-icon-monochrome.png   1024, saydam     — Android 13+ temali ikon silueti
    splash-icon.png               1024, saydam     — acilis ekrani marki

Detay: docs/MOBIL_STORE_HAZIRLIK.md §2.
"""

from __future__ import annotations

import shutil
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "apps" / "mobile" / "assets"
SOURCE = ASSETS / "brand" / "icon-source.png"

SIZE = 1024
RIM_ERODE = 20  # sahte 3B kenar parlamasinin kalinligi (kaynak olceginde piksel)
FOREGROUND_SCALE = 0.60  # Android adaptive maskesi dis %33'u kirpar
SPLASH_SCALE = 0.86


def erode(mask: np.ndarray, px: int) -> np.ndarray:
    """Ikili maskeyi ~px piksel ice cek (PIL MinFilter(9) adimi = 4px)."""
    img = Image.fromarray((mask * 255).astype(np.uint8))
    for _ in range(max(1, px // 4)):
        img = img.filter(ImageFilter.MinFilter(9))
    return np.array(img) > 127


def blob_at(mask: np.ndarray, seed: tuple[int, int]) -> np.ndarray:
    """seed'in bagli bileseni. Kucuk parcalari (isilti, nokta) dislar."""
    h, w = mask.shape
    out = np.zeros_like(mask)
    if not mask[seed]:
        return out
    out[seed] = True
    q = deque([seed])
    while q:
        y, x = q.popleft()
        for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not out[ny, nx]:
                out[ny, nx] = True
                q.append((ny, nx))
    return out


def grow_into(pixels: np.ndarray, keep: np.ndarray) -> np.ndarray:
    """keep=False olan pikselleri en yakin keep rengiyle doldurur (kose dolgusu)."""
    out = pixels.copy()
    m = keep.copy()
    while not m.all():
        progressed = False
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            take = (~m) & np.roll(m, (dy, dx), (0, 1))
            if take.any():
                out[take] = np.roll(out, (dy, dx), (0, 1))[take]
                m |= take
                progressed = True
        if not progressed:  # tamamen bos kaynak — sonsuz donguye girme
            break
    return out


def is_blue(rgb: np.ndarray) -> np.ndarray:
    """Marka mavisi zemin maskesi (turuncu/krem/kahve maskot dislanir)."""
    return (rgb[:, :, 2] - np.maximum(rgb[:, :, 0], rgb[:, :, 1]) > 20) & (rgb[:, :, 2] > 95)


def build_icon(src: Path) -> Image.Image:
    """Kaynaktan tam dolu (saydamsiz) kare ikon."""
    im = Image.open(src).convert("RGB")
    arr = np.array(im).astype(np.int16)

    # Ikon kompozisyonunun bbox'i = mavi zeminin sinirlari → merkezleyip kare kirp
    ys, xs = np.where(is_blue(arr))
    if len(xs) == 0:
        raise SystemExit(f"{src}: marka mavisi zemin bulunamadi — kaynak beklenen formatta degil")
    side = max(xs.max() - xs.min() + 1, ys.max() - ys.min() + 1)
    cx, cy = (xs.min() + xs.max()) // 2, (ys.min() + ys.max()) // 2
    box = (cx - side // 2, cy - side // 2, cx - side // 2 + side, cy - side // 2 + side)
    crop = np.array(im.crop(box)).astype(np.int16)

    # Disaridaki beyaz kagit + golge: kenardan flood-fill (ic beyazlar korunur)
    pale = (crop.min(2) > 190) & (crop.max(2) - crop.min(2) < 40)
    content = ~blob_at(pale, (0, 0))

    # Kenar parlamasini at, cekirdek rengi tuvalin tamamina genislet
    filled = grow_into(crop, erode(content, RIM_ERODE))
    return Image.fromarray(filled.astype(np.uint8)).resize((SIZE, SIZE), Image.LANCZOS)


def cutout(icon: Image.Image) -> Image.Image:
    """Maskotu mavi zeminden ayirir (kirpilmis, saydam RGBA)."""
    arr = np.array(icon).astype(np.int16)
    fox = erode(blob_at(~is_blue(arr), (SIZE // 2, SIZE // 2)), 4)
    ys, xs = np.where(fox)
    rgba = np.dstack([np.array(icon), np.where(fox, 255, 0).astype(np.uint8)])
    return Image.fromarray(rgba, "RGBA").crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))


def centered(mark: Image.Image, scale: float) -> Image.Image:
    """Marki SIZE tuvalinde `scale` oraninda ortalar (saydam zemin)."""
    target = int(SIZE * scale)
    w, h = mark.size
    k = target / max(w, h)
    small = mark.resize((max(1, round(w * k)), max(1, round(h * k))), Image.LANCZOS)
    out = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    out.paste(small, ((SIZE - small.width) // 2, (SIZE - small.height) // 2), small)
    return out


def silhouette(mark: Image.Image, scale: float) -> Image.Image:
    """Monokrom (temali) ikon: OS opak pikselleri tek renge boyar → siluet yeter."""
    placed = centered(mark, scale)
    out = Image.new("RGBA", placed.size, (0, 0, 0, 0))
    out.putalpha(placed.getchannel("A").point(lambda v: 255 if v > 128 else 0))
    return out


def main() -> None:
    if len(sys.argv) > 1:  # yeni kaynak verildi → brand/ altina kopyala
        incoming = Path(sys.argv[1])
        if not incoming.is_file():
            raise SystemExit(f"kaynak bulunamadi: {incoming}")
        SOURCE.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(incoming, SOURCE)
        print(f"kaynak kopyalandi -> {SOURCE.relative_to(ROOT)}")
    if not SOURCE.is_file():
        raise SystemExit(f"kaynak yok: {SOURCE} (yol vererek calistir)")

    images = ASSETS / "images"
    images.mkdir(parents=True, exist_ok=True)

    icon = build_icon(SOURCE)
    icon.save(images / "icon.png")

    mark = cutout(icon)
    centered(mark, FOREGROUND_SCALE).save(images / "android-icon-foreground.png")
    silhouette(mark, FOREGROUND_SCALE).save(images / "android-icon-monochrome.png")
    centered(mark, SPLASH_SCALE).save(images / "splash-icon.png")

    # app.json'daki duz arka plan renkleri icin zemin ortalamasi
    arr = np.array(icon).astype(int)
    blue = arr[is_blue(arr)]
    r, g, b = (blue.mean(0) + 0.5).astype(int)
    print(f"uretildi -> {images.relative_to(ROOT)}")
    print(f"zemin rengi (app.json backgroundColor): #{r:02X}{g:02X}{b:02X}")


if __name__ == "__main__":
    main()
