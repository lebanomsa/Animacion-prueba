"""Separa la composición final de Agalia (agalia_marco_rojo_c.gif) en marco + fondo y animación.

Aquí el marco rojo y el fondo ('agalia stage', x5) están quietos, así que el marco con fondo es un PNG.
La animación (Agalia + humo, y las chispas a los lados) va en un GIF transparente de 1024x1024 en la misma posición:
  * Agalia y el humo van por DETRÁS del marco: donde el marco los tapa, la capa es transparente
  * las chispas van por DELANTE del marco (sobresalen de la ventana), como en el original

  marco_y_fondo_agalia.png        1024x1024, fijo
  agalia_animacion_sola.gif       1024x1024 transparente, en su sitio
  agalia_animacion_recortada.gif  la misma animación recortada a su tamaño
Usa los mismos parámetros que componer_marco_agalia_c.py y comprueba que PNG + animación reproduce el GIF final.
Salida: salida_separada/
"""
import contextlib
import io
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import componer_marco_agalia_c as cc          # noqa: E402
from componer_marco_agalia_c import ma, marco, ROJO_CLARO, ROJO_OSCURO, BG_X0, BG_COLS, BG_ROWS, quantize_rgb  # noqa: E402

OUT = HERE / "salida_separada"
key = lambda a: a[..., 0].astype(np.uint32) << 16 | a[..., 1].astype(np.uint32) << 8 | a[..., 2]


def gif_transparente(frames, ruta, dur):
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
    out[0].save(ruta, save_all=True, append_images=out[1:], duration=dur, loop=0, transparency=0, disposal=2, optimize=False)
    return len(cols)


def por_paso(ruta, total, tick):
    g = Image.open(ruta); out = []
    for i in range(g.n_frames):
        g.seek(i); f = g.convert("RGBA")
        out += [f] * round(g.info.get("duration", tick) / tick)
    assert len(out) == total, (ruta.name, len(out))
    return out


def main():
    OUT.mkdir(exist_ok=True)
    S, SIZE, S_FRAME = cc.S, cc.SIZE, cc.S_FRAME
    frame, (wx0, wy0, wx1, wy1) = marco.build(ROJO_CLARO, ROJO_OSCURO)
    win_x, win_y = wx0 * S_FRAME, wy0 * S_FRAME
    win = (wx1 - wx0 + 1) * S_FRAME
    ma.SPARK_SCALE, ma.SPARK_MODE, ma.SPARK_GAP = 1, "lados", cc.SPARK_GAP
    with contextlib.redirect_stdout(io.StringIO()):
        chars, sparks = ma.main(layers=True)
    uc, us = cc.union_bbox(chars), cc.union_bbox(sparks)
    cw, ch = uc[2] - uc[0], uc[3] - uc[1]
    ox = win_x + (win - cw * S) // 2 - uc[0] * S
    oy = win_y + win - cc.BOTTOM_MARGIN - ch * S - uc[1] * S

    bg = Image.open(cc.ROOT / "agalia stage.png").convert("RGB")
    crop = np.asarray(bg.crop((BG_X0, 0, BG_X0 + BG_COLS, BG_ROWS)))
    big = np.asarray(Image.fromarray(crop).resize((BG_COLS * S, BG_ROWS * S), Image.NEAREST))
    pad = win - big.shape[0]
    mirror = np.asarray(Image.fromarray(crop[:pad // S][::-1]).resize((BG_COLS * S, pad), Image.NEAREST))
    bg_big = np.concatenate([mirror, big], axis=0)

    anim_rgb = {tuple(p[:3]) for f in chars + sparks for p in f.getdata() if p[3]}
    m_arr = np.asarray(frame); m_op = m_arr[..., 3] > 0
    km = 170
    while True:
        mq = m_arr[..., :3].copy(); mq[m_op] = quantize_rgb(m_arr[..., :3][m_op], km)
        total = (anim_rgb | {tuple(c) for c in np.unique(bg_big.reshape(-1, 3), axis=0)}
                 | {tuple(c) for c in np.unique(mq[m_op], axis=0)} | {(0, 0, 0)})
        if len(total) <= 256:
            break
        km -= max(1, len(total) - 256)
    marco_big = Image.fromarray(np.dstack([mq, m_arr[..., 3]]), "RGBA").resize((marco.N * S_FRAME,) * 2, Image.NEAREST)
    tapa = np.asarray(marco_big)[..., 3] > 0
    print(f"marco con {km} tonos (igual que el final)")

    # 1. marco + fondo
    base = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 255))
    base.alpha_composite(Image.fromarray(bg_big, "RGB").convert("RGBA"), (win_x, win_y))
    base.alpha_composite(marco_big)
    ruta_png = OUT / "marco_y_fondo_agalia.png"
    base.convert("RGB").save(ruta_png)

    # 2. animación: personaje (sin lo que tapa el marco) + chispas encima
    capas = []
    for c_img, s_img in zip(chars, sparks):
        lay = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        lay.alpha_composite(c_img.crop(uc).resize((cw * S, ch * S), Image.NEAREST), (ox + uc[0] * S, oy + uc[1] * S))
        a = np.array(lay); a[tapa] = 0
        lay = Image.fromarray(a, "RGBA")
        if s_img.getchannel("A").getbbox():
            lay.alpha_composite(s_img.crop(us).resize(((us[2] - us[0]) * S, (us[3] - us[1]) * S), Image.NEAREST),
                                (ox + us[0] * S, oy + us[1] * S))
        capas.append(lay)
    n = gif_transparente(capas, OUT / "agalia_animacion_sola.gif", ma.TICK)
    boxes = [c.getchannel("A").getbbox() for c in capas if c.getchannel("A").getbbox()]
    box = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
    gif_transparente([c.crop(box) for c in capas], OUT / "agalia_animacion_recortada.gif", ma.TICK)
    print(f"agalia_animacion_sola.gif: {len(capas)} pasos de {ma.TICK} ms = {len(capas) * ma.TICK} ms, {n} colores, "
          f"{(OUT / 'agalia_animacion_sola.gif').stat().st_size / 1024:.0f} KB; recorte {box[2] - box[0]}x{box[3] - box[1]}")

    # comprobación contra el GIF final
    final = por_paso(HERE / "agalia_marco_rojo_c.gif", len(capas), ma.TICK)
    sola = por_paso(OUT / "agalia_animacion_sola.gif", len(capas), ma.TICK)
    png = Image.open(ruta_png).convert("RGBA")
    dif = 0
    for t in range(len(capas)):
        comp = png.copy(); comp.alpha_composite(sola[t])
        dif += int((np.abs(np.asarray(comp.convert("RGB")).astype(int)
                           - np.asarray(final[t].convert("RGB")).astype(int)).sum(-1) > 0).sum())
    print(f"píxeles distintos entre (PNG + animación) y el GIF final, en los {len(capas)} pasos:", dif)


if __name__ == "__main__":
    main()
