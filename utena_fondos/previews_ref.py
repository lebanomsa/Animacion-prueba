"""Previews del fondo hecho con la referencia: recortes de la imagen y tres estilos de cometa, con Utena y el marco animado (vertical) dentro."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "utena_marco"))
import marco_animado as ma   # noqa: E402
sys.path.insert(0, str(HERE))
import referencia as rf      # noqa: E402

tr = ma.tr
OUT = HERE / "previews"
Z = 2


def frames_para(ref, crop, cometa_fn, marcos_cache):
    bgf = rf.bgf_para(ref, crop, cometa_fn)
    caps = tr.cargar_capas(bgf, snap_destello=(0, 38))
    for K in (140, 126, 112, 98, 84, 70):
        if K not in marcos_cache:
            marcos_cache[K] = ma.construir_marco("vertical", K)
        marcos, ws, win = marcos_cache[K]
        frames = [ma.escena(caps, marcos, t) for t in range(ma.L)]
        n = len({tuple(c) for f in frames for c in np.unique(np.asarray(f).reshape(-1, 3), axis=0)})
        if n <= 256:
            return frames, K, n
    raise RuntimeError("no cabe en 256 colores")


def hoja(frames_por_columna, titulos, momentos, ruta):
    sh = Image.new("RGB", (len(frames_por_columna) * 126 * Z, len(momentos) * 126 * Z))
    for i, fr in enumerate(frames_por_columna):
        for j, t in enumerate(momentos):
            sh.paste(fr[t].resize((126 * Z, 126 * Z), Image.NEAREST), (i * 126 * Z, j * 126 * Z))
        ImageDraw.Draw(sh).text((i * 126 * Z + 6, 6), titulos[i], fill=(255, 255, 255))
    sh.save(ruta)


def main():
    OUT.mkdir(exist_ok=True)
    ref = rf.cargar()
    marcos_cache = {}
    # 1) recortes de la referencia (sin cometa)
    cols, titulos = [], []
    for crop in ("nebulosa", "nebulosa_der", "cumulos", "arriba"):
        fr, K, n = frames_para(ref, crop, None, marcos_cache)
        cols.append(fr); titulos.append(f"recorte: {crop}")
        print(f"recorte {crop}: marco {K} tonos, {n} colores")
    hoja(cols, titulos, (2, 21, 26), OUT / "ref_recortes.png")
    # 2) tres cometas sobre el recorte elegido para comparar
    crop = "nebulosa"
    cols, titulos = [], []
    for nombre, fn in rf.COMETAS.items():
        fr, K, n = frames_para(ref, crop, fn, marcos_cache)
        ma.pe.gif_opaco(fr, OUT / f"ref_cometa_{nombre}_126.gif", ma.TICK)
        f504 = [f.resize((504, 504), Image.NEAREST) for f in fr]
        ma.pe.gif_opaco(f504, OUT / f"ref_cometa_{nombre}_x4.gif", ma.TICK)
        print(f"cometa {nombre}: marco {K} tonos, {n} colores, {(OUT / f'ref_cometa_{nombre}_126.gif').stat().st_size / 1024:.0f} KB")
        cols.append(fr); titulos.append(f"cometa {nombre}")
    hoja(cols, titulos, (4, 6, 8, 20, 27), OUT / "ref_cometas.png")
    # solo el fondo de cada cometa, sin Utena ni marco: 6 momentos
    sh = Image.new("RGB", (6 * 63 * 3, len(rf.COMETAS) * 63 * 3))
    for i, (nombre, fn) in enumerate(rf.COMETAS.items()):
        bgf = rf.bgf_para(ref, crop, fn)
        for j, t in enumerate((3, 5, 7, 9, 26, 29)) if nombre != "B_cometa_grande" else enumerate((6, 14, 22, 30, 36, 39)):
            sh.paste(Image.fromarray(bgf(t)[0]).resize((63 * 3, 63 * 3), Image.NEAREST), (j * 63 * 3, i * 63 * 3))
    sh.save(OUT / "ref_cometas_solo_fondo.png")
    print("listo")


if __name__ == "__main__":
    main()
