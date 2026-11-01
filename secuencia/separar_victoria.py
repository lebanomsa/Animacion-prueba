"""Separa la composición final de 'Matilda victoria' (x5, marco negro-morado + fondo 2) en dos archivos:

  1. marco_y_fondo_victoria_x5.png   1024x1024, el marco con 'fondo 2' dentro de la ventana (sin personaje)
  2. matilda_victoria_x5_sola.gif     1024x1024 transparente, solo la animación, en la misma posición que en la
                                      composición: al ponerla encima del PNG queda exactamente igual que el GIF final
  3. matilda_victoria_x5_recortada.gif  470x610 transparente, la animación sola recortada a su tamaño (por si se usa aparte)

Usa los mismos parámetros que componer_marco.py ("victoria_x5") y comprueba que PNG + animación reproduce el GIF final.
Salida: salida/separado/
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import componer_marco as cm      # noqa: E402
import marco                     # noqa: E402

OUT = HERE / "salida" / "separado"


def gif_transparente(frames, ruta, dur):
    colores = sorted({p[:3] for im in frames for p in im.getdata() if p[3]})
    assert len(colores) <= 255
    index = {c: i + 1 for i, c in enumerate(colores)}
    flat = [255, 0, 255] + [v for c in colores for v in c]
    out = []
    for im in frames:
        p = Image.new("P", im.size, 0); p.putpalette(flat + [0] * (768 - len(flat)))
        p.putdata([index[q[:3]] if q[3] else 0 for q in im.getdata()]); out.append(p)
    out[0].save(ruta, save_all=True, append_images=out[1:], duration=dur, loop=0, transparency=0, disposal=2,
                optimize=False)
    return len(colores)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = cm.CONFIG["victoria_x5"]
    sc, crop, fy0, feet_y = cfg["sc"], cfg["crop"], cfg["y0"], cfg["feet"]
    frame, (wx0, wy0, wx1, wy1) = marco.build()
    win_x, win_y = wx0 * cm.S_FRAME, wy0 * cm.S_FRAME
    win_w = (wx1 - wx0 + 1) * cm.S_FRAME
    anim, feet_row, _, tick = cm.victory_frames()
    fw, fh = anim[0].size
    anim_rgb = {tuple(p[:3]) for f in anim for p in f.getdata() if p[3]}

    # mismas agrupaciones de color que la composición final
    fondo = Image.open(cm.ROOT / "fondo 2.PNG").convert("RGB")
    fx = (fondo.width - crop) // 2
    fondo_c = np.asarray(fondo.crop((fx, fy0, fx + crop, fy0 + crop)))
    m_arr = np.asarray(frame); m_op = m_arr[..., 3] > 0
    kf, km = 105, 130
    while True:
        fq = cm.quantize_rgb(fondo_c.reshape(-1, 3), kf).reshape(fondo_c.shape)
        mq = m_arr[..., :3].copy(); mq[m_op] = cm.quantize_rgb(m_arr[..., :3][m_op], km)
        total = (anim_rgb | {tuple(c) for c in np.unique(fq.reshape(-1, 3), axis=0)}
                 | {tuple(c) for c in np.unique(mq[m_op], axis=0)} | {(0, 0, 0)})
        if len(total) <= 256:
            break
        km -= max(1, len(total) - 256)
    marco_big = Image.fromarray(np.dstack([mq, m_arr[..., 3]]), "RGBA").resize((cm.SIZE,) * 2, Image.NEAREST)
    fondo_big = Image.fromarray(fq, "RGB").resize((crop * sc,) * 2, Image.NEAREST)
    ax = win_x + (win_w - fw * sc) // 2
    ay = win_y + feet_y - feet_row * sc

    # 1. marco + fondo
    base = Image.new("RGBA", (cm.SIZE, cm.SIZE), (0, 0, 0, 255))
    base.alpha_composite(fondo_big.convert("RGBA"), (win_x, win_y))
    base.alpha_composite(marco_big)
    ruta_png = OUT / "marco_y_fondo_victoria_x5.png"
    base.convert("RGB").save(ruta_png)

    # 2 y 3. animación sola
    capas, recortes = [], []
    for f in anim:
        g = f.resize((fw * sc, fh * sc), Image.NEAREST)
        c = Image.new("RGBA", (cm.SIZE, cm.SIZE), (0, 0, 0, 0)); c.alpha_composite(g, (ax, ay))
        capas.append(c); recortes.append(g)
    n1 = gif_transparente(capas, OUT / "matilda_victoria_x5_sola.gif", tick)
    n2 = gif_transparente(recortes, OUT / "matilda_victoria_x5_recortada.gif", tick)

    # comprobación: PNG + animación == GIF final
    final = Image.open(HERE / "salida" / cfg["out"])
    dif = 0
    png = Image.open(ruta_png).convert("RGBA")
    sola = Image.open(OUT / "matilda_victoria_x5_sola.gif")
    for i in range(len(anim)):
        final.seek(i); sola.seek(i)
        ref = np.asarray(final.convert("RGB")).astype(int)
        comp = png.copy(); comp.alpha_composite(sola.convert("RGBA"))
        dif += int((np.abs(np.asarray(comp.convert("RGB")).astype(int) - ref).sum(-1) > 0).sum())
    print(f"{ruta_png.name}: {base.size}")
    print(f"matilda_victoria_x5_sola.gif: {len(capas)} fotogramas de {tick} ms, 1024x1024, {n1} colores, "
          f"{(OUT / 'matilda_victoria_x5_sola.gif').stat().st_size / 1024:.0f} KB; posición del personaje ({ax}, {ay})")
    print(f"matilda_victoria_x5_recortada.gif: {recortes[0].size}, {n2} colores, "
          f"{(OUT / 'matilda_victoria_x5_recortada.gif').stat().st_size / 1024:.0f} KB")
    print("píxeles distintos entre (PNG + animación) y el GIF final, en todos los fotogramas:", dif)


if __name__ == "__main__":
    main()
