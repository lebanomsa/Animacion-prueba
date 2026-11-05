"""Convierte 'nebula utena.jpg' (fotografía) en una capa de pixel art de 126x126, sutil, para rellenar los vacíos oscuros del fondo.

Se quitan las estrellas con un filtro de mediana, se reduce la foto a 126x126 y cada píxel se lleva a una paleta corta de violetas apagados
(dos rampas: índigo y magenta) con tramado ordenado 4x4 en los degradados. El resultado usa solo 8 colores y es poco luminoso.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).parent
FOTO = HERE.parent / "nebula utena.jpg"
N = 126
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
INDIGO = [(10, 6, 28), (22, 14, 58), (40, 28, 92), (62, 46, 124)]
MAGENTA = [(14, 6, 30), (34, 14, 60), (62, 26, 90), (92, 44, 118)]


def capa(box, intensidad=1.0, mediana=9):
    """box = (x0, y0, x1, y1) de la foto. intensidad < 1 la hace más tenue."""
    foto = Image.open(FOTO).convert("RGB").crop(box).filter(ImageFilter.MedianFilter(mediana))
    a = np.asarray(foto.resize((N, N), Image.LANCZOS)).astype(float)
    L = a.mean(-1) / 255.0
    ratio = a[..., 0] / (a[..., 0] + a[..., 2] + 1e-6)                      # 0.3 azulado ... 0.6 rosado
    yy, xx = np.mgrid[0:N, 0:N]
    dit = BAYER[yy % 4, xx % 4]
    t = np.clip((L - 0.14) / 0.62, 0, 1) ** 1.15 * intensidad * 3.0         # 0..3 (índice de tono)
    i0 = np.floor(t).astype(int)
    idx = np.minimum(i0 + ((t - i0) > dit), 3)
    magenta = np.clip((ratio - 0.44) / 0.14, 0, 1) > dit
    out = np.where(magenta[..., None], np.array(MAGENTA)[idx], np.array(INDIGO)[idx])
    return out.astype(np.uint8)


CAJAS = {
    "nube_rosada_arriba": (150, 0, 650, 500),
    "bruma_azul_centro": (0, 300, 500, 800),
    "estrellas_abajo": (200, 527, 700, 1027),
}

if __name__ == "__main__":
    Z = 4
    sh = Image.new("RGB", (len(CAJAS) * N * Z + 20, N * Z))
    for i, (nom, box) in enumerate(CAJAS.items()):
        sh.paste(Image.fromarray(capa(box)).resize((N * Z, N * Z), Image.NEAREST), (i * (N * Z + 10), 0))
        print(nom, "colores:", len(np.unique(capa(box).reshape(-1, 3), axis=0)))
    sh.save("/projects/sandbox/tmp/fondo_ref/nebulas_prueba.png")
