"""Animación final de Drache (bucle 1, 1x) dentro del marco de siempre en tierra y oro: 504x504 (126 x4) y 126x126, más las piezas por separado."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).parent
import bucles as b
import entrega_stage as e
import marco_126 as mf

OUT = HERE / "salida_marco"
Z, VW, WX = 4, 320, 92          # zoom, lado de la ventana (px de 504) y su esquina


def main():
    OUT.mkdir(exist_ok=True)
    b.W, b.H, b.CX, b.SUELO = VW, VW, 160, 306
    e.X0, e.W, e.H, e.SUELO = 1515, VW, VW, 306
    R = b.cargar()
    capas = b.dibujar_ticks_bucle1(b.guion_bucle1(R), R)
    bg = Image.fromarray(e.agrupar(np.asarray(e.con_sombra(e.fondo_rgb())), e.K_FONDO)).convert("RGBA")
    img, win = mf.build(k=int(sys.argv[1]) if len(sys.argv) > 1 else 48)
    assert win == (24, 24, 103, 103)
    f4 = Image.fromarray(img, "RGBA").crop((1, 1, 127, 127)).resize((126 * Z, 126 * Z), Image.NEAREST)
    print("colores del marco:", len(np.unique(np.asarray(f4).reshape(-1, 4), axis=0)), "| del fondo:", len(np.unique(np.asarray(bg).reshape(-1, 4), axis=0)))
    base = Image.new("RGBA", f4.size, (0, 0, 0, 255)); base.paste(bg, (WX, WX)); base.alpha_composite(f4)   # marco + fondo
    base.convert("RGB").save(OUT / "marco_y_fondo_x4.png")
    frames = []
    for lz in capas:
        c = base.copy(); c.alpha_composite(lz, (WX, WX)); frames.append(c.convert("RGB"))
    n = max(len(np.unique(np.asarray(fr).reshape(-1, 3), axis=0)) for fr in frames)
    print(f"{len(frames)} pasos de {b.TICK} ms = {len(frames) * b.TICK / 1000:.2f} s; máximo de colores por fotograma: {n}")
    ag = b.gif_local(frames, OUT / "drache_marco_x4.gif", b.TICK)
    print("fotogramas con más de 256 colores (agrupados):", ag)
    f126 = [fr.resize((126, 126), Image.BOX) for fr in frames]
    ag2 = b.gif_local(f126, OUT / "drache_marco_126.gif", b.TICK)
    print("126 px: fotogramas agrupados a 256:", ag2)
    # animación sola: capa transparente 504x504 (solo dentro de la ventana)
    bi = b.binarizar(capas)
    solas = []
    for lz in bi:
        c = Image.new("RGBA", f4.size, (0, 0, 0, 0)); c.alpha_composite(lz, (WX, WX)); solas.append(c)
    b.gif_transparente(solas, OUT / "animacion_sola_x4.gif", b.TICK)
    # verificación: marco_y_fondo + animación sola frente al GIF completo
    g = Image.open(OUT / "drache_marco_x4.gif"); exp = []
    for i in range(g.n_frames):
        g.seek(i); exp += [np.asarray(g.convert("RGB")).astype(int)] * round(g.info["duration"] / b.TICK)
    h = Image.open(OUT / "animacion_sola_x4.gif"); rec = []
    for i in range(h.n_frames):
        h.seek(i); rec += [h.convert("RGBA").copy()] * round(h.info["duration"] / b.TICK)
    difs = []
    for t in range(len(frames)):
        c = base.copy(); c.alpha_composite(rec[t])
        d = int((np.abs(np.asarray(c.convert("RGB")).astype(int) - exp[t]).sum(-1) > 0).sum())
        if d: difs.append((t, d))
    print("recomposición (marco_y_fondo + animación sola) vs GIF completo, pasos con diferencia (tick, píxeles):", difs)
    b.hoja_contacto([f.resize((252, 252), Image.NEAREST) if False else f for f in frames], [0, 8, 32, 34, 36, 43, 52, 58], OUT / "momentos_x4.png", z=1, cols=4)
    for r in sorted(OUT.iterdir()):
        print(f"  {r.name}: {Image.open(r).size}, {r.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
