"""Marco de Utena: el marco personalizado con un degradado en diagonal, morado arriba a la izquierda y dorado abajo a la
derecha (12 bandas diagonales, como las bandas verticales de los otros marcos), y detalles del personaje:

  * estrellas de 4 puntas en las esquinas (las de sus cuernos), doradas sobre la parte morada y moradas sobre la dorada,
    que destellan por turnos
  * un par de cuernitos dorados con una estrella morada en el centro de arriba
  * un nudo de corbata morado en el centro de abajo (el traje)
  * corazones rosas en los lados que laten (la vergüenza)
  * destellos que parpadean a lo largo del marco
Los detalles se animan en un ciclo de 8 fotogramas (la animación tiene 32, así que el bucle enlaza).
Vista previa con la animación final dentro, sobre un fondo provisional liso. Salida en previews/.
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
import marco                         # noqa: E402
import efectos_bucle as eb           # noqa: E402

PREV = HERE / "previews"
OSC = (24, 10, 34)
CICLO = 8

MORADO = [(0.0, (20, 6, 38)), (0.3, (72, 28, 124)), (0.6, (132, 72, 194)), (0.85, (192, 142, 236)), (1.0, (242, 224, 255))]
DORADO = [(0.0, (40, 24, 4)), (0.3, (130, 90, 16)), (0.6, (212, 160, 40)), (0.85, (250, 214, 90)), (1.0, (255, 246, 190))]


T0, T1 = 0.36, 0.64


def recolor_diagonal(rgb, top_stops, bot_stops):
    """Como marco.recolor, pero las bandas van en diagonal: t = 0 arriba a la izquierda y t = 1 abajo a la derecha."""
    N, B = marco.N, marco.BANDS
    yy, xx = np.mgrid[0:N, 0:N]
    lum = rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114
    v = np.clip(lum / np.percentile(lum, 98), 0, 1)
    banda = np.minimum((xx + yy) * B // (2 * N - 1), B - 1)
    t = np.clip((banda / (B - 1) - T0) / (T1 - T0), 0, 1)       # transición corta en el centro: menos tono marrón
    a, b = marco.ramp(top_stops, v), marco.ramp(bot_stops, v)
    return (a + (b - a) * t[..., None]).round().astype(np.uint8)


def quantize_rgb(rgb, k):
    img = Image.fromarray(rgb.reshape(-1, 1, 3).astype(np.uint8), "RGB")
    q = img.quantize(colors=k, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = np.array(q.getpalette()[:768], np.uint8).reshape(-1, 3)
    return pal[np.asarray(q).reshape(-1)]


# ---- detalles -------------------------------------------------------------------------------------------------------
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


ESTRELLA = ["....a....", "....a....", "...aba...", "..abcba..", "aabcdcbaa", "..abcba..", "...aba...", "....a....", "....a...."]
ESTRELLA_DESTELLO = ["....a....", "...aba...", "...aba...", "..abcba..", "abbcdcbba", "..abcba..", "...aba...", "...aba...", "....a...."]
EST_ORO = {"a": (196, 140, 30), "b": (240, 196, 70), "c": (255, 232, 140), "d": (255, 255, 230)}
EST_MOR = {"a": (100, 44, 160), "b": (150, 84, 216), "c": (200, 150, 248), "d": (250, 236, 255)}

CUERNO = ["....kk", "...kgg", "..kggl", ".kggl.", "kggl..", "ggl..."]          # curva hacia fuera, base abajo
CUERNO_C = {"k": (196, 140, 30), "g": (250, 214, 90), "l": (255, 244, 180)}
ESTRELLITA = ["..a..", ".aba.", "abcba", ".aba.", "..a.."]

CORAZON = [".rr.rr.", "rRRrRRr", "rRhRRRr", "rRRRRRr", ".rRRRr.", "..rRr..", "...r..."]
CORAZON_PEQ = [".r.r.", "rRrRr", "rRRRr", ".rRr.", "..r.."]
COR_C = {"r": (190, 46, 100), "R": (255, 120, 168), "h": (255, 236, 244)}

NUDO = ["mm.....mm", "mMm...mMm", "mMMmnmMMm", "mMMnNnMMm", "mMMmnmMMm", "mMm...mMm", "mm.....mm"]  # pajarita/nudo
NUDO_C = {"m": (74, 38, 82), "M": (116, 65, 122), "n": (90, 48, 98), "N": (160, 104, 166)}


def destello(img, x, y, r, col=(255, 252, 236)):
    d = ImageDraw.Draw(img)
    d.line((x - r, y, x + r, y), fill=col + (255,)); d.line((x, y - r, x, y + r), fill=col + (255,))
    d.point((x, y), fill=(255, 255, 255, 255))


def detalles(fr, t):
    t = t % CICLO
    # estrellas de las esquinas: destellan por turnos (cada una en 2 de los 8 fotogramas)
    esquinas = [((2, 2), EST_ORO, 0), ((117, 2), EST_MOR, 2), ((2, 117), EST_ORO, 6), ((117, 117), EST_MOR, 4)]
    for (x, y), col, fase in esquinas:
        brilla = (t - fase) % CICLO in (0, 1)
        blit(fr, ESTRELLA_DESTELLO if brilla else ESTRELLA, x, y, col)
    # cuernitos dorados con una estrellita morada en medio (arriba)
    blit(fr, CUERNO, 53, 1, CUERNO_C)
    blit(fr, [r[::-1] for r in CUERNO], 69, 1, CUERNO_C)
    blit(fr, ESTRELLITA, 61, 2, EST_MOR if t % 4 < 2 else {**EST_MOR, "c": (250, 236, 255)})
    # nudo de corbata morado (abajo)
    blit(fr, NUDO, 59, 120, NUDO_C)
    # corazones en los lados: laten (grande en 2 de cada 4 fotogramas)
    for (x, y, fase) in ((2, 60, 0), (119, 60, 2)):
        grande = (t + fase) % 4 < 2
        if grande:
            blit(fr, CORAZON, x - 1, y - 1, COR_C)
        else:
            blit(fr, CORAZON_PEQ, x, y, COR_C)
    # destellos a lo largo del marco
    pos = [(30, 3), (98, 3), (3, 34), (124, 34), (3, 92), (124, 92), (30, 124), (98, 124)]
    for k, (x, y) in enumerate(pos):
        r = (1, 2, 2, 1, 0, 0, 0, 0)[(t + k * 3) % CICLO]
        if r:
            destello(fr, x, y, r)


def marco_base(km=None):
    orig = marco.recolor
    marco.recolor = recolor_diagonal
    try:
        fr, _ = marco.build(MORADO, DORADO)
    finally:
        marco.recolor = orig
    fr = fr.copy()
    if km:
        a = np.array(fr); op = a[..., 3] > 0
        a[..., :3][op] = quantize_rgb(a[..., :3][op], km)
        fr = Image.fromarray(a, "RGBA")
    return fr


# ---- composición ----------------------------------------------------------------------------------------------------
FONDO_PROV = (34, 26, 46)


def animacion_utena():
    """La animación final, rotada para que empiece en una pose normal (paso 4: brazos abiertos con el globo vacío)."""
    fr, durs, _, _ = eb.construir(eb.capa_sonrojo, True)
    i0 = 3
    return fr[i0:] + fr[:i0], durs[i0:] + durs[:i0]


def ventana(personaje, fondo=None):
    """Ventana de 128x128 nativos: el lienzo de Utena (120x140) centrado en x y con la fila 8 arriba; luego x5 = 640 px."""
    w = Image.new("RGBA", (128, 128), (*FONDO_PROV, 255)) if fondo is None else fondo.copy()
    w.alpha_composite(personaje.crop((0, 8, 120, 136)), (4, 0))
    return w.resize((640, 640), Image.NEAREST)


def componer(fr_marco, vent):
    base = Image.new("RGBA", (1024, 1024), (0, 0, 0, 255))
    base.alpha_composite(vent, (192, 192))
    base.alpha_composite(fr_marco.resize((1024, 1024), Image.NEAREST))
    return base.convert("RGB")


def guardar(frames, durs, ruta):
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
    out[0].save(ruta, save_all=True, append_images=out[1:], duration=durs, loop=0, disposal=1, optimize=False)
    return len(keys)


def main(fondo_fn=None, salida="utena_marco_prueba.gif"):
    PREV.mkdir(exist_ok=True)
    pers, durs = animacion_utena()
    fondos = [fondo_fn(t) for t in range(len(pers))] if fondo_fn else [None] * len(pers)
    ventanas = [ventana(p, f) for p, f in zip(pers, fondos)]
    km = 70
    while True:
        base = marco_base(km)
        marcos = []
        for t in range(CICLO):
            m = base.copy(); detalles(m, t); marcos.append(m)
        frames = [componer(marcos[i % CICLO], v) for i, v in enumerate(ventanas)]
        n = guardar(frames, durs, PREV / salida)
        print(f"marco {km} tonos -> {n} colores")
        if n <= 256:
            break
        km -= max(4, n - 256)
    print(f"{salida}: {len(frames)} pasos, {sum(durs)} ms, {(PREV / salida).stat().st_size / 1024:.0f} KB")
    frames[0].save(PREV / salida.replace(".gif", ".png"))
    frames[6].save(PREV / salida.replace(".gif", "_sobresalto.png"))
    return frames


if __name__ == "__main__":
    main()
