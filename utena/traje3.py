"""Traje entallado con silueta femenina y estrellas en los cuernos (pose 0), a partir de traje2.
Traje entallado mejorado para Utena (pose 0): cuello visible, hombros redondeados, mangas con axila y codo,
solapas anchas con muesca, sombra que sigue el volumen y algo más de contraste.

Todo en píxeles nativos (96x128). Del GIF se conservan la cabeza (filas 0-40) y las manos.
Salida: previews/traje_mejorado_comparacion.png, previews/traje_mejorado_detalle.png, previews/traje_mejorado_x5.png
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import hojas
import traje as t1
import traje2 as t2

HERE = Path(__file__).parent
PREV = HERE / "previews"

OL, J0, J1, J2, J3 = (8, 8, 10), (22, 22, 26), (36, 36, 40), (66, 66, 72), (108, 108, 116)
P0, P1, P2 = (18, 18, 22), (31, 31, 35), (58, 58, 64)
T0, T1_, T2 = (74, 38, 82), (116, 65, 122), (160, 104, 166)
W, WS = (255, 255, 255), (209, 201, 207)
PIEL, PIEL_S = (255, 225, 215), (250, 184, 167)
XX = np.arange(96)[None, :]
YY = np.arange(128)[:, None]


def m(pol):
    return t1.mascara(pol)


def borde(mk):
    return t1.borde(mk)


def bordes_fila(mk, y):
    xs = np.where(mk[y])[0]
    return (xs.min(), xs.max()) if len(xs) else (None, None)


def vestir(src, solo_torso=False):
    """solo_torso=True: solo saco, camisa, corbata y cuello (sin pantalón, zapatos, mangas, manos ni cabeza)."""
    out = np.zeros((128, 96, 4), np.uint8)
    rgb = out[..., :3]

    def poner(mask, col):
        rgb[mask] = col
        out[mask, 3] = 255

    # ---------------- pantalón (pierna entallada recta) ----------------
    izq = m([(38, 66), (46, 66), (46, 84), (41, 107), (36, 107), (36, 84)])
    der = m([(46, 66), (55, 66), (57, 84), (58, 107), (53, 107), (47, 84)])
    if solo_torso:
        izq[:] = False; der[:] = False
    piernas = izq | der
    poner(piernas, P1)
    for y in range(66, 108):                       # sombra en el lado interior de cada pierna
        a, b = bordes_fila(izq, y)
        if a is not None:
            rgb[y, b - 1] = P0
        a, b = bordes_fila(der, y)
        if a is not None:
            rgb[y, a + 1] = P0
    for (xa, ya, xb, yb) in ((41, 84, 38, 104), (51, 84, 55, 104)):   # raya del pantalón
        for k in range(yb - ya + 1):
            x = round(xa + (xb - xa) * k / (yb - ya))
            rgb[ya + k, x] = P2
    for (x, y, c) in ((38, 90, P2), (39, 91, P0), (55, 90, P2), (54, 91, P0)):   # pliegue de rodilla
        rgb[y, x] = c
    rgb[borde(izq)] = OL
    rgb[borde(der)] = OL

    # ---------------- zapatos (silueta de los pies del GIF) ----------------
    for y in (range(108, 119) if not solo_torso else ()):
        for x in range(96):
            if src[y, x, 3]:
                lum = src[y, x, :3].astype(int).sum() / 3
                rgb[y, x] = OL if lum < 55 else (P1 if lum < 150 else ((48, 48, 52) if lum < 215 else (78, 78, 84)))
                out[y, x, 3] = 255

    # ---------------- saco ----------------
    cuerpo = m([(41, 42), (51, 42), (53, 43), (57, 46), (58, 50), (57, 54), (54, 58), (52, 61), (53, 64), (56, 69),
                (57, 74), (57, 78), (50, 80), (46, 64), (42, 80), (35, 78), (35, 74), (36, 69), (39, 64), (40, 61),
                (38, 58), (35, 54), (34, 50), (35, 46), (39, 43)])
    poner(cuerpo, J1)
    for y in range(44, 81):
        a, b = bordes_fila(cuerpo, y)
        if a is None:
            continue
        rgb[y, a + 1] = J2 if y >= 46 else J1                  # luz de borde a la izquierda
        rgb[y, b - 1] = J0                                      # sombra a la derecha, siguiendo el contorno
        if 47 <= y <= 66:
            rgb[y, b - 2] = J0
    for (x, y) in ((41, 60), (42, 61), (51, 60), (50, 61), (39, 74), (53, 74)):   # pliegues de cintura y faldón
        rgb[y, x] = J0
    for x in range(36, 42):                                    # luz en los hombros
        rgb[45 if x < 39 else 44, x] = J2
    for x in range(51, 57):
        rgb[44 if x < 54 else 45, x] = J2
    for (x0, x1, y) in ((38, 41, 70), (51, 54, 70)):           # bolsillos con tapa
        rgb[y, x0:x1 + 1] = J2
        rgb[y + 1, x0:x1 + 1] = OL

    # solapas anchas con muesca
    sol_i = m([(41, 44), (45, 62), (44, 62), (39, 51), (37, 50), (38, 47), (37, 45), (39, 44)])
    sol_d = m([(51, 44), (47, 62), (48, 62), (53, 51), (55, 50), (54, 47), (55, 45), (53, 44)])
    for s, interior_izq in ((sol_i, False), (sol_d, True)):
        rgb[s] = J2
        rgb[borde(s)] = J0
        for y in range(44, 53):                                # filo de luz junto a la camisa
            a, b = bordes_fila(s, y)
            if a is not None:
                rgb[y, a if interior_izq else b] = J3
    rgb[48, 37] = OL; rgb[48, 55] = OL                         # muesca

    # curva del pecho: sombra en arco bajo el busto y una luz encima
    for (x, y) in ((38, 55), (39, 56), (40, 56), (41, 55), (51, 55), (52, 56), (53, 56), (54, 55)):
        rgb[y, x] = J0
    for (x, y) in ((39, 54), (40, 54), (52, 54), (53, 54)):
        rgb[y, x] = J2
    # pañuelo blanco en el bolsillo del pecho
    for (x, y, c) in ((53, 52, W), (54, 51, W), (54, 52, W), (55, 52, WS)):
        rgb[y, x] = c
    for x in range(53, 57):
        rgb[53, x] = OL

    # ---------------- mangas con axila, codo y puño ----------------
    m_izq = m([(35, 45), (37, 46), (38, 49), (38, 53), (36, 58), (32, 67), (27, 66), (31, 57), (33, 50), (34, 47)])
    m_der = m([(56, 45), (58, 46), (60, 50), (61, 53), (66, 57), (66, 62), (64, 62), (58, 58), (56, 55), (55, 50)])
    if solo_torso:
        m_izq[:] = False; m_der[:] = False
    for s in (m_izq, m_der):
        rgb[s] = J1
        out[s, 3] = 255
    for y in range(45, 68):                                    # manga izquierda: luz fuera, sombra en la axila
        a, b = bordes_fila(m_izq, y)
        if a is not None:
            rgb[y, a + 1] = J2
            rgb[y, b - 1] = J0
    for x in range(55, 67):                                    # manga derecha: luz arriba, sombra abajo
        ys = np.where(m_der[:, x])[0]
        if len(ys):
            rgb[ys.min() + 1, x] = J2
            rgb[ys.max() - 1, x] = J0
    for (x, y, c) in ((33, 57, J2), (34, 57, J2), (34, 58, J0), (59, 55, J0), (60, 56, J0), (60, 54, J2)):   # codos
        rgb[y, x] = c
    rgb[borde(m_izq)] = OL
    rgb[borde(m_der)] = OL
    rgb[borde(cuerpo) & ~m_izq & ~m_der] = OL
    if not solo_torso:
        pr_i = YY * 0.92 - XX * 0.4
        pu = m_izq & (pr_i >= pr_i[m_izq].max() - 1.7)
        rgb[pu] = W; rgb[pu & (XX >= np.where(pu.any(0))[0].max() - 1)] = WS
        pr_d = XX * 0.88 + YY * 0.48
        pd = m_der & (pr_d >= pr_d[m_der].max() - 1.7)
        rgb[pd] = W; rgb[pd & (YY >= np.where(pd.any(1))[0].max())] = WS

    # ---------------- cuello, camisa y corbata ----------------
    for y in range(41, 44):                                    # cuello visible (3 filas)
        for x in range(44, 49):
            rgb[y, x] = PIEL_S if (y == 41 or x in (44, 48)) else PIEL
            out[y, x, 3] = 255
    abertura = m([(41, 44), (51, 44), (46, 63)]) & ~sol_i & ~sol_d
    abertura |= m([(42, 44), (50, 44), (46, 61)]) & ~sol_i & ~sol_d
    rgb[abertura] = W
    rgb[abertura & (XX >= 48)] = WS
    out[abertura, 3] = 255
    for (x, y, c) in ((43, 44, W), (44, 44, W), (44, 45, W), (48, 44, W), (49, 44, W), (48, 45, WS)):   # puntas del cuello
        rgb[y, x] = c; out[y, x, 3] = 255
    for y in range(44, 57):                                    # corbata: nudo pequeño, cuerpo de 3 y punta
        xs = (45, 46, 47) if y <= 55 else (46,)
        for x in xs:
            rgb[y, x] = T0 if x == 47 else T1_
        if y in (44, 47, 50, 53):
            rgb[y, 45] = T2
    rgb[45, 45:48] = T0                                        # base del nudo
    rgb[44, 46] = T2
    rgb[62, 46] = J3; rgb[63, 46] = OL                         # botón

    # ---------------- manos y cabeza del GIF ----------------
    for (x0, x1, y0, y1) in (((20, 33, 66, 74), (64, 78, 58, 67)) if not solo_torso else ()):
        for y in range(y0, y1):
            for x in range(x0, x1):
                c = tuple(src[y, x, :3])
                if src[y, x, 3] and c in t1.PIEL:
                    rgb[y, x] = c; out[y, x, 3] = 255
    cab = src[:41] if not solo_torso else np.zeros((41, 96, 4), np.uint8)
    mk = cab[..., 3] > 0
    out[:41][mk] = cab[mk]
    S1, S2 = (98, 50, 146), (196, 150, 236)
    for (cx, cy) in (((53, 22), (35, 23)) if not solo_torso else ()):                     # estrella morada de 4 puntas en cada cuerno
        for (dx, dy) in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            rgb[cy + dy, cx + dx] = S1
        rgb[cy, cx] = S2
    return Image.fromarray(out, "RGBA")


def main():
    PREV.mkdir(exist_ok=True)
    fr, _ = hojas.fotogramas()
    src = np.asarray(fr[0]).copy()
    antes = t2.vestir(src)
    despues = vestir(src)
    from PIL import ImageDraw as D
    S2, rec = 8, (24, 14, 80, 84)
    h2 = Image.new("RGB", (2 * (rec[2] - rec[0]) * S2, (rec[3] - rec[1]) * S2 + 24), (46, 46, 56))
    d2 = D.Draw(h2)
    for i, (im, nombre) in enumerate(((antes, "actual"), (despues, "silueta + estrellas"))):
        b = Image.new("RGBA", im.size, (70, 70, 84, 255)); b.alpha_composite(im)
        c = b.convert("RGB").crop(rec)
        h2.paste(c.resize((c.width * S2, c.height * S2), Image.NEAREST), (i * c.width * S2, 24))
        d2.text((i * c.width * S2 + 8, 6), nombre, fill=(255, 230, 120))
    h2.save(PREV / "traje_silueta_detalle.png")
    S = 5
    w = 96 * S
    hoja = Image.new("RGB", (w * 2, 128 * S + 24), (46, 46, 56))
    d = D.Draw(hoja)
    for i, (im, nombre) in enumerate(((antes, "actual"), (despues, "silueta + estrellas"))):
        b = Image.new("RGBA", im.size, (46, 46, 56, 255)); b.alpha_composite(im)
        hoja.paste(b.convert("RGB").resize((w, 128 * S), Image.NEAREST), (i * w, 24))
        d.text((i * w + 8, 6), nombre, fill=(255, 230, 120))
    hoja.save(PREV / "traje_silueta_comparacion.png")
    despues.resize((96 * S, 128 * S), Image.NEAREST).save(PREV / "traje_silueta_x5.png")
    print("colores:", len({tuple(p[:3]) for p in despues.getdata() if p[3]}))


if __name__ == "__main__":
    main()
