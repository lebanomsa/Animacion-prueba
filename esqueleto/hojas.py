"""Hojas del esqueleto: recorta los fotogramas, quita el fondo gris (46,46,46) y calcula el punto de apoyo.

esqueleto 1.PNG  291x121  3 fotogramas (apunta y dispara)
esqueleto 2.PNG  206x103  2 fotogramas (zancada y golpe dorado)
esqueleto 3.PNG  487x130  5 fotogramas (arma al hombro y festejo con el arma arriba)
Cada fotograma se devuelve con la fila de suela (la más baja del conjunto) y la columna de anclaje: el centro de masa de
las partes del cuerpo, sin contar el arma ni el golpe dorado (que son naranja, marrón u oliva), para que no bailen al cambiar de pose.
"""
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).parent.parent
FONDO = (46, 46, 46)
SUELO_HOJA = {1: 95, 2: 85, 3: 107}          # fila de suela de cada hoja (fila más baja de la mayoría de los fotogramas)


def _runs(fg):
    cols = fg.any(0)
    out, s = [], None
    for x, v in enumerate(cols):
        if v and s is None:
            s = x
        if not v and s is not None:
            out.append((s, x)); s = None
    if s is not None:
        out.append((s, len(cols)))
    return out


def es_arma(rgb):
    """Naranja, marrón, dorado u oliva: el arma y el golpe."""
    r, g, b = rgb[..., 0].astype(int), rgb[..., 1].astype(int), rgb[..., 2].astype(int)
    calido = (r > g + 8) & (g >= b - 4)                      # marrones, naranjas, dorados
    oliva = (r >= b + 25) & (g >= b + 25)                    # verde oliva del cañón
    return calido | oliva


def hoja(n):
    im = Image.open(ROOT / f"esqueleto {n}.PNG").convert("RGB")
    a = np.asarray(im)
    fg = ~(a == FONDO).all(-1)
    out = []
    for x0, x1 in _runs(fg):
        sub = a[:, x0:x1]
        m = fg[:, x0:x1]
        rgba = np.zeros(sub.shape[:2] + (4,), np.uint8)
        rgba[..., :3] = sub
        rgba[..., 3] = np.where(m, 255, 0)
        cuerpo = m & ~es_arma(sub)
        ys, xs = np.where(cuerpo)
        out.append({"img": Image.fromarray(rgba, "RGBA"), "ancla_x": float(xs.mean()),
                    "suelo": SUELO_HOJA[n], "hoja": n, "x0": x0})
    return out


def todos():
    h1, h2, h3 = hoja(1), hoja(2), hoja(3)
    return {"1.0": h1[0], "1.1": h1[1], "1.2": h1[2], "2.0": h2[0], "2.1": h2[1],
            "3.0": h3[0], "3.1": h3[1], "3.2": h3[2], "3.3": h3[3], "3.4": h3[4]}
