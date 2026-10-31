"""Hojas de Lady: recorta los fotogramas (fila normal y fila arcoíris), quita el fondo y calcula el centro de los pies.

lady.PNG    929x236  13 fotogramas x 2 filas (arriba normal, abajo versión arcoíris con la misma silueta)
lady 2.PNG  413x241   6 fotogramas x 2 filas
Los separadores son magenta (255,0,255), el fondo gris (46,46,46). Las celdas miden 62-78 x 110 px y la suela está en la fila 107.
"""
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).parent.parent
SUELO = 107


def _bloques(m):
    out, s = [], None
    for i, v in enumerate(m):
        if not v and s is None:
            s = i
        if v and s is not None:
            out.append((s, i)); s = None
    if s is not None:
        out.append((s, len(m)))
    return out


def hoja(nombre):
    a = np.asarray(Image.open(ROOT / nombre).convert("RGB")).copy()
    mag = (a == (255, 0, 255)).all(-1)
    cols, filas = _bloques(mag.mean(0) > 0.5), _bloques(mag.mean(1) > 0.5)[:2]
    out = []
    for (y0, y1) in filas:
        fila = []
        for (x0, x1) in cols:
            sub = a[y0:y1, x0:x1]
            fg = ~((sub == (46, 46, 46)).all(-1) | (sub == (255, 0, 255)).all(-1))
            ys, xs = np.where(fg)
            low = fg[ys.max() - 5:ys.max() + 1]
            lx = np.where(low.any(0))[0]
            rgba = np.zeros(sub.shape[:2] + (4,), np.uint8)
            rgba[..., :3] = sub
            rgba[..., 3] = np.where(fg, 255, 0)
            fila.append({"img": Image.fromarray(rgba, "RGBA"), "pies": (lx.min() + lx.max()) / 2})
        out.append(fila)
    return out


_L1, _L2 = hoja("lady.PNG"), hoja("lady 2.PNG")
NORMAL = {f"1.{i}": _L1[0][i] for i in range(13)} | {f"2.{i}": _L2[0][i] for i in range(6)}
ARCO = {f"1.{i}": _L1[1][i] for i in range(13)} | {f"2.{i}": _L2[1][i] for i in range(6)}
# ciclo de llamas: 4..12 de lady.PNG y los 6 de lady 2.PNG (las diferencias entre consecutivos son pequeñas)
LLAMAS = [f"1.{i}" for i in range(4, 13)] + [f"2.{i}" for i in range(6)]
