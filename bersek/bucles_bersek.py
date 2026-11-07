"""Special Bersek: propuestas de bucle de prueba sobre fondo neutro (sin marco ni escenario todavía), tamaño nativo 1x.
  2. contraataque : se encoge, rueda en bola, salta, golpea el suelo y sube un pilar de fuego delante de él
  3. especial     : se lanza con el cañón, arcos de llama, y una bola de fuego en forma de cometa cruza la escena y estalla
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "secuencia"))
import hoja_bersek as hb
import marco

OUT = HERE / "salida"
TICK = 70
W, H = 420, 190
SUELO, BX = 176, 60
FONDO, SUELO_COL = (30, 32, 40, 255), (22, 24, 30, 255)
PILAR_DX = 60            # el pilar de fuego sube a esta distancia por delante de Bersek


class R:
    pass


def cargar():
    r = R()
    r.idle = hb.fotogramas(10, 60, 0, 500)
    r.contra = hb.fotogramas(140, 206, 0, 1510)
    r.esp = hb.fotogramas(485, 541, 0, 1195)[:14]
    r.pilar = hb.fotogramas(206, 370, 0, 1730)
    r.bola = hb.fotogramas(541, 730, 0, 660)[:3]
    r.arcos = hb.fotogramas(588, 725, 650, 1390)
    return r


def pegar_pies(lz, img, x, y=SUELO):
    cx, by = hb.pies(img)
    lz.alpha_composite(img, (int(round(x - cx)), int(round(y - by))))


def pegar_base(lz, img, x, y=SUELO):
    """Ancla en el centro de la fila inferior (efectos de suelo como el pilar de fuego)."""
    lz.alpha_composite(img, (int(round(x - img.width / 2)), int(round(y - img.height))))


def nueva(fondo=True):
    lz = Image.new("RGBA", (W, H), FONDO if fondo else (0, 0, 0, 0))
    if fondo: lz.paste(Image.new("RGBA", (W, H - SUELO), SUELO_COL), (0, SUELO))
    return lz


# ------------------------------------------------------------------ 2. contraataque con pilar de fuego
def guion2(r):
    """Lista de dicts por paso: bers (imagen de Bersek), pilar (índice o None)."""
    P = []
    def b(img, n=1, **kw):
        for _ in range(n): P.append(dict(bers=img, **kw))
    for i in range(6): b(r.idle[i])
    b(r.contra[0], 2); b(r.contra[1])
    for i in range(2, 10): b(r.contra[i])                 # rueda en bola
    for i in range(10, 15): b(r.contra[i])                # salto
    t_golpe = len(P)
    b(r.contra[15], 2)                                    # cae con el cañón
    for i in (25, 26, 27): b(r.contra[i])
    for i in range(27):                                   # el pilar dura 27 pasos
        t = t_golpe + i
        while len(P) <= t: b(r.idle[len(P) % 8])
        P[t]["pilar"] = i
    n_idle = len(P)
    for t in range(len(P)):
        if t >= t_golpe + 5 and P[t]["bers"] is not None and "pilar" in P[t] and t >= t_golpe + 6:
            pass
    # tras recuperarse, vuelve a la espera con las chispas (idle 0..7) mientras el pilar se apaga
    for t in range(t_golpe + 6, len(P)):
        P[t]["bers"] = r.idle[(t - t_golpe - 6) % 8]
    return P


def render2(r, fondo=True, pilar_dx=None):
    fr = []
    for p in guion2(r):
        lz = nueva(fondo)
        if p.get("pilar") is not None:
            pegar_base(lz, r.pilar[p["pilar"]], BX + (PILAR_DX if pilar_dx is None else pilar_dx), SUELO + 2)
        pegar_pies(lz, p["bers"], BX)
        fr.append(lz)
    return fr


# ------------------------------------------------------------------ 3. ataque especial con bola de fuego
def guion3(r):
    P = []
    def b(img, n=1, **kw):
        for _ in range(n): P.append(dict(bers=img, **kw))
    for i in range(4): b(r.idle[i])
    b(r.esp[0], 2)
    for i in (1, 2, 3, 4): b(r.esp[i])
    t_arco = len(P)
    for i in (5, 6, 7): b(r.esp[i])
    for i in (8, 9, 10): b(r.esp[i])
    t_disp = len(P)
    b(r.esp[11], 2)
    for i in (12, 13): b(r.esp[i])
    # arcos de llama: 11 pasos desde que levanta el cañón
    for k in range(11):
        t = t_arco + k
        while len(P) <= t: b(r.idle[len(P) % 8])
        P[t]["arco"] = k
    # bola de fuego: cometa que viaja a la derecha y estalla (2 pasos de llama + 3 de bola grande)
    vuelo = 8
    for k in range(vuelo + 5):
        t = t_disp + k
        while len(P) <= t: b(r.idle[len(P) % 8])
        P[t]["bola"] = k
    n = len(P)
    for t in range(t_disp + 4, n): P[t]["bers"] = r.idle[(t - t_disp - 4) % 8]
    return P


def render3(r, fondo=True):
    """La bola de fuego sale del cañón como un chorro: se ve sólo la parte de la llama que ya ha salido, y cuando la cabeza se aleja pasa entera."""
    fr = []
    comet = r.bola[0]
    for p in guion3(r):
        lz = nueva(fondo)
        if p.get("bola") is not None:
            k = p["bola"]
            x0, y0 = BX + 40, SUELO - 24
            if k < 8:
                cabeza = x0 + 36 * (k + 1)
                izq = cabeza - comet.width
                recorte = max(0, x0 - izq)
                parte = comet.crop((recorte, 0, comet.width, comet.height))
                lz.alpha_composite(parte, (int(izq + recorte), int(y0 - comet.height / 2)))
            else:
                g = r.bola[1] if k < 10 else r.bola[2]
                xe = x0 + 36 * 8 - 30
                lz.alpha_composite(g, (int(xe - g.width / 2), int(y0 - g.height / 2)))
        if p.get("arco") is not None:
            a = r.arcos[p["arco"]]
            lz.alpha_composite(a, (BX + 20, SUELO - a.height))
        pegar_pies(lz, p["bers"], BX)
        fr.append(lz)
    return fr


def gif_local(frames, ruta, dur):
    k = lambda a: a[..., 0].astype(np.uint32) << 16 | a[..., 1].astype(np.uint32) << 8 | a[..., 2]
    ps, agrupados = [], 0
    for fr in frames:
        a = np.asarray(fr.convert("RGB")); keys = np.unique(k(a))
        if len(keys) <= 256:
            pal = np.zeros(768, np.uint8)
            pal[0:len(keys) * 3:3], pal[1:len(keys) * 3:3], pal[2:len(keys) * 3:3] = keys >> 16, keys >> 8 & 255, keys & 255
            p = Image.fromarray(np.searchsorted(keys, k(a)).astype(np.uint8), "P"); p.putpalette(pal.tolist())
        else:
            p = fr.convert("RGB").quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE); agrupados += 1
        ps.append(p)
    ps[0].save(ruta, save_all=True, append_images=ps[1:], duration=dur, loop=0, disposal=1, optimize=False)
    return agrupados


def hoja_contacto(frames, idx, ruta, z=2, cols=4):
    filas = (len(idx) + cols - 1) // cols
    s = Image.new("RGB", (cols * (W * z + 6), filas * (H * z + 6)), (10, 10, 10))
    for j, i in enumerate(idx):
        s.paste(frames[i].convert("RGB").resize((W * z, H * z), Image.NEAREST), ((j % cols) * (W * z + 6), (j // cols) * (H * z + 6)))
    s.save(ruta)


def maqueta(capas, idx, ruta, cx=55, suelo=98):
    """Escena sin fondo dentro del marco de siempre (ventana 80x80 en la rejilla de 126): todo se dibuja por delante del marco."""
    fr, _ = marco.build()
    marco_im = fr.crop((1, 1, 127, 127))
    ims = []
    for i in idx:
        base = Image.new("RGBA", (126, 126), (0, 0, 0, 255)); base.paste(Image.new("RGBA", (80, 80), FONDO), (23, 23)); base.alpha_composite(marco_im)
        sup = Image.new("RGBA", (126, 126), (0, 0, 0, 0))
        dx, dy = cx - BX, suelo - SUELO
        c = capas[i]
        sup.alpha_composite(c.crop((max(0, -dx), max(0, -dy), min(c.width, 126 - dx), min(c.height, 126 - dy))), (max(0, dx), max(0, dy)))
        base.alpha_composite(sup)
        ims.append(base.convert("RGB").resize((504, 504), Image.NEAREST))
    s = Image.new("RGB", (504 * 3 + 20, 504 * ((len(ims) + 2) // 3) + 10 * ((len(ims) + 2) // 3 - 1)), (30, 30, 30))
    for j, im in enumerate(ims): s.paste(im, ((j % 3) * 514, (j // 3) * 514))
    s.save(ruta)


def main():
    r = cargar(); OUT.mkdir(exist_ok=True)
    for nombre, fr in (("2_contraataque_pilar", render2(r)), ("3_especial_bola_fuego", render3(r))):
        ag = gif_local([f.resize((W * 2, H * 2), Image.NEAREST) for f in fr], OUT / f"{nombre}_x2.gif", TICK)
        gif_local(fr, OUT / f"{nombre}_1x.gif", TICK)
        print(nombre, len(fr), "pasos de", TICK, "ms =", round(len(fr) * TICK / 1000, 2), "s; agrupados:", ag)
        n = len(fr); idx = sorted(set(int(round(i * (n - 1) / 11)) for i in range(12)))
        hoja_contacto(fr, idx, OUT / f"momentos_{nombre}.png", z=1, cols=3)
    c2 = render2(r, fondo=False, pilar_dx=48); c3 = render3(r, fondo=False)
    maqueta(c2, [4, 14, 22, 24, 28, 34], OUT / "maqueta_marco_2.png")
    maqueta(c3, [10, 14, 17, 19, 21, 24], OUT / "maqueta_marco_3.png")


if __name__ == "__main__":
    main()
