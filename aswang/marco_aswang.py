"""Marcos de Aswang: el marco de siempre (secuencia/marco.py) con tres paletas, detalles estáticos y animados que repiten cada 8 pasos (el bucle de la lengua).
Coordenadas de 128x128 (ventana 24..103; banda exterior de 4 px).
  sangre : burdeos arriba y oro abajo; rubí que late, murciélagos dorados que aletean y adornos de oro
  noche  : azul medianoche arriba y violeta abajo; luna creciente y estrellas doradas que titilan
  piedra : piedra gris-azulada arriba y bronce abajo; arcos góticos y velas con llama que parpadea
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "nova")); sys.path.insert(0, str(HERE.parent / "secuencia"))
import marco
import marco_nova as mn

PALETAS = {
    "sangre": ([(0.0, (10, 2, 4)), (0.3, (34, 6, 12)), (0.6, (78, 12, 24)), (0.85, (130, 24, 40)), (1.0, (210, 90, 90))],
               [(0.0, (30, 16, 4)), (0.3, (92, 56, 10)), (0.6, (170, 116, 24)), (0.85, (232, 184, 64)), (1.0, (255, 236, 160))]),
    "noche": ([(0.0, (2, 3, 14)), (0.3, (8, 12, 44)), (0.6, (20, 32, 92)), (0.85, (50, 80, 160)), (1.0, (150, 190, 240))],
              [(0.0, (14, 10, 40)), (0.3, (34, 26, 84)), (0.6, (70, 56, 140)), (0.85, (112, 96, 190)), (1.0, (190, 176, 240))]),
    "piedra": ([(0.0, (6, 6, 10)), (0.3, (24, 24, 34)), (0.6, (54, 54, 70)), (0.85, (98, 96, 116)), (1.0, (170, 168, 190))],
               [(0.0, (22, 12, 4)), (0.3, (70, 40, 12)), (0.6, (132, 84, 30)), (0.85, (190, 134, 56)), (1.0, (244, 208, 130))]),
}
ORO, ORO_C, ORO_O = (240, 200, 90), (255, 240, 170), (140, 96, 24)
CRUZ = [".X.", "XXX", ".X."]
MURC = [["X...X", "XXXXX", ".XXX."], [".....", "XXXXX", "X.X.X"]]          # alas arriba / alas abajo
LLAMA = [[".X.", "XXX", ".X."], ["X..", "XXX", ".X."], [".X.", "XXX", "X.."], ["..X", "XXX", ".X."]]


def det_sangre(p, t):
    # rubí arriba al centro: late con doble pulso dentro de las 8 pasos
    pulso = t in (0, 1, 3)
    rub = (255, 120, 120) if pulso else (200, 30, 44) if t in (2, 4) else (130, 14, 28)
    p.forma([".XX.", "XXXX", "XXXX", ".XX."], 62, 1, rub); p.put(63, 2, (255, 220, 220)); p.put(65, 4, (70, 6, 14))
    p.rect(54, 2, 6, 1, ORO); p.rect(68, 2, 6, 1, ORO); p.put(53, 2, ORO_C); p.put(74, 2, ORO_C)     # filigrana a los lados
    # murciélagos dorados que aletean (2 pasos por posición) en las esquinas de arriba
    for x0 in (10, 113):
        p.forma(MURC[(t // 2) % 2], x0, 1, ORO)
    # diamantes de oro en las esquinas de abajo
    for x0, y0 in ((6, 121), (119, 121)):
        p.forma([".X.", "XXX", ".X."], x0, y0, ORO_C if t % 4 < 2 else ORO)
    # hilos de oro a lo largo de los laterales
    for y in range(20, 108, 8):
        p.put(2, y, ORO_O); p.put(125, y, ORO_O)


def det_noche(p, t):
    # luna creciente arriba al centro
    luna = [".XXX.", "XX...", "XX...", ".XXX."]
    p.forma(luna, 61, 1, (255, 244, 190)); p.put(61, 2, (255, 255, 235))
    # estrellas que titilan: cada una tiene su fase; brillante -> tenue -> apagada
    for i, (x, y) in enumerate([(14, 2), (30, 3), (94, 3), (113, 2), (3, 24), (124, 40), (3, 76), (124, 96), (20, 124), (108, 124)]):
        e = (t + i * 3) % 8
        if e < 3: p.forma(CRUZ, x - 1, y - 1, ORO_C) if 1 <= y <= 126 and x >= 1 else None
        elif e < 6: p.put(x, y, ORO)
    # murciélagos pequeños plateados que aletean en las esquinas de abajo
    for x0 in (8, 114):
        p.forma(MURC[(t // 2) % 2], x0, 122, (190, 190, 230))


def det_piedra(p, t):
    # arcos góticos a lo largo de la banda de arriba
    arco = [".X.", "X.X", "X.X", "X.X"]
    for x0 in list(range(12, 54, 8)) + list(range(74, 116, 8)):
        p.forma(arco, x0, 1, (130, 128, 150))
    # remaches
    for x, y in ((3, 3), (124, 3), (3, 124), (124, 124)):
        p.rect(x, y, 2, 2, (200, 198, 214)); p.put(x + 1, y + 1, (60, 58, 72))
    # velas con llama que parpadea (ciclo de 4 pasos), dos por cada esquina de abajo
    for x0 in (8, 16, 106, 114):
        p.rect(x0, 123, 2, 4, (240, 232, 204)); p.put(x0 + 1, 125, (196, 186, 156)); p.put(x0 + 1, 126, (196, 186, 156))
        f = LLAMA[(t + x0 // 8) % 4]
        for j, fila in enumerate(f):
            for i, c in enumerate(fila):
                if c == "X": p.put(x0 - 1 + i, 120 + j, (255, 238, 150) if j == 2 else (255, 150, 30) if j == 1 else (255, 90, 20))


DETALLES = {"sangre": det_sangre, "noche": det_noche, "piedra": det_piedra}


def build(op, t=0, k=40):
    top, bot = PALETAS[op]
    fr, win = marco.build(top, bot)
    img = np.array(fr)
    o = img[..., 3] > 0
    img[..., :3][o] = mn.agrupar(img[..., :3][o], k)
    DETALLES[op](mn.Pincel(img), t % 8)
    return img


def frame_126(op, t, k=40):
    return Image.fromarray(build(op, t, k), "RGBA").crop((1, 1, 127, 127))
