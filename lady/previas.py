"""Vistas previas de las opciones de escenario de Lady con relámpago (ciclo de 24 pasos de 80 ms: 8 de destello y 16 de calma)."""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import escenario as e

HERE = Path(__file__).parent
PREV = HERE / "previews"
TICK = 80
CICLO = 24
LADY = e.lady_referencia()


def con_lady(win):
    w = win.copy()
    w.alpha_composite(LADY, ((128 - LADY.width) // 2, 120 - LADY.height))
    return w


def frames(v):
    return [con_lady(e.ventana(v, t if t < 8 else -1)).resize((640, 640), Image.NEAREST).convert("RGB") for t in range(CICLO)]


def gif(frs, ruta):
    arrs = [np.asarray(f) for f in frs]
    key = lambda a: a[..., 0].astype(np.uint32) << 16 | a[..., 1].astype(np.uint32) << 8 | a[..., 2]
    keys = np.unique(np.concatenate([key(a).ravel() for a in arrs]))
    n = len(keys)
    if n <= 256:
        pal = np.zeros(768, np.uint8)
        pal[0:n * 3:3], pal[1:n * 3:3], pal[2:n * 3:3] = keys >> 16, keys >> 8 & 255, keys & 255
        out = []
        for a in arrs:
            p = Image.fromarray(np.searchsorted(keys, key(a)).astype(np.uint8), "P"); p.putpalette(pal.tolist()); out.append(p)
    else:                                               # demasiados tonos: paleta común por corte mediano, sin tramado
        mosaico = Image.fromarray(np.concatenate([a[::4, ::4] for a in arrs[:12]], axis=0))
        q = mosaico.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        out = [f.quantize(palette=q, dither=Image.Dither.NONE) for f in frs]
    out[0].save(ruta, save_all=True, append_images=out[1:], duration=TICK, loop=0, disposal=1, optimize=False)
    return n


def main():
    PREV.mkdir(exist_ok=True)
    nombres = {"A": "cielo_y_cubierta", "B": "silueta_negra", "C": "muro_de_piedra"}
    hoja = Image.new("RGB", (3 * 440, 2 * 440 + 16), (14, 10, 20))
    d = ImageDraw.Draw(hoja)
    for i, v in enumerate("ABC"):
        fr = frames(v)
        ruta = PREV / f"escenario_{v}_{nombres[v]}.gif"
        n = gif(fr, ruta)
        print(f"{ruta.name}: {n} tonos, {ruta.stat().st_size / 1024:.0f} KB")
        d.text((i * 440 + 4, 2), f"{v}: {nombres[v]}", fill=(255, 220, 120))
        hoja.paste(fr[0].resize((420, 420), Image.LANCZOS), (i * 440, 16))
        hoja.paste(fr[12].resize((420, 420), Image.LANCZOS), (i * 440, 16 + 440))
    hoja.save(PREV / "escenarios_opciones.png")


if __name__ == "__main__":
    main()
