"""Aswang 2x (lengua fuera) con los murciélagos siempre dentro de la ventana de 80x80:
  A: murciélagos a 2x en una órbita pequeña (radio 11 x 7) a la altura del pecho
  D: murciélagos a tamaño normal (1x) en una órbita más amplia (radio 22 x 8) a la altura de la cara
Aswang sí asoma 8 px por la banda de arriba, como antes."""
import math
import numpy as np
from PIL import Image
import bucles_aswang as ba

OUT, TICK = ba.OUT, ba.TICK
Z = 2
CX, SUELO_G = 63, 23 + 72
GRADOS = 22.5
CONF = {"A": dict(z=2, c=(CX + 4, 50), rx=11, ry=7), "D": dict(z=1, c=(CX + 4, 44), rx=22, ry=8)}


def x2(im, z=Z): return im.resize((im.width * z, im.height * z), Image.NEAREST)


def main():
    r = ba.cargar()
    seq2 = [x2(f) for f in r.seq2]
    fr, _ = ba.marco.build()
    img = np.array(fr); o = img[..., 3] > 0
    q = Image.fromarray(img[..., :3][o].reshape(-1, 1, 3), "RGB").quantize(colors=40, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    img[..., :3][o] = np.array(q.getpalette()[:120], np.uint8).reshape(-1, 3)[np.asarray(q).reshape(-1)]
    marco_im = Image.fromarray(img, "RGBA").crop((1, 1, 127, 127))
    ventana = np.zeros((126, 126), bool); ventana[23:103, 23:103] = True
    for modo, cf in CONF.items():
        seq1 = [x2(f, cf["z"]) for f in r.seq1]
        frames, fuera, visibles = [], [], []
        for t in range(8):
            c = Image.new("RGBA", (126, 126), (0, 0, 0, 255))
            c.paste(Image.new("RGBA", (80, 80), ba.FONDO), (23, 23)); c.paste(Image.new("RGBA", (80, 8), ba.SUELO_COL), (23, 23 + 72))
            c.alpha_composite(marco_im)
            det, del_ = [], []
            for b in (0, 1):
                ang = math.radians(GRADOS * t + 180 * b)
                x, y, prof = cf["c"][0] + cf["rx"] * math.cos(ang), cf["c"][1] + cf["ry"] * math.sin(ang), math.sin(ang)
                im = seq1[(t + 4 * b) % 8]
                (del_ if prof > 0 else det).append((im, x, y))
            def capa(bs):
                lz = Image.new("RGBA", (126, 126), (0, 0, 0, 0))
                for im, x, y in bs: ba.pegar(lz, im, x - im.width / 2, y - im.height / 2)
                return lz
            Ld, Lf = capa(det), capa(del_)
            ad, af = np.asarray(Ld)[..., 3] > 0, np.asarray(Lf)[..., 3] > 0
            fuera.append(int(((ad | af) & ~ventana).sum()))
            cx, by = ba.ha.pies(seq2[t])
            ela = Image.new("RGBA", (126, 126), (0, 0, 0, 0)); ba.pegar(ela, seq2[t], CX - cx, SUELO_G - by)
            ae = np.asarray(ela)[..., 3] > 0
            visibles.append((int((ad & ~ae).sum() + af.sum()), int(ad.sum() + af.sum())))
            c.alpha_composite(Ld); c.alpha_composite(ela); c.alpha_composite(Lf)
            frames.append(c.convert("RGB"))
        ag = ba.gif_local([f.resize((504, 504), Image.NEAREST) for f in frames], OUT / f"lengua_2x_{modo}_x4.gif", TICK)
        a = [np.asarray(f).astype(int) for f in frames]
        d = lambda x, y: int((np.abs(x - y).sum(-1) > 0).sum())
        vis = sum(v for v, _ in visibles) / max(1, sum(t for _, t in visibles))
        print(modo, "agrupados", ag, "| último->primero", d(a[-1], a[0]), "px; mediana", int(np.median([d(a[i], a[(i + 1) % 8]) for i in range(8)])),
              "| píxeles de murciélago fuera de la ventana por paso:", fuera, "| murciélago visible (no tapado por ella):", f"{100 * vis:.0f} %")
        s = Image.new("RGB", (4 * 254, 2 * 254), (10, 10, 10))
        for j in range(8): s.paste(frames[j].resize((252, 252), Image.NEAREST), ((j % 4) * 254, (j // 4) * 254))
        s.save(OUT / f"lengua_2x_{modo}_momentos.png")


if __name__ == "__main__":
    main()
