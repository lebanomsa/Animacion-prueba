"""Utena prepara y lanza un hechizo (primera versión, sobre el escenario del propio sprite).

1. Recupera el sprite original: 'utena sprite.PNG' está ampliado ~4,925x con suavizado; se toma el centro de cada celda
   -> 52x68 píxeles con 20 colores (el personaje mide 43x51).
2. Anima en una cuadrícula nativa de 63x63 y la amplía 2x -> 126x126 (y x4 -> 504x504), como 'gif referencia'.
   Todo (sprite y efectos) comparte la misma cuadrícula, sin mezclar tamaños de píxel.
3. Guion (40 pasos de 100 ms = 4 s, bucle sin salto):
     0-7   reposo: respira (torso +1 px), el rulo de la antena y las capas se mecen
     8-15  carga: la estrella brilla cada vez más, partículas se juntan en ella, nace el círculo mágico
     16-27 hechizo: Utena levita, el círculo gira con runas, suben partículas, las capas se abren
     28    destello
     29-31 estallido de estrellas
     32-39 calma: el círculo se cierra, Utena baja y vuelve al reposo
Salida: salida/utena_hechizo_126.gif, utena_hechizo_x4.gif y hojas de fotogramas.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "white_baby"))
import pesca as pe   # noqa: E402  (solo para escribir el GIF con paleta exacta)

SRC = HERE / "fuentes" / "utena_sprite.png"
OUT = HERE / "salida"
NC = 63                                   # lienzo nativo
OFX, OFY = 5, -5                          # del sprite recuperado (52x68) al lienzo: x+5, y-5
TICK, L = 100, 40

WALL, FLOOR, SHADOW = (97, 158, 155), (59, 95, 94), (29, 51, 50)
GOLD, GOLD_D, WHITE, CREAM = (255, 238, 104), (212, 179, 0), (251, 248, 253), (255, 238, 205)
LAV, LAV_D = (186, 122, 176), (95, 75, 116)
STAR_C = (45, 16)                         # centro de la estrella en el sprite recuperado
HORIZON = 48                              # fila (en el sprite recuperado) donde empieza el suelo


# ---------------------------------------------------------------- recuperación del sprite
def recuperar():
    a = np.asarray(Image.open(SRC).convert("RGB")).astype(int)
    H, W = a.shape[:2]
    dx = (np.abs(np.diff(a[45:296], axis=1)).sum(-1) > 40).sum(0).astype(float)
    dy = (np.abs(np.diff(a[:296], axis=0)).sum(-1) > 40).sum(1).astype(float)

    def fase(d, p):
        i = np.arange(len(d)); z = (d * np.exp(-2j * np.pi * i / p)).sum()
        return (np.angle(z) / (2 * np.pi)) % 1 * p
    best = None
    for p in np.arange(4.85, 4.96, 0.005):
        x0 = (fase(dx, p) + 1) % p; y0 = (fase(dy, p) + 1) % p
        xs = np.floor((np.arange(int((W - x0) / p)) + 0.5) * p + x0).astype(int)
        ys = np.floor((np.arange(int((H - y0) / p)) + 0.5) * p + y0).astype(int)
        nat = a[np.ix_(ys, xs)]
        q = len(np.unique(nat.reshape(-1, 3), axis=0))
        if best is None or q < best[0]:
            best = (q, p, nat)
    q, p, nat = best
    assert nat.shape[:2] == (68, 52) and q <= 24, (nat.shape, q)
    return nat.astype(np.uint8), p, q


# ---------------------------------------------------------------- capas base
def capas_base(nat):
    """(sprite RGBA 68x52 sin fondo ni sombra, fondo RGB 63x63 con sombra y sombra pequeña)."""
    es = lambda c: (nat == c).all(-1)
    fondo = es(WALL) | es(FLOOR) | es(SHADOW)
    spr = np.dstack([nat, (~fondo * 255).astype(np.uint8)])
    # sombra: rellenar cada fila entre su primer y último píxel de sombra (bajo los pies queda tapado por el sprite)
    sh = es(SHADOW).copy()
    for y in range(sh.shape[0]):
        xs = np.nonzero(sh[y])[0]
        if len(xs):
            sh[y, xs.min():xs.max() + 1] = True
    sh_peq = np.zeros_like(sh)
    for y in range(sh.shape[0]):
        xs = np.nonzero(sh[y])[0]
        if len(xs) > 6:
            sh_peq[y, xs.min() + 2:xs.max() - 1] = True
    ys = np.nonzero(sh_peq.any(1))[0]
    sh_peq[ys.max()] = False

    def fondo_rgb(sombra):
        bg = np.zeros((NC, NC, 3), np.uint8)
        for y in range(NC):
            bg[y] = WALL if y + 5 < HORIZON else FLOOR
        for y in range(68):
            for x in range(52):
                if sombra[y, x] and 0 <= y - 5 < NC:
                    bg[y - 5, x + 5] = SHADOW
        return bg
    return spr, fondo_rgb(sh), fondo_rgb(sh_peq)


# ---------------------------------------------------------------- transformaciones del sprite
def transformar(spr, resp, ant, f, h):
    out = spr.copy()
    if resp:                                              # respirar: el torso y la cabeza suben 1 px (se estira entre las filas 3 y 38)
        for y in range(3, 39):
            out[y] = spr[y + resp]
    o2 = out.copy()
    if ant:                                               # rulo de la antena (filas <= 12) se desplaza
        for y in range(0, 13 - resp):
            o2[y] = np.roll(out[y], ant, axis=0)
    o3 = o2.copy()
    if f:                                                 # capas: se abren f px hacia fuera (se estiran sin dejar huecos)
        for x in range(6, 16):
            o3[41:59, x] = o2[41:59, x + f]
        for x in range(37, 51):
            o3[41:59, x] = o2[41:59, x - f]
    if h:                                                 # levitar
        o4 = np.zeros_like(o3); o4[:-h] = o3[h:]; o3 = o4
    lay = np.zeros((NC, NC, 4), np.uint8)
    lay[0:NC, OFX:OFX + 52] = o3[5:68, 0:52]
    return lay


# ---------------------------------------------------------------- efectos
def px(img, x, y, col):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < NC and 0 <= y < NC:
        img[y, x] = tuple(col) + (255,) if img.shape[2] == 4 else tuple(col)


def elipse(img, cx, cy, rx, ry, col, paso=1, saltar=1):
    if rx < 1:
        return
    k = 0
    for ang in range(0, 360, paso):
        t = np.deg2rad(ang)
        if k % saltar == 0:
            px(img, cx + rx * np.cos(t), cy + ry * np.sin(t), col)
        k += 1


def estrella_rayos(img, cx, cy, L, flash):
    """Rayos de luz desde la estrella (que ya tiene 4 px de radio) y destellos diagonales."""
    for k in range(1, L + 1):
        c = WHITE if (k == L or flash) else GOLD
        for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            px(img, cx + dx * (4 + k), cy + dy * (4 + k), c)
    if L >= 3:
        for (dx, dy) in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            px(img, cx + dx * 3, cy + dy * 3, CREAM)
            if L >= 5:
                px(img, cx + dx * 4, cy + dy * 4, GOLD)


def frame(t, spr, bg, bg_peq):
    B = [0, 0, 1, 1, 1, 1, 0, 0]; A = [0, 1, 1, 1, 0, 0, 0, 0]; F = [0, 0, 0, 1, 1, 1, 0, 0]
    resp = B[t % 8]; ant = A[t % 8]
    hover = ([0] * 16 + [1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1] + [2, 2, 2, 1] + [1, 0, 0, 0, 0, 0, 0, 0])[t]
    f = (F[t % 8] if t < 16 else (1 + t % 2 if t < 32 else (1 if t < 34 else F[t % 8] * 0)))
    Ls = ([0, 0, 0, 1, 0, 0, 0, 1] + [1, 1, 2, 2, 3, 3, 4, 4] + [3, 4, 3, 4, 3, 4, 3, 4, 4, 5, 5, 6] + [8, 6, 5, 4]
          + [3, 2, 2, 1, 1, 0, 0, 0])[t]
    rx = ([0] * 12 + [3, 7, 12, 18] + [18] * 16 + [14, 10, 6, 3, 0, 0, 0, 0])[t]
    flash = (t == 28)

    base = (bg_peq if hover >= 2 else bg).astype(int)
    if flash:
        base = np.clip(base + 38, 0, 255)
    img = np.dstack([base.astype(np.uint8), np.full((NC, NC), 255, np.uint8)])

    # círculo mágico en el suelo (detrás de los pies)
    ccx, ccy = 32, 51
    if rx:
        ry = max(1, round(rx * 0.28))
        elipse(img, ccx, ccy, rx, ry, LAV)
        if rx >= 8:
            elipse(img, ccx, ccy, round(rx * 0.62), max(1, round(rx * 0.62 * 0.28)), GOLD_D, saltar=3)
        for k in range(8):                                # runas que giran
            ang = np.deg2rad(15 * t + 45 * k)
            col = GOLD if k % 2 == 0 else WHITE
            px(img, ccx + rx * np.cos(ang), ccy + ry * np.sin(ang), col)
            if rx >= 12:
                px(img, ccx + rx * np.cos(ang), ccy + ry * np.sin(ang) - 1, col)

    # sprite
    lay = transformar(spr, resp, ant, f, hover)
    a = lay[..., 3] > 0
    img[a] = np.dstack([lay[..., :3], lay[..., 3]])[a]

    cx, cy = STAR_C[0] + OFX, STAR_C[1] - resp - hover + OFY
    # estrella: brillo y rayos
    if flash:
        for (dx, dy) in [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (2, 0), (-2, 0), (0, 2), (0, -2)]:
            px(img, cx + dx, cy + dy, WHITE)
    if Ls:
        estrella_rayos(img, cx, cy, Ls, flash)

    # partículas que se juntan en la estrella (8-15)
    if 8 <= t <= 15:
        rs = np.random.RandomState(4)
        for i in range(10):
            ang = rs.rand() * 2 * np.pi
            r0 = 14 + 6 * rs.rand()
            r = r0 * (1 - (t - 8) / 8.0)
            if r < 2:
                continue
            x, y = cx + r * np.cos(ang), cy + r * np.sin(ang) * 0.8
            px(img, x, y, GOLD if i % 2 == 0 else WHITE)
            px(img, cx + (r + 2) * np.cos(ang), cy + (r + 2) * np.sin(ang) * 0.8, LAV)

    # partículas que suben del círculo (spawn 16-29, vida 9)
    for s in range(16, 30):
        if not (s <= t < s + 9):
            continue
        rs = np.random.RandomState(100 + s)
        for i in range(5):
            ang = rs.rand() * 2 * np.pi
            ph = rs.rand() * 6
            rr = 16 * (0.5 + 0.5 * rs.rand())
            age = t - s
            x = ccx + rr * np.cos(ang) + 1.5 * np.sin(age * 0.9 + ph)
            y = ccy + rr * 0.28 * np.sin(ang) - age * 1.4
            if i % 2 == 0 and 2 <= age <= 6:                  # pequeña estrella de 5 px
                px(img, x, y, GOLD if age < 5 else CREAM)
                for (ddx, ddy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    px(img, x + ddx, y + ddy, WHITE if age < 5 else LAV)
            else:
                px(img, x, y, WHITE if age < 3 else GOLD if age < 6 else LAV)

    # estallido de estrellas (29-31)
    if 29 <= t <= 31:
        j = t - 28
        for k, (dx, dy) in enumerate(((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1))):
            n = 1.0 if dx == 0 or dy == 0 else 0.72
            r = (5 + 5 * j) * n
            col = GOLD if j == 1 else (CREAM if j == 2 else LAV)
            for q in (0, 1, 2):
                px(img, cx + dx * (r + q * n), cy + dy * (r + q * n), col)
            if j <= 2:
                px(img, cx + dx * (r + 3 * n), cy + dy * (r + 3 * n), WHITE)
    return img[..., :3]


def main():
    OUT.mkdir(exist_ok=True)
    nat, p, q = recuperar()
    print(f"sprite recuperado: período {p:.3f}, {nat.shape[1]}x{nat.shape[0]} px, {q} colores")
    Image.fromarray(nat).save(HERE / "sprite_recuperado_52x68.png")
    spr, bg, bg_peq = capas_base(nat)
    fr = [Image.fromarray(frame(t, spr, bg, bg_peq), "RGB") for t in range(L)]
    f126 = [f.resize((126, 126), Image.NEAREST) for f in fr]
    f504 = [f.resize((504, 504), Image.NEAREST) for f in f126]
    n = pe.gif_opaco(f126, OUT / "utena_hechizo_126.gif", TICK)
    pe.gif_opaco(f504, OUT / "utena_hechizo_x4.gif", TICK)
    print(f"{L} pasos = {L * TICK / 1000:.1f} s; {n} colores")
    for r in ("utena_hechizo_126.gif", "utena_hechizo_x4.gif"):
        print(f"  {r}: {Image.open(OUT / r).size}, {(OUT / r).stat().st_size / 1024:.0f} KB")
    # hoja de fotogramas
    cols, z = 8, 2
    sh = Image.new("RGB", (cols * 126 * z // 2 * 1, ((L + cols - 1) // cols) * 126 * z // 2 * 1))
    w = 126
    sh = Image.new("RGB", (cols * w, ((L + cols - 1) // cols) * w))
    for i, f in enumerate(f126):
        sh.paste(f, ((i % cols) * w, (i // cols) * w))
    sh.save(OUT / "hoja_fotogramas.png")
    # comprobación del bucle: el último paso es casi igual al primero
    d = int((np.abs(np.asarray(fr[-1]).astype(int) - np.asarray(fr[0]).astype(int)).sum(-1) > 0).sum())
    print("píxeles nativos distintos entre el último paso y el primero:", d, "(el reposo respira, no es exactamente igual)")


if __name__ == "__main__":
    main()
