"""Marcos rectangulares para el bucle de Drache (escena de 380x259 píxeles a tamaño natural; el marco usa píxeles de 1 px, igual que el sprite).

Estructura (de fuera a dentro, T = 28 px de grosor): contorno negro, bisel de 3 px, línea oscura, banda principal de 16 px con un degradado vertical
a bandas y un patrón que se repite, línea oscura, ribete dorado de 3 px, sombra de 2 px y contorno negro. En las cuatro esquinas hay un medallón
con una espiral de cuerno de carnero (los cuernos de Drache) y, arriba y abajo en el centro, una gema roja (sus ojos) flanqueada por dos espirales.
Todo es estático. Tres temas: 'hueso', 'roca' y 'alien'.
"""
import math
from pathlib import Path

import numpy as np
from PIL import Image

T = 28

K = (18, 10, 4)                                         # contorno
HUESO = [(236, 224, 188), (204, 190, 152), (162, 148, 118), (114, 102, 80)]
ORO = [(255, 232, 128), (248, 184, 0), (176, 120, 0), (104, 64, 0)]
ROJO = [(255, 140, 112), (216, 52, 40), (136, 20, 20)]

TEMAS = {
    "hueso": dict(grad=[(52, 38, 24), (150, 116, 68)], bisel=[(214, 200, 164), (164, 150, 120), (112, 100, 80)], base=(66, 48, 30),
                  patron="cuentas", acento=HUESO, medallon=(58, 40, 24)),
    "roca": dict(grad=[(30, 18, 6), (140, 84, 44)], bisel=[(176, 130, 80), (128, 88, 52), (84, 56, 32)], base=(60, 36, 18),
                 patron="vetas", acento=HUESO, medallon=(40, 24, 10)),
    "alien": dict(grad=[(36, 26, 52), (104, 80, 128)], bisel=[(150, 124, 176), (104, 82, 128), (66, 50, 86)], base=(60, 46, 80),
                  patron="runas", acento=ORO, medallon=(30, 22, 44)),
}

GLIFOS = [   # 9 x 10, las tres runas se alternan
    ["....X....", "....X....", "X...X...X", "X...X...X", ".X..X..X.", "..X.X.X..", "...XXX...", "....X....", "....X....", "....X...."],
    ["XXXXXXXXX", "X.......X", "X..XXX..X", "X.X...X.X", "X.X.X.X.X", "X.X...X.X", "X..XXX..X", "X.......X", "XXXXXXXXX", "........."],
    ["X.......X", "XX.....XX", ".XX...XX.", "..XX.XX..", "...XXX...", "....X....", "....X....", "...XXX...", "..X.X.X..", ".X..X..X."],
]


def _interp(grad, t):
    a, b = np.array(grad[0], float), np.array(grad[1], float)
    return tuple(int(round(v)) for v in a + (b - a) * t)


def _mul(c, f):
    return tuple(int(max(0, min(255, v * f))) for v in c)


def espiral(tam, hueso, oscuro=K, vueltas=2.9, rmax=None):
    """Espiral de cuerno de carnero en un lienzo de tam x tam (RGBA): contorno oscuro, cuerpo de hueso con luz arriba a la izquierda."""
    im = np.zeros((tam, tam, 4), np.uint8)
    c = (tam - 1) / 2.0
    rmax = rmax or (tam / 2.0 - 3.0)
    pts = []
    n = 400
    for i in range(n + 1):
        u = i / n
        th = u * vueltas * 2 * math.pi
        r = 1.0 + (rmax - 1.0) * u
        w = 1.2 + 2.0 * (1 - u) * (rmax / 9.0)
        pts.append((c + r * math.cos(th), c + r * math.sin(th), w))

    def estampar(extra, color_fn):
        for (x, y, w) in pts:
            rr = w / 2.0 + extra
            for yy in range(int(y - rr - 1), int(y + rr + 2)):
                for xx in range(int(x - rr - 1), int(x + rr + 2)):
                    if 0 <= xx < tam and 0 <= yy < tam and (xx - x) ** 2 + (yy - y) ** 2 <= rr * rr:
                        col = color_fn(xx - x, yy - y, rr)
                        if col is not None:
                            im[yy, xx] = col + (255,)
    estampar(1.0, lambda dx, dy, rr: oscuro)
    estampar(0.0, lambda dx, dy, rr: hueso[0] if (dx + dy) < -rr * 0.55 else hueso[1] if (dx + dy) < rr * 0.35 else hueso[2])
    return Image.fromarray(im, "RGBA")


def medallon(tema):
    """Disco de 28x28 con aro dorado, fondo oscuro y la espiral de cuerno."""
    t = TEMAS[tema]
    im = np.zeros((T, T, 4), np.uint8)
    c = (T - 1) / 2.0
    for y in range(T):
        for x in range(T):
            d = math.hypot(x - c, y - c)
            if d <= 13.6:
                col = K if d > 13.0 else ORO[3] if d > 12.0 else ORO[1] if d > 10.6 else ORO[2] if d > 9.6 else t["medallon"]
                if 9.6 < d <= 12.0 and (x + y) < c * 1.2:
                    col = ORO[0] if d > 10.6 else ORO[1]
                im[y, x] = col + (255,)
    sp = espiral(T - 8, t["acento"])
    base = Image.fromarray(im, "RGBA"); base.alpha_composite(sp, (4, 4))
    return base


def gema():
    """Gema roja de 14x18 con engaste dorado."""
    w, h = 16, 20
    im = np.zeros((h, w, 4), np.uint8)
    cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
    for y in range(h):
        for x in range(w):
            d = abs(x - cx) / 7.2 + abs(y - cy) / 9.4
            if d <= 1.0:
                if d > 0.88:
                    col = K
                elif d > 0.72:
                    col = ORO[1] if (x + y) < cx + cy else ORO[2]
                else:
                    f = (x - cx) / 6 + (y - cy) / 8
                    col = ROJO[0] if (d < 0.30 and x < cx and y < cy) else ROJO[1] if f < 0.2 else ROJO[2]
                im[y, x] = col + (255,)
    return Image.fromarray(im, "RGBA")


def adorno_centro(tema):
    """Gema flanqueada por dos espirales pequeñas (la de la derecha, reflejada), en una pieza de T de alto."""
    t = TEMAS[tema]
    g = gema()
    e = espiral(20, t["acento"], vueltas=2.4, rmax=7.2)
    ancho = 20 * 2 + g.width + 4
    im = Image.new("RGBA", (ancho, T), (0, 0, 0, 0))
    im.alpha_composite(e, (0, (T - 20) // 2))
    im.alpha_composite(e.transpose(Image.FLIP_LEFT_RIGHT), (ancho - 20, (T - 20) // 2))
    im.alpha_composite(g, ((ancho - g.width) // 2, (T - g.height) // 2))
    return im


# ---------------------------------------------------------------- patrones de la banda (coordenadas: s a lo largo, v = 0..13 a lo ancho)
def patron(tema, s, v, rs):
    t = TEMAS[tema]
    if t["patron"] == "cuentas":                       # cuentas de hueso (vértebras) enhebradas
        per = 16
        u = s % per
        cx, cy = 7.5, 6.5
        d = math.hypot(u - cx, v - cy)
        if d <= 5.6:
            if d > 4.8:
                return K
            return HUESO[0] if (u - cx) + (v - cy) < -3.5 else HUESO[1] if (u - cx) + (v - cy) < 1.5 else HUESO[2]
        if abs(v - cy) < 1.0 and (u < 2 or u > 13):
            return ORO[2]                               # hilo dorado entre cuentas
        return None
    if t["patron"] == "vetas":                          # roca moteada con vetas de oro en diagonal
        base = rs[(s % 997, v)]
        if base > 0.93:
            return (96, 62, 34)
        if base < 0.07:
            return (20, 12, 4)
        diag = (s + 2 * v) % 41
        if diag in (0, 1) and (s // 41) % 3 != 2:
            return ORO[1] if diag == 0 else ORO[2]
        if diag == 40 and (s // 41) % 3 != 2:
            return ORO[0]
        return None
    g = GLIFOS[(s // 16) % 3]                           # runas doradas
    u = s % 16 - 3
    vv = v - 2
    if 0 <= u < 9 and 0 <= vv < 10 and g[vv][u] == "X":
        return ORO[1] if vv < 5 else ORO[2]
    if 0 <= u - 1 < 9 and 0 <= vv - 1 < 10 and g[vv - 1][u - 1] == "X":
        return (14, 8, 22)
    return None


def construir(W, H, tema):
    """Marco RGBA de (W + 2T) x (H + 2T) con la ventana de W x H transparente."""
    t = TEMAS[tema]
    Wf, Hf = W + 2 * T, H + 2 * T
    img = np.zeros((Hf, Wf, 4), np.uint8)
    rs = np.random.RandomState(7).rand(997, 14)
    rsd = {(i, j): rs[i, j] for i in range(997) for j in range(14)}
    bi = t["bisel"]
    for y in range(Hf):
        banda = int(y / Hf * 8) / 7.0
        base = _interp(t["grad"], banda)
        for x in range(Wf):
            dists = (y, x, Wf - 1 - x, Hf - 1 - y)
            lado = int(np.argmin(dists))
            d = dists[lado]
            if d >= T:
                continue
            s = x if lado in (0, 3) else y
            claro = lado in (0, 1)
            if d == 0 or d == T - 1:
                col = K
            elif d <= 3:
                col = bi[d - 1] if claro else bi[min(3 - d, 2)] if d else bi[0]
                col = _mul(col, 1.0 if claro else 0.62)
            elif d == 4 or d == T - 7:
                col = _mul(base, 0.35)
            elif d <= T - 8:                                       # banda principal
                v = d - 6
                p = patron(tema, s, v, rsd) if 0 <= v < 14 else None
                col = p if p is not None else (_mul(base, 1.18) if v == 0 else _mul(base, 0.8) if v >= 13 else base)
            elif d <= T - 4:                                       # ribete dorado
                k = d - (T - 6)
                col = ORO[0 if (claro and k == 0) else 1 if k <= 0 else 2] if claro else ORO[2 if k <= 0 else 3]
            else:                                                  # sombra interior
                col = _mul(base, 0.28)
            img[y, x] = col + (255,)
    fr = Image.fromarray(img, "RGBA")
    med = medallon(tema)
    for (x, y, fx, fy) in ((0, 0, False, False), (Wf - T, 0, True, False), (0, Hf - T, False, True), (Wf - T, Hf - T, True, True)):
        m = med
        if fx: m = m.transpose(Image.FLIP_LEFT_RIGHT)
        if fy: m = m.transpose(Image.FLIP_TOP_BOTTOM)
        fr.alpha_composite(m, (x, y))
    ad = adorno_centro(tema)
    fr.alpha_composite(ad, ((Wf - ad.width) // 2, 0))
    fr.alpha_composite(ad.transpose(Image.FLIP_TOP_BOTTOM), ((Wf - ad.width) // 2, Hf - T))
    return fr


if __name__ == "__main__":
    import sys
    for tema in TEMAS:
        fr = construir(380, 259, tema)
        fondo = Image.new("RGBA", fr.size, (70, 100, 120, 255)); fondo.alpha_composite(fr)
        fondo.convert("RGB").save(f"/projects/sandbox/tmp/drache/marco_{tema}.png"); print(tema, fr.size)
