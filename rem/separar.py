"""Separa la composición final de Rem (rem_marco_aurora.gif) en marco + fondo y animación.

Todo dura 24 pasos de 80 ms (1920 ms): Rem, el círculo mágico, la nieve, la aurora y los detalles del marco.

  marco_y_fondo_rem.gif       1024x1024, 24 fotogramas: marco 'aurora de medianoche' + bosque nevado (sin Rem ni efectos)
  marco_y_fondo_rem.png       1024x1024, el primer fotograma, fijo
  rem_animacion_sola.gif      1024x1024 transparente: Rem, el círculo mágico, las ondas y las chispas, en su sitio
  rem_animacion_recortada.gif la misma animación recortada a su tamaño
El círculo, las ondas y las chispas son brillos que se suman al fondo (no tienen un color propio), y un GIF solo admite
transparencia total o nada: por eso la capa de la animación lleva los colores ya mezclados con el bosque en los bordes del
brillo. Encima de este marco y fondo queda idéntica al GIF final; sobre otro fondo esos bordes se verían con tonos del bosque.
Salida: salida_separada/
"""
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import final as fi                 # noqa: E402  (aplica los 8 pasos de color de la aurora del marco)

import numpy as np                 # noqa: E402
from PIL import Image              # noqa: E402

import fondos                      # noqa: E402
import marco                       # noqa: E402
import marcos as mk                # noqa: E402
import previas                     # noqa: E402

OUT = HERE / "salida_separada"
N, TICK = 24, 80
UMBRAL = 24                # diferencia mínima (por canal) para considerar un píxel parte de la animación
key = lambda a: a[..., 0].astype(np.uint32) << 16 | a[..., 1].astype(np.uint32) << 8 | a[..., 2]


def paleta_ventanas(frames, k):
    mos = Image.fromarray(np.concatenate([np.asarray(f)[::2, ::2] for f in frames], axis=0))
    return mos.quantize(colors=k, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)


def gif_paleta(frames, ruta):
    arrs = [np.asarray(f) for f in frames]
    keys = np.unique(np.concatenate([key(a).ravel() for a in arrs]))
    assert len(keys) <= 256, len(keys)
    pal = np.zeros(768, np.uint8)
    pal[0:len(keys) * 3:3], pal[1:len(keys) * 3:3], pal[2:len(keys) * 3:3] = keys >> 16, keys >> 8 & 255, keys & 255
    out = []
    for a in arrs:
        p = Image.fromarray(np.searchsorted(keys, key(a)).astype(np.uint8), "P"); p.putpalette(pal.tolist()); out.append(p)
    out[0].save(ruta, save_all=True, append_images=out[1:], duration=TICK, loop=0, disposal=1, optimize=False)
    return len(keys)


def gif_transparente(frames, ruta):
    arrs = [np.asarray(f) for f in frames]
    cols = np.unique(np.concatenate([key(a)[a[..., 3] > 0] for a in arrs]))
    assert len(cols) <= 255, len(cols)
    flat = np.zeros(768, np.uint8); flat[0:3] = (255, 0, 255)
    flat[3:3 + len(cols) * 3:3], flat[4:4 + len(cols) * 3:3], flat[5:5 + len(cols) * 3:3] = cols >> 16, cols >> 8 & 255, cols & 255
    out = []
    for a in arrs:
        idx = (np.searchsorted(cols, key(a)) + 1).astype(np.uint8)
        idx[a[..., 3] == 0] = 0
        p = Image.fromarray(idx, "P"); p.putpalette(flat.tolist()); out.append(p)
    out[0].save(ruta, save_all=True, append_images=out[1:], duration=TICK, loop=0, transparency=0, disposal=2,
                optimize=False)
    return len(cols)


def por_paso(ruta, total):
    g = Image.open(ruta); out = []
    for i in range(g.n_frames):
        g.seek(i); f = g.convert("RGBA")
        out += [f] * round(g.info.get("duration", TICK) / TICK)
    assert len(out) == total, (ruta.name, len(out))
    return out


def main():
    OUT.mkdir(exist_ok=True)
    bosque = [fondos.a_float(fondos.bosque(t % 24)) for t in range(N)]
    ventanas = previas.op1(lambda t: bosque[t].copy())       # op1 pinta encima del array: se le pasa una copia
    solo_fondo = [previas.salir(b) for b in bosque]
    f0, _ = marco.build(*mk.P3)
    f0 = f0.copy()
    kw, km = 160, 90
    while True:                                            # mismo reparto de colores que final.py
        q = paleta_ventanas(ventanas, kw)
        vq = [v.quantize(palette=q, dither=Image.Dither.NONE).convert("RGB") for v in ventanas]
        a = np.array(f0); op = a[..., 3] > 0
        a[..., :3][op] = mk.quantize_rgb(a[..., :3][op], km)
        base = Image.fromarray(a, "RGBA")
        marcos = []
        for t in range(N):
            m = base.copy(); mk.det3(m, t); marcos.append(m.resize((1024, 1024), Image.NEAREST))

        def componer(win, t):
            img = Image.new("RGBA", (1024, 1024), (0, 0, 0, 255))
            img.alpha_composite(win.convert("RGBA"), (192, 192)); img.alpha_composite(marcos[t])
            return img.convert("RGB")
        out = [componer(vq[t], t) for t in range(N)]
        n = len(np.unique(np.concatenate([key(np.asarray(f)).ravel() for f in out])))
        if n <= 256:
            break
        ex = n - 256
        kw -= max(2, int(ex * 0.6)); km -= max(2, ex - int(ex * 0.6))
    print(f"ventana {kw} y marco {km} tonos (igual que el final)")

    # 1. marco + fondo, con la misma paleta de la ventana
    fq = [s.quantize(palette=q, dither=Image.Dither.NONE).convert("RGB") for s in solo_fondo]
    mf = [componer(fq[t], t) for t in range(N)]
    r = gif_paleta(mf, OUT / "marco_y_fondo_rem.gif")
    mf[0].save(OUT / "marco_y_fondo_rem.png")
    print(f"marco_y_fondo_rem.gif: {N} fotogramas, {r} colores, {(OUT / 'marco_y_fondo_rem.gif').stat().st_size / 1024:.0f} KB")

    # 2. animación: todo lo que Rem y sus efectos cambian respecto del fondo, con el color del GIF final
    capas = []
    for t in range(N):
        fin = np.asarray(out[t]); mfa = np.asarray(mf[t])
        dif_v = np.zeros((1024, 1024), bool)
        # cambios claros (Rem, el centro del círculo, chispas); los brillos muy tenues solo entran si cambian el color final
        dif_v[192:832, 192:832] = np.abs(np.asarray(ventanas[t]).astype(int) - np.asarray(solo_fondo[t]).astype(int)).max(-1) > UMBRAL
        mask = (dif_v | (np.abs(fin.astype(int) - mfa.astype(int)).sum(-1) > 0)) & (np.asarray(marcos[t])[..., 3] == 0)
        c = np.zeros((1024, 1024, 4), np.uint8)
        c[mask, :3] = fin[mask]; c[mask, 3] = 255
        capas.append(Image.fromarray(c, "RGBA"))
    nc = gif_transparente(capas, OUT / "rem_animacion_sola.gif")
    boxes = [c.getchannel("A").getbbox() for c in capas]
    box = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
    gif_transparente([c.crop(box) for c in capas], OUT / "rem_animacion_recortada.gif")
    print(f"rem_animacion_sola.gif: {N} fotogramas, {nc} colores, {(OUT / 'rem_animacion_sola.gif').stat().st_size / 1024:.0f} KB;"
          f" recorte {box} -> {box[2] - box[0]}x{box[3] - box[1]}")

    # comprobación contra el GIF final
    final = por_paso(HERE / "rem_marco_aurora.gif", N)
    fondo_g = por_paso(OUT / "marco_y_fondo_rem.gif", N)
    sola = por_paso(OUT / "rem_animacion_sola.gif", N)
    dif = 0
    for t in range(N):
        comp = fondo_g[t].copy(); comp.alpha_composite(sola[t])
        dif += int((np.abs(np.asarray(comp.convert("RGB")).astype(int) - np.asarray(final[t].convert("RGB")).astype(int)).sum(-1) > 0).sum())
    print("píxeles distintos entre (marco y fondo + animación) y el GIF final, en los 24 pasos:", dif)


if __name__ == "__main__":
    main()
