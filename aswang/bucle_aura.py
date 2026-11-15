"""Aswang: aura de sangre a 2x que empieza con la lengua fuera (secuencia 2), se agacha (3), aura de colores (4), pose final y una nube de humo que tapa el cambio de vuelta a la lengua.
56 pasos de 80 ms (múltiplo de 8, para que los detalles animados del marco cierren). Fondo de Percier y marco 'sangre y oro'.
  A: todo a 2x; Aswang y el humo pueden sobresalir por delante del marco; el anillo de fuego y los murciélagos se cortan en el borde de la ventana
  C: todo se corta en el borde de la ventana; para que la lengua entre entera, Aswang apoya los pies en el borde de abajo de la ventana"""
import math
import numpy as np
from PIL import Image
import bucles_aswang as ba
import bucle_lengua_fondos as bf
import marco_aswang as mk
import hoja_aswang as ha

OUT, TICK = ba.OUT, ba.TICK
Z, CX, N = 2, 63, 56
SMOKE = list(range(26))


def x2(im): return im.resize((im.width * Z, im.height * Z), Image.NEAREST)


def main():
    r = ba.cargar()
    seq1 = [x2(f) for f in r.seq1]; seq2 = [x2(f) for f in r.seq2]; seq3 = [x2(f) for f in r.seq3]; seq4 = [x2(f) for f in r.seq4]
    fin = x2(r.fin); anillo = [x2(f) for f in r.anillo]
    humo = [x2(ha.recorte(c)) for c in ha.fila(1817) + ha.fila(1877)]     # celdas completas de 50x50: la nube se ancla siempre en el mismo punto
    bg = bf.recorte("percier")
    ventana = np.zeros((126, 126), bool); ventana[23:103, 23:103] = True

    def clip(lz):
        a = np.array(lz); a[~ventana] = 0
        return Image.fromarray(a, "RGBA")

    for var in ("A", "C"):
        suelo = 23 + (72 if var == "A" else 80)
        head = (CX + 2 * Z, suelo - 31 * Z)
        frames = []; descubiertos = []
        for t in range(N):
            c = Image.new("RGBA", (126, 126), (0, 0, 0, 255)); c.paste(bg, (23, 23)); c.alpha_composite(mk.frame_126("sangre", t))
            # quién es Aswang en este paso
            if t < 16: ela = seq2[t % 8]
            elif t < 21: ela = seq3[t - 16]
            elif t < 45: ela = seq4[(t - 21) % 12]
            elif t < 54: ela = fin
            else: ela = seq2[6 + (t - 54)]
            # murciélagos solo mientras tiene la lengua fuera (pasos 0..15)
            det, del_ = [], []
            if t < 16:
                for b in (0, 1):
                    ang = math.radians(bf.GRADOS * t + 180 * b)
                    x, y, prof = head[0] + bf.RX * math.cos(ang), head[1] + bf.RY * math.sin(ang), math.sin(ang)
                    (del_ if prof > 0 else det).append((seq1[(t + 4 * b) % 8], x, y))
            def capa(bs):
                lz = Image.new("RGBA", (126, 126), (0, 0, 0, 0))
                for im, x, y in bs: ba.pegar(lz, im, x - im.width / 2, y - im.height / 2)
                return clip(lz)
            c.alpha_composite(capa(det))
            if 21 <= t < 45:                                   # anillo de fuego bajo los pies (siempre cortado por la ventana)
                lz = Image.new("RGBA", (126, 126), (0, 0, 0, 0)); a = anillo[((t - 21) // 2) % 6]
                ba.pegar(lz, a, CX - a.width / 2, suelo + 4 - a.height); c.alpha_composite(clip(lz))
            cx, by = ha.pies(ela)
            ela_l = Image.new("RGBA", (126, 126), (0, 0, 0, 0)); ba.pegar(ela_l, ela, CX - cx, suelo - by)
            if var == "C": ela_l = clip(ela_l)
            if var == "A": ba.pegar(c, ela, CX - cx, suelo - by)
            else:
                lz = Image.new("RGBA", (126, 126), (0, 0, 0, 0)); ba.pegar(lz, ela, CX - cx, suelo - by); c.alpha_composite(clip(lz))
            c.alpha_composite(capa(del_))
            # humo: crece en los pasos 46..55 (fotogramas 0..9) y se disipa en 0..15 (fotogramas 10..25)
            k = t - 46 if t >= 46 else (t + 10 if t < 16 else None)
            if k is not None and k < 26:
                h = humo[k]; h2 = h.transpose(Image.FLIP_LEFT_RIGHT)          # dos nubes (la segunda en espejo): una cubre la cabeza y la otra los pies
                lz = Image.new("RGBA", (126, 126), (0, 0, 0, 0))
                ba.pegar(lz, h, CX - h.width / 2, suelo - 62 - h.height / 2); ba.pegar(lz, h2, CX - h2.width / 2, suelo - 24 - h2.height / 2)
                if var == "A": c.alpha_composite(lz)
                else: c.alpha_composite(clip(lz))
                if t in (50, 52, 53, 54, 55):
                    vis = int(((np.asarray(Image.fromarray(np.asarray(ela_l)))[..., 3] > 0) & (np.asarray(lz)[..., 3] == 0)).sum())
                    descubiertos.append((t, vis))
            frames.append(c.convert("RGB"))
        n = max(len(np.unique(np.asarray(f).reshape(-1, 3), axis=0)) for f in frames)
        ag = ba.gif_local([f.resize((504, 504), Image.NEAREST) for f in frames], OUT / f"aura_{var}_x4.gif", TICK)
        a = [np.asarray(f).astype(int) for f in frames]
        d = lambda x, y: int((np.abs(x - y).sum(-1) > 0).sum())
        ds = [d(a[i], a[(i + 1) % N]) for i in range(N)]
        print(var, N, "pasos =", round(N * TICK / 1000, 2), "s; colores máx", n, "agrupados", ag, "| cierre (paso 55 -> 0):", ds[-1], "px; mediana entre pasos", int(np.median(ds)), "; mayores saltos:", sorted(((v, i) for i, v in enumerate(ds)), reverse=True)[:4], "| píxeles de Aswang sin cubrir por el humo (paso, px):", descubiertos)
        idx = [0, 5, 10, 16, 19, 23, 28, 35, 44, 47, 50, 53]
        s = Image.new("RGB", (4 * 254, 3 * 254), (20, 20, 20))
        for j, i in enumerate(idx): s.paste(frames[i].resize((252, 252), Image.NEAREST), ((j % 4) * 254, (j // 4) * 254))
        s.save(OUT / f"aura_{var}_momentos.png")


if __name__ == "__main__":
    main()
