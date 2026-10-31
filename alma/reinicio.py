"""Efectos nuevos de reinicio para Alma (de la forma humana de rodillas a la criatura acurrucada).

Todos usan solo colores del propio sprite (crema, amarillos y ámbares del pelo y de la cola de tigre) y son
de píxeles duros, aptos para GIF. Cada efecto se calcula para 10 pasos de 70 ms, con el cambio entre el paso 3
(forma humana) y el paso 4 (criatura):
  A  estallido radial: un disco de luz crece con rayos, tapa la figura y se abre en un anillo que se aleja.
  B  columna de luz: un haz vertical se ensancha hasta tapar la figura y se estrecha dejando motas que suben.
  C  zarpazos: tres cortes diagonales (de tigre) cruzan la figura y terminan en un destello.
  D  disolución en chispas: la forma humana se deshace de arriba abajo en chispas que suben y la criatura se
     recompone de abajo arriba con chispas que caen. No necesita cubrir nada.
"""
import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import hojas                    # noqa: E402
import make_alma as ma          # noqa: E402

W_, Y1, Y2, Y3, Y4 = (248, 248, 232), (248, 232, 128), (240, 200, 80), (216, 144, 40), (160, 88, 32)
CWE, CHE = 220, 160             # lienzo de los efectos
OFF = (45, 20)                  # dónde se pega el lienzo de make_alma (130x120)
CX, CY = 113, 92                # centro de los efectos
SUELO = ma.SUELO + OFF[1]       # fila del suelo en el lienzo de los efectos
NP = 10
TS = 4                          # paso en que la criatura sustituye a la forma humana

YY, XX = np.mgrid[0:CHE, 0:CWE]


def canvas():
    return np.zeros((CHE, CWE, 4), np.uint8)


def put(a, mask, color):
    a[mask] = color + (255,)


def escena():
    """(forma humana, criatura) en el lienzo de los efectos, como arrays RGBA."""
    F = hojas.fotogramas()
    lien, _ = ma.alinear(F)
    out = []
    for k in (28, 0):
        c = Image.new("RGBA", (CWE, CHE), (0, 0, 0, 0)); c.alpha_composite(lien[k], OFF); out.append(np.asarray(c).copy())
    return out


# ------------------------------------------------------------------ A: estallido radial
def estallido(t):
    a = canvas()
    rf = [6, 16, 30, 46, 52, 36, 22, 9, 0, 0][t]
    ring = [0, 0, 0, 0, 0, 58, 66, 71, 75, 77][t]
    th = [0, 0, 0, 0, 0, 8, 6, 4, 3, 2][t]
    d = np.hypot((XX - CX) / 1.3, (YY - CY) / 0.95)                    # elipse algo más ancha que alta
    if 1 <= t <= 6:                                                   # rayos largos y cortos alternados
        for k in range(12):
            ang = k * math.pi / 6 + (math.pi / 12 if t % 2 else 0)
            L = (rf * 1.2 + 16) if k % 2 == 0 else (rf * 1.2 + 8)
            ca, sa = math.cos(ang), math.sin(ang)
            along = (XX - CX) * ca + (YY - CY) * sa
            perp = -(XX - CX) * sa + (YY - CY) * ca
            r0 = rf * 0.7 * (1.3 if abs(ca) > 0.7 else 1.0)
            m = (along > r0) & (along < L) & (np.abs(perp) <= 3.2 * (1 - (along - r0) / max(L - r0, 1)))
            put(a, m, Y3); put(a, m & (along < L - 5), Y2)
    if rf > 0:
        put(a, d <= rf, Y3); put(a, d <= rf * 0.86, Y2); put(a, d <= rf * 0.66, Y1); put(a, d <= rf * 0.42, W_)
    if th:
        m = (d <= ring) & (d > ring - th)
        put(a, m, Y1); put(a, m & (d > ring - th * 0.5), W_)
        put(a, (d <= ring - th) & (d > ring - th - 2), Y3)
    return a


# ------------------------------------------------------------------ B: columna de luz
def columna(t):
    a = canvas()
    w = [3, 12, 44, 92, 100, 56, 30, 12, 4, 0][t]
    top, bot = 14, SUELO + 6
    if w > 0:
        u = np.abs(XX - CX) / (w / 2.0)
        hw = w / 2.0
        cuerpo = (u <= 1) & (YY >= top + hw) & (YY <= bot)
        punta = (((XX - CX) / max(hw, 1)) ** 2 + ((YY - (top + hw)) / max(hw, 1)) ** 2 <= 1) & (YY < top + hw)
        m = cuerpo | punta
        u = np.where(YY < top + hw, np.hypot(XX - CX, YY - (top + hw)) / max(hw, 1), u)
        put(a, m, Y3); put(a, m & (u <= 0.85), Y2); put(a, m & (u <= 0.62), Y1); put(a, m & (u <= 0.30), W_)
        base = ((XX - CX) / (w * 0.9 + 4)) ** 2 + ((YY - bot) / 7.0) ** 2 <= 1               # charco de luz en el suelo
        put(a, base, Y2); put(a, base & (((XX - CX) / (w * 0.5 + 2)) ** 2 + ((YY - bot) / 4.0) ** 2 <= 1), Y1)
    rnd = random.Random(11)
    for _ in range(16):                                                # motas que suben
        x = CX + rnd.randint(-40, 40); y0 = rnd.randint(SUELO - 70, SUELO + 4); s = rnd.randint(1, 3) + 1
        for age in range(0, 5):
            tt = t - age
            if 1 <= tt <= 9 and age <= 3:
                y = y0 - 8 * tt
                col = (W_, Y1, Y2, Y3)[age]
                if 0 <= y < CHE - 2 and 0 <= x < CWE - 2:
                    a[y:y + 2, x:x + 2] = col + (255,)
    return a


# ------------------------------------------------------------------ C: zarpazos de tigre
def zarpazo(a, p0, p1, frac, tmax):
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    along = ((XX - x0) * ux + (YY - y0) * uy) / L
    perp = np.abs(-(XX - x0) * uy + (YY - y0) * ux)
    half = tmax / 2.0 * np.sin(np.clip(along, 0, 1) * math.pi) ** 0.8
    m = (along >= 0) & (along <= frac) & (perp <= half)
    put(a, m, Y3); put(a, m & (perp <= half * 0.78), Y2); put(a, m & (perp <= half * 0.5), Y1); put(a, m & (perp <= half * 0.22), W_)


def zarpazos(t):
    a = canvas()
    tmax = [9, 10, 11, 12, 12, 10, 6, 3, 0, 0][t]
    fade = t >= 5
    for k in range(3):
        p0 = (CX - 64 + 38 * k, CY - 66)
        p1 = (CX - 6 + 38 * k, CY + 56)
        frac = 1.0 if t >= 4 else float(np.clip((t - k + 1) / 2.0, 0, 1))
        if t > 6:
            frac = 0
        if frac > 0:
            zarpazo(a, p0, p1, frac, tmax * (1.0 if not fade else 1.0))
    if t in (3, 4):                                                     # destello que tapa la figura (pico en el 4)
        r_ = 44 if t == 3 else 52
        el = np.hypot((XX - CX) / 1.4, (YY - CY) / 0.95)               # elipse más ancha que alta
        put(a, el <= r_, Y3); put(a, el <= r_ * 0.86, Y2); put(a, el <= r_ * 0.64, Y1); put(a, el <= r_ * 0.36, W_)
    if t in (5, 6):                                                     # chispas que salen del destello
        rnd = random.Random(5 + t)
        for _ in range(26):
            ang = rnd.uniform(0, 2 * math.pi); r = rnd.uniform(40, 60) + (t - 4) * 10
            x = int(CX + r * math.cos(ang)); y = int(CY + r * math.sin(ang) * 0.9)
            col = rnd.choice((W_, Y1, Y2))
            if 0 <= x < CWE - 2 and 0 <= y < CHE - 2:
                a[y:y + 2, x:x + 2] = col + (255,)
    return a


# ------------------------------------------------------------------ D: disolución en chispas
def disolucion(t, viejo, nuevo):
    """Devuelve (capa del personaje, capa de chispas) del paso t."""
    rnd = np.random.RandomState(3)
    r_old, r_new = rnd.rand(CHE, CWE), rnd.rand(CHE, CWE)

    def ynorm(img):
        ys, xs = np.nonzero(img[..., 3] > 0)
        return np.clip((YY - ys.min()) / max(ys.max() - ys.min(), 1), 0, 1)

    T_old = 0.62 * ynorm(viejo) + 0.38 * r_old                          # se va de arriba abajo
    T_new = 0.62 * (1 - ynorm(nuevo)) + 0.38 * r_new                    # llega de abajo arriba
    prog_old = lambda s: (s + 1) / 5.0                                   # fuera del todo en el paso 4
    prog_new = lambda s: (s - 3) / 5.0                                   # completo en el paso 8
    perso = canvas()
    keep_old = (viejo[..., 3] > 0) & (T_old >= prog_old(t))
    keep_new = (nuevo[..., 3] > 0) & (T_new <= prog_new(t))
    perso[keep_old] = viejo[keep_old]
    perso[keep_new] = nuevo[keep_new]
    chispas = canvas()
    prng = random.Random(9)
    col_age = (W_, Y1, Y2, Y3, Y4)
    # chispas que salen de los píxeles que se van (suben)
    for s in range(0, 5):
        lo, hi = (prog_old(s - 1) if s > 0 else 0), prog_old(s)
        ys, xs = np.nonzero((viejo[..., 3] > 0) & (T_old >= lo) & (T_old < hi))
        for y, x in zip(ys, xs):
            if prng.random() < 0.42:
                age = t - s
                if 0 <= age <= 4:
                    yy = int(y - 3 * age - prng.randint(0, 2)); xx = int(x + prng.randint(-1, 1) * age)
                    sz = 2 if age <= 1 else 1
                    if 0 <= yy < CHE - 2 and 0 <= xx < CWE - 2:
                        chispas[yy:yy + sz, xx:xx + sz] = col_age[age] + (255,)
    # chispas que caen sobre los píxeles que llegan
    for s in range(3, 9):
        lo, hi = prog_new(s - 1), prog_new(s)
        ys, xs = np.nonzero((nuevo[..., 3] > 0) & (T_new > lo) & (T_new <= hi))
        for y, x in zip(ys, xs):
            if prng.random() < 0.42:
                lead = s - t                                          # pasos que faltan para que el píxel llegue
                if 1 <= lead <= 3:
                    yy = int(y - 4 * lead); xx = int(x + prng.randint(-1, 1) * lead)
                    sz = 2 if lead >= 2 else 1
                    if 0 <= yy < CHE - 2 and 0 <= xx < CWE - 2:
                        chispas[yy:yy + sz, xx:xx + sz] = col_age[min(lead, 3)] + (255,)
    return perso, chispas


# ------------------------------------------------------------------ composición
def componer(opcion):
    viejo, nuevo = escena()
    frames = []
    cover = {}
    for t in range(NP):
        base = canvas()
        if opcion == "D":
            perso, chispas = disolucion(t, viejo, nuevo)
            img = Image.fromarray(perso, "RGBA"); img.alpha_composite(Image.fromarray(chispas, "RGBA"))
            frames.append(img); continue
        fx = {"A": estallido, "B": columna, "C": zarpazos}[opcion](t)
        src = viejo if t < TS else nuevo
        img = Image.fromarray(src, "RGBA"); img.alpha_composite(Image.fromarray(fx, "RGBA"))
        frames.append(img)
        if t in (TS - 1, TS):
            cubre = fx[..., 3] > 0
            cover[t] = int(((src[..., 3] > 0) & ~cubre).sum())
    return frames, cover


def main():
    out = HERE / "previews"; out.mkdir(exist_ok=True)
    nombres = {"A": "estallido radial", "B": "columna de luz", "C": "zarpazos de tigre", "D": "disolución en chispas"}
    S = 2
    pasos = [1, 3, 4, 5, 7]
    cw, ch = CWE * S, CHE * S
    sheet = Image.new("RGB", (cw * len(pasos), (ch + 16) * 4), (20, 10, 14))
    from PIL import ImageDraw
    d = ImageDraw.Draw(sheet)
    for r, op in enumerate("ABCD"):
        frames, cover = componer(op)
        d.text((4, r * (ch + 16) + 2), f"{op}: {nombres[op]}"
               + (f"  |  figura a la vista: antes del cambio {cover[TS - 1]} px, después {cover[TS]} px" if cover else ""),
               fill=(255, 255, 255))
        for c, p in enumerate(pasos):
            bg = Image.new("RGBA", frames[p].size, (40, 22, 36, 255)); bg.alpha_composite(frames[p])
            sheet.paste(bg.convert("RGB").resize((cw, ch), Image.NEAREST), (c * cw, r * (ch + 16) + 16))
        print(op, nombres[op], "| cobertura (px de la figura a la vista, antes/después del cambio):", cover or "no aplica")
        # GIF de prueba: transparente y en bucle
        imgs = [f.resize((f.width * 2, f.height * 2), Image.NEAREST) for f in frames]
        colors = sorted({p[:3] for im in imgs for p in im.getdata() if p[3]})
        index = {c: i + 1 for i, c in enumerate(colors)}
        flat = [255, 0, 255] + [v for c in colors for v in c]
        pal = []
        for im in imgs:
            p = Image.new("P", im.size, 0); p.putpalette(flat + [0] * (768 - len(flat)))
            p.putdata([index[q[:3]] if q[3] else 0 for q in im.getdata()]); pal.append(p)
        pal[0].save(out / f"reinicio_{op}.gif", save_all=True, append_images=pal[1:], duration=70, loop=0,
                    transparency=0, disposal=2, optimize=False)
    sheet.save(out / "reinicio_opciones.png"); print("hoja:", sheet.size)


if __name__ == "__main__":
    main()
