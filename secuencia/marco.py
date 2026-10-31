"""Marco personalizado: limpieza (igual que el marco azul) y recoloreado con degradado vertical.

  1. Reduce el JPEG de 1024x1024 a su resolución real de 128x128 (mediana de cada bloque 8x8).
  2. Reconstruye el marco simétrico: cuadrante limpio (arriba-derecha) espejado en ambos ejes.
  3. Quita el borde magenta y vacía la ventana interior (transparente).
  4. Recolorea usando el brillo de cada píxel como mapa de tonos y un degradado vertical por bandas.
"""
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).parent.parent
N = 128
BANDS = 12   # número de bandas del degradado vertical (aspecto pixel art, sin degradado suave)

# Paletas por brillo (V entre 0 y 1) -> color.
# Arriba: negro metálico suave (gris casi negro con brillo frío). Abajo: morado.
NEGRO_METALICO = [(0.0, (4, 4, 7)), (0.3, (15, 16, 21)), (0.6, (36, 38, 48)),
                  (0.85, (68, 72, 88)), (1.0, (132, 138, 160))]
MORADO = [(0.0, (8, 2, 20)), (0.3, (34, 10, 68)), (0.6, (72, 28, 132)),
          (0.85, (124, 70, 198)), (1.0, (198, 162, 242))]


def load_native():
    m = np.asarray(Image.open(ROOT / "Marco personalizado.jfif").convert("RGB")).astype(float)
    b = m.reshape(N, 8, N, 8, 3)[:, 2:6, :, 2:6, :]          # centro 4x4 de cada bloque 8x8
    nat = np.median(b.transpose(0, 2, 1, 3, 4).reshape(N, N, 16, 3), axis=2)
    return nat.round().astype(np.uint8)


def symmetrize(nat):
    h = N // 2
    s = nat.copy()
    top_right = nat[:h, h:]                     # la única esquina sin defectos
    s[:h, h:] = top_right
    s[:h, :h] = top_right[:, ::-1]
    s[h:, h:] = top_right[::-1, :]
    s[h:, :h] = top_right[::-1, ::-1]
    return s


def ramp(stops, v):
    xs = [s[0] for s in stops]
    return np.stack([np.interp(v, xs, [s[1][c] for s in stops]) for c in range(3)], axis=-1)


def recolor(rgb, top_stops, bot_stops):
    y_index = np.repeat(np.arange(N)[:, None], N, axis=1)
    lum = rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114
    v = np.clip(lum / np.percentile(lum, 98), 0, 1)
    t = np.minimum((y_index * BANDS // N), BANDS - 1) / (BANDS - 1)
    top, bot = ramp(top_stops, v), ramp(bot_stops, v)
    return (top + (bot - top) * t[..., None]).round().astype(np.uint8)


def build(top_stops=NEGRO_METALICO, bot_stops=MORADO):
    """Devuelve (marco RGBA de 128x128 con la ventana transparente, (x0, y0, x1, y1) de la ventana)."""
    sym = symmetrize(load_native())
    r, g, b = (sym[..., i].astype(int) for i in range(3))
    magenta = (r > 180) & (b > 180) & (g < 90)
    green = (g > r + 15) & (g > b + 15) & (g > 50)
    ys, xs = np.where(green)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    alpha = np.full((N, N), 255, np.uint8)
    alpha[magenta] = 0
    alpha[y0:y1 + 1, x0:x1 + 1] = 0
    frame = Image.fromarray(np.dstack([recolor(sym, top_stops, bot_stops), alpha]), "RGBA")
    return frame, (int(x0), int(y0), int(x1), int(y1))
