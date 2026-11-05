"""Marco de siempre (secuencia/marco.py) en paleta tierra y oro para Drache, con detalles estáticos de 'alien de cueva y oro'.

Coordenadas nativas del marco de 128x128 (ventana 24..103; banda exterior de 4 px: filas/columnas 1..4 y 123..126).
Los detalles eligen su color según el brillo del marco que tienen debajo (claro sobre fondo oscuro, oscuro sobre fondo dorado).
  * arriba al centro: gema roja (sus ojos) entre dos espirales de cuerno de carnero
  * arriba a los lados: runas alienígenas (4 a cada lado)
  * abajo al centro: montón de pepitas de oro; abajo a la izquierda: tres gemas (roja, dorada, violeta de las botas); abajo a la derecha: inicial D
  * laterales: vetas de oro en diagonal
  * esquinas de la ventana: corchetes dorados
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "secuencia"))
import marco

TIERRA = [(0.0, (8, 5, 4)), (0.3, (34, 20, 12)), (0.6, (82, 50, 28)), (0.85, (140, 92, 48)), (1.0, (214, 170, 98))]
ORO = [(0.0, (30, 16, 4)), (0.3, (92, 56, 8)), (0.6, (170, 112, 12)), (0.85, (232, 176, 32)), (1.0, (255, 232, 140))]

CLARO = (244, 206, 108)         # trazos claros (sobre zonas oscuras)
CLARO2 = (255, 238, 170)
OSCURO = (52, 28, 6)            # trazos oscuros (sobre zonas doradas)
OSCURO2 = (92, 52, 8)
ROJO, ROJO_L, ROJO_O = (214, 40, 36), (255, 150, 120), (110, 10, 14)
ORO_A, ORO_B, ORO_C = (255, 240, 150), (240, 180, 20), (150, 92, 8)
VIOLETA = (122, 96, 156)
CORCHETE = (196, 134, 26)

ESPIRAL = ["XXX.", "X.XX", "X..X", ".XX."]
GEMA = [".XX.", "XXXX", "XXXX", ".XX."]
RUNAS = [["X.X", "X.X", "XXX", ".X."], ["XXX", "..X", ".X.", "X.."], ["XX.", "X.X", "X.X", ".XX"], [".X.", "XXX", ".X.", "X.X"]]
RUNAS_D = [["XXX", "X.X", "..X", ".X."], ["X..", "XXX", "X.X", "..X"], [".X.", "X.X", "XXX", "X.."], ["XX.", ".X.", ".XX", "X.."]]
D = ["XX.", "X.X", "X.X", "XX."]
PILA = ["....XX......", "..XXXXX.XX..", ".XXXXXXXXXX.", "XXXXXXXXXXXX"]


class Pincel:
    def __init__(self, img):
        self.img = img
        self.op = img[..., 3] > 0
        self.lum = img[..., 0] * .299 + img[..., 1] * .587 + img[..., 2] * .114

    def put(self, x, y, col):
        if 0 <= x < 128 and 0 <= y < 128 and self.op[y, x]:
            self.img[y, x, :3] = col

    def claro_bajo(self, x, y):
        """True si el marco que hay en (x, y) es oscuro (conviene dibujar claro)."""
        return self.lum[y, x] < 110

    def dibujar(self, forma, x0, y0, col, x1=None):
        for j, fila in enumerate(forma):
            for i, c in enumerate(fila):
                if c == "X":
                    self.put(x0 + i, y0 + j, col)


def adaptativo(p, forma, x0, y0, cy=None):
    cx = x0 + len(forma[0]) // 2
    cy = y0 + len(forma) // 2
    return (CLARO, CLARO2) if p.claro_bajo(cx, cy) else (OSCURO, OSCURO2)


def detalles(img):
    p = Pincel(img)
    # centro de arriba: gema roja entre dos espirales
    p.dibujar(GEMA, 62, 1, ROJO)
    p.put(62, 2, ROJO_L); p.put(63, 1, ROJO_L)
    p.put(65, 3, ROJO_O); p.put(64, 4, ROJO_O); p.put(63, 4, ROJO_O)
    esp_i, esp_d = ESPIRAL, [fila[::-1] for fila in ESPIRAL]
    p.dibujar(esp_i, 56, 1, CLARO); p.dibujar(esp_d, 68, 1, CLARO)
    # runas arriba (4 a cada lado)
    for k, r in enumerate(RUNAS):
        p.dibujar(r, 14 + 5 * k, 1, (200, 148, 48))
    for k, r in enumerate(RUNAS_D):
        p.dibujar(r, 93 + 5 * k, 1, (200, 148, 48))
    # abajo al centro: montón de pepitas (3 tonos)
    for j, fila in enumerate(PILA):
        for i, c in enumerate(fila):
            if c == "X":
                tono = ORO_A if (j == 0 or (j == 1 and i in (2, 3, 9))) else ORO_C if (j == 3 or i == 11) else ORO_B
                p.put(58 + i, 123 + j, tono)
    # abajo a la izquierda: tres gemas de 2x2
    for k, col in enumerate((ROJO, ORO_B, VIOLETA)):
        for dx in (0, 1):
            for dy in (0, 1):
                p.put(21 + k * 5 + dx, 124 + dy, col)
        p.put(21 + k * 5, 124, tuple(min(255, c + 70) for c in col))
    # abajo a la derecha: D de Drache
    cl, _ = adaptativo(p, D, 106, 123)
    p.dibujar(D, 106, 123, cl)
    # laterales: vetas de oro en diagonal con un nodo en la punta
    for y in (12, 30, 92, 110):
        for lado in ("izq", "der"):
            sx = 1 if lado == "izq" else 126
            dx = 1 if lado == "izq" else -1
            c, c2 = (CLARO, CLARO2) if p.claro_bajo(sx + dx * 2, y + 2) else (OSCURO, OSCURO2)
            for k in range(4):
                p.put(sx + dx * k, y + k, c)
            p.put(sx + dx * 3, y + 4, c2); p.put(sx + dx * 2, y + 3, c2); p.put(sx, y, c2)
    # corchetes en el anillo oscuro de la ventana
    lo, hi = 23, 104
    for (cx, cy, sx, sy) in [(lo, lo, 1, 1), (hi, lo, -1, 1), (lo, hi, 1, -1), (hi, hi, -1, -1)]:
        for k in range(8):
            p.put(cx + sx * k, cy, CORCHETE); p.put(cx, cy + sy * k, CORCHETE)


def agrupar(rgb, k):
    q = Image.fromarray(rgb.reshape(-1, 1, 3).astype(np.uint8), "RGB").quantize(colors=k, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = np.array(q.getpalette()[:768], np.uint8).reshape(-1, 3)
    return pal[np.asarray(q).reshape(-1)]


def build(con_detalles=True, k=None):
    """(marco RGBA de 128x128, ventana). Si se da `k`, los tonos del marco se agrupan en k colores ANTES de dibujar los detalles."""
    fr, win = marco.build(TIERRA, ORO)
    img = np.array(fr)
    if k:
        op = img[..., 3] > 0
        img[..., :3][op] = agrupar(img[..., :3][op], k)
    if con_detalles:
        detalles(img)
    return img, win


if __name__ == "__main__":
    out = HERE / "marco_final"; out.mkdir(exist_ok=True)
    img, win = build()
    bg = Image.new("RGBA", (128, 128), (255, 0, 255, 255)); bg.alpha_composite(Image.fromarray(img, "RGBA"))
    bg.convert("RGB").crop((1, 1, 127, 127)).resize((126 * 7, 126 * 7), Image.NEAREST).save(out / "marco_detalles_7x.png")
    print(win)
