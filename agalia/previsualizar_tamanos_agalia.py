"""Opciones para agrandar a Agalia dentro del marco rojo con agalia stage.

La ventana mide 640x640 px: a escala s solo caben 640/s píxeles del dibujo (x3: 213, x4: 160, x5: 128).
El ancho lo marca la silueta con las alas (92 px) más las chispas de los lados; por eso para subir de escala
hay que cambiar el tamaño o la posición de las chispas.
Salida: previews/tamanos_agalia.png (columnas = pasos 10, 14, 18 y 30).
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
import make_agalia as ma        # noqa: E402
import marco                    # noqa: E402
from componer_marco_agalia import ROJO_CLARO, ROJO_OSCURO, BG_X0, BG_COLS, BG_ROWS  # noqa: E402

S_FRAME = 8
STEPS = (10, 14, 18, 30)
# nombre, escala del personaje, escala de las chispas, modo, separación de las chispas
OPCIONES = [
    ("Actual: personaje x3, chispas x2 a los lados", 3, 2, "lados", 1),
    ("A: personaje x4, chispas x1 (tamaño original) a los lados", 4, 1, "lados", 2),
    ("B: personaje x4, chispas x2 a los lados, metidas detrás de las alas", 4, 2, "lados", -28),
    ("C: personaje x5, chispas x1 encima de la cabeza", 5, 1, "arriba", 2),
]


def render(sc_spark, mode, gap):
    ma.SPARK_SCALE, ma.SPARK_MODE, ma.SPARK_GAP = sc_spark, mode, gap
    with contextlib.redirect_stdout(io.StringIO()):
        frames, box = ma.main(save=False)
    return frames


def main():
    frame, (wx0, wy0, wx1, wy1) = marco.build(ROJO_CLARO, ROJO_OSCURO)
    win_x, win_y = wx0 * S_FRAME, wy0 * S_FRAME
    win = (wx1 - wx0 + 1) * S_FRAME
    marco_big = frame.resize((marco.N * S_FRAME,) * 2, Image.NEAREST)
    bg = Image.open(ROOT / "agalia stage.png").convert("RGB")
    crop = np.asarray(bg.crop((BG_X0, 0, BG_X0 + BG_COLS, BG_ROWS)))
    big = np.asarray(Image.fromarray(crop).resize((BG_COLS * 5, BG_ROWS * 5), Image.NEAREST))
    pad = win - big.shape[0]
    mirror = np.asarray(Image.fromarray(crop[:pad // 5][::-1]).resize((BG_COLS * 5, pad), Image.NEAREST))
    bg_big = Image.fromarray(np.concatenate([mirror, big], axis=0), "RGB").convert("RGBA")

    W, T = 512, 18
    sheet = Image.new("RGB", (W * len(STEPS), (W + T) * len(OPCIONES)), (20, 10, 14))
    d = ImageDraw.Draw(sheet)
    for r, (nombre, sc, sc_spark, mode, gap) in enumerate(OPCIONES):
        frames = render(sc_spark, mode, gap)
        boxes = [b for b in (f.getchannel("A").getbbox() for f in frames) if b]
        ub = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
        cw, ch = ub[2] - ub[0], ub[3] - ub[1]
        fits = cw * sc <= win and ch * sc <= win
        ax = (win - cw * sc) // 2
        ay = max(0, win - 20 - ch * sc)
        d.text((6, r * (W + T) + 4), f"{nombre}  |  contenido {cw}x{ch} px -> {cw * sc}x{ch * sc} px "
               f"(ventana 640x640){'' if fits else '  | NO CABE'}", fill=(255, 255, 255))
        for c, s_ in enumerate(STEPS):
            f = frames[s_].crop(ub).resize((cw * sc, ch * sc), Image.NEAREST)
            layer = bg_big.copy()
            if fits:
                layer.alpha_composite(f, (max(ax, 0), ay))
            img = Image.new("RGBA", (1024, 1024), (0, 0, 0, 255))
            img.alpha_composite(layer, (win_x, win_y))
            img.alpha_composite(marco_big)
            sheet.paste(img.convert("RGB").resize((W, W), Image.LANCZOS), (c * W, r * (W + T) + T))
        print(f"{nombre}: contenido {cw}x{ch} -> {cw * sc}x{ch * sc} {'cabe' if fits else 'NO CABE'}")
    out = HERE / "previews"; out.mkdir(exist_ok=True)
    sheet.save(out / "tamanos_agalia.png")
    print("ok ->", out / "tamanos_agalia.png", sheet.size)


if __name__ == "__main__":
    main()
