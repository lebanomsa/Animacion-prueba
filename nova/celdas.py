"""Detecta las celdas (rectángulos con borde verde) de la hoja de Nova por etiquetado de componentes sobre los píxeles no verdes."""
import json
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).parent


def runs(row):
    d = np.diff(np.concatenate([[0], row.astype(np.int8), [0]]))
    return list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))


def componentes(mask):
    padre = {}
    def f(a):
        while padre[a] != a:
            padre[a] = padre[padre[a]]; a = padre[a]
        return a
    prev, ident, info = [], 0, {}
    for y in range(mask.shape[0]):
        cur = []
        for (a, b) in runs(mask[y]):
            ident += 1; padre[ident] = ident; cur.append((a, b, ident))
            info[ident] = [y, a, y, b]
            for (pa, pb, pid) in prev:
                if pa < b and a < pb:
                    ra, rb = f(ident), f(pid)
                    if ra != rb: padre[rb] = ra
        prev = cur
    cajas = {}
    for i, (y0, x0, y1, x1) in info.items():
        r = f(i)
        c = cajas.setdefault(r, [y0, x0, y1, x1, 0])
        c[0], c[1], c[2], c[3] = min(c[0], y0), min(c[1], x0), max(c[2], y1), max(c[3], x1)
    return list(cajas.values())


def celdas():
    im = np.asarray(Image.open(HERE / "fuentes/nova.png").convert("RGBA"))
    verde = (im[..., 0] == 0) & (im[..., 1] == 255) & (im[..., 2] == 0) & (im[..., 3] == 255)
    out = []
    for y0, x0, y1, x1, _ in componentes(~verde):
        h, w = y1 - y0 + 1, x1 - x0 + 1
        if 10 <= h <= 200 and 10 <= w <= 700:
            out.append((y0, x0, h, w))
    out.sort()
    filas = []
    for c in out:
        if filas and abs(filas[-1][0][0] - c[0]) <= 8: filas[-1].append(c)
        else: filas.append([c])
    for f in filas: f.sort(key=lambda c: c[1])
    return filas


if __name__ == "__main__":
    filas = celdas()
    for f in filas:
        print("y", f[0][0], "n", len(f), "alturas", sorted(set(c[2] for c in f))[:5], "x", f[0][1], "..", f[-1][1] + f[-1][3])
    json.dump([[list(map(int, c)) for c in f] for f in filas], open(HERE / "analisis/celdas.json", "w"))
