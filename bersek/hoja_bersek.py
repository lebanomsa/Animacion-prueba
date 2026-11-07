"""Celdas de la hoja de Special Bersek (bordes magenta sobre fondo verde)."""
import sys
from functools import lru_cache
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "nova"))
import celdas as cd


@lru_cache(None)
def hoja():
    return Image.open(HERE / "fuentes/special_bersek.png").convert("RGBA")


@lru_cache(None)
def celdas():
    a = np.asarray(hoja())
    verde = (a[..., 0] == 0) & (a[..., 1] == 255) & (a[..., 2] == 0) & (a[..., 3] == 255)
    magenta = (a[..., 0] == 255) & (a[..., 1] == 0) & (a[..., 2] == 255) & (a[..., 3] == 255)
    out = []
    for y0, x0, y1, x1, _ in cd.componentes(~verde & ~magenta):
        h, w = y1 - y0 + 1, x1 - x0 + 1
        if 20 <= h <= 400 and 20 <= w <= 700:
            out.append((int(y0), int(x0), int(h), int(w)))
    return sorted(out)


def recorte(c):
    y0, x0, h, w = c
    return hoja().crop((x0, y0, x0 + w, y0 + h))


def region(y0, y1, x0=0, x1=9999):
    return sorted([c for c in celdas() if y0 <= c[0] < y1 and x0 <= c[1] < x1], key=lambda c: c[1])


if __name__ == "__main__":
    cs = celdas(); print(len(cs))
    filas = []
    for c in cs:
        if filas and abs(filas[-1][0][0] - c[0]) <= 12: filas[-1].append(c)
        else: filas.append([c])
    for f in filas:
        f.sort(key=lambda c: c[1])
        print("y", f[0][0], "n", len(f), "alto", sorted(set(c[2] for c in f))[:4], "x", f[0][1], "..", f[-1][1] + f[-1][3])


def sin_borde(img):
    a = np.array(img)
    m = ((a[..., 0] == 255) & (a[..., 1] == 0) & (a[..., 2] == 255)) | ((a[..., 0] == 0) & (a[..., 1] == 255) & (a[..., 2] == 0))
    a[m & (a[..., 3] == 255)] = 0
    ys, xs = np.where(a[..., 3] > 0)
    return Image.fromarray(a[ys.min():ys.max() + 1, xs.min():xs.max() + 1], "RGBA")


def fotogramas(y0, y1, x0, x1):
    return [sin_borde(recorte(c)) for c in region(y0, y1, x0, x1)]


def pies(img):
    """(centro x de las 4 filas más bajas con píxeles opacos, fila inferior)."""
    a = np.asarray(img)[..., 3] > 0
    y1 = np.where(a.any(1))[0].max()
    xs = np.where(a[max(0, y1 - 3):y1 + 1].any(0))[0]
    return (xs.min() + xs.max() + 1) / 2, y1 + 1
