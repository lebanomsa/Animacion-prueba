"""Marcos de Nova: el marco de siempre (secuencia/marco.py) con tres paletas y detalles estáticos y animados.
Coordenadas nativas de 128x128 (ventana 24..103; banda exterior de 4 px: filas/columnas 1..4 y 123..126). 32 pasos de 80 ms:
el disparo del rayo dura los pasos 13..23 y la carga 5..12 (de 32); las luces del marco reaccionan a eso.

  acero   : acero azulado arriba, óxido/cobre abajo (hace juego con el fondo naranja y las máquinas grises)
  militar : verde oliva (su chaqueta) arriba, latón abajo
  vita    : verde cristal arriba, rosa y plata abajo (la cápsula de Vita)
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "secuencia"))
import marco

PALETAS = {
    "acero": ([(0.0, (8, 10, 14)), (0.3, (24, 30, 38)), (0.6, (56, 66, 78)), (0.85, (110, 124, 138)), (1.0, (196, 208, 218))],
              [(0.0, (24, 8, 2)), (0.3, (80, 30, 8)), (0.6, (150, 66, 20)), (0.85, (214, 114, 38)), (1.0, (255, 190, 110))]),
    "militar": ([(0.0, (8, 12, 4)), (0.3, (28, 38, 14)), (0.6, (62, 80, 30)), (0.85, (110, 132, 58)), (1.0, (190, 204, 130))],
                [(0.0, (30, 18, 2)), (0.3, (92, 60, 8)), (0.6, (166, 118, 24)), (0.85, (226, 176, 60)), (1.0, (255, 232, 150))]),
    "vita": ([(0.0, (2, 12, 12)), (0.3, (10, 40, 38)), (0.6, (34, 92, 84)), (0.85, (100, 162, 148)), (1.0, (204, 236, 224))],
             [(0.0, (26, 8, 18)), (0.3, (88, 34, 64)), (0.6, (170, 86, 126)), (0.85, (228, 148, 176)), (1.0, (255, 214, 226))]),
}
MODOS = {"rapido32": (32, range(5, 13), range(13, 24)), "fluido48": (48, range(16, 25), range(25, 39))}
PASOS, CARGA, DISPARO = MODOS["rapido32"]


def modo(nombre):
    """Elige la temporización del bucle (pasos totales, pasos de carga y de disparo) que usan las luces animadas del marco."""
    global PASOS, CARGA, DISPARO
    PASOS, CARGA, DISPARO = MODOS[nombre]


class Pincel:
    def __init__(self, img):
        self.img, self.op = img, img[..., 3] > 0

    def put(self, x, y, col):
        if 0 <= x < 128 and 0 <= y < 128 and self.op[y, x]:
            self.img[y, x, :3] = col

    def forma(self, f, x0, y0, col):
        for j, fila in enumerate(f):
            for i, c in enumerate(fila):
                if c == "X":
                    self.put(x0 + i, y0 + j, col)

    def rect(self, x0, y0, w, h, col):
        for j in range(h):
            for i in range(w):
                self.put(x0 + i, y0 + j, col)


def agrupar(rgb, k):
    q = Image.fromarray(rgb.reshape(-1, 1, 3).astype(np.uint8), "RGB").quantize(colors=k, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = np.array(q.getpalette()[:768], np.uint8).reshape(-1, 3)
    return pal[np.asarray(q).reshape(-1)]


def parpadeo(t):
    """(carga, disparo, encendido) del paso t: durante el disparo parpadea cada paso; durante la carga, cada dos."""
    if t in DISPARO: return False, True, t % 2 == 0
    if t in CARGA: return True, False, (t // 2) % 2 == 0
    return False, False, False


# ------------------------------------------------------------------ acero y óxido
def det_acero(p, t):
    carga, disp, on = parpadeo(t)
    # remaches: esquinas y a lo largo de los laterales
    for (x, y) in [(10, 2), (116, 2), (10, 124), (116, 124)] + [(2, y) for y in (24, 48, 72, 96)] + [(124, y) for y in (24, 48, 72, 96)]:
        p.rect(x, y, 2, 2, (214, 222, 230)); p.put(x + 1, y + 1, (52, 60, 70))
    # franja de peligro abajo en el centro
    for x in range(44, 84):
        for y in range(123, 127):
            p.put(x, y, (232, 176, 32) if ((x + y) // 4) % 2 == 0 else (22, 16, 10))
    # tres luces: una encendida por turno; durante el disparo la roja parpadea
    lamp = [((214, 40, 36), (84, 18, 18)), ((240, 170, 30), (92, 64, 10)), ((60, 200, 90), (20, 76, 34))]
    enc = (t // 4) % 3
    for k, (v, o) in enumerate(lamp):
        if disp: col = v if (k == 0 and on) else o
        elif carga: col = v if (k == 1 and on) else o
        else: col = v if k == enc else o
        p.rect(14 + 5 * k, 124, 2, 2, col)
    # lámpara roja arriba al centro en una placa de acero
    p.rect(60, 1, 8, 4, (44, 52, 62)); p.rect(61, 2, 6, 2, (20, 24, 30))
    p.rect(63, 2, 2, 2, (255, 70, 60) if (disp and on) or (carga and on) else (96, 24, 22))


# ------------------------------------------------------------------ verde militar y latón
def det_militar(p, t):
    carga, disp, on = parpadeo(t)
    chev = ["XX..", ".XX.", ".XX.", "XX.."]
    for k in range(3):
        p.forma(chev, 12 + 5 * k, 1, (232, 196, 90)); p.forma(chev, 104 - 5 * k + 5, 1, (232, 196, 90))
    # gema dorada al centro de arriba y placa de identificación abajo a la derecha
    p.forma([".XX.", "XXXX", "XXXX", ".XX."], 62, 1, (236, 190, 64)); p.put(63, 2, (255, 244, 190)); p.put(65, 4, (140, 96, 16))
    p.rect(104, 124, 8, 3, (190, 196, 204)); p.put(105, 125, (40, 44, 50)); p.rect(108, 125, 3, 1, (120, 126, 134))
    # puntos de luz que recorren el borde exterior (una vuelta cada 48 pasos); rojos durante el disparo
    per = [(x, 2) for x in range(2, 126)] + [(125, y) for y in range(3, 126)] + [(x, 125) for x in range(124, 1, -1)] + [(2, y) for y in range(124, 2, -1)]
    cabeza = int(t * len(per) / PASOS) % len(per)
    tono = [(255, 244, 190), (232, 196, 90), (170, 130, 40), (110, 84, 24)] if not disp else [(255, 150, 130), (230, 60, 50), (160, 30, 30), (100, 20, 20)]
    for k in range(16):
        x, y = per[(cabeza - k) % len(per)]
        p.put(x, y, tono[min(3, k // 4)])
        if k < 3: p.put(x, y + (1 if y in (2,) else -1 if y == 125 else 0), tono[min(3, k // 4)]) if False else None


# ------------------------------------------------------------------ laboratorio de Vita
def det_vita(p, t):
    carga, disp, on = parpadeo(t)
    # latido en la gema rosa de arriba: doble pulso cada 16 pasos (como el bucle de burbujas de la cápsula)
    f = t % 16
    gem = (255, 150, 190) if f in (0, 1, 3) else (236, 100, 150) if f in (2, 4) else (150, 54, 96)
    p.forma([".XX.", "XXXX", "XXXX", ".XX."], 62, 1, gem); p.put(63, 2, (255, 230, 240))
    # electrocardiograma estático a los lados de la gema
    ecg = [3, 3, 3, 3, 2, 3, 4, 1, 4, 3, 3, 3, 3, 3]
    for lado, x0 in (("i", 44), ("d", 68)):
        for k, y in enumerate(ecg if lado == "d" else ecg[::-1]):
            p.put(x0 + k if lado == "d" else x0 - k + 13 - 13 + 13 - 13, y, (255, 190, 214))
    # burbujas que suben por los dos laterales (3 por lado), una vuelta cada 48 pasos
    for lado_x, fase in ((2, 0), (123, 16)):
        for k in range(3):
            y = 118 - (int((t + fase + 16 * k) * 112 / PASOS) % 112)
            p.forma([".X.", "X.X", ".X."], lado_x, 8 + y, (214, 246, 240)); p.put(lado_x + 1, 8 + y + 1, (120, 190, 180))
    # luces de estado abajo a la izquierda y cruz médica abajo a la derecha
    for k, (v, o) in enumerate([((120, 255, 220), (20, 80, 70)), ((255, 120, 170), (80, 30, 50)), ((255, 255, 255), (90, 90, 96))]):
        col = v if (disp and on) or (not disp and not carga and k == (t // 4) % 3) or (carga and on) else o
        p.rect(14 + 5 * k, 124, 2, 2, col)
    p.forma([".X.", "XXX", ".X."], 110, 124, (255, 236, 244))


DETALLES = {"acero": det_acero, "militar": det_militar, "vita": det_vita}


def build(op, t=0, k=40):
    top, bot = PALETAS[op]
    fr, win = marco.build(top, bot)
    img = np.array(fr)
    o = img[..., 3] > 0
    img[..., :3][o] = agrupar(img[..., :3][o], k)
    DETALLES[op](Pincel(img), t)
    return img


def frame_126(op, t, k=40):
    return Image.fromarray(build(op, t, k), "RGBA").crop((1, 1, 127, 127))


if __name__ == "__main__":
    out = HERE / "salida"; out.mkdir(exist_ok=True)
    for op in PALETAS:
        ims = []
        for t in (0, 18, 24):
            bg = Image.new("RGBA", (126, 126), (255, 0, 255, 255)); bg.alpha_composite(frame_126(op, t))
            ims.append(bg.convert("RGB").resize((504, 504), Image.NEAREST))
        s = Image.new("RGB", (504 * 3 + 20, 504), (30, 30, 30))
        for i, im in enumerate(ims): s.paste(im, (i * 514, 0))
        s.save(out / f"marco_{op}_solo.png"); print(op)
