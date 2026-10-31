"""Destello con contorno y brillos nuevos para el parpadeo final de Abigail (prueba).

Genera una hoja de prueba con:
  1. tres variantes de contorno sobre Abigail tumbada y la gorra (sobre fondo oscuro y claro),
  2. las fases de los brillos (destellos en cruz) a dos tamaños,
  3. la secuencia de 7 pasos del parpadeo con la variante elegida, y un GIF de prueba.
Todo con colores del sprite (blanco, amarillo, ámbar) y nada de semitransparencias.
"""
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import make_completa as mc      # noqa: E402

WHITE, YEL, AMB, AMB2, BROWN = (248, 248, 248), (248, 232, 112), (224, 136, 48), (240, 176, 64), (96, 32, 0)
BG_DARK, BG_LIGHT = (60, 20, 30), (230, 225, 215)
SELECTED = 4                # variante de contorno que se usa en la secuencia y en el GIF de prueba


# ------------------------------------------------------------------ escena
def scene():
    """Abigail tumbada y la gorra aterrizada, sobre el lienzo del GIF."""
    stand, walk, fall, disc, fire, rel, capf = mc.load_all()
    last = np.asarray(stand[3].getchannel("A")) > 0
    ys, xs = np.nonzero(last)
    top = ys.min(); head = xs[ys <= top + 8]
    sx = float(head.mean())
    cx, cy = sx + mc.CAP_DX, mc.G + 2 - capf[8].height / 2.0
    can = fall[12].copy()
    cap = capf[8]
    can.alpha_composite(cap, (int(round(cx - cap.width / 2)), int(round(cy - cap.height / 2))))
    return can


# ------------------------------------------------------------------ contorno
def dilate(mask, n=1):
    m = mask.copy()
    for _ in range(n):
        p = np.pad(m, 1)
        m = m | p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
    return m


def flash(img, variant):
    """Silueta blanca con contorno. 1: contorno ámbar. 2: contorno doble amarillo + ámbar.
    3: como la 2 pero conservando el trazo oscuro del dibujo original dentro de la silueta."""
    a = np.asarray(img).copy()
    alpha = a[..., 3] > 0
    out = np.zeros_like(a)
    out[alpha] = WHITE + (255,)
    if variant == 4:
        # sobreexposición por tonos: la luminosidad del dibujo original decide el tono del destello
        lum = a[..., :3].astype(int) @ np.array([0.299, 0.587, 0.114])
        out[alpha & (lum < 150)] = YEL + (255,)
        out[alpha & (lum < 85)] = AMB + (255,)
        out[alpha & (lum < 28)] = BROWN + (255,)
    if variant == 3:
        dark = alpha & (a[..., :3].sum(axis=2) < 70)
        out[dark] = BROWN + (255,)
    d1, d2 = dilate(alpha, 1), dilate(alpha, 2)
    if variant == 1:
        out[d1 & ~alpha] = AMB2 + (255,)
    else:
        out[d1 & ~alpha] = YEL + (255,)
        out[d2 & ~d1] = AMB + (255,)
    return Image.fromarray(out, "RGBA")


# ------------------------------------------------------------------ brillos
def star(phase):
    """Pixeles (dx, dy, color) de un brillo en cruz. Fases 0..3: punto, cruz pequeña, estrella, estrella grande."""
    px = [(0, 0, WHITE)]
    if phase >= 1:
        px += [(1, 0, YEL), (-1, 0, YEL), (0, 1, YEL), (0, -1, YEL)]
    if phase >= 2:
        px += [(2, 0, AMB), (-2, 0, AMB), (0, 2, AMB), (0, -2, AMB)]
    if phase >= 3:
        px = [(0, 0, WHITE), (1, 0, WHITE), (-1, 0, WHITE), (0, 1, WHITE), (0, -1, WHITE),
              (2, 0, YEL), (-2, 0, YEL), (0, 2, YEL), (0, -2, YEL),
              (3, 0, AMB), (-3, 0, AMB), (0, 3, AMB), (0, -3, AMB)]
    return px


SMALL = [0, 1, 2, 1, 0]
LARGE = [1, 2, 3, 2, 1]


SP = 2   # escala de los brillos (igual que la caída y la explosión)


def draw_star(img, x, y, phase, sp=None):
    sp = sp or SP
    for dx, dy, col in star(phase):
        for ix in range(sp):
            for iy in range(sp):
                px, py = x + dx * sp + ix, y + dy * sp + iy
                if 0 <= px < img.width and 0 <= py < img.height:
                    img.putpixel((px, py), col + (255,))


def sparkle_points(mask, n=9, seed=7, min_d=18):
    """Puntos de brillo alrededor de la silueta: sobre su contorno y un poco hacia fuera."""
    ys, xs = np.nonzero(mask)
    cx, cy = xs.mean(), ys.mean()
    edge = mask & ~dilate(~mask & True, 0) if False else mask & ~np.pad(mask, 1)[1:-1, 1:-1] | \
        (mask & (~np.roll(mask, 1, 0) | ~np.roll(mask, -1, 0) | ~np.roll(mask, 1, 1) | ~np.roll(mask, -1, 1)))
    ey, ex = np.nonzero(edge)
    rnd = random.Random(seed)
    idx = list(range(len(ex))); rnd.shuffle(idx)
    pts = []
    for i in idx:
        x, y = int(ex[i]), int(ey[i])
        v = np.array([x - cx, y - cy], float); nrm = np.linalg.norm(v) or 1.0
        x += int(round(4 * v[0] / nrm)); y += int(round(4 * v[1] / nrm))
        if all((x - px) ** 2 + (y - py) ** 2 >= min_d ** 2 for px, py, *_ in pts):
            pts.append((x, y))
        if len(pts) == n:
            break
    out = []
    starts_large, starts_small = [1, 2, 3], [1, 2, 2, 3, 3, 1]
    li = si = 0
    for k, (x, y) in enumerate(pts):
        if k % 3 == 0 and li < 3:
            out.append((x, y, LARGE, starts_large[li])); li += 1
        else:
            out.append((x, y, SMALL, starts_small[si % 6])); si += 1
    return out


def sequence(base, variant, pts):
    """8 pasos: normal, blanco, normal, blanco, normal, blanco (último destello), brillos, brillos que se apagan."""
    steps = []
    wh = flash(base, variant)
    for t in range(8):
        can = Image.new("RGBA", base.size, (0, 0, 0, 0))
        if t < 6:
            can.alpha_composite(wh if t % 2 == 1 else base)
        for x, y, phases, start in pts:
            i = t - start
            if t >= 1 and 0 <= i < len(phases):
                draw_star(can, x, y, phases[i])
        steps.append(can)
    return steps


def crop_to(imgs, pad=8):
    boxes = [b for b in (i.getchannel("A").getbbox() for i in imgs) if b]
    box = (max(min(b[0] for b in boxes) - pad, 0), max(min(b[1] for b in boxes) - pad, 0),
           min(max(b[2] for b in boxes) + pad, imgs[0].width), min(max(b[3] for b in boxes) + pad, imgs[0].height))
    return [i.crop(box) for i in imgs]


def on(bg, img):
    b = Image.new("RGBA", img.size, bg + (255,)); b.alpha_composite(img); return b


def main():
    base = scene()
    mask = np.asarray(base.getchannel("A")) > 0
    pts = sparkle_points(mask)
    print("brillos:", [(x, y, 'grande' if p is LARGE else 'pequeño', s) for x, y, p, s in pts])

    # ---- 1) contornos
    variants = {v: flash(base, v) for v in (2, 3, 4)}
    names = {2: "2: silueta blanca + contorno doble", 3: "3: + trazo oscuro del dibujo", 4: "4: blanco por tonos (propuesta) + contorno doble"}
    crops = crop_to([base] + list(variants.values()))
    S = 5
    cw, ch = crops[0].size
    W = (cw * S + 12) * 2
    sheet = Image.new("RGBA", (W, 18 + (ch * S + 22) * 4 + 18 + 1 * 150 + 18 + 30), (20, 10, 14, 255))
    sheet = Image.new("RGBA", (max(W, 1100), sheet.height), (20, 10, 14, 255))
    d = ImageDraw.Draw(sheet)
    y = 4
    d.text((6, y), "CONTORNOS (izquierda sobre fondo oscuro, derecha sobre fondo claro)", fill=WHITE)
    y += 16
    for t, (nm, img) in enumerate([("original", crops[0])] + [(names[v], crops[1 + k]) for k, v in enumerate(variants)]):
        d.text((6, y), nm, fill=YEL); y += 14
        for j, bg in enumerate((BG_DARK, BG_LIGHT)):
            z = on(bg, img).resize((cw * S, ch * S), Image.NEAREST)
            sheet.alpha_composite(z, (6 + j * (cw * S + 12), y))
        y += ch * S + 8

    # ---- 2) fases de los brillos
    d.text((6, y), "BRILLOS: fases de la cruz (pequeño 5 fases, grande 7 fases)", fill=WHITE); y += 16
    sx = 10
    for phases in (SMALL, LARGE):
        for ph in phases:
            tile = Image.new("RGBA", (9, 9), BG_DARK + (255,))
            draw_star(tile, 4, 4, ph, sp=1)
            sheet.alpha_composite(tile.resize((54, 54), Image.NEAREST), (sx, y)); sx += 62
        sx += 20
    y += 70

    # ---- 3) secuencia del parpadeo
    seq = crop_to(sequence(base, SELECTED, pts), pad=12)
    S2 = 3
    sw, sh_ = seq[0].size
    d.text((6, y), f"SECUENCIA DEL PARPADEO con la variante {SELECTED} (8 pasos de 70 ms): normal, blanco, normal, "
                   "blanco, normal, blanco, brillos, brillos que se apagan", fill=WHITE)
    y += 16
    per_row = 4
    rows = (8 + per_row - 1) // per_row
    strip = Image.new("RGBA", ((sw * S2 + 6) * per_row, (sh_ * S2 + 6) * rows), BG_DARK + (255,))
    for k, im in enumerate(seq):
        strip.alpha_composite(on(BG_DARK, im).resize((sw * S2, sh_ * S2), Image.NEAREST),
                              ((k % per_row) * (sw * S2 + 6), (k // per_row) * (sh_ * S2 + 6)))
    sheet2 = Image.new("RGBA", (max(sheet.width, strip.width), y + strip.height + 10), (20, 10, 14, 255))
    sheet2.alpha_composite(sheet.crop((0, 0, sheet.width, y)), (0, 0))
    sheet2.alpha_composite(strip, (0, y))
    out = HERE / "previews"; out.mkdir(exist_ok=True)
    sheet2.convert("RGB").save(out / "destello_prueba.png")
    print("hoja:", sheet2.size)

    # ---- GIF de prueba (transparente, en bucle, fondo transparente)
    def save_gif(imgs, path, scale):
        imgs = [i.resize((i.width * scale, i.height * scale), Image.NEAREST) for i in imgs]
        colors = sorted({p[:3] for im in imgs for p in im.getdata() if p[3]})
        index = {c: i + 1 for i, c in enumerate(colors)}
        flat = [255, 0, 255] + [v for c in colors for v in c]
        pal = []
        for im in imgs:
            p = Image.new("P", im.size, 0); p.putpalette(flat + [0] * (768 - len(flat)))
            p.putdata([index[q[:3]] if q[3] else 0 for q in im.getdata()]); pal.append(p)
        pal[0].save(path, save_all=True, append_images=pal[1:], duration=70, loop=0,
                    transparency=0, disposal=2, optimize=False)
        return len(colors)
    n = save_gif(crop_to(sequence(base, SELECTED, pts), pad=12), out / "destello_prueba.gif", 4)
    print("destello_prueba.gif:", n, "colores")


if __name__ == "__main__":
    main()
