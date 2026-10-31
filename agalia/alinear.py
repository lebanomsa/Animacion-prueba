"""Alineación del personaje de 'agalia 1': en vertical se respetan las alturas de la hoja (origen común)
y en horizontal cada fotograma se encadena con el anterior por máximo solape de silueta (IoU)."""
import numpy as np
from PIL import Image

import hojas

CW, CH = 240, 175        # lienzo (ancho para que quepan las chispas a los lados)
CX = 120                 # columna central del primer fotograma
Y_OFF = 50               # fila del lienzo donde está la fila 28 de la hoja (la más alta del personaje)


def _mask(img, x, y):
    m = np.zeros((CH, CW), bool)
    a = np.asarray(img.getchannel("A")) > 0
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + a.shape[1], CW), min(y + a.shape[0], CH)
    if x1 > x0 and y1 > y0:
        m[y0:y1, x0:x1] = a[y0 - y:y1 - y, x0 - x:x1 - x]
    return m


def personaje_alineado(search=14):
    P = hojas.personaje()
    pos = []
    for k, f in enumerate(P):
        img = f["img"]; y = Y_OFF + (f["y0"] - 28)
        if k == 0:
            x = CX - img.width // 2
        else:
            px, _ = pos[-1]
            prev = _mask(P[k - 1]["img"], px, Y_OFF + (P[k - 1]["y0"] - 28))
            best = None
            for dx in range(-search, search + 1):
                x_try = px + (P[k - 1]["img"].width - img.width) // 2 + dx
                m = _mask(img, x_try, y)
                score = (m & prev).sum() / max((m | prev).sum(), 1) - 0.002 * abs(dx)
                if best is None or score > best[0]:
                    best = (score, x_try)
            x = best[1]
        pos.append((x, y))
    frames = []
    for f, (x, y) in zip(P, pos):
        c = Image.new("RGBA", (CW, CH), (0, 0, 0, 0)); c.alpha_composite(f["img"], (x, y)); frames.append(c)
    return frames, pos
