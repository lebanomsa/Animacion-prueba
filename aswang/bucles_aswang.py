"""Aswang: cuatro propuestas de bucle de prueba, a tamaño nativo 1x, en la ventana de 80x80 del marco de siempre (marco por defecto, sin paleta todavía).
  1 brindis    : reposo, frasco rojo (victoria) y vuelta al reposo
  2 aura       : murciélagos, se pone de pie, se agacha, aura de sangre parpadeante, pose final
  3 historia   : el ataque especial, explosión de fuego a la derecha, comando señalando con murciélagos que salen volando
  4 vuelo      : despega, flota con alas de murciélago y desciende
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "secuencia"))
import hoja_aswang as ha
import marco

OUT = HERE / "salida"
TICK = 80
VN, SUELO = 80, 72
FONDO, SUELO_COL = (30, 32, 40, 255), (22, 24, 30, 255)


class R:
    pass


def cargar():
    r = R()
    f = lambda y: [ha.recorte_sin_borde(c) for c in ha.fila(y)]
    r.idle, r.idle_nb, r.vuelo = f(50), f(136), f(210)
    r.seq1, r.seq2, r.seq3 = f(454), f(503), f(573)
    r.seq4 = f(805)                                   # 12 fotogramas sin efectos, en el orden de la hoja
    r.fin = f(883)[0]
    r.vic = f(1293) + f(1343)
    r.cmd, r.desc = f(1417), f(1490)
    r.murc = f(1637)                                  # murciélagos aleteando (8)
    r.fuego, r.humo = f(1937), f(1817) + f(1877)
    r.anillo = f(2070)                                # anillo de fuego/sangre para el aura (6)
    return r


def nueva():
    lz = Image.new("RGBA", (VN, VN), FONDO)
    lz.paste(Image.new("RGBA", (VN, VN - SUELO), SUELO_COL), (0, SUELO))
    return lz


def pegar(lz, img, x, y):
    x, y = int(round(x)), int(round(y))
    l, t = max(0, -x), max(0, -y)
    r_, b_ = min(img.width, lz.width - x), min(img.height, lz.height - y)
    if r_ > l and b_ > t: lz.alpha_composite(img.crop((l, t, r_, b_)), (x + l, y + t))


def pies(lz, img, x, h=0):
    cx, by = ha.pies(img)
    pegar(lz, img, x - cx, SUELO - h - by)


def base(lz, img, x, y):
    """Ancla en el centro de la fila de abajo (efectos de suelo)."""
    pegar(lz, img, x - img.width / 2, y - img.height)


# ------------------------------------------------------------------ guiones: lista de dicts {ase: imagen, x, h, extra: [(imagen, x, y, 'pies'|'base'|'abs')]}
def P(img, x, h=0, extra=None): return dict(img=img, x=x, h=h, extra=extra or [])


def g1(r):
    X = 40; L = []
    L += [P(r.idle_nb[i], X) for i in range(8)]
    L += [P(r.vic[i], X) for i in range(14)]
    return L


def seq_aura(r, X, repeticiones):
    L = []
    for i in range(4): L.append(P(r.idle_nb[i], X))
    for i in range(8):                                  # murciélagos pequeños la rodean mientras se pone de pie
        mx = X - 18 + 36 * ((i + 1) / 8)
        L.append(P(r.seq2[i], X, extra=[(r.seq1[i], mx, SUELO - 56 + 3 * np.sin(i), "abs")]))
    for i in range(5): L.append(P(r.seq3[i], X))
    for k in range(12 * repeticiones):
        L.append(P(r.seq4[k % 12], X, extra=[(r.anillo[(k // 2) % 6], X, SUELO + 2, "base")]))
    return L


def g2(r):
    X = 40
    L = seq_aura(r, X, 2)
    L.append(P(r.fin, X))
    return L


def g3(r):
    X = 34; XE = 70
    L = seq_aura(r, X, 1)
    L.append(P(r.fin, X)); L.append(P(r.fin, X))
    t0 = len(L)                                         # explosión de fuego a la derecha, luego humo
    for k in range(10):
        L.append(P(r.fin if k < 2 else r.cmd[min(5, k - 2)], X, extra=[(r.fuego[k], XE, SUELO + 2, "base_f")]))
    for k in range(13):
        L.append(P(r.cmd[5], X, extra=[(r.humo[k], XE, SUELO + 2, "base_f")] + ([(r.murc[k % 8], X + 8 + 6 * k, SUELO - 44 + (k % 3) * 5, "abs_f")] if k < 11 else [])))
    for k in range(13, 26):
        L.append(P(r.idle_nb[k % 8], X, extra=[(r.humo[k], XE, SUELO + 2, "base_f")]))
    return L


def g4(r):
    X = 40; L = []
    for i in range(8): L.append(P(r.idle[i], X))
    for k in range(6):                                  # despega
        L.append(P(r.vuelo[k % 8], X, h=22 * (k + 1) / 6))
    for k in range(16):                                 # flota
        L.append(P(r.vuelo[k % 8], X, h=22 + 1.2 * np.sin(2 * np.pi * k / 8)))
    for k in range(6):                                  # desciende
        L.append(P(r.vuelo[(k + 6) % 8] if k < 4 else r.desc[k - 4], X, h=22 * (5 - k) / 6))
    L.append(P(r.desc[1], X))
    return L


def render126(L, marco_im):
    """Fotogramas de 126x126: fondo de la ventana, Aswang y efectos, marco, y por delante del marco los efectos marcados con '_f' (explosión, humo, murciélagos)."""
    out = []
    for p in L:
        lz = nueva()
        for img, x, y, modo in p["extra"]:
            if modo == "base": base(lz, img, x, y)
        pies(lz, p["img"], p["x"], p["h"])
        for img, x, y, modo in p["extra"]:
            if modo == "abs": pegar(lz, img, x - img.width / 2, y - img.height / 2)
        c = Image.new("RGBA", (126, 126), (0, 0, 0, 255)); c.paste(lz, (23, 23)); c.alpha_composite(marco_im)
        for img, x, y, modo in p["extra"]:
            if modo == "base_f": pegar(c, img, 23 + x - img.width / 2, 23 + y - img.height)
            if modo == "abs_f": pegar(c, img, 23 + x - img.width / 2, 23 + y - img.height / 2)
        out.append(c.convert("RGB"))
    return out


def gif_local(frames, ruta, dur):
    k = lambda a: a[..., 0].astype(np.uint32) << 16 | a[..., 1].astype(np.uint32) << 8 | a[..., 2]
    ps, agrupados = [], 0
    for fr in frames:
        a = np.asarray(fr.convert("RGB")); keys = np.unique(k(a))
        if len(keys) <= 256:
            pal = np.zeros(768, np.uint8)
            pal[0:len(keys) * 3:3], pal[1:len(keys) * 3:3], pal[2:len(keys) * 3:3] = keys >> 16, keys >> 8 & 255, keys & 255
            p = Image.fromarray(np.searchsorted(keys, k(a)).astype(np.uint8), "P"); p.putpalette(pal.tolist())
        else:
            p = fr.convert("RGB").quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE); agrupados += 1
        ps.append(p)
    ps[0].save(ruta, save_all=True, append_images=ps[1:], duration=dur, loop=0, disposal=1, optimize=False)
    return agrupados


def main():
    r = cargar(); OUT.mkdir(exist_ok=True)
    fr, _ = marco.build()
    img = np.array(fr); o = img[..., 3] > 0
    q = Image.fromarray(img[..., :3][o].reshape(-1, 1, 3), "RGB").quantize(colors=40, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    img[..., :3][o] = np.array(q.getpalette()[:120], np.uint8).reshape(-1, 3)[np.asarray(q).reshape(-1)]
    marco_im = Image.fromarray(img, "RGBA").crop((1, 1, 127, 127))
    for nombre, g in (("1_brindis", g1), ("2_aura", g2), ("3_historia", g3), ("4_vuelo", g4)):
        L = g(r)
        marcos = render126(L, marco_im)
        ag = gif_local([m.resize((504, 504), Image.NEAREST) for m in marcos], OUT / f"{nombre}_x4.gif", TICK)
        n = len(L); idx = sorted(set(int(round(i * (n - 1) / 11)) for i in range(12)))
        s = Image.new("RGB", (4 * 254, 3 * 254), (10, 10, 10))
        for j, i in enumerate(idx): s.paste(marcos[i].resize((252, 252), Image.NEAREST), ((j % 4) * 254, (j // 4) * 254))
        s.save(OUT / f"momentos_{nombre}.png")
        a = [np.asarray(m).astype(int) for m in marcos]
        d = int((np.abs(a[-1] - a[0]).sum(-1) > 0).sum())
        print(nombre, n, "pasos de", TICK, "ms =", round(n * TICK / 1000, 2), "s; agrupados:", ag, "; último vs primero:", d, "px de", 126 * 126)


if __name__ == "__main__":
    main()
