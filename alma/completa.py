"""Animación completa de Alma con un efecto de reinicio nuevo: C (zarpazos de tigre) o D (disolución en chispas).

El efecto de 10 pasos se reparte entre el final y el principio del ciclo (como el humo de Matilda):
  pasos 0-3  -> últimos 4 pasos del ciclo (la forma humana de rodillas)
  pasos 4-9  -> primeros 6 pasos del ciclo (la criatura acurrucada reaparece)
Para que se vea limpia la pose antes y después, el último fotograma humano dura 10 pasos (6 sin efecto) y el
primero de la criatura 4 (2 de ellos ya sin efecto).
Salida: alma_reinicio_C.gif y alma_reinicio_D.gif (+ _x2). Transparentes y en bucle.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import hojas                    # noqa: E402
import make_alma as ma          # noqa: E402
import reinicio as rn           # noqa: E402

TICK = 70
HOLD_HUMANA = 10                # pasos del último fotograma (forma humana)
HOLD_CRIATURA = 4               # pasos del primer fotograma (criatura)


def guion(F):
    dur = []
    for f in F:
        dur.append(ma.PASOS[f["hoja"]][f["n"]])
    dur[0] = HOLD_CRIATURA
    dur[-1] = HOLD_HUMANA
    sched = []
    for k, d in enumerate(dur):
        sched += [k] * d
    return sched


def en_lienzo(img):
    c = Image.new("RGBA", (rn.CWE, rn.CHE), (0, 0, 0, 0))
    c.alpha_composite(img, rn.OFF)
    return np.asarray(c).copy()


def paso_de_efecto(c, L):
    if c >= L - 4:
        return c - (L - 4)
    if c < 6:
        return c + 4
    return None


def componer(opcion):
    F = hojas.fotogramas()
    lien, _ = ma.alinear(F)
    fig = [en_lienzo(x) for x in lien]
    sched = guion(F)
    L = len(sched)
    humana = fig[28]
    frames, visibles = [], {}
    for c in range(L):
        k = sched[c]
        s = paso_de_efecto(c, L)
        base = fig[k]
        if s is None:
            img = Image.fromarray(base, "RGBA")
        elif opcion == "C":
            fx = rn.zarpazos(s)
            img = Image.fromarray(base, "RGBA"); img.alpha_composite(Image.fromarray(fx, "RGBA"))
            if s == 3:
                visibles[c] = int(((base[..., 3] > 0) & ~(fx[..., 3] > 0)).sum())
        else:
            nuevo = fig[k] if s >= 4 else fig[0]
            perso, chispas = rn.disolucion(s, humana, nuevo)
            img = Image.fromarray(perso, "RGBA"); img.alpha_composite(Image.fromarray(chispas, "RGBA"))
        frames.append(img)
    return frames, sched, L, visibles


def guardar(frames, path, escala):
    imgs = [f.resize((f.width * escala, f.height * escala), Image.NEAREST) if escala > 1 else f for f in frames]
    colores = sorted({p[:3] for im in imgs for p in im.getdata() if p[3]})
    assert len(colores) <= 255, len(colores)
    index = {c: i + 1 for i, c in enumerate(colores)}
    flat = [255, 0, 255] + [v for c in colores for v in c]
    pal = []
    for im in imgs:
        p = Image.new("P", im.size, 0); p.putpalette(flat + [0] * (768 - len(flat)))
        p.putdata([index[q[:3]] if q[3] else 0 for q in im.getdata()]); pal.append(p)
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=TICK, loop=0,
                transparency=0, disposal=2, optimize=False)
    return len(colores)


def main():
    todas = {}
    for op in "CD":
        frames, sched, L, vis = componer(op)
        boxes = [b for b in (f.getchannel("A").getbbox() for f in frames) if b]
        box = (max(min(b[0] for b in boxes) - 2, 0), max(min(b[1] for b in boxes) - 2, 0),
               min(max(b[2] for b in boxes) + 2, rn.CWE), min(max(b[3] for b in boxes) + 2, rn.CHE))
        cro = [f.crop(box) for f in frames]
        todas[op] = (cro, L)
        for esc, suf in ((1, ""), (2, "_x2")):
            p = HERE / f"alma_reinicio_{op}{suf}.gif"
            n = guardar(cro, p, esc)
            print(f"{p.name}: {len(cro)} pasos = {len(cro) * TICK} ms, lienzo {cro[0].size}, {n} colores, {p.stat().st_size / 1024:.0f} KB")
        if vis:
            print(f"  C: figura a la vista justo antes del cambio: {vis}")
    # hoja con el final y el principio del ciclo de cada opción
    cro, L = todas["C"]
    w, h = cro[0].size
    S = 2
    ticks = [L - 8, L - 5, L - 4, L - 3, L - 2, L - 1, 0, 1, 2, 4, 6]
    sheet = Image.new("RGB", (w * S * len(ticks) // 2 + 10, (h * S + 16) * 2 * 1), (20, 10, 14))
    sheet = Image.new("RGB", (w * S * 6, (h * S + 16) * 4), (20, 10, 14))
    d = ImageDraw.Draw(sheet)
    for r, op in enumerate("CD"):
        fr, L = todas[op]
        for half in range(2):
            sel = ticks[:6] if half == 0 else ticks[5:]
            y0 = (r * 2 + half) * (h * S + 16)
            d.text((4, y0 + 2), f"{op}: pasos {'finales' if half == 0 else 'iniciales'} del ciclo (ticks {sel})", fill=(255, 255, 255))
            for i, t in enumerate(sel):
                bg = Image.new("RGBA", fr[t].size, (40, 22, 36, 255)); bg.alpha_composite(fr[t])
                sheet.paste(bg.convert("RGB").resize((w * S, h * S), Image.NEAREST), (i * w * S, y0 + 16))
    out = HERE / "previews"; out.mkdir(exist_ok=True)
    sheet.save(out / "alma_reinicio_CD.png"); print("hoja:", sheet.size)


if __name__ == "__main__":
    main()
