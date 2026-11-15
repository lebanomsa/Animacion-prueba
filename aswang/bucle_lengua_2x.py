"""Aswang (lengua fuera) y murciélagos al doble de tamaño (cada píxel del sprite = 2x2 de la rejilla de 126), por delante del marco: la cabeza asoma por la banda de arriba."""
import math
import numpy as np
from PIL import Image
import bucles_aswang as ba

OUT, TICK = ba.OUT, ba.TICK
Z = 2
CX, SUELO_G = 63, 23 + 72            # centro de la ventana (rejilla de 126) y fila del suelo
RX, RY, GRADOS = 22 * Z, 8 * Z, 22.5


def x2(im): return im.resize((im.width * Z, im.height * Z), Image.NEAREST)


def main():
    r = ba.cargar()
    seq2 = [x2(f) for f in r.seq2]; seq1 = [x2(f) for f in r.seq1]
    fr, _ = ba.marco.build()
    img = np.array(fr); o = img[..., 3] > 0
    q = Image.fromarray(img[..., :3][o].reshape(-1, 1, 3), "RGB").quantize(colors=40, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    img[..., :3][o] = np.array(q.getpalette()[:120], np.uint8).reshape(-1, 3)[np.asarray(q).reshape(-1)]
    marco_im = Image.fromarray(img, "RGBA").crop((1, 1, 127, 127))
    head = (CX + 2 * Z, SUELO_G - 31 * Z)
    frames = []
    for t in range(8):
        c = Image.new("RGBA", (126, 126), (0, 0, 0, 255))
        c.paste(Image.new("RGBA", (80, 80), ba.FONDO), (23, 23)); c.paste(Image.new("RGBA", (80, 8), ba.SUELO_COL), (23, 23 + 72))
        c.alpha_composite(marco_im)
        delante = []
        for b in (0, 1):
            ang = math.radians(GRADOS * t + 180 * b)
            x, y, prof = head[0] + RX * math.cos(ang), head[1] + RY * math.sin(ang), math.sin(ang)
            im = seq1[(t + 4 * b) % 8]
            if prof > 0: delante.append((im, x, y))
            else: ba.pegar(c, im, x - im.width / 2, y - im.height / 2)
        cx, by = ba.ha.pies(seq2[t])
        ba.pegar(c, seq2[t], CX - cx, SUELO_G - by)
        for im, x, y in delante: ba.pegar(c, im, x - im.width / 2, y - im.height / 2)
        frames.append(c.convert("RGB"))
    ag = ba.gif_local([f.resize((504, 504), Image.NEAREST) for f in frames], OUT / "lengua_2x_x4.gif", TICK)
    a = [np.asarray(f).astype(int) for f in frames]
    d = lambda x, y: int((np.abs(x - y).sum(-1) > 0).sum())
    print("2x:", len(frames), "pasos; agrupados", ag, "; último->primero", d(a[-1], a[0]), "px; mediana", int(np.median([d(a[i], a[(i + 1) % 8]) for i in range(8)])))
    w, h = seq2[0].size; cx0, by0 = ba.ha.pies(seq2[0])
    print("Aswang 2x mide", w, "x", h, "px; cabeza sobresale de la ventana por", max(0, 23 - (SUELO_G - by0 - h)) if False else max(0, 23 - (SUELO_G - h)), "px; ancho de la ventana 80")
    s = Image.new("RGB", (4 * 254, 2 * 254), (10, 10, 10))
    for j in range(8): s.paste(frames[j].resize((252, 252), Image.NEAREST), ((j % 4) * 254, (j // 4) * 254))
    s.save(OUT / "lengua_2x_momentos.png")


if __name__ == "__main__":
    main()
