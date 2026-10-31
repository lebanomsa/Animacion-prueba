"""Secuencia completa de Matilda con dos bombas de humo (GIF transparente en bucle).

Ciclo de 39 pasos de 70 ms (2,73 s):
  0-7    postura de arriba, el humo de la bomba 2 se disipa
  8-15   postura de arriba, limpia
  16-23  postura de arriba, el humo de la bomba 1 crece y la tapa
  24-38  movimiento del arma (humo de la bomba 1 se disipa, el de la bomba 2 crece al final)
  39=0   la bomba 2 cubre a Matilda y vuelve la postura de arriba

Cada bomba son 6 nubes del sprite a tamaño original. La nube k muestra la celda
IDX[k] + 2*(paso - paso_de_cambio) del sprite, así que todas llegan a su punto máximo
justo cuando cambia la pose. Las posiciones se buscan para que, en el paso anterior y
en el posterior al cambio, no quede a la vista ningún píxel de Matilda.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from sprites import CANVAS_H, CANVAS_W, M_BASE, M_X, matilda_frames, smoke_frames  # noqa: E402

HERE = Path(__file__).parent
OUT = HERE / "salida"
OUT.mkdir(exist_ok=True)

TICK = 70          # ms por paso
CYCLE = 39
STEP = 2           # celdas de humo que avanza cada paso mientras crece
STEP_POST = 4      # y mientras se disipa: más rápido, para dejar ver el movimiento
IDX = [13, 12, 11, 10, 9, 8]    # celda del humo de cada nube en el instante del cambio
TS1, TS2 = 24, 0                # paso del cambio de pose de cada bomba

# Postura de Matilda en cada paso: ("T", i) arriba, ("B", i) abajo
SCHEDULE = []
for _ in range(3):
    for i in range(4):
        SCHEDULE += [("T", i)] * 2
for i, n in enumerate([2, 2, 2, 1, 2, 6]):
    SCHEDULE += [("B", i)] * n
assert len(SCHEDULE) == CYCLE


def delta(c, ts):
    """Pasos respecto al cambio, en el rango [-19, 19] (el ciclo es circular)."""
    return ((c - ts + CYCLE + 19) % CYCLE) - 19


def cell_index(k, c, ts):
    d = delta(c, ts)
    return IDX[k] + (STEP if d <= 0 else STEP_POST) * d


# ------------------------------------------------------------------ búsqueda de posiciones
def mask_in_canvas(alpha, ox, oy):
    m = np.zeros((CANVAS_H, CANVAS_W), bool)
    x0, y0 = max(ox, 0), max(oy, 0)
    x1, y1 = min(ox + alpha.shape[1], CANVAS_W), min(oy + alpha.shape[0], CANVAS_H)
    if x1 > x0 and y1 > y0:
        m[y0:y1, x0:x1] = alpha[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
    return m


def optimize(ts, pre_pose, post_pose, smoke, pose_masks, rounds=4):
    """Coloca las 6 nubes minimizando los píxeles de Matilda que quedan a la vista."""
    alpha = [np.asarray(s.getchannel("A")) > 0 for s in smoke]
    bbox = [s.getchannel("A").getbbox() for s in smoke]
    m_pre, m_post = pose_masks[pre_pose], pose_masks[post_pose]
    pre_c, post_c = (ts - 1) % CYCLE, ts % CYCLE
    # celda que muestra cada nube justo antes y justo después del cambio
    cells = [(cell_index(k, pre_c, ts), cell_index(k, post_c, ts)) for k in range(6)]
    pos = [None] * 6

    def covers(k, p):
        a, b = cells[k]
        return (mask_in_canvas(alpha[a], *p), mask_in_canvas(alpha[b], *p))

    def unc(cov_pre, cov_post):
        return int((m_pre & ~cov_pre).sum()) + int((m_post & ~cov_post).sum())

    for rnd in range(rounds):
        for k in range(6):
            cp = np.zeros_like(m_pre); cq = np.zeros_like(m_post)
            for j in range(6):
                if j != k and pos[j] is not None:
                    a, b = covers(j, pos[j]); cp |= a; cq |= b
            u_pre, u_post = m_pre & ~cp, m_post & ~cq
            a_idx, b_idx = cells[k]
            bb = bbox[a_idx]
            best = None
            step = 2 if rnd == 0 else 1
            cand = [(ox, oy) for oy in range(-bb[1] - 6, CANVAS_H - bb[3], step)
                    for ox in range(-bb[0] - 12, CANVAS_W - bb[2] + 12, step)]
            if pos[k] is not None and rnd > 0:      # refinar alrededor de la posición actual
                px, py = pos[k]
                cand = [(px + dx, py + dy) for dy in range(-3, 4) for dx in range(-3, 4)]
            for ox, oy in cand:
                if oy + bbox[a_idx][3] > CANVAS_H - 1 or oy + bbox[b_idx][3] > CANVAS_H - 1:
                    continue
                ma = mask_in_canvas(alpha[a_idx], ox, oy)
                mb = mask_in_canvas(alpha[b_idx], ox, oy)
                s = int((u_pre & ~ma).sum()) + int((u_post & ~mb).sum())
                if best is None or s < best[0]:
                    best = (s, ox, oy)
            pos[k] = (best[1], best[2])
        cp = np.zeros_like(m_pre); cq = np.zeros_like(m_post)
        for j in range(6):
            a, b = covers(j, pos[j]); cp |= a; cq |= b
        print(f"  ronda {rnd + 1}: a la vista antes {int((m_pre & ~cp).sum())} px, "
              f"después {int((m_post & ~cq).sum())} px")
    return pos


# ------------------------------------------------------------------ composición
def build_frames(top, bot, smoke, bombs):
    frames = []
    for c in range(CYCLE):
        kind, i = SCHEDULE[c]
        mat = (top if kind == "T" else bot)[i]
        can = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        can.alpha_composite(mat, (M_X, M_BASE - mat.height))
        for ts, pos in bombs:
            for k in range(6):
                idx = cell_index(k, c, ts)
                if 0 <= idx < len(smoke):
                    ox, oy = pos[k]
                    layer = Image.new("RGBA", can.size, (0, 0, 0, 0))
                    layer.paste(smoke[idx], (ox, oy))
                    can.alpha_composite(layer)
        frames.append(can)
    return frames


def crop_all(frames, pad=2):
    boxes = [f.getchannel("A").getbbox() for f in frames]
    x0 = max(min(b[0] for b in boxes) - pad, 0); y0 = max(min(b[1] for b in boxes) - pad, 0)
    x1 = min(max(b[2] for b in boxes) + pad, CANVAS_W); y1 = min(max(b[3] for b in boxes) + pad, CANVAS_H)
    return [f.crop((x0, y0, x1, y1)) for f in frames], (x0, y0, x1, y1)


def save_gif(frames, path, scale=1):
    imgs = [f.resize((f.width * scale, f.height * scale), Image.NEAREST) if scale > 1 else f
            for f in frames]
    colors = sorted({c[:3] for im in imgs for c in im.getdata() if c[3]})
    assert len(colors) <= 255, len(colors)
    index = {c: i + 1 for i, c in enumerate(colors)}
    flat = [255, 0, 255] + [v for c in colors for v in c]
    pal = []
    for im in imgs:
        p = Image.new("P", im.size, 0)
        p.putpalette(flat + [0] * (768 - len(flat)))
        p.putdata([index[c[:3]] if c[3] else 0 for c in im.getdata()])
        pal.append(p)
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=TICK, loop=0,
                transparency=0, disposal=2, optimize=False)
    return len(colors)


def main():
    top, bot = matilda_frames()
    smoke = smoke_frames()
    pose_masks = {("T", i): np.asarray(Image.new("RGBA", (CANVAS_W, CANVAS_H)).convert("RGBA")
                                       .getchannel("A")) > 0 for i in range(0)}
    for kind, frs in (("T", top), ("B", bot)):
        for i, f in enumerate(frs):
            can = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
            can.alpha_composite(f, (M_X, M_BASE - f.height))
            pose_masks[(kind, i)] = np.asarray(can.getchannel("A")) > 0

    cache = HERE / "nubes.json"
    if cache.exists():
        bombs = json.loads(cache.read_text())
        print("posiciones de las nubes leídas de nubes.json")
    else:
        print("bomba 1 (arriba -> abajo):")
        p1 = optimize(TS1, ("T", 3), ("B", 0), smoke, pose_masks)
        print("bomba 2 (abajo -> arriba):")
        p2 = optimize(TS2, ("B", 5), ("T", 0), smoke, pose_masks)
        bombs = [[TS1, p1], [TS2, p2]]
        cache.write_text(json.dumps(bombs))

    frames = build_frames(top, bot, smoke, bombs)
    frames, box = crop_all(frames)
    print("lienzo recortado:", frames[0].size, "desde", box)
    for scale, suf in ((1, ""), (4, "_x4")):
        path = OUT / f"matilda_bombas{suf}.gif"
        n = save_gif(frames, path, scale)
        print(f"{path.name}: {len(frames)} fotogramas, {n} colores, {path.stat().st_size / 1024:.0f} KB")
    # hoja de revisión (no se versiona)
    cols = 6; w, h = frames[0].size
    sheet = Image.new("RGBA", (w * cols, h * ((len(frames) + cols - 1) // cols)), (60, 20, 30, 255))
    for i, f in enumerate(frames):
        sheet.alpha_composite(f, ((i % cols) * w, (i // cols) * h))
    sheet.save(Path("/projects/sandbox/tmp") / "bombas_hoja.png")


if __name__ == "__main__":
    main()
