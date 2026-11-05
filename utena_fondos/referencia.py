"""Fondo de Utena hecho con 'fondo utena.gif' (referencia): el cielo de la referencia, con sus estrellas que titilan, y un cometa que pasa al fondo.

La referencia es un pixel art de 336x224 píxeles ampliado 2x (672x448). Nuestro lienzo nativo es de 63x63, ampliado 2x, así que se recorta
una ventana de 63x63 píxeles nativos y se usa tal cual (misma cuadrícula, sin reescalar). El suelo y la sombra no existen: Utena flota en el espacio.
Las estrellas titilan porque se usan los fotogramas de la referencia (25 fps) tomados a 10 fps. El cometa se dibuja encima, por detrás de Utena,
con los colores de la propia referencia (blanco, celestes, azules y violeta oscuro).

Comentario sobre la referencia: la 'diagonal' que parece una estrella fugaz son estrellas en forma de X fijas que se encienden por turnos; no hay cometa.
"""
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
REF = HERE.parent / "fondo utena.gif"
NC = 63
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0

# colores de la propia referencia, de la cabeza a la punta de la cola
COLA = [(232, 232, 232), (200, 232, 232), (152, 176, 232), (120, 120, 232), (88, 88, 232), (48, 88, 232),
        (48, 0, 176), (48, 0, 120), (0, 0, 120), (0, 0, 48)]
ION = [(0, 232, 232), (0, 152, 232), (0, 88, 200), (0, 48, 200), (0, 0, 176), (0, 0, 120), (0, 0, 48)]
BLANCO = (232, 232, 232)

CROPS = {                     # esquina (x, y) en píxeles nativos de la referencia (336x224)
    "nebulosa": (170, 50),    # la nube roja y azul detrás de Utena
    "nebulosa_der": (215, 75),
    "cumulos": (20, 70),      # cúmulos de puntitos a la izquierda
    "arriba": (75, 0),        # cúmulos y la nube pequeña de arriba
}


def cargar():
    g = Image.open(REF)
    out = []
    for i in range(g.n_frames):
        g.seek(i)
        out.append(np.asarray(g.convert("RGB"))[::2, ::2].copy())          # 224x336 nativos
    return out


def recorte(ref, idx, crop):
    x0, y0 = CROPS[crop]
    return ref[idx % len(ref)][y0:y0 + NC, x0:x0 + NC].copy()


def indice(t):
    """Fotograma de la referencia (25 fps) que corresponde al paso t de Utena (10 fps)."""
    return int(round(t * 2.5))


def px(img, x, y, c):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < img.shape[1] and 0 <= y < img.shape[0]:
        img[y, x] = c


def estrella_fugaz(img, hx, hy, dx, dy, largo=11, ancho=True):
    """Cabeza de 2x2 con halo y una cola delgada que se apaga. (dx, dy) es la dirección del movimiento."""
    n = np.hypot(dx, dy); ux, uy = dx / n, dy / n
    px_, py_ = -uy, ux
    for i in range(largo, 0, -1):
        k = int(i * len(COLA) / (largo + 1))
        cx, cy = hx - ux * i, hy - uy * i
        px(img, cx, cy, COLA[k])
        if ancho and i < largo * 0.45:
            px(img, cx + px_, cy + py_, COLA[min(k + 2, len(COLA) - 1)])
    for ox, oy in ((0, 0), (1, 0), (0, 1), (1, 1)):
        px(img, hx + ox, hy + oy, (255, 255, 255))
    for ox, oy in ((-1, 0), (2, 0), (0, -1), (0, 2), (1, -1), (-1, 1), (2, 1), (1, 2)):
        px(img, hx + ox, hy + oy, COLA[2])


def cometa(img, hx, hy, dx, dy, largo=24, cola=None, ion=None):
    """Cometa grande: cabeza de 3x3 con halo, cola de polvo ancha (con tramado) y cola de iones fina y celeste."""
    cola = COLA if cola is None else cola
    ion = ION if ion is None else ion
    n = np.hypot(dx, dy); ux, uy = dx / n, dy / n
    px_, py_ = -uy, ux
    for i in range(largo, 0, -1):
        k = int(i * len(cola) / (largo + 1))
        w = 1 + int(i * 3.2 / largo)
        for s in range(-w, w + 1):
            cx, cy = hx - ux * i + px_ * s * 0.9, hy - uy * i + py_ * s * 0.9
            borde = abs(s) / (w + 0.5)
            if borde < 0.45 or BAYER[int(round(cy)) % 4, int(round(cx)) % 4] > borde * 0.9:
                px(img, cx, cy, cola[min(k + (1 if abs(s) > 1 else 0), len(cola) - 1)])
    ang = 0.22                                             # la cola de iones sale un poco girada
    ca, sa = np.cos(ang), np.sin(ang)
    vx, vy = ux * ca - uy * sa, ux * sa + uy * ca
    for i in range(2, largo + 6):
        k = int(i * len(ion) / (largo + 7))
        px(img, hx - vx * i, hy - vy * i, ion[min(k, len(ion) - 1)])
    for ox in (-1, 0, 1):
        for oy in (-1, 0, 1):
            px(img, hx + ox, hy + oy, BLANCO)
    px(img, hx, hy, (255, 255, 255))
    for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        px(img, hx + ox, hy + oy, cola[2])


# ------------------------------------------------------------------------------------------ opciones de cometa
def comet_A(img, t):                 # una estrella fugaz rápida que cae casi vertical por el lado izquierdo (pasos 3-9, mientras es agente)
    if 3 <= t <= 9:
        s = (t - 3) / 6.0
        estrella_fugaz(img, 22 - 13 * s, -6 + 66 * s, -13, 66, largo=11)


def comet_B(img, t):                 # un cometa grande y lento que desciende por el lado derecho durante todo el bucle
    s = t / 39.0
    cometa(img, 53 - 8 * s, -22 + 108 * s, -8, 108, largo=24)


def comet_C(img, t):                 # dos estrellas fugaces pequeñas: una por la izquierda (agente) y otra por la derecha (chica mágica)
    if 3 <= t <= 8:
        s = (t - 3) / 5.0
        estrella_fugaz(img, 16 - 7 * s, -4 + 60 * s, -7, 60, largo=8, ancho=False)
    if 25 <= t <= 30:
        s = (t - 25) / 5.0
        estrella_fugaz(img, 47 - 3 * s, -4 + 62 * s, -3, 62, largo=8, ancho=False)


COMETAS = {"A_estrella_fugaz": comet_A, "B_cometa_grande": comet_B, "C_dos_estrellas": comet_C}


def bgf_para(ref, crop, cometa_fn):
    cache = {}

    def bgf(t):
        if t not in cache:
            img = recorte(ref, indice(t), crop)
            if cometa_fn is not None:
                cometa_fn(img, t)
            cache[t] = (img, img)
        return cache[t]
    return bgf
