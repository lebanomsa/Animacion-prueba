"""Animación de Abigail: caída, impacto y explosión final que tapa el reinicio del bucle.

Pasos de 70 ms. Ciclo de L pasos:
  0-7     caída (fotogramas 1-8, uno por paso); la explosión de la vuelta anterior se está deshaciendo
  8-17    impacto y melena (fotogramas 9-13, dos pasos cada uno)
  18-25   tumbada (fotograma 13), sin explosión
  L-G-1   destello (el círculo blanco del sprite de la explosión)
  L-G..L-1 la bola de fuego crece y tapa a Abigail tumbada
  0       la explosión está en su punto máximo y Abigail ya está en su primer fotograma
La explosión muestra la celda IDX + paso_de_crecimiento*d (d = pasos respecto al cambio), así que
llega al máximo justo en el cambio. El círculo oscuro del sprite se descarta.
Salida: abigail_caida.gif y abigail_caida_x4.gif (fondo transparente, bucle infinito).
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import explosion as ex      # noqa: E402
import personaje as pj      # noqa: E402

TICK = 70
CANVAS = (170, 150)
GROUND, CX = 100, 85        # fila del suelo y columna central de Abigail en el lienzo
HOLD_CLEAN = 8              # pasos que se ve a Abigail tumbada antes del destello
STEP_UP, STEP_DOWN = 2, 3   # celdas de explosión por paso al crecer y al deshacerse
FALL = [(0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1),
        (8, 2), (9, 2), (10, 2), (11, 2), (12, 2)]       # (fotograma, pasos)


def mask_at(img, ox, oy, size=CANVAS):
    W, H = size
    m = np.zeros((H, W), bool)
    a = np.asarray(img.getchannel("A")) > 0
    x0, y0 = max(ox, 0), max(oy, 0)
    x1, y1 = min(ox + a.shape[1], W), min(oy + a.shape[0], H)
    if x1 > x0 and y1 > y0:
        m[y0:y1, x0:x1] = a[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
    return m


class Fuego:
    """Explosión con una posición común: (OX, OY) es donde cae la esquina del fotograma 0."""
    def __init__(self, fire, disc, rel):
        self.fire, self.disc, self.rel = fire, disc, rel

    def at(self, k, ox, oy):
        return ox + self.rel[k][0], oy + self.rel[k][1]

    def center(self, k, ox, oy):
        x, y = self.at(k, ox, oy)
        return x + self.fire[k].width // 2, y + self.fire[k].height // 2


def main():
    ab, _ = pj.placed(canvas=CANVAS, ground=GROUND, cx=CX)
    disc, fire = ex.raw_frames()
    _, fpos = ex.aligned(fire)
    rel = [(p[0] - fpos[0][0], p[1] - fpos[0][1]) for p in fpos]
    F = Fuego(fire, disc, rel)
    m_lying = np.asarray(ab[12].getchannel("A")) > 0      # tumbada: justo antes del cambio
    m_first = np.asarray(ab[0].getchannel("A")) > 0       # primer fotograma: justo después

    # ---- el destello (disco blanco) se centra en Abigail tumbada
    ys, xs = np.nonzero(m_lying)
    flash_c = ((xs.min() + xs.max()) // 2, (ys.min() + ys.max()) // 2)
    fl = mask_at(disc, flash_c[0] - disc.width // 2, flash_c[1] - disc.height // 2)
    u_fl = int((m_lying & ~fl).sum())
    ys, xs = np.nonzero(m_first)
    first_c = ((xs.min() + xs.max()) // 2, (ys.min() + ys.max()) // 2)

    # ---- celda del cambio y posición de la bola de fuego que mejor cubre a Abigail tumbada
    # (la llegada de su primer fotograma ya no hace falta cubrirla: sale por delante de la explosión)
    best = None
    for idx in range(8, 17):
        for oy in range(10, 110):
            for ox in range(10, 110):
                pre = mask_at(fire[idx - STEP_UP], *F.at(idx - STEP_UP, ox, oy))
                u_pre = int((m_lying & ~pre).sum())
                fx, fy = F.center(idx, ox, oy)
                key = (u_pre, abs(fx - first_c[0]) + abs(fy - first_c[1]))   # cerca de donde nace
                if best is None or key < best[0]:
                    best = (key, idx, ox, oy, u_pre)
    _, IDX, OX, OY, u_pre = best
    G = math.ceil(IDX / STEP_UP)                     # pasos de crecimiento antes del cambio
    print(f"cambio en la celda {IDX + 1} de 26, crecimiento de {G} pasos, esquina del fuego ({OX}, {OY})")
    print(f"Abigail tumbada a la vista: bajo la bola de fuego {u_pre} px | bajo el destello {u_fl} px")

    # ---- guion
    sched = []
    for k, n in FALL:
        sched += [k] * n
    L = len(sched) + HOLD_CLEAN + 1 + G
    # pausa tumbada: la melena alterna los fotogramas 12 y 13 (de 140 ms) en vez de quedarse quieta;
    # el último paso antes del destello y la bola de fuego es siempre el 13 (el que se calculó cubrir)
    for i in range(HOLD_CLEAN // 2):
        sched += [11 if i % 2 == 0 else 12] * 2
    sched += [12] * (L - len(sched))
    print(f"ciclo: {L} pasos = {L * TICK} ms")

    frames = []
    for c in range(L):
        can = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
        d = c - L if c >= L - G - 1 else c               # pasos respecto al cambio
        if d == -G - 1:                                  # destello: encima de Abigail tumbada
            can.alpha_composite(ab[sched[c]])
            can.alpha_composite(disc, (flash_c[0] - disc.width // 2, flash_c[1] - disc.height // 2))
        else:
            idx = IDX + (STEP_UP if d <= 0 else STEP_DOWN) * d
            has_fire = 0 <= idx < len(fire)
            if d < 0:                                    # crece por delante y la tapa
                can.alpha_composite(ab[sched[c]])
                if has_fire:
                    can.alpha_composite(fire[idx], F.at(idx, OX, OY))
            else:                                        # se deshace por detrás: ella sale disparada
                if has_fire:
                    can.alpha_composite(fire[idx], F.at(idx, OX, OY))
                can.alpha_composite(ab[sched[c]])
        frames.append(can)

    boxes = [f.getchannel("A").getbbox() for f in frames]
    box = (max(min(b[0] for b in boxes) - 2, 0), max(min(b[1] for b in boxes) - 2, 0),
           min(max(b[2] for b in boxes) + 2, CANVAS[0]), min(max(b[3] for b in boxes) + 2, CANVAS[1]))
    frames = [f.crop(box) for f in frames]
    print("lienzo recortado:", frames[0].size, "desde", box)

    def save_gif(imgs, path, scale):
        imgs = [i.resize((i.width * scale, i.height * scale), Image.NEAREST) if scale > 1 else i
                for i in imgs]
        colors = sorted({p[:3] for im in imgs for p in im.getdata() if p[3]})
        assert len(colors) <= 255
        index = {c: i + 1 for i, c in enumerate(colors)}
        flat = [255, 0, 255] + [v for c in colors for v in c]
        pal = []
        for im in imgs:
            p = Image.new("P", im.size, 0); p.putpalette(flat + [0] * (768 - len(flat)))
            p.putdata([index[q[:3]] if q[3] else 0 for q in im.getdata()]); pal.append(p)
        pal[0].save(path, save_all=True, append_images=pal[1:], duration=TICK, loop=0,
                    transparency=0, disposal=2, optimize=False)
        return len(colors)

    for scale, suf in ((1, ""), (4, "_x4")):
        path = HERE / f"abigail_caida{suf}.gif"
        n = save_gif(frames, path, scale)
        print(f"{path.name}: {len(frames)} pasos, {n} colores, {path.stat().st_size / 1024:.0f} KB")
    cols = 8; w, h = frames[0].size
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGBA", (w * cols, h * rows), (60, 20, 30, 255))
    for i, f in enumerate(frames):
        sheet.alpha_composite(f, ((i % cols) * w, (i // cols) * h))
    sheet.save(Path("/projects/sandbox/tmp") / "abigail_hoja.png")


if __name__ == "__main__":
    main()
