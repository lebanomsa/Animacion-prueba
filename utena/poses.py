"""Traje (silueta femenina, versión de traje3) en todas las poses del GIF de Utena.

Pose 0 (fotogramas 0-5) es la de traje3. Para las demás se combina:
  * pantalón: el contorno de las piernas del GIF (medias negras), fila a fila y pierna por pierna, rellenado y sombreado
  * saco, camisa, corbata y cuello: el torso de la pose 0 desplazado lo mismo que se desplaza la cabeza
  * mangas: los píxeles del brazo del GIF dentro de unos polígonos (hombro abullonado, guante o brazo desnudo) recoloreados
    en negro de saco, con contorno, luz arriba y puño blanco donde tocan la mano
  * manos (piel del GIF) y cabeza (con su expresión) del propio fotograma, y las estrellas de los cuernos
Fotograma 7 = 8 (difieren en 4 píxeles) y el 9 es el 8 desplazado 1 px a la derecha.
"""
from pathlib import Path

import numpy as np
from PIL import Image

import hojas
import traje as t1
import traje3 as t3

HERE = Path(__file__).parent
PREV = HERE / "previews"
OL, J0, J1, J2 = t3.OL, t3.J0, t3.J1, t3.J2
P0, P1, P2 = t3.P0, t3.P1, t3.P2
W, WS = t3.W, t3.WS
S1, S2 = (98, 50, 146), (196, 150, 236)

POSES = {
    # dx, dy: desplazamiento de la cabeza respecto a la pose 0; piernas: filas desde las que se toma el contorno
    6: dict(dx=-2, dy=3, piernas_y0=76, rangos=((28, 45), (45, 62)),
            mangas=[[(29, 47), (38, 47), (38, 59), (30, 59)],                      # hombro izquierdo (abullonado)
                    [(48, 47), (58, 47), (58, 59), (48, 59)],                      # hombro derecho
                    [(45, 57), (51, 58), (50, 62), (36, 70), (31, 72), (24, 74), (24, 67), (34, 62)],   # brazo en diagonal
                    [(45, 69), (67, 67), (67, 77), (45, 77)]],                     # brazo horizontal
            manos=[[(23, 66), (29, 66), (29, 76), (23, 76)], [(62, 66), (68, 66), (68, 77), (62, 77)]],
            piel_es_manga=True, punos=True),
    8: dict(dx=-4, dy=4, piernas_y0=62, rangos=((32, 44), (44, 57)),
            mangas=[[(28, 47), (38, 47), (38, 53), (44, 54), (44, 60), (31, 60), (28, 56)],
                    [(45, 47), (55, 47), (55, 58), (52, 60), (44, 60), (44, 54), (46, 53)]],
            manos=[[(32, 54), (50, 54), (50, 60), (32, 60)]],
            piel_es_manga=False, punos=False),
}


def mascara(pol, dx=0):
    return t1.mascara([(x + dx, y) for (x, y) in pol])


def es_piel(c):
    """Piel (rosa) y no dorado: el dorado tiene el azul bajo y el amarillo claro casi no tiene diferencia rojo-verde."""
    r, g, b = int(c[0]), int(c[1]), int(c[2])
    return r >= 195 and r - g >= 25 and b >= 120 and r - b <= 100


def lum(c):
    return (int(c[0]) + int(c[1]) + int(c[2])) / 3


def pantalon(src, out, cfg, dx_extra=0):
    rgb = out[..., :3]
    piernas = []
    for (xa, xb) in cfg["rangos"]:
        mk = np.zeros((128, 96), bool)
        for y in range(cfg["piernas_y0"], 108):
            xs = [x for x in range(xa + dx_extra, xb + dx_extra) if src[y, x, 3] and lum(src[y, x]) < 84]
            if xs:
                mk[y, min(xs):max(xs) + 1] = True
        piernas.append(mk)
    for mk in piernas:
        rgb[mk] = P1
        out[mk, 3] = 255
    for i, mk in enumerate(piernas):
        for y in range(cfg["piernas_y0"], 108):
            xs = np.where(mk[y])[0]
            if len(xs) >= 4:
                rgb[y, xs.max() - 1 if i == 0 else xs.min() + 1] = P0       # sombra interior
                rgb[y, (xs.min() + xs.max()) // 2] = P2 if y > cfg["piernas_y0"] + 20 else P1   # raya
        rgb[t1.borde(mk)] = OL


def zapatos(src, out):
    rgb = out[..., :3]
    for y in range(108, 119):
        for x in range(96):
            if src[y, x, 3]:
                L = lum(src[y, x])
                rgb[y, x] = OL if L < 55 else (P1 if L < 150 else ((48, 48, 52) if L < 215 else (78, 78, 84)))
                out[y, x, 3] = 255


def vestir_pose(src, src0, cfg, dx_extra=0):
    dx, dy = cfg["dx"] + dx_extra, cfg["dy"]
    out = np.zeros((128, 96, 4), np.uint8)
    rgb = out[..., :3]
    pantalon(src, out, cfg, dx_extra)
    zapatos(src, out)
    torso = np.array(t3.vestir(src0, solo_torso=True))
    torso = np.roll(np.roll(torso, dy, 0), dx, 1)
    mt = torso[..., 3] > 0
    out[mt] = torso[mt]
    # ---- manos
    manos = np.zeros((128, 96), bool)
    for pol in cfg["manos"]:
        zona = mascara(pol, dx_extra)
        for y, x in zip(*np.where(zona)):
            if src[y, x, 3] and es_piel(src[y, x]):
                manos[y, x] = True
    # ---- mangas
    manga = np.zeros((128, 96), bool)
    tono = np.zeros((128, 96), np.uint8)               # 0 base, 1 sombra
    cab_y = 41 + dy
    for pol in cfg["mangas"]:
        zona = mascara(pol, dx_extra)
        for y, x in zip(*np.where(zona)):
            if y < cab_y or not src[y, x, 3] or manos[y, x]:
                continue
            c = src[y, x]
            if es_piel(c) and not cfg["piel_es_manga"]:
                continue
            manga[y, x] = True
            L = lum(c)
            tono[y, x] = 1 if (L < 50 or 140 <= L < 200) else 0
    rgb[manga] = J1
    rgb[manga & (tono == 1)] = J0
    p = np.pad(manga, 1)
    arriba = manga & ~p[:-2, 1:-1]
    rgb[arriba] = J2
    rgb[t1.borde(manga)] = OL
    out[manga, 3] = 255
    pm = np.pad(manos, 1)
    junto_mano = manga & (pm[:-2, 1:-1] | pm[2:, 1:-1] | pm[1:-1, :-2] | pm[1:-1, 2:])
    if cfg.get("punos", True):
        rgb[junto_mano] = W
    out[manos] = src[manos]
    # ---- cabeza del fotograma y estrellas de los cuernos
    cab = src[:cab_y]
    mk = cab[..., 3] > 0
    out[:cab_y][mk] = cab[mk]
    for (cx, cy) in ((53 + dx, 22 + dy), (35 + dx, 23 + dy)):
        for (ex, ey) in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            rgb[cy + ey, cx + ex] = S1
        rgb[cy, cx] = S2
    return Image.fromarray(out, "RGBA")


def todas():
    """Devuelve {fotograma del GIF: imagen vestida} para las poses distintas (0, 6, 8, 9)."""
    fr, _ = hojas.fotogramas()
    A = [np.asarray(f).copy() for f in fr]
    res = {0: t3.vestir(A[0]), 6: vestir_pose(A[6], A[0], POSES[6]), 8: vestir_pose(A[8], A[0], POSES[8])}
    res[9] = vestir_pose(A[9], A[0], POSES[8], dx_extra=1)
    return res, fr


def con_globo(vestida, fr, k):
    """Copia el globo de diálogo del fotograma k (1-5): los píxeles que difieren del fotograma 0 en la zona del globo."""
    a0, ak = np.asarray(fr[0]), np.asarray(fr[k])
    out = np.array(vestida)
    zona = np.zeros((128, 96), bool); zona[14:36, 62:73] = True
    dif = zona & (np.abs(ak.astype(int) - a0.astype(int)).sum(-1) > 0) & (ak[..., 3] > 0)
    out[dif] = ak[dif]
    return Image.fromarray(out, "RGBA")


def main():
    PREV.mkdir(exist_ok=True)
    res, fr = todas()
    res = dict(res)
    res[5] = con_globo(res[0], fr, 5)
    from PIL import ImageDraw
    S = 4
    w, h = 96 * S, 128 * S
    hoja = Image.new("RGB", (4 * w, 2 * h + 40), (46, 46, 56))
    d = ImageDraw.Draw(hoja)
    for i, k in enumerate((5, 6, 8, 9)):
        for j, im in enumerate((fr[k], res[k])):
            b = Image.new("RGBA", im.size, (46, 46, 56, 255)); b.alpha_composite(im)
            hoja.paste(b.convert("RGB").resize((w, h), Image.NEAREST), (i * w, j * (h + 20) + 20))
        d.text((i * w + 6, 4), f"fotograma {k}", fill=(255, 230, 120))
    hoja.save(PREV / "poses_traje.png")
    print("ok")


if __name__ == "__main__":
    main()
