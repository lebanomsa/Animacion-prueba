"""Escenario de nieve animado, pensado para la ventana del marco (640x640 px).

La ventana se llena con un tramo de 320x320 píxeles del escenario a escala x2 (vecino más cercano, como el resto de
los fondos pixelados). El cielo es un único cielo con luna (512 px de ancho), así que no hay costuras; el suelo es el
sprite largo. Los 9 cielos con luna de la hoja son un ciclo de parpadeo de estrellas (varias se atenúan en el 2º
fotograma y destellan en el 9º): se recorren en el orden de lectura de la hoja.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "secuencia"))
import stage as st              # noqa: E402
import marco                    # noqa: E402

MOON_FRAMES = [3, 4, 5, 9, 10, 11, 15, 16, 17]     # cielos con luna, en el orden de lectura de la hoja
W = H = 320                     # píxeles del escenario que caben en la ventana a x2
SCALE = 2
Y0 = 50                         # fila del escenario donde empieza el recorte
SKY = (14, 16, 38)

# Opciones de tramo: (nombre, x0 del recorte en el suelo, columna de la luna dentro del recorte)
TRAMOS = [
    ("A: escalón de hielo recortado a la izquierda y luna a la derecha", 100, 235),
    ("B: nieve llana en el centro", 900, 230),
    ("C: foso oscuro a la derecha", 2176 - W, 150),
]


def paste_clip(dst, src, x, y):
    """alpha_composite con recorte (admite posiciones negativas o fuera del destino)."""
    sx, sy = max(-x, 0), max(-y, 0)
    dx, dy = max(x, 0), max(y, 0)
    w = min(src.width - sx, dst.width - dx)
    h = min(src.height - sy, dst.height - dy)
    if w > 0 and h > 0:
        dst.alpha_composite(src.crop((sx, sy, sx + w, sy + h)), (dx, dy))


def ventana(x0, moon_col, sky_img, ground, y0=Y0):
    """Recorte de WxH píxeles del escenario (RGB) con el cielo `sky_img` y el suelo."""
    can = Image.new("RGBA", (W, H), SKY + (255,))
    tile_x = moon_col - 287                        # la luna está en la columna 287 del cielo
    paste_clip(can, sky_img.convert("RGBA"), tile_x, st.SKY_Y - y0)
    paste_clip(can, ground, -x0, st.SUELO_Y - st.GROUND_FLAT_Y - y0)
    return can.convert("RGB")


def vista_marco(img_640, win_xy=(192, 192)):
    """Compone la ventana en el marco azul (provisional) para ver cómo queda."""
    TOP = [(0.0, (1, 2, 10)), (0.3, (5, 10, 36)), (0.6, (11, 22, 68)), (0.85, (24, 46, 110)), (1.0, (62, 92, 160))]
    BOT = [(0.0, (4, 6, 26)), (0.3, (16, 26, 74)), (0.6, (38, 68, 148)), (0.85, (78, 120, 208)), (1.0, (176, 206, 252))]
    frame, (wx0, wy0, wx1, wy1) = marco.build(TOP, BOT)
    big = frame.resize((marco.N * 8,) * 2, Image.NEAREST)
    base = Image.new("RGBA", (1024, 1024), (0, 0, 0, 255))
    base.alpha_composite(img_640.convert("RGBA"), (wx0 * 8, wy0 * 8))
    base.alpha_composite(big)
    return base.convert("RGB")


def _corte_mediano(rgb, k):
    q = Image.fromarray(rgb.reshape(-1, 1, 3).astype(np.uint8), "RGB").quantize(
        colors=k, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    return np.array(q.getpalette()[:k * 3]).reshape(-1, 3)


def paleta(frames, k, k_estrellas=32):
    """Paleta de k colores para todos los fotogramas: k_estrellas colores representativos de los píxeles que
    cambian entre ellos (las estrellas que parpadean, que tienen unos 200 tonos por los bordes suavizados) para que
    ninguna se pierda, y el resto por corte mediano sin tramado."""
    A = np.stack(frames).astype(int)
    lum = A.sum(axis=-1)
    cambia = (lum.max(axis=0) - lum.min(axis=0)) > 25
    estrellas = np.unique(A[:, cambia].reshape(-1, 3), axis=0)
    reservados = _corte_mediano(estrellas, min(k_estrellas, len(estrellas)))
    mosaic = np.concatenate([f.reshape(-1, 3) for f in frames]).astype(np.uint8)[::3]
    base = _corte_mediano(mosaic, k - len(reservados))
    return np.concatenate([reservados, base]).astype(int), len(reservados), int(cambia.sum())


def reducir(img, pal):
    flat = img.reshape(-1, 3).astype(int)
    d = ((flat[:, None, :] - pal[None, :, :]) ** 2).sum(axis=2)
    return pal[d.argmin(axis=1)].reshape(img.shape).astype(np.uint8)


def gif_paleta(frames_rgb, duracion, path):
    """GIF con paleta global exacta (cada color de los fotogramas tiene su índice)."""
    key = lambda a: a[..., 0].astype(np.uint32) << 16 | a[..., 1].astype(np.uint32) << 8 | a[..., 2]
    keys = np.unique(np.concatenate([key(f).ravel() for f in frames_rgb]))
    assert len(keys) <= 256, len(keys)
    pal = np.zeros(768, np.uint8)
    pal[0:len(keys) * 3:3], pal[1:len(keys) * 3:3], pal[2:len(keys) * 3:3] = keys >> 16, keys >> 8 & 255, keys & 255
    out = []
    for f in frames_rgb:
        p = Image.fromarray(np.searchsorted(keys, key(f)).astype(np.uint8), "P"); p.putpalette(pal.tolist()); out.append(p)
    out[0].save(path, save_all=True, append_images=out[1:], duration=duracion, loop=0, disposal=1, optimize=False)
    return len(keys)


def animar(tramo=0, k_stage=128):
    """Devuelve los fotogramas (a x2, ya reducidos de color) del tramo elegido."""
    sheet = st.load_sheet(); sky = st.skies(sheet); ground = st.ground(sheet)
    _, x0, moon_col = TRAMOS[tramo]
    native = [np.asarray(ventana(x0, moon_col, sky[i], ground)) for i in MOON_FRAMES]
    pal, n_res, n_cambian = paleta(native, k_stage)
    red = [reducir(f, pal) for f in native]
    err = np.mean([np.abs(r.astype(int) - f.astype(int)).mean() for r, f in zip(red, native)])
    print(f"escenario: {len(native)} fotogramas de {W}x{H}; paleta de {len(pal)} colores "
          f"({n_res} reservados para {n_cambian} píxeles que parpadean); error medio {err:.2f} niveles")
    return [np.asarray(Image.fromarray(r).resize((W * SCALE, H * SCALE), Image.NEAREST)) for r in red]


def main():
    big = animar()
    path = HERE / "nieve_stage_anim.gif"
    n = gif_paleta(big, 140, path)
    print(f"{path.name}: {len(big)} fotogramas de {big[0].shape[1]}x{big[0].shape[0]}, {n} colores, {path.stat().st_size / 1024:.0f} KB")

    # ---- el mismo escenario dentro del marco (azul provisional) para ver cómo queda
    TOP = [(0.0, (1, 2, 10)), (0.3, (5, 10, 36)), (0.6, (11, 22, 68)), (0.85, (24, 46, 110)), (1.0, (62, 92, 160))]
    BOT = [(0.0, (4, 6, 26)), (0.3, (16, 26, 74)), (0.6, (38, 68, 148)), (0.85, (78, 120, 208)), (1.0, (176, 206, 252))]
    frame, (wx0, wy0, wx1, wy1) = marco.build(TOP, BOT)
    m = np.asarray(frame); op = m[..., 3] > 0
    stage_cols = {tuple(c) for c in np.unique(np.concatenate([b.reshape(-1, 3) for b in big]), axis=0)}
    km = 255 - len(stage_cols)
    sys.path.insert(0, str(ROOT / "agalia"))
    from componer_marco_agalia import quantize_rgb
    mq = m[..., :3].copy(); mq[op] = quantize_rgb(m[..., :3][op], km)
    big_frame = Image.fromarray(np.dstack([mq, m[..., 3]]), "RGBA").resize((marco.N * 8,) * 2, Image.NEAREST)
    en_marco = []
    for b in big:
        base = Image.new("RGBA", (1024, 1024), (0, 0, 0, 255))
        base.alpha_composite(Image.fromarray(b, "RGB").convert("RGBA"), (wx0 * 8, wy0 * 8))
        base.alpha_composite(big_frame)
        en_marco.append(np.asarray(base.convert("RGB")))
    p2 = HERE / "nieve_stage_marco_prueba.gif"
    n2 = gif_paleta(en_marco, 140, p2)
    print(f"{p2.name}: {len(en_marco)} fotogramas de 1024x1024, {n2} colores (marco: {km} tonos), {p2.stat().st_size / 1024:.0f} KB")
    (HERE / "previews").mkdir(exist_ok=True)
    Image.fromarray(en_marco[0]).save(HERE / "previews" / "nieve_stage_marco_prueba.png")
    # ampliación de la estrella que más cambia, en 3 fotogramas
    lum = np.stack([b.astype(int) for b in big]).sum(axis=-1)
    var = lum.max(axis=0) - lum.min(axis=0); y, x = np.unravel_index(var.argmax(), var.shape)
    x0, y0 = int(np.clip(x - 24, 0, big[0].shape[1] - 48)), int(np.clip(y - 24, 0, big[0].shape[0] - 48))
    tira = Image.new("RGB", (3 * 240 + 20, 240), (20, 10, 14))
    for i, fi in enumerate((0, 1, 8)):
        tira.paste(Image.fromarray(big[fi][y0:y0 + 48, x0:x0 + 48]).resize((240, 240), Image.NEAREST), (i * 250, 0))
    tira.save(HERE / "previews" / "nieve_estrella_parpadeo.png")
    print("estrella que más cambia en", (int(x), int(y)), "de la ventana de 640x640")


if __name__ == "__main__":
    main()
