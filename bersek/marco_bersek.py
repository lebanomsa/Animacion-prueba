"""Marcos de Special Bersek: el marco de siempre (secuencia/marco.py) con tres paletas, detalles estáticos y animados.
Coordenadas de 128x128 (ventana 24..103; banda exterior de 4 px). 43 pasos: salto 7..20, aterrizaje y pilar de fuego 21..42.
  brasa   : carbón oscuro arriba, brasa roja y naranja abajo; grietas de lava y chispas que suben
  hierro  : hierro negro arriba, carmesí abajo; vetas rojas como las de su armadura y rayos que recorren el borde
  violeta : violeta sombrío arriba, naranja fuego abajo; llamas en las esquinas de abajo y gema que se enciende
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "nova")); sys.path.insert(0, str(HERE.parent / "secuencia"))
import marco
import marco_nova as mn           # Pincel, agrupar

PALETAS = {
    "brasa": ([(0.0, (6, 6, 8)), (0.3, (22, 22, 28)), (0.6, (48, 46, 54)), (0.85, (92, 88, 98)), (1.0, (160, 156, 168))],
              [(0.0, (24, 4, 2)), (0.3, (86, 16, 6)), (0.6, (170, 48, 12)), (0.85, (236, 110, 24)), (1.0, (255, 200, 90))]),
    "hierro": ([(0.0, (4, 4, 6)), (0.3, (16, 16, 20)), (0.6, (36, 36, 44)), (0.85, (70, 70, 82)), (1.0, (130, 130, 146))],
               [(0.0, (18, 2, 4)), (0.3, (62, 8, 12)), (0.6, (120, 16, 22)), (0.85, (186, 30, 34)), (1.0, (255, 120, 110))]),
    "violeta": ([(0.0, (6, 3, 12)), (0.3, (22, 12, 44)), (0.6, (52, 30, 92)), (0.85, (96, 64, 150)), (1.0, (170, 140, 220))],
                [(0.0, (24, 8, 2)), (0.3, (86, 34, 6)), (0.6, (170, 84, 12)), (0.85, (236, 150, 30)), (1.0, (255, 225, 130))]),
}
SALTO, FUEGO = range(7, 21), range(21, 43)


def fase(t):
    return t in FUEGO, t in (21, 22)


def perimetro():
    """Camino cerrado por la franja exterior (x/y 2 y 125), en sentido horario."""
    return [(x, 2) for x in range(2, 126)] + [(125, y) for y in range(3, 126)] + [(x, 125) for x in range(124, 1, -1)] + [(2, y) for y in range(124, 2, -1)]


# ------------------------------------------------------------------ brasa
def det_brasa(p, t):
    fuego, flash = fase(t)
    claro = ((255, 236, 150) if flash else (255, 196, 80)) if fuego else None
    c1, c2 = (claro, claro) if fuego else ((190, 56, 14), (240, 110, 24))
    col = c1 if (t // 3) % 2 == 0 else c2
    zig = [0, 1, 2, 1, 0, 1, 2, 1]
    for y0 in (14, 40, 66, 92):                                 # grietas de lava en los laterales
        for k in range(14):
            p.put(2 + zig[k % 8], y0 + k, col); p.put(124 - zig[k % 8], y0 + k, col)
    # chispas que suben por los laterales
    for lado, x in ((0, 3), (1, 124)):
        for k in range(5):
            y = 120 - ((t * 3 + k * 23 + lado * 11) % 112)
            tono = (120, 40, 14) if y < 40 else (240, 110, 24) if y < 80 else (255, 210, 100)
            p.put(x + (k % 2 if lado == 0 else -(k % 2)), y, tono)
            if y > 80: p.put(x + (k % 2 if lado == 0 else -(k % 2)), y + 1, (240, 110, 24))
    # barra de brasa arriba al centro, más brillante con el fuego
    barra = (255, 220, 120) if fuego else (190, 60, 16)
    p.rect(58, 2, 12, 2, barra)
    p.put(58, 2, (60, 20, 8)); p.put(69, 2, (60, 20, 8))


# ------------------------------------------------------------------ hierro y vetas rojas
def det_hierro(p, t):
    fuego, flash = fase(t)
    base = (214, 40, 36)
    if flash: col = (255, 240, 220)
    elif t in (23, 24, 25): col = (255, 150, 130)
    else: col = (255, 90, 80) if fuego and t % 4 < 2 else base
    for x in range(14, 114): p.put(x, 2, col); p.put(x, 125, col)
    for y in range(14, 114): p.put(2, y, col); p.put(125, y, col)
    for x in range(40, 88): p.put(x, 3, (110, 14, 18)); p.put(x, 124, (110, 14, 18))
    # tres arañazos en cada esquina
    for (x0, y0, dx) in ((6, 1, 1), (121, 1, -1), (6, 122, 1), (121, 122, -1)):
        for j in range(3):
            for k in range(3):
                p.put(x0 + dx * (j * 3 + k), y0 + k if y0 < 64 else y0 + 2 - k, (150, 22, 26))
    # rayo que recorre el borde: cabeza blanca y cola roja con zigzag
    per = perimetro()
    cab = int(t * len(per) / 43) % len(per)
    for k in range(18):
        x, y = per[(cab - k) % len(per)]
        jx, jy = ((k % 3) - 1, 0) if y in (2, 125) else (0, (k % 3) - 1)
        p.put(x + jx * (1 if y == 2 or x == 125 else -1) * (k // 6 % 2), y + jy * (1 if x == 2 or y == 125 else -1) * (k // 6 % 2),
              (255, 245, 235) if k < 3 else (255, 120, 110) if k < 9 else (150, 24, 28))


# ------------------------------------------------------------------ violeta y llamas
LLAMA = [[".X...", ".XX..", "XXX.X", "XXXXX", "XXXXX", ".XXX."],
         ["..X..", ".XXX.", ".XXXX", "XXXXX", "XXXXX", ".XXX."],
         ["...X.", "X.XX.", "XXXXX", "XXXXX", "XXXXX", ".XXX."]]


def det_violeta(p, t):
    fuego, flash = fase(t)
    # llamas en las esquinas de abajo (3 fotogramas); más altas durante el fuego
    f = LLAMA[(t // 2) % 3]
    for x0 in (7, 116):
        for j, fila in enumerate(f):
            for i, c in enumerate(fila):
                if c != "X": continue
                y = 120 + j - (2 if fuego else 0)
                tono = (255, 236, 150) if j >= 4 else (250, 160, 30) if j >= 2 else (190, 60, 12)
                if fuego and j < 2: tono = (255, 200, 80)
                p.put(x0 + i, y, tono)
    # gema arriba al centro: se enciende al caer el pilar
    g = (255, 245, 190) if flash else (255, 190, 50) if fuego else (140, 60, 20)
    p.forma([".XX.", "XXXX", "XXXX", ".XX."], 62, 1, g)
    p.put(63, 2, (255, 255, 235) if fuego else (210, 120, 50))
    # marcas de garra arriba a los lados
    for x0 in (22, 98):
        for j in range(3):
            for k in range(4):
                p.put(x0 + j * 4 + k, 1 + k, (170, 140, 220))


DETALLES = {"brasa": det_brasa, "hierro": det_hierro, "violeta": det_violeta}


def build(op, t=0, k=40):
    top, bot = PALETAS[op]
    fr, win = marco.build(top, bot)
    img = np.array(fr)
    o = img[..., 3] > 0
    img[..., :3][o] = mn.agrupar(img[..., :3][o], k)
    DETALLES[op](mn.Pincel(img), t)
    return img


def frame_126(op, t, k=40):
    return Image.fromarray(build(op, t, k), "RGBA").crop((1, 1, 127, 127))
