"""Piezas derivadas de las hojas de Percier: Percier sin el objeto, el objeto suelto, la nube y el retrato."""
from collections import deque

import numpy as np
from PIL import Image

import hojas

CREMA = (248, 248, 232)          # color de la nube


def centro_pies(img):
    a = np.asarray(img)[..., 3] > 0
    xs = np.where(a[104:117].any(0))[0]
    return (xs.min() + xs.max()) / 2


def es_naranja(p):
    r, g, b = int(p[0]), int(p[1]), int(p[2])
    return r >= 150 and g >= 70 and b <= 70 and r > g + 30


def separar_objeto(c):
    """De 1.7 (objeto bajado a la izquierda) devuelve (cuerpo sin objeto, objeto). Retoque a mano del contorno del tentáculo."""
    a = np.array(c)
    zona = np.zeros(a.shape[:2], bool)
    zona[40:76, :24] = True
    zona[60:100, :14] = True
    quitar = zona & (a[..., 3] > 0)
    for y, x in zip(*np.where(quitar)):
        if es_naranja(a[y, x]) and (y >= 63 or x >= 20):     # el tentáculo se queda
            quitar[y, x] = False
    obj = a.copy(); obj[~quitar] = 0
    cuerpo = a.copy(); cuerpo[quitar] = 0
    # contorno negro alrededor del extremo del tentáculo
    op = cuerpo[..., 3] > 0
    for y in range(40, 96):
        for x in range(0, 28):
            if not op[y, x]:
                vec = [op[y + dy, x + dx] for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))
                       if 0 <= y + dy < a.shape[0] and 0 <= x + dx < a.shape[1]]
                if any(vec) and quitar[y, x] | (x < 28):
                    cuerpo[y, x] = (0, 0, 0, 255)
    return Image.fromarray(cuerpo, "RGBA"), Image.fromarray(obj, "RGBA")


def separar_nube(c):
    """De la nube con retrato devuelve (nube sola, retrato). La nube es el crema conectado con el exterior."""
    a = np.array(c)
    h, w = a.shape[:2]
    crema = (a[..., :3] == CREMA).all(-1) & (a[..., 3] > 0)
    visto = np.zeros((h, w), bool)
    q = deque()
    for y in range(h):
        for x in range(w):
            if crema[y, x] and any(not (0 <= y + dy < h and 0 <= x + dx < w) or a[y + dy, x + dx, 3] == 0
                                   for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                visto[y, x] = True; q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w and crema[yy, xx] and not visto[yy, xx]:
                visto[yy, xx] = True; q.append((yy, xx))
    nube_px = visto
    retrato = a.copy(); retrato[nube_px] = 0
    # el resto de píxeles de color no crema que rodean al retrato y no son de la nube (p. ej. el tono claro de la esquina)
    nube = a.copy(); nube[(a[..., 3] > 0) & ~nube_px] = 0
    return Image.fromarray(nube, "RGBA"), Image.fromarray(retrato, "RGBA")


def separar_pistola(c):
    """De 1.0 (pistola levantada a la izquierda) devuelve (cuerpo sin pistola, pistola). La mano (tentáculo naranja) se queda."""
    a = np.array(c)
    h, w = a.shape[:2]
    zona = np.zeros((h, w), bool)
    zona[14:33, :28] = True
    zona[33:41, :26] = True
    zona[41:74, :25] = True
    quitar = zona & (a[..., 3] > 0)
    for y, x in zip(*np.where(quitar)):
        if es_naranja(a[y, x]) and y >= 69:
            quitar[y, x] = False
    pis = a.copy(); pis[~quitar] = 0
    cuerpo = a.copy(); cuerpo[quitar] = 0
    return Image.fromarray(cuerpo, "RGBA"), Image.fromarray(pis, "RGBA")
