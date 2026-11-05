"""Previews de los fondos cósmicos con Utena y el marco animado (variante vertical) dentro.

Salida en previews/: un GIF de 126x126 por fondo y una hoja con 3 momentos de cada uno.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "utena_marco"))
import marco_animado as ma   # noqa: E402  (importa también la animación de Utena)
sys.path.insert(0, str(HERE))
import cosmos as cs          # noqa: E402

tr, hz = ma.tr, ma.tr.hz
OUT = HERE / "previews"


def main(opcion_marco="vertical"):
    OUT.mkdir(exist_ok=True)
    nat, _, _ = hz.recuperar()
    spr, bg0, bgp0 = hz.capas_base(nat)
    m_norm = (bg0 == hz.SHADOW).all(-1)
    m_peq = (bgp0 == hz.SHADOW).all(-1)
    cache_marcos = {}
    hoja = {}
    z = 2
    for nombre in cs.FONDOS:
        bgf = cs.con_sombras(nombre, m_norm, m_peq)
        caps = tr.cargar_capas(bgf, snap_destello=True)
        for K in (130, 118, 106, 94, 82):
            if K not in cache_marcos:
                cache_marcos[K] = ma.construir_marco(opcion_marco, K)
            marcos, ws, win = cache_marcos[K]
            frames = [ma.escena(caps, marcos, t) for t in range(ma.L)]
            n = len({tuple(c) for f in frames for c in np.unique(np.asarray(f).reshape(-1, 3), axis=0)})
            if n <= 256:
                break
        ma.pe.gif_opaco(frames, OUT / f"fondo_{nombre}_126.gif", ma.TICK)
        print(f"{nombre}: marco {K} tonos, {n} colores, {(OUT / f'fondo_{nombre}_126.gif').stat().st_size / 1024:.0f} KB")
        hoja[nombre] = [frames[t] for t in (2, 21, 26)]
    names = list(cs.FONDOS)
    sh = Image.new("RGB", (len(names) * 126 * z, 3 * 126 * z))
    for i, nom in enumerate(names):
        for j, f in enumerate(hoja[nom]):
            sh.paste(f.resize((126 * z, 126 * z), Image.NEAREST), (i * 126 * z, j * 126 * z))
        ImageDraw.Draw(sh).text((i * 126 * z + 6, 6), nom, fill=(255, 255, 255))
    sh.save(OUT / "hoja_fondos.png")
    print("listo", sh.size)


if __name__ == "__main__":
    main()
