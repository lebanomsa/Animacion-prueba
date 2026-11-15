"""Aswang (lengua fuera, 2x, murciélagos de la opción B) sobre el fondo de Percier, con las tres opciones de marco."""
import math
import numpy as np
from PIL import Image
import bucles_aswang as ba
import bucle_lengua_fondos as bf
import marco_aswang as mk

OUT = ba.OUT


def main():
    r = ba.cargar()
    seq2 = [bf.x2(f) for f in r.seq2]; seq1 = [bf.x2(f) for f in r.seq1]
    bg = bf.recorte("percier")
    ventana = np.zeros((126, 126), bool); ventana[23:103, 23:103] = True
    head = (bf.CX + 2 * bf.Z, bf.SUELO_G - 31 * bf.Z)

    def capa(bs):
        lz = Image.new("RGBA", (126, 126), (0, 0, 0, 0))
        for im, x, y in bs: ba.pegar(lz, im, x - im.width / 2, y - im.height / 2)
        a = np.array(lz); a[~ventana] = 0
        return Image.fromarray(a, "RGBA")

    for op in mk.PALETAS:
        frames = []
        for t in range(8):
            c = Image.new("RGBA", (126, 126), (0, 0, 0, 255)); c.paste(bg, (23, 23)); c.alpha_composite(mk.frame_126(op, t))
            det, del_ = [], []
            for b in (0, 1):
                ang = math.radians(bf.GRADOS * t + 180 * b)
                x, y, prof = head[0] + bf.RX * math.cos(ang), head[1] + bf.RY * math.sin(ang), math.sin(ang)
                (del_ if prof > 0 else det).append((seq1[(t + 4 * b) % 8], x, y))
            c.alpha_composite(capa(det))
            cx, by = ba.ha.pies(seq2[t]); ba.pegar(c, seq2[t], bf.CX - cx, bf.SUELO_G - by)
            c.alpha_composite(capa(del_))
            frames.append(c.convert("RGB"))
        n = max(len(np.unique(np.asarray(f).reshape(-1, 3), axis=0)) for f in frames)
        ag = ba.gif_local([f.resize((504, 504), Image.NEAREST) for f in frames], OUT / f"marco_{op}_aswang_x4.gif", ba.TICK)
        a = [np.asarray(f).astype(int) for f in frames]
        d = lambda x, y: int((np.abs(x - y).sum(-1) > 0).sum())
        print(op, "colores máx", n, "agrupados", ag, "| último->primero", d(a[-1], a[0]), "px; mediana", int(np.median([d(a[i], a[(i + 1) % 8]) for i in range(8)])))
        s = Image.new("RGB", (2 * 514, 2 * 514), (20, 20, 20))
        for j, t in enumerate((0, 2, 4, 6)): s.paste(frames[t].resize((504, 504), Image.NEAREST), ((j % 2) * 514, (j // 2) * 514))
        s.save(OUT / f"marco_{op}_momentos.png")


if __name__ == "__main__":
    main()
