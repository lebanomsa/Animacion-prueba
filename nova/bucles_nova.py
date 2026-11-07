"""Nova + cápsula de Vita: tres bucles de prueba sobre fondo neutro (sin marco ni escenario todavía), tamaño nativo 1x.

  1. victoria_capsula : la cápsula se monta, Nova hace el gesto de victoria y el saludo, Vita flota, la cápsula se desmonta (marcha atrás) y Nova vuelve a la espera.
  2. guardia_capsula  : Nova en espera junto a la cápsula ya montada (bucle perfecto de 16 pasos).
  3. timor_capsula    : Nova dispara el láser Timor hacia la derecha; la cápsula burbujea a su lado (bucle de 32 pasos).
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).parent
import hoja_nova as h

OUT = HERE / "salida"
TICK = 80
W, H = 176, 112
SUELO = 105
CAPS_X, NOVA_X = 44, 110
FONDO, SUELO_COL = (32, 34, 44, 255), (24, 26, 34, 255)


class R:
    pass


def gif_local(frames, ruta, dur):
    """GIF con una paleta propia por fotograma (los colores no se agrupan si el fotograma cabe en 256)."""
    k = lambda a: a[..., 0].astype(np.uint32) << 16 | a[..., 1].astype(np.uint32) << 8 | a[..., 2]
    ps, agrupados = [], 0
    for fr in frames:
        a = np.asarray(fr.convert("RGB"))
        keys = np.unique(k(a))
        if len(keys) <= 256:
            pal = np.zeros(768, np.uint8)
            pal[0:len(keys) * 3:3], pal[1:len(keys) * 3:3], pal[2:len(keys) * 3:3] = keys >> 16, keys >> 8 & 255, keys & 255
            p = Image.fromarray(np.searchsorted(keys, k(a)).astype(np.uint8), "P"); p.putpalette(pal.tolist())
        else:
            p = fr.convert("RGB").quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE); agrupados += 1
        ps.append(p)
    ps[0].save(ruta, save_all=True, append_images=ps[1:], duration=dur, loop=0, disposal=1, optimize=False)
    return agrupados


def cargar():
    r = R()
    r.idle, r.vic = h.fotogramas("idle"), h.fotogramas("victoria")
    r.cap = h.fotogramas("capsula")
    r.timor = h.crudos("timor")
    return r


def pegar_pies(lz, img, x, y=SUELO):
    cx, by = h.pies(img)
    lz.alpha_composite(img, (int(round(x - cx)), int(round(y - by))))


def bota_derecha(celda):
    """Centro x de la bota derecha de Nova en una celda sin recortar de Timor: último tramo de la fila justo sobre la base (los chispazos quedan a su izquierda)."""
    a = np.asarray(celda)[..., 3] > 0
    yb = np.where(a.any(1))[0].max()
    d = np.diff(np.concatenate([[0], a[yb - 1].astype(np.int8), [0]]))
    tr = list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))
    p, q = [t for t in tr if t[1] - t[0] >= 6][-1]
    return (p + q) / 2, yb + 1


def escena(nova, cap, timor=False, r=None):
    lz = Image.new("RGBA", (W, H), FONDO)
    lz.paste(Image.new("RGBA", (W, H - SUELO), SUELO_COL), (0, SUELO))
    if cap is not None:
        pegar_pies(lz, cap, CAPS_X, SUELO + 1)
    if timor:      # celda sin recortar: se alinea por la bota derecha (en el primer paso está 10 px a la derecha del centro de los pies)
        bx, by = bota_derecha(nova)
        lz.alpha_composite(nova, (int(round(NOVA_X + 10 - bx)), SUELO - by))
    elif nova is not None:
        pegar_pies(lz, nova, NOVA_X)
    return lz




def guion1(r):
    """(índice idle | None, índice victoria | None, índice cápsula) por paso: 60 pasos."""
    P = []
    # A: montaje (0-13). Nova en espera (poses 4..7 de idle, 2 pasos cada una) y gesto de victoria cuando cae el sombrero (paso 8)
    espera = [4, 4, 5, 5, 6, 6, 7, 7]
    for t in range(14):
        cap = t
        if t < 8: n = ("idle", espera[t])
        else: n = ("vic", {8: 0, 9: 0, 10: 1, 11: 2, 12: 3, 13: 4}[t])
        P.append((n, cap))
    # B: cápsula completa, 2 vueltas del bucle de 16; saludo con la oreja (ida y vuelta 5..9)
    sway = [4, 5, 6, 7, 8, 7, 6, 5]
    for t in range(32):
        P.append((("vic", sway[t % 8]), 14 + t % 16))
    # C: desmontaje al revés; Nova deshace el gesto y vuelve a la espera
    out = [("vic", 4), ("vic", 3), ("vic", 2), ("vic", 1), ("vic", 0), ("vic", 0), ("idle", 4), ("idle", 4), ("idle", 5), ("idle", 5), ("idle", 6), ("idle", 6), ("idle", 7), ("idle", 7)]
    for t in range(14):
        P.append((out[t], 13 - t))
    return P


def render1(r):
    fr = []
    for (tipo, i), c in guion1(r):
        nova = r.idle[i] if tipo == "idle" else r.vic[i]
        fr.append(escena(nova, r.cap[c]))
    return fr


def render2(r):
    fr = []
    for t in range(16):
        fr.append(escena(r.idle[t // 2], r.cap[14 + t]))
    return fr


def guion3(r, rapido=True):
    """(imagen de Nova, es celda de Timor, índice de cápsula) por paso.
    rapido=True: 32 pasos; Nova cambia de fotograma a cada paso (como Vita), con pausas solo en la preparación y en el rayo.
      0-3 idle (poses 4..7) | 4-12 preparación | 13-23 rayo | 24-27 recuperación | 28-31 idle (poses 0..3) -> el idle enlaza con el inicio.
    rapido=False: la versión lenta anterior (48 pasos)."""
    P = []
    if not rapido:
        dur = [6, 3, 3, 2, 3, 2, 3, 6, 3, 3, 2, 2, 2, 2, 3]
        for k, d in enumerate(dur):
            for _ in range(d): P.append((r.timor[k], True, 14 + len(P) % 16))
        for _ in range(3): P.append((r.idle[0], False, 14 + len(P) % 16))
        return P
    for i in (4, 5, 6, 7): P.append((r.idle[i], False, 14 + len(P) % 16))
    dur = [2, 1, 1, 1, 1, 1, 2, 5, 3, 2, 1, 1, 1, 1, 1]
    assert sum(dur) == 24
    for k, d in enumerate(dur):
        for _ in range(d): P.append((r.timor[k], True, 14 + len(P) % 16))
    for i in (0, 1, 2, 3): P.append((r.idle[i], False, 14 + len(P) % 16))
    assert len(P) == 32, len(P)
    return P


def render3(r):
    return [escena(n, r.cap[c], timor=tm) for n, tm, c in guion3(r)]


def guardar(frames, nombre):
    OUT.mkdir(exist_ok=True)
    gif_local(frames, OUT / f"{nombre}_1x.gif", TICK)
    gif_local([f.resize((f.width * 4, f.height * 4), Image.NEAREST) for f in frames], OUT / f"{nombre}_x4.gif", TICK)
    d0 = int((np.abs(np.asarray(frames[-1].convert("RGB")).astype(int) - np.asarray(frames[0].convert("RGB")).astype(int)).sum(-1) > 0).sum())
    print(f"{nombre}: {len(frames)} pasos de {TICK} ms = {len(frames) * TICK / 1000:.2f} s; píxeles distintos entre el último y el primer paso: {d0}")


def hoja_contacto(frames, idx, ruta, z=3, cols=4):
    filas = (len(idx) + cols - 1) // cols
    s = Image.new("RGB", (cols * (W * z + 6), filas * (H * z + 6)), (10, 10, 10))
    for j, i in enumerate(idx):
        s.paste(frames[i].convert("RGB").resize((W * z, H * z), Image.NEAREST), ((j % cols) * (W * z + 6), (j // cols) * (H * z + 6)))
    s.save(ruta)


def main():
    r = cargar()
    OUT.mkdir(exist_ok=True)
    f1, f2, f3 = render1(r), render2(r), render3(r)
    guardar(f1, "1_victoria_capsula"); guardar(f2, "2_guardia_capsula"); guardar(f3, "3_timor_capsula")
    hoja_contacto(f1, [0, 7, 8, 10, 12, 14, 24, 40, 46, 50, 54, 59], OUT / "momentos_1.png")
    hoja_contacto(f2, [0, 4, 8, 12], OUT / "momentos_2.png", cols=4)
    hoja_contacto(f3, [0, 7, 9, 11, 13, 15, 18, 22, 24, 26, 28, 31], OUT / "momentos_3.png")


if __name__ == "__main__":
    main()
