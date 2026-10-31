"""Propuestas de marco y fondo para el esqueleto (pose de celebración).

Cuatro combinaciones (marco + detalles + fondo con destello). El mismo marco personalizado de siempre, recoloreado:
  1 oro -> plata       corona y estrellas      rayos dorados que giran
  2 rojo -> oro        gemas y confeti         aura de luz que late
  3 azul noche -> plata  estrellas y fuegos    foco de luz y fuegos artificiales
  4 negro -> oro       copa y estrellas        foco de luz y confeti que cae
Vista previa con el esqueleto en la pose 3.4 (festejo) a x5 dentro de la ventana de 640 px; ciclos animados de 12 pasos
(el confeti, de 24). Salida en previews/.
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
import animacion                # noqa: E402
import giros                    # noqa: E402


def quantize_rgb(rgb, k):
    img = Image.fromarray(rgb.reshape(-1, 1, 3).astype(np.uint8), "RGB")
    q = img.quantize(colors=k, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = np.array(q.getpalette()[:768], np.uint8).reshape(-1, 3)
    return pal[np.asarray(q).reshape(-1)]


PREV = HERE / "previews"
WIN = (24, 24, 103, 103)
CICLO = 12
OSC = (22, 12, 18)

ORO = [(0.0, (40, 24, 4)), (0.3, (130, 90, 16)), (0.6, (212, 160, 40)), (0.85, (250, 214, 90)), (1.0, (255, 246, 190))]
PLATA = [(0.0, (18, 20, 26)), (0.3, (70, 76, 90)), (0.6, (150, 158, 174)), (0.85, (206, 212, 226)), (1.0, (246, 248, 255))]
ROJO = [(0.0, (30, 0, 6)), (0.3, (110, 10, 24)), (0.6, (188, 28, 44)), (0.85, (232, 90, 100)), (1.0, (255, 200, 200))]
AZUL = [(0.0, (4, 8, 30)), (0.3, (16, 40, 110)), (0.6, (40, 86, 190)), (0.85, (110, 160, 240)), (1.0, (214, 232, 255))]
NEGRO = [(0.0, (6, 6, 8)), (0.3, (24, 24, 30)), (0.6, (56, 56, 68)), (0.85, (110, 108, 120)), (1.0, (200, 196, 210))]

COL = {"y": (250, 214, 90), "d": (170, 120, 20), "r": (230, 40, 60), "b": (60, 140, 255), "w": (255, 250, 220), "k": OSC}


def blit(img, rows, x, y, cmap=COL, contorno=True):
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


CORONA = ["y....y....y", "yy..yyy..yy", "yyyyyyyyyyy", "yyryybyyryy", "yyyyyyyyyyy", "ddddddddddd"]
COPA = ["yyyyyyyyyyy", "y.yyyyyyy.y", "y.yyyyyyy.y", ".yyyyyyyyy.", "..yyyyyyy..", "...yyyyy...",
        "....yyy....", "....yyy....", "...yyyyy...", "..ddddddd.."]


def estrella5(img, cx, cy, R=5.2, col=(250, 214, 90)):
    pts = []
    for k in range(10):
        r = R if k % 2 == 0 else R * 0.45
        a = -math.pi / 2 + k * math.pi / 5
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    big = Image.new("L", (img.width, img.height), 0)
    ImageDraw.Draw(big).polygon(pts, fill=255)
    m = np.asarray(big) > 0
    out = m.copy()
    out[1:] |= m[:-1]; out[:-1] |= m[1:]; out[:, 1:] |= m[:, :-1]; out[:, :-1] |= m[:, 1:]
    px = img.load()
    ys, xs = np.where(out)
    for y, x in zip(ys, xs):
        px[int(x), int(y)] = (*OSC, 255)
    ys, xs = np.where(m)
    for y, x in zip(ys, xs):
        px[int(x), int(y)] = (*col, 255)
    px[int(round(cx)) - 1, int(round(cy)) - 1] = (255, 246, 190, 255)


def gema(img, cx, cy, col=(220, 30, 50), luz=(255, 150, 160)):
    pts = [(cx, cy - 5), (cx + 5, cy), (cx, cy + 5), (cx - 5, cy)]
    big = Image.new("L", (img.width, img.height), 0)
    ImageDraw.Draw(big).polygon(pts, fill=255)
    m = np.asarray(big) > 0
    out = m.copy()
    out[1:] |= m[:-1]; out[:-1] |= m[1:]; out[:, 1:] |= m[:, :-1]; out[:, :-1] |= m[:, 1:]
    px = img.load()
    for y, x in zip(*np.where(out)):
        px[int(x), int(y)] = (*OSC, 255)
    for y, x in zip(*np.where(m)):
        px[int(x), int(y)] = (*(luz if (x - cx) + (y - cy) < -1 and y < cy + 1 else col), 255)


def destello(img, cx, cy, r, col=(255, 252, 225)):
    d = ImageDraw.Draw(img)
    d.line((cx - r, cy, cx + r, cy), fill=col + (255,)); d.line((cx, cy - r, cx, cy + r), fill=col + (255,))
    d.point((cx, cy), fill=(255, 255, 255, 255))


def brillos(img, t, pos, fase=2):
    for k, (x, y) in enumerate(pos):
        r = (1, 2, 3, 2, 1, 1)[(t + k * fase) % 6]
        destello(img, x, y, r)


def confeti_marco(img, semilla=3, n=44):
    rng = np.random.default_rng(semilla)
    cols = [(255, 90, 90), (255, 214, 80), (110, 220, 255), (140, 255, 140), (255, 160, 230)]
    px = img.load()
    for _ in range(n):
        x, y = int(rng.integers(12, 116)), int(rng.integers(0, 8))
        c = cols[int(rng.integers(0, len(cols)))]
        if rng.random() < 0.5:
            px[x, y] = (*c, 255); px[min(x + 1, 127), y] = (*c, 255)
        else:
            px[x, y] = (*c, 255); px[x, min(y + 1, 9)] = (*c, 255)


def fuego_esquina(img, cx, cy, t, fase, col):
    u = (t + fase) % CICLO
    if u >= 7:
        return
    rad = 2 + u
    d = ImageDraw.Draw(img)
    c = tuple(int(v * (0.65 if u >= 5 else 1.0)) for v in col)
    for k in range(8):
        a = k * math.pi / 4
        d.point((round(cx + rad * math.cos(a)), round(cy + rad * math.sin(a))), fill=c + (255,))
        if rad > 3:
            d.point((round(cx + rad * 0.55 * math.cos(a)), round(cy + rad * 0.55 * math.sin(a))), fill=c + (255,))


# ---- detalles por opción -----------------------------------------------------------------------------------------------
def det1(fr, t):
    for (x, y) in ((6, 6), (121, 6), (6, 121), (121, 121)):
        estrella5(fr, x, y)
    blit(fr, CORONA, 58, 1)
    brillos(fr, t, [(24, 3), (104, 3), (3, 28), (124, 28), (3, 100), (124, 100), (30, 124), (98, 124)])


def det2(fr, t):
    confeti_marco(fr)
    for (x, y) in ((6, 6), (121, 6), (6, 121), (121, 121)):
        gema(fr, x, y)
    brillos(fr, t, [(24, 3), (104, 3), (64, 124)])


def det3(fr, t):
    for (x, y) in ((6, 6), (121, 6), (6, 121), (121, 121)):
        estrella5(fr, x, y, col=(214, 232, 255))
    for k, (x, y) in enumerate(((22, 4), (106, 4), (64, 4))):
        fuego_esquina(fr, x, y, t, k * 4, [(255, 214, 80), (255, 90, 90), (110, 220, 255)][k])
    brillos(fr, t, [(3, 40), (124, 40), (3, 90), (124, 90)])


def det4(fr, t):
    for (x, y) in ((6, 6), (121, 6), (6, 121), (121, 121)):
        estrella5(fr, x, y)
    blit(fr, COPA, 58, 0)
    brillos(fr, t, [(26, 3), (102, 3), (3, 64), (124, 64)])


# ---- fondos con destello (128x128 nativos, RGB) -----------------------------------------------------------------------
YY, XX = np.mgrid[0:128, 0:128]


def _anillos(r, cortes, colores):
    out = np.zeros((128, 128, 3), np.uint8)
    out[:] = colores[-1]
    for lim, c in reversed(list(zip(cortes, colores))):
        out[r < lim] = c
    return out


def fondo_rayos(t, n=128):
    """Abanico de rayos dorados que gira; `n` = lado en píxeles nativos (128 a x5, 107 a x6: mismos tamaños en pantalla)."""
    yy, xx = np.mgrid[0:n, 0:n]
    s = n / 128
    dx, dy = xx + 0.5 - n / 2, yy + 0.5 - n * 62 / 128
    th = np.arctan2(dy, dx)
    r = np.hypot(dx, dy) / s
    sect = np.floor(((th + 2 * math.pi * t / (12 * 12)) / (2 * math.pi)) * 24).astype(int) % 24
    base = np.where((sect % 2 == 0)[..., None], np.array([255, 226, 112]), np.array([255, 245, 184]))
    f = np.select([r < 26, r < 46, r < 66], [1.0, 0.9, 0.78], 0.64)[..., None]
    out = np.clip(base * f, 0, 255).astype(np.uint8)
    nucleo = 12 + (0, 1, 2, 3, 3, 2, 1, 0, 0, 1, 2, 3)[t % 12]
    out[r < nucleo] = (255, 252, 226)
    return Image.fromarray(out, "RGB")


def fondo_aura(t):
    dx, dy = XX + 0.5 - 64, YY + 0.5 - 62
    r = np.hypot(dx, dy) + 2.5 * math.sin(2 * math.pi * t / 12)
    out = _anillos(r, [16, 28, 42, 58, 76, 96],
                   [(255, 252, 230), (255, 236, 150), (252, 196, 90), (236, 140, 60), (190, 80, 60), (120, 40, 70), (56, 18, 56)])
    img = Image.fromarray(out, "RGB")
    pos = [(14, 20), (112, 16), (20, 100), (110, 104), (60, 8), (8, 62), (120, 60), (40, 118), (92, 120), (30, 44)]
    px = img.load()
    for k, (x, y) in enumerate(pos):
        r_ = (1, 2, 3, 2, 1, 1)[(t + k * 2) % 6]
        for dx_ in range(-r_, r_ + 1):
            px[x + dx_, y] = (255, 250, 220)
        for dy_ in range(-r_, r_ + 1):
            px[x, y + dy_] = (255, 250, 220)
    return img


def _estrellas(img, semilla, col=(200, 214, 255), n=40):
    rng = np.random.default_rng(semilla)
    px = img.load()
    for _ in range(n):
        px[int(rng.integers(0, 128)), int(rng.integers(0, 128))] = col


def fondo_fuegos(t):
    dx, dy = XX + 0.5 - 64, YY + 0.5 - 66
    r = np.hypot(dx, dy)
    out = np.zeros((128, 128, 3), np.uint8)
    out[:] = (16, 24, 66)
    out[YY < 84] = (12, 18, 52)
    out[YY < 40] = (8, 12, 36)
    foco = _anillos(r, [26, 40, 56], [(150, 180, 240), (100, 132, 206), (62, 88, 160), (0, 0, 0)])
    out = np.where((r < 56)[..., None], foco, out)
    img = Image.fromarray(out.astype(np.uint8), "RGB")
    px = img.load()
    _estrellas(img, 5)
    d = ImageDraw.Draw(img)
    centros = [(22, 26, 0, (255, 214, 80)), (106, 30, 3, (255, 100, 100)), (24, 98, 6, (120, 230, 255)), (104, 96, 9, (150, 255, 150))]
    for (cx, cy, fase, col) in centros:
        u = (t + fase) % 12
        if u >= 8:
            continue
        rad = 3 + u * 3
        c = tuple(int(v * (0.6 if u >= 6 else 1.0)) for v in col)
        for k in range(12):
            a = k * math.pi / 6
            px_ = round(cx + rad * math.cos(a)); py_ = round(cy + rad * math.sin(a))
            d.rectangle((px_, py_, px_ + 1, py_ + 1), fill=c)
            if rad > 6:
                d.point((round(cx + rad * 0.6 * math.cos(a)), round(cy + rad * 0.6 * math.sin(a))), fill=c)
        if u < 2:
            d.rectangle((cx - 1, cy - 1, cx + 1, cy + 1), fill=(255, 255, 240))
    return img


def fondo_confeti(t):
    dx, dy = XX + 0.5 - 64, YY + 0.5 - 62
    r = np.hypot(dx, dy)
    out = np.where(YY[..., None] < 64, np.array([26, 14, 46]), np.array([34, 18, 58])).astype(np.uint8)
    foco = _anillos(r, [22, 36, 52, 70], [(255, 246, 200), (255, 220, 130), (230, 170, 90), (150, 90, 90), (0, 0, 0)])
    out = np.where((r < 70)[..., None], foco[..., :3], out).astype(np.uint8)
    img = Image.fromarray(out, "RGB")
    rng = np.random.default_rng(11)
    cols = [(255, 90, 90), (255, 214, 80), (110, 220, 255), (140, 255, 140), (255, 160, 230), (255, 255, 255)]
    d = ImageDraw.Draw(img)
    for k in range(64):
        x0, y0 = int(rng.integers(0, 128)), int(rng.integers(0, 128))
        vel = 1 if k % 3 else 2
        c = cols[int(rng.integers(0, len(cols)))]
        y = int((y0 + vel * 128 * t / 24) % 128)
        x = int(x0 + round(1.5 * math.sin(2 * math.pi * (t / 24 * vel) + k)))
        d.rectangle((x, y, x + 1, y + 1), fill=c)
    return img


OPCIONES = [
    ("1_oro_plata", ORO, PLATA, det1, fondo_rayos, 12),
    ("2_rojo_oro", ROJO, ORO, det2, fondo_aura, 12),
    ("3_azul_plata", AZUL, PLATA, det3, fondo_fuegos, 12),
    ("4_negro_oro", NEGRO, ORO, det4, fondo_confeti, 24),
]


def esqueleto_capa():
    fr = animacion.pasos()
    boxes = [f.getchannel("A").getbbox() for f in fr]
    box = (min(b[0] for b in boxes) - 1, min(b[1] for b in boxes) - 1, max(b[2] for b in boxes) + 1, max(b[3] for b in boxes) + 1)
    box = (max(box[0], 0), max(box[1], 0), min(box[2], giros.CW), min(box[3], giros.CH))
    return giros.colocar(giros.F["3.4"]).crop(box)


def ventana(fondo_img, sk):
    w = fondo_img.convert("RGBA")
    w.alpha_composite(sk, ((128 - sk.width) // 2, 128 - sk.height - 2))
    return w.resize((640, 640), Image.NEAREST)


def componer(fr, win):
    base = Image.new("RGBA", (1024, 1024), (0, 0, 0, 255))
    base.alpha_composite(win, (WIN[0] * 8, WIN[1] * 8))
    base.alpha_composite(fr.resize((1024, 1024), Image.NEAREST))
    return base.convert("RGB")


def main():
    PREV.mkdir(exist_ok=True)
    sk = esqueleto_capa()
    print("esqueleto", sk.size)
    estaticas = []
    for nombre, top, bot, det, fondo, n in OPCIONES:
        fr0, _ = marco.build(top, bot)
        fr0 = fr0.copy()
        km = 150
        while True:
            a = np.array(fr0); op = a[..., 3] > 0
            a[..., :3][op] = quantize_rgb(a[..., :3][op], km)
            base = Image.fromarray(a, "RGBA")
            frames = []
            for t in range(n):
                fr = base.copy()
                det(fr, t % 12)
                frames.append(componer(fr, ventana(fondo(t), sk)))
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
        ruta = PREV / f"marco_{nombre}.gif"
        out[0].save(ruta, save_all=True, append_images=out[1:], duration=80, loop=0, disposal=1, optimize=False)
        print(f"{ruta.name}: {n} pasos, {len(keys)} colores, marco {km} tonos, {ruta.stat().st_size / 1024:.0f} KB")
        frames[3].save(PREV / f"marco_{nombre}.png")
        estaticas.append(frames[3])
    hoja = Image.new("RGB", (1024, 1024))
    for i, im in enumerate(estaticas):
        hoja.paste(im.resize((512, 512), Image.LANCZOS), ((i % 2) * 512, (i // 2) * 512))
    hoja.save(PREV / "marcos_opciones.png")


if __name__ == "__main__":
    main()
