"""Extracción de fotogramas de la hoja de Nova (nova/fuentes/nova.png). Las celdas ya vienen con transparencia real (cristal de la cápsula con alfa 127/191)."""
from functools import lru_cache
from pathlib import Path
import numpy as np
from PIL import Image
import celdas

HERE = Path(__file__).parent
SECCIONES = {   # nombre: (y0, y1, x0, x1) región donde buscar las celdas
    "idle": (10, 70, 0, 320),
    "mover": (80, 135, 0, 340),
    "retroceso": (140, 200, 0, 300),
    "patada": (10, 70, 320, 1060),
    "timor": (80, 155, 330, 1700),
    "invicta": (165, 225, 330, 1000),
    "victoria": (380, 435, 0, 350),
    "capsula": (450, 520, 0, 2000),        # 30 fotogramas: 14 de montaje + 16 de bucle
    "nina": (365, 440, 1500, 2060),
}


@lru_cache(None)
def hoja():
    return Image.open(HERE / "fuentes/nova.png").convert("RGBA")


@lru_cache(None)
def _celdas():
    return [c for f in celdas.celdas() for c in f]


def _cs(nombre):
    y0, y1, x0, x1 = SECCIONES[nombre]
    return sorted([c for c in _celdas() if y0 <= c[0] < y1 and x0 <= c[1] < x1], key=lambda c: c[1])


def fotogramas(nombre):
    return [sin_borde(hoja().crop((c[1], c[0], c[1] + c[3], c[0] + c[2]))) for c in _cs(nombre)]


def crudos(nombre):
    """Celdas sin recortar al contenido (solo sin el verde del borde): conservan la posición de Nova dentro de la celda, necesario para Timor."""
    out = []
    for c in _cs(nombre):
        a = np.array(hoja().crop((c[1], c[0], c[1] + c[3], c[0] + c[2])))
        a[(a[..., 0] == 0) & (a[..., 1] == 255) & (a[..., 2] == 0) & (a[..., 3] == 255)] = 0
        out.append(Image.fromarray(a, "RGBA"))
    return out


def sin_borde(img):
    """Quita los píxeles verdes puros del borde de la celda y recorta al contenido (el ancla se calcula con los pies)."""
    a = np.array(img)
    a[(a[..., 0] == 0) & (a[..., 1] == 255) & (a[..., 2] == 0) & (a[..., 3] == 255)] = 0
    ys, xs = np.where(a[..., 3] > 0)
    return Image.fromarray(a[ys.min():ys.max() + 1, xs.min():xs.max() + 1], "RGBA")


def pies(img):
    """Centro horizontal de las 4 filas más bajas con píxeles opacos: sirve de ancla en x. El ancla en y es la fila más baja."""
    a = np.asarray(img)[..., 3] > 0
    ys = np.where(a.any(1))[0]
    y1 = ys.max()
    xs = np.where(a[max(0, y1 - 3):y1 + 1].any(0))[0]
    return (xs.min() + xs.max() + 1) / 2, y1 + 1
