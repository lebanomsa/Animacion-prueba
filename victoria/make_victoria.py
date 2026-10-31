"""Animación 'victoria' de Matilda a partir de 'matilda victoria.PNG' (15 fotogramas).

La hoja tiene una rejilla de celdas de 94x122 px (11 en la primera fila y 4 en la segunda),
separadas 100 px, con fondo magenta (248, 0, 248) que aquí se vuelve transparente.
El cuerpo cambia cada dos fotogramas (1-2, 3-4, ...) y los efectos (explosiones con nota
azul, rosa y amarilla) cambian en cada fotograma, así que se respetan los 15 fotogramas tal cual.

Salida: matilda_victoria.gif (tamaño original) y matilda_victoria_x4.gif (ampliado x4, vecino
más cercano). Fondo transparente y bucle infinito.
"""
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
SRC = HERE.parent / "matilda victoria.PNG"
MAG = (248, 0, 248)
CELL_W, CELL_H, PITCH = 94, 122, 100
ROW_Y = (11, 151)
COLS = 11
N = 15
TICK = 80      # ms por fotograma (15 fotogramas = 1200 ms por vuelta)


def cells():
    sheet = Image.open(SRC).convert("RGBA")
    out = []
    for k in range(N):
        r, c = divmod(k, COLS)
        x0, y0 = 17 + PITCH * c, ROW_Y[r]
        a = np.asarray(sheet.crop((x0, y0, x0 + CELL_W, y0 + CELL_H))).copy()
        a[(a[..., 0] == MAG[0]) & (a[..., 1] == MAG[1]) & (a[..., 2] == MAG[2])] = (0, 0, 0, 0)
        out.append(Image.fromarray(a, "RGBA"))
    return out


def save_gif(frames, path, scale=1):
    imgs = [f.resize((f.width * scale, f.height * scale), Image.NEAREST) if scale > 1 else f
            for f in frames]
    colors = sorted({c[:3] for im in imgs for c in im.getdata() if c[3]})
    assert len(colors) <= 255, len(colors)
    index = {c: i + 1 for i, c in enumerate(colors)}          # 0 = transparente
    flat = [255, 0, 255] + [v for c in colors for v in c]
    pal = []
    for im in imgs:
        p = Image.new("P", im.size, 0)
        p.putpalette(flat + [0] * (768 - len(flat)))
        p.putdata([index[c[:3]] if c[3] else 0 for c in im.getdata()])
        pal.append(p)
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=TICK, loop=0,
                transparency=0, disposal=2, optimize=False)
    return len(colors)


def main():
    frames = cells()
    # recorte común (el mismo en todos los fotogramas, para que Matilda no se mueva)
    boxes = [f.getchannel("A").getbbox() for f in frames]
    box = (min(b[0] for b in boxes), min(b[1] for b in boxes),
           max(b[2] for b in boxes), max(b[3] for b in boxes))
    frames = [f.crop(box) for f in frames]
    print(f"{len(frames)} fotogramas, lienzo {frames[0].size} (recorte {box})")
    for scale, suf in ((1, ""), (4, "_x4")):
        path = HERE / f"matilda_victoria{suf}.gif"
        n = save_gif(frames, path, scale)
        print(f"{path.name}: {n} colores, {path.stat().st_size / 1024:.0f} KB, "
              f"{len(frames)} x {TICK} ms = {len(frames) * TICK} ms")


if __name__ == "__main__":
    main()
