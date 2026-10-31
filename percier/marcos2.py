"""Marco verde veneno de Percier, segunda ronda: franja superior, ojos de las calabazas que brillan y se apagan, y tamaños.

  * 4 calabazas en las esquinas con los ojos y la boca animados (ciclo de 12 pasos de 80 ms, parejas en diagonal en oposición)
  * telaraña arriba a la derecha y araña, como en la versión aprobada
  * 5 propuestas para la franja superior (luna y estrellas, fantasmitas, velas, calavera, guirnalda de luces)
Todos los ciclos animados dividen a 12 para que el bucle del marco enlace con el de Percier (72 pasos = 6 ciclos).
Salida en previews/: franja_opciones.png, franja_<nombre>.gif (vista previa de 512 px) y tamano_comparacion.png.
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).parent
ROOT = HERE.parent
for d in (HERE, ROOT / "secuencia", ROOT / "agalia"):
    sys.path.insert(0, str(d))
import marco                    # noqa: E402
import marcos as mk             # noqa: E402
import completa                 # noqa: E402
from componer_marco_agalia import quantize_rgb   # noqa: E402

PREV = HERE / "previews"
CICLO = 12
NIVELES = [3, 3, 3, 2, 1, 0, 0, 0, 1, 2, 3, 3]            # brillo de los ojos de la calabaza en cada paso del ciclo
COLOR_Y = {0: (66, 26, 6), 1: (176, 88, 14), 2: (255, 232, 110), 3: (255, 252, 200)}
HALO = (255, 206, 96)
OSCURO = (22, 12, 18)
TOP, BOT = mk.PALETAS["verde"]


def blit(img, rows, x, y, cmap):
    px = img.load()
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch != "." and ch in cmap and 0 <= x + i < img.width and 0 <= y + j < img.height:
                px[x + i, y + j] = (*cmap[ch], 255)


def calabaza(img, x, y, nivel):
    cmap = dict(mk.COL)
    cmap["y"] = COLOR_Y[nivel]
    rows = [list(r) for r in mk.CALABAZA]
    if nivel == 3:                                         # halo: la piel junto a los ojos se ilumina
        for j, r in enumerate(mk.CALABAZA):
            for i, ch in enumerate(r):
                if ch in "Oo" and any(0 <= j + b < len(mk.CALABAZA) and 0 <= i + a < len(r) and mk.CALABAZA[j + b][i + a] == "y"
                                      for a in (-1, 0, 1) for b in (-1, 0, 1)):
                    rows[j][i] = "H"
        cmap["H"] = HALO
    blit(img, ["".join(r) for r in rows], x, y, cmap)


def calabazas(img, t):
    for (x, y, fase) in ((0, 0, 0), (117, 0, 6), (0, 118, 6), (117, 118, 0)):
        calabaza(img, x, y, NIVELES[(t + fase) % CICLO])


# ---- franja superior ---------------------------------------------------------------------------------------------
def luna(img, t):
    m = np.zeros((9, 9), bool)
    for yy in range(9):
        for xx in range(9):
            m[yy, xx] = math.hypot(xx - 4, yy - 4) <= 4.4 and math.hypot(xx - 5.9, yy - 3.1) > 3.7
    px = img.load()
    for yy in range(9):
        for xx in range(9):
            if m[yy, xx]:
                px[60 + xx, yy] = (252, 240, 170, 255)
    for k, (sx, sy) in enumerate(((34, 3), (47, 6), (80, 6), (93, 3), (22, 6), (106, 6))):
        c = (255, 248, 205, 255)
        if (t + k * 2) % 6 < 3:
            for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                px[sx + dx, sy + dy] = c
        else:
            px[sx, sy] = c


FANTASMA = ["..www..", ".wwwww.", "wwwwwww", "wwkwkww", "wwwkwww", "wwwwwww", "wwwwwww", "ww.w.ww"]


def fantasmas(img, t):
    for k, cx in enumerate((34, 64, 94)):
        dy = 1 if (t + k * 2) % 6 < 3 else 0
        blit(img, FANTASMA, cx - 3, dy, {"w": (240, 244, 255), "k": OSCURO})


VELA = ["ccccd", "ccccd", "cdccd", "ccccd", "ddddd"]
LLAMA = [["..O..", ".OyO.", ".OyO."], ["...O.", ".OyO.", ".OyO."], ["..O..", ".OOO.", ".OyO."], [".O...", ".OyO.", ".OyO."]]


def velas(img, t):
    for k, cx in enumerate((34, 64, 94)):
        cm = {"c": (240, 228, 196), "d": (196, 178, 140), "O": (255, 140, 30), "y": (255, 236, 120), "k": OSCURO}
        blit(img, LLAMA[(t // 1 + k) % 4], cx - 2, 0, cm)
        blit(img, ["..k.."], cx - 2, 3, cm)
        blit(img, VELA, cx - 2, 4, cm)


CALAVERA = ["..wwwww..", ".wwwwwww.", "wwwwwwwww", "wkkwwwkkw", "wkkwwwkkw", "wwwwkwwww", ".wwwwwww.", "..wkwkw..", "..wwwww.."]


def calavera(img, t):
    n = NIVELES[(t + 3) % CICLO]
    ojo = {0: (14, 8, 10), 1: (40, 90, 20), 2: (120, 230, 60), 3: (190, 255, 110)}[n]
    rows = [r.replace("k", "e") if j in (3, 4) else r for j, r in enumerate(CALAVERA)]
    blit(img, rows, 60, 0, {"w": (236, 230, 210), "k": OSCURO, "e": ojo})


def guirnalda(img, t):
    d = ImageDraw.Draw(img)
    cols = [(255, 150, 30), (170, 255, 70), (200, 120, 255), (255, 240, 190)]
    xs = [16 + 11 * i for i in range(10)]
    prev = None
    for x in range(12, 116):
        y = 1 + round(0.9 * math.sin(math.pi * (x - 12) / 104))
        d.point((x, y), fill=OSCURO + (255,))
    for i, x in enumerate(xs):
        wy = 1 + round(0.9 * math.sin(math.pi * (x - 12) / 104))
        on = (i + t) % 3 == 0
        c = cols[i % 4]
        c = c if on else tuple(int(v * 0.32) for v in c)
        d.point((x, wy + 1), fill=OSCURO + (255,))
        d.rectangle((x - 1, wy + 2, x + 1, wy + 4), fill=c + (255,))
        if on:
            d.point((x, wy + 3), fill=(255, 255, 235, 255))


FRANJAS = {"luna": luna, "fantasmas": fantasmas, "velas": velas, "calavera": calavera, "luces": guirnalda}


# ---- marco --------------------------------------------------------------------------------------------------------
def marco_base(km=None):
    fr, _ = marco.build(TOP, BOT)
    fr = fr.copy()
    if km:
        a = np.array(fr)
        op = a[..., 3] > 0
        a[..., :3][op] = quantize_rgb(a[..., :3][op], km)
        fr = Image.fromarray(a, "RGBA")
    return fr


def marco_t(base, franja, t):
    fr = base.copy()
    mk.telarana(fr, "tr")
    mk.hilo_arana(fr, 92)
    calabazas(fr, t)
    if franja:
        FRANJAS[franja](fr, t)
    return fr


def ventana_estatica(escala_per):
    """Ventana de 640 px con Percier fijo (nube con retrato) a `escala_per`, sobre un fondo plano provisional."""
    f = completa.parte_b()[22].crop((0, 0, 139, 126))
    w = Image.new("RGBA", (640, 640), (28, 24, 48, 255))
    g = f.resize((round(f.width * escala_per), round(f.height * escala_per)), Image.NEAREST)
    w.alpha_composite(g, ((640 - g.width) // 2, 640 - g.height - 8))
    return w


def componer(fr, ventana, escala=8):
    base = Image.new("RGBA", (128 * escala, 128 * escala), (0, 0, 0, 255))
    v = ventana.resize((640 * escala // 8, 640 * escala // 8), Image.NEAREST) if escala != 8 else ventana
    base.alpha_composite(v, (24 * escala, 24 * escala))
    base.alpha_composite(fr.resize((128 * escala, 128 * escala), Image.NEAREST))
    return base.convert("RGB")


def guardar_gif(frames, path, duracion=80):
    arrs = [np.asarray(f) for f in frames]
    key = lambda a: a[..., 0].astype(np.uint32) << 16 | a[..., 1].astype(np.uint32) << 8 | a[..., 2]
    keys = np.unique(np.concatenate([key(a).ravel() for a in arrs]))
    if len(keys) > 256:
        return len(keys)
    pal = np.zeros(768, np.uint8)
    pal[0:len(keys) * 3:3], pal[1:len(keys) * 3:3], pal[2:len(keys) * 3:3] = keys >> 16, keys >> 8 & 255, keys & 255
    out = []
    for a in arrs:
        p = Image.fromarray(np.searchsorted(keys, key(a)).astype(np.uint8), "P"); p.putpalette(pal.tolist()); out.append(p)
    out[0].save(path, save_all=True, append_images=out[1:], duration=duracion, loop=0, disposal=1, optimize=False)
    return len(keys)


def previas():
    PREV.mkdir(exist_ok=True)
    vent8 = ventana_estatica(4)            # a escala 8 del marco: Percier x4
    vent4 = ventana_estatica(4).resize((320, 320), Image.NEAREST)     # a escala 4 del marco: Percier x2
    # --- hoja estática de la franja: recorte superior a x8 de cada opción, pasos 2 (ojos brillando) para ver el detalle
    base = marco_base()
    nombres = list(FRANJAS)
    tiras = []
    for n in nombres:
        full = componer(marco_t(base, n, 1), vent8)
        tiras.append(full.crop((0, 0, 1024, 200)))
    hoja = Image.new("RGB", (1024, len(tiras) * 218 + 4), (14, 10, 20))
    d = ImageDraw.Draw(hoja)
    for i, (n, t) in enumerate(zip(nombres, tiras)):
        d.text((6, i * 218 + 2), f"{i + 1}. {n}", fill=(255, 230, 120))
        hoja.paste(t, (0, i * 218 + 16))
    hoja.save(PREV / "franja_opciones.png")
    # --- GIF por opción (512 px, 12 pasos)
    for n in nombres:
        km = 160
        while True:
            b = marco_base(km)
            frs = [componer(marco_t(b, n, t), vent4, escala=4) for t in range(CICLO)]
            r = guardar_gif(frs, PREV / f"franja_{n}.gif")
            if r <= 256:
                break
            km -= 12
        print(f"franja_{n}.gif: {r} colores, marco {km} tonos, {(PREV / f'franja_{n}.gif').stat().st_size / 1024:.0f} KB")
    # gif sin franja (solo calabazas animadas)
    frs = [componer(marco_t(marco_base(160), None, t), vent4, escala=4) for t in range(CICLO)]
    print("sin franja:", guardar_gif(frs, PREV / "franja_ninguna.gif"))


def tamanos():
    """Percier a x4, x4.5 y x5 dentro de la ventana, en una pose normal y en la más ancha (1.5)."""
    base = marco_base()
    fr = marco_t(base, None, 0)
    reposo = completa.parte_b()[22].crop((0, 0, 139, 126))
    ancha = completa.parte_a()[14].crop((0, 0, 139, 126))
    paneles = []
    for pose in (reposo, ancha):
        for s in (4, 4.5, 5):
            w = Image.new("RGBA", (640, 640), (28, 24, 48, 255))
            g = pose.resize((round(pose.width * s), round(pose.height * s)), Image.NEAREST)
            x = (640 - g.width) // 2 if s < 5 else 0                 # a x5 se alinea a la izquierda: la nube se ve entera
            w.alpha_composite(g, (x, 640 - g.height - 8))
            paneles.append(componer(fr, w).resize((512, 512), Image.LANCZOS))
    hoja = Image.new("RGB", (1536, 1024))
    for i, p in enumerate(paneles):
        hoja.paste(p, ((i % 3) * 512, (i // 3) * 512))
    hoja.save(PREV / "tamano_comparacion.png")
    # recorte en x5: píxeles que se pasan de los 128 de la ventana (con la animación alineada a la izquierda)
    frames = completa.parte_a() + completa.parte_b() + completa.parte_c() + completa.parte_d()
    n_af, maxp = 0, 0
    for f in frames:
        a = np.asarray(f)[..., 3] > 0
        over = a[:, 128:].sum()
        if over:
            n_af += 1; maxp = max(maxp, int(a[:, 128:].any(0).sum()))
    print(f"a x5 con la ventana de 128 px: {n_af} de {len(frames)} pasos tienen píxeles fuera por la derecha (hasta {maxp} columnas)")


if __name__ == "__main__":
    previas()
    tamanos()
