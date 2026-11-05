"""Entrega final de Drache a 2x dentro del marco de siempre (tierra y oro): 504x504, 126x126 y piezas por separado."""
import numpy as np
from PIL import Image
import bucles as b
import marco_126 as mf
import opciones_tamano as o

OUT = o.HERE / "salida_marco_2x"
S = 2.0


def main():
    OUT.mkdir(exist_ok=True)
    img, _ = mf.build(k=40)
    f4 = Image.fromarray(img, "RGBA").crop((1, 1, 127, 127)).resize((504, 504), Image.NEAREST)
    bg, capas = o.nativo()
    fondo, caps = o.escena(bg, capas, S)
    dentro, sobre = o.mascaras()
    _, spr = o.escena(bg, o.NATIVO_SPRITE, S)
    todo = dentro | sobre
    # ¿hay algo (aparte de Drache) en la franja de arriba? cuenta de píxeles opacos de la capa en la franja, por paso
    franja = [int((np.asarray(c)[..., 3][sobre] > 0).sum()) for c in spr]
    print("píxeles de la capa en la franja de arriba (min/máx):", min(franja), max(franja))
    # píxeles de la capa que quedan fuera de lo permitido (y se recortan)
    base = Image.new("RGBA", (504, 504), (0, 0, 0, 255)); base.paste(fondo, (o.WX, o.WX)); base.alpha_composite(f4)
    base.convert("RGB").save(OUT / "marco_y_fondo_x4.png")
    frames = [o.componer(f4, fondo, c, dentro, sobre, sp) for c, sp in zip(caps, spr)]
    n = max(len(np.unique(np.asarray(fr).reshape(-1, 3), axis=0)) for fr in frames)
    print(f"{len(frames)} pasos de {b.TICK} ms = {len(frames) * b.TICK / 1000:.2f} s; máximo de colores por fotograma: {n}")
    ag = b.gif_local(frames, OUT / "drache_2x_marco_x4.gif", b.TICK)
    ag2 = b.gif_local([f.resize((126, 126), Image.BOX) for f in frames], OUT / "drache_2x_marco_126.gif", b.TICK)
    print("fotogramas agrupados a 256 colores: 504 px ->", ag, "| 126 px ->", ag2)
    mezcla = [np.where(dentro[..., None], np.asarray(c), np.where(sobre[..., None], np.asarray(sp), 0)).astype(np.uint8) for c, sp in zip(caps, spr)]
    solas = b.binarizar([Image.fromarray(m, "RGBA") for m in mezcla])
    b.gif_transparente(solas, OUT / "animacion_sola_x4.gif", b.TICK)
    # verificación de la recomposición
    g = Image.open(OUT / "drache_2x_marco_x4.gif"); exp = []
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
    print("recomposición vs GIF completo, pasos con diferencia (tick, píxeles):", difs)
    ts = [0, 8, 20, 31, 32, 33, 34, 35, 36, 43, 52, 58]
    hoja = Image.new("RGB", (4 * 254, 3 * 254), (30, 30, 30))
    for i, t in enumerate(ts):
        hoja.paste(frames[t].resize((252, 252), Image.LANCZOS), ((i % 4) * 254, (i // 4) * 254))
    hoja.save(OUT / "momentos_2x.png")
    for r in sorted(OUT.iterdir()):
        print(f"  {r.name}: {Image.open(r).size}, {r.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
