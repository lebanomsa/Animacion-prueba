"""Previews del fondo de la referencia con Utena a tamaño natural (1x): cuatro recortes del cielo y tres estilos de cometa."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "utena_marco")); sys.path.insert(0, str(HERE))
import marco_animado as ma
import referencia as rf
import referencia1x as r1
tr = ma.tr
OUT = HERE / "previews_1x"
Z = 2


def frames_para(ref, crop, cometa_fn, cache):
    caps = tr.cargar_capas_1x(r1.bgf_para(ref, crop, cometa_fn))
    for K in (140, 126, 112, 98, 84, 70, 56):
        if K not in cache:
            cache[K] = ma.construir_marco("vertical", K)
        marcos, ws, win = cache[K]
        frames = [ma.escena(caps, marcos, t, esc=1) for t in range(ma.L)]
        n = len({tuple(c) for f in frames for c in np.unique(np.asarray(f).reshape(-1, 3), axis=0)})
        if n <= 256:
            return frames, K, n
    raise RuntimeError("no cabe en 256 colores")


def hoja(cols, titulos, momentos, ruta):
    sh = Image.new("RGB", (len(cols) * 126 * Z, len(momentos) * 126 * Z))
    for i, fr in enumerate(cols):
        for j, t in enumerate(momentos):
            sh.paste(fr[t].resize((126 * Z, 126 * Z), Image.NEAREST), (i * 126 * Z, j * 126 * Z))
        ImageDraw.Draw(sh).text((i * 126 * Z + 6, 6), titulos[i], fill=(255, 255, 255))
    sh.save(ruta)


def main():
    OUT.mkdir(exist_ok=True)
    ref = rf.cargar(); cache = {}
    cols, tit = [], []
    for crop in r1.CROPS:
        fr, K, n = frames_para(ref, crop, None, cache)
        cols.append(fr); tit.append(crop)
        ma.pe.gif_opaco(fr, OUT / f"recorte_{crop}_126.gif", ma.TICK)
        print(f"recorte {crop}: marco {K} tonos, {n} colores")
    hoja(cols, tit, (2, 12, 21, 30), OUT / "recortes.png")
    cols, tit = [], []
    for nombre, fn in r1.COMETAS.items():
        fr, K, n = frames_para(ref, "D_nebulosa", fn, cache)
        ma.pe.gif_opaco(fr, OUT / f"cometa_{nombre}_126.gif", ma.TICK)
        ma.pe.gif_opaco([f.resize((504, 504), Image.NEAREST) for f in fr], OUT / f"cometa_{nombre}_x4.gif", ma.TICK)
        print(f"cometa {nombre}: marco {K} tonos, {n} colores, {(OUT / f'cometa_{nombre}_126.gif').stat().st_size / 1024:.0f} KB")
        cols.append(fr); tit.append(nombre)
    hoja(cols, tit, (4, 6, 8, 14, 20, 27, 36), OUT / "cometas.png")
    print("listo")


if __name__ == "__main__":
    main()
