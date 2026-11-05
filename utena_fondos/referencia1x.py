"""Fondo de la referencia para Utena a tamaño natural (1x): la ventana muestra 126x126 píxeles nativos de 'fondo utena.gif' (1 px = 1 px),
el mismo tamaño de píxel que el marco y que Utena. La escena de Utena (63x63) se coloca en el centro del lienzo.

Cometas pensados para esta escala (coordenadas del lienzo de 126x126; la ventana visible es 23..102 y lo de fuera lo tapa el marco).
"""
from pathlib import Path
import numpy as np
import referencia as rf

N = 126
CROPS = {                     # esquina (x, y) en píxeles nativos de la referencia (336x224)
    "A_cielo_oscuro": (110, 30),
    "B_cumulos_y_estrella": (0, 50),
    "C_cielo_de_arriba": (60, 0),
    "D_nebulosa": (210, 60),
}


def recorte(ref, idx, crop):
    x0, y0 = CROPS[crop]
    return ref[idx % len(ref)][y0:y0 + N, x0:x0 + N].copy()


def comet_A(img, t):                 # estrella fugaz rápida en diagonal, de arriba a la derecha a abajo a la izquierda (pasos 3-9)
    if 3 <= t <= 9:
        s = (t - 3) / 6.0
        rf.estrella_fugaz(img, 110 - 88 * s, 12 + 66 * s, -88, 66, largo=12)


def comet_B(img, t):                 # cometa grande y lento: cruza la ventana en diagonal durante todo el bucle
    s = t / 39.0
    rf.cometa(img, 4 + 118 * s, 4 + 96 * s, 118, 96, largo=26)


def comet_C(img, t):                 # dos estrellas fugaces: una con el agente (derecha a izquierda) y otra con la chica mágica (izquierda a derecha)
    if 3 <= t <= 8:
        s = (t - 3) / 5.0
        rf.estrella_fugaz(img, 104 - 70 * s, 22 + 40 * s, -70, 40, largo=9, ancho=False)
    if 25 <= t <= 30:
        s = (t - 25) / 5.0
        rf.estrella_fugaz(img, 26 + 74 * s, 20 + 34 * s, 74, 34, largo=9, ancho=False)


COMETAS = {"A_estrella_fugaz": comet_A, "B_cometa_grande": comet_B, "C_dos_estrellas": comet_C}


def bgf_para(ref, crop, cometa_fn):
    cache = {}

    def bgf(t):
        if t not in cache:
            img = recorte(ref, rf.indice(t), crop)
            if cometa_fn is not None:
                cometa_fn(img, t)
            cache[t] = (img, img)
        return cache[t]
    return bgf
