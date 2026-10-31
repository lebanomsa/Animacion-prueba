"""Animación de Alma: criatura felina -> se levanta -> estalla en luz -> forma humana de rodillas.

29 fotogramas de las 4 hojas, en orden, con el fondo transparente. Cada hoja se alinea por su suelo (la fila inferior
del cuerpo) y en horizontal cada fotograma se encadena con el anterior por máximo solape de silueta (IoU); entre hojas
se enlaza el último fotograma de una con el primero de la siguiente de la misma forma.
Pasos de 70 ms. Salida: alma.gif y alma_x2.gif (transparentes, en bucle).
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import hojas                    # noqa: E402

TICK = 70
CW, CH = 130, 120               # lienzo
SUELO = 108                     # fila del lienzo donde queda el suelo del cuerpo
CX = 65

# pasos que dura cada fotograma (1 paso = 70 ms), por hoja
PASOS = {
    0: [2, 2, 2, 2, 2, 2, 2, 2, 2],         # alma 1: la cola menea, ritmo tranquilo
    1: [2, 2, 2, 2, 2, 2, 2, 2],            # alma 2: se levanta
    2: [2, 1, 1, 2, 3],                     # alma 3: el pelo se eriza y estalla (rápido) y la nube se asienta
    3: [2, 2, 2, 2, 2, 2, 6],               # alma 4: emerge y se queda mirando
}


def _mask(img, x, y):
    m = np.zeros((CH, CW), bool)
    a = np.asarray(img.getchannel("A")) > 0
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + a.shape[1], CW), min(y + a.shape[0], CH)
    if x1 > x0 and y1 > y0:
        m[y0:y1, x0:x1] = a[y0 - y:y1 - y, x0 - x:x1 - x]
    return m


def alinear(F, search=12):
    pos = []
    for k, f in enumerate(F):
        img = f["img"]
        y = SUELO - (f["y1"] - f["y0"]) - 0            # el suelo del cuerpo queda en SUELO
        y = SUELO + 1 - img.height
        if k == 0:
            x = CX - img.width // 2
        else:
            px, py = pos[-1]
            prev = _mask(F[k - 1]["img"], px, py)
            best = None
            for dx in range(-search, search + 1):
                xt = px + (F[k - 1]["img"].width - img.width) // 2 + dx
                m = _mask(img, xt, y)
                score = (m & prev).sum() / max((m | prev).sum(), 1) - 0.002 * abs(dx)
                if best is None or score > best[0]:
                    best = (score, xt)
            x = best[1]
        pos.append((x, y))
    out = []
    for f, (x, y) in zip(F, pos):
        c = Image.new("RGBA", (CW, CH), (0, 0, 0, 0)); c.alpha_composite(f["img"], (x, y)); out.append(c)
    return out, pos


def main(save=True):
    F = hojas.fotogramas()
    lienzos, pos = alinear(F)
    print("posiciones (x, y):", pos)
    frames = []
    for f, c in zip(F, lienzos):
        frames += [c] * PASOS[f["hoja"]][f["n"]]
    print(f"{len(F)} fotogramas -> {len(frames)} pasos = {len(frames) * TICK} ms")
    boxes = [b for b in (c.getchannel("A").getbbox() for c in lienzos) if b]
    box = (max(min(b[0] for b in boxes) - 2, 0), max(min(b[1] for b in boxes) - 2, 0),
           min(max(b[2] for b in boxes) + 2, CW), min(max(b[3] for b in boxes) + 2, CH))
    frames = [fr.crop(box) for fr in frames]
    print("lienzo recortado:", frames[0].size, "desde", box)
    if not save:
        return frames, box

    def save_gif(imgs, path, scale):
        imgs = [i.resize((i.width * scale, i.height * scale), Image.NEAREST) if scale > 1 else i for i in imgs]
        colors = sorted({p[:3] for im in imgs for p in im.getdata() if p[3]})
        assert len(colors) <= 255
        index = {c: i + 1 for i, c in enumerate(colors)}
        flat = [255, 0, 255] + [v for c in colors for v in c]
        pal = []
        for im in imgs:
            p = Image.new("P", im.size, 0); p.putpalette(flat + [0] * (768 - len(flat)))
            p.putdata([index[q[:3]] if q[3] else 0 for q in im.getdata()]); pal.append(p)
        pal[0].save(path, save_all=True, append_images=pal[1:], duration=TICK, loop=0,
                    transparency=0, disposal=2, optimize=False)
        return len(colors)

    for scale, suf in ((1, ""), (2, "_x2")):
        path = HERE / f"alma{suf}.gif"
        n = save_gif(frames, path, scale)
        print(f"{path.name}: {len(frames)} pasos, {n} colores, {path.stat().st_size / 1024:.0f} KB")
    # hoja de contacto de los 29 fotogramas
    cols = 10; w, h = frames[0].size
    uniq = [c.crop(box) for c in lienzos]
    rows = (len(uniq) + cols - 1) // cols
    sheet = Image.new("RGBA", (w * cols, h * rows), (60, 20, 30, 255))
    for i, f in enumerate(uniq):
        sheet.alpha_composite(f, ((i % cols) * w, (i // cols) * h))
    sheet.save(Path("/projects/sandbox/tmp") / "alma_hoja.png")


if __name__ == "__main__":
    main()
