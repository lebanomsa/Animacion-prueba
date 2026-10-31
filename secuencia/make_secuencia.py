"""Secuencias de Matilda con dos bombas de humo (GIF transparente en bucle).

Cada paso dura 70 ms. El ciclo es:
  pasos 0-23   postura de arriba, 3 pasadas (la primera con el humo de la bomba 2 disipándose,
               la última con el humo de la bomba 1 creciendo y tapándola)
  paso 24      cambio de pose bajo la bomba 1
  pasos 24-fin movimiento del arma (el humo de la bomba 1 se disipa y, al final, crece el de la 2)
  paso fin=0   cambio de pose bajo la bomba 2 y vuelve la postura de arriba

Variantes del movimiento del arma:
  A  repetición  - el movimiento se repite 3 veces, de ida y vuelta, y acaba en la última pose
  B  misma duración - un solo recorrido estirado a 24 pasos (1680 ms), igual que la postura de arriba
  0  original    - un solo recorrido de 15 pasos (1050 ms)

Cada bomba son 6 nubes del sprite a tamaño original. La nube k muestra la celda del sprite
IDX[k] + paso_de_humo*(paso - paso_de_cambio), así que todas están al máximo justo en el cambio.
Las posiciones (nubes.json) se buscan una vez para que en el paso anterior y en el posterior
al cambio no quede a la vista ningún píxel de Matilda.
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
STEP = 2           # celdas de humo que avanza cada paso mientras crece
STEP_POST = 4      # y mientras se disipa (más rápido, para dejar ver el movimiento)
IDX = [13, 12, 11, 10, 9, 8]    # celda del humo de cada nube en el instante del cambio
TS1, TS2 = 24, 0                # paso del cambio de pose de cada bomba

# Visitas (pose, pasos) del movimiento del arma para cada variante. Poses B1..B6 = 0..5.
FORWARD = [(0, 2), (1, 2), (2, 2), (3, 1), (4, 2)]
ORIGINAL = FORWARD + [(5, 6)]
# A: B1..B6, vuelta B5..B2, B1, B2..B6, vuelta B5..B2, B1, B2..B6 (la última pose se queda 6 pasos)
_up = lambda a, b: [(p, d) for p, d in (FORWARD + [(5, 2)]) if a <= p <= b]
_down = [(4, 2), (3, 1), (2, 2), (1, 2)]
REPETIDO = (_up(0, 5) + _down + [(0, 2)] + _up(1, 5) + _down + [(0, 2)] + _up(1, 4) + [(5, 6)])
# B: el mismo recorrido, con el arco rápido igual y las dos últimas poses estiradas a 24 pasos
ESTIRADO = [(0, 2), (1, 2), (2, 2), (3, 1), (4, 5), (5, 12)]

VARIANTS = {
    "original": ORIGINAL,
    "A_repeticion": REPETIDO,
    "B_misma_duracion": ESTIRADO,
}


def make_schedule(swing):
    sched = []
    for _ in range(3):
        for i in range(4):
            sched += [("T", i)] * 2
    assert len(sched) == TS1
    for pose, n in swing:
        sched += [("B", pose)] * n
    return sched


def delta(c, ts, cycle):
    """Pasos respecto al cambio, en el rango [-19, cycle-20] (el ciclo es circular)."""
    return ((c - ts + cycle + 19) % cycle) - 19


def cell_index(k, c, ts, cycle):
    d = delta(c, ts, cycle)
    return IDX[k] + (STEP if d <= 0 else STEP_POST) * d


# ------------------------------------------------------------------ búsqueda de posiciones
def mask_in_canvas(alpha, ox, oy):
    m = np.zeros((CANVAS_H, CANVAS_W), bool)
    x0, y0 = max(ox, 0), max(oy, 0)
    x1, y1 = min(ox + alpha.shape[1], CANVAS_W), min(oy + alpha.shape[0], CANVAS_H)
    if x1 > x0 and y1 > y0:
        m[y0:y1, x0:x1] = alpha[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
    return m


def optimize(ts, pre_pose, post_pose, smoke, pose_masks, cycle, rounds=4):
    """Coloca las 6 nubes minimizando los píxeles de Matilda que quedan a la vista."""
    alpha = [np.asarray(s.getchannel("A")) > 0 for s in smoke]
    bbox = [s.getchannel("A").getbbox() for s in smoke]
    m_pre, m_post = pose_masks[pre_pose], pose_masks[post_pose]
    pre_c, post_c = (ts - 1) % cycle, ts % cycle
    cells = [(cell_index(k, pre_c, ts, cycle), cell_index(k, post_c, ts, cycle)) for k in range(6)]
    pos = [None] * 6

    def covers(k, p):
        a, b = cells[k]
        return mask_in_canvas(alpha[a], *p), mask_in_canvas(alpha[b], *p)

    for rnd in range(rounds):
        for k in range(6):
            cp = np.zeros_like(m_pre); cq = np.zeros_like(m_post)
            for j in range(6):
                if j != k and pos[j] is not None:
                    a, b = covers(j, pos[j]); cp |= a; cq |= b
            u_pre, u_post = m_pre & ~cp, m_post & ~cq
            a_idx, b_idx = cells[k]
            bb = bbox[a_idx]
            step = 2 if rnd == 0 else 1
            cand = [(ox, oy) for oy in range(-bb[1] - 6, CANVAS_H - bb[3], step)
                    for ox in range(-bb[0] - 12, CANVAS_W - bb[2] + 12, step)]
            if pos[k] is not None and rnd > 0:
                px, py = pos[k]
                cand = [(px + dx, py + dy) for dy in range(-3, 4) for dx in range(-3, 4)]
            best = None
            for ox, oy in cand:
                if oy + bbox[a_idx][3] > CANVAS_H - 1 or oy + bbox[b_idx][3] > CANVAS_H - 1:
                    continue
                s = (int((u_pre & ~mask_in_canvas(alpha[a_idx], ox, oy)).sum())
                     + int((u_post & ~mask_in_canvas(alpha[b_idx], ox, oy)).sum()))
                if best is None or s < best[0]:
                    best = (s, ox, oy)
            pos[k] = (best[1], best[2])
    return pos


# ------------------------------------------------------------------ composición
def smoke_layer(smoke, bombs, c, cycle):
    layer = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    for ts, pos in bombs:
        for k in range(6):
            idx = cell_index(k, c, ts, cycle)
            if 0 <= idx < len(smoke):
                one = Image.new("RGBA", layer.size, (0, 0, 0, 0))
                one.paste(smoke[idx], tuple(pos[k]))
                layer.alpha_composite(one)
    return layer


def matilda_canvas(frame):
    can = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    can.alpha_composite(frame, (M_X, M_BASE - frame.height))
    return can


def build_frames(top, bot, smoke, bombs, schedule):
    cycle = len(schedule)
    frames, visible = [], []
    for c in range(cycle):
        kind, i = schedule[c]
        mat = matilda_canvas((top if kind == "T" else bot)[i])
        sm = smoke_layer(smoke, bombs, c, cycle)
        can = mat.copy(); can.alpha_composite(sm)
        frames.append(can)
        m = np.asarray(mat.getchannel("A")) > 0
        visible.append(int((m & ~(np.asarray(sm.getchannel("A")) > 0)).sum()))
    return frames, visible


def crop_all(frames, pad=2):
    boxes = [f.getchannel("A").getbbox() for f in frames]
    x0 = max(min(b[0] for b in boxes) - pad, 0); y0 = max(min(b[1] for b in boxes) - pad, 0)
    x1 = min(max(b[2] for b in boxes) + pad, CANVAS_W); y1 = min(max(b[3] for b in boxes) + pad, CANVAS_H)
    return [f.crop((x0, y0, x1, y1)) for f in frames]


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


def load_bombs(smoke, pose_masks, cycle):
    cache = HERE / "nubes.json"
    if cache.exists():
        return json.loads(cache.read_text())
    print("buscando posiciones de las nubes...")
    p1 = optimize(TS1, ("T", 3), ("B", 0), smoke, pose_masks, cycle)
    p2 = optimize(TS2, ("B", 5), ("T", 0), smoke, pose_masks, cycle)
    bombs = [[TS1, p1], [TS2, p2]]
    cache.write_text(json.dumps(bombs))
    return bombs


def main(only=None):
    top, bot = matilda_frames(); smoke = smoke_frames()
    pose_masks = {}
    for kind, frs in (("T", top), ("B", bot)):
        for i, f in enumerate(frs):
            pose_masks[(kind, i)] = np.asarray(matilda_canvas(f).getchannel("A")) > 0
    for name, swing in VARIANTS.items():
        if only and name not in only:
            continue
        sched = make_schedule(swing)
        cycle = len(sched)
        bombs = load_bombs(smoke, pose_masks, cycle)
        frames, visible = build_frames(top, bot, smoke, bombs, sched)
        # Matilda a la vista justo antes y justo después de cada cambio de pose
        chk = {f"paso {c}": visible[c] for c in (TS1 - 1, TS1, cycle - 1, 0)}
        frames = crop_all(frames)
        base = f"matilda_bombas_{name}" if name != "original" else "matilda_bombas"
        print(f"\n{name}: {cycle} pasos = {cycle * TICK} ms | a la vista en los cambios: {chk}")
        for scale, suf in ((1, ""), (4, "_x4")):
            path = OUT / f"{base}{suf}.gif"
            n = save_gif(frames, path, scale)
            print(f"  {path.name}: {n} colores, {path.stat().st_size / 1024:.0f} KB, {frames[0].size}")
        cols = 9; w, h = frames[0].size
        rows = (len(frames) + cols - 1) // cols
        sheet = Image.new("RGBA", (w * cols, h * rows), (60, 20, 30, 255))
        for i, f in enumerate(frames):
            sheet.alpha_composite(f, ((i % cols) * w, (i // cols) * h))
        sheet.save(Path("/projects/sandbox/tmp") / f"hoja_{name}.png")


if __name__ == "__main__":
    main(sys.argv[1:] or None)
