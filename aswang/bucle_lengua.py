"""Aswang con la lengua fuera (secuencia 2 del ataque especial, 8 fotogramas) y dos murciélagos pequeños (secuencia 1) que la rodean en órbita.
Dos versiones del orden de los fotogramas de la lengua:
  adelante   : 0..7 y vuelta al 0 (8 pasos); los murciélagos giran 180 grados por vuelta (son iguales, así que cierra)
  ida_vuelta : 0..7 y 7..0 (16 pasos, los extremos se mantienen un paso); los murciélagos giran 360 grados
Misma velocidad angular en las dos. 80 ms por paso, ventana de 80x80 del marco de siempre."""
import math
import numpy as np
from PIL import Image
import bucles_aswang as ba

OUT = ba.OUT
TICK = ba.TICK
CX, SUELO = 40, ba.SUELO
HEAD = (CX + 2, SUELO - 31)         # centro de la órbita (altura de la cabeza)
RX, RY = 22, 8
GRADOS = 22.5                        # por paso


def render(orden, r, marco_im):
    out = []
    for t, k in enumerate(orden):
        lz = ba.nueva()
        delante = []
        for b in (0, 1):
            ang = math.radians(GRADOS * t + 180 * b)
            x, y, prof = HEAD[0] + RX * math.cos(ang), HEAD[1] + RY * math.sin(ang), math.sin(ang)
            img = r.seq1[(t + 4 * b) % 8]
            (delante if prof > 0 else []).append((img, x, y))
            if prof <= 0: ba.pegar(lz, img, x - img.width / 2, y - img.height / 2)
        ba.pies(lz, r.seq2[k], CX)
        for img, x, y in delante: ba.pegar(lz, img, x - img.width / 2, y - img.height / 2)
        c = Image.new("RGBA", (126, 126), (0, 0, 0, 255)); c.paste(lz, (23, 23)); c.alpha_composite(marco_im)
        out.append(c.convert("RGB"))
    return out


def main():
    r = ba.cargar()
    fr, _ = ba.marco.build()
    img = np.array(fr); o = img[..., 3] > 0
    q = Image.fromarray(img[..., :3][o].reshape(-1, 1, 3), "RGB").quantize(colors=40, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    img[..., :3][o] = np.array(q.getpalette()[:120], np.uint8).reshape(-1, 3)[np.asarray(q).reshape(-1)]
    marco_im = Image.fromarray(img, "RGBA").crop((1, 1, 127, 127))
    versiones = {"adelante": list(range(8)), "ida_vuelta": list(range(8)) + list(range(7, -1, -1))}
    for nombre, orden in versiones.items():
        frames = render(orden, r, marco_im)
        ag = ba.gif_local([f.resize((504, 504), Image.NEAREST) for f in frames], OUT / f"lengua_{nombre}_x4.gif", TICK)
        a = [np.asarray(f).astype(int) for f in frames]
        d = lambda x, y: int((np.abs(x - y).sum(-1) > 0).sum())
        n = len(frames)
        print(nombre, n, "pasos =", round(n * TICK / 1000, 2), "s; agrupados:", ag, "; último->primero:", d(a[-1], a[0]), "px; mediana entre consecutivos:", int(np.median([d(a[i], a[(i + 1) % n]) for i in range(n)])))
        cols = 4; idx = list(range(n))[:: max(1, n // 8)][:8]
        s = Image.new("RGB", (cols * 254, ((len(idx) + cols - 1) // cols) * 254), (10, 10, 10))
        for j, i in enumerate(idx): s.paste(frames[i].resize((252, 252), Image.NEAREST), ((j % cols) * 254, (j // cols) * 254))
        s.save(OUT / f"lengua_momentos_{nombre}.png")


if __name__ == "__main__":
    main()
