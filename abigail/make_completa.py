"""Animación completa de Abigail: [camina] -> [gestos] -> explosión -> caída (con la gorra volando) -> tumbada -> reinicio.

Escala: todo a la escala grande de los fotogramas de pie, de caminar y de la gorra. La caída ('abigail 1/2')
y la explosión ('bomba abigail 1/2'), dibujadas a la mitad de resolución, se amplían x2 (vecino más cercano).

Variantes (python make_completa.py [caminar|parpadeo|explosiones]):
  caminar      (la última) camina 2 ciclos ('abigail 5'), hace los 4 gestos una vez ('abigail 3'), la golpea la
               explosión, cae, queda tumbada y parpadea con destellos (contorno doble y brillos) hasta deshacerse; vuelve a caminar.
  parpadeo     de pie 4 pasadas de gestos; el reinicio es un parpadeo visible/invisible.
  explosiones  de pie 2 pasadas de gestos; el reinicio lo tapa una segunda explosión.

Pasos de 70 ms. Ciclo de la variante 'caminar' (TS1 es el paso del golpe):
  0..19       camina (10 fotogramas x 2 ciclos, 1 paso cada uno), en el sitio
  20..31      gestos 1-4 una sola vez, 3 pasos (210 ms) cada uno
  32..37      el gesto 4 queda quieto: destello (disco blanco) y la bola de fuego crece y la tapa
  38 (= TS1)  cambio: pasa a su primer fotograma de caída y la gorra sale volando
  38..55      caída (fotogramas 1-13); la gorra describe un arco y aterriza
  56..63      tumbada (la melena alterna dos fotogramas)
  64..71      parpadeo de destello (8 pasos): normal, destello, normal, destello, normal, destello, y dos pasos solo con
              brillos que se apagan; al paso 0 vuelve a caminar
La bomba son bolas de fuego del sprite que llegan a su celda IDX[k] justo en el cambio
(crecen 2 celdas por paso y se deshacen 3). Salida: <nombre>.gif y <nombre>_x2.gif, transparentes y en bucle.
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import brillos              # noqa: E402
import explosion as ex      # noqa: E402
import personaje as pj      # noqa: E402

TICK = 70
BW, BH = 200, 180           # lienzo
G = 164                     # fila del suelo (la fila inferior de Abigail tumbada)
CX = 96                     # columna central de Abigail
STEP_UP, STEP_DOWN = 2, 3
FALL = [(0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1),
        (8, 2), (9, 2), (10, 2), (11, 2), (12, 2)]
HOLD = 8                    # pasos tumbada (con la melena alternando) antes del reinicio
CAP_T, CAP_APEX, CAP_DX = 11, 40, 66      # vuelo de la gorra: pasos, altura del arco y avance
IDX1, IDX2 = [11], [12, 9]  # celda de cada bola de fuego en el cambio (bomba 1 y bomba 2)
BLINK = [True, False, True, False]        # variante 'parpadeo': visible / invisible en cada paso
FLASH = ["n", "w", "n", "w", "n", "w", "s", "s"]  # variante 'caminar': normal/destello x3, y dos pasos solo con brillos
WALK_UP = 50                # filas superiores (gorra, cara, torso) con las que se alinea el caminar

VARIANTS = {
    "explosiones": dict(passes=2, gest=2, final="explosion", out="abigail_completa"),
    "parpadeo": dict(passes=4, gest=2, final="parpadeo", out="abigail_completa_parpadeo"),
    "caminar": dict(walk_cycles=2, gest=3, final="flash", out="abigail_completa_caminar"),
}


def mask_at(img, ox, oy):
    m = np.zeros((BH, BW), bool)
    a = np.asarray(img.getchannel("A")) > 0
    x0, y0 = max(ox, 0), max(oy, 0)
    x1, y1 = min(ox + a.shape[1], BW), min(oy + a.shape[0], BH)
    if x1 > x0 and y1 > y0:
        m[y0:y1, x0:x1] = a[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
    return m


def up2(img):
    return img.resize((img.width * 2, img.height * 2), Image.NEAREST)


def whiten(img):
    """Silueta blanca de una imagen RGBA (todos los píxeles opacos pasan al blanco del sprite)."""
    a = np.asarray(img).copy()
    a[a[..., 3] > 0] = (248, 248, 248, 255)
    return Image.fromarray(a, "RGBA")


def load_walk():
    """10 fotogramas de caminar ('abigail 5'), en el sitio: apoyados en el suelo y alineados por la
    parte superior (gorra, cara y torso) con el primer fotograma para que no se desplace la cabeza."""
    fr = pj._cut("abigail 5.PNG")
    assert len(fr) == 10, len(fr)
    ref = np.asarray(fr[0].getchannel("A"))[:WALK_UP] > 0
    top_ys, top_xs = np.nonzero(ref[:6])
    x_ref = CX - int(np.median(top_xs))                        # esquina del fotograma 1
    out, offsets = [], []
    for f in fr:
        a = np.asarray(f.getchannel("A"))[:WALK_UP] > 0
        best = None
        for dx in range(-12, 13):
            m = np.zeros((WALK_UP, 140), bool)
            r = np.zeros((WALK_UP, 140), bool)
            r[:, 30:30 + ref.shape[1]] = ref
            m[:, 30 + dx:30 + dx + a.shape[1]] = a if 30 + dx >= 0 else a
            score = (m & r).sum() / (m | r).sum() - 0.002 * abs(dx)
            if best is None or score > best[0]:
                best = (score, dx)
        dx = best[1]
        can = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
        can.alpha_composite(f, (x_ref + dx, G + 2 - f.height))
        out.append(can); offsets.append(dx)
    return out, offsets


def load_all():
    # ---- de pie: se alinean por los pies (centro de las 8 filas inferiores) y descansan sobre el suelo
    stand = []
    for f in pj.standing():
        a = np.asarray(f.getchannel("A")) > 0
        ys, xs = np.nonzero(a[-8:])
        ax = int(np.median(xs))
        can = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
        can.alpha_composite(f, (CX - ax, G + 2 - f.height))
        stand.append(can)
    walk, _ = load_walk()
    # ---- caída: se coloca en el lienzo pequeño (la mitad) y se amplía x2 entero
    small, _ = pj.placed(canvas=(BW // 2, BH // 2), ground=G // 2, cx=CX // 2)
    fall = [up2(c) for c in small]
    # ---- explosión x2 con posiciones relativas al fotograma 0
    disc, fire = ex.raw_frames()
    _, fpos = ex.aligned(fire)
    rel = [((p[0] - fpos[0][0]) * 2, (p[1] - fpos[0][1]) * 2) for p in fpos]
    return stand, walk, fall, up2(disc), [up2(f) for f in fire], rel, [c for c in pj.cap()]


class Fuego:
    def __init__(self, fire, rel):
        self.fire, self.rel = fire, rel

    def at(self, k, ox, oy):
        return ox + self.rel[k][0], oy + self.rel[k][1]


def optimize(F, idxs, pre_mask, post_mask, rounds=3):
    """Coloca las bolas de fuego (esquina del fotograma 0) para que en el paso anterior (celda idx-2) tapen
    pre_mask y, si hay post_mask, que en el cambio (celda idx) tapen también post_mask."""
    n = len(idxs)
    ubb = (min(f.getchannel("A").getbbox()[0] + r[0] for f, r in zip(F.fire, F.rel)),
           min(f.getchannel("A").getbbox()[1] + r[1] for f, r in zip(F.fire, F.rel)),
           max(f.getchannel("A").getbbox()[2] + r[0] for f, r in zip(F.fire, F.rel)),
           max(f.getchannel("A").getbbox()[3] + r[1] for f, r in zip(F.fire, F.rel)))
    lo_x, hi_x, lo_y, hi_y = -ubb[0], BW - ubb[2], -ubb[1], BH - ubb[3]
    pos = [None] * n

    def cov(k, p):
        a = mask_at(F.fire[idxs[k] - STEP_UP], *F.at(idxs[k] - STEP_UP, *p))
        b = mask_at(F.fire[idxs[k]], *F.at(idxs[k], *p)) if post_mask is not None else None
        return a, b

    def score(cp, cq):
        s = int((pre_mask & ~cp).sum())
        if post_mask is not None:
            s += int((post_mask & ~cq).sum())
        return s

    for rnd in range(rounds):
        for k in range(n):
            cp = np.zeros((BH, BW), bool); cq = np.zeros((BH, BW), bool)
            for j in range(n):
                if j != k and pos[j] is not None:
                    a, b = cov(j, pos[j]); cp |= a
                    if b is not None:
                        cq |= b
            if pos[k] is not None and rnd > 0:
                px, py = pos[k]
                cand = [(px + dx, py + dy) for dy in range(-3, 4) for dx in range(-3, 4)
                        if lo_x <= px + dx <= hi_x and lo_y <= py + dy <= hi_y]
            else:
                cand = [(x, y) for y in range(lo_y, hi_y + 1, 2) for x in range(lo_x, hi_x + 1, 2)]
            best = None
            for p in cand:
                a, b = cov(k, p)
                s = score(cp | a, cq | b if b is not None else cq)
                if best is None or s < best[0]:
                    best = (s, p)
            pos[k] = best[1]
    cp = np.zeros((BH, BW), bool); cq = np.zeros((BH, BW), bool)
    for k in range(n):
        a, b = cov(k, pos[k]); cp |= a
        if b is not None:
            cq |= b
    return pos, int((pre_mask & ~cp).sum()), (int((post_mask & ~cq).sum()) if post_mask is not None else None)


def main(variant="caminar"):
    cfg = VARIANTS[variant]
    final = cfg["final"]
    stand, walk, fall, disc, fire, rel, capf = load_all()
    F = Fuego(fire, rel)
    G1 = max(IDX1) // STEP_UP
    G2 = max(IDX2) // STEP_UP

    # ---- guion de Abigail (antes del golpe)
    if final == "flash":
        sched = [("W", i % 10) for i in range(10 * cfg["walk_cycles"])]
        for i in range(4):
            sched += [("S", i)] * cfg["gest"]
        sched += [("S", 3)] * (G1 + 1)                      # el último gesto queda quieto bajo el destello y el fuego
    else:
        sched = [("S", i // cfg["gest"] % 4) for i in range(4 * cfg["passes"] * cfg["gest"])]
    TS1 = len(sched)
    for k, n in FALL:
        sched += [("F", k)] * n
    tail = {"explosion": 1 + G2, "parpadeo": len(BLINK), "flash": len(FLASH)}[final]
    L = len(sched) + HOLD + tail
    for i in range(HOLD // 2):
        sched += [("F", 11 if i % 2 == 0 else 12)] * 2
    sched += [("F", 12)] * (L - len(sched))
    walk_end = 10 * cfg.get("walk_cycles", 0)
    print(f"[{variant}] ciclo: {L} pasos = {L * TICK} ms | antes del golpe {TS1} pasos ({TS1 * TICK} ms)"
          f"{f' | camina {walk_end} pasos' if walk_end else ''} | bomba 1: crecimiento de {G1} pasos")

    # ---- gorra: arco desde la cabeza hasta el suelo
    pre_src = {"S": stand, "W": walk}[sched[TS1 - 1][0]][sched[TS1 - 1][1]]
    last_stand = np.asarray(pre_src.getchannel("A")) > 0
    ys, xs = np.nonzero(last_stand)
    top = ys.min(); head = xs[ys <= top + 8]
    sx, sy = float(head.mean()), float(top + 8)                     # centro de la gorra sobre la cabeza
    ex_, ey = sx + CAP_DX, G + 2 - capf[8].height / 2.0              # centro al aterrizar
    drop = ey - sy
    T = CAP_T                                                        # y(t) = sy - v0 t + g t^2 / 2, y(T) = ey
    s = (math.sqrt(2 * CAP_APEX) + math.sqrt(2 * CAP_APEX + 2 * drop)) / T
    g = s * s; v0 = math.sqrt(2 * g * CAP_APEX)
    cap_pos = [(sx + CAP_DX * t / T, sy - v0 * t + 0.5 * g * t * t) for t in range(CAP_T + 1)]
    cap_pos[-1] = (ex_, ey)
    cap_frame = [min(8, t * 9 // (CAP_T + 1)) for t in range(CAP_T + 1)]
    cap_frame[-1] = 8

    def cap_at(c):
        if c < TS1:
            return None
        t = min(c - TS1, CAP_T)
        f = capf[cap_frame[t]]; x, y = cap_pos[t]
        can = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
        can.alpha_composite(f, (int(round(x - f.width / 2)), int(round(y - f.height / 2))))
        return can

    # ---- brillos del parpadeo final, repartidos alrededor de Abigail tumbada y la gorra
    sparks = []
    if final == "flash":
        scene_mask = (np.asarray(fall[12].getchannel("A")) > 0) | (np.asarray(cap_at(TS1 + CAP_T).getchannel("A")) > 0)
        sparks = brillos.sparkle_points(scene_mask)

    # ---- bomba 1 (el golpe): cubre a Abigail justo antes del cambio
    p1, a1, _ = optimize(F, IDX1, last_stand, None)
    print(f"bomba 1: a la vista antes del cambio {a1} px | posiciones {p1}")
    bombs = [(TS1, G1, IDX1, p1, (CX, G - 44))]
    if final == "explosion":                                          # bomba 2: tapa el reinicio
        lying = np.asarray(fall[12].getchannel("A")) > 0
        capm = np.asarray(cap_at(L - 1).getchannel("A")) > 0
        m_pre = lying | capm
        m_post = np.asarray(stand[sched[0][1]].getchannel("A")) > 0
        p2, a2, b2 = optimize(F, IDX2, m_pre, m_post)
        print(f"bomba 2: a la vista antes {a2} px | después {b2} px | posiciones {p2}")
        ys, xs = np.nonzero(m_pre)
        fl2 = ((xs.min() + xs.max()) // 2, min((ys.min() + ys.max()) // 2, BH - disc.height // 2))
        bombs.append((0, G2, IDX2, p2, fl2))

    def fire_layers(c):
        """[(imagen, esquina, delante?)] de las bolas de fuego visibles en el paso c."""
        out = []
        for ts, Gk, idxs, pos, fl in bombs:
            d = (c - ts) if ts else (c if c < L // 2 else c - L)
            if d == -Gk - 1:
                out.append((disc, (fl[0] - disc.width // 2, fl[1] - disc.height // 2), True)); continue
            for k, idx0 in enumerate(idxs):
                idx = idx0 + (STEP_UP if d <= 0 else STEP_DOWN) * d
                if 0 <= idx < len(fire):
                    out.append((fire[idx], F.at(idx, *pos[k]), d <= 0))
        return out

    sources = {"S": stand, "W": walk, "F": fall}
    frames = []
    for c in range(L):
        kind, i = sched[c]
        ab = sources[kind][i]
        can = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
        cap_img = cap_at(c)
        if final == "parpadeo" and c >= L - len(BLINK) and not BLINK[c - (L - len(BLINK))]:
            frames.append(can); continue                              # este paso no se ve nada
        if final == "flash" and c >= L - len(FLASH):
            t = c - (L - len(FLASH))
            mode = FLASH[t]
            if mode in ("n", "w"):                                    # Abigail y la gorra: normales o en destello
                can.alpha_composite(ab if mode == "n" else brillos.flash(ab, 4))
                can.alpha_composite(cap_img if mode == "n" else brillos.flash(cap_img, 4))
            brillos.sparkles_at(can, sparks, t)                       # brillos en cruz; con el último destello se deshace en brillos
            frames.append(can); continue
        layers = fire_layers(c)
        behind = [l for l in layers if not l[2]]
        front = [l for l in layers if l[2]]
        if c >= TS1:
            for img, p, _ in behind:
                can.alpha_composite(img, p)
            can.alpha_composite(ab)
            if cap_img is not None:
                can.alpha_composite(cap_img)
            for img, p, _ in front:
                can.alpha_composite(img, p)
        else:
            can.alpha_composite(ab)
            for img, p, _ in layers:
                can.alpha_composite(img, p)
        frames.append(can)

    boxes = [b for b in (f.getchannel("A").getbbox() for f in frames) if b]
    box = (max(min(b[0] for b in boxes) - 2, 0), max(min(b[1] for b in boxes) - 2, 0),
           min(max(b[2] for b in boxes) + 2, BW), min(max(b[3] for b in boxes) + 2, BH))
    frames = [f.crop(box) for f in frames]
    print("lienzo recortado:", frames[0].size, "desde", box)

    def save_gif(imgs, path, scale):
        imgs = [i.resize((i.width * scale, i.height * scale), Image.NEAREST) if scale > 1 else i
                for i in imgs]
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
        path = HERE / f"{cfg['out']}{suf}.gif"
        n = save_gif(frames, path, scale)
        print(f"{path.name}: {len(frames)} pasos, {n} colores, {path.stat().st_size / 1024:.0f} KB")
    cols = 10; w, h = frames[0].size
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGBA", (w * cols, h * rows), (60, 20, 30, 255))
    for i, f in enumerate(frames):
        sheet.alpha_composite(f, ((i % cols) * w, (i // cols) * h))
    sheet.save(Path("/projects/sandbox/tmp") / f"abigail_{variant}_hoja.png")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "caminar")
