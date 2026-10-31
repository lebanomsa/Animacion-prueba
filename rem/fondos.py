"""Fondos pixel art para Rem (160x160 píxeles nativos, se ven a x4 en la ventana de 640 px). Ciclos de 24 pasos.

  bosque(t)  bosque nevado de noche: cielo con estrellas que parpadean, aurora que ondula, luna, montañas, pinos, nieve que cae
  salon(t)   salón de la mansión de noche: ventanales con luna, cortinas ciruela, rayos de luna sobre el suelo, velas que parpadean, polvo en el aire
Se dibujan con código con pocos colores y tramado Bayer 4x4 en los degradados.
"""
import math

import numpy as np
from PIL import Image, ImageDraw

S = 160
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
YY, XX = np.mgrid[0:S, 0:S]
UMBRAL = BAYER[YY % 4, XX % 4]


def degradado(colores, y0, y1):
    """Degradado vertical por bandas con tramado entre colores consecutivos."""
    out = np.zeros((S, S, 3), np.uint8)
    n = len(colores) - 1
    pos = np.clip((YY - y0) / max(1, y1 - y0), 0, 1) * n
    idx = np.minimum(pos.astype(int), n - 1)
    frac = pos - idx
    pick = np.where(frac > UMBRAL, idx + 1, idx)
    arr = np.array(colores, np.uint8)
    out[:] = arr[pick]
    return out


def mezcla(base, color, alfa):
    return (base * (1 - alfa) + np.array(color) * alfa)


def estrellas(img, semilla, n, ymax, t, col=(220, 232, 255)):
    rng = np.random.default_rng(semilla)
    px = img.load()
    for k in range(n):
        x, y = int(rng.integers(0, S)), int(rng.integers(0, ymax))
        fase = int(rng.integers(0, 24))
        if k % 3 == 0:
            e = (t + fase) % 12
            if e < 3:
                for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                    px[min(max(x + dx, 0), S - 1), min(max(y + dy, 0), S - 1)] = col
            elif e < 7:
                px[x, y] = col
            else:
                px[x, y] = tuple(int(v * 0.55) for v in col)
        else:
            px[x, y] = tuple(int(v * 0.8) for v in col)


def pino(d, cx, base, h, ancho, col, nieve=None):
    """Pino triangular en 4 pisos."""
    pisos = 4
    for k in range(pisos):
        top = base - h + k * h // (pisos + 1)
        bot = base - h + (k + 2) * h // (pisos + 1)
        w = int(ancho * (k + 1) / pisos)
        d.polygon([(cx, top), (cx - w, bot), (cx + w, bot)], fill=col)
        if nieve:
            d.line([(cx, top + 1), (cx - w // 2, top + (bot - top) // 2)], fill=nieve)
    d.rectangle((cx - 1, base - 2, cx + 1, base), fill=col)


def bosque(t):
    sky = degradado([(5, 8, 24), (8, 14, 38), (12, 22, 56), (18, 34, 80), (28, 52, 108), (44, 76, 136)], 0, 104)
    img = Image.fromarray(sky, "RGB")
    estrellas(img, 3, 55, 70, t)
    arr = np.asarray(img).astype(float)
    # aurora: dos cortinas que ondulan
    for (base_y, amp, col_mid, col_top, col_bot, fase0) in ((34, 9, (90, 255, 205), (110, 90, 230), (240, 100, 175), 0.0),
                                                              (46, 6, (70, 210, 190), (80, 90, 210), (210, 90, 190), 0.4)):
        for x in range(S):
            yc = base_y + amp * math.sin(2 * math.pi * (x / 90 - t / 24 + fase0)) + 4 * math.sin(2 * math.pi * (x / 41 + t / 12))
            h = 15 + 5 * math.sin(2 * math.pi * (x / 55 + t / 24))
            rayo = 0.65 + 0.35 * (math.sin(x * 0.85 + fase0 * 5) > 0.1)
            for y in range(max(0, int(yc - h)), min(S, int(yc + h))):
                d = (y - yc) / h
                if d < -0.55:
                    col, a = col_top, 0.30 * (d + 1.0) / 0.45
                elif d < 0.1:
                    col, a = col_mid, 0.55
                elif d < 0.55:
                    col, a = col_mid, 0.40
                else:
                    col, a = col_bot, 0.38 * (1 - d) / 0.45
                a = round(a * rayo * 3) / 3                       # 3-4 niveles de opacidad
                if a > 0:
                    arr[y, x] = mezcla(arr[y, x], col, a)
    img = Image.fromarray(arr.round().astype(np.uint8), "RGB")
    d = ImageDraw.Draw(img)
    # luna con halo
    for r, c in ((17, (24, 44, 92)), (14, (34, 60, 112))):
        for yy in range(-r, r + 1):
            for xx in range(-r, r + 1):
                if xx * xx + yy * yy <= r * r and BAYER[(130 + xx) % 4, (22 + yy) % 4] > 0.5:
                    img.putpixel((130 + xx, 22 + yy), c)
    d.ellipse((121, 13, 139, 31), fill=(236, 243, 255))
    d.ellipse((127, 17, 133, 23), fill=(205, 218, 240)); d.ellipse((124, 24, 128, 28), fill=(214, 226, 246))
    d.ellipse((133, 22, 136, 25), fill=(214, 226, 246))
    # montañas lejanas
    mont = [100 - int(12 + 7 * math.sin(x / 19) + 4 * math.sin(x / 7 + 1)) for x in range(S)]
    for x in range(S):
        d.line([(x, mont[x]), (x, 112)], fill=(18, 32, 72))
        if mont[x] < 90:
            d.point((x, mont[x]), fill=(70, 104, 168)); d.point((x, mont[x] + 1), fill=(46, 72, 128))
    # bosque lejano
    rng = np.random.default_rng(8)
    for x in range(-6, S + 6, 9):
        pino(d, x + int(rng.integers(-2, 3)), 112, int(rng.integers(26, 38)), 7, (12, 24, 58))
    # nieve del suelo (3 tonos con tramado)
    suelo = degradado([(168, 196, 238), (140, 168, 214), (108, 136, 188), (80, 104, 158)], 111, S)
    arr = np.asarray(img).copy()
    arr[111:] = suelo[111:]
    img = Image.fromarray(arr, "RGB")
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(5)
    for _ in range(40):
        d.point((int(rng.integers(0, S)), int(rng.integers(113, S))), fill=(226, 238, 255))
    # pinos grandes de primer plano en los bordes
    for (cx, h, w) in ((8, 96, 20), (34, 70, 15), (150, 100, 21), (127, 64, 14)):
        pino(d, cx, 126, h, w, (7, 13, 32), nieve=(66, 98, 160))
    # nieve que cae (dos profundidades; recorre 160 px por ciclo para enlazar)
    rng = np.random.default_rng(12)
    for k in range(34):
        x0, y0 = int(rng.integers(0, S)), int(rng.integers(0, S))
        gran = k % 3 == 0
        y = int((y0 + 160 * t / 24) % S)
        x = int(x0 + round(1.2 * math.sin(2 * math.pi * (t / 24 + k / 7))))
        c = (236, 244, 255) if gran else (190, 208, 240)
        d.rectangle((x, y, x + (1 if gran else 0), y + (1 if gran else 0)), fill=c)
    return img


def salon(t):
    arr = np.zeros((S, S, 3), np.uint8)
    # pared con papel pintado a rayas suaves y friso
    arr[:] = (26, 30, 62)
    arr[:, ((np.arange(S) // 8) % 2 == 0)] = (30, 35, 70)
    arr[(YY % 6 == 0) & (XX % 8 == 4)] = (38, 44, 84)
    img = Image.fromarray(arr, "RGB")
    d = ImageDraw.Draw(img)
    d.rectangle((0, 78, S, 106), fill=(44, 34, 70))
    for x in range(2, S, 20):
        d.rectangle((x, 82, x + 15, 102), outline=(62, 50, 96))
    d.rectangle((0, 76, S, 78), fill=(70, 56, 104)); d.rectangle((0, 104, S, 109), fill=(22, 18, 38))
    # suelo de madera oscuro con tablones
    piso = degradado([(52, 36, 66), (40, 28, 54), (28, 20, 42)], 109, S)
    a = np.asarray(img).copy(); a[109:] = piso[109:]; img = Image.fromarray(a, "RGB"); d = ImageDraw.Draw(img)
    for y in range(114, S, 9):
        d.line([(0, y), (S, y)], fill=(24, 16, 36))
    for y in range(109, S, 9):
        for x in range((y * 7) % 40, S, 40):
            d.line([(x, y), (x, y + 8)], fill=(24, 16, 36))
    # ventanales arqueados con noche estrellada
    for (x0, x1) in ((12, 42), (118, 148)):
        cielo = degradado([(6, 12, 36), (16, 30, 72), (30, 56, 112)], 14, 92)
        ventana = Image.fromarray(cielo, "RGB")
        mask = Image.new("L", (S, S), 0)
        md = ImageDraw.Draw(mask)
        md.rectangle((x0, 28, x1, 92), fill=255); md.ellipse((x0, 14, x1, 42), fill=255)
        img.paste(ventana, (0, 0), mask)
        d = ImageDraw.Draw(img)
        estrellas(img, x0, 12, 70, t)
        d.rectangle((x0, 28, x1, 92), outline=(70, 52, 96), width=2); d.arc((x0, 14, x1, 42), 180, 360, fill=(70, 52, 96), width=2)
        d.line([((x0 + x1) // 2, 14), ((x0 + x1) // 2, 92)], fill=(58, 44, 82)); d.line([(x0, 56), (x1, 56)], fill=(58, 44, 82))
        d.rectangle((x0 - 3, 92, x1 + 3, 95), fill=(58, 44, 82))
    estrellas(img, 40, 0, 1, t)
    d = ImageDraw.Draw(img)
    # cortinas ciruela con pliegues y alzapaños rosa
    for (xa, xb) in ((2, 11), (43, 52), (108, 117), (149, 158)):
        d.rectangle((xa, 10, xb, 96), fill=(74, 24, 70))
        for x in range(xa + 1, xb, 3):
            d.line([(x, 10), (x, 96)], fill=(118, 42, 100))
        d.line([(xa, 10), (xb, 10)], fill=(150, 62, 120))
    for (xa, xb) in ((2, 11), (43, 52), (108, 117), (149, 158)):
        d.rectangle((xa, 56, xb, 58), fill=(240, 120, 170))
    d.rectangle((0, 8, S, 11), fill=(60, 44, 84))
    # velas de pared que parpadean (a ambos lados de Rem)
    LL = [(2, "O"), (3, "y")]
    for cx in (52, 108):
        d.rectangle((cx - 2, 63, cx + 2, 66), fill=(150, 112, 50)); d.line([(cx, 66), (cx, 70)], fill=(120, 88, 40))
        for off in (-3, 0, 3):
            d.rectangle((cx + off - 1, 58, cx + off, 62), fill=(236, 226, 196))
            s = (t + off + cx) % 4
            d.point((cx + off - 1 + (1 if s == 1 else 0), 55 + (s == 2)), fill=(255, 236, 130))
            d.point((cx + off - 1, 56 + (s == 2)), fill=(255, 150, 40))
            d.point((cx + off - 1, 57), fill=(255, 200, 80))
        for r, c in ((12, (46, 36, 66)), (8, (62, 46, 70))):
            for yy in range(-r, r + 1):
                for xx in range(-r, r + 1):
                    if xx * xx + yy * yy <= r * r and BAYER[(cx + xx) % 4, (58 + yy) % 4] > 0.55:
                        q = (cx + xx, 58 + yy)
                        if 0 <= q[0] < S and 0 <= q[1] < S and img.getpixel(q) != (236, 226, 196):
                            img.putpixel(q, c)
    # rayos de luna sobre el suelo: dos haces que oscilan de intensidad
    a = np.asarray(img).astype(float)
    for (xa, xb, xs) in ((14, 40, 52), (120, 146, 94)):
        for y in range(94, S):
            u = (y - 94) / (S - 94)
            lo = xa + (xs - xa) * u; hi = xb + (xs - xa) * u + 6 * u
            al = 0.10 + 0.05 * math.sin(2 * math.pi * (t / 24) + xa) + (0.04 if (y // 3) % 2 == 0 else 0)
            al = round(al * 12) / 12
            x_i, x_j = int(max(lo, 0)), int(min(hi, S - 1))
            if x_j > x_i:
                a[y, x_i:x_j] = mezcla(a[y, x_i:x_j], (150, 190, 255), al)
    img = Image.fromarray(a.round().astype(np.uint8), "RGB")
    d = ImageDraw.Draw(img)
    # polvo flotando en los haces
    rng = np.random.default_rng(21)
    for k in range(18):
        x0, y0 = int(rng.integers(10, 150)), int(rng.integers(96, 150))
        x = x0 + int(round(3 * math.sin(2 * math.pi * (t / 24 + k / 9))))
        y = y0 + int(round(2 * math.sin(2 * math.pi * (2 * t / 24 + k / 5))))
        if (t + k) % 6 < 4:
            d.point((x, y), fill=(210, 226, 255))
    return img


def a_float(img):
    return np.asarray(img.resize((640, 640), Image.NEAREST)).astype(float)
