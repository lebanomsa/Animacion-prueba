"""Poses del GIF de Utena con el traje, con la estructura de la pose 1 (traje3) en todas.

El original solo da el movimiento:
  * piernas: la línea central de cada pierna del original en las filas 84-106 (más el desplazamiento que ya tiene la pose 1
    del traje respecto de la pose 1 original) y la posición de los zapatos. El ancho de cada fila sale del perfil de la
    pose 1 del traje (9 px en la cadera, 11 en la rodilla, 6 en el tobillo), comprimido si el cuerpo baja (fotogramas 7+).
  * brazos: la posición de hombros, codos y muñecas. El grosor es el de las mangas de la pose 1 (6 px el brazo, 5 el
    antebrazo y 4 en el puño), con los hombros en el mismo punto que en la pose 1 (desplazado con el cuerpo).
  * manos: del tamaño de las de la pose 1 (unos 8x6 px) y con su paleta, en las posiciones del original.
El torso es el de la pose 1 desplazado igual que la cabeza, y la cabeza (con su expresión) es la de cada fotograma.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import hojas
import poses as p1
import poses2 as p2
import traje as t1
import traje3 as t3

HERE = Path(__file__).parent
PREV = HERE / "previews"
OL, J0, J1, J2, J3 = t3.OL, t3.J0, t3.J1, t3.J2, t3.J3
P0, P1, P2 = t3.P0, t3.P1, t3.P2
W, WS = t3.W, t3.WS
YY, XX = np.mgrid[0:128, 0:96]
FILAS = (84, 90, 96, 102, 106)

# ---- perfil del pantalón de la pose 1 del traje (de los polígonos de traje3) -----------------------------------------
# (fila, centro, medio ancho) en la pose 1
PERFIL = {
    "izq": [(66, 42.0, 4.5), (84, 41.0, 5.5), (107, 38.5, 3.0)],
    "der": [(66, 50.5, 4.5), (84, 52.0, 5.5), (107, 55.5, 3.0)],
}


def interp(tabla, y):
    ys = [t[0] for t in tabla]
    return [float(np.interp(y, ys, [t[i] for t in tabla])) for i in (1, 2)]


def centros_original(src):
    """Centro de cada pierna del original en las FILAS (medias negras), como {fila: (izq, der)}."""
    out = {}
    for y in FILAS:
        xs = [x for x in range(20, 76) if src[y, x, 3] and p1.lum(src[y, x]) < 84]
        tr, s, prev = [], None, None
        for x in xs:
            if s is None:
                s = x
            elif x != prev + 1:
                tr.append((s, prev)); s = x
            prev = x
        if s is not None:
            tr.append((s, prev))
        tr = [t for t in tr if t[1] - t[0] >= 1]
        if len(tr) >= 2:
            out[y] = ((tr[0][0] + tr[0][1]) / 2, (tr[-1][0] + tr[-1][1]) / 2)
    return out


C0 = None


def pantalon(src, out, dx, dy):
    """Pantalón con el perfil de la pose 1, siguiendo las piernas del fotograma."""
    global C0
    if C0 is None:
        fr, _ = hojas.fotogramas()
        C0 = centros_original(np.asarray(fr[0]))
    cf = centros_original(src)
    rgb = out[..., :3]
    cadera = 66 + dy
    mascaras = []
    for i, lado in enumerate(("izq", "der")):
        # centro: fila -> original del fotograma + (traje pose 1 - original pose 1)
        pts = [(cadera, PERFIL[lado][0][1] + dx)]
        for y in FILAS:
            if y in cf and y in C0:
                c_traje0, _ = interp(PERFIL[lado], y)
                pts.append((y, cf[y][i] + (c_traje0 - C0[y][i])))
        pts.append((107, pts[-1][1]))
        # línea central suave: parábola por los puntos (sin escalones de una fila a otra)
        coef = np.polyfit([p[0] for p in pts], [p[1] for p in pts], 2)
        filas = np.arange(cadera, 108)
        cen = np.polyval(coef, filas)
        bordes = []
        for y, c in zip(filas, cen):
            y_eq = 66 + (y - cadera) * (107 - 66) / (107 - cadera)        # fila equivalente en la pose 1
            _, hw = interp(PERFIL[lado], y_eq)
            bordes.append((c - hw, c + hw))
        b0 = np.array([int(np.floor(b[0] + 0.5)) for b in bordes])
        b1 = np.array([int(np.floor(b[1] + 0.5)) - 1 for b in bordes])
        for b in (b0, b1):                                                 # mediana de 3 filas: quita picos sueltos
            b[1:-1] = np.median(np.stack([b[:-2], b[1:-1], b[2:]]), axis=0).astype(int)
        mk = np.zeros((128, 96), bool)
        for y, x0, x1 in zip(filas, b0, b1):
            mk[y, max(x0, 0):min(x1, 95) + 1] = True
        pts = [(int(y), float(c)) for y, c in zip(filas, cen)]
        mascaras.append((mk, pts, cadera))
    # la pierna izquierda va detrás; la derecha delante con su contorno completo
    for i, (mk, pts, cad) in enumerate(mascaras):
        rgb[mk] = P1
        out[mk, 3] = 255
        for y in range(cad, 108):
            xs = np.where(mk[y])[0]
            if len(xs) < 4:
                continue
            rgb[y, xs.max() - 1 if i == 0 else xs.min() + 1] = P0           # sombra interior
            y_eq = 66 + (y - cad) * (107 - 66) / (107 - cad)
            if y_eq >= 84:                                                  # raya del pantalón
                c = float(np.interp(y, [p[0] for p in pts], [p[1] for p in pts]))
                rgb[y, int(round(c)) + (-1 if i == 0 else 0)] = P2
            if abs(y_eq - 90) < 0.5:                                       # pliegue de rodilla
                rgb[y, xs.min() + 1 if i == 0 else xs.max() - 1] = P2
        rgb[t1.borde(mk)] = OL
    return [m[0] for m in mascaras]


# ---- manos con el tamaño y la paleta de las de la pose 1 -------------------------------------------------------------
MANO_IZQ = [".OOGGO..", "OGGGGGO.", "GGOGNGGN", "HOGNOGHN", ".HONGN..", "..H.H..."]        # dedos a la izquierda
MANO_DER = [r[::-1] for r in MANO_IZQ]
MANO_PECHO = ["..OGGGO.", ".OGGGGGN", "OGGOGGON", "NOGNOGH.", ".NHNH..."]                 # palma en el pecho, dedos a la derecha
MANO_ABAJO = [".OGGO.", "OGGGGO", "OGGGGN", "GGOGGN", "NGHGHN", "NGHGHN", ".NHNH.", "..H.H."]   # dedos hacia abajo

R_BRAZO = (3.0, 2.8)        # radios de la pose 1: brazo de 6 px
R_ANTEBRAZO = (3.1, 2.6)    # antebrazo de 6 px (como la pose 1) que se estrecha a 5 en el puño


def manga(rgb, out, hombro, codo, muneca, luz="arriba"):
    return p2.manga(rgb, out, (hombro, codo, *R_BRAZO), (codo, muneca, *R_ANTEBRAZO),
                    codo_pliegue=[(codo[0] + (1 if codo[0] < 46 else -1), codo[1])], luz=luz)


def armar(src, src0, dx, dy, brazos, manos, sin_panuelo=False):
    out = np.zeros((128, 96, 4), np.uint8)
    rgb = out[..., :3]
    piernas = pantalon(src, out, dx, dy)
    p1.zapatos(src, out)
    torso = np.array(t3.vestir(src0, solo_torso=True))
    torso = np.roll(np.roll(torso, dy, 0), dx, 1)
    mt = torso[..., 3] > 0
    out[mt] = torso[mt]
    if sin_panuelo:                                    # el brazo lo tapa casi entero: se quita para que no quede un punto suelto
        for (x, y) in ((53, 52), (54, 51), (54, 52), (55, 52), (53, 53), (54, 53), (55, 53), (56, 53)):
            rgb[y + dy, x + dx] = J1
    mangas = [manga(rgb, out, *b) for b in brazos]
    for (pl, x, y) in manos:
        p2.mano(rgb, out, pl, x, y)
    limpiar(out, 44 + dy, 108)
    p2.cabeza(src, out, dx, dy)
    return Image.fromarray(out, "RGBA"), piernas, mangas


def limpiar(out, y0, y1):
    """Quita los píxeles de contorno que sobresalen solos (con un único vecino opaco en 4 direcciones)."""
    for _ in range(2):
        op = out[..., 3] > 0
        p = np.pad(op, 1)
        vec = p[:-2, 1:-1].astype(int) + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]
        es_ol = (out[..., 0] == OL[0]) & (out[..., 1] == OL[1]) & (out[..., 2] == OL[2])
        quitar = op & es_ol & (vec <= 1)
        quitar[:y0] = False; quitar[y1:] = False
        out[quitar] = 0


def pose_sobresalto(src, src0):
    dx, dy = -2, 3
    hi, hd = (36 + dx, 48 + dy), (56 + dx, 48 + dy)                   # hombros de la pose 1, desplazados
    brazos = [(hi, (34, 62), (61, 67)),                                # del hombro izquierdo a la cadera derecha (detrás)
              (hd, (55, 60), (34, 70))]                                # del hombro derecho a la cadera izquierda (delante)
    manos = [(MANO_IZQ, 26, 68), (MANO_DER, 62, 65)]
    return armar(src, src0, dx, dy, brazos, manos)


def pose_tapandose(src, src0, e=0):
    dx, dy = -4 + e, 4
    hi, hd = (36 + dx, 48 + dy), (56 + dx, 48 + dy)
    brazos = [(hd, (52 + e, 59), (45 + e, 69), "izq"),                 # derecho: baja hasta la entrepierna
              (hi, (31 + e, 59), (44 + e, 55))]                        # izquierdo: cruza hasta el pecho
    manos = [(MANO_PECHO, 44 + e, 51), (MANO_ABAJO, 41 + e, 70)]
    return armar(src, src0, dx, dy, brazos, manos, sin_panuelo=True)


def todas():
    fr, _ = hojas.fotogramas()
    A = [np.asarray(f).copy() for f in fr]
    res, medidas = {}, {}
    res[0] = t3.vestir(A[0])
    res[5] = p1.con_globo(res[0], fr, 5)
    for k, fn in ((6, lambda: pose_sobresalto(A[6], A[0])), (7, lambda: pose_tapandose(A[7], A[0])),
                  (8, lambda: pose_tapandose(A[8], A[0])), (9, lambda: pose_tapandose(A[9], A[0], e=1))):
        im, piernas, mangas = fn()
        res[k] = im
        medidas[k] = (piernas, mangas)
    return res, fr, medidas


# ---- verificación -------------------------------------------------------------------------------------------------
def anchos_piernas_pose1():
    izq = t1.mascara([(38, 66), (46, 66), (46, 84), (41, 107), (36, 107), (36, 84)])
    der = t1.mascara([(46, 66), (55, 66), (57, 84), (58, 107), (53, 107), (47, 84)])
    return izq, der


def informe(medidas):
    ref = anchos_piernas_pose1()
    lineas = ["ancho de cada pierna (izq/der) en píxeles, por fila equivalente (cadera, muslo, rodilla, media pierna, tobillo)"]
    filas0 = (70, 78, 84, 96, 106)
    lineas.append("pose 1:      " + "  ".join(f"{y}:{ref[0][y].sum()}/{ref[1][y].sum()}" for y in filas0))
    for k, (piernas, mangas) in medidas.items():
        dy = 3 if k == 6 else 4
        cad = 66 + dy
        fila = []
        for y0 in filas0:
            y = int(round(cad + (y0 - 66) * (107 - cad) / (107 - 66)))
            fila.append(f"{y}:{piernas[0][y].sum()}/{piernas[1][y].sum()}")
        lineas.append(f"fotograma {k + 1:2d}: " + "  ".join(fila))
    return lineas


def main():
    PREV.mkdir(exist_ok=True)
    res, fr, medidas = todas()
    for l in informe(medidas):
        print(l)
    p2.hoja(res, fr, (0, 5, 6, 7, 9), PREV / "poses3_hoja.png")
    p2.hoja(res, fr, (0, 6, 7, 9), PREV / "poses3_detalle.png", S=7, rec=(16, 14, 80, 120))
    # superposición: contorno de la pose 1 del traje sobre cada pose (para comparar la silueta)
    for k in (6, 7, 9):
        print(k + 1, "colores", len({tuple(p[:3]) for p in res[k].getdata() if p[3]}))


if __name__ == "__main__":
    main()
