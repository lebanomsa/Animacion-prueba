"""Entrega final de Special Bersek: contraataque con salto alto, giro, cámara que sigue el salto, pilar de fuego, salto corto hacia atrás para cerrar el bucle.
Marco de brasa, fondo = Stage Fukai (el de Drache). Todo en la rejilla nativa de 126 px; la versión de 504 px es el mismo fotograma ampliado x4 sin suavizar.
Salida en bersek/entrega/: bersek_126.gif, bersek_x4.gif y separado/ (marco_y_fondo_*.gif, animacion_sola_x4.png (APNG), animacion_sola_*.gif)."""
from pathlib import Path
import numpy as np
from PIL import Image
import animacion_pilar as ap
import marco_bersek as mb

HERE = Path(__file__).parent
OUT = HERE / "entrega"; SEP = OUT / "separado"
TICK = ap.TICK
VARIANTE = "salto_atras"


def a4(im): return im.resize((504, 504), Image.NEAREST)


def leer(ruta, rgba=False):
    g = Image.open(ruta); out = []
    for i in range(g.n_frames):
        g.seek(i); out += [np.asarray(g.convert("RGBA" if rgba else "RGB")).astype(int)] * round(g.info["duration"] / TICK)
    return out


def gif_transparente(capas, ruta):
    arrs = [np.asarray(c) for c in capas]
    k = lambda a: a[..., 0].astype(np.uint32) << 16 | a[..., 1].astype(np.uint32) << 8 | a[..., 2]
    cols = np.unique(np.concatenate([k(a)[a[..., 3] > 0] for a in arrs]))
    if len(cols) > 255: return len(cols)
    flat = np.zeros(768, np.uint8); flat[0:3] = (255, 0, 255)
    flat[3:3 + len(cols) * 3:3], flat[4:4 + len(cols) * 3:3], flat[5:5 + len(cols) * 3:3] = cols >> 16, cols >> 8 & 255, cols & 255
    ps = []
    for a in arrs:
        idx = (np.searchsorted(cols, k(a)) + 1).astype(np.uint8); idx[a[..., 3] == 0] = 0
        p = Image.fromarray(idx, "P"); p.putpalette(flat.tolist()); ps.append(p)
    ps[0].save(ruta, save_all=True, append_images=ps[1:], duration=TICK, loop=0, transparency=0, disposal=2, optimize=False)
    return len(cols)


def main():
    OUT.mkdir(exist_ok=True); SEP.mkdir(exist_ok=True)
    piezas = []
    fin = ap.render(VARIANTE, marco_fn=lambda t: mb.frame_126("brasa", t), piezas=piezas)
    n = len(fin)
    cols = max(len(np.unique(np.asarray(f).reshape(-1, 3), axis=0)) for f in fin)
    print(f"{n} pasos de {TICK} ms = {n * TICK / 1000:.2f} s; máximo de colores por fotograma: {cols}")
    ag1 = ap.bb.gif_local(fin, OUT / "bersek_126.gif", TICK)
    ag4 = ap.bb.gif_local([a4(f) for f in fin], OUT / "bersek_x4.gif", TICK)
    print("agrupados a 256: 126 ->", ag1, "| x4 ->", ag4)
    inf = [p["inf"].convert("RGB") for p in piezas]; sup = [p["sup"] for p in piezas]
    ap.bb.gif_local(inf, SEP / "marco_y_fondo_126.gif", TICK)
    ap.bb.gif_local([a4(f) for f in inf], SEP / "marco_y_fondo_x4.gif", TICK)
    s4 = [a4(s) for s in sup]
    s4[0].save(SEP / "animacion_sola_x4.png", save_all=True, append_images=s4[1:], duration=TICK, loop=0, disposal=1)
    nc = gif_transparente(sup, SEP / "animacion_sola_126.gif")
    nc4 = gif_transparente(s4, SEP / "animacion_sola_x4.gif")
    print("colores de la capa de arriba (GIF):", nc, nc4, "(si pasa de 255 no se genera el GIF y se entrega solo el APNG)")
    # verificación
    E = [np.asarray(f).astype(int) for f in fin]
    d = lambda x, y: int((np.abs(x - y).sum(-1) > 0).sum())
    g126, g4 = leer(OUT / "bersek_126.gif"), leer(OUT / "bersek_x4.gif")
    print("bersek_126.gif vs exacto, pasos con diferencia:", [t for t in range(n) if d(E[t], g126[t])][:10])
    print("bersek_x4.gif vs exacto x4, pasos con diferencia:", [t for t in range(n) if d(np.asarray(a4(fin[t])).astype(int), g4[t])][:10])
    base = leer(SEP / "marco_y_fondo_x4.gif", rgba=True)
    ap_ = Image.open(SEP / "animacion_sola_x4.png"); capas = []
    for i in range(ap_.n_frames):
        ap_.seek(i); capas.append(ap_.convert("RGBA").copy())
    dif = []
    for t in range(n):
        c = Image.fromarray(base[t].astype(np.uint8), "RGBA"); c.alpha_composite(capas[t])
        x = d(np.asarray(c.convert("RGB")).astype(int), np.asarray(a4(fin[t])).astype(int))
        if x: dif.append((t, x))
    print("marco_y_fondo + animacion_sola (APNG) vs completo x4, pasos con diferencia:", dif[:10], "total", len(dif))
    if nc4 <= 255:
        gs = leer(SEP / "animacion_sola_x4.gif", rgba=True); dif2 = []
        for t in range(n):
            c = Image.fromarray(base[t].astype(np.uint8), "RGBA"); c.alpha_composite(Image.fromarray(gs[t].astype(np.uint8), "RGBA"))
            x = d(np.asarray(c.convert("RGB")).astype(int), np.asarray(a4(fin[t])).astype(int))
            if x: dif2.append((t, x))
        print("marco_y_fondo + animacion_sola (GIF) vs completo x4, pasos con diferencia:", dif2[:10], "total", len(dif2))
    idx = [0, 5, 7, 10, 14, 18, 21, 22, 26, 33, 36, 39, 42]
    s = Image.new("RGB", (5 * 256, 3 * 256), (20, 20, 20))
    for j, i in enumerate(idx): s.paste(a4(fin[i]).resize((252, 252), Image.LANCZOS), ((j % 5) * 256, (j // 5) * 256))
    s.save(OUT / "momentos.png")
    for r in sorted(list(OUT.iterdir()) + list(SEP.iterdir())):
        if r.is_file(): print(f"  {r.relative_to(OUT)}: {Image.open(r).size}, {r.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
