"""Abigail (animación 'caminar') dentro del marco dorado -> rubí plateado, con 'Fondo 3.png'.

Capas (de atrás hacia delante): negro -> Fondo 3 (x5) -> Abigail (x5) -> marco (x8).
Marco: el mismo de siempre (limpio y simétrico), recoloreado: dorado arriba, degradado a un rubí con
reflejos plateados abajo. Abigail y el fondo van a la misma escala (x5), así que sus píxeles miden lo mismo.
A x5 la ventana de 640 px solo admite 128x128 píxeles del dibujo, por eso la animación se compacta un poco
(opción A): arco de la gorra de 24 px (antes 40), aterrizaje a 54 px (antes 66) y brillos a 3 px del contorno
(antes 4). El fondo se rellena con 15 px por arriba reflejando sus 3 filas superiores (625 de alto frente a 640).
Un GIF admite 256 colores: Abigail (40) y el fondo (59) se conservan exactos y el marco se agrupa en el resto.

Salida: abigail_marco_dorado_rubi_x5.gif, marco_dorado_rubi_1024.png y una vista previa.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "secuencia"))
import make_completa as mc      # noqa: E402
import marco                    # noqa: E402

# Paletas por brillo (V entre 0 y 1): arriba oro, abajo rubí con reflejos plateados
ORO = [(0.0, (16, 9, 2)), (0.3, (68, 42, 8)), (0.6, (150, 106, 22)),
       (0.85, (214, 168, 56)), (1.0, (255, 236, 150))]
RUBI_PLATA = [(0.0, (20, 0, 6)), (0.3, (88, 6, 26)), (0.6, (172, 24, 52)),
              (0.85, (214, 120, 138)), (1.0, (234, 228, 238))]

SIZE, S_FRAME = 1024, 8
S_CHAR, S_BG = 5, 5
CAP_APEX, CAP_DX, SPARK_OFFSET = 24, 54, 3      # animación compactada para que quepa en 128x128 píxeles
BG_X0, BG_COLS, BG_ROWS = 10, 128, 125


def quantize_rgb(rgb, k):
    img = Image.fromarray(rgb.reshape(-1, 1, 3).astype(np.uint8), "RGB")
    q = img.quantize(colors=k, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = np.array(q.getpalette()[:768], np.uint8).reshape(-1, 3)
    return pal[np.asarray(q).reshape(-1)]


def main():
    out_dir = HERE
    frame, (wx0, wy0, wx1, wy1) = marco.build(ORO, RUBI_PLATA)
    win_x, win_y = wx0 * S_FRAME, wy0 * S_FRAME
    win_w, win_h = (wx1 - wx0 + 1) * S_FRAME, (wy1 - wy0 + 1) * S_FRAME
    print(f"ventana: {win_w}x{win_h} px en ({win_x}, {win_y})")

    # ---- animación (RGBA recortada) y fila de los pies dentro de ese recorte
    mc.CAP_APEX, mc.CAP_DX, mc.SPARK_OFFSET = CAP_APEX, CAP_DX, SPARK_OFFSET
    anim, box = mc.main("caminar", save=False)
    boxes = [b for b in (f.getchannel("A").getbbox() for f in anim) if b]
    ub = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
    anim = [f.crop(ub) for f in anim]                  # recorte exacto al contenido (sin margen)
    fw, fh = anim[0].size
    feet_row = (mc.G + 2) - box[1] - ub[1]
    anim_rgb = {tuple(p[:3]) for f in anim for p in f.getdata() if p[3]}
    print(f"animación: {len(anim)} pasos, {fw}x{fh} px, {len(anim_rgb)} colores")

    # ---- fondo 3: x5, recorte de 128 columnas, relleno de 15 px por arriba
    bg = Image.open(ROOT / "Fondo 3.png").convert("RGB")
    crop = np.asarray(bg.crop((BG_X0, 0, BG_X0 + BG_COLS, BG_ROWS)))
    bg_colors = len(np.unique(crop.reshape(-1, 3), axis=0))
    big = np.asarray(Image.fromarray(crop).resize((BG_COLS * S_BG, BG_ROWS * S_BG), Image.NEAREST))
    pad = win_h - big.shape[0]
    assert pad >= 0 and big.shape[1] == win_w, (big.shape, win_w, win_h)
    assert pad % S_BG == 0
    mirror = np.asarray(Image.fromarray(crop[:pad // S_BG][::-1]).resize((BG_COLS * S_BG, pad), Image.NEAREST))
    bg_big = np.concatenate([mirror, big], axis=0)          # filas superiores reflejadas: continúa la textura sin rayas
    print(f"fondo 3: {bg_colors} colores, recorte {BG_COLS}x{BG_ROWS} a x{S_BG} = {big.shape[1]}x{big.shape[0]} "
          f"(+{pad} px reflejando las filas superiores)")

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
    marco_big.save(out_dir / "marco_dorado_rubi_1024.png")

    # ---- composición
    ax = win_x + (win_w - fw * S_CHAR) // 2
    ay = win_y + win_h - fh * S_CHAR                  # apoyada en el borde inferior de la ventana
    assert win_x <= ax and ax + fw * S_CHAR <= win_x + win_w, (ax, fw * S_CHAR)
    assert win_y <= ay and ay + fh * S_CHAR <= win_y + win_h, (ay, fh * S_CHAR)
    print(f"Abigail {fw * S_CHAR}x{fh * S_CHAR} px en ({ax}, {ay}); pies en y={ay + feet_row * S_CHAR} "
          f"(ventana {win_y}..{win_y + win_h})")
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
    path = out_dir / "abigail_marco_dorado_rubi_x5.gif"
    out[0].save(path, save_all=True, append_images=out[1:], duration=mc.TICK, loop=0,
                disposal=1, optimize=False)
    print(f"{path.name}: {len(out)} pasos de {mc.TICK} ms = {len(out) * mc.TICK} ms, {path.stat().st_size / 1024:.0f} KB")
    for i in (12, 30, 44, 66, 70):
        frames[i].save(Path("/projects/sandbox/tmp") / f"abigail_marco_paso{i}.png")
    frames[22].save(out_dir / "previews" / "vista_previa_abigail_marco_dorado_rubi_x5.png")


if __name__ == "__main__":
    main()
