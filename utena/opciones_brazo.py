"""Tres opciones para que el antebrazo no se vea delgado (fotograma 7 y, de paso, el 8), frente a la versión actual.

  1 grosor de la pose 1: antebrazo de 6 px casi hasta el puño (5 en la muñeca)
  2 como la 1 y además el codo 1 px más ancho, con un pliegue de tela
  3 grosor actual, pero donde la manga pasa por delante del saco el contorno es una sombra gris en vez de negro
Salida: previews/opciones_brazo.png (y el grosor medido de cada antebrazo en la consola).
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import hojas
import poses as p1
import poses2 as p2
import poses3 as p3
import traje as t1
import traje3 as t3

HERE = Path(__file__).parent
PREV = HERE / "previews"
OL, J0, J1, J2, J3 = t3.OL, t3.J0, t3.J1, t3.J2, t3.J3
W, WS = t3.W, t3.WS

OPCIONES = {
    "actual": dict(r_ante=(2.7, 2.2), codo=0.0, suave=False),
    "1 grosor de la pose 1": dict(r_ante=(3.1, 2.6), codo=0.0, suave=False),
    "2 codo holgado": dict(r_ante=(3.1, 2.6), codo=1.0, suave=False),
    "3 contorno suave": dict(r_ante=(2.7, 2.2), codo=0.0, suave=True),
}


def manga(rgb, out, hombro, codo, muneca, luz="arriba", r_ante=(2.7, 2.2), r_codo=0.0, suave=False, otras=None):
    mb, _ = p2.segmento(hombro, codo, *p3.R_BRAZO)
    ma, ta = p2.segmento(codo, muneca, *r_ante)
    m = mb | ma
    if r_codo:
        YY, XX = np.mgrid[0:128, 0:96]
        m |= np.hypot(XX - codo[0], YY - codo[1]) <= p3.R_BRAZO[1] + r_codo
    debajo = out[..., 3] > 0                                   # lo que ya había (saco, otras mangas)
    rgb[m] = J1
    pm = np.pad(m, 1)
    arriba, abajo = m & ~pm[:-2, 1:-1], m & ~pm[2:, 1:-1]
    rgb[abajo] = J0
    rgb[arriba] = J2
    pa = np.pad(ma, 1)
    rgb[ma & pa[2:, 1:-1] & ~np.pad(ma, 2)[4:, 2:-2]] = J0
    rgb[codo[1], codo[0] + (1 if codo[0] < 46 else -1)] = J0
    if r_codo:                                                 # pliegue de tela en el codo
        for d in (-1, 1):
            rgb[codo[1] + d, codo[0]] = J0
    filo = ma & (~pa[:-2, 1:-1] if luz == "arriba" else ~pa[1:-1, :-2])
    filo = np.pad(filo, 1)[:-2, 1:-1] & ma if luz == "arriba" else np.pad(filo, 1)[1:-1, :-2] & ma
    rgb[filo & ~t1.borde(ma)] = J3
    bd = t1.borde(m)
    if suave:
        # el contorno es negro hacia el fondo y hacia otras mangas; gris hacia el saco
        p = np.pad(debajo & ~(otras if otras is not None else False) & ~m, 1)
        junto_saco = p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
        pf = np.pad(~debajo & ~m, 1)
        junto_fondo = pf[:-2, 1:-1] | pf[2:, 1:-1] | pf[1:-1, :-2] | pf[1:-1, 2:]
        rgb[bd] = OL
        rgb[bd & junto_saco & ~junto_fondo] = J0
    else:
        rgb[bd] = OL
    out[m, 3] = 255
    largo = np.hypot(muneca[0] - codo[0], muneca[1] - codo[1])
    puno = ma & (ta >= 1 - 1.6 / largo) & ~t1.borde(ma)
    rgb[puno] = W
    rgb[puno & abajo] = WS
    return m


def armar(src, src0, dx, dy, brazos, manos, cfg, sin_panuelo=False):
    out = np.zeros((128, 96, 4), np.uint8)
    rgb = out[..., :3]
    p3.pantalon(src, out, dx, dy)
    p1.zapatos(src, out)
    torso = np.array(t3.vestir(src0, solo_torso=True))
    torso = np.roll(np.roll(torso, dy, 0), dx, 1)
    mt = torso[..., 3] > 0
    out[mt] = torso[mt]
    if sin_panuelo:
        for (x, y) in ((53, 52), (54, 51), (54, 52), (55, 52), (53, 53), (54, 53), (55, 53), (56, 53)):
            rgb[y + dy, x + dx] = J1
    hechas = np.zeros((128, 96), bool)
    mangas = []
    for b in brazos:
        mk = manga(rgb, out, *b, r_ante=cfg["r_ante"], r_codo=cfg["codo"], suave=cfg["suave"], otras=hechas)
        hechas |= mk
        mangas.append(mk)
    for (pl, x, y) in manos:
        p2.mano(rgb, out, pl, x, y)
    p3.limpiar(out, 44 + dy, 108)
    p2.cabeza(src, out, dx, dy)
    return Image.fromarray(out, "RGBA"), mangas


def sobresalto(A, cfg):
    dx, dy = -2, 3
    hi, hd = (36 + dx, 48 + dy), (56 + dx, 48 + dy)
    brazos = [(hi, (34, 62), (61, 67)), (hd, (55, 60), (34, 70))]
    manos = [(p3.MANO_IZQ, 26, 68), (p3.MANO_DER, 62, 65)]
    return armar(A[6], A[0], dx, dy, brazos, manos, cfg), brazos


def tapandose(A, cfg):
    dx, dy = -4, 4
    hi, hd = (36 + dx, 48 + dy), (56 + dx, 48 + dy)
    brazos = [(hd, (52, 59), (45, 69), "izq"), (hi, (31, 59), (44, 55))]
    manos = [(p3.MANO_PECHO, 44, 51), (p3.MANO_ABAJO, 41, 70)]
    return armar(A[7], A[0], dx, dy, brazos, manos, cfg, sin_panuelo=True), brazos


def grosor(m, p0, p1, t=0.5):
    (x0, y0), (x1, y1) = p0, p1
    vx, vy = x1 - x0, y1 - y0
    L = np.hypot(vx, vy)
    nx, ny = -vy / L, vx / L
    cx, cy = x0 + vx * t, y0 + vy * t
    n = sum(1 for s in np.arange(-6, 6.01, 0.25)
            if m[int(round(cy + ny * s)), int(round(cx + nx * s))])
    return round(n * 0.25, 1)


def main():
    PREV.mkdir(exist_ok=True)
    fr, _ = hojas.fotogramas()
    A = [np.asarray(f).copy() for f in fr]
    S = 9
    recs = {7: (20, 42, 74, 84), 8: (24, 42, 64, 84)}
    paneles = {7: [], 8: []}
    for nombre, cfg in OPCIONES.items():
        (im7, m7), b7 = sobresalto(A, cfg)
        (im8, m8), b8 = tapandose(A, cfg)
        g = [grosor(m7[0], b7[0][1], b7[0][2]), grosor(m7[1], b7[1][1], b7[1][2])]
        print(f"{nombre:24s} antebrazos del fotograma 7 a mitad: {g[0]} y {g[1]} px")
        for k, im in ((7, im7), (8, im8)):
            b = Image.new("RGBA", im.size, (70, 70, 84, 255)); b.alpha_composite(im)
            rec = recs[k]
            paneles[k].append((nombre, b.convert("RGB").crop(rec).resize(((rec[2] - rec[0]) * S, (rec[3] - rec[1]) * S), Image.NEAREST)))
    w7 = paneles[7][0][1].width; w8 = paneles[8][0][1].width; h = paneles[7][0][1].height
    hoja = Image.new("RGB", (len(OPCIONES) * (w7 + 8), 2 * (h + 22)), (30, 30, 40))
    d = ImageDraw.Draw(hoja)
    for i, ((n, p7), (_, p8)) in enumerate(zip(paneles[7], paneles[8])):
        x = i * (w7 + 8)
        d.text((x + 6, 5), f"{n} - fotograma 7", fill=(255, 230, 120))
        hoja.paste(p7, (x, 22))
        d.text((x + 6, h + 27), f"{n} - fotograma 8", fill=(255, 230, 120))
        hoja.paste(p8, (x + (w7 - w8) // 2, h + 44))
    hoja.save(PREV / "opciones_brazo.png")
    print(hoja.size)


if __name__ == "__main__":
    main()
