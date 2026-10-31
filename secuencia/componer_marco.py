"""Compone el marco negro-morado + 'fondo 2.PNG' + animación de Matilda (balanceo con nota musical).

Capas (de atrás hacia delante): negro -> fondo 2 (recorte cuadrado, x3) -> animación (x3) -> marco (x8).
El fondo y la animación van a la misma escala (x3), así que sus píxeles miden lo mismo.
Un GIF admite 256 colores como máximo: la animación (43 colores) se conserva exacta y el fondo
y el marco, que tienen muchos tonos casi idénticos, se agrupan en los colores que quedan libres.

Salida (./salida): matilda_marco_negro_morado.gif, marco_negro_morado_1024.png (ventana transparente)
y vista previa de un fotograma.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import make_secuencia as ms                                   # noqa: E402
import marco                                                  # noqa: E402
from sprites import M_BASE, matilda_frames, music_frames, smoke_frames  # noqa: E402

ROOT = HERE.parent
OUT = HERE / "salida"
VARIANT = "B_balanceo_musica"
SIZE, S_FRAME, S_CONT = 1024, 8, 3
FEET_Y = 540            # fila (dentro de la ventana) donde apoyan los pies de Matilda: borde de las piedras
FEET_Y_VICTORIA = 556   # la pose agachada apoya en la franja de piedras (que va de 540 a 585)
FONDO_CROP = 213        # 213 px x3 = 639 px: cabe en la ventana de 640 px
FONDO_Y0 = 30           # fila del fondo donde empieza el recorte (el fondo acaba en una franja negra)


def quantize_rgb(rgb, k):
    """Agrupa los colores de un array (n,3) en k colores (corte mediano, sin tramado)."""
    img = Image.fromarray(rgb.reshape(-1, 1, 3).astype(np.uint8), "RGB")
    q = img.quantize(colors=k, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = np.array(q.getpalette()[:768], np.uint8).reshape(-1, 3)
    return pal[np.asarray(q).reshape(-1)]


def animation_frames():
    top, bot = matilda_frames(); smoke = smoke_frames()
    pose_masks = {}
    for kind, frs in (("T", top), ("B", bot)):
        for i, f in enumerate(frs):
            pose_masks[(kind, i)] = np.asarray(ms.matilda_canvas(f).getchannel("A")) > 0
    sched = ms.make_schedule(ms.VARIANTS[VARIANT]); cycle = len(sched)
    bombs = ms.load_bombs(smoke, pose_masks, cycle)
    synth = ms.make_synth(bot)
    puffs = ms.place_music(music_frames(), bot, synth)
    frames, _ = ms.build_frames(top, bot, smoke, bombs, sched, synth, puffs)
    boxes = [f.getchannel("A").getbbox() for f in frames]
    box = (min(b[0] for b in boxes), min(b[1] for b in boxes),
           max(b[2] for b in boxes), max(b[3] for b in boxes))
    return [f.crop(box) for f in frames], M_BASE - box[1], cycle


def victory_frames():
    """Los 15 fotogramas de 'matilda victoria.PNG' (94x122, pies en el borde inferior)."""
    sys.path.insert(0, str(ROOT / "victoria"))
    import make_victoria as mv
    fr = mv.cells()
    return fr, fr[0].height, len(fr), mv.TICK


def main(which="sway"):
    OUT.mkdir(exist_ok=True)
    frame, (wx0, wy0, wx1, wy1) = marco.build()
    win_x, win_y = wx0 * S_FRAME, wy0 * S_FRAME
    win_w, win_h = (wx1 - wx0 + 1) * S_FRAME, (wy1 - wy0 + 1) * S_FRAME
    print(f"ventana: {win_w}x{win_h} px en ({win_x}, {win_y})")

    if which == "victoria":
        anim, feet_row, cycle, tick_ms = victory_frames()
        feet_y, out_name, preview_idx = FEET_Y_VICTORIA, "matilda_victoria_marco_negro_morado.gif", 7
    else:
        anim, feet_row, cycle = animation_frames()
        tick_ms, feet_y, out_name, preview_idx = ms.TICK, FEET_Y, "matilda_marco_negro_morado.gif", cycle - 8
    fw, fh = anim[0].size
    anim_rgb = {tuple(p[:3]) for f in anim for p in f.getdata() if p[3]}
    print(f"animación: {len(anim)} pasos, {fw}x{fh} px, {len(anim_rgb)} colores exactos")

    fondo = Image.open(ROOT / "fondo 2.PNG").convert("RGB")
    fx = (fondo.width - FONDO_CROP) // 2
    fy = FONDO_Y0
    fondo_c = np.asarray(fondo.crop((fx, fy, fx + FONDO_CROP, fy + FONDO_CROP)))
    print(f"fondo 2: recorte de {FONDO_CROP}x{FONDO_CROP} desde ({fx}, {fy}), "
          f"{len(np.unique(fondo_c.reshape(-1, 3), axis=0))} colores")
    m_arr = np.asarray(frame)
    m_opaque = m_arr[..., 3] > 0

    # reparto de la paleta de 256 colores: animación exacta, el resto para fondo y marco
    kf, km = 105, 130        # el marco se reduce solo lo necesario para que quepa en 256 colores
    while True:
        fq = quantize_rgb(fondo_c.reshape(-1, 3), kf).reshape(fondo_c.shape)
        mq_rgb = m_arr[..., :3].copy()
        mq_rgb[m_opaque] = quantize_rgb(m_arr[..., :3][m_opaque], km)
        total = (anim_rgb | {tuple(c) for c in np.unique(fq.reshape(-1, 3), axis=0)}
                 | {tuple(c) for c in np.unique(mq_rgb[m_opaque], axis=0)} | {(0, 0, 0)})
        print(f"  fondo {kf} + marco {km} colores -> paleta total {len(total)}")
        if len(total) <= 256:
            break
        km -= max(1, len(total) - 256)
    d_f = np.abs(fq.astype(int) - fondo_c.astype(int)).max(axis=2)
    d_m = np.abs(mq_rgb.astype(int) - m_arr[..., :3].astype(int)).max(axis=2)[m_opaque]
    print(f"error de agrupación: fondo media {d_f.mean():.2f} máx {d_f.max()} | "
          f"marco media {d_m.mean():.2f} máx {d_m.max()} (niveles por canal)")

    marco_q = Image.fromarray(np.dstack([mq_rgb, m_arr[..., 3]]), "RGBA")
    marco_big = marco_q.resize((marco.N * S_FRAME, marco.N * S_FRAME), Image.NEAREST)
    marco_big.save(OUT / "marco_negro_morado_1024.png")
    fondo_big = Image.fromarray(fq, "RGB").resize((FONDO_CROP * S_CONT,) * 2, Image.NEAREST)

    ax = win_x + (win_w - fw * S_CONT) // 2
    ay = win_y + feet_y - feet_row * S_CONT
    assert win_y <= ay and ay + fh * S_CONT <= win_y + win_h, (ay, fh * S_CONT)
    print(f"animación en ({ax}, {ay}), pies en y={win_y + feet_y}")

    base = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 255))
    base.alpha_composite(fondo_big.convert("RGBA"), (win_x, win_y))
    frames = []
    for f in anim:
        img = base.copy()
        img.alpha_composite(f.resize((fw * S_CONT, fh * S_CONT), Image.NEAREST), (ax, ay))
        img.alpha_composite(marco_big)
        frames.append(img.convert("RGB"))

    # paleta global exacta: cada color de los fotogramas tiene su índice
    arrs = [np.asarray(f) for f in frames]
    keys = np.unique(np.concatenate([(a[..., 0].astype(np.uint32) << 16 | a[..., 1].astype(np.uint32) << 8
                                      | a[..., 2]).ravel() for a in arrs]))
    print("paleta global:", len(keys), "colores")
    assert len(keys) <= 256
    pal = np.zeros(768, np.uint8)
    pal[0:len(keys) * 3:3], pal[1:len(keys) * 3:3], pal[2:len(keys) * 3:3] = keys >> 16, keys >> 8 & 255, keys & 255
    out = []
    for a in arrs:
        k = a[..., 0].astype(np.uint32) << 16 | a[..., 1].astype(np.uint32) << 8 | a[..., 2]
        p = Image.fromarray(np.searchsorted(keys, k).astype(np.uint8), "P")
        p.putpalette(pal.tolist())
        out.append(p)
    path = OUT / out_name
    out[0].save(path, save_all=True, append_images=out[1:], duration=tick_ms, loop=0,
                disposal=1, optimize=False)
    print(f"{path.name}: {len(out)} pasos de {tick_ms} ms = {len(out) * tick_ms} ms, "
          f"{path.stat().st_size / 1024:.0f} KB")
    frames[preview_idx].save(OUT / ("vista_previa_" + out_name.replace(".gif", ".png")))
    for i in (0, preview_idx):
        frames[i].save(Path("/projects/sandbox/tmp") / f"marco_{which}_paso{i}.png")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "sway")
