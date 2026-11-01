"""Utena con el traje del PNG (saco y pantalón negros, camisa blanca, corbata morada, zapatos negros) sobre las poses del GIF.

Se conserva del GIF la cabeza (pelo, cara, cuernos y antena) y las manos; se quitan las alas, la capa blanca y el top.
El traje se dibuja con polígonos en píxeles nativos (96x128) y se sombrea con la paleta neutra del PNG:
contorno casi negro, base 30, sombra 20, brillo 57 y filo 90; la corbata en tres morados.
Por ahora solo la pose 0 (brazos abiertos). Salida: previews/traje_prueba_pose0.png
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import hojas

HERE = Path(__file__).parent
PREV = HERE / "previews"

OL, J0, J1, J2, J3 = (6, 6, 8), (20, 20, 23), (30, 30, 33), (57, 57, 60), (90, 90, 96)
P0, P1, P2 = (16, 16, 19), (27, 27, 30), (48, 48, 52)            # pantalón (un poco más oscuro que el saco)
T0, T1, T2 = (74, 38, 82), (116, 65, 122), (160, 104, 166)
W, WS = (255, 255, 255), (209, 201, 207)
PIEL = {(255, 225, 215), (250, 184, 167), (237, 143, 138), (200, 87, 97), (206, 96, 104), (98, 73, 101)}


def mascara(pol, size=(96, 128)):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).polygon(pol, fill=255)
    return np.asarray(m) > 0


def borde(m):
    """Píxeles de m con algún vecino (4-conexión) fuera de m."""
    p = np.pad(m, 1)
    fuera = ~p[:-2, 1:-1] | ~p[2:, 1:-1] | ~p[1:-1, :-2] | ~p[1:-1, 2:]
    return m & fuera


def pieza(arr, m, base, sombra, brillo, luz_izq=True, frac_sombra=0.32):
    """Rellena la máscara con base, sombra a la derecha, brillo en el filo superior izquierdo y contorno."""
    ys, xs = np.where(m)
    if not len(xs):
        return
    x0, x1 = xs.min(), xs.max()
    corte = x1 - (x1 - x0) * frac_sombra
    arr[m] = base
    arr[m & (np.arange(96)[None, :] >= corte)] = sombra
    p = np.pad(m, 1)
    filo = m & (~p[:-2, 1:-1] | (~p[1:-1, :-2] if luz_izq else ~p[1:-1, 2:]))
    inner = filo & ~borde(m) if False else filo
    arr[inner] = brillo
    arr[borde(m)] = OL


def pose0():
    fr, _ = hojas.fotogramas()
    src = np.asarray(fr[0]).copy()
    out = np.zeros((128, 96, 4), np.uint8)
    rgb = out[..., :3]

    # --- pantalón: dos piernas en compás abierto desde la cadera hasta los tobillos del GIF
    izq = mascara([(38, 66), (46, 66), (46, 84), (41, 107), (35, 107), (36, 84)])
    der = mascara([(46, 66), (55, 66), (57, 84), (59, 107), (53, 107), (47, 84)])
    for m in (izq, der):
        pieza(rgb, m, P1, P0, P2)
    out[izq | der, 3] = 255
    # pliegue de la raya del pantalón
    for (xa, ya, xb, yb) in ((40, 86, 38, 104), (52, 86, 55, 104)):
        for k in range(yb - ya + 1):
            x = round(xa + (xb - xa) * k / (yb - ya)); y = ya + k
            if (izq | der)[y, x] and not borde(izq | der)[y, x]:
                rgb[y, x] = P2

    # --- zapatos: la silueta de los pies del GIF (filas 108-118) en negro con brillo
    pies = src[108:119]
    mp = pies[..., 3] > 0
    tono = {}
    for y in range(108, 119):
        for x in range(96):
            if src[y, x, 3]:
                c = tuple(src[y, x, :3])
                lum = sum(c) / 3
                rgb[y, x] = OL if lum < 55 else (J1 if lum < 150 else (J2 if lum < 215 else J3))
                out[y, x, 3] = 255
    # --- saco: cuerpo con faldones abiertos bajo el botón
    cuerpo = mascara([(41, 41), (51, 41), (58, 45), (59, 56), (57, 64), (58, 80), (50, 82), (46, 64), (42, 82),
                      (34, 80), (35, 64), (33, 56), (34, 45)])
    pieza(rgb, cuerpo, J1, J0, J2)
    out[cuerpo, 3] = 255
    # bolsillos
    for (x0, x1, y) in ((37, 41, 71), (51, 55, 71)):
        rgb[y, x0:x1 + 1] = J2
        rgb[y + 1, x0:x1 + 1] = OL

    # --- camisa en V con cuello y corbata
    camisa = mascara([(42, 41), (50, 41), (49, 50), (47, 61), (45, 61), (43, 50)])
    rgb[camisa] = W
    rgb[camisa & (np.arange(96)[None, :] >= 48)] = WS
    out[camisa, 3] = 255
    # solapas: filo de brillo junto a la camisa y muesca
    for y in range(42, 61):
        fila = np.where(camisa[y])[0]
        if len(fila):
            xl, xr = fila.min() - 1, fila.max() + 1
            rgb[y, xl] = J3 if y < 52 else J2
            rgb[y, xr] = J2
            if y < 50:
                rgb[y, xl - 1] = J2
    for (x, y) in ((41, 47), (40, 48), (52, 47), (53, 48)):
        rgb[y, x] = OL
    # puntas del cuello
    for (x, y) in ((42, 41), (43, 42), (42, 42), (43, 43), (50, 41), (49, 42), (50, 42), (49, 43)):
        rgb[y, x] = W; out[y, x, 3] = 255
    rgb[43, 42] = WS; rgb[43, 50] = WS
    # corbata: nudo, cuerpo y punta
    corb = mascara([(45, 42), (47, 42), (47, 44), (48, 55), (46, 60), (44, 55), (45, 44)])
    rgb[corb] = T1
    rgb[corb & (np.arange(96)[None, :] >= 47)] = T0
    rgb[42:44, 45] = T2
    for y in range(46, 55, 3):
        rgb[y, 45] = T2
    rgb[44, 45:48] = T0
    rgb[borde(corb) & (np.arange(128)[:, None] >= 45)] = T0
    out[corb, 3] = 255
    # botón
    rgb[62, 46] = J3; rgb[63, 46] = OL

    # --- mangas (sobre el cuerpo) con puño blanco
    m_izq = mascara([(35, 44), (40, 45), (38, 58), (33, 67), (27, 66), (31, 57)])
    m_der = mascara([(52, 45), (58, 45), (61, 53), (67, 58), (65, 63), (58, 59), (55, 55)])
    pieza(rgb, m_izq, J1, J0, J2)
    pieza(rgb, m_der, J1, J0, J2, frac_sombra=0.25)
    out[m_izq | m_der, 3] = 255
    for (x, y) in ((27, 66), (28, 66), (29, 67), (30, 67), (31, 67), (28, 67), (32, 67)):
        rgb[y, x] = W if x < 31 else WS; out[y, x, 3] = 255
    for (x, y) in ((65, 59), (66, 60), (66, 61), (65, 62), (64, 63), (65, 60), (65, 61)):
        rgb[y, x] = W if y < 62 else WS; out[y, x, 3] = 255

    # --- manos del GIF
    for (x0, x1, y0, y1) in ((20, 33, 66, 74), (64, 78, 58, 67)):
        for y in range(y0, y1):
            for x in range(x0, x1):
                c = tuple(src[y, x, :3])
                if src[y, x, 3] and c in PIEL:
                    rgb[y, x] = c; out[y, x, 3] = 255

    # --- cabeza del GIF (pelo, cara, cuernos y antena) hasta la barbilla
    cab = src[:41]
    m = cab[..., 3] > 0
    out[:41][m] = cab[m]
    return Image.fromarray(out, "RGBA"), fr[0]


def main():
    PREV.mkdir(exist_ok=True)
    nuevo, orig = pose0()
    S = 5
    w = 96 * S
    hoja = Image.new("RGB", (w * 2 + 380, 128 * S), (46, 46, 56))
    for i, im in enumerate((orig, nuevo)):
        b = Image.new("RGBA", im.size, (46, 46, 56, 255)); b.alpha_composite(im)
        hoja.paste(b.convert("RGB").resize((w, 128 * S), Image.NEAREST), (i * w, 0))
    ref = Image.open(HERE.parent / "Utena.PNG").convert("RGB")
    ref.thumbnail((370, 128 * S))
    hoja.paste(ref, (2 * w + 5, 0))
    hoja.save(PREV / "traje_prueba_pose0.png")
    nuevo.resize((96 * S, 128 * S), Image.NEAREST).save(PREV / "traje_prueba_pose0_x5.png")
    print("colores:", len({tuple(p[:3]) for p in nuevo.getdata() if p[3]}))


if __name__ == "__main__":
    main()
