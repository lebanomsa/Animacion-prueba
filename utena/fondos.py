"""Cuatro fondos pixel art para Utena (128x128 nativos, se ven a x5 en la ventana del marco). Animados en ciclos que caben
en los 32 fotogramas de la animación, así que el bucle enlaza.

  A oficina de noche   ventana grande con la ciudad: luces de los edificios que se encienden y apagan, estrellas
  B pasillo            pared clara, ventana con luz, puerta de madera (como la ilustración de referencia); motas de polvo
  C abstracto          degradado morado con estrellas de 4 puntas que destellan y corazones que suben
  D infierno kawaii    cielo magenta, llamas rosas que bailan, chispas que suben y murcielaguitos
Los pies de Utena quedan en la fila 117 de la ventana; el suelo empieza en la 100.
Salida: previews/fondo_<letra>_*.gif (con el marco) y previews/fondos_opciones.png.
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

S = 128
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
YY, XX = np.mgrid[0:S, 0:S]
UMB = BAYER[YY % 4, XX % 4]


def degradado(colores, y0, y1):
    n = len(colores) - 1
    pos = np.clip((YY - y0) / max(1, y1 - y0), 0, 1) * n
    idx = np.minimum(pos.astype(int), n - 1)
    pick = np.where(pos - idx > UMB, idx + 1, idx)
    return np.array(colores, np.uint8)[pick]


def img(arr):
    return Image.fromarray(np.ascontiguousarray(arr), "RGB")


def estrella4(d, x, y, r, col, centro=(255, 255, 255)):
    d.line((x - r, y, x + r, y), fill=col); d.line((x, y - r, x, y + r), fill=col)
    d.point((x, y), fill=centro)


CORAZON5 = [".r.r.", "rRrRr", "rRRRr", ".rRr.", "..r.."]


def corazon(px, x, y, cols):
    for j, f in enumerate(CORAZON5):
        for i, ch in enumerate(f):
            if ch != "." and 0 <= x + i < S and 0 <= y + j < S:
                px[x + i, y + j] = cols[ch]


# ---- A: oficina de noche ---------------------------------------------------------------------------------------------
def oficina(t):
    a = np.zeros((S, S, 3), np.uint8)
    a[:] = (40, 30, 62)
    a[:, ::16] = (34, 25, 54)                                          # paneles de la pared
    a[10:80, 12:117] = degradado([(12, 14, 44), (20, 20, 60), (34, 26, 78), (48, 32, 92)], 10, 80)[10:80, 12:117]
    im = img(a); d = ImageDraw.Draw(im); px = im.load()
    rng = np.random.default_rng(4)
    for k in range(14):                                                # estrellas
        x, y = int(rng.integers(14, 115)), int(rng.integers(12, 40))
        if (t + k) % 8 < 6:
            px[x, y] = (200, 206, 240)
    d.ellipse((94, 16, 104, 26), fill=(240, 236, 214)); d.ellipse((96, 18, 99, 21), fill=(220, 214, 192))
    # edificios lejanos y cercanos
    x = 12
    rng = np.random.default_rng(7)
    while x < 117:
        w = int(rng.integers(6, 12)); h = int(rng.integers(14, 32))
        d.rectangle((x, 79 - h, x + w - 1, 79), fill=(30, 26, 64)); x += w
    x = 10
    luces = []
    while x < 117:
        w = int(rng.integers(8, 15)); h = int(rng.integers(10, 26))
        d.rectangle((x, 79 - h, x + w - 1, 79), fill=(18, 14, 40))
        for yy in range(79 - h + 3, 77, 4):
            for xx in range(x + 2, x + w - 2, 3):
                if rng.random() < 0.55:
                    luces.append((xx, yy, int(rng.integers(0, 32))))
        x += w
    for (xx, yy, fase) in luces:
        if 12 <= xx < 116:
            on = ((t + fase) % 32) < 26
            c = (250, 214, 120) if on else (70, 56, 50)
            px[xx, yy] = c; px[xx + 1 if xx + 1 < 116 else xx, yy] = c
    # marco de la ventana y alféizar
    d.rectangle((10, 8, 118, 81), outline=(80, 64, 108), width=2)
    d.line((64, 10, 64, 79), fill=(24, 18, 36), width=2); d.line((12, 44, 116, 44), fill=(24, 18, 36), width=2)
    d.rectangle((8, 81, 120, 84), fill=(96, 76, 120)); d.line((8, 84, 120, 84), fill=(24, 18, 36))
    # zócalo y suelo
    d.rectangle((0, 97, S, 100), fill=(24, 18, 36))
    suelo = degradado([(60, 38, 76), (52, 32, 68), (42, 26, 56)], 101, S)
    a = np.asarray(im).copy(); a[101:] = suelo[101:]
    return img(a).convert("RGBA")


# ---- B: pasillo ---------------------------------------------------------------------------------------------------
def pasillo(t):
    a = np.zeros((S, S, 3), np.uint8)
    a[:] = (226, 214, 196)
    a[70:98] = (204, 188, 166)
    im = img(a); d = ImageDraw.Draw(im); px = im.load()
    for x0 in range(4, 92, 22):                                        # paneles del zócalo
        d.rectangle((x0, 74, x0 + 17, 94), outline=(182, 164, 140))
    d.line((0, 70, S, 70), fill=(172, 150, 124)); d.line((0, 71, S, 71), fill=(240, 232, 218))
    # ventana a la izquierda
    d.rectangle((4, 12, 26, 60), fill=(252, 248, 236))
    d.rectangle((4, 12, 26, 60), outline=(150, 118, 86), width=2)
    d.line((15, 12, 15, 60), fill=(150, 118, 86)); d.line((4, 36, 26, 36), fill=(150, 118, 86))
    # puerta de madera a la derecha (como en la ilustración)
    d.rectangle((96, 10, 127, 100), fill=(112, 74, 46))
    d.rectangle((100, 14, 127, 100), fill=(148, 98, 60))
    for (y0, y1) in ((20, 52), (58, 94)):
        d.rectangle((104, y0, 124, y1), outline=(122, 80, 48))
        d.line((105, y0 + 1, 123, y0 + 1), fill=(170, 118, 76))
    d.ellipse((102, 58, 106, 62), fill=(240, 200, 80)); d.point((103, 59), fill=(255, 240, 180))
    d.line((100, 14, 100, 100), fill=(92, 60, 36))
    # suelo de madera
    d.rectangle((0, 98, S, 100), fill=(120, 84, 56))
    for k, y in enumerate(range(101, S, 5)):
        d.rectangle((0, y, S, y + 4), fill=(178, 128, 86) if k % 2 == 0 else (166, 118, 78))
        for x in range((k * 23) % 40, S, 40):
            d.line((x, y, x, y + 4), fill=(140, 98, 64))
    # haz de luz de la ventana sobre el suelo y polvo
    a = np.asarray(im).astype(float)
    pulso = 0.10 + 0.03 * math.sin(2 * math.pi * t / 32)
    haz = (YY >= 101) & (XX >= 4 + (YY - 101) * 1.1) & (XX <= 26 + (YY - 101) * 1.6) & (UMB < 0.6)
    a[haz] = a[haz] + (np.array([255, 248, 228]) - a[haz]) * (pulso + 0.12)
    im = img(a.round().astype(np.uint8)); px = im.load()
    rng = np.random.default_rng(9)
    for k in range(12):
        x0, y0 = rng.uniform(8, 50), rng.uniform(16, 96)
        y = (y0 - 1 * t) % 84 + 14
        x = x0 + 2 * math.sin(2 * math.pi * (t / 32 + k / 6))
        if (t + k) % 4 != 0:
            px[int(x), int(y)] = (255, 252, 240)
    return im.convert("RGBA")


# ---- C: abstracto -------------------------------------------------------------------------------------------------
def abstracto(t):
    a = degradado([(26, 10, 46), (44, 18, 72), (66, 28, 100), (90, 40, 128), (112, 54, 150)], 0, S)
    r = np.hypot(XX - 64, YY - 66) / 64
    brillo = np.clip(1 - r, 0, 1)
    a = a.astype(float)
    for lim, k in ((0.25, 0.30), (0.5, 0.18), (0.75, 0.08)):           # resplandor rosa detrás del personaje (con tramado)
        m = (brillo > lim) & (UMB < 0.7)
        a[m] = a[m] + (np.array([230, 120, 200]) - a[m]) * k
    im = img(a.round().astype(np.uint8)); d = ImageDraw.Draw(im); px = im.load()
    rng = np.random.default_rng(3)
    for k in range(12):                                                # estrellas de 4 puntas que destellan
        x, y = int(rng.integers(6, 122)), int(rng.integers(6, 122))
        if 36 < x < 92 and 20 < y < 120:
            continue
        e = (t + k * 3) % 8
        col = (250, 214, 90) if k % 2 else (210, 160, 255)
        if e in (0, 1):
            estrella4(d, x, y, 3, col)
        elif e in (2, 7):
            estrella4(d, x, y, 1, col)
        else:
            px[x, y] = col
    cols = {"r": (176, 40, 96), "R": (255, 130, 176)}
    for k in range(7):                                                 # corazones que suben (128 px en 32 fotogramas)
        x0, y0 = int(rng.integers(4, 118)), int(rng.integers(0, S))
        if 34 < x0 < 90:
            x0 = x0 - 34 if x0 < 62 else x0 + 30
        y = int((y0 - 4 * t) % (S + 8)) - 6
        x = x0 + int(round(1.5 * math.sin(2 * math.pi * (t / 16 + k / 7))))
        corazon(px, x, y, cols)
    return im.convert("RGBA")


# ---- D: infierno kawaii -------------------------------------------------------------------------------------------
LLAMA = [["...a...", "..aba..", ".abcba.", ".abcba.", "abcccba", "abcccba"],
         ["....a..", "...aba.", "..abcba", ".abcba.", "abcccba", "abcccba"],
         ["..a....", ".aba...", "abcba..", ".abcba.", "abcccba", "abcccba"],
         ["...a...", "...b...", "..aba..", ".abcba.", "abcccba", "abcccba"]]
LL_C = {"a": (232, 70, 150), "b": (255, 140, 190), "c": (255, 220, 236)}
MURCIELAGO = [["k.....k", "kk.k.kk", "kkkkkkk", ".k...k."], ["...k...", "k.kkk.k", "kkkkkkk", "kk...kk"]]


def infierno(t):
    a = degradado([(36, 6, 40), (70, 14, 70), (110, 26, 96), (150, 44, 118), (186, 66, 136)], 0, 100)
    im = img(a); d = ImageDraw.Draw(im); px = im.load()
    rng = np.random.default_rng(5)
    for x in range(0, S, 2):                                           # agujas de roca al fondo
        h = int(20 + 14 * abs(math.sin(x / 9)) + 6 * math.sin(x / 3.3))
        d.line((x, 100 - h, x, 100), fill=(64, 16, 56)); d.line((x + 1, 100 - h + 2, x + 1, 100), fill=(64, 16, 56))
    # llamas detrás, en dos filas
    for fila, (y0, paso, desfase) in enumerate(((86, 10, 0), (92, 9, 5))):
        for k, x in enumerate(range(-4 + desfase, S, paso)):
            forma = LLAMA[(t + k + fila * 2) % 4]
            for j, f in enumerate(forma):
                for i, ch in enumerate(f):
                    if ch != "." and 0 <= x + i < S:
                        px[x + i, y0 + j] = LL_C[ch]
    # suelo de roca
    d.rectangle((0, 98, S, S), fill=(52, 14, 44))
    d.line((0, 98, S, 98), fill=(120, 40, 90))
    for k in range(18):
        x, y = int(rng.integers(0, S)), int(rng.integers(102, S))
        d.line((x, y, x + 3, y), fill=(74, 22, 62))
    # chispas que suben
    for k in range(14):
        x0, y0 = rng.uniform(2, 126), rng.uniform(0, 100)
        y = int((y0 - 3 * t) % 100)
        x = int(x0 + math.sin(2 * math.pi * (t / 16 + k / 5)))
        px[x, y] = (255, 200, 120) if k % 3 else (255, 240, 200)
    # murcielaguitos que aletean
    for (x, y, fase) in ((14, 18, 0), (104, 26, 1), (34, 34, 1)):
        forma = MURCIELAGO[(t + fase) % 2]
        for j, f in enumerate(forma):
            for i, ch in enumerate(f):
                if ch != ".":
                    px[x + i, y + j] = (20, 4, 22)
    return im.convert("RGBA")


K_FONDO = 96


def cuantizar(frames, k):
    """Paleta común de k colores para los 32 fotogramas del fondo (corte mediano, sin tramado)."""
    mos = Image.fromarray(np.concatenate([np.asarray(f.convert("RGB")) for f in frames.values()], axis=0))
    n = len(np.unique(np.asarray(mos).reshape(-1, 3), axis=0))
    if n <= k:
        return frames
    q = mos.quantize(colors=k, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    return {t: f.convert("RGB").quantize(palette=q, dither=Image.Dither.NONE).convert("RGBA") for t, f in frames.items()}


OPCIONES = [("A_oficina_de_noche", oficina), ("B_pasillo", pasillo), ("C_abstracto", abstracto), ("D_infierno_kawaii", infierno)]


def main():
    import marco_utena as mu
    estaticas = []
    for nombre, fn in OPCIONES:
        cache = cuantizar({t: fn(t) for t in range(32)}, K_FONDO)
        fr = mu.main(fondo_fn=lambda t, c=cache: c[t % 32], salida=f"fondo_{nombre}.gif", k_tinte=24)
        estaticas.append(fr[8])
    hoja = Image.new("RGB", (1024, 1024))
    for i, im in enumerate(estaticas):
        hoja.paste(im.resize((512, 512), Image.LANCZOS), ((i % 2) * 512, (i // 2) * 512))
    hoja.save(HERE / "previews" / "fondos_opciones.png")


if __name__ == "__main__":
    main()
