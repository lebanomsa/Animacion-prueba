"""Luna en pixel art con fases (inspirada en 'referencia-marco-utena 2.gif', que recorre las fases de la luna).

luna(fase, r): imagen RGBA de (2r+3)x(2r+3) con la luna de radio r y un contorno oscuro.
fase: 0 = luna nueva, 0.25 = cuarto creciente, 0.5 = llena, 0.75 = cuarto menguante (1.0 = otra vez nueva).
"""
import numpy as np
from PIL import Image

LUZ, SOMBRA_L, CRATER = (246, 242, 255), (196, 186, 228), (150, 138, 200)
OSCURA, BORDE_OSC, CONTORNO = (24, 14, 50), (96, 80, 150), (12, 6, 28)


def luna(fase, r):
    n = 2 * r + 3
    img = np.zeros((n, n, 4), np.uint8)
    c = r + 1
    alpha = 2 * np.pi * fase
    k = np.cos(alpha)
    for y in range(n):
        for x in range(n):
            dx, dy = x - c, y - c
            d = np.hypot(dx, dy)
            if d <= r + 0.35:
                w = np.sqrt(max(r * r - dy * dy, 0))
                lit = (dx >= k * w) if fase < 0.5 else (dx <= -k * w)
                if fase <= 0.0 or fase >= 1.0:
                    lit = False
                if abs(fase - 0.5) < 1e-6:
                    lit = True
                if lit:
                    col = LUZ if d < r - 1.2 or r < 4 else SOMBRA_L
                    # luz más tenue hacia el borde del lado del terminador
                    img[y, x] = col + (255,)
                else:
                    col = BORDE_OSC if d > r - 0.9 else OSCURA
                    img[y, x] = col + (255,)
            elif d <= r + 1.35:
                img[y, x] = CONTORNO + (255,)
    if r >= 4:                                              # cráteres (solo donde hay luz)
        for (fx, fy, s) in ((-0.35, -0.3, 1), (0.4, 0.05, 1), (-0.1, 0.5, 1), (0.1, -0.55, 1)):
            for ddx in range(s):
                for ddy in range(s):
                    px_, py_ = c + int(round(fx * r)) + ddx, c + int(round(fy * r)) + ddy
                    if tuple(img[py_, px_][:3]) in (LUZ, SOMBRA_L):
                        img[py_, px_] = CRATER + (255,)
    return Image.fromarray(img, "RGBA")


if __name__ == "__main__":
    fases = [0.0, 0.1, 0.25, 0.4, 0.5, 0.6, 0.75, 0.9]
    Z = 10
    for r, nombre in ((3, "r3"), (4, "r4"), (6, "r6")):
        hoja = Image.new("RGB", (len(fases) * (2 * r + 5) * Z, (2 * r + 5) * Z), (70, 40, 110))
        for i, f in enumerate(fases):
            m = luna(f, r).resize(((2 * r + 3) * Z, (2 * r + 3) * Z), Image.NEAREST)
            hoja.paste(m, (i * (2 * r + 5) * Z + Z, Z), m)
        hoja.save(f"/projects/sandbox/tmp/ref_marco/fases_{nombre}.png")
    print("ok")
