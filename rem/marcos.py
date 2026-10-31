"""Propuestas de marco para Rem (con el bosque nevado y aurora): el mismo marco personalizado recoloreado y con detalles de su personaje.

  1 hielo y plata        azul hielo -> azul noche      carámbanos colgando, copos de nieve en las esquinas que brillan
  2 rosa y azul (Rem)    rosa -> azul                  lazo rosa arriba, encaje blanco en los bordes, destellos rosa y cian
  3 aurora de medianoche azul noche -> verde azulado   gemas de aurora que cambian de color, una franja de luz que fluye
  4 sirvienta negro y plata  negro -> plata            cuernos de oni, bolas con pinchos colgando de cadenas, encaje
Vista previa con la animación de Rem (idle + círculo mágico) sobre el bosque. Ciclos de 24 pasos.
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.append(str(ROOT / "secuencia"))
import marco                    # noqa: E402
import fondos                   # noqa: E402
import previas                  # noqa: E402

PREV = HERE / "previews"
OSC = (10, 8, 20)
WIN = (24, 24, 103, 103)

P1 = ([(0.0, (10, 34, 70)), (0.3, (40, 100, 170)), (0.6, (110, 180, 230)), (0.85, (190, 230, 250)), (1.0, (240, 252, 255))],
      [(0.0, (4, 8, 24)), (0.3, (10, 24, 64)), (0.6, (24, 54, 120)), (0.85, (60, 110, 180)), (1.0, (150, 200, 240))])
P2 = ([(0.0, (60, 10, 40)), (0.3, (170, 50, 110)), (0.6, (240, 110, 170)), (0.85, (255, 170, 205)), (1.0, (255, 225, 238))],
      [(0.0, (6, 14, 60)), (0.3, (20, 60, 160)), (0.6, (60, 140, 235)), (0.85, (130, 205, 255)), (1.0, (215, 242, 255))])
P3 = ([(0.0, (3, 5, 16)), (0.3, (10, 18, 50)), (0.6, (24, 40, 100)), (0.85, (60, 90, 160)), (1.0, (150, 180, 230))],
      [(0.0, (6, 22, 30)), (0.3, (14, 70, 80)), (0.6, (40, 150, 140)), (0.85, (110, 210, 190)), (1.0, (200, 250, 235))])
P4 = ([(0.0, (4, 4, 8)), (0.3, (22, 22, 34)), (0.6, (50, 52, 70)), (0.85, (100, 106, 134)), (1.0, (190, 196, 220))],
      [(0.0, (40, 44, 60)), (0.3, (110, 116, 140)), (0.6, (180, 186, 206)), (0.85, (226, 230, 242)), (1.0, (255, 255, 255))])


def quantize_rgb(rgb, k):
    img = Image.fromarray(rgb.reshape(-1, 1, 3).astype(np.uint8), "RGB")
    q = img.quantize(colors=k, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = np.array(q.getpalette()[:768], np.uint8).reshape(-1, 3)
    return pal[np.asarray(q).reshape(-1)]


def blit(img, rows, x, y, cmap, contorno=True):
    px = img.load()
    celdas = {(x + i, y + j): ch for j, row in enumerate(rows) for i, ch in enumerate(row) if ch != "."}
    if contorno:
        for (cx, cy) in celdas:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    q = (cx + dx, cy + dy)
                    if q not in celdas and 0 <= q[0] < img.width and 0 <= q[1] < img.height:
                        px[q] = (*OSC, 255)
    for (cx, cy), ch in celdas.items():
        if 0 <= cx < img.width and 0 <= cy < img.height:
            px[cx, cy] = (*cmap[ch], 255)


COPO = ["....w....", ".w..w..w.", "..w.w.w..", "...www...", "wwwwwwwww", "...www...", "..w.w.w..", ".w..w..w.", "....w...."]
LAZO = ["..rrrr.rrrr..", ".rRRRrkrRRRr.", "rRhRRRkRRRRRr", "rRRRRrkrRRRRr", ".rrrr.k.rrrr.", "....rRkRr....", "....rR.Rr....", "...rR...Rr..."]
CUERNO_I = ["...p.", "..ww.", "..ww.", ".www.", ".www.", "wwww."]
CUERNO_D = [r[::-1] for r in CUERNO_I]
ESQ = ((1, 1), (118, 1), (1, 118), (118, 118))


def copo(img, x, y, t, fase=0):
    col = (255, 255, 255) if (t + fase) % 6 < 3 else (170, 232, 255)
    blit(img, COPO, x, y, {"w": col})


def carambanos(img, t):
    px = img.load()
    d = ImageDraw.Draw(img)
    for k, x in enumerate(range(15, 114, 6)):
        L = (5, 9, 6, 11, 7)[k % 5]
        for j in range(L):
            w = 1 if j > L * 0.55 else 2
            for i in range(-w, w + 1):
                px[x + i, j] = (*((210, 240, 255) if i <= 0 else (110, 180, 225)), 255)
        d.point((x, L), fill=(255, 255, 255, 255))
    # gotas que brillan
    for k, x in enumerate((21, 45, 75, 99)):
        if (t + k * 3) % 6 < 2:
            d.point((x, 6 + (t + k) % 5), fill=(220, 250, 255, 255))


def brillo(img, cx, cy, r, col):
    d = ImageDraw.Draw(img)
    d.line((cx - r, cy, cx + r, cy), fill=col + (255,)); d.line((cx, cy - r, cx, cy + r), fill=col + (255,))
    d.point((cx, cy), fill=(255, 255, 255, 255))


def encaje(img, y, abajo=False):
    d = ImageDraw.Draw(img)
    for x0 in range(12, 116, 6):
        pts = [(0, 1), (1, 2), (2, 3), (3, 3), (4, 2), (5, 1)]
        for (dx, dy) in pts:
            yy = y + (3 - dy if abajo else dy)
            d.point((x0 + dx, yy), fill=(244, 246, 255, 255))
            d.point((x0 + dx, yy + (-1 if abajo else 1)), fill=(150, 160, 200, 255))


def pelota(img, cx, cy):
    d = ImageDraw.Draw(img)
    d.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=OSC + (255,))
    d.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill=(140, 148, 172, 255))
    d.point((cx - 1, cy - 1), fill=(236, 240, 255, 255)); d.point((cx + 1, cy + 1), fill=(70, 76, 98, 255))
    for a in range(8):
        ang = a * math.pi / 4
        for r in (4, 5):
            d.point((round(cx + r * math.cos(ang)), round(cy + r * math.sin(ang))), fill=(210, 216, 236, 255))


def cadena(img, x, y0, largo, t, fase=0):
    d = ImageDraw.Draw(img)
    sway = (0, 1, 1, 0, -1, -1)[(t + fase) % 6]
    y = y0; k = 0
    while y < y0 + largo:
        xx = x + (sway if y > y0 + largo // 2 else 0)
        d.rectangle((xx - 1, y, xx + 1, y + 2), outline=(176, 182, 202, 255)) if k % 2 == 0 else d.line((xx, y, xx, y + 2), fill=(176, 182, 202, 255))
        y += 3; k += 1
    return x + sway, y


ARCO = [(60, 230, 200), (120, 255, 180), (150, 100, 240), (240, 110, 190)]


def color_aurora(u):
    u = (u % 1.0) * len(ARCO)
    i = int(u) % len(ARCO)
    f = u - int(u)
    a, b = np.array(ARCO[i]), np.array(ARCO[(i + 1) % len(ARCO)])
    return tuple(int(v) for v in a + (b - a) * f)


def gema(img, cx, cy, color):
    d = ImageDraw.Draw(img)
    d.polygon([(cx, cy - 5), (cx + 5, cy), (cx, cy + 5), (cx - 5, cy)], fill=OSC + (255,))
    d.polygon([(cx, cy - 4), (cx + 4, cy), (cx, cy + 4), (cx - 4, cy)], fill=color + (255,))
    d.point((cx - 1, cy - 1), fill=(255, 255, 255, 255))


def det1(fr, t):
    carambanos(fr, t)
    for k, (x, y) in enumerate(ESQ):
        copo(fr, x, y + (9 if y > 100 else 0) - (9 if y > 100 else 0), t, k * 2)
    brillo(fr, 3, 64, 2, (190, 240, 255)) if (t % 6) < 3 else None
    brillo(fr, 124, 64, 2, (190, 240, 255)) if ((t + 3) % 6) < 3 else None


def det2(fr, t):
    encaje(fr, 0); encaje(fr, 124, abajo=True)
    blit(fr, LAZO, 57, 1, {"r": (150, 30, 90), "R": (255, 120, 180), "h": (255, 200, 225), "k": (110, 20, 70)}, contorno=True)
    for k, (x, y) in enumerate(((6, 6), (121, 6), (6, 121), (121, 121))):
        brillo(fr, x, y, 2 + ((t + k * 2) % 6 < 3), (255, 190, 225) if k % 2 == 0 else (170, 235, 255))


def det3(fr, t):
    d = ImageDraw.Draw(fr)
    for x in range(12, 116):
        u = x / 36 - t / 24
        c = color_aurora(u)
        d.point((x, 3), fill=c + (255,))
        d.point((x, 2), fill=tuple(int(v * 0.65) for v in c) + (255,)); d.point((x, 4), fill=tuple(int(v * 0.65) for v in c) + (255,))
        c2 = color_aurora(-x / 36 - t / 24 + 0.5)
        d.point((x, 124), fill=c2 + (255,))
        d.point((x, 123), fill=tuple(int(v * 0.65) for v in c2) + (255,)); d.point((x, 125), fill=tuple(int(v * 0.65) for v in c2) + (255,))
    for k, (x, y) in enumerate(((6, 6), (121, 6), (6, 121), (121, 121))):
        gema(fr, x, y, color_aurora(t / 24 + k * 0.25))
    for k, (x, y) in enumerate(((3, 40), (124, 40), (3, 88), (124, 88))):
        if (t + k * 2) % 6 < 3:
            brillo(fr, x, y, 2, color_aurora(t / 24 + k * 0.25))


def det4(fr, t):
    encaje(fr, 0); encaje(fr, 124, abajo=True)
    cm = {"w": (240, 244, 255), "p": (255, 150, 200)}
    blit(fr, CUERNO_I, 55, 2, cm, contorno=True); blit(fr, CUERNO_D, 69, 2, cm, contorno=True)
    for k, x in enumerate((22, 106)):
        cx, cy = cadena(fr, x, 0, 12, t, fase=k * 3)
        pelota(fr, cx, cy + 4)
    for k, (x, y) in enumerate(((6, 6), (121, 6), (6, 121), (121, 121))):
        brillo(fr, x, y, 2, (255, 190, 225)) if (t + k * 3) % 6 < 3 else None


OPCIONES = [("1_hielo_y_plata", P1, det1), ("2_rosa_y_azul", P2, det2), ("3_aurora_de_medianoche", P3, det3), ("4_sirvienta_negro_y_plata", P4, det4)]


def main():
    PREV.mkdir(exist_ok=True)
    rem = previas.op1(lambda t: fondos.a_float(fondos.bosque(t % 24)))
    estaticas = []
    for nombre, (top, bot), det in OPCIONES:
        f0, _ = marco.build(top, bot)
        f0 = f0.copy()
        km = 140
        a = np.array(f0); op = a[..., 3] > 0
        a[..., :3][op] = quantize_rgb(a[..., :3][op], km)
        base = Image.fromarray(a, "RGBA")
        frames = []
        for t in range(24):
            fr = base.copy(); det(fr, t)
            img = Image.new("RGBA", (1024, 1024), (0, 0, 0, 255))
            img.alpha_composite(rem[t].convert("RGBA"), (192, 192))
            img.alpha_composite(fr.resize((1024, 1024), Image.NEAREST))
            frames.append(img.convert("RGB"))
        ruta = PREV / f"marco_rem_{nombre}.gif"
        previas.gif(frames, ruta)
        print(f"{ruta.name}: {ruta.stat().st_size / 1024 / 1024:.1f} MB")
        frames[6].save(PREV / f"marco_rem_{nombre}.png")
        estaticas.append(frames[6])
    hoja = Image.new("RGB", (1024, 1024))
    for i, im in enumerate(estaticas):
        hoja.paste(im.resize((512, 512), Image.LANCZOS), ((i % 2) * 512, (i // 2) * 512))
    hoja.save(PREV / "marcos_rem_opciones.png")


if __name__ == "__main__":
    main()
