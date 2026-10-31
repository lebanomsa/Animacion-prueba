"""Escenario de Lady: tormenta con relámpago (hoja 'stage lady.png') en ventanas de 128x128 píxeles nativos (x5 = 640 px).

Capas: cielo (se repite cada 304 px), silueta de almenas negras, muro de piedra, cubierta de madera.
Relámpago: los 8 fragmentos de 100x46 (L0 brillante .. L7 apagado) y los 7 de 195x35 (R0..R6) se pegan sobre el cielo en las
posiciones donde encajan (L: x=212,y=53; R: x=261,y=0 en el cielo de 612x228) y se repiten con el período del cielo.
"""
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).parent.parent
PERIODO = 304
L_POS, R_POS = (212, 53), (261, 0)


def cargar():
    im = Image.open(ROOT / "stage lady.png").convert("RGBA")
    sky = im.crop((13, 88, 625, 316))
    L = [im.crop((632, y, 732, y + 46)) for y in (89, 137, 185, 233, 280, 327, 374, 421)]
    R = [im.crop((x, y, x + 195, y + 35)) for x, y in ((740, 90), (740, 186), (740, 233), (740, 280), (740, 327), (739, 375), (739, 420))]
    return {"cielo": sky, "L": L, "R": R,
            "silueta": im.crop((12, 348, 360, 392)), "cubierta": im.crop((12, 401, 592, 478)), "muro": im.crop((12, 492, 364, 529))}


P = cargar()


def cielo_ancho(n_rep=3):
    """Cielo repetido en horizontal: un período de 304 px, n_rep veces."""
    base = P["cielo"].crop((0, 0, PERIODO, 228))
    w = Image.new("RGBA", (PERIODO * n_rep, 228))
    for k in range(n_rep):
        w.paste(base, (k * PERIODO, 0))
    return w


def pegar(dst, src, x, y):
    dst.alpha_composite(src, (int(x), int(y))) if (x >= 0 and y >= 0 and x + src.width <= dst.width and y + src.height <= dst.height) else _recorte(dst, src, int(x), int(y))


def _recorte(dst, src, x, y):
    sx, sy = max(-x, 0), max(-y, 0)
    dx, dy = max(x, 0), max(y, 0)
    w, h = min(src.width - sx, dst.width - dx), min(src.height - sy, dst.height - dy)
    if w > 0 and h > 0:
        dst.alpha_composite(src.crop((sx, sy, sx + w, sy + h)), (dx, dy))


def ventana(variante, paso, x0=198, sy0=15, glow=True):
    """Ventana de 128x128 RGBA en el paso `paso` del relámpago (0..7 = destello, otro valor = reposo)."""
    # se usa el cielo original (612 px, sin repetirlo: el patrón no es exactamente periódico y dejaría una costura)
    sky = P["cielo"].copy()
    if 0 <= paso < 8:
        pegar(sky, P["L"][paso], L_POS[0], L_POS[1])
        if paso < 7:
            pegar(sky, P["R"][paso], R_POS[0], R_POS[1])
    win = Image.new("RGBA", (128, 128), (1, 18, 18, 255))
    win.alpha_composite(sky.crop((x0, sy0, x0 + 128, sy0 + 128)))
    if variante == "A":
        pegar(win, P["cubierta"].crop((100, 0, 228, 44)), 0, 84)
    elif variante == "B":
        pegar(win, P["silueta"].crop((0, 0, 128, 24)), 0, 62)
        pegar(win, P["cubierta"].crop((100, 0, 228, 44)), 0, 84)
    elif variante == "C":
        pegar(win, P["muro"].crop((0, 0, 128, 37)), 0, 62)
        pegar(win, P["cubierta"].crop((100, 0, 228, 44)), 0, 99)
    if glow and 0 <= paso <= 2:                            # destello ambiente suave en los primeros pasos
        a = np.asarray(win).astype(float)
        k = (0.16, 0.10, 0.05)[paso]
        a[..., :3] = a[..., :3] + (np.array([150, 230, 230]) - a[..., :3]) * k
        win = Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")
    return win


def lady_referencia():
    """Primer fotograma de Lady (fila de arriba de lady.PNG) sin fondo, para ver la escala."""
    a = np.asarray(Image.open(ROOT / "lady.PNG").convert("RGB")).copy()
    mag = (a == (255, 0, 255)).all(-1)
    cols = mag.mean(0) > 0.5
    rows = mag.mean(1) > 0.5
    xs = np.where(cols)[0]; ys = np.where(rows)[0]
    # primera celda: entre el primer y el segundo separador de columnas / filas
    def rangos(idx):
        out, s = [], None
        for i in range(idx.min(), idx.max() + 2):
            if i in set(idx):
                if s is not None and i - 1 > s:
                    out.append((s, i - 1)); s = None
                s = i
        return out
    cx = [i for i in range(len(cols)) if not cols[i]]
    cy = [i for i in range(len(rows)) if not rows[i]]
    x0 = cx[0]; x1 = x0
    while x1 + 1 < len(cols) and not cols[x1 + 1]:
        x1 += 1
    y0 = cy[0]; y1 = y0
    while y1 + 1 < len(rows) and not rows[y1 + 1]:
        y1 += 1
    sub = a[y0:y1 + 1, x0:x1 + 1]
    rgba = np.zeros(sub.shape[:2] + (4,), np.uint8)
    rgba[..., :3] = sub
    rgba[..., 3] = np.where((sub == (46, 46, 46)).all(-1) | (sub == (255, 0, 255)).all(-1), 0, 255)
    im = Image.fromarray(rgba, "RGBA")
    return im.crop(im.getchannel("A").getbbox())
