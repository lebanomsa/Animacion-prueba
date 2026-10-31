"""Vista previa de los reinicios de Percier: de la mano vacía (tras el aspirado) al fotograma 1.0 con la pistola levantada.

  1 cae y la atrapa:  la pistola cae girando desde arriba (giros de 90°) y cae en su mano abierta
  2 de la espalda:    la pistola sube por detrás del cuerpo, asoma por encima y se desliza a su mano
Sin humo ni destellos. Salida en previews/.
"""
import numpy as np
from PIL import Image

import piezas
from opciones_cierre import (C1, CUERPO17, OX17, OY17, PREV, TMP, CW, CH, X_F, Y_F,
                             componer, guardar_gif, pegar, percier, tira)

CUERPO10, PISTOLA = piezas.separar_pistola(C1[0])
BB = PISTOLA.getchannel("A").getbbox()
PIS = PISTOLA.crop(BB)                                   # pistola recortada
PW, PH = PIS.size
P10, (OX10, OY10) = percier(C1[0])
CUERPO10_L = pegar(CUERPO10, OX10, OY10)
CUERPO17_L = pegar(CUERPO17, OX17, OY17)
# ancla = centro de la base de la pistola
A10 = (OX10 + (BB[0] + BB[2]) / 2, OY10 + BB[3])
H17 = (OX17 + 18, OY17 + 68)                              # donde queda la base de la pistola en la mano abierta de 1.7


def giro(img, k):
    return Image.fromarray(np.rot90(np.array(img), k).copy(), "RGBA")


def pistola(cx, cy, k=0, ancla_base=False):
    """Pistola con el centro en (cx, cy), o con el centro de la base en (cx, cy) si ancla_base."""
    g = giro(PIS, k)
    if ancla_base:
        return pegar(g, round(cx - g.width / 2), round(cy - g.height))
    return pegar(g, round(cx - g.width / 2), round(cy - g.height / 2))


def opcion1():
    f = [componer([CUERPO17_L])] * 3
    for (y, k) in ((-34, 3), (-12, 2), (14, 1)):
        f.append(componer([CUERPO17_L, pistola(H17[0], y, k)]))
    f.append(componer([CUERPO17_L, pistola(H17[0], H17[1], 0, True)]))                         # la atrapa
    f.append(componer([CUERPO17_L, pistola(H17[0], H17[1] + 2, 0, True)]))                     # cede un poco al recibir el peso
    f.append(componer([CUERPO17_L, pistola(H17[0], H17[1], 0, True)]))
    mid = ((H17[0] + A10[0]) / 2, (H17[1] + A10[1]) / 2)
    f.append(componer([CUERPO10_L, pistola(*mid, 0, True)]))
    f.append(componer([CUERPO10_L, pistola(*A10, 0, True)]))                                   # = 1.0
    return f


def opcion2():
    cx0 = X_F - 6                                      # centro de la pistola escondida, detrás del cuerpo
    f = [componer([CUERPO17_L])] * 3
    esc = componer([pistola(cx0, 80, 0), CUERPO17_L])                                         # pistola detrás del cuerpo
    f.append(esc)
    f.append(componer([pistola(cx0, 62, 0), CUERPO17_L]))
    f.append(componer([pistola(cx0, 46, 0), CUERPO17_L]))                                     # asoma por encima
    xs = [cx0 - 8, cx0 - 20, H17[0] + 4]
    for i, x in enumerate(xs):
        y = 46 + (H17[1] - PH / 2 - 46) * (i + 1) / len(xs)
        capas = [pistola(x, y, 0), CUERPO17_L] if i < 1 else [CUERPO17_L, pistola(x, y, 0)]
        f.append(componer(capas))
    f.append(componer([CUERPO17_L, pistola(H17[0], H17[1], 0, True)]))
    mid = ((H17[0] + A10[0]) / 2, (H17[1] + A10[1]) / 2)
    f.append(componer([CUERPO10_L, pistola(*mid, 0, True)]))
    f.append(componer([CUERPO10_L, pistola(*A10, 0, True)]))
    return f


if __name__ == "__main__":
    PREV.mkdir(exist_ok=True)
    ref = componer([P10])
    for n, fn, nombre in ((1, opcion1, "cae_y_la_atrapa"), (2, opcion2, "de_la_espalda")):
        fr = fn()
        p = PREV / f"reinicio_{n}_{nombre}.gif"
        nc = guardar_gif(fr, p)
        tira(fr, list(range(2, len(fr)))[:12], PREV / f"reinicio_{n}_{nombre}_pasos.png", titulo=f"Reinicio {n}: {nombre}")
        igual = np.array_equal(np.asarray(fr[-1]), np.asarray(ref))
        print(f"{p.name}: {len(fr)} pasos, {nc} colores, último paso idéntico al 1.0: {igual}")
