"""Propuestas de marco para Lady (tema oscuro, gótico / emo, con detalles del personaje): llamas rojas, tachuelas, cadenas, corazones.

  1 sangre y llamas        negro -> carmesí       llamas rojas en las esquinas (como su pelo) y tachuelas
  2 medianoche verde azulado  verde azulado -> casi negro   cadenas con corazón colgante y cruces, brillos
  3 morado gótico y plata  violeta -> plata       pinchos plateados, corazón con cadenas y cruces
  4 acero y arcoíris       acero oscuro           gemas arcoíris que cambian de color y tachuelas
Vista previa con Lady (pelo en llamas) a x5 en la ventana de 640 px sobre el escenario B (silueta negra); ciclos de 12 pasos.
Salida en previews/.
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
import escenario as esc         # noqa: E402
import hojas                    # noqa: E402

PREV = HERE / "previews"
WIN = (24, 24, 103, 103)
OSC = (14, 8, 14)


def quantize_rgb(rgb, k):
    img = Image.fromarray(rgb.reshape(-1, 1, 3).astype(np.uint8), "RGB")
    q = img.quantize(colors=k, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = np.array(q.getpalette()[:768], np.uint8).reshape(-1, 3)
    return pal[np.asarray(q).reshape(-1)]


# ---- paletas (arriba, abajo) ---------------------------------------------------------------------------------------
P1 = ([(0.0, (6, 4, 6)), (0.3, (28, 20, 24)), (0.6, (64, 44, 50)), (0.85, (120, 86, 92)), (1.0, (200, 170, 176))],
      [(0.0, (20, 0, 4)), (0.3, (80, 4, 16)), (0.6, (160, 12, 28)), (0.85, (226, 60, 60)), (1.0, (255, 170, 160))])
P2 = ([(0.0, (4, 10, 12)), (0.3, (14, 36, 40)), (0.6, (34, 80, 86)), (0.85, (80, 140, 146)), (1.0, (190, 230, 230))],
      [(0.0, (2, 6, 8)), (0.3, (8, 24, 28)), (0.6, (20, 54, 60)), (0.85, (50, 100, 106)), (1.0, (140, 190, 190))])
P3 = ([(0.0, (10, 4, 20)), (0.3, (40, 16, 70)), (0.6, (84, 40, 130)), (0.85, (140, 90, 196)), (1.0, (214, 190, 240))],
      [(0.0, (10, 10, 14)), (0.3, (46, 48, 60)), (0.6, (104, 108, 126)), (0.85, (170, 176, 194)), (1.0, (236, 240, 250))])
P4 = ([(0.0, (4, 4, 6)), (0.3, (22, 24, 30)), (0.6, (52, 56, 68)), (0.85, (96, 104, 122)), (1.0, (190, 200, 220))],
      [(0.0, (2, 2, 4)), (0.3, (14, 14, 18)), (0.6, (34, 36, 44)), (0.85, (70, 74, 88)), (1.0, (150, 156, 174))])


# ---- dibujo --------------------------------------------------------------------------------------------------------
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


def llama(img, x, y, t, fase=0):
    """Llama roja de 11x14 con 4 posturas (como el pelo de Lady). (x, y) = esquina superior izquierda."""
    s = (t + fase) % 4
    sway = (-1, 0, 1, 0)[s]
    H = (14, 13, 14, 12)[s]
    px = img.load()
    cel = {}
    for j in range(H):
        u = j / (H - 1)
        hw = 4.8 * (u ** 0.75) * (1 - 0.12 * u) + 0.4
        cx = 5 + sway * (1 - u) * 1.6
        for i in range(11):
            d = abs(i - cx)
            if d <= hw:
                r = d / max(hw, 0.5)
                col = (150, 8, 20) if r > 0.78 else ((232, 24, 32) if (r > 0.38 or u < 0.35) else (255, 110, 60))
                cel[(x + i, y + j + (14 - H))] = col
    for (cx_, cy_) in list(cel):
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                q = (cx_ + dx, cy_ + dy)
                if q not in cel and 0 <= q[0] < img.width and 0 <= q[1] < img.height:
                    px[q] = (*OSC, 255)
    for (cx_, cy_), col in cel.items():
        if 0 <= cx_ < img.width and 0 <= cy_ < img.height:
            px[cx_, cy_] = (*col, 255)


def tachuela(img, x, y):
    px = img.load()
    for (dx, dy, c) in ((0, 0, (150, 156, 172)), (-1, -1, (226, 232, 246)), (1, 1, (70, 74, 92)), (0, -1, (226, 232, 246)),
                        (-1, 0, (226, 232, 246)), (1, 0, (110, 116, 134)), (0, 1, (110, 116, 134))):
        if 0 <= x + dx < img.width and 0 <= y + dy < img.height:
            px[x + dx, y + dy] = (*c, 255)


CORAZON = [".rr...rr.", "rRRr.rRRr", "rRhRRRRRr", "rRRRRRRRr", ".rRRRRRr.", "..rRRRr..", "...rRr...", "....r...."]
CRUZ = ["..sss..", "..sws..", "sssssss", "swwsssw", "sssssss", "..sss..", "..sss..", "..sss..", "..sss.."]
CMAP = {"r": (150, 8, 22), "R": (240, 30, 50), "h": (255, 160, 170), "s": (170, 176, 196), "w": (240, 244, 255)}


def cadena(img, x, y0, largo, t, col=(170, 176, 196), fase=0):
    """Cadena que cuelga de (x, y0): eslabones alternos con un balanceo de 1 px; devuelve la posición final."""
    d = ImageDraw.Draw(img)
    sway = (0, 1, 1, 0, -1, -1)[(t + fase) % 6]
    y = y0
    k = 0
    while y < y0 + largo:
        xx = x + (sway if y > y0 + largo // 2 else 0)
        if k % 2 == 0:
            d.rectangle((xx - 1, y, xx + 1, y + 2), outline=col + (255,))
            d.point((xx, y + 1), fill=OSC + (255,))
        else:
            d.line((xx, y, xx, y + 2), fill=col + (255,))
        y += 3
        k += 1
    return x + sway, y


def brillo(img, cx, cy, r, col=(255, 255, 255)):
    d = ImageDraw.Draw(img)
    d.line((cx - r, cy, cx + r, cy), fill=col + (255,)); d.line((cx, cy - r, cx, cy + r), fill=col + (255,))
    d.point((cx, cy), fill=(255, 255, 255, 255))


def pincho(img, x, y, abajo=False):
    """Cono plateado de 5x5 (apunta arriba, o abajo si abajo=True)."""
    px = img.load()
    filas = [(0, (230, 236, 250)), (1, (186, 192, 210)), (2, (150, 156, 174))]
    for j, ancho in enumerate((1, 3, 5)):
        for i in range(ancho):
            yy = y + (4 - 2 * j + 2 if False else 0)
    rows = ["..w..", ".wmd.", "wmmdd"]
    cm = {"w": (240, 244, 255), "m": (170, 176, 196), "d": (84, 88, 106)}
    if abajo:
        rows = rows[::-1]
    blit(img, rows, x, y, cm, contorno=False)


ARCO = [(255, 40, 60), (255, 150, 20), (255, 230, 40), (60, 210, 90), (50, 150, 255), (180, 70, 255)]


def gema(img, cx, cy, color):
    d = ImageDraw.Draw(img)
    pts = [(cx, cy - 4), (cx + 4, cy), (cx, cy + 4), (cx - 4, cy)]
    d.polygon([(cx, cy - 5), (cx + 5, cy), (cx, cy + 5), (cx - 5, cy)], fill=OSC + (255,))
    d.polygon(pts, fill=color + (255,))
    d.point((cx - 1, cy - 1), fill=(255, 255, 255, 255))


# ---- detalles por opción ---------------------------------------------------------------------------------------------
ESQ = ((0, 0), (117, 0), (0, 115), (117, 115))


def det1(fr, t):
    for i, (x, y) in enumerate(ESQ):
        llama(fr, x, y + (0 if y == 0 else 0), t, i)
    for x in range(22, 108, 14):
        tachuela(fr, x, 2); tachuela(fr, x, 125)
    for y in range(22, 108, 14):
        tachuela(fr, 2, y); tachuela(fr, 125, y)


def det2(fr, t):
    for (x, y) in ESQ:
        blit(fr, CRUZ, x + 2, y + 1 if y == 0 else y, CMAP)
    for k, x in enumerate((38, 90)):
        cx, cy = cadena(fr, x, 0, 12, t, fase=k * 3)
        blit(fr, CORAZON, cx - 4, cy - 1, CMAP)
    for k, (x, y) in enumerate(((22, 4), (106, 4), (4, 40), (123, 70), (64, 124))):
        if (t + k * 2) % 6 < 3:
            brillo(fr, x, y, 2, (150, 240, 240))


def det3(fr, t):
    for x in range(14, 114, 9):
        pincho(fr, x, 0)
        pincho(fr, x, 123, abajo=True)
    for (x, y) in ESQ:
        blit(fr, CRUZ, x + 2, y + 1 if y == 0 else y, CMAP)
    cx, cy = cadena(fr, 64, 0, 10, t)
    blit(fr, CORAZON, cx - 4, cy - 1, CMAP)
    for k, (x, y) in enumerate(((4, 30), (123, 30), (4, 100), (123, 100))):
        if (t + k * 2) % 6 < 3:
            brillo(fr, x, y, 2, (230, 230, 255))


def det4(fr, t):
    for k, (x, y) in enumerate(((6, 6), (121, 6), (6, 121), (121, 121))):
        gema(fr, x, y, ARCO[(t // 2 + k) % 6])
    for x in range(22, 108, 14):
        tachuela(fr, x, 2); tachuela(fr, x, 125)
    for y in range(22, 108, 14):
        tachuela(fr, 2, y); tachuela(fr, 125, y)
    for k, x in enumerate((40, 64, 88)):
        gema(fr, x, 3, ARCO[(t // 2 + k * 2) % 6]) if False else None


OPCIONES = [("1_sangre_y_llamas", P1, det1), ("2_verde_azulado", P2, det2), ("3_morado_y_plata", P3, det3), ("4_acero_y_arcoiris", P4, det4)]


def ventana():
    """Ventana de 640 px con el escenario B en calma y Lady con el pelo en llamas (a x5)."""
    w = esc.ventana("B", -1)
    f = hojas.NORMAL["1.8"]
    w.alpha_composite(f["img"], (int(round(64 - f["pies"])), 118 - hojas.SUELO))
    return w.resize((640, 640), Image.NEAREST)


def componer(fr, win):
    base = Image.new("RGBA", (1024, 1024), (0, 0, 0, 255))
    base.alpha_composite(win, (WIN[0] * 8, WIN[1] * 8))
    base.alpha_composite(fr.resize((1024, 1024), Image.NEAREST))
    return base.convert("RGB")


def main():
    PREV.mkdir(exist_ok=True)
    win = ventana()
    estaticas = []
    for nombre, (top, bot), det in OPCIONES:
        f0, _ = marco.build(top, bot)
        f0 = f0.copy()
        km = 150
        while True:
            a = np.array(f0); op = a[..., 3] > 0
            a[..., :3][op] = quantize_rgb(a[..., :3][op], km)
            base = Image.fromarray(a, "RGBA")
            frames = []
            for t in range(12):
                fr = base.copy(); det(fr, t)
                frames.append(componer(fr, win))
            arrs = [np.asarray(f) for f in frames]
            key = lambda a_: a_[..., 0].astype(np.uint32) << 16 | a_[..., 1].astype(np.uint32) << 8 | a_[..., 2]
            keys = np.unique(np.concatenate([key(a_).ravel() for a_ in arrs]))
            if len(keys) <= 256:
                break
            km -= max(6, len(keys) - 256)
        pal = np.zeros(768, np.uint8)
        pal[0:len(keys) * 3:3], pal[1:len(keys) * 3:3], pal[2:len(keys) * 3:3] = keys >> 16, keys >> 8 & 255, keys & 255
        out = []
        for a_ in arrs:
            p = Image.fromarray(np.searchsorted(keys, key(a_)).astype(np.uint8), "P"); p.putpalette(pal.tolist()); out.append(p)
        ruta = PREV / f"marco_lady_{nombre}.gif"
        out[0].save(ruta, save_all=True, append_images=out[1:], duration=80, loop=0, disposal=1, optimize=False)
        print(f"{ruta.name}: {len(keys)} colores, marco {km} tonos, {ruta.stat().st_size / 1024:.0f} KB")
        frames[2].save(PREV / f"marco_lady_{nombre}.png")
        estaticas.append(frames[2])
    hoja = Image.new("RGB", (1024, 1024))
    for i, im in enumerate(estaticas):
        hoja.paste(im.resize((512, 512), Image.LANCZOS), ((i % 2) * 512, (i // 2) * 512))
    hoja.save(PREV / "marcos_lady_opciones.png")


if __name__ == "__main__":
    main()
