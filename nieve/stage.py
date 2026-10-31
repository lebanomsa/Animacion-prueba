"""Montaje del escenario de nieve ('nieve stage.png').

La hoja trae 18 cielos de 512x256 (bosque de pinos nevados de noche, con o sin luna; los 3 de cada grupo
solo se diferencian en la fase de las estrellas), un suelo de nieve de 2176x334 (escalón a la izquierda, foso a la
derecha), una miniatura y los créditos del ripeador (que no se usan).
El escenario se monta con el suelo delante y el cielo detrás. Los cielos no son continuos entre sí (la diferencia en el borde es
el doble que entre columnas vecinas), así que se repiten espejando una de cada dos teselas para que no haya costuras.

Entre el cielo y el suelo: la línea del suelo (parte plana) queda en SUELO_Y y deja ver unos 90 px del bosque por encima.
"""
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
ROOT = HERE.parent

TILE_W, TILE_H = 512, 256
COLS_X, ROWS_Y = [42, 584, 1126, 1666, 2208, 2750], [52, 338, 624]
GROUND_BOX = (85, 974, 2261, 1308)
GROUND_FLAT_Y = 165                     # fila del suelo plano dentro del sprite del suelo
SUELO_Y = 210                           # fila del suelo plano en el escenario
STAGE_H = SUELO_Y + (334 - GROUND_FLAT_Y)
SKY_Y = SUELO_Y - 224                   # el bosque (filas 134..256 del cielo) queda 90 px por encima del suelo


def load_sheet():
    return Image.open(ROOT / "nieve stage.png").convert("RGBA")


def skies(sheet):
    """18 cielos de 512x256 (RGB). Índices 0-2, 6-8, 12-14 sin luna; 3-5, 9-11, 15-17 con luna."""
    return [sheet.crop((x, y, x + TILE_W, y + TILE_H)).convert("RGB") for y in ROWS_Y for x in COLS_X]


def ground(sheet):
    return sheet.crop(GROUND_BOX)


def build_stage(width=2176, moon_tile=1, sky_index=0, moon_index=3):
    """Escenario completo (RGB) de ancho `width`. moon_tile = nº de tesela con luna (o None)."""
    sheet = load_sheet()
    sk = skies(sheet)
    g = ground(sheet)
    stage = Image.new("RGBA", (width, STAGE_H), (14, 16, 38, 255))
    n = -(-width // TILE_W)
    for k in range(n):
        tile = sk[moon_index if k == moon_tile else sky_index]
        if k % 2 == 1:
            tile = tile.transpose(Image.FLIP_LEFT_RIGHT)                # espejo: sin costuras
        stage.paste(tile, (k * TILE_W, SKY_Y))
    # por debajo del cielo (y > SKY_Y + 256) y por encima de su borde superior: color del cielo
    arr = np.asarray(stage).copy()
    top = arr[max(SKY_Y, 0)]
    if SKY_Y > 0:
        arr[:SKY_Y] = top
    stage = Image.fromarray(arr, "RGBA")
    stage.alpha_composite(g, (0, SUELO_Y - GROUND_FLAT_Y))
    return stage.convert("RGB")


if __name__ == "__main__":
    st = build_stage()
    print("escenario:", st.size)
    out = HERE / "previews"; out.mkdir(exist_ok=True)
    st.save(out / "stage_completo.png")
    views = [st.crop((x, 0, x + 640, st.height)) for x in (0, 768, st.width - 640)]
    sheet = Image.new("RGB", (640 * 3 + 20, st.height), (20, 10, 14))
    for i, v in enumerate(views):
        sheet.paste(v, (i * 650, 0))
    sheet.save(out / "stage_vistas.png")
    print("vistas:", sheet.size)
