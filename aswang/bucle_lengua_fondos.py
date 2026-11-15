"""Aswang 2x con la lengua fuera y los murciélagos de la opción B (cortados por el borde de la ventana), sobre fondos reales de 80x80 a tamaño nativo."""
import math
import numpy as np
from PIL import Image
import bucles_aswang as ba

HERE = ba.HERE
OUT, TICK = ba.OUT, ba.TICK
Z = 2
CX, SUELO_G = 63, 23 + 72
RX, RY, GRADOS = 22 * Z, 8 * Z, 22.5
K_FONDO = 48
FONDOS = {"percier": ("fondo_percier.png", 300, 232), "fondo2": ("fondo_2.png", 120, 128)}   # archivo, x0, y0 del recorte de 80x80 (el suelo cae en la fila 72)


def x2(im): return im.resize((im.width * Z, im.height * Z), Image.NEAREST)


def agrupar(rgb, k):
    q = Image.fromarray(rgb.reshape(-1, 1, 3).astype(np.uint8), "RGB").quantize(colors=k, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = np.array(q.getpalette()[:768], np.uint8).reshape(-1, 3)
    return pal[np.asarray(q).reshape(-1)]


def recorte(nombre):
    f, x0, y0 = FONDOS[nombre]
    a = np.asarray(Image.open(HERE / "fuentes" / f).convert("RGB"))[y0:y0 + 80, x0:x0 + 80]
    return Image.fromarray(agrupar(a, K_FONDO).reshape(a.shape)).convert("RGBA")


def main():
    r = ba.cargar()
    seq2 = [x2(f) for f in r.seq2]; seq1 = [x2(f) for f in r.seq1]
    fr, _ = ba.marco.build()
    img = np.array(fr); o = img[..., 3] > 0
    img[..., :3][o] = agrupar(img[..., :3][o], 40)
    marco_im = Image.fromarray(img, "RGBA").crop((1, 1, 127, 127))
    ventana = np.zeros((126, 126), bool); ventana[23:103, 23:103] = True
    head = (CX + 2 * Z, SUELO_G - 31 * Z)

    def capa(bs):
        lz = Image.new("RGBA", (126, 126), (0, 0, 0, 0))
        for im, x, y in bs: ba.pegar(lz, im, x - im.width / 2, y - im.height / 2)
        a = np.array(lz); a[~ventana] = 0
        return Image.fromarray(a, "RGBA")

    for nombre in FONDOS:
        bg = recorte(nombre); frames = []
        for t in range(8):
            c = Image.new("RGBA", (126, 126), (0, 0, 0, 255)); c.paste(bg, (23, 23)); c.alpha_composite(marco_im)
            det, del_ = [], []
            for b in (0, 1):
                ang = math.radians(GRADOS * t + 180 * b)
                x, y, prof = head[0] + RX * math.cos(ang), head[1] + RY * math.sin(ang), math.sin(ang)
                (del_ if prof > 0 else det).append((seq1[(t + 4 * b) % 8], x, y))
            c.alpha_composite(capa(det))
            cx, by = ba.ha.pies(seq2[t]); ba.pegar(c, seq2[t], CX - cx, SUELO_G - by)
            c.alpha_composite(capa(del_))
            frames.append(c.convert("RGB"))
        n = max(len(np.unique(np.asarray(f).reshape(-1, 3), axis=0)) for f in frames)
        ag = ba.gif_local([f.resize((504, 504), Image.NEAREST) for f in frames], OUT / f"aswang_{nombre}_x4.gif", TICK)
        a = [np.asarray(f).astype(int) for f in frames]
        d = lambda x, y: int((np.abs(x - y).sum(-1) > 0).sum())
        print(nombre, "colores máx", n, "agrupados", ag, "| último->primero", d(a[-1], a[0]), "px; mediana", int(np.median([d(a[i], a[(i + 1) % 8]) for i in range(8)])))
        s = Image.new("RGB", (4 * 254, 2 * 254), (10, 10, 10))
        for j in range(8): s.paste(frames[j].resize((252, 252), Image.NEAREST), ((j % 4) * 254, (j // 4) * 254))
        s.save(OUT / f"fondo_{nombre}_momentos.png")
        bg.convert("RGB").resize((320, 320), Image.NEAREST).save(OUT / f"fondo_{nombre}_recorte.png")


if __name__ == "__main__":
    main()
