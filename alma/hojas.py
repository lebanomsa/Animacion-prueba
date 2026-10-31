"""Carga de las cuatro hojas de Alma (alma 1, alma 2, alam 3, alma 4): 9 + 8 + 5 + 7 = 29 fotogramas.

El fondo de las cuatro es un gris oscuro (46, 46, 46) que aquí se vuelve transparente.
  alma 1: criatura felina de pelo rubio y cola de tigre, acurrucada, con la cola meneándose.
  alma 2: se levanta, de acurrucada a casi a cuatro patas.
  alma 3: el pelo se eriza, estalla en esquirlas doradas y se disuelve en una nube de luz.
  alma 4: de la luz emerge la forma humana, de rodillas y de espaldas, con el pelo largo.
Cada fotograma se recorta por su silueta (no hay rejilla regular) y conserva su fila dentro de la hoja.
"""
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).parent.parent
BG = (46, 46, 46)
HOJAS = ["alma 1.PNG", "alma 2.PNG", "alam 3.PNG", "alma 4.PNG"]     # "alam 3" lleva el nombre con las letras cambiadas
ESPERADOS = [9, 8, 5, 7]


def _runs(flags, gap=1):
    out, s, last = [], None, None
    for i, f in enumerate(flags):
        if f:
            if s is None:
                s = i
            last = i
        elif s is not None and i - last > gap:
            out.append((s, last)); s = None
    if s is not None:
        out.append((s, last))
    return out


def fotogramas():
    """Lista de 29 dict(img, hoja, n, x0, y0, y1): imagen RGBA recortada y su posición en la hoja."""
    out = []
    for h, (name, esperados) in enumerate(zip(HOJAS, ESPERADOS)):
        a = np.asarray(Image.open(ROOT / name).convert("RGB")).astype(int)
        m = (a[..., 0] == BG[0]) & (a[..., 1] == BG[1]) & (a[..., 2] == BG[2])
        rgba = np.dstack([a, np.where(m, 0, 255)]).astype(np.uint8)
        fg = ~m
        segs = _runs(fg.any(axis=0).tolist(), gap=1)
        assert len(segs) == esperados, (name, len(segs), esperados)
        for n, (x0, x1) in enumerate(segs):
            ys = np.nonzero(fg[:, x0:x1 + 1].any(axis=1))[0]
            y0, y1 = int(ys.min()), int(ys.max())
            out.append(dict(img=Image.fromarray(rgba[y0:y1 + 1, x0:x1 + 1], "RGBA"), hoja=h, n=n, x0=x0, y0=y0, y1=y1))
    return out
