"""Agalia dentro del marco rojo, opción C: personaje y fondo a x5, con las chispas a los lados.

Capas (de atrás hacia delante): negro -> agalia stage (x5) -> Agalia + humo (x5) -> marco (x8) -> chispas (x5).
Las chispas van al tamaño original del sprite (x1 antes de ampliar, es decir 145 px de ancho en pantalla), una a cada lado
de la silueta y espejadas, y se dibujan POR ENCIMA del marco: donde rebasan la ventana se ven sobre él.
El personaje y el humo caben enteros en la ventana (128x128 píxeles de dibujo); las chispas son lo único que sale.
Los píxeles del personaje y los del fondo miden lo mismo (x5).
Un GIF admite 256 colores: Agalia (71) y el fondo (23) se conservan exactos y el marco se agrupa en el resto.

Salida: agalia_marco_rojo_c.gif y una vista previa.
"""
import contextlib
import io
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "secuencia"))
import make_agalia as ma        # noqa: E402
import marco                    # noqa: E402
from componer_marco_agalia import ROJO_CLARO, ROJO_OSCURO, BG_X0, BG_COLS, BG_ROWS, quantize_rgb  # noqa: E402

SIZE, S_FRAME = 1024, 8
S = 5                       # escala del personaje y del fondo
BOTTOM_MARGIN = 20          # separación entre el contenido del personaje y el borde inferior de la ventana
SPARK_GAP = 2               # separación entre las chispas y la silueta


def union_bbox(imgs):
    boxes = [b for b in (i.getchannel("A").getbbox() for i in imgs) if b]
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def main():
    frame, (wx0, wy0, wx1, wy1) = marco.build(ROJO_CLARO, ROJO_OSCURO)
    win_x, win_y = wx0 * S_FRAME, wy0 * S_FRAME
    win = (wx1 - wx0 + 1) * S_FRAME
    print(f"ventana: {win}x{win} px en ({win_x}, {win_y})")

    # ---- capas de la animación: personaje+humo y chispas, por separado
    ma.SPARK_SCALE, ma.SPARK_MODE, ma.SPARK_GAP = 1, "lados", SPARK_GAP
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        chars, sparks = ma.main(layers=True)
    print(buf.getvalue().strip().splitlines()[1])
    uc, us = union_bbox(chars), union_bbox(sparks)
    cw, ch = uc[2] - uc[0], uc[3] - uc[1]
    print(f"personaje+humo: {cw}x{ch} px -> {cw * S}x{ch * S} px | chispas: {us[2] - us[0]}x{us[3] - us[1]} px "
          f"-> {(us[2] - us[0]) * S}x{(us[3] - us[1]) * S} px")
    assert cw * S <= win and ch * S <= win - BOTTOM_MARGIN, (cw * S, ch * S)
    # origen en pantalla del lienzo de la animación: el contenido del personaje centrado y apoyado abajo
    ox = win_x + (win - cw * S) // 2 - uc[0] * S
    oy = win_y + win - BOTTOM_MARGIN - ch * S - uc[1] * S
    ub = (min(uc[0], us[0]), min(uc[1], us[1]), max(uc[2], us[2]), max(uc[3], us[3]))
    sx0, sy0 = ox + us[0] * S, oy + us[1] * S
    print(f"las chispas ocupan x {ox + us[0] * S}..{ox + us[2] * S} (ventana {win_x}..{win_x + win}) "
          f"e y {oy + us[1] * S}..{oy + us[3] * S} (ventana {win_y}..{win_y + win})")
    assert 0 <= ox + us[0] * S and ox + us[2] * S <= SIZE and 0 <= oy + us[1] * S and oy + us[3] * S <= SIZE

    # ---- fondo x5, 128 columnas, 15 px de relleno por arriba reflejando filas
    bg = Image.open(ROOT / "agalia stage.png").convert("RGB")
    crop = np.asarray(bg.crop((BG_X0, 0, BG_X0 + BG_COLS, BG_ROWS)))
    big = np.asarray(Image.fromarray(crop).resize((BG_COLS * S, BG_ROWS * S), Image.NEAREST))
    pad = win - big.shape[0]
    assert pad >= 0 and pad % S == 0 and big.shape[1] == win
    mirror = np.asarray(Image.fromarray(crop[:pad // S][::-1]).resize((BG_COLS * S, pad), Image.NEAREST))
    bg_big = np.concatenate([mirror, big], axis=0)

    # ---- marco: agrupar tonos para que todo quepa en 256 colores
    anim_rgb = {tuple(p[:3]) for f in chars + sparks for p in f.getdata() if p[3]}
    print(f"animación: {len(chars)} pasos, {len(anim_rgb)} colores")
    m_arr = np.asarray(frame)
    m_opaque = m_arr[..., 3] > 0
    km = 170
    while True:
        mq_rgb = m_arr[..., :3].copy()
        mq_rgb[m_opaque] = quantize_rgb(m_arr[..., :3][m_opaque], km)
        total = (anim_rgb | {tuple(c) for c in np.unique(bg_big.reshape(-1, 3), axis=0)}
                 | {tuple(c) for c in np.unique(mq_rgb[m_opaque], axis=0)} | {(0, 0, 0)})
        if len(total) <= 256:
            break
        km -= max(1, len(total) - 256)
    print(f"marco: {km} tonos, paleta total {len(total)}")
    marco_q = Image.fromarray(np.dstack([mq_rgb, m_arr[..., 3]]), "RGBA")
    marco_big = marco_q.resize((marco.N * S_FRAME,) * 2, Image.NEAREST)

    # ---- composición
    base = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 255))
    base.alpha_composite(Image.fromarray(bg_big, "RGB").convert("RGBA"), (win_x, win_y))
    frames = []
    for c_img, s_img in zip(chars, sparks):
        img = base.copy()
        cc = c_img.crop(uc).resize((cw * S, ch * S), Image.NEAREST)
        img.alpha_composite(cc, (ox + uc[0] * S, oy + uc[1] * S))
        img.alpha_composite(marco_big)
        if s_img.getchannel("A").getbbox():
            sc_ = s_img.crop(us).resize(((us[2] - us[0]) * S, (us[3] - us[1]) * S), Image.NEAREST)
            img.alpha_composite(sc_, (ox + us[0] * S, oy + us[1] * S))   # por encima del marco
        frames.append(img.convert("RGB"))

    # ---- paleta global exacta
    arrs = [np.asarray(f) for f in frames]
    key = lambda a: a[..., 0].astype(np.uint32) << 16 | a[..., 1].astype(np.uint32) << 8 | a[..., 2]
    keys = np.unique(np.concatenate([key(a).ravel() for a in arrs]))
    print("paleta global:", len(keys), "colores")
    assert len(keys) <= 256
    pal = np.zeros(768, np.uint8)
    pal[0:len(keys) * 3:3], pal[1:len(keys) * 3:3], pal[2:len(keys) * 3:3] = keys >> 16, keys >> 8 & 255, keys & 255
    out = []
    for a in arrs:
        p = Image.fromarray(np.searchsorted(keys, key(a)).astype(np.uint8), "P")
        p.putpalette(pal.tolist())
        out.append(p)
    path = HERE / "agalia_marco_rojo_c.gif"
    out[0].save(path, save_all=True, append_images=out[1:], duration=ma.TICK, loop=0, disposal=1, optimize=False)
    print(f"{path.name}: {len(out)} pasos de {ma.TICK} ms = {len(out) * ma.TICK} ms, {path.stat().st_size / 1024:.0f} KB")
    (HERE / "previews").mkdir(exist_ok=True)
    frames[18].save(HERE / "previews" / "vista_previa_agalia_marco_rojo_c.png")
    for i in (10, 14, 18, 21, 30):
        frames[i].save(Path("/projects/sandbox/tmp") / f"agalia_c_paso{i}.png")


if __name__ == "__main__":
    main()
