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


GEO = {
    "suelto": dict(
        izq=[(38, 66), (46, 66), (46, 84), (41, 107), (35, 107), (36, 84)],
        der=[(46, 66), (55, 66), (57, 84), (59, 107), (53, 107), (47, 84)],
        cuerpo=[(41, 41), (51, 41), (58, 45), (59, 56), (57, 64), (58, 80), (50, 82), (46, 64), (42, 82),
                (34, 80), (35, 64), (33, 56), (34, 45)],
        m_izq=[(35, 44), (40, 45), (38, 58), (33, 67), (27, 66), (31, 57)],
        m_der=[(52, 45), (58, 45), (61, 53), (67, 58), (65, 63), (58, 59), (55, 55)],
        bolsillos=((37, 41, 71), (51, 55, 71)), pliegues=((40, 86, 38, 104), (52, 86, 55, 104))),
    "entallado": dict(
        izq=[(39, 66), (46, 66), (46, 84), (41, 107), (36, 107), (37, 84)],
        der=[(46, 66), (54, 66), (56, 84), (58, 107), (53, 107), (47, 84)],
        cuerpo=[(41, 41), (51, 41), (57, 44), (58, 49), (57, 55), (53, 62), (56, 70), (56, 78), (50, 80), (46, 64),
                (42, 80), (36, 78), (36, 70), (39, 62), (35, 55), (34, 49), (35, 44)],
        m_izq=[(35, 44), (39, 45), (37, 57), (32, 67), (28, 66), (32, 56)],
        m_der=[(53, 45), (57, 45), (60, 53), (66, 58), (65, 62), (58, 58), (55, 54)],
        bolsillos=((38, 41, 70), (51, 54, 70)), pliegues=((41, 86, 39, 104), (51, 86, 55, 104))),
    "muy_ajustado": dict(
        izq=[(38, 63), (46, 63), (46, 78), (43, 90), (40, 107), (36, 107), (37, 90), (37, 76)],
        der=[(46, 63), (55, 63), (56, 76), (56, 90), (58, 107), (54, 107), (50, 90), (47, 78)],
        cuerpo=[(41, 41), (51, 41), (56, 44), (57, 49), (55, 55), (52, 61), (54, 66), (54, 71), (50, 73), (46, 63),
                (42, 73), (38, 71), (38, 66), (40, 61), (37, 55), (35, 49), (36, 44)],
        m_izq=[(36, 44), (39, 45), (37, 57), (32, 67), (29, 66), (33, 56)],
        m_der=[(53, 45), (56, 45), (59, 53), (66, 58), (65, 61), (58, 57), (55, 54)],
        bolsillos=(), pliegues=((40, 80, 38, 104), (52, 80, 55, 104))),
}


def pose0(estilo="suelto"):
    g = GEO[estilo]
    fr, _ = hojas.fotogramas()
    src = np.asarray(fr[0]).copy()
    out = np.zeros((128, 96, 4), np.uint8)
    rgb = out[..., :3]

    # --- pantalón: dos piernas en compás abierto desde la cadera hasta los tobillos del GIF
    izq, der = mascara(g["izq"]), mascara(g["der"])
    for m in (izq, der):
        pieza(rgb, m, P1, P0, P2)
    out[izq | der, 3] = 255
    # pliegue de la raya del pantalón
    for (xa, ya, xb, yb) in g["pliegues"]:
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
    cuerpo = mascara(g["cuerpo"])
    pieza(rgb, cuerpo, J1, J0, J2)
    out[cuerpo, 3] = 255
    # bolsillos
    for (x0, x1, y) in g["bolsillos"]:
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
    m_izq, m_der = mascara(g["m_izq"]), mascara(g["m_der"])
    pieza(rgb, m_izq, J1, J0, J2)
    pieza(rgb, m_der, J1, J0, J2, frac_sombra=0.25)
    out[m_izq | m_der, 3] = 255
    # puños blancos: las dos últimas filas de la manga izquierda y las dos últimas columnas de la derecha
    yy = np.arange(128)[:, None]; xx = np.arange(96)[None, :]
    # (el puño son los píxeles más lejanos a lo largo del brazo: abajo-izquierda en el izquierdo, derecha-abajo en el derecho)
    pr_i = yy * 0.92 - xx * 0.4
    pu = m_izq & (pr_i >= pr_i[m_izq].max() - 1.7)
    rgb[pu] = W; rgb[pu & (xx >= np.where(pu.any(0))[0].max() - 1)] = WS
    pr_d = xx * 0.88 + yy * 0.48
    pd = m_der & (pr_d >= pr_d[m_der].max() - 1.7)
    rgb[pd] = W; rgb[pd & (yy >= np.where(pd.any(1))[0].max())] = WS

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
    S = 5
    w = 96 * S
    estilos = ["suelto", "entallado", "muy_ajustado"]
    figuras = [pose0(e)[0] for e in estilos]
    orig = pose0("suelto")[1]
    from PIL import ImageDraw
    hoja = Image.new("RGB", (w * 4 + 380, 128 * S + 24), (46, 46, 56))
    d = ImageDraw.Draw(hoja)
    for i, (im, nombre) in enumerate(zip([orig] + figuras, ["GIF original", "prueba anterior", "1 entallado", "2 muy ajustado"])):
        b = Image.new("RGBA", im.size, (46, 46, 56, 255)); b.alpha_composite(im)
        hoja.paste(b.convert("RGB").resize((w, 128 * S), Image.NEAREST), (i * w, 24))
        d.text((i * w + 8, 6), nombre, fill=(255, 230, 120))
    ref = Image.open(HERE.parent / "Utena.PNG").convert("RGB")
    ref.thumbnail((370, 128 * S))
    hoja.paste(ref, (4 * w + 5, 24)); d.text((4 * w + 10, 6), "PNG", fill=(255, 230, 120))
    hoja.save(PREV / "traje_ajuste_opciones.png")
    S2 = 7
    rec = (24, 36, 80, 120)
    h2 = Image.new("RGB", (3 * (rec[2] - rec[0]) * S2, (rec[3] - rec[1]) * S2 + 24), (46, 46, 56))
    d2 = ImageDraw.Draw(h2)
    for i, (im, nombre) in enumerate(zip(figuras, ["prueba anterior", "1 entallado", "2 muy ajustado"])):
        b = Image.new("RGBA", im.size, (70, 70, 84, 255)); b.alpha_composite(im)
        c = b.convert("RGB").crop(rec)
        h2.paste(c.resize((c.width * S2, c.height * S2), Image.NEAREST), (i * c.width * S2, 24))
        d2.text((i * c.width * S2 + 8, 6), nombre, fill=(255, 230, 120))
    h2.save(PREV / "traje_ajuste_detalle.png")
    for e, im in zip(estilos, figuras):
        im.resize((96 * S, 128 * S), Image.NEAREST).save(PREV / f"traje_{e}_x5.png")
        print(e, "colores:", len({tuple(p[:3]) for p in im.getdata() if p[3]}))


if __name__ == "__main__":
    main()
