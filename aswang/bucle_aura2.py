"""Aswang, aura de sangre a 2x (opción A), sin murciélagos y con el humo recortado.
56 pasos de 80 ms: lengua fuera (0-15, dos pasadas) / se agacha (16-20) / aura de colores con anillo de fuego (21-44, dos vueltas) / pose final quieta (45-50) / humo que crece (51-55)
y que se disipa en los pasos 0-8 del bucle siguiente. El cambio de la pose final a la lengua se hace en el paso 55, con la nube al máximo.
Aswang y el humo pueden sobresalir por delante del marco; el anillo de fuego se corta en el borde de la ventana. Fondo de Percier y marco 'sangre y oro'."""
import numpy as np
from PIL import Image
import bucles_aswang as ba
import bucle_lengua_fondos as bf
import marco_aswang as mk
import hoja_aswang as ha

OUT, TICK = ba.OUT, ba.TICK
Z, CX, N = 2, 63, 56
SUELO = 23 + 72
CRECE = [0, 2, 4, 6, 7]                       # fotogramas del humo en los pasos 51..55
SE_VA = [8, 10, 12, 14, 16, 18, 20, 22, 24]   # fotogramas del humo en los pasos 0..8


def x2(im): return im.resize((im.width * Z, im.height * Z), Image.NEAREST)


def cargar():
    r = ba.cargar()
    d = dict(seq2=[x2(f) for f in r.seq2], seq3=[x2(f) for f in r.seq3], seq4=[x2(f) for f in r.seq4], fin=x2(r.fin), anillo=[x2(f) for f in r.anillo],
             humo=[x2(ha.recorte(c)) for c in ha.fila(1817) + ha.fila(1877)])
    return d


def render(d, n_pasos=N):
    bg = bf.recorte("percier")
    ventana = np.zeros((126, 126), bool); ventana[23:103, 23:103] = True

    def clip(lz):
        a = np.array(lz); a[~ventana] = 0
        return Image.fromarray(a, "RGBA")

    fin_, sup_, inf_, descub = [], [], [], []
    for t in range(n_pasos):
        base = Image.new("RGBA", (126, 126), (0, 0, 0, 255)); base.paste(bg, (23, 23)); base.alpha_composite(mk.frame_126("sangre", t))
        inf_.append(base.copy())
        if t < 16: ela = d["seq2"][t % 8]
        elif t < 21: ela = d["seq3"][t - 16]
        elif t < 45: ela = d["seq4"][(t - 21) % 12]
        elif t < 55: ela = d["fin"]
        else: ela = d["seq2"][7]
        L = Image.new("RGBA", (126, 126), (0, 0, 0, 0))
        if 21 <= t < 45:
            a = d["anillo"][((t - 21) // 2) % 6]; lz = Image.new("RGBA", (126, 126), (0, 0, 0, 0))
            ba.pegar(lz, a, CX - a.width / 2, SUELO + 4 - a.height); L.alpha_composite(clip(lz))
        cx, by = ha.pies(ela); ba.pegar(L, ela, CX - cx, SUELO - by)
        ela_a = np.asarray(L)[..., 3] > 0
        k = CRECE[t - 51] if t >= 51 else (SE_VA[t] if t < len(SE_VA) else None)
        if k is not None:
            h = d["humo"][k]; h2 = h.transpose(Image.FLIP_LEFT_RIGHT)
            H = Image.new("RGBA", (126, 126), (0, 0, 0, 0))
            ba.pegar(H, h, CX - h.width / 2, SUELO - 62 - h.height / 2); ba.pegar(H, h2, CX - h2.width / 2, SUELO - 24 - h2.height / 2)
            humo_a = np.asarray(H)[..., 3] > 0
            L.alpha_composite(H)
            if t >= 51 or t < 3: descub.append((t, int((ela_a & ~humo_a).sum())))
        sup_.append(L)
        c = base.copy(); c.alpha_composite(L); fin_.append(c.convert("RGB"))
    return fin_, inf_, sup_, descub


def main():
    d = cargar(); fin_, inf_, sup_, descub = render(d)
    ag = ba.gif_local([f.resize((504, 504), Image.NEAREST) for f in fin_], OUT / "aura2_A_humo_corto_x4.gif", TICK)
    n = max(len(np.unique(np.asarray(f).reshape(-1, 3), axis=0)) for f in fin_)
    a = [np.asarray(f).astype(int) for f in fin_]
    ds = [int((np.abs(a[i] - a[(i + 1) % N]).sum(-1) > 0).sum()) for i in range(N)]
    print(N, "pasos =", round(N * TICK / 1000, 2), "s; colores máx", n, "agrupados", ag, "| cierre (55 -> 0):", ds[-1], "px; mediana", int(np.median(ds)))
    print("píxeles de Aswang sin cubrir por el humo (paso, px):", descub)
    dens = [int((np.asarray(d["humo"][k])[..., 3] > 0).sum()) for k in range(26)]
    print("opacidad del humo en los pasos 0..8 (px):", [dens[k] for k in SE_VA], "; en 51..55:", [dens[k] for k in CRECE], "; máx", max(dens))
    idx = [0, 2, 4, 6, 8, 16, 21, 28, 45, 52, 54, 55]
    s = Image.new("RGB", (4 * 254, 3 * 254), (20, 20, 20))
    for j, i in enumerate(idx): s.paste(fin_[i].resize((252, 252), Image.NEAREST), ((j % 4) * 254, (j // 4) * 254))
    s.save(OUT / "aura2_A_humo_corto_momentos.png")
    ts = [51, 52, 53, 54, 55, 0, 1, 2, 3, 4, 5, 6]
    t_ = Image.new("RGB", (6 * 254, 2 * 254), (20, 20, 20))
    for j, i in enumerate(ts): t_.paste(fin_[i].resize((252, 252), Image.NEAREST), ((j % 6) * 254, (j // 6) * 254))
    t_.save(OUT / "aura2_A_humo_corto_tira.png")


if __name__ == "__main__":
    main()
