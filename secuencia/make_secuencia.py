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

# B fluido: el mismo recorrido de B, pero en vez de dejar B5 y B6 quietas se alternan
# (B5 B6 B5 B6...) a 140 ms. B5 y B6 casi no se diferencian (~1 px), así que da un balanceo sutil.
# Termina en B6, la pose para la que están calculadas las nubes de la segunda bomba.
ALTERNADO = [(0, 2), (1, 2), (2, 2), (3, 1),
             (4, 3), (5, 2), (4, 2), (5, 2), (4, 2), (5, 2), (4, 2), (5, 2)]

# B balanceo: la pausa final sigue un ciclo de respiración con 2 poses sintetizadas:
#   "Sd" = B6 con el torso 1 px más abajo, "Su" = B5 con el torso 1 px más arriba.
#   B5, B6, Sd, B6, B5, Su, B5, B6 -> el torso baja y sube suavemente y acaba en B6 original.
BALANCEO = [(0, 2), (1, 2), (2, 2), (3, 1),
            (4, 3), (5, 2), ("Sd", 2), (5, 2), (4, 2), ("Su", 2), (4, 2), (5, 2)]

VARIANTS = {
    "original": ORIGINAL,
    "A_repeticion": REPETIDO,
    "B_misma_duracion": ESTIRADO,
    "B_fluido": ALTERNADO,
    "B_balanceo": BALANCEO,
    "B_volutas": ALTERNADO,        # igual que B_fluido, más las volutas de vapor de la fila de arriba
}
VARIANTS["B_balanceo_musica"] = BALANCEO      # balanceo + explosión con nota musical
CON_VOLUTAS = {"B_volutas"}
CON_MUSICA = {"B_balanceo_musica"}
# Celda de musica.PNG (0..6) que se muestra en cada paso, a partir de HOLD_START:
#   pop (celdas 1-5, un paso cada una), oscilación (celdas 6 y 7, 140 ms) y salida inversa
#   (celdas 4..1) para que el efecto se apague antes de que llegue el humo de la segunda bomba.
MUSIC_SEQ = [0, 1, 2, 3, 4, 5, 5, 6, 6, 3, 2, 1, 0]
HOLD_START = TS1 + 7               # paso en que empieza la pausa final (tras B1..B4)

# Cortes del cuerpo en B5/B6 (filas de la celda de 134 px): cabeza y arma arriba, torso y brazos, piernas
CUT_NECK, CUT_WAIST = 83, 101


def make_schedule(swing):
    sched = []
    for _ in range(3):
        for i in range(4):
            sched += [("T", i)] * 2
    assert len(sched) == TS1
    for pose, n in swing:
        # un entero es una pose original B1..B6; un texto, una pose sintetizada (ver make_synth)
        key = ("B", pose) if isinstance(pose, int) else ("S", pose)
        sched += [key] * n
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
    ubb = (min(b[0] for b in bbox), min(b[1] for b in bbox),
           max(b[2] for b in bbox), max(b[3] for b in bbox))
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
            step = 2 if rnd == 0 else 1
            # la nube debe caber ENTERA en el lienzo en todos sus fotogramas (si no, el lienzo
            # la recorta con un borde plano); ubb es la caja que cubre las 26 celdas del humo
            lo_x, hi_x = -ubb[0], CANVAS_W - ubb[2]
            lo_y, hi_y = -ubb[1], CANVAS_H - ubb[3]
            cand = [(ox, oy) for oy in range(lo_y, hi_y + 1, step) for ox in range(lo_x, hi_x + 1, step)]
            if pos[k] is not None and rnd > 0:
                px, py = pos[k]
                cand = [(px + dx, py + dy) for dy in range(-3, 4) for dx in range(-3, 4)
                        if lo_x <= px + dx <= hi_x and lo_y <= py + dy <= hi_y]
            best = None
            for ox, oy in cand:
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


def shift_torso(frame, dy):
    """Desplaza el torso y los brazos dy px (+ abajo). La cabeza (con el arma y el pelo) y
    las piernas se quedan fijas, así que la cabeza va un paso por detrás del cuerpo.
    Se mapea fila de destino -> fila de origen, sin dejar huecos: en las costuras se
    repite o se descarta una fila."""
    a = np.asarray(frame)
    out = a.copy()
    for y in range(CUT_NECK, CUT_WAIST):
        out[y] = a[min(max(y - dy, 0), a.shape[0] - 1)]
    return Image.fromarray(out, "RGBA")


def make_synth(bot):
    return {"Sd": shift_torso(bot[5], +1), "Su": shift_torso(bot[4], -1)}


def place_puffs(top, bot, synth, hold_ticks, last_tick):
    """Coloca las volutas de la fila de arriba encima de la cabeza, sin tocar a Matilda en
    ninguna de las poses de la pausa. Devuelve {paso: (imagen, (x, y))}."""
    from sprites import puff_frames
    pf = puff_frames(top)
    sil = np.zeros((CANVAS_H, CANVAS_W), bool)
    for f in (bot[4], bot[5], synth.get("Sd", bot[5]), synth.get("Su", bot[4])):
        sil |= np.asarray(matilda_canvas(f).getchannel("A")) > 0
    pad = sil.copy()                                     # margen de 1 px alrededor de Matilda
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        pad |= np.roll(np.roll(sil, dy, 0), dx, 1)
    best = None
    for dy in range(-34, 12):
        for dx in range(-10, 30):
            ox, oy = 76 + dx, 41 + dy
            if ox < 0 or oy < 0 or ox + pf[0].width > CANVAS_W:
                continue
            if any((mask_in_canvas(np.asarray(p.getchannel("A")) > 0, ox, oy) & pad).any() for p in pf):
                continue
            key = (oy, -abs(dx))                         # lo más cerca posible de la cabeza
            if best is None or key > best[0]:
                best = (key, (ox, oy))
    ox, oy = best[1]
    print(f"  volutas colocadas en ({ox}, {oy})")
    return {c: (pf[((c - HOLD_START) // 2) % 4], (ox, oy)) for c in range(HOLD_START, last_tick + 1)}


def place_music(music, bot, synth):
    """Coloca la explosión con nota encima de la cabeza (a la derecha del arma) sin tocar a
    Matilda en ninguna de las poses de la pausa. Devuelve {paso: (imagen, (x, y))}."""
    sil = np.zeros((CANVAS_H, CANVAS_W), bool)
    for f in (bot[4], bot[5], synth["Sd"], synth["Su"]):
        sil |= np.asarray(matilda_canvas(f).getchannel("A")) > 0
    pad = sil.copy()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        pad |= np.roll(np.roll(sil, dy, 0), dx, 1)
    best = None
    # las celdas son todas del mismo tamaño y la explosión crece desde el centro, así que se
    # usa un único origen; se comprueba el fotograma más grande de la secuencia
    masks = [np.asarray(m.getchannel("A")) > 0 for m in music]
    for oy in range(0, 71):                            # solo por encima de la cabeza
        for ox in range(55, CANVAS_W - 54 + 1):        # a la derecha de la cabeza del arma
            if any((mask_in_canvas(m, ox, oy) & pad).any() for m in masks):
                continue
            head = (M_X + 63, M_BASE - 134 + 72)       # centro aproximado de la cabeza en el lienzo
            key = -((ox + 27 - head[0]) ** 2 + (oy + 27 - head[1]) ** 2)   # lo más cerca de la cabeza
            if best is None or key > best[0]:
                best = (key, (ox, oy))
    ox, oy = best[1]
    print(f"  nota musical colocada en ({ox}, {oy}) [celda de 54x54]")
    return {HOLD_START + t: (music[i], (ox, oy)) for t, i in enumerate(MUSIC_SEQ)}


def build_frames(top, bot, smoke, bombs, schedule, synth=None, puffs=None):
    cycle = len(schedule)
    frames, visible = [], []
    for c in range(cycle):
        kind, i = schedule[c]
        base = synth[i] if kind == "S" else (top if kind == "T" else bot)[i]
        mat = matilda_canvas(base)
        sm = smoke_layer(smoke, bombs, c, cycle)
        can = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        if puffs and c in puffs:
            can.alpha_composite(puffs[c][0], puffs[c][1])     # las volutas van detrás de Matilda
        can.alpha_composite(mat); can.alpha_composite(sm)
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
        synth = make_synth(bot)
        puffs = None
        if name in CON_VOLUTAS:
            puffs = place_puffs(top, bot, synth, HOLD_START, cycle - 1)
            # se cortan justo cuando el humo las tapa del todo, para que no salten a la vista
            for c in range(cycle - 12, cycle):
                img, (ox, oy) = puffs[c]
                smk = np.asarray(smoke_layer(smoke, bombs, c, cycle).getchannel("A")) > 0
                vis = (mask_in_canvas(np.asarray(img.getchannel("A")) > 0, ox, oy) & ~smk).sum()
                if vis == 0 and smk.any():
                    print(f"  volutas tapadas del todo por el humo desde el paso {c}")
                    puffs = {k: v for k, v in puffs.items() if k <= c}
                    break
            else:
                print("  aviso: las volutas no llegan a taparse del todo antes del cambio")
        if name in CON_MUSICA:
            from sprites import music_frames
            puffs = place_music(music_frames(), bot, synth)
        frames, visible = build_frames(top, bot, smoke, bombs, sched, synth, puffs)
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
