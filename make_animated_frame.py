"""Compone marco azul + fondo + animación 'prueba 2.gif' en un GIF de 1024x1024.

Capas (de atrás hacia delante): negro -> fondo (recorte cuadrado x5) -> animación (x5) -> marco.
La animación se recorta a la misma zona que el fondo (125x125 centrales), así que todo
queda alineado 1:1 con el fondo. Todo se escala con vecino más cercano.
"""
from pathlib import Path

from PIL import Image, ImageSequence

HERE = Path(__file__).parent
OUT = HERE / "out"
SCALE_FRAME = 8        # el marco está dibujado a 128x128 -> 1024
SCALE_CONTENT = 5      # fondo y animación (125 px -> 625 px)
WIN = (24, 24, 104, 104)   # ventana interior del marco en px lógicos (x0, y0, x1, y1)
FRAME_COLORS = 170         # tonos del marco (+42 del fondo +37 del sprite < 256)


def main():
    # El marco aprobado usa ~750 tonos por el degradado continuo. Para que todo el GIF
    # quepa en una única paleta de 256 colores se agrupan los tonos casi idénticos.
    f128 = Image.open(OUT / "frame_blue_128.png").convert("RGBA")
    alpha = f128.getchannel("A")
    q = f128.convert("RGB").quantize(colors=FRAME_COLORS, method=Image.Quantize.MEDIANCUT,
                                     dither=Image.Dither.NONE).convert("RGB")
    diffs = [max(abs(a - b) for a, b in zip(p, r)) for p, r in
             zip(f128.convert("RGB").getdata(), q.getdata())]
    print(f"marco: {FRAME_COLORS} tonos | diferencia máxima por canal: {max(diffs)} "
          f"| media: {sum(diffs) / len(diffs):.2f}")
    q.putalpha(alpha)
    frame = q.resize((128 * SCALE_FRAME, 128 * SCALE_FRAME), Image.NEAREST)
    fondo = Image.open(HERE / "fondo.png").convert("RGBA")
    src = Image.open(HERE / "prueba 2.gif")

    side = fondo.height
    cx0 = (fondo.width - side) // 2
    box = (cx0, 0, cx0 + side, side)

    wx, wy = WIN[0] * SCALE_FRAME, WIN[1] * SCALE_FRAME
    ww, wh = (WIN[2] - WIN[0]) * SCALE_FRAME, (WIN[3] - WIN[1]) * SCALE_FRAME
    size = side * SCALE_CONTENT
    ox, oy = wx + (ww - size) // 2, wy + (wh - size) // 2

    base = Image.new("RGBA", frame.size, (0, 0, 0, 255))
    base.alpha_composite(fondo.crop(box).resize((size, size), Image.NEAREST), (ox, oy))

    frames, durations, clipped = [], [], []
    for i, f in enumerate(ImageSequence.Iterator(src)):
        sp = f.convert("RGBA")
        full = sp.getchannel("A").point(lambda a: 255 if a else 0).getbbox()
        # píxeles opacos que quedan fuera del recorte (se pierden)
        inside = sp.crop(box).getchannel("A").point(lambda a: 255 if a else 0)
        lost = sum(1 for v in sp.getchannel("A").getdata() if v) - sum(1 for v in inside.getdata() if v)
        clipped.append(lost)
        img = base.copy()
        img.alpha_composite(sp.crop(box).resize((size, size), Image.NEAREST), (ox, oy))
        img.alpha_composite(frame)
        frames.append(img.convert("RGB"))
        durations.append(f.info.get("duration", 90))

    print("fotogramas:", len(frames), "| píxeles del sprite recortados por fotograma:", clipped)

    colors = set()
    for im in frames:
        colors.update(c for _, c in im.getcolors(maxcolors=1024 * 1024))
    print("colores únicos en total:", len(colors))

    # Paleta global única y exacta (sin tramado ni pérdida): no hay parpadeo entre fotogramas.
    assert len(colors) <= 256, f"{len(colors)} colores: no caben en una paleta de GIF"
    ordered = sorted(colors)
    index = {c: i for i, c in enumerate(ordered)}
    flat = [v for c in ordered for v in c]
    pal = []
    for im in frames:
        p = Image.new("P", im.size)
        p.putpalette(flat + [0] * (768 - len(flat)))
        p.putdata([index[c] for c in im.getdata()])
        pal.append(p)
    # comprobación: el GIF reproduce los fotogramas sin ningún cambio de color
    assert all(list(a.convert("RGB").getdata()) == list(b.getdata()) for a, b in zip(pal, frames))
    print("paleta global exacta:", len(colors), "colores")

    path = OUT / "marco_animado_1024.gif"
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=durations,
                loop=0, disposal=1, optimize=False)
    print("guardado:", path, f"{path.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
