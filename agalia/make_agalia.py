"""Animación de la transformación de Agalia: forma demoníaca -> capullo de alas con estallido de chispas ->
forma humana -> nube de humo que tapa el reinicio del bucle.

Escala: el personaje va a su tamaño; las chispas y el humo, dibujados a la mitad de resolución, se amplían x2.
Pasos de 70 ms. Ciclo de L pasos (el paso 0 es el cambio de la nube de humo):
  0..3     fotograma 1 (alas plegadas); las nubes de humo se están deshaciendo delante
  4..11    fotogramas 2-5 (flota con las alas abiertas), 2 pasos cada uno; empiezan las chispas
  12..17   fotogramas 6-8 (el ala la envuelve), 2 pasos cada uno; las chispas se juntan en una cruz
  18..25   fotogramas 9-12 (se revela la forma humana), 2 pasos cada uno; las chispas estallan (pico en el 18)
  26..L-1  se queda con las manos juntas (fotogramas 11 y 12 alternando); las nubes de humo crecen y la tapan
Las chispas llegan a su fotograma de mayor tamaño justo cuando se revela la forma nueva. Salida: GIF transparente.
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "abigail"))
import alinear                  # noqa: E402
import explosion as ex          # noqa: E402  (alineación encadenada de fotogramas)
import hojas                    # noqa: E402

TICK = 70
CW, CH = alinear.CW, alinear.CH
STEP_UP, STEP_DOWN = 2, 3
PEAK_FX = 10                    # índice de las chispas que coincide con la revelación
SPARK_AT = (88, 72)             # centro de las chispas sobre el personaje
IDX = [12, 9]                   # celdas de las dos nubes de humo en el cambio (desfasadas para que se hinchen una tras otra)
HOLD = 8


def up2(img):
    return img.resize((img.width * 2, img.height * 2), Image.NEAREST)


def mask_at(img, ox, oy):
    m = np.zeros((CH, CW), bool)
    a = np.asarray(img.getchannel("A")) > 0
    x0, y0 = max(ox, 0), max(oy, 0)
    x1, y1 = min(ox + a.shape[1], CW), min(oy + a.shape[0], CH)
    if x1 > x0 and y1 > y0:
        m[y0:y1, x0:x1] = a[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
    return m


def personaje():
    """12 fotogramas alineados. Los 5 últimos (de pie) se alinean por los pies para que no se deslicen."""
    fr, pos = alinear.personaje_alineado()
    P = hojas.personaje()
    feet = []
    for k in range(7, 12):
        a = np.asarray(fr[k].getchannel("A")) > 0
        ys, xs = np.nonzero(a); bot = ys.max()
        feet.append(int(np.median(xs[ys >= bot - 8])))
    target = feet[0]
    for j, k in enumerate(range(7, 12)):
        dx = target - feet[j]
        if dx:
            c = Image.new("RGBA", fr[k].size, (0, 0, 0, 0)); c.alpha_composite(fr[k], (dx, 0)); fr[k] = c
    return fr


def chispas():
    """16 chispas x2, centradas en su silueta. Devuelve [(imagen, (dx, dy) respecto al centro)]."""
    out = []
    for f in hojas.efectos():
        im = up2(f["img"]); out.append((im, (-im.width // 2, -im.height // 2)))
    return out


def humo():
    """26 fotogramas de humo x2 alineados en cadena (la nube nace en el suelo). Devuelve (imágenes, posiciones)."""
    imgs = [up2(f["img"]) for f in hojas.humo()]
    al, pos = ex.aligned(imgs, canvas=(140, 140), search=10)
    return imgs, pos


class Humo:
    def __init__(self, imgs, pos):
        self.imgs = imgs
        p0 = pos[0]
        self.rel = [(p[0] - p0[0], p[1] - p0[1]) for p in pos]

    def at(self, k, ox, oy):
        return ox + self.rel[k][0], oy + self.rel[k][1]


def optimize(H, idxs, pre_mask, post_mask, rounds=3):
    """Coloca la(s) nube(s) de humo (esquina del fotograma 0) para que en el paso anterior (celda idx-2) tapen
    pre_mask y en el cambio (celda idx) tapen post_mask."""
    n = len(idxs)
    ub = (min(i.getchannel("A").getbbox()[0] + r[0] for i, r in zip(H.imgs, H.rel)),
          min(i.getchannel("A").getbbox()[1] + r[1] for i, r in zip(H.imgs, H.rel)),
          max(i.getchannel("A").getbbox()[2] + r[0] for i, r in zip(H.imgs, H.rel)),
          max(i.getchannel("A").getbbox()[3] + r[1] for i, r in zip(H.imgs, H.rel)))
    lo_x, hi_x, lo_y, hi_y = -ub[0], CW - ub[2], -ub[1], CH - ub[3]
    pos = [None] * n

    def cov(k, p):
        a = mask_at(H.imgs[idxs[k] - STEP_UP], *H.at(idxs[k] - STEP_UP, *p))
        b = mask_at(H.imgs[idxs[k]], *H.at(idxs[k], *p))
        return a, b

    for rnd in range(rounds):
        for k in range(n):
            cp = np.zeros((CH, CW), bool); cq = np.zeros((CH, CW), bool)
            for j in range(n):
                if j != k and pos[j] is not None:
                    a, b = cov(j, pos[j]); cp |= a; cq |= b
            if pos[k] is not None and rnd > 0:
                px, py = pos[k]
                cand = [(px + dx, py + dy) for dy in range(-3, 4) for dx in range(-3, 4)
                        if lo_x <= px + dx <= hi_x and lo_y <= py + dy <= hi_y]
            else:
                cand = [(x, y) for y in range(lo_y, hi_y + 1, 2) for x in range(lo_x, hi_x + 1, 2)]
            best = None
            for p in cand:
                a, b = cov(k, p)
                s = int((pre_mask & ~(cp | a)).sum()) + int((post_mask & ~(cq | b)).sum())
                if best is None or s < best[0]:
                    best = (s, p)
            pos[k] = best[1]
    cp = np.zeros((CH, CW), bool); cq = np.zeros((CH, CW), bool)
    for k in range(n):
        a, b = cov(k, pos[k]); cp |= a; cq |= b
    return pos, int((pre_mask & ~cp).sum()), int((post_mask & ~cq).sum())


def main():
    ch = personaje()
    chs = chispas()
    H = Humo(*humo())

    # ---- guion del personaje
    sched = [0] * 4
    for k in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11):
        sched += [k] * 2
    swap_fx = 4 + 8 + 6                     # paso en que se revela la forma humana (fotograma 9)
    for i in range(HOLD // 2):
        sched += [10 if i % 2 == 0 else 11] * 2
    L = len(sched)
    G = max(IDX) // STEP_UP
    print(f"ciclo: {L} pasos = {L * TICK} ms | humo: crecimiento de {G} pasos | chispas del paso {swap_fx - PEAK_FX} al {swap_fx - PEAK_FX + 15}")

    # ---- humo: cubre a la forma humana justo antes del reinicio y al personaje 1 justo después
    m_pre = np.asarray(ch[sched[L - 1]].getchannel("A")) > 0
    m_post = np.asarray(ch[sched[0]].getchannel("A")) > 0
    pos, a, b = optimize(H, IDX, m_pre, m_post)
    print(f"humo: a la vista antes del cambio {a} px (forma humana) | después {b} px (forma demoníaca) | posiciones {pos}")

    def humo_layers(c):
        d = c if c < L // 2 else c - L
        out = []
        for k, idx0 in enumerate(IDX):
            idx = idx0 + (STEP_UP if d <= 0 else STEP_DOWN) * d
            if 0 <= idx < len(H.imgs) and d > -G - 1:
                out.append((H.imgs[idx], H.at(idx, *pos[k])))
        return out

    frames = []
    for c in range(L):
        can = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
        can.alpha_composite(ch[sched[c]])
        fx = c - (swap_fx - PEAK_FX)
        if 0 <= fx < len(chs):                                           # chispas, por delante del personaje
            im, (dx, dy) = chs[fx]
            can.alpha_composite(im, (SPARK_AT[0] + dx, SPARK_AT[1] + dy))
        for im, p in humo_layers(c):                                     # humo por delante de todo
            can.alpha_composite(im, p)
        frames.append(can)

    boxes = [b_ for b_ in (f.getchannel("A").getbbox() for f in frames) if b_]
    box = (max(min(b_[0] for b_ in boxes) - 2, 0), max(min(b_[1] for b_ in boxes) - 2, 0),
           min(max(b_[2] for b_ in boxes) + 2, CW), min(max(b_[3] for b_ in boxes) + 2, CH))
    frames = [f.crop(box) for f in frames]
    print("lienzo recortado:", frames[0].size, "desde", box)

    def save_gif(imgs, path, scale):
        imgs = [i.resize((i.width * scale, i.height * scale), Image.NEAREST) if scale > 1 else i for i in imgs]
        colors = sorted({p[:3] for im in imgs for p in im.getdata() if p[3]})
        assert len(colors) <= 255, len(colors)
        index = {c: i + 1 for i, c in enumerate(colors)}
        flat = [255, 0, 255] + [v for c in colors for v in c]
        pal = []
        for im in imgs:
            p = Image.new("P", im.size, 0); p.putpalette(flat + [0] * (768 - len(flat)))
            p.putdata([index[q[:3]] if q[3] else 0 for q in im.getdata()]); pal.append(p)
        pal[0].save(path, save_all=True, append_images=pal[1:], duration=TICK, loop=0,
                    transparency=0, disposal=2, optimize=False)
        return len(colors)

    for scale, suf in ((1, ""), (2, "_x2")):
        path = HERE / f"agalia_transformacion{suf}.gif"
        n = save_gif(frames, path, scale)
        print(f"{path.name}: {len(frames)} pasos, {n} colores, {path.stat().st_size / 1024:.0f} KB")
    cols = 10; w, h = frames[0].size
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGBA", (w * cols, h * rows), (60, 20, 30, 255))
    for i, f in enumerate(frames):
        sheet.alpha_composite(f, ((i % cols) * w, (i // cols) * h))
    sheet.save(Path("/projects/sandbox/tmp") / "agalia_hoja.png")


if __name__ == "__main__":
    main()
