"""Carga y recorte de los sprites: Matilda (Postura.PNG) y la bomba de humo (sprite bomba.PNG)."""
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).parent.parent
MAG = (248, 0, 248)

# Lienzo común: las poses de Matilda se alinean por los pies (borde inferior) y por la izquierda
CANVAS_W, CANVAS_H = 172, 194
M_X, M_BASE = 24, 172          # x de la celda de Matilda y fila de los pies (borde inferior)


def _key(img):
    """Convierte el magenta en transparente."""
    img = img.convert("RGBA")
    a = np.asarray(img).copy()
    mask = (a[..., 0] == MAG[0]) & (a[..., 1] == MAG[1]) & (a[..., 2] == MAG[2])
    a[mask] = (0, 0, 0, 0)
    return Image.fromarray(a, "RGBA")


def matilda_frames():
    """(arriba x4, abajo x6). Cada fotograma ya es transparente, del tamaño de su celda."""
    sheet = Image.open(ROOT / "Postura.PNG").convert("RGBA")
    top = [_key(sheet.crop((13 + 140 * i, 7, 13 + 140 * i + 122, 7 + 124))) for i in range(4)]
    bot = [_key(sheet.crop((13 + 140 * i, 191, 13 + 140 * i + 124, 191 + 134))) for i in range(6)]
    return top, bot


def smoke_frames():
    """Las 26 celdas de humo (celdas 2 a 27; las 2 primeras son círculos y no se usan)."""
    sheet = Image.open(ROOT / "sprite bomba.PNG").convert("RGBA")
    cells = []
    for r in range(4):
        for c in range(7):
            cells.append(_key(sheet.crop((2 + 90 * c, 130 * r, 2 + 90 * c + 81, 130 * r + 120))))
    return cells[2:]


def place_matilda(frame):
    """Coloca un fotograma de Matilda en el lienzo común (pies en M_BASE)."""
    can = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    can.alpha_composite(frame, (M_X, M_BASE - frame.height))
    return can
