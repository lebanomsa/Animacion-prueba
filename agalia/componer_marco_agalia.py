"""Agalia dentro del marco rojo sangre (claro arriba, más oscuro abajo) con 'agalia stage.png' de fondo.

Capas (de atrás hacia delante): negro -> agalia stage (x5) -> Agalia (x3) -> marco (x8).
El marco es el de siempre (limpio y simétrico, marco.build) recoloreado: rojo sangre claro arriba y rojo más
oscuro abajo. La animación mide 210 px de ancho por las chispas de los lados, así que a x3 (630 px) es lo más grande
que cabe en la ventana de 640 px; el fondo va a x5 para cubrirla (148x125 px de origen, recorte de 128 columnas
y 15 px de relleno por arriba reflejando sus filas superiores). Los píxeles del personaje (x3) y los del fondo (x5)
no miden lo mismo.
Un GIF admite 256 colores: Agalia (71) y el fondo (23) se conservan exactos y el marco se agrupa en el resto.

Salida: agalia_marco_rojo.gif, marco_rojo_1024.png y una vista previa.
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

# Paletas por brillo (V entre 0 y 1): arriba rojo sangre claro, abajo rojo oscuro
ROJO_CLARO = [(0.0, (46, 0, 6)), (0.3, (118, 8, 18)), (0.6, (190, 28, 36)),
              (0.85, (228, 70, 66)), (1.0, (255, 160, 150))]
ROJO_OSCURO = [(0.0, (12, 0, 3)), (0.3, (44, 0, 8)), (0.6, (86, 4, 16)),
               (0.85, (128, 14, 28)), (1.0, (182, 52, 64))]

SIZE, S_FRAME = 1024, 8
S_CHAR, S_BG = 3, 5
BOTTOM_Y = 530              # fila (dentro de la ventana) donde acaba el contenido de la animación
BG_X0, BG_COLS, BG_ROWS = 10, 128, 125
SPARK_GAP = 1               # chispas pegadas al contorno para que la animación quepa en 213 columnas (x3)


def quantize_rgb(rgb, k):
    img = Image.fromarray(rgb.reshape(-1, 1, 3).astype(np.uint8), "RGB")
    q = img.quantize(colors=k, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = np.array(q.getpalette()[:768], np.uint8).reshape(-1, 3)
    return pal[np.asarray(q).reshape(-1)]


def main():
    frame, (wx0, wy0, wx1, wy1) = marco.build(ROJO_CLARO, ROJO_OSCURO)
    win_x, win_y = wx0 * S_FRAME, wy0 * S_FRAME
    win_w, win_h = (wx1 - wx0 + 1) * S_FRAME, (wy1 - wy0 + 1) * S_FRAME
    print(f"ventana: {win_w}x{win_h} px en ({win_x}, {win_y})")

    # ---- animación recortada al contenido exacto
    ma.SPARK_GAP = SPARK_GAP
    with contextlib.redirect_stdout(io.StringIO()) as out_:
        anim, box = ma.main(save=False)
    print(out_.getvalue().strip().splitlines()[1] if len(out_.getvalue().splitlines()) > 1 else "")
    boxes = [b for b in (f.getchannel("A").getbbox() for f in anim) if b]
    ub = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
    anim = [f.crop(ub) for f in anim]
    fw, fh = anim[0].size
    anim_rgb = {tuple(p[:3]) for f in anim for p in f.getdata() if p[3]}
    print(f"animación: {len(anim)} pasos, {fw}x{fh} px -> {fw * S_CHAR}x{fh * S_CHAR} px, {len(anim_rgb)} colores")
    assert fw * S_CHAR <= win_w and fh * S_CHAR <= win_h, (fw * S_CHAR, fh * S_CHAR)

    # ---- fondo: x5, recorte de 128 columnas, relleno por arriba reflejando filas
    bg = Image.open(ROOT / "agalia stage.png").convert("RGB")
    crop = np.asarray(bg.crop((BG_X0, 0, BG_X0 + BG_COLS, BG_ROWS)))
    big = np.asarray(Image.fromarray(crop).resize((BG_COLS * S_BG, BG_ROWS * S_BG), Image.NEAREST))
    pad = win_h - big.shape[0]
    assert pad >= 0 and pad % S_BG == 0 and big.shape[1] == win_w, (big.shape, win_w, win_h)
    mirror = np.asarray(Image.fromarray(crop[:pad // S_BG][::-1]).resize((BG_COLS * S_BG, pad), Image.NEAREST))
    bg_big = np.concatenate([mirror, big], axis=0)
    bg_colors = len(np.unique(bg_big.reshape(-1, 3), axis=0))
    print(f"fondo: {bg_colors} colores, recorte {BG_COLS}x{BG_ROWS} a x{S_BG} (+{pad} px reflejando las filas superiores)")

    # ---- marco: agrupar tonos para que todo quepa en 256 colores
    m_arr = np.asarray(frame)
    m_opaque = m_arr[..., 3] > 0
    km = 170
    while True:
        mq_rgb = m_arr[..., :3].copy()
        mq_rgb[m_opaque] = quantize_rgb(m_arr[..., :3][m_opaque], km)
        total = (anim_rgb | {tuple(c) for c in np.unique(bg_big.reshape(-1, 3), axis=0)}
                 | {tuple(c) for c in np.unique(mq_rgb[m_opaque], axis=0)} | {(0, 0, 0)})
        print(f"  marco {km} colores -> paleta total {len(total)}")
        if len(total) <= 256:
            break
        km -= max(1, len(total) - 256)
    d_m = np.abs(mq_rgb.astype(int) - m_arr[..., :3].astype(int)).max(axis=2)[m_opaque]
    print(f"error de agrupación del marco: media {d_m.mean():.2f}, máx {d_m.max()} (niveles por canal)")
    marco_q = Image.fromarray(np.dstack([mq_rgb, m_arr[..., 3]]), "RGBA")
    marco_big = marco_q.resize((marco.N * S_FRAME, marco.N * S_FRAME), Image.NEAREST)
    marco_big.save(HERE / "marco_rojo_1024.png")

    # ---- composición
    ax = win_x + (win_w - fw * S_CHAR) // 2
    ay = win_y + BOTTOM_Y - fh * S_CHAR
    assert win_y <= ay and ay + fh * S_CHAR <= win_y + win_h, (ay, fh * S_CHAR)
    print(f"Agalia en ({ax}, {ay}), su contenido acaba en y={ay + fh * S_CHAR - win_y} dentro de la ventana")
    base = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 255))
    base.alpha_composite(Image.fromarray(bg_big, "RGB").convert("RGBA"), (win_x, win_y))
    frames = []
    for f in anim:
        img = base.copy()
        img.alpha_composite(f.resize((fw * S_CHAR, fh * S_CHAR), Image.NEAREST), (ax, ay))
        img.alpha_composite(marco_big)
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
    path = HERE / "agalia_marco_rojo.gif"
    out[0].save(path, save_all=True, append_images=out[1:], duration=ma.TICK, loop=0, disposal=1, optimize=False)
    print(f"{path.name}: {len(out)} pasos de {ma.TICK} ms = {len(out) * ma.TICK} ms, {path.stat().st_size / 1024:.0f} KB")
    (HERE / "previews").mkdir(exist_ok=True)
    frames[17].save(HERE / "previews" / "vista_previa_agalia_marco_rojo.png")


if __name__ == "__main__":
    main()
