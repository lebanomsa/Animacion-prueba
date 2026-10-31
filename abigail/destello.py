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
from brillos import (WHITE, YEL, AMB, AMB2, BROWN, SMALL, LARGE, dilate, flash, star,  # noqa: E402,F401
                     draw_star, sparkle_points)

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


# contorno, brillos y su colocación: ver brillos.py


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
