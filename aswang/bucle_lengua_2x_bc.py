"""Aswang 2x (lengua fuera) con los murciélagos en la órbita grande, en dos versiones:
  B: los murciélagos quedan siempre dentro de la ventana de 80x80 (pasan por debajo del marco y se cortan en su borde)
  C: por la izquierda pueden salir por delante del marco; por la derecha y por arriba se cortan en el borde de la ventana
Aswang sí asoma 8 px por la banda de arriba, como antes."""
import math
import numpy as np
from PIL import Image
import bucles_aswang as ba

OUT, TICK = ba.OUT, ba.TICK
Z = 2
CX, SUELO_G = 63, 23 + 72
RX, RY, GRADOS = 22 * Z, 8 * Z, 22.5


def x2(im): return im.resize((im.width * Z, im.height * Z), Image.NEAREST)


def mascara(modo):
    m = np.zeros((126, 126), bool); m[23:103, 23:103] = True
    if modo == "C": m[:, :23] = True                # por la izquierda se puede salir por delante del marco
    return m


def capa(bats, modo):
    lz = Image.new("RGBA", (126, 126), (0, 0, 0, 0))
    for im, x, y in bats: ba.pegar(lz, im, x - im.width / 2, y - im.height / 2)
    a = np.array(lz); a[~mascara(modo)] = 0
    return Image.fromarray(a, "RGBA")


def main():
    r = ba.cargar()
    seq2 = [x2(f) for f in r.seq2]; seq1 = [x2(f) for f in r.seq1]
    fr, _ = ba.marco.build()
    img = np.array(fr); o = img[..., 3] > 0
    q = Image.fromarray(img[..., :3][o].reshape(-1, 1, 3), "RGB").quantize(colors=40, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    img[..., :3][o] = np.array(q.getpalette()[:120], np.uint8).reshape(-1, 3)[np.asarray(q).reshape(-1)]
    marco_im = Image.fromarray(img, "RGBA").crop((1, 1, 127, 127))
    head = (CX + 2 * Z, SUELO_G - 31 * Z)
    for modo in ("B", "C"):
        frames, recortados = [], []
        for t in range(8):
            c = Image.new("RGBA", (126, 126), (0, 0, 0, 255))
            c.paste(Image.new("RGBA", (80, 80), ba.FONDO), (23, 23)); c.paste(Image.new("RGBA", (80, 8), ba.SUELO_COL), (23, 23 + 72))
            c.alpha_composite(marco_im)
            det, del_ = [], []
            for b in (0, 1):
                ang = math.radians(GRADOS * t + 180 * b)
                x, y, prof = head[0] + RX * math.cos(ang), head[1] + RY * math.sin(ang), math.sin(ang)
                im = seq1[(t + 4 * b) % 8]
                (del_ if prof > 0 else det).append((im, x, y))
            full = Image.new("RGBA", (126, 126), (0, 0, 0, 0))
            for im, x, y in det + del_: ba.pegar(full, im, x - im.width / 2, y - im.height / 2)
            c.alpha_composite(capa(det, modo))
            cx, by = ba.ha.pies(seq2[t])
            ba.pegar(c, seq2[t], CX - cx, SUELO_G - by)
            c.alpha_composite(capa(del_, modo))
            recortados.append(int((np.asarray(full)[..., 3] > 0).sum()) - int((np.asarray(capa(det + del_, modo))[..., 3] > 0).sum()))
            frames.append(c.convert("RGB"))
        ag = ba.gif_local([f.resize((504, 504), Image.NEAREST) for f in frames], OUT / f"lengua_2x_{modo}_x4.gif", TICK)
        a = [np.asarray(f).astype(int) for f in frames]
        d = lambda x, y: int((np.abs(x - y).sum(-1) > 0).sum())
        print(modo, "agrupados", ag, "| último->primero", d(a[-1], a[0]), "px; mediana", int(np.median([d(a[i], a[(i + 1) % 8]) for i in range(8)])), "| píxeles de murciélago recortados por paso:", recortados)
        s = Image.new("RGB", (4 * 254, 2 * 254), (10, 10, 10))
        for j in range(8): s.paste(frames[j].resize((252, 252), Image.NEAREST), ((j % 4) * 254, (j // 4) * 254))
        s.save(OUT / f"lengua_2x_{modo}_momentos.png")


if __name__ == "__main__":
    main()
