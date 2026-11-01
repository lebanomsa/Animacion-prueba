"""Animación final de Utena con el traje: los 30 fotogramas del GIF original más el regreso al revés para cerrar el bucle.

Correspondencia con el original (numeración desde 0):
  0        brazos abiertos (300 ms)
  1-5      el globo se llena de puntos (300 ms cada uno)
  6        sobresalto (en el original 50 ms; aquí 100 ms para que se vea)
  7        se tapa: mano en el pecho y mano delante de la entrepierna (100 ms)
  8-29     balanceo: pares = 8, impares = 9 (cuerpo 1 px a la derecha, pies quietos), 100 ms cada uno
  regreso  7 (100 ms) y 6 (100 ms), y vuelve al 0
Salida: utena_traje.gif (x1), utena_traje_x5.gif (480x640) y utena_traje_x5_fondo.gif (fondo oscuro, para revisar),
transparentes salvo la de fondo, en bucle.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import hojas
import poses as p1
import poses3 as p3

HERE = Path(__file__).parent
PREV = HERE / "previews"


def secuencia():
    res, fr, _ = p3.todas()
    _, dur0 = hojas.fotogramas()
    globos = {k: p1.con_globo(res[0], fr, k) for k in range(1, 6)}
    cuadros, durs, origen = [], [], []
    for k in range(30):
        if k == 0:
            im = res[0]
        elif k <= 5:
            im = globos[k]
        elif k == 6:
            im = res[6]
        elif k == 7:
            im = res[7]
        else:
            im = res[8] if k % 2 == 0 else res[9]
        d = 100 if k == 6 else dur0[k]
        cuadros.append(im); durs.append(d); origen.append(str(k))
    for k in (7, 6):                                           # regreso al revés
        cuadros.append(res[k]); durs.append(100); origen.append(f"{k} (regreso)")
    return cuadros, durs, origen


def guardar(cuadros, durs, ruta, escala=1, fondo=None):
    imgs = [c.resize((c.width * escala, c.height * escala), Image.NEAREST) if escala > 1 else c for c in cuadros]
    if fondo:
        planos = []
        for im in imgs:
            b = Image.new("RGBA", im.size, fondo + (255,)); b.alpha_composite(im); planos.append(b.convert("RGB"))
        arrs = [np.asarray(p) for p in planos]
        key = lambda a: a[..., 0].astype(np.uint32) << 16 | a[..., 1].astype(np.uint32) << 8 | a[..., 2]
        keys = np.unique(np.concatenate([key(a).ravel() for a in arrs]))
        assert len(keys) <= 256
        pal = np.zeros(768, np.uint8)
        pal[0:len(keys) * 3:3], pal[1:len(keys) * 3:3], pal[2:len(keys) * 3:3] = keys >> 16, keys >> 8 & 255, keys & 255
        out = []
        for a in arrs:
            p = Image.fromarray(np.searchsorted(keys, key(a)).astype(np.uint8), "P"); p.putpalette(pal.tolist()); out.append(p)
        out[0].save(ruta, save_all=True, append_images=out[1:], duration=durs, loop=0, disposal=1, optimize=False)
        return len(keys)
    colores = sorted({p[:3] for im in imgs for p in im.getdata() if p[3]})
    assert len(colores) <= 255, len(colores)
    index = {c: i + 1 for i, c in enumerate(colores)}
    flat = [255, 0, 255] + [v for c in colores for v in c]
    pal = []
    for im in imgs:
        p = Image.new("P", im.size, 0); p.putpalette(flat + [0] * (768 - len(flat)))
        p.putdata([index[q[:3]] if q[3] else 0 for q in im.getdata()]); pal.append(p)
    pal[0].save(ruta, save_all=True, append_images=pal[1:], duration=durs, loop=0, transparency=0, disposal=2, optimize=False)
    return len(colores)


def main():
    cuadros, durs, origen = secuencia()
    print(f"{len(cuadros)} fotogramas, {sum(durs)} ms")
    for esc, suf in ((1, ""), (5, "_x5")):
        ruta = HERE / f"utena_traje{suf}.gif"
        n = guardar(cuadros, durs, ruta, esc)
        print(f"{ruta.name}: {cuadros[0].width * esc}x{cuadros[0].height * esc}, {n} colores, {ruta.stat().st_size / 1024:.0f} KB")
    ruta = HERE / "utena_traje_x5_fondo.gif"
    n = guardar(cuadros, durs, ruta, 5, fondo=(46, 46, 56))
    print(f"{ruta.name}: {n} colores, {ruta.stat().st_size / 1024:.0f} KB")
    # hoja con cada cambio de la secuencia
    sel = [0, 3, 5, 6, 7, 8, 9, 30, 31]
    S = 3
    w, h = 96 * S, 128 * S
    hoja = Image.new("RGB", (len(sel) * (w + 6), h + 20), (30, 30, 40))
    d = ImageDraw.Draw(hoja)
    for i, t in enumerate(sel):
        b = Image.new("RGBA", cuadros[t].size, (46, 46, 56, 255)); b.alpha_composite(cuadros[t])
        hoja.paste(b.convert("RGB").resize((w, h), Image.NEAREST), (i * (w + 6), 20))
        d.text((i * (w + 6) + 4, 4), f"paso {t + 1}: {durs[t]} ms", fill=(255, 230, 120))
    PREV.mkdir(exist_ok=True)
    hoja.save(PREV / "utena_traje_pasos.png")


if __name__ == "__main__":
    main()
