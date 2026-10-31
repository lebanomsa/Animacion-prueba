"""Vista previa de las opciones de cierre de Percier: guarda el objeto y la nube con el retrato desaparece.

  1 aspirado: el objeto se traga la nube (se estira hacia él y desaparece con un 'glup')
  2 pop:      la nube se infla y revienta, el retrato cae y se aplasta
  3 soplido:  el cuerno la manda volando, el retrato gira hasta un destello (no guarda el objeto)
Lienzo de 128x128 píxeles nativos (la ventana del marco a x5), fondo plano provisional. Salida en previews/.
"""
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import hojas
import piezas

HERE = Path(__file__).parent
PREV = HERE / "previews"
TMP = Path("/projects/sandbox/tmp/percier")
CW = CH = 128
FONDO = (46, 56, 84)
CREMA = piezas.CREMA
SOMBRA = (200, 200, 184)
AMARILLO = (248, 232, 128)
TICK = 80
X_F, Y_F = 90, 124                 # centro de las botas y suela de Percier en el lienzo
AX, AY = 64, 60                    # esquina inferior derecha de la nube (la burbuja pequeña apunta a Percier)

C1, C2, C3 = hojas.celdas(1), hojas.celdas(2), hojas.celdas(3)
CUERPO17, OBJETO17 = piezas.separar_objeto(C1[7])
NUBE_RET = C3[4]
_, RETRATO = piezas.separar_nube(NUBE_RET)
_a = np.array(NUBE_RET); _m = _a[..., 3] > 0
_a[_m] = (*CREMA, 255)
NUBE_LLENA = Image.fromarray(_a, "RGBA")           # silueta de la nube rellena (sin el retrato)


def pegar(img, x, y):
    lay = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    lay.alpha_composite(img, (int(x), int(y))) if 0 <= x and 0 <= y and x + img.width <= CW and y + img.height <= CH else _pegar_recorte(lay, img, int(x), int(y))
    return lay


def _pegar_recorte(lay, img, x, y):
    sx, sy = max(-x, 0), max(-y, 0)
    dx, dy = max(x, 0), max(y, 0)
    w, h = min(img.width - sx, CW - dx), min(img.height - sy, CH - dy)
    if w > 0 and h > 0:
        lay.alpha_composite(img.crop((sx, sy, sx + w, sy + h)), (dx, dy))


def percier(img, extra=None):
    """Percier con los pies en (X_F, Y_F); `extra` = (img, dx, dy) en coordenadas de la celda."""
    ox, oy = int(X_F - piezas.centro_pies(img)), Y_F - 116
    lay = pegar(img, ox, oy)
    return lay, (ox, oy)


def xf(lay, centro, destino, su=1.0, sv=1.0, ang=0.0, eje=0.0):
    """Mueve la capa de `centro` a `destino`; escala su (a lo largo del eje) y sv (perpendicular); gira `ang` grados."""
    c, s = math.cos(math.radians(eje)), math.sin(math.radians(eje))
    R = np.array([[c, -s], [s, c]])
    M = R @ np.diag([su, sv]) @ R.T                      # escalado en el eje
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    M = np.array([[ca, -sa], [sa, ca]]) @ M
    Mi = np.linalg.inv(M)
    cx, cy = destino
    a, b = Mi[0]; d, e = Mi[1]
    cc = centro[0] - a * cx - b * cy + 0.0
    ff = centro[1] - d * cx - e * cy + 0.0
    return lay.transform((CW, CH), Image.AFFINE, (a, b, cc, d, e, ff), resample=Image.NEAREST)


def disco(lay, cx, cy, r, col=CREMA, borde=SOMBRA):
    d = ImageDraw.Draw(lay)
    r = max(r, 1)
    d.ellipse((cx - r - 1, cy - r - 1, cx + r + 1, cy + r + 1), fill=borde + (255,))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col + (255,))


def destello(lay, cx, cy, r=4, col=AMARILLO):
    d = ImageDraw.Draw(lay)
    d.line((cx - r, cy, cx + r, cy), fill=col + (255,)); d.line((cx, cy - r, cx, cy + r), fill=col + (255,))
    d.rectangle((cx - 1, cy - 1, cx + 1, cy + 1), fill=(255, 255, 255, 255))


def componer(capas):
    img = Image.new("RGBA", (CW, CH), FONDO + (255,))
    for c in capas:
        if c is not None:
            img.alpha_composite(c)
    return img.convert("RGB")


# --- posiciones ---------------------------------------------------------------------------------------------------
NUBE_XY = (AX - 63, AY - 64)                       # esquina de la celda de la nube
C_NUBE = (NUBE_XY[0] + 32.5, NUBE_XY[1] + 34.5)    # centro de la nube
P17, (OX17, OY17) = percier(C1[7])
T_OBJ = (OX17 + 17, OY17 + 55)                     # placa del objeto bajado en 1.7 (en el lienzo)


def reposo(k):
    return percier(C2[k % 4])[0]


def nube(base="ret"):
    return pegar(NUBE_RET if base == "ret" else NUBE_LLENA, *NUBE_XY)


def cuerpo17():
    return pegar(CUERPO17, OX17, OY17)


def objeto17(dx=0, dy=0):
    return pegar(OBJETO17, OX17 + dx, OY17 + dy)


# --- opciones -----------------------------------------------------------------------------------------------------
def intro():
    return [componer([reposo(k), nube()]) for k in range(4)]


def op1():
    f = intro()
    f.append(componer([cuerpo17(), objeto17(), nube()]))                                 # baja el objeto
    f.append(componer([cuerpo17(), objeto17(1, 0), xf(nube(), C_NUBE, C_NUBE, 1.1, 0.9, eje=40)]))   # tiembla
    ang = math.degrees(math.atan2(T_OBJ[1] - C_NUBE[1], T_OBJ[0] - C_NUBE[0]))
    tabla = [(1.15, 0.85, .08), (1.35, 0.7, .2), (1.5, 0.52, .38), (1.3, 0.36, .58), (0.9, 0.22, .8), (0.4, 0.1, 1.0)]
    for i, (su, sv, mv) in enumerate(tabla):
        c = (C_NUBE[0] + (T_OBJ[0] - C_NUBE[0]) * mv, C_NUBE[1] + (T_OBJ[1] - C_NUBE[1]) * mv)
        sc = 1.12 if i in (3, 4) else 1.0
        f.append(componer([cuerpo17(), objeto17((-1) ** i, 0) if sc == 1.0 else
                           xf(objeto17(), T_OBJ, T_OBJ, sc, sc), xf(nube(), C_NUBE, c, su, sv, eje=ang)]))
    # glup: el objeto se encoge, puff
    g = pegar(Image.new("RGBA", (1, 1), (0, 0, 0, 0)), 0, 0)
    p = g.copy(); disco(p, int(T_OBJ[0]), int(T_OBJ[1]), 3)
    f.append(componer([cuerpo17(), xf(objeto17(), T_OBJ, T_OBJ, 0.6, 0.6), p]))
    p = g.copy(); disco(p, int(T_OBJ[0]), int(T_OBJ[1]) - 2, 5)
    f.append(componer([cuerpo17(), xf(objeto17(), T_OBJ, T_OBJ, 0.25, 0.25), p]))
    p = g.copy()
    for k in range(6):
        a = k * math.pi / 3 + 0.3
        disco(p, int(T_OBJ[0] + 9 * math.cos(a)), int(T_OBJ[1] - 2 + 9 * math.sin(a)), 1)
    f.append(componer([cuerpo17(), p]))
    f += [componer([cuerpo17()])] * 3
    return f


def op2():
    f = intro()
    f.append(componer([cuerpo17(), objeto17(), nube()]))
    f.append(componer([cuerpo17(), objeto17(), xf(nube(), C_NUBE, (C_NUBE[0] + 1, C_NUBE[1]), 1.08, 1.08)]))
    f.append(componer([cuerpo17(), xf(objeto17(), T_OBJ, T_OBJ, .7, .7), xf(nube(), C_NUBE, (C_NUBE[0] - 1, C_NUBE[1]), 1.18, 1.18)]))
    g = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    ret_xy = NUBE_XY
    suelo = Y_F - 4

    def puffs(r, rad):
        p = g.copy()
        for k in range(8):
            a = k * math.pi / 4 + 0.2
            disco(p, int(C_NUBE[0] + r * math.cos(a)), int(C_NUBE[1] + r * math.sin(a)), rad)
        return p
    f.append(componer([cuerpo17(), xf(objeto17(), T_OBJ, T_OBJ, .35, .35), pegar(RETRATO, *ret_xy), puffs(17, 5)]))
    f.append(componer([cuerpo17(), pegar(RETRATO, ret_xy[0], ret_xy[1] + 8), puffs(24, 5)]))
    f.append(componer([cuerpo17(), pegar(RETRATO, ret_xy[0], ret_xy[1] + 26), puffs(34, 3)]))
    # cae al suelo y se aplasta
    ret_base = (C_NUBE[0], suelo)
    y_suelo = suelo - 59 + 0
    sq = xf(pegar(RETRATO, ret_xy[0], y_suelo - 5 + 6), (C_NUBE[0], suelo), (C_NUBE[0], suelo), 1.35, 0.55)
    s = g.copy(); destello(s, int(C_NUBE[0]) - 12, suelo - 16); destello(s, int(C_NUBE[0]) + 14, suelo - 20, 3)
    f.append(componer([cuerpo17(), sq, s]))
    f.append(componer([cuerpo17(), sq, s]))
    f.append(componer([cuerpo17(), xf(sq, (C_NUBE[0], suelo), (C_NUBE[0], suelo), 0.6, 0.6)]))
    p = g.copy(); disco(p, int(C_NUBE[0]), suelo - 3, 4)
    f.append(componer([cuerpo17(), p]))
    f += [componer([cuerpo17()])] * 3
    return f


def op3():
    f = intro()
    horn = percier(C1[0])[0]
    f.append(componer([horn, nube()]))
    f.append(componer([horn, xf(nube(), C_NUBE, (C_NUBE[0] - 1, C_NUBE[1]), 1.05, 1.05)]))
    objetivo = [(-2, -4), (-12, -10), (-20, -18), (-26, -22), (-30, -26)]
    for i, (dx, dy) in enumerate(objetivo):
        sc = [1.0, .8, .6, .45, .3][i]
        f.append(componer([horn, xf(pegar(NUBE_RET, *NUBE_XY), C_NUBE, (C_NUBE[0] + dx * 1.2, C_NUBE[1] + dy * 0.7), sc, sc, ang=i * 50)]))
    s = Image.new("RGBA", (CW, CH), (0, 0, 0, 0)); destello(s, 8, 8, 5)
    f.append(componer([horn, s]))
    f += [componer([reposo(0)])] * 3
    return f


def guardar_gif(frames, path, escala=4, ultimo=700):
    imgs = [f.resize((CW * escala, CH * escala), Image.NEAREST) for f in frames]
    arrs = [np.asarray(i) for i in imgs]
    key = lambda a: a[..., 0].astype(np.uint32) << 16 | a[..., 1].astype(np.uint32) << 8 | a[..., 2]
    keys = np.unique(np.concatenate([key(a).ravel() for a in arrs]))
    assert len(keys) <= 256, len(keys)
    pal = np.zeros(768, np.uint8)
    pal[0:len(keys) * 3:3], pal[1:len(keys) * 3:3], pal[2:len(keys) * 3:3] = keys >> 16, keys >> 8 & 255, keys & 255
    out = []
    for a in arrs:
        p = Image.fromarray(np.searchsorted(keys, key(a)).astype(np.uint8), "P"); p.putpalette(pal.tolist()); out.append(p)
    dur = [TICK] * len(out); dur[-1] = ultimo
    out[0].save(path, save_all=True, append_images=out[1:], duration=dur, loop=0, disposal=1, optimize=False)
    return len(keys)


def tira(frames, idx, path, escala=3, titulo=""):
    w, h = CW * escala, CH * escala
    cols = 6
    rows = (len(idx) + cols - 1) // cols
    hoja = Image.new("RGB", (cols * w, rows * (h + 16) + 18), (20, 14, 24))
    d = ImageDraw.Draw(hoja); d.text((4, 3), titulo, fill=(255, 255, 255))
    for n, i in enumerate(idx):
        x, y = (n % cols) * w, 18 + (n // cols) * (h + 16)
        d.text((x + 4, y + 2), f"paso {i}", fill=(255, 220, 120))
        hoja.paste(frames[i].resize((w, h), Image.NEAREST), (x, y + 16))
    hoja.save(path)


def hoja1_numerada(path):
    """Hoja 1 con los fotogramas numerados del 1 al 10 (contando desde 1) para confirmar el noveno."""
    S = 4
    w = max(c.width for c in C1) * S
    hoja = Image.new("RGB", (5 * w, 2 * (120 * S + 22)), (60, 60, 86))
    d = ImageDraw.Draw(hoja)
    for k, c in enumerate(C1):
        x, y = (k % 5) * w, (k // 5) * (120 * S + 22)
        marca = (255, 230, 90) if k == 8 else (255, 255, 255)
        d.text((x + 6, y + 4), f"fotograma {k + 1}  (= 1.{k})" + ("   <- el 9" if k == 8 else ""), fill=marca)
        g = c.resize((c.width * S, c.height * S), Image.NEAREST)
        hoja.paste(g, (x, y + 20), g)
        if k == 8:
            d.rectangle((x + 1, y + 1, x + w - 2, y + 120 * S + 20), outline=(255, 230, 90), width=3)
    hoja.save(path)


if __name__ == "__main__":
    PREV.mkdir(exist_ok=True); TMP.mkdir(parents=True, exist_ok=True)
    hoja1_numerada(PREV / "hoja1_numerada.png")
    for n, fn, nombre in ((1, op1, "aspirado"), (2, op2, "pop"), (3, op3, "soplido")):
        fr = fn()
        p = PREV / f"cierre_{n}_{nombre}.gif"
        nc = guardar_gif(fr, p)
        idx = list(range(3, len(fr)))
        tira(fr, idx[:12], PREV / f"cierre_{n}_{nombre}_pasos.png", titulo=f"Opción {n}: {nombre}")
        print(f"{p.name}: {len(fr)} pasos, {nc} colores, {p.stat().st_size / 1024:.0f} KB")
        fr[0].save(TMP / f"op{n}_0.png")
