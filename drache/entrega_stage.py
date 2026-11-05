"""Bucle 1 de Drache sobre el escenario 'stage drache.png' (Stage Fukai, Metal Slug Attack; crédito de la hoja: AkaPreston (rip), Patchworks (arreglo)).

Ventana elegida: columnas 1500-1880 del panorama (la zona de los pilares): la parte de arriba es la más oscura y las pepitas doradas resaltan.
Lienzo de 380x259 a tamaño natural. Techo: se amplía hacia arriba con un degradado suave del propio color de la parte alta. Se añade una sombra
suave bajo las botas. El fondo se agrupa en unos tonos para que, con los efectos, el GIF quepa en 256 colores.

Salida en drache/salida_stage/:
  bucle1_stage_1x.gif / _2x.gif          el bucle sobre el escenario
  fondo_stage_1x.png / _2x.png           solo el escenario (con la sombra)
  animacion_sola_1x.gif / _2x.gif        solo Drache y sus efectos sobre transparente (los efectos con borde duro: el GIF no admite transparencia suave)
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import bucles as b
import fondo as f

HERE = Path(__file__).parent
OUT = HERE / "salida_stage"
X0, W, H = 1500, 380, 259
SUELO = 245
K_FONDO = 120


def fondo_rgb():
    p = f.panorama()[:, X0:X0 + W].astype(float)
    alto = p.shape[0]
    extra = H - alto
    # techo: la parte alta del propio escenario reflejada hacia arriba (sin costura), cada vez más oscura
    arriba = p[:extra][::-1].copy()
    t = np.linspace(0.30, 1.0, extra)[:, None, None]
    arriba = arriba * t
    return np.vstack([arriba, p]).clip(0, 255).astype(np.uint8)


def con_sombra(img):
    im = Image.fromarray(img).convert("RGBA")
    sombra = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(sombra)
    cx, cy = b.CX + 6, SUELO - 3
    for k, (rx, ry, al) in enumerate(((70, 9, 60), (56, 7, 70), (40, 5, 80))):
        d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=(0, 0, 0, al))
    sombra = sombra.filter(ImageFilter.GaussianBlur(1.2))
    im.alpha_composite(sombra)
    return im.convert("RGB")


def agrupar(img, K):
    q = Image.fromarray(img).quantize(colors=K, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    return np.asarray(q.convert("RGB"))


def main():
    OUT.mkdir(exist_ok=True)
    b.H = H
    b.SUELO = SUELO
    R = b.cargar()
    ticks = b.guion_bucle1(R)
    capas = b.dibujar_ticks_bucle1(ticks, R)                     # RGBA 380x259, transparente
    bg = agrupar(np.asarray(con_sombra(fondo_rgb())), K_FONDO)
    bg_im = Image.fromarray(bg).convert("RGBA")
    exact = b.colores_sprite(R) | {int(r) << 16 | int(g) << 8 | int(bb) for r, g, bb in np.unique(bg.reshape(-1, 3), axis=0)}
    frames = []
    for lz in capas:
        c = bg_im.copy(); c.alpha_composite(lz); frames.append(c.convert("RGB"))
    n = max(len(np.unique(np.asarray(fr).reshape(-1, 3), axis=0)) for fr in frames)
    print(f"{len(frames)} pasos de {b.TICK} ms = {len(frames) * b.TICK / 1000:.2f} s; máximo de colores en un fotograma: {n}")
    ag = b.gif_local(frames, OUT / "bucle1_stage_1x.gif", b.TICK)
    b.gif_local([fr.resize((W * 2, H * 2), Image.NEAREST) for fr in frames], OUT / "bucle1_stage_2x.gif", b.TICK)
    print("fotogramas que han necesitado agrupar colores (más de 256):", ag)
    bg_im.convert("RGB").save(OUT / "fondo_stage_1x.png")
    bg_im.convert("RGB").resize((W * 2, H * 2), Image.NEAREST).save(OUT / "fondo_stage_2x.png")
    bi = b.binarizar(capas)
    b.gif_transparente(bi, OUT / "animacion_sola_1x.gif", b.TICK)
    b.gif_transparente([c.resize((W * 2, H * 2), Image.NEAREST) for c in bi], OUT / "animacion_sola_2x.gif", b.TICK)
    for r in sorted(OUT.iterdir()):
        if r.suffix in (".gif", ".png"):
            print(f"  {r.name}: {Image.open(r).size}, {r.stat().st_size / 1024:.0f} KB")
    # fidelidad del sprite: en los pasos sin efectos, el GIF debe ser idéntico a la composición exacta
    g = Image.open(OUT / "bucle1_stage_1x.gif"); exp = []
    for i in range(g.n_frames):
        g.seek(i); exp += [np.asarray(g.convert("RGB")).astype(int)] * round(g.info["duration"] / b.TICK)
    difs = []
    for t, lz in enumerate(capas):
        c = bg_im.copy(); c.alpha_composite(lz)
        d = int((np.abs(np.asarray(c.convert("RGB")).astype(int) - exp[t]).sum(-1) > 0).sum())
        if d: difs.append((t, d))
    print("pasos cuyo GIF difiere de la composición con el escenario agrupado (tick, píxeles):", difs[:12], "... total", len(difs))
    b.hoja_contacto(frames, [0, 8, 32, 34, 36, 40, 43, 46, 49, 52, 55, 58], OUT / "momentos.png", z=1, cols=4)
    return capas


if __name__ == "__main__":
    main()
