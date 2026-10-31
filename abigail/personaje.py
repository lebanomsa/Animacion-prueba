"""Carga y alineación de los 13 fotogramas de Abigail ('abigail 1.PNG' x10 y 'abigail 2.PNG' x3).

El fondo es verde puro (0, 255, 0). La hoja 1 trae un borde negro de 1 px (columnas 0 y 533, fila 53)
que se ignora; el negro del interior del dibujo es parte del sprite y se conserva.
Los fotogramas no están en una rejilla: se separan por columnas vacías. En vertical se respeta la
altura de cada uno respecto a la línea del suelo de su hoja (fila 43 en la hoja 1, fila 33 en la 2),
y en horizontal se centran (los cinco últimos, tumbada, se alinean por superposición de la silueta
para que el cuerpo no se desplace cuando solo cambia la melena).
"""
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).parent.parent
GROUND = {1: 43, 2: 33}       # fila del suelo en cada hoja


def _runs(flags):
    out, s = [], None
    for i, f in enumerate(flags):
        if f and s is None:
            s = i
        if not f and s is not None:
            out.append((s, i - 1)); s = None
    if s is not None:
        out.append((s, len(flags) - 1))
    return out


def _sheet(name, sheet_id):
    a = np.asarray(Image.open(ROOT / name).convert("RGB")).astype(int)
    h, w, _ = a.shape
    green = (a[..., 0] == 0) & (a[..., 1] == 255) & (a[..., 2] == 0)
    fg = ~green
    if sheet_id == 1:                       # borde negro de la hoja 1
        fg[:, 0] = False; fg[:, w - 1] = False; fg[h - 1, :] = False
    rgba = np.dstack([a, np.where(fg, 255, 0)]).astype(np.uint8)
    frames = []
    for (x0, x1) in _runs(fg.any(axis=0).tolist()):
        sub = fg[:, x0:x1 + 1]
        ys = np.nonzero(sub.any(axis=1))[0]
        y0, y1 = int(ys.min()), int(ys.max())
        frames.append(dict(img=Image.fromarray(rgba[y0:y1 + 1, x0:x1 + 1], "RGBA"),
                           y0=y0, y1=y1, sheet=sheet_id))
    return frames


def raw_frames():
    f = _sheet("abigail 1.PNG", 1) + _sheet("abigail 2.PNG", 2)
    assert len(f) == 13, len(f)
    return f


def _mask(img, w, h, ox, oy):
    m = np.zeros((h, w), bool)
    a = np.asarray(img.getchannel("A")) > 0
    m[oy:oy + a.shape[0], ox:ox + a.shape[1]] = a
    return m


def placed(canvas=(140, 120), ground=96, cx=70):
    """Devuelve (lista de lienzos RGBA con cada fotograma colocado, lista de (x, y) de cada recorte)."""
    W, H = canvas
    fr = raw_frames()
    pos = []
    for k, f in enumerate(fr):
        img = f["img"]
        y = ground + (f["y0"] - GROUND[f["sheet"]])
        x = cx - img.width // 2
        if k >= 8:                          # fotogramas 9..13: tumbada. Alinear con el anterior
            px, py = pos[-1]
            prev = _mask(fr[k - 1]["img"], W, H, px, py)
            best = None
            for dx in range(-6, 7):
                m = _mask(img, W, H, x + dx, y)
                score = (m & prev).sum() / (m | prev).sum() - 0.003 * abs(dx)
                if best is None or score > best[0]:
                    best = (score, x + dx)
            x = best[1] if k > 8 else x
        pos.append((x, y))
    out = []
    for f, (x, y) in zip(fr, pos):
        c = Image.new("RGBA", (W, H), (0, 0, 0, 0)); c.alpha_composite(f["img"], (x, y)); out.append(c)
    return out, pos
