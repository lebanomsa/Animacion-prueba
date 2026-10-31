"""Limpia y recolorea 'Marco personalizado.jfif' (azul oscuro arriba -> azul cielo noche abajo).

Pasos:
  1. Reduce el JPEG de 1024x1024 a su resolución real de 128x128 (mediana de cada bloque 8x8).
  2. Reconstruye el marco simétrico: se toma el cuadrante limpio (arriba-derecha) y se
     espeja en horizontal y vertical.
  3. Quita el borde magenta y vacía la ventana interior (transparente).
  4. Recolorea usando el valor (brillo) de cada píxel como mapa de tonos y un degradado vertical.

Salida (./out): frame_blue_128.png, frame_blue_1024.png, preview_blue_1024.png
"""
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
OUT = HERE / "out"
OUT.mkdir(exist_ok=True)
N, SCALE = 128, 8

# Paletas por brillo (V): (V, color). Arriba azul marino, abajo azul de cielo nocturno.
TOP = [(0.0, (1, 2, 10)), (0.3, (5, 10, 36)), (0.6, (11, 22, 68)),
       (0.85, (24, 46, 110)), (1.0, (62, 92, 160))]
BOT = [(0.0, (4, 6, 26)), (0.3, (16, 26, 74)), (0.6, (38, 68, 148)),
       (0.85, (78, 120, 208)), (1.0, (176, 206, 252))]
BANDS = 12   # número de bandas del degradado vertical (look pixel art)


def load_native():
    m = np.asarray(Image.open(HERE / "Marco personalizado.jfif").convert("RGB")).astype(float)
    b = m.reshape(N, 8, N, 8, 3)[:, 2:6, :, 2:6, :]          # centro 4x4 de cada bloque
    nat = np.median(b.transpose(0, 2, 1, 3, 4).reshape(N, N, 16, 3), axis=2)
    return nat.round().astype(np.uint8)


def symmetrize(nat):
    h = N // 2
    s = nat.copy()
    # Una sola esquina buena (arriba-derecha) espejada en ambos ejes: el brillo queda
    # idéntico arriba y abajo y no aparece un corte a media altura.
    top_right = nat[:h, h:]
    s[:h, h:] = top_right
    s[:h, :h] = top_right[:, ::-1]
    s[h:, h:] = top_right[::-1, :]
    s[h:, :h] = top_right[::-1, ::-1]
    return s


def ramp(stops, v):
    xs = [s[0] for s in stops]
    return np.stack([np.interp(v, xs, [s[1][c] for s in stops]) for c in range(3)], axis=-1)


def recolor(rgb, y_index):
    # luminancia percibida, normalizada con el percentil 98 para aprovechar todo el rango
    lum = rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114
    v = np.clip(lum / np.percentile(lum, 98), 0, 1)
    t = np.minimum((y_index * BANDS // N), BANDS - 1) / (BANDS - 1)   # (N,N) por filas
    top, bot = ramp(TOP, v), ramp(BOT, v)
    out = top + (bot - top) * t[..., None]
    return out.round().astype(np.uint8)


def main():
    nat = load_native()
    sym = symmetrize(nat)

    r, g, b = (sym[..., i].astype(int) for i in range(3))
    magenta = (r > 180) & (b > 180) & (g < 90)
    green = (g > r + 15) & (g > b + 15) & (g > 50)
    ys, xs = np.where(green)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    print("ventana interior (px lógicos): x", x0, "-", x1, " y", y0, "-", y1,
          " tamaño", x1 - x0 + 1, "x", y1 - y0 + 1)

    y_index = np.repeat(np.arange(N)[:, None], N, axis=1)
    col = recolor(sym, y_index)
    alpha = np.full((N, N), 255, np.uint8)
    alpha[magenta] = 0
    alpha[y0:y1 + 1, x0:x1 + 1] = 0
    frame = Image.fromarray(np.dstack([col, alpha]), "RGBA")
    frame.save(OUT / "frame_blue_128.png")
    big = frame.resize((N * SCALE, N * SCALE), Image.NEAREST)
    big.save(OUT / "frame_blue_1024.png")

    # vista previa: fondo recortado a cuadrado y escalado x5 dentro de la ventana
    fondo = Image.open(HERE / "fondo.png").convert("RGBA")
    side = fondo.height
    crop = fondo.crop(((fondo.width - side) // 2, 0, (fondo.width - side) // 2 + side, side))
    crop = crop.resize((side * 5, side * 5), Image.NEAREST)
    wx, wy = x0 * SCALE, y0 * SCALE
    ww, wh = (x1 - x0 + 1) * SCALE, (y1 - y0 + 1) * SCALE
    prev = Image.new("RGBA", big.size, (0, 0, 0, 255))
    prev.alpha_composite(crop, (wx + (ww - crop.width) // 2, wy + (wh - crop.height) // 2))
    prev.alpha_composite(big)
    prev.save(OUT / "preview_blue_1024.png")
    print("ok ->", OUT)


if __name__ == "__main__":
    main()
