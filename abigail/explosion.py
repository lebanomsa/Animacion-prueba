"""Carga y alineación de la explosión ('bomba abigail 1.PNG' y 'bomba abigail 2.PNG').

Las dos hojas son una sola secuencia: 2 círculos (oscuro y blanco, que aquí se descarta el oscuro)
y 26 fotogramas de explosión: 10 en la hoja 1 y 16 en la hoja 2. El fondo es verde puro
(0, 255, 0) y la hoja 1 trae restos de un borde (píxeles negros puros y grises 46,46,46) que se quitan.
Los fotogramas no están en una rejilla regular, así que se recortan por su silueta y se alinean
encadenando cada uno con el anterior (máxima superposición de siluetas).
"""
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).parent.parent


def _runs(flags, gap):
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


def _load(name):
    a = np.asarray(Image.open(ROOT / name).convert("RGB")).astype(int)
    green = (a[..., 0] == 0) & (a[..., 1] == 255) & (a[..., 2] == 0)
    art = (a.sum(axis=2) == 0) | ((a[..., 0] == 46) & (a[..., 1] == 46) & (a[..., 2] == 46))
    rgba = np.dstack([a, np.where(~green & ~art, 255, 0)]).astype(np.uint8)
    return rgba


def _frames_of(rgba, y_bands):
    fg = rgba[..., 3] > 0
    out = []
    for (ya, yb) in y_bands:
        for (x0, x1) in _runs(fg[ya:yb].any(axis=0).tolist(), gap=2):
            sub = fg[ya:yb, x0:x1 + 1]
            ys = np.nonzero(sub.any(axis=1))[0]
            y0, y1 = ya + ys.min(), ya + ys.max()
            out.append(Image.fromarray(rgba[y0:y1 + 1, x0:x1 + 1], "RGBA"))
    return out


def raw_frames():
    """(disco blanco, [26 fotogramas de explosión]) recortados por su silueta."""
    s1, s2 = _load("bomba abigail 1.PNG"), _load("bomba abigail 2.PNG")
    f1 = _frames_of(s1, [(0, 55), (55, 114)])      # fila 1: 2 círculos + 4 explosiones; fila 2: 6
    f2 = _frames_of(s2, [(0, 54), (54, 106)])      # 8 + 8
    assert len(f1) == 12 and len(f2) == 16, (len(f1), len(f2))
    return f1[1], f1[2:] + f2


def _mask(img, w, h, ox, oy):
    m = np.zeros((h, w), bool)
    a = np.asarray(img.getchannel("A")) > 0
    m[oy:oy + a.shape[0], ox:ox + a.shape[1]] = a
    return m


def aligned(frames, canvas=(120, 120), search=8):
    """Coloca los fotogramas en un lienzo común. Devuelve (lista de RGBA del tamaño del lienzo,
    lista de (x, y) de la esquina de cada recorte dentro del lienzo)."""
    W, H = canvas
    pos = []
    for k, f in enumerate(frames):
        if k == 0:
            pos.append(((W - f.width) // 2, H - 12 - f.height)); continue
        px, py = pos[-1]
        prev = _mask(frames[k - 1], W, H, px, py)
        best = None
        for dy in range(-search, search + 1):
            for dx in range(-search, search + 1):
                ox, oy = px + dx, py + dy
                if ox < 0 or oy < 0 or ox + f.width > W or oy + f.height > H:
                    continue
                m = _mask(f, W, H, ox, oy)
                inter = (m & prev).sum(); uni = (m | prev).sum()
                # IoU con un pequeño castigo al desplazamiento para que no derive sin motivo
                score = inter / uni - 0.002 * (abs(dx) + abs(dy))
                if best is None or score > best[0]:
                    best = (score, ox, oy)
        pos.append((best[1], best[2]))
    out = []
    for f, (x, y) in zip(frames, pos):
        can = Image.new("RGBA", (W, H), (0, 0, 0, 0)); can.alpha_composite(f, (x, y)); out.append(can)
    return out, pos
