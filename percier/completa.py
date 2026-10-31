"""Animación completa de Percier, sin marco, transparente y en bucle.

Ciclo (pasos de 80 ms):
  A. gestos de la hoja 1:  1.0 pistola arriba -> 1.1/1.2 apunta -> 1.3 tajo azul -> 1.4/1.5/1.6 objeto levantado -> 1.7 lo baja
  B. nube:                 1.8 (noveno fotograma, objeto al frente): empieza la nube (3.0-3.3), Percier en reposo (hoja 2),
                           y el retrato (3.4-3.7) se queda un rato
  C. aspirado:             baja el objeto, la nube se estira hacia él y se la traga
  D. reinicio (opción 1):  cae la pistola desde arriba, la atrapa y pasa al 1.0, que es el primer fotograma del ciclo

Todo se coloca por la posición de las botas (los pies no se mueven). El lienzo se recorta al contenido de toda la animación;
la pistola entra por el borde superior.
Salida: percier_animacion.gif (x1), percier_animacion_x4.gif y percier_animacion_x4_fondo.gif (con fondo oscuro, para revisar).
"""
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import hojas
import piezas

HERE = Path(__file__).parent
W, H = 160, 128
TICK = 80
X_F, Y_F = 90, 124                 # centro de las botas y suela de Percier
AX, AY = 64, 60                    # esquina inferior derecha de la nube (la burbuja pequeña apunta a Percier)
CREMA, SOMBRA = piezas.CREMA, (200, 200, 184)

C1, C2, C3 = hojas.celdas(1), hojas.celdas(2), hojas.celdas(3)
CUERPO17, OBJETO17 = piezas.separar_objeto(C1[7])
CUERPO10, PISTOLA = piezas.separar_pistola(C1[0])
BB = PISTOLA.getchannel("A").getbbox()
PIS = PISTOLA.crop(BB)
PH = PIS.height


# ---- utilidades de capas ---------------------------------------------------------------------------------------------
def capa(img, x, y):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x, y = int(round(x)), int(round(y))
    sx, sy = max(-x, 0), max(-y, 0)
    dx, dy = max(x, 0), max(y, 0)
    w, h = min(img.width - sx, W - dx), min(img.height - sy, H - dy)
    if w > 0 and h > 0:
        lay.alpha_composite(img.crop((sx, sy, sx + w, sy + h)), (dx, dy))
    return lay


def componer(capas):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for c in capas:
        if c is not None:
            img.alpha_composite(c)
    return img


def poner_percier(img):
    ox, oy = int(X_F - piezas.centro_pies(img)), Y_F - 116
    return capa(img, ox, oy), (ox, oy)


def xf(lay, centro, destino, su=1.0, sv=1.0, eje=0.0):
    """Mueve la capa de `centro` a `destino`; escala su (a lo largo del eje, en grados) y sv (perpendicular)."""
    c, s = math.cos(math.radians(eje)), math.sin(math.radians(eje))
    R = np.array([[c, -s], [s, c]])
    Mi = np.linalg.inv(R @ np.diag([su, sv]) @ R.T)
    cx, cy = destino
    a, b = Mi[0]; d, e = Mi[1]
    return lay.transform((W, H), Image.AFFINE, (a, b, centro[0] - a * cx - b * cy, d, e, centro[1] - d * cx - e * cy),
                         resample=Image.NEAREST)


def disco(lay, cx, cy, r):
    d = ImageDraw.Draw(lay)
    r = max(r, 1)
    d.ellipse((cx - r - 1, cy - r - 1, cx + r + 1, cy + r + 1), fill=SOMBRA + (255,))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=CREMA + (255,))


def vacia():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


# ---- piezas colocadas -----------------------------------------------------------------------------------------------
P17, (OX17, OY17) = poner_percier(C1[7])
P10, (OX10, OY10) = poner_percier(C1[0])
CUERPO17_L, CUERPO10_L = capa(CUERPO17, OX17, OY17), capa(CUERPO10, OX10, OY10)
T_OBJ = (OX17 + 17, OY17 + 55)                     # placa del objeto bajado en 1.7
A10 = (OX10 + (BB[0] + BB[2]) / 2, OY10 + BB[3])   # centro de la base de la pistola en 1.0
H17 = (OX17 + 18, OY17 + 68)                       # base de la pistola en la mano abierta
NUBE_ENT = C3[4]
NUBE_XY = (AX - 63, AY - 64)
C_NUBE = (NUBE_XY[0] + 32.5, NUBE_XY[1] + 34.5)


def objeto17(dx=0, dy=0):
    return capa(OBJETO17, OX17 + dx, OY17 + dy)


def nube(k):
    """Celda k de la hoja 3, alineada por su borde derecho (la burbuja pequeña apunta a Percier) y su base."""
    c = C3[k]
    bb = c.getchannel("A").getbbox()
    return capa(c, AX - (bb[2] - 1), AY - 64)


def pistola(cx, cy, k=0, base=False):
    g = Image.fromarray(np.rot90(np.array(PIS), k).copy(), "RGBA")
    if base:
        return capa(g, cx - g.width / 2, cy - g.height)
    return capa(g, cx - g.width / 2, cy - g.height / 2)


# ---- partes ---------------------------------------------------------------------------------------------------------
def parte_a():
    f = []
    for k, n in ((0, 4), (1, 2), (2, 3), (3, 2), (4, 2), (5, 3), (6, 3), (7, 2)):
        f += [componer([poner_percier(C1[k])[0]])] * n
    return f


def parte_b():
    f = [componer([poner_percier(C1[8])[0], nube(0)])] * 2                       # fotograma 9 (1.8): sale el objeto, nace la nube
    t = 0
    for k in (1, 2, 3):                                                           # la nube crece, Percier en reposo
        for _ in range(2):
            f.append(componer([poner_percier(C2[t % 4])[0], nube(k)])); t += 1
    for _ in range(3):                                                            # el retrato se queda un rato
        for k in (4, 5, 6, 7):
            for _ in range(2):
                f.append(componer([poner_percier(C2[t % 4])[0], nube(k)])); t += 1
    return f


def parte_c():
    nb = nube(4)
    f = [componer([CUERPO17_L, objeto17(), nb])]
    f.append(componer([CUERPO17_L, objeto17(1, 0), xf(nb, C_NUBE, C_NUBE, 1.1, 0.9, eje=40)]))
    ang = math.degrees(math.atan2(T_OBJ[1] - C_NUBE[1], T_OBJ[0] - C_NUBE[0]))
    tabla = [(1.15, 0.85, .08), (1.35, 0.7, .2), (1.5, 0.52, .38), (1.3, 0.36, .58), (0.9, 0.22, .8), (0.4, 0.1, 1.0)]
    for i, (su, sv, mv) in enumerate(tabla):
        c = (C_NUBE[0] + (T_OBJ[0] - C_NUBE[0]) * mv, C_NUBE[1] + (T_OBJ[1] - C_NUBE[1]) * mv)
        obj = xf(objeto17(), T_OBJ, T_OBJ, 1.12, 1.12) if i in (3, 4) else objeto17((-1) ** i, 0)
        f.append(componer([CUERPO17_L, obj, xf(nb, C_NUBE, c, su, sv, eje=ang)]))
    p = vacia(); disco(p, int(T_OBJ[0]), int(T_OBJ[1]), 3)
    f.append(componer([CUERPO17_L, xf(objeto17(), T_OBJ, T_OBJ, 0.6, 0.6), p]))
    p = vacia(); disco(p, int(T_OBJ[0]), int(T_OBJ[1]) - 2, 5)
    f.append(componer([CUERPO17_L, xf(objeto17(), T_OBJ, T_OBJ, 0.25, 0.25), p]))
    p = vacia()
    for k in range(6):
        a = k * math.pi / 3 + 0.3
        disco(p, int(T_OBJ[0] + 9 * math.cos(a)), int(T_OBJ[1] - 2 + 9 * math.sin(a)), 1)
    f.append(componer([CUERPO17_L, p]))
    return f


def parte_d():
    f = [componer([CUERPO17_L])] * 3                                              # espera con la mano abierta
    for (y, k) in ((-34, 3), (-12, 2), (14, 1)):                                  # cae girando
        f.append(componer([CUERPO17_L, pistola(H17[0], y, k)]))
    f.append(componer([CUERPO17_L, pistola(H17[0], H17[1], 0, True)]))            # la atrapa
    f.append(componer([CUERPO17_L, pistola(H17[0], H17[1] + 2, 0, True)]))        # cede con el peso
    f.append(componer([CUERPO17_L, pistola(H17[0], H17[1], 0, True)]))
    mid = ((H17[0] + A10[0]) / 2, (H17[1] + A10[1]) / 2)
    f.append(componer([CUERPO10_L, pistola(mid[0], mid[1], 0, True)]))            # el siguiente paso es el 1.0 (inicio del ciclo)
    return f


# ---- salida -------------------------------------------------------------------------------------------------------
def guardar(frames, path, escala=1, fondo=None):
    imgs = [f.resize((f.width * escala, f.height * escala), Image.NEAREST) if escala > 1 else f for f in frames]
    if fondo:
        imgs2 = []
        for im in imgs:
            b = Image.new("RGBA", im.size, fondo + (255,)); b.alpha_composite(im); imgs2.append(b)
        imgs = imgs2
        arrs = [np.asarray(i.convert("RGB")) for i in imgs]
        key = lambda a: a[..., 0].astype(np.uint32) << 16 | a[..., 1].astype(np.uint32) << 8 | a[..., 2]
        keys = np.unique(np.concatenate([key(a).ravel() for a in arrs]))
        assert len(keys) <= 256
        pal = np.zeros(768, np.uint8)
        pal[0:len(keys) * 3:3], pal[1:len(keys) * 3:3], pal[2:len(keys) * 3:3] = keys >> 16, keys >> 8 & 255, keys & 255
        out = []
        for a in arrs:
            p = Image.fromarray(np.searchsorted(keys, key(a)).astype(np.uint8), "P"); p.putpalette(pal.tolist()); out.append(p)
        out[0].save(path, save_all=True, append_images=out[1:], duration=TICK, loop=0, disposal=1, optimize=False)
        return len(keys)
    colores = sorted({p[:3] for im in imgs for p in im.getdata() if p[3]})
    assert len(colores) <= 255, len(colores)
    index = {c: i + 1 for i, c in enumerate(colores)}
    flat = [255, 0, 255] + [v for c in colores for v in c]
    pal = []
    for im in imgs:
        p = Image.new("P", im.size, 0); p.putpalette(flat + [0] * (768 - len(flat)))
        p.putdata([index[q[:3]] if q[3] else 0 for q in im.getdata()]); pal.append(p)
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=TICK, loop=0, transparency=0, disposal=2, optimize=False)
    return len(colores)


def main():
    a, b, c, d = parte_a(), parte_b(), parte_c(), parte_d()
    frames = a + b + c + d
    print(f"A {len(a)} + B {len(b)} + C {len(c)} + D {len(d)} = {len(frames)} pasos = {len(frames) * TICK} ms")
    boxes = [f.getchannel("A").getbbox() for f in frames]
    box = (min(b[0] for b in boxes) - 1, 0, max(b[2] for b in boxes) + 1, max(b[3] for b in boxes) + 1)
    box = (max(box[0], 0), box[1], min(box[2], W), min(box[3], H))
    cro = [f.crop(box) for f in frames]
    print("lienzo recortado:", cro[0].size, "(origen", box[:2], ")")
    # el paso que cierra el ciclo debe enlazar con el primero (1.0): comprobación
    ref = componer([P10])
    ok = np.array_equal(np.asarray(cro[0]), np.asarray(ref.crop(box)))
    print("el primer paso es el 1.0 completo:", ok)
    for esc, suf in ((1, ""), (4, "_x4")):
        p = HERE / f"percier_animacion{suf}.gif"
        n = guardar(cro, p, esc)
        print(f"{p.name}: {cro[0].width * esc}x{cro[0].height * esc}, {n} colores, {p.stat().st_size / 1024:.0f} KB")
    p = HERE / "percier_animacion_x4_fondo.gif"
    n = guardar(cro, p, 4, fondo=(46, 56, 84))
    print(f"{p.name}: {n} colores, {p.stat().st_size / 1024:.0f} KB")
    # hoja con pasos clave
    S = 3
    idx = [0, 5, 9, 13, 18, 22, 24, 30, 40, 58, 66, 72, 76, 80, 84, 88]
    idx = [i for i in idx if i < len(cro)]
    w, h = cro[0].size
    cols = 6
    rows = (len(idx) + cols - 1) // cols
    hoja = Image.new("RGB", (cols * w * S, rows * (h * S + 16)), (20, 14, 24))
    dr = ImageDraw.Draw(hoja)
    for n_, i in enumerate(idx):
        x, y = (n_ % cols) * w * S, (n_ // cols) * (h * S + 16)
        dr.text((x + 4, y + 2), f"paso {i}", fill=(255, 220, 120))
        bg = Image.new("RGBA", cro[i].size, (46, 56, 84, 255)); bg.alpha_composite(cro[i])
        hoja.paste(bg.convert("RGB").resize((w * S, h * S), Image.NEAREST), (x, y + 16))
    (HERE / "previews").mkdir(exist_ok=True)
    hoja.save(HERE / "previews" / "percier_animacion_pasos.png")
    print("pasos:", len(cro))


if __name__ == "__main__":
    main()
