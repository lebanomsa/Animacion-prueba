"""Hojas de Percier: recorta los fotogramas, quita el verde/rojo de fondo y devuelve RGBA.

percier 1.PNG  851x120  10 fotogramas (gestos y ataques, el 9º y 10º con el objeto al frente)
percier 2.PNG  290x120  4 fotogramas (reposo con el objeto)
percier 3.PNG  451x70   8 fotogramas (nube de pensamiento: 4 de crecimiento y 4 con el retrato)
Las celdas se dan como (x, ancho) medidas sobre las hojas.
"""
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).parent.parent
CELDAS = {
    1: [(0, 72), (78, 70), (154, 74), (234, 78), (318, 92), (416, 96), (518, 92), (616, 86), (708, 68), (782, 68)],
    2: [(0, 68), (74, 68), (148, 68), (222, 68)],
    3: [(6, 12), (24, 32), (62, 40), (108, 52), (166, 66), (238, 66), (310, 66), (382, 64)],
}
FONDO, SEPARADOR = (0, 255, 0), (255, 0, 0)


def hoja(n):
    a = np.asarray(Image.open(ROOT / f"percier {n}.PNG").convert("RGB")).copy()
    m = (a == FONDO).all(-1) | (a == SEPARADOR).all(-1)
    out = np.zeros(a.shape[:2] + (4,), np.uint8)
    out[..., :3] = a
    out[..., 3] = np.where(m, 0, 255)
    return Image.fromarray(out, "RGBA")


def celdas(n):
    im = hoja(n)
    return [im.crop((x, 0, x + w, im.height)) for x, w in CELDAS[n]]
