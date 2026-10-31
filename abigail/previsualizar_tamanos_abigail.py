"""Vistas previas de tamaños de Abigail dentro del marco dorado-rubí con Fondo 3.

La ventana mide 640x640 px: a escala s solo caben 640/s píxeles del dibujo (x4: 160, x5: 128).
Opciones (filas): la actual, A (x5 con la animación compactada) y B (x5 sin tocar la animación, se recorta).
Salida: previews/tamanos_abigail.png (columnas = pasos 22, 36, 43 y 67 de la animación).
"""
import contextlib
import io
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "secuencia"))
import make_completa as mc      # noqa: E402
import marco                    # noqa: E402
from componer_marco_abigail import ORO, RUBI_PLATA, BG_X0, BG_COLS, BG_ROWS  # noqa: E402

S_FRAME = 8
STEPS = (22, 36, 43, 67)         # gestos, explosión, arco de la gorra, brillos
# nombre, escala, (arco de la gorra, avance de la gorra, separación de los brillos), centrado vertical
OPCIONES = [
    ("Actual: personaje x4, fondo x5", 4, (40, 66, 4), "pies"),
    ("A: personaje x5, fondo x5, animación compactada (cabe entera)", 5, (24, 54, 3), "abajo"),
    ("B: personaje x5, fondo x5, animación sin tocar (se recorta por los bordes)", 5, (40, 66, 4), "centro"),
]


def render(params):
    mc.CAP_APEX, mc.CAP_DX, mc.SPARK_OFFSET = params
    mc.SPARK_BOUNDS = None
    with contextlib.redirect_stdout(io.StringIO()):
        frames, box = mc.main("caminar", save=False)
    return frames, box


def paste_clipped(layer, img, x, y):
    """Compone img en layer en (x, y) recortando lo que se sale por los bordes."""
    sx, sy = max(-x, 0), max(-y, 0)
    dx, dy = max(x, 0), max(y, 0)
    w = min(img.width - sx, layer.width - dx); h = min(img.height - sy, layer.height - dy)
    if w > 0 and h > 0:
        layer.alpha_composite(img.crop((sx, sy, sx + w, sy + h)), (dx, dy))


def main():
    frame, (wx0, wy0, wx1, wy1) = marco.build(ORO, RUBI_PLATA)
    win_x, win_y = wx0 * S_FRAME, wy0 * S_FRAME
    win = (wx1 - wx0 + 1) * S_FRAME
    marco_big = frame.resize((marco.N * S_FRAME,) * 2, Image.NEAREST)
    bg = Image.open(ROOT / "Fondo 3.png").convert("RGB")
    crop = np.asarray(bg.crop((BG_X0, 0, BG_X0 + BG_COLS, BG_ROWS)))
    big = np.asarray(Image.fromarray(crop).resize((BG_COLS * 5, BG_ROWS * 5), Image.NEAREST))
    pad = win - big.shape[0]
    mirror = np.asarray(Image.fromarray(crop[:pad // 5][::-1]).resize((BG_COLS * 5, pad), Image.NEAREST))
    bg_big = Image.fromarray(np.concatenate([mirror, big], axis=0), "RGB").convert("RGBA")

    W, T = 512, 18
    sheet = Image.new("RGB", (W * len(STEPS), (W + T) * len(OPCIONES)), (20, 10, 14))
    d = ImageDraw.Draw(sheet)
    for r, (nombre, sc, params, modo) in enumerate(OPCIONES):
        frames, box = render(params)
        ub = (min(b[0] for b in (f.getchannel("A").getbbox() for f in frames) if b),
              min(b[1] for b in (f.getchannel("A").getbbox() for f in frames) if b),
              max(b[2] for b in (f.getchannel("A").getbbox() for f in frames) if b),
              max(b[3] for b in (f.getchannel("A").getbbox() for f in frames) if b))
        cw, ch = ub[2] - ub[0], ub[3] - ub[1]
        feet_row = (mc.G + 2) - box[1] - ub[1]
        if modo == "pies":
            ax = (win - cw * sc) // 2; ay = 575 - feet_row * sc        # como la versión actual
        elif modo == "abajo":
            ax = (win - cw * sc) // 2; ay = win - ch * sc               # apoyada en el borde inferior de la ventana
        else:
            ax = (win - cw * sc) // 2; ay = (win - ch * sc) // 2        # centrada: lo que sobra se recorta
        d.text((6, r * (W + T) + 4), f"{nombre}  |  contenido {cw}x{ch} px -> {cw * sc}x{ch * sc} px en pantalla "
               f"(ventana 640x640)", fill=(255, 255, 255))
        for c, s_ in enumerate(STEPS):
            f = frames[s_].crop(ub).resize((cw * sc, ch * sc), Image.NEAREST)
            layer = bg_big.copy()
            paste_clipped(layer, f, ax, ay)
            img = Image.new("RGBA", (1024, 1024), (0, 0, 0, 255))
            img.alpha_composite(layer, (win_x, win_y))
            img.alpha_composite(marco_big)
            sheet.paste(img.convert("RGB").resize((W, W), Image.LANCZOS), (c * W, r * (W + T) + T))
        print(f"{nombre}: contenido {cw}x{ch}, en pantalla {cw * sc}x{ch * sc}, posición ({ax}, {ay})")
    out = HERE / "previews"; out.mkdir(exist_ok=True)
    sheet.save(out / "tamanos_abigail.png")
    print("ok ->", out / "tamanos_abigail.png", sheet.size)


if __name__ == "__main__":
    main()
