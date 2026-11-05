"""Extracción de los fotogramas de 'drache.png' (hoja de Drache Goldenes, ripeada por SamuelGR/Gestalt).

Las secciones se localizan por bandas de contenido; cada fotograma se recorta por su caja. El rótulo 'VICTORY' (en negro, entre el 3.º y el 4.º
fotograma) se excluye empezando el recorte por debajo de él.
"""
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
SHEET = HERE / "fuentes" / "drache.png"
_cache = {}


def hoja():
    if "im" not in _cache:
        _cache["im"] = Image.open(SHEET).convert("RGBA")
    return _cache["im"]


def segmentos(y0, y1, gap=4, minw=20, x0=0, x1=None):
    """Cajas (x, y, w, h) de los fotogramas de la fila y0..y1: columnas ocupadas separadas por huecos de al menos `gap` columnas."""
    a = np.asarray(hoja())[..., 3] > 10
    x1 = x1 or a.shape[1]
    cols = a[y0:y1, x0:x1].any(0)
    xs = np.nonzero(cols)[0]
    out, st, pv = [], xs[0], xs[0]
    for x in xs[1:]:
        if x - pv > gap:
            out.append((st, pv)); st = x
        pv = x
    out.append((st, pv))
    cajas = []
    for s, e in out:
        r = np.nonzero(a[y0:y1, x0 + s:x0 + e + 1].any(1))[0]
        cajas.append([x0 + s, y0 + int(r.min()), e - s + 1, int(r.max() - r.min() + 1)])
    # los trocitos estrechos (zarpazos sueltos) se unen al fotograma más cercano
    grandes = [c for c in cajas if c[2] >= minw * 3]
    for c in cajas:
        if c[2] < minw * 3:
            j = min(range(len(grandes)), key=lambda k: abs((grandes[k][0] + grandes[k][2] / 2) - (c[0] + c[2] / 2)))
            g = grandes[j]
            nx0, ny0 = min(g[0], c[0]), min(g[1], c[1])
            nx1, ny1 = max(g[0] + g[2], c[0] + c[2]), max(g[1] + g[3], c[1] + c[3])
            grandes[j] = [nx0, ny0, nx1 - nx0, ny1 - ny0]
    return sorted(grandes)


def recorte(caja):
    x, y, w, h = caja
    return hoja().crop((x, y, x + w, y + h))


FILAS = {"idle": (150, 380), "victoria": (1895, 2108)}


def fotogramas(nombre):
    ya, yb = FILAS[nombre]
    return [recorte(c) for c in segmentos(ya, yb)], segmentos(ya, yb)


if __name__ == "__main__":
    for n in FILAS:
        fr, cajas = fotogramas(n)
        print(n, len(fr), [f"{c[2]}x{c[3]}" for c in cajas])


BOTAS = [(96, 80, 80), (64, 48, 72)]


def ancla(img):
    """(x, y) de apoyo de un fotograma: x = centro de las botas, y = fila más baja de las botas (las dos tonos de gris violáceo)."""
    a = np.asarray(img).astype(int)
    m = np.zeros(a.shape[:2], bool)
    for c in BOTAS:
        m |= (a[..., :3] == c).all(-1) & (a[..., 3] > 10)
    ys, xs = np.nonzero(m)
    if len(ys) < 15:
        raise ValueError("no se encontraron las botas")
    return float(xs.mean()), int(ys.max())


BANDAS_EFECTOS = {"polvo_anillo": (3215, 3258), "chispas": (3299, 3345), "pinchos": (3376, 3519), "pepitas": (3562, 3680),
                  "fuego": (3712, 3963), "explosion1": (4006, 4126), "explosion2": (4172, 4298), "humo1": (4330, 4409), "humo2": (4443, 4519)}


def efecto(nombre, minw=4):
    ya, yb = BANDAS_EFECTOS[nombre]
    cajas = segmentos(ya, yb, gap=3, minw=minw)
    return [recorte(c) for c in cajas], cajas
