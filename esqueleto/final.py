"""Esqueleto completo: marco oro -> plata (corona, estrellas, destellos), fondo de rayos dorados y el personaje a x6.

36 pasos de 80 ms (2880 ms): el guion de 39 pasos con 3 esperas más cortas (3.0 inicial 4->3, 1.2 3->2, 2.0 3->2), para que
los ciclos de 12 pasos del marco y de los rayos encajen 3 veces.
Escenario y personaje a x6: el fondo se dibuja en 107x107 píxeles nativos y se amplía a x6 (642 px, recortado a 640).
Salida: esqueleto_marco_oro_plata.gif y una hoja de pasos.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import giros                    # noqa: E402
import marcos as mk             # noqa: E402
import marco                    # noqa: E402

PREV = HERE / "previews"
S = 6
N_BG = 107
TICK = 80
GUION = [("3.0", 3), ("T", 1), ("1.0", 3), ("1.1", 2), ("1.2", 2), ("2.0", 2), ("2.1", 4), ("T", 1), ("3.0", 2),
         ("3.1", 2), ("3.2", 2), ("3.3", 2), ("3.4", 4), ("3.3", 2), ("3.2", 2), ("3.1", 2)]


def pasos():
    T = giros.agachado()
    out = []
    for k, n in GUION:
        out += [T if k == "T" else giros.colocar(giros.F[k])] * n
    return out


def main():
    fr = pasos()
    n = len(fr)
    print(f"{n} pasos = {n * TICK} ms")
    assert n == 36
    boxes = [f.getchannel("A").getbbox() for f in fr]
    box = (min(b[0] for b in boxes) - 1, min(b[1] for b in boxes) - 1, max(b[2] for b in boxes) + 1, max(b[3] for b in boxes) + 1)
    box = (max(box[0], 0), max(box[1], 0), min(box[2], giros.CW), min(box[3], giros.CH))
    sk = [f.crop(box) for f in fr]
    w, h = sk[0].size
    print("personaje:", w, "x", h, "->", w * S, "x", h * S)
    ox, oy = (640 - w * S) // 2, 640 - h * S - 10
    assert ox >= 0 and oy >= 0
    fondos = [mk.fondo_rayos(t, N_BG).convert("RGBA").resize((N_BG * S, N_BG * S), Image.NEAREST).crop((1, 1, 641, 641)) for t in range(12)]
    f0, _ = marco.build(mk.ORO, mk.PLATA)
    f0 = f0.copy()
    km = 150
    while True:
        a = np.array(f0); op = a[..., 3] > 0
        a[..., :3][op] = mk.quantize_rgb(a[..., :3][op], km)
        base = Image.fromarray(a, "RGBA")
        marcos = []
        for t in range(12):
            m = base.copy(); mk.det1(m, t); marcos.append(m.resize((1024, 1024), Image.NEAREST))
        out = []
        for t in range(n):
            win = fondos[t % 12].copy()
            win.alpha_composite(sk[t].resize((w * S, h * S), Image.NEAREST), (ox, oy))
            img = Image.new("RGBA", (1024, 1024), (0, 0, 0, 255))
            img.alpha_composite(win, (192, 192))
            img.alpha_composite(marcos[t % 12])
            out.append(img.convert("RGB"))
        arrs = [np.asarray(f) for f in out]
        key = lambda a_: a_[..., 0].astype(np.uint32) << 16 | a_[..., 1].astype(np.uint32) << 8 | a_[..., 2]
        keys = np.unique(np.concatenate([key(a_).ravel() for a_ in arrs]))
        print(f"marco {km} tonos -> paleta {len(keys)}")
        if len(keys) <= 256:
            break
        km -= max(6, len(keys) - 256)
    pal = np.zeros(768, np.uint8)
    pal[0:len(keys) * 3:3], pal[1:len(keys) * 3:3], pal[2:len(keys) * 3:3] = keys >> 16, keys >> 8 & 255, keys & 255
    pp = []
    for a_ in arrs:
        p = Image.fromarray(np.searchsorted(keys, key(a_)).astype(np.uint8), "P"); p.putpalette(pal.tolist()); pp.append(p)
    ruta = HERE / "esqueleto_marco_oro_plata.gif"
    pp[0].save(ruta, save_all=True, append_images=pp[1:], duration=TICK, loop=0, disposal=1, optimize=False)
    print(f"{ruta.name}: {n} pasos, {len(keys)} colores, marco {km} tonos, {ruta.stat().st_size / 1024 / 1024:.1f} MB")
    sel = [0, 3, 9, 13, 17, 20, 23, 27, 31, 34]
    sh = Image.new("RGB", (5 * 410, 2 * 410), (14, 10, 20))
    for i, t in enumerate(sel):
        sh.paste(out[t].resize((410, 410), Image.LANCZOS), ((i % 5) * 410, (i // 5) * 410))
    PREV.mkdir(exist_ok=True)
    sh.save(PREV / "esqueleto_marco_oro_plata_pasos.png")


if __name__ == "__main__":
    main()
