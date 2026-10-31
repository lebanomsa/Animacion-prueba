"""Carga de las hojas de Agalia ('agalia 1.PNG', 'agalia efectos.PNG', 'agalia humo.PNG').

El fondo de las tres es un naranja salmón (225, 147, 86) que aquí se vuelve transparente.
  - agalia 1: 12 fotogramas de la transformación, recortados por su silueta (no hay rejilla regular).
  - efectos: 16 fotogramas de chispas, en una rejilla de 40 px: el origen común es el centro de cada celda.
  - humo: 26 fotogramas (2 filas de 13) en una rejilla de unos 46,4 px: el origen común es el centro de cada celda.
"""
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).parent.parent
BG = (225, 147, 86)


def _load(name):
    a = np.asarray(Image.open(ROOT / name).convert("RGB")).astype(int)
    m = (a[..., 0] == BG[0]) & (a[..., 1] == BG[1]) & (a[..., 2] == BG[2])
    return np.dstack([a, np.where(m, 0, 255)]).astype(np.uint8)


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


def personaje():
    """12 fotogramas de la transformación. Devuelve [dict(img, x0, y0)] con la posición en la hoja."""
    rgba = _load("agalia 1.PNG")
    fg = rgba[..., 3] > 0
    out = []
    for (x0, x1) in _runs(fg.any(axis=0).tolist(), gap=1):
        ys = np.nonzero(fg[:, x0:x1 + 1].any(axis=1))[0]
        y0, y1 = int(ys.min()), int(ys.max())
        out.append(dict(img=Image.fromarray(rgba[y0:y1 + 1, x0:x1 + 1], "RGBA"), x0=x0, y0=y0))
    assert len(out) == 12, len(out)
    return out


def _grid(name, cell_w, x_first_center, row_bands, n_cols, pad_y=0):
    """Recorta una hoja de celdas regulares. Cada fotograma se devuelve con el centro de su celda como origen:
    (img, ox, oy) donde (ox, oy) es la posición de la esquina del recorte respecto al centro horizontal
    de la celda y a la fila central de su banda."""
    rgba = _load(name)
    frames = []
    for (ya, yb) in row_bands:
        for k in range(n_cols):
            cx = x_first_center + cell_w * k
            xa, xb = int(round(cx - cell_w / 2)), int(round(cx + cell_w / 2))
            sub = rgba[ya:yb, max(xa, 0):min(xb, rgba.shape[1])]
            a = sub[..., 3] > 0
            if not a.any():
                continue
            ys, xs = np.nonzero(a)
            x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
            img = Image.fromarray(sub[y0:y1 + 1, x0:x1 + 1], "RGBA")
            frames.append(dict(img=img, ox=int(x0 + max(xa, 0) - cx), oy=int(y0), band=(ya, yb)))
    return frames


def efectos():
    """16 fotogramas de chispas. oy es la fila del recorte dentro de la banda (y 0..48)."""
    f = _grid("agalia efectos.PNG", 40.0, 32.0, [(0, 49)], 16)
    assert len(f) == 16, len(f)
    return f


def humo():
    """26 fotogramas del humo (2 filas de 13)."""
    f = _grid("agalia humo.PNG", 46.4, 29.5, [(0, 50), (50, 105)], 13)
    assert len(f) == 26, len(f)
    return f
