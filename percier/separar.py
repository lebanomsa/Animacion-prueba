"""Separa la composición final de Percier (percier_marco_halloween.gif) en marco + fondo y animación.

El marco (ojos de las calabazas, estrellas de la franja) y el fondo (niebla, calabaza y velas) están animados en un ciclo
de 12 pasos de 80 ms, así que el marco con fondo es un GIF de 12 fotogramas (y un PNG de un fotograma, por si se quiere fijo).
La animación de Percier son 72 pasos de 80 ms (= 6 vueltas del ciclo del fondo).

  marco_y_fondo_percier.gif       1024x1024, 12 fotogramas de 80 ms en bucle (960 ms)
  marco_y_fondo_percier.png       1024x1024, el primer fotograma, fijo
  percier_animacion_sola.gif      1024x1024 transparente, 72 fotogramas de 80 ms (5760 ms), en la misma posición que en la
                                  composición; los píxeles que el marco tapa (telaraña, araña, borde) se dejan transparentes
  percier_animacion_recortada.gif la misma animación recortada a su tamaño
Comprueba que, poniendo la animación encima del marco con fondo (los dos empezando a la vez), sale el GIF final exacto.
Salida: salida_separada/
"""
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import final as fi                             # noqa: E402  (configura layout antes de importar completa)

import numpy as np                             # noqa: E402
from PIL import Image                          # noqa: E402

import fondo                                   # noqa: E402
import marcos2 as m2                           # noqa: E402

OUT = HERE / "salida_separada"
TICK = 80


def gif_transparente(frames, ruta):
    colores = sorted({p[:3] for im in frames for p in im.getdata() if p[3]})
    assert len(colores) <= 255, len(colores)
    index = {c: i + 1 for i, c in enumerate(colores)}
    flat = [255, 0, 255] + [v for c in colores for v in c]
    out = []
    for im in frames:
        a = np.asarray(im)
        idx = np.zeros(a.shape[:2], np.uint8)
        op = a[..., 3] > 0
        lut = {c: i for c, i in index.items()}
        for y, x in zip(*np.where(op)):
            idx[y, x] = lut[tuple(a[y, x, :3])]
        p = Image.fromarray(idx, "P"); p.putpalette(flat + [0] * (768 - len(flat))); out.append(p)
    out[0].save(ruta, save_all=True, append_images=out[1:], duration=TICK, loop=0, transparency=0, disposal=2,
                optimize=False)
    return len(colores)


def main():
    OUT.mkdir(exist_ok=True)
    frames = fi.pasos()
    n = len(frames)
    lays = [f.crop((0, 0, 128, 128)) for f in frames]
    campo = fondo.campo_niebla()
    base_bg = fondo.ventana_base()
    escena = [fondo.escenario(t, True, campo, base_bg).convert("RGBA") for t in range(12)]
    ventanas = []
    for t in range(n):
        e = escena[t % 12].copy(); e.alpha_composite(lays[t]); ventanas.append(e.resize((640, 640), Image.NEAREST))
    # mismo número de tonos del marco que la composición final
    km = 140
    while True:
        base = m2.marco_base(km)
        marcos = [m2.marco_t(base, "luna", t) for t in range(12)]
        out = [m2.componer(marcos[t % 12], ventanas[t]) for t in range(n)]
        key = lambda a: a[..., 0].astype(np.uint32) << 16 | a[..., 1].astype(np.uint32) << 8 | a[..., 2]
        cols = len(np.unique(np.concatenate([key(np.asarray(f)).ravel() for f in out])))
        if cols <= 256:
            break
        km -= max(4, cols - 256)
    print("marco con", km, "tonos (igual que el final)")

    # 1. marco + fondo (12 fotogramas)
    mf = [m2.componer(marcos[t], escena[t].resize((640, 640), Image.NEAREST)) for t in range(12)]
    r = m2.guardar_gif(mf, OUT / "marco_y_fondo_percier.gif", TICK)
    mf[0].save(OUT / "marco_y_fondo_percier.png")
    print(f"marco_y_fondo_percier.gif: 12 fotogramas, {r} colores, {(OUT / 'marco_y_fondo_percier.gif').stat().st_size / 1024:.0f} KB")

    # 2. animación sola, en su sitio, sin lo que tapa el marco
    marcos_big = [np.asarray(m.resize((1024, 1024), Image.NEAREST)) for m in marcos]
    capas = []
    for t in range(n):
        c = np.zeros((1024, 1024, 4), np.uint8)
        c[192:832, 192:832] = np.asarray(lays[t].resize((640, 640), Image.NEAREST))
        c[marcos_big[t % 12][..., 3] > 0] = 0
        capas.append(Image.fromarray(c, "RGBA"))
    nc = gif_transparente(capas, OUT / "percier_animacion_sola.gif")
    boxes = [c.getchannel("A").getbbox() for c in capas]
    box = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
    gif_transparente([c.crop(box) for c in capas], OUT / "percier_animacion_recortada.gif")
    print(f"percier_animacion_sola.gif: {n} fotogramas, {nc} colores, "
          f"{(OUT / 'percier_animacion_sola.gif').stat().st_size / 1024:.0f} KB; recorte {box} -> "
          f"{box[2] - box[0]}x{box[3] - box[1]}")

    # comprobación contra el GIF final (Pillow junta fotogramas idénticos seguidos sumando su duración: se expanden por tiempo)
    def por_paso(ruta, total):
        g = Image.open(ruta); out = []
        for i in range(g.n_frames):
            g.seek(i); f = g.convert("RGBA")
            out += [f] * round(g.info.get("duration", TICK) / TICK)
        assert len(out) == total, (ruta.name, len(out))
        return out
    final = por_paso(HERE / "percier_marco_halloween.gif", n)
    fondo_g = por_paso(OUT / "marco_y_fondo_percier.gif", 12)
    sola = por_paso(OUT / "percier_animacion_sola.gif", n)
    dif = 0
    for t in range(n):
        comp = fondo_g[t % 12].copy(); comp.alpha_composite(sola[t])
        dif += int((np.abs(np.asarray(comp.convert("RGB")).astype(int)
                           - np.asarray(final[t].convert("RGB")).astype(int)).sum(-1) > 0).sum())
    g = Image.open(OUT / "percier_animacion_sola.gif")
    tot = 0
    for i in range(g.n_frames):
        g.seek(i); tot += g.info.get("duration", 0)
    print(f"percier_animacion_sola.gif guardado: {g.n_frames} fotogramas distintos, {tot} ms en total")
    print("píxeles distintos entre (marco y fondo + animación) y el GIF final, en los 72 pasos:", dif)


if __name__ == "__main__":
    main()
