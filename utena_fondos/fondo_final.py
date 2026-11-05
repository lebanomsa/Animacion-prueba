"""Fondo final de Utena (1x): cielo de la referencia (recorte D, estrellas que titilan) + nebulosa violeta sutil de la foto solo en los vacíos negros
+ cometa grande B (con colores más claros para que se vea sobre el violeta). Marco animado vertical.

Salida (utena_fondos/salida/): utena_nebulosa_cometa_126.gif y _x4.gif, y una comparación con el fondo anterior.
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "utena_marco")); sys.path.insert(0, str(HERE))
import marco_animado as ma
import referencia as rf
import referencia1x as r1
import nebulosa_foto as nf
tr = ma.tr
OUT = HERE / "salida"

COLA_VIS = [(255, 255, 255), (232, 244, 255), (196, 226, 255), (160, 206, 255), (124, 176, 250), (96, 140, 240), (80, 100, 220), (64, 72, 180), (52, 52, 140), (44, 40, 108)]
ION_VIS = [(120, 255, 255), (80, 224, 255), (60, 184, 250), (48, 140, 230), (44, 100, 200), (40, 70, 160), (36, 52, 120)]
CAJA_NEBULOSA = "bruma_azul_centro"
INTENSIDAD = 1.0


def comet_B_visible(img, t):
    s = t / 39.0
    rf.cometa(img, 4 + 118 * s, 4 + 96 * s, 118, 96, largo=26, cola=COLA_VIS, ion=ION_VIS)


def bgf_final(ref, nebulosa, crop="D_nebulosa"):
    cache = {}

    def bgf(t):
        if t not in cache:
            img = r1.recorte(ref, rf.indice(t), crop)
            vacio = (img == 0).all(-1)                              # solo los píxeles negros puros de la referencia
            img[vacio] = nebulosa[vacio]
            comet_B_visible(img, t)
            cache[t] = (img, img)
        return cache[t]
    return bgf


def main():
    OUT.mkdir(exist_ok=True)
    ref = rf.cargar()
    neb = nf.capa(nf.CAJAS[CAJA_NEBULOSA], INTENSIDAD)
    crop0 = r1.recorte(ref, 0, "D_nebulosa")
    W = np.zeros((126, 126), bool); W[23:103, 23:103] = True
    print("vacíos negros de la referencia dentro de la ventana: %.0f %%" % (100 * ((crop0 == 0).all(-1) & W).sum() / W.sum()))
    caps = tr.cargar_capas_1x(bgf_final(ref, neb))
    cache = {}
    for K in (140, 126, 112, 98, 84, 70, 56):
        marcos, ws, win = cache.setdefault(K, ma.construir_marco("vertical", K))
        frames = [ma.escena(caps, marcos, t, esc=1) for t in range(ma.L)]
        n = len({tuple(c) for f in frames for c in np.unique(np.asarray(f).reshape(-1, 3), axis=0)})
        print(f"marco con {K} tonos -> {n} colores")
        if n <= 256:
            break
    ma.pe.gif_opaco(frames, OUT / "utena_nebulosa_cometa_126.gif", ma.TICK)
    ma.pe.gif_opaco([f.resize((504, 504), Image.NEAREST) for f in frames], OUT / "utena_nebulosa_cometa_x4.gif", ma.TICK)
    for r in ("utena_nebulosa_cometa_126.gif", "utena_nebulosa_cometa_x4.gif"):
        print(f"  {r}: {Image.open(OUT / r).size}, {(OUT / r).stat().st_size / 1024:.0f} KB")
    # comparación con el fondo anterior (sin nebulosa violeta)
    caps0 = tr.cargar_capas_1x(r1.bgf_para(ref, "D_nebulosa", r1.comet_B))
    fr0 = [ma.escena(caps0, marcos, t, esc=1) for t in range(ma.L)]
    mom = [2, 8, 14, 21, 27, 36]
    Z = 2
    sh = Image.new("RGB", (len(mom) * 126 * Z, 2 * 126 * Z))
    for j, t in enumerate(mom):
        sh.paste(fr0[t].resize((126 * Z, 126 * Z), Image.NEAREST), (j * 126 * Z, 0))
        sh.paste(frames[t].resize((126 * Z, 126 * Z), Image.NEAREST), (j * 126 * Z, 126 * Z))
    d = ImageDraw.Draw(sh); d.text((6, 6), "antes", fill=(255, 255, 255)); d.text((6, 126 * Z + 6), "con nebulosa violeta sutil", fill=(255, 255, 255))
    sh.save(OUT / "comparacion_antes_despues.png")
    Image.fromarray(neb).resize((126 * 4, 126 * 4), Image.NEAREST).save(OUT / "nebulosa_pixelada.png")
    # sin Utena ni marco: el fondo solo en 6 momentos
    sh = Image.new("RGB", (6 * 126 * 2, 126 * 2))
    bg = bgf_final(ref, neb)
    for j, t in enumerate((0, 8, 16, 24, 32, 39)):
        sh.paste(Image.fromarray(bg(t)[0]).resize((252, 252), Image.NEAREST), (j * 252, 0))
    sh.save(OUT / "fondo_solo_momentos.png")
    print("listo")


if __name__ == "__main__":
    main()
