"""Marco plata y violeta para Alice y Heart: el diseño de nudos de siempre (secuencia/marco.py) recoloreado,
más detalles estáticos de 'holograma / inteligencia artificial' dibujados sobre zonas libres.

Dónde van (coordenadas nativas del marco de 128x128; la ventana es 24..103):
  * banda exterior de 4 px (filas/columnas 1..4 y 123..126): trazos de circuito, tira de datos, luces de estado, 'A', corazón, emisor
  * anillo oscuro de la ventana (23 y 104): corchetes en las cuatro esquinas
Las figuras (al doble de tamaño) pasan por delante del marco, pero casi nunca llegan a la banda exterior.
No se anima nada: todo es estático.

  python marco_alice_heart.py   -> salida/marco_alice_heart_detalles.png (marco solo, 6x) y salida/maqueta_detalles.png
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "secuencia"))
sys.path.insert(0, str(HERE))
import marco   # noqa: E402

PLATA = [(0.0, (20, 24, 36)), (0.3, (64, 72, 92)), (0.6, (132, 144, 168)), (0.85, (196, 206, 224)), (1.0, (244, 248, 255))]
VIOLETA = [(0.0, (18, 8, 44)), (0.3, (60, 34, 112)), (0.6, (110, 76, 178)), (0.85, (168, 134, 232)), (1.0, (226, 208, 252))]

# colores de los detalles (los cianes salen de los sprites holograma)
CIAN = (41, 206, 173)
CIAN_MEDIO = (24, 156, 123)
CIAN_OSC = (0, 82, 49)
CIAN_CLARO = (181, 255, 247)
NARANJA = (222, 140, 82)
BLANCO = (255, 247, 231)
ROSA = (240, 110, 170)
ROSA_CLARO = (255, 190, 215)

GLIFOS = {   # 3x4
    "0": ["XXX", "X.X", "X.X", "XXX"],
    "1": [".X.", "XX.", ".X.", "XXX"],
    "A": [".X.", "X.X", "XXX", "X.X"],
}
CORAZON = [".X.X.", "XXXXX", ".XXX.", "..X.."]


def _banda(lado, a, u):
    """(a, u) -> (x, y): `a` a lo largo de la banda exterior y `u` hacia dentro (0 = borde, 3 = lado de dentro)."""
    return {"arriba": (a, 1 + u), "abajo": (a, 126 - u), "izq": (1 + u, a), "der": (126 - u, a)}[lado]


class Pincel:
    def __init__(self, img):
        self.img = img
        self.op = img[..., 3] > 0

    def put(self, x, y, col):
        if 0 <= x < 128 and 0 <= y < 128 and self.op[y, x]:
            self.img[y, x, :3] = col

    def banda(self, lado, a, u, col):
        self.put(*_banda(lado, a, u), col)


def circuito(p, lado, a0, d, tramos=((9, 1), (7, 3), (5, 1))):
    """Trazo de circuito en la banda exterior: tramos (largo, nivel u) unidos por conexiones verticales, con un nodo claro en cada extremo."""
    a, prev, pts = a0, None, []
    for largo, u in tramos:
        if prev is not None:
            for uu in range(min(prev, u), max(prev, u) + 1):
                p.banda(lado, a, uu, CIAN_MEDIO)
        for _ in range(largo):
            p.banda(lado, a, u, CIAN_MEDIO); pts.append((a, u)); a += d
        prev = u
    for (aa, uu) in (pts[0], pts[-1]):
        p.banda(lado, aa, uu, CIAN_CLARO)
        p.banda(lado, aa + d if (aa, uu) == pts[0] else aa - d, uu, CIAN)


def glifo(p, lado, a0, texto, col):
    a = a0
    for ch in texto:
        for fila, row in enumerate(GLIFOS[ch]):
            for k, c in enumerate(row):
                if c == "X":
                    p.banda(lado, a + k, 3 - fila if lado == "abajo" else fila, col)   # abajo la banda crece hacia arriba
        a += 4


def corchetes(p):
    """L de 8 px en el anillo oscuro, en las cuatro esquinas de la ventana (24..103)."""
    lo, hi = 23, 104
    for (cx, cy, sx, sy) in [(lo, lo, 1, 1), (hi, lo, -1, 1), (lo, hi, 1, -1), (hi, hi, -1, -1)]:
        for k in range(8):
            p.put(cx + sx * k, cy, CIAN); p.put(cx, cy + sy * k, CIAN)
        p.put(cx, cy, CIAN_CLARO)


def emisor(p):
    """Ranura del proyector en el centro de abajo: 12x4, con el centro más claro."""
    for k in range(12):
        x = 58 + k
        c = CIAN_CLARO if k in (5, 6) else CIAN if k in (3, 4, 7, 8) else CIAN_MEDIO
        p.put(x, 123, CIAN_OSC); p.put(x, 126, CIAN_OSC)
        p.put(x, 124, c); p.put(x, 125, c)


def luces(p, x0=21, y0=124):
    """Tres luces de estado de 2x2 px: cian, naranja y blanca."""
    for k, c in enumerate([CIAN, NARANJA, BLANCO]):
        for dx in (0, 1):
            for dy in (0, 1):
                p.put(x0 + k * 5 + dx, y0 + dy, c)


def corazon(p, x0=110, y0=123):
    for fila, row in enumerate(CORAZON):
        for k, c in enumerate(row):
            if c == "X":
                p.put(x0 + k, y0 + fila, ROSA_CLARO if (fila == 0 and k == 1) else ROSA)


def build(con_detalles=True):
    """(marco RGBA uint8 de 128x128 con detalles, (x0, y0, x1, y1) de la ventana)."""
    fr, win = marco.build(PLATA, VIOLETA)
    img = np.array(fr)
    if con_detalles:
        p = Pincel(img)
        glifo(p, "arriba", 12, "01101", CIAN_MEDIO)          # tira de datos, arriba a la izquierda
        circuito(p, "arriba", 115, -1)                       # arriba a la derecha
        circuito(p, "izq", 12, 1); circuito(p, "izq", 115, -1)
        circuito(p, "der", 12, 1); circuito(p, "der", 115, -1)
        glifo(p, "abajo", 8, "A", CIAN)                      # inicial de Alice
        luces(p)
        emisor(p)
        corazon(p)                                           # Heart
        corchetes(p)
    return img, win


def vista():
    out = HERE / "salida"; out.mkdir(exist_ok=True)
    img, win = build()
    fondo = Image.new("RGBA", (128, 128), (255, 0, 255, 255)); fondo.alpha_composite(Image.fromarray(img, "RGBA"))
    fondo.convert("RGB").resize((128 * 6, 128 * 6), Image.NEAREST).save(out / "marco_alice_heart_detalles.png")

    import choque as ch
    import sprites as sp
    S, _ = sp.cargar()
    s, floor = 2, 104
    esc = lambda im: im.resize((im.width * s, im.height * s), Image.NEAREST)
    h, a = esc(S["H2B4"]), esc(S["H2T4"])
    hx, hy = ch.mano_derecha(h); ax, ay = ch.mano_izquierda(a)
    dif = round((floor - a.height + ay) - (floor - h.height + hy)); total = (hx + 1 - ax) + a.width
    hxp = (126 - total) // 2; axp = hxp + hx + 1 - ax
    x0, y0, x1, y1 = win
    base = Image.new("RGBA", (128, 128), (22, 28, 44, 255)); d = ImageDraw.Draw(base)
    d.rectangle((x0, floor - 7, x1, y1), fill=(34, 44, 66, 255))
    base.alpha_composite(Image.fromarray(img, "RGBA"))
    base.alpha_composite(h, (hxp + 1, floor - h.height)); base.alpha_composite(a, (axp + 1, floor - a.height - dif))
    base.convert("RGB").crop((1, 1, 127, 127)).resize((126 * 6, 126 * 6), Image.NEAREST).save(out / "maqueta_detalles.png")
    print("listo:", win)


if __name__ == "__main__":
    vista()
