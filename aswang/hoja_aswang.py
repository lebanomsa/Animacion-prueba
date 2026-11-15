"""Celdas de la hoja de Aswang (fondo blanco, cada fotograma sobre un rectángulo magenta)."""
import sys
from functools import lru_cache
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "nova"))
import celdas as cd

MAGENTA = (248, 0, 248)


@lru_cache(None)
def hoja():
    return Image.open(HERE / "fuentes/aswang.png").convert("RGBA")


@lru_cache(None)
def celdas():
    """Cada fotograma es un bloque no blanco (rectángulo magenta con el sprite encima) separado de los demás por blanco."""
    a = np.asarray(hoja())
    blanco = (a[..., 0] == 255) & (a[..., 1] == 255) & (a[..., 2] == 255)
    magenta = (a[..., 0] == 248) & (a[..., 1] == 0) & (a[..., 2] == 248)
    out = []
    for y0, x0, y1, x1, _ in cd.componentes(~blanco):
        h, w = y1 - y0 + 1, x1 - x0
        if h < 10 or w < 10: continue
        mag = magenta[y0:y1 + 1, x0:x1].mean()
        if mag > 0.3 and w * h >= 200:                 # texto y bordes rojos tienen muy poco magenta
            out.append((int(y0), int(x0), int(h), int(w)))
    return sorted(out)


def recorte(c, transparente=True):
    y0, x0, h, w = c
    a = np.array(hoja().crop((x0, y0, x0 + w, y0 + h)))
    if transparente: a[(a[..., 0] == 248) & (a[..., 1] == 0) & (a[..., 2] == 248)] = 0
    return Image.fromarray(a, "RGBA")


if __name__ == "__main__":
    cs = celdas(); print(len(cs))
    filas = []
    for c in cs:
        if filas and abs(filas[-1][0][0] - c[0]) <= 10: filas[-1].append(c)
        else: filas.append([c])
    for f in filas:
        f.sort(key=lambda c: c[1])
        print("y", f[0][0], "n", len(f), "alto", sorted(set(c[2] for c in f))[:4], "ancho", sorted(set(c[3] for c in f))[:3], "x", f[0][1], "..", f[-1][1] + f[-1][3])


def fila(y0):
    return sorted([c for c in celdas() if y0 - 3 <= c[0] <= y0 + 3], key=lambda c: c[1])


def recorte_sin_borde(c):
    im = recorte(c); a = np.asarray(im)
    ys, xs = np.where(a[..., 3] > 0)
    return Image.fromarray(a[ys.min():ys.max() + 1, xs.min():xs.max() + 1], "RGBA")


def pies(img):
    a = np.asarray(img)[..., 3] > 0
    y1 = np.where(a.any(1))[0].max()
    xs = np.where(a[max(0, y1 - 3):y1 + 1].any(0))[0]
    return (xs.min() + xs.max() + 1) / 2, y1 + 1
