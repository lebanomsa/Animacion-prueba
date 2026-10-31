"""Comparación de tamaños del esqueleto en el marco oro y plata: x5, x5,5 y x6 (pose del golpe, la más ancha, y del festejo, la más alta).

x5 y x6 son enteros (píxeles uniformes); x5,5 no lo es (píxeles de 5 y 6 px). El fondo de rayos se dibuja a la misma escala que el personaje.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import marcos as mk             # noqa: E402
import giros                    # noqa: E402
import marco                    # noqa: E402

PREV = HERE / "previews"


def capa_pose(clave, box):
    return giros.colocar(giros.F[clave]).crop(box)


def ventana(S, sk):
    """Ventana de 640 px con el fondo y el esqueleto a escala S (el fondo en píxeles nativos del mismo tamaño)."""
    n = int(np.ceil(640 / S))
    fondo = mk.fondo_rayos(3, n).convert("RGBA")
    if float(S).is_integer():
        S = int(S)
        grande = fondo.resize((n * S, n * S), Image.NEAREST)
        x = (n * S - 640) // 2
        win = grande.crop((x, x, x + 640, x + 640))
    else:
        win = fondo.resize((640, 640), Image.NEAREST)
    g = sk.resize((round(sk.width * S), round(sk.height * S)), Image.NEAREST)
    win.alpha_composite(g, ((640 - g.width) // 2, 640 - g.height - 10))
    return win


def main():
    PREV.mkdir(exist_ok=True)
    fr = mk.animacion.pasos()
    boxes = [f.getchannel("A").getbbox() for f in fr]
    box = (min(b[0] for b in boxes) - 1, min(b[1] for b in boxes) - 1, max(b[2] for b in boxes) + 1, max(b[3] for b in boxes) + 1)
    box = (max(box[0], 0), max(box[1], 0), min(box[2], giros.CW), min(box[3], giros.CH))
    w, h = box[2] - box[0], box[3] - box[1]
    for S in (5, 5.5, 6, 6.5):
        print(f"x{S}: lienzo {round(w * S)}x{round(h * S)} de 640 ({round(h * S / 640 * 100)} % de alto)")
    f0, _ = marco.build(mk.ORO, mk.PLATA)
    f0 = f0.copy()
    mk.det1(f0, 3)
    paneles = []
    for clave in ("2.1", "3.4"):
        sk = capa_pose(clave, box)
        for S in (5, 5.5, 6):
            base = Image.new("RGBA", (1024, 1024), (0, 0, 0, 255))
            base.alpha_composite(ventana(S, sk), (192, 192))
            base.alpha_composite(f0.resize((1024, 1024), Image.NEAREST))
            paneles.append(base.convert("RGB").resize((512, 512), Image.LANCZOS))
    hoja = Image.new("RGB", (1536, 1024))
    for i, p in enumerate(paneles):
        hoja.paste(p, ((i % 3) * 512, (i // 3) * 512))
    hoja.save(PREV / "tamano_esqueleto.png")
    print("hoja", hoja.size)


if __name__ == "__main__":
    main()
