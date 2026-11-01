"""Poses del GIF de Utena con el traje, con los brazos dibujados a mano siguiendo el original.

Análisis del original (coordenadas a tamaño real, 96x128):
  * fotogramas 0-5: brazos abiertos (traje3, sin cambios) y globo de diálogo
  * fotograma 6 (sobresalto): se abraza; el antebrazo que viene del hombro derecho baja en diagonal hasta la mano en la
    cadera izquierda (x 29-34, filas 68-73) y el otro llega a la mano en la cadera derecha (x 58-64, filas 65-70)
  * fotogramas 7-29: una mano en la parte alta del pecho, al lado derecho (x 45-50, filas 52-57), con el antebrazo
    cruzando desde el codo izquierdo; la otra mano abajo, delante de la entrepierna (x 41-46, filas 70-79), con el
    antebrazo bajando recto (x 45-49) desde el codo derecho. El 7 y el 8 son iguales y el 9 es el 8 con el cuerpo 1 px
    a la derecha y los pies quietos (el balanceo).
Las mangas se trazan como segmentos (brazo y antebrazo) con contorno, luz arriba, sombra abajo y puño blanco; las manos son
pequeñas plantillas con la paleta de piel del GIF. El pantalón, los zapatos y el torso son los de poses.py.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import hojas
import poses as p1
import traje as t1
import traje3 as t3

HERE = Path(__file__).parent
PREV = HERE / "previews"
OL, J0, J1, J2, J3 = t3.OL, t3.J0, t3.J1, t3.J2, t3.J3
W, WS = t3.W, t3.WS
YY, XX = np.mgrid[0:128, 0:96]
PIEL = {"G": (255, 225, 215), "O": (250, 184, 167), "N": (237, 143, 138), "H": (98, 73, 101), "Z": (206, 96, 104)}

# plantillas de mano (la primera fila o columna es la que toca el puño)
MANO_ABAJO = ["OGGGO", "GGGGN", "OGGGN", "OGHGN", "NGHGH", "NGHGH", ".NHN."]   # dedos hacia abajo (7 filas, como el original)
MANO_PECHO = ["...OGN", "..OGGN", ".OGGON", "OGGON.", "NONH.."]               # palma sobre el pecho, dedos hacia el hombro
MANO_CADERA_IZQ = [".OGGO", "OGGGO", "NGGON", ".NHNH"]                     # agarrando la cadera, dedos hacia la izquierda
MANO_CADERA_DER = [r[::-1] for r in MANO_CADERA_IZQ]


def segmento(p0, p1, r0, r1):
    """Máscara de un segmento con radio que pasa de r0 a r1 (extremos redondeados)."""
    (x0, y0), (x1, y1) = p0, p1
    vx, vy = x1 - x0, y1 - y0
    L2 = vx * vx + vy * vy
    t = np.clip(((XX - x0) * vx + (YY - y0) * vy) / L2, 0, 1)
    d = np.hypot(XX - (x0 + t * vx), YY - (y0 + t * vy))
    return d <= r0 + (r1 - r0) * t, t


def manga(rgb, out, brazo, antebrazo, codo_pliegue=None, luz="arriba"):
    """Dibuja una manga (brazo + antebrazo). `luz` = lado del antebrazo con el filo de luz más claro
    ('arriba' o 'izq'), para que se separe del saco que tiene detrás."""
    mb, _ = segmento(*brazo)
    ma, ta = segmento(*antebrazo)
    m = mb | ma
    rgb[m] = J1
    p = np.pad(m, 1)
    arriba = m & ~p[:-2, 1:-1]
    abajo = m & ~p[2:, 1:-1]
    rgb[abajo] = J0
    rgb[arriba] = J2
    # sombra del antebrazo en el lado de abajo, una fila hacia dentro
    pa = np.pad(ma, 1)
    rgb[ma & pa[2:, 1:-1] & ~np.pad(ma, 2)[4:, 2:-2]] = J0
    if codo_pliegue:
        for (x, y) in codo_pliegue:
            rgb[y, x] = J0
    pa = np.pad(ma, 1)
    filo = ma & (~pa[:-2, 1:-1] if luz == "arriba" else ~pa[1:-1, :-2])
    filo = np.pad(filo, 1)[:-2, 1:-1] & ma if luz == "arriba" else np.pad(filo, 1)[1:-1, :-2] & ma   # una fila/columna hacia dentro
    rgb[filo & ~t1.borde(ma)] = J3
    rgb[t1.borde(m)] = OL
    out[m, 3] = 255
    # puño: los últimos ~1,5 px del antebrazo junto a la muñeca
    largo = np.hypot(antebrazo[1][0] - antebrazo[0][0], antebrazo[1][1] - antebrazo[0][1])
    puno = ma & (ta >= 1 - 1.6 / largo) & ~t1.borde(ma)
    rgb[puno] = W
    rgb[puno & abajo] = WS
    return m


def mano(rgb, out, plantilla, x, y):
    for j, fila in enumerate(plantilla):
        for i, ch in enumerate(fila):
            if ch != ".":
                rgb[y + j, x + i] = PIEL[ch]
                out[y + j, x + i, 3] = 255


def base(src, src0, dx, dy, cfg_piernas):
    """Pantalón y zapatos del fotograma + torso de la pose 0 desplazado (dx, dy)."""
    out = np.zeros((128, 96, 4), np.uint8)
    p1.pantalon(src, out, cfg_piernas)
    p1.zapatos(src, out)
    torso = np.array(t3.vestir(src0, solo_torso=True))
    torso = np.roll(np.roll(torso, dy, 0), dx, 1)
    mt = torso[..., 3] > 0
    out[mt] = torso[mt]
    return out


def cabeza(src, out, dx, dy):
    rgb = out[..., :3]
    cy = 41 + dy
    mk = src[:cy, :, 3] > 0
    out[:cy][mk] = src[:cy][mk]
    for (cx, sy) in ((53 + dx, 22 + dy), (35 + dx, 23 + dy)):
        for (ex, ey) in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            rgb[sy + ey, cx + ex] = p1.S1
        rgb[sy, cx] = p1.S2


def pose_sobresalto(src, src0):
    dx, dy = -2, 3
    out = base(src, src0, dx, dy, p1.POSES[6])
    rgb = out[..., :3]
    # brazo del hombro izquierdo: baja por el costado y cruza hacia la cadera derecha (queda detrás)
    manga(rgb, out, ((34, 50), (34, 61), 2.6, 2.3), ((35, 63), (62, 67), 2.2, 1.6), codo_pliegue=[(36, 61)])
    # brazo del hombro derecho: baja por el costado y cruza hacia la cadera izquierda (delante)
    manga(rgb, out, ((54, 50), (55, 59), 2.6, 2.3), ((54, 60), (34, 70), 2.2, 1.6), codo_pliegue=[(53, 59)])
    mano(rgb, out, MANO_CADERA_IZQ, 29, 69)
    mano(rgb, out, MANO_CADERA_DER, 63, 66)
    cabeza(src, out, dx, dy)
    return Image.fromarray(out, "RGBA")


def pose_tapandose(src, src0, extra=0):
    dx, dy = -4 + extra, 4
    out = base(src, src0, dx, dy, p1.POSES[8])
    rgb = out[..., :3]
    e = extra
    # brazo derecho: baja por el costado, el antebrazo baja recto hacia el centro; la mano queda delante de la cadera
    manga(rgb, out, ((52 + e, 50), (50 + e, 58), 2.6, 2.3), ((50 + e, 59), (44 + e, 69), 2.2, 1.6), codo_pliegue=[(49 + e, 58)], luz="izq")
    # brazo izquierdo: baja por el costado y el antebrazo cruza el pecho; la mano queda en la parte alta del pecho
    manga(rgb, out, ((32 + e, 50), (32 + e, 57), 2.6, 2.3), ((33 + e, 58), (45 + e, 55), 2.2, 1.6), codo_pliegue=[(34 + e, 57)])
    mano(rgb, out, MANO_PECHO, 45 + e, 51)
    mano(rgb, out, MANO_ABAJO, 41 + e, 70)
    cabeza(src, out, dx, dy)
    return Image.fromarray(out, "RGBA")


def todas():
    fr, _ = hojas.fotogramas()
    A = [np.asarray(f).copy() for f in fr]
    res = {0: t3.vestir(A[0])}
    res[5] = p1.con_globo(res[0], fr, 5)
    res[6] = pose_sobresalto(A[6], A[0])
    res[7] = pose_tapandose(A[7], A[0])
    res[8] = pose_tapandose(A[8], A[0])
    res[9] = pose_tapandose(A[9], A[0], extra=1)
    return res, fr


def hoja(res, fr, claves, ruta, S=4, rec=None, titulo=""):
    w, h = (rec[2] - rec[0]) * S if rec else 96 * S, (rec[3] - rec[1]) * S if rec else 128 * S
    im = Image.new("RGB", (len(claves) * (w + 8), 2 * (h + 18) + 6), (40, 40, 50))
    d = ImageDraw.Draw(im)
    for i, k in enumerate(claves):
        for j, src in enumerate((fr[k], res[k])):
            c = src.crop(rec) if rec else src
            b = Image.new("RGBA", c.size, (70, 70, 84, 255)); b.alpha_composite(c)
            im.paste(b.convert("RGB").resize((w, h), Image.NEAREST), (i * (w + 8), j * (h + 18) + 18))
            d.text((i * (w + 8) + 4, j * (h + 18) + 3), f"{'original' if j == 0 else 'con traje'} - fotograma {k + 1}", fill=(255, 230, 120))
    im.save(ruta)


def verificar(res, fr, claves, ruta, S=10, rec=(20, 40, 72, 84)):
    """Versión con traje con el contorno (cian) de la piel de las manos del original, para comprobar la posición."""
    from poses import es_piel
    paneles = []
    for k in claves:
        a = np.asarray(fr[k])
        piel = np.zeros((128, 96), bool)
        for y in range(rec[1], rec[3]):
            for x in range(rec[0], rec[2]):
                if a[y, x, 3] and es_piel(a[y, x]):
                    piel[y, x] = True
        piel[:62 if k >= 7 else 64, 36:56] = piel[:62 if k >= 7 else 64, 36:56] & (np.arange(96)[None, 36:56] >= 44) if k >= 7 else piel[:64, 36:56] & False
        b = Image.new("RGBA", res[k].size, (70, 70, 84, 255)); b.alpha_composite(res[k])
        c = b.convert("RGB").crop(rec).resize(((rec[2] - rec[0]) * S, (rec[3] - rec[1]) * S), Image.NEAREST)
        d = ImageDraw.Draw(c)
        bd = t1.borde(piel)
        for y, x in zip(*np.where(bd)):
            if rec[0] <= x < rec[2] and rec[1] <= y < rec[3]:
                d.rectangle(((x - rec[0]) * S, (y - rec[1]) * S, (x - rec[0] + 1) * S - 1, (y - rec[1] + 1) * S - 1), outline=(0, 255, 255))
        paneles.append(c)
    im = Image.new("RGB", (sum(p.width for p in paneles) + 8 * len(paneles), paneles[0].height), (30, 30, 40))
    x = 0
    for p in paneles:
        im.paste(p, (x, 0)); x += p.width + 8
    im.save(ruta)


def main():
    PREV.mkdir(exist_ok=True)
    res, fr = todas()
    verificar(res, fr, (6, 7, 9), "/projects/sandbox/tmp/utena/verif.png")
    hoja(res, fr, (0, 5, 6, 7, 9), PREV / "poses2_hoja.png")
    hoja(res, fr, (6, 7, 9), PREV / "poses2_detalle.png", S=8, rec=(20, 14, 72, 120))
    for k in (6, 7, 9):
        print(k, "colores", len({tuple(p[:3]) for p in res[k].getdata() if p[3]}))


if __name__ == "__main__":
    main()
