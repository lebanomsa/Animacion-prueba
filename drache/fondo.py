"""Fondo de Drache a partir de 'stage drache.png' (Stage Fukai de Metal Slug Attack; crédito de la hoja: AkaPreston (rip), Patchworks (arreglo)).

Se usa el panorama marrón de 2048x219 px a tamaño natural (sin escalar). Se elige una ventana de 380 px de ancho; por arriba se añade techo de cueva
(continuación oscura de la fila superior) para que haya sitio sobre la cabeza y los efectos. Las botas de Drache apoyan sobre la arena.
"""
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
STAGE = HERE / "fuentes" / "stage drache.png"
PANORAMA = (5, 17, 2048, 219)          # x, y, ancho, alto del panorama marrón dentro de la imagen


def panorama():
    a = np.asarray(Image.open(STAGE).convert("RGB"))
    x, y, w, h = PANORAMA
    return a[y:y + h, x:x + w].copy()


def ventana(x0, W=380, H=259, suelo_en_stage=205, extra_arriba=None):
    """Fondo de W x H píxeles: la ventana del panorama en x0, pegada abajo, con el techo extendido arriba."""
    p = panorama()
    alto = p.shape[0]
    extra = H - alto if extra_arriba is None else extra_arriba
    w = p[:, x0:x0 + W].astype(float)
    arriba = np.repeat(w[:6].mean(0, keepdims=True), extra, axis=0)               # techo: la fila superior repetida, cada vez más oscura
    t = np.linspace(0.35, 1.0, extra)[:, None, None]
    arriba = arriba * t
    return np.vstack([arriba, w]).clip(0, 255).astype(np.uint8)


if __name__ == "__main__":
    p = panorama()
    verde = ((p == (0, 255, 0)).all(-1)).sum(); mag = ((p == (255, 0, 255)).all(-1)).sum()
    print("panorama", p.shape[1], "x", p.shape[0], "; píxeles verdes/magenta sobrantes:", int(verde), int(mag))
