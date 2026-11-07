"""Vista previa de las tres opciones de marco con el bucle 2 de Bersek (variante con avance)."""
from pathlib import Path
from PIL import Image
import numpy as np
import animacion_pilar as ap
import marco_bersek as mb

OUT = Path(__file__).parent / "salida_pilar"


def main():
    for op in mb.PALETAS:
        fr = ap.render("avance", marco_fn=lambda t, op=op: mb.frame_126(op, t))
        n = max(len(np.unique(np.asarray(f).reshape(-1, 3), axis=0)) for f in fr)
        ag = ap.bb.gif_local([f.resize((504, 504), Image.NEAREST) for f in fr], OUT / f"marco_{op}_avance_x4.gif", ap.TICK)
        idx = [4, 12, 22, 31]
        s = Image.new("RGB", (504 * 2 + 10, 504 * 2 + 10), (30, 30, 30))
        for j, i in enumerate(idx): s.paste(fr[i].resize((504, 504), Image.NEAREST), ((j % 2) * 514, (j // 2) * 514))
        s.save(OUT / f"marco_{op}_momentos.png")
        print(op, len(fr), "colores máx", n, "agrupados", ag)


if __name__ == "__main__":
    main()
