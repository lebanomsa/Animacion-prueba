"""Entrega final de Nova: bucle de 42 pasos (rayo Timor + cápsula de Vita) con el marco de acero y óxido y el fondo 'fondo.png'.
Todo está en la rejilla nativa de 126 px (cada píxel de Nova, del fondo y del marco es 1 px); la versión de 504 px es el mismo fotograma ampliado x4 sin suavizar.
Salida en nova/entrega/:
  nova_126.gif, nova_x4.gif                    animación completa
  separado/marco_y_fondo_x4.gif (y _126)       capa de abajo: fondo + marco (el marco anima sus luces)
  separado/animacion_sola_x4.png (APNG)        capa de arriba con alfa exacto (cristal de la cápsula translúcido)
  separado/animacion_sola_x4.gif (y _126)      misma capa en GIF (la transparencia parcial del cristal no cabe en GIF: se descartan los píxeles con alfa < 50 %)
"""
from pathlib import Path
import numpy as np
from PIL import Image
import maqueta_marco as m
import marco_nova as mn
import bucles_nova as b

HERE = Path(__file__).parent
OUT = HERE / "entrega"
SEP = OUT / "separado"
MODO = "continuo42"
TICK = b.TICK


def a4(im):
    return im.resize((504, 504), Image.NEAREST)


def binarizar(im):
    a = np.array(im); a[..., 3] = np.where(a[..., 3] >= 128, 255, 0); a[a[..., 3] == 0, :3] = 0
    return Image.fromarray(a, "RGBA")


def gif_transparente(capas, ruta, dur):
    arrs = [np.asarray(c) for c in capas]
    k = lambda a: a[..., 0].astype(np.uint32) << 16 | a[..., 1].astype(np.uint32) << 8 | a[..., 2]
    cols = np.unique(np.concatenate([k(a)[a[..., 3] > 0] for a in arrs]))
    assert len(cols) <= 255, len(cols)
    flat = np.zeros(768, np.uint8); flat[0:3] = (255, 0, 255)
    flat[3:3 + len(cols) * 3:3], flat[4:4 + len(cols) * 3:3], flat[5:5 + len(cols) * 3:3] = cols >> 16, cols >> 8 & 255, cols & 255
    ps = []
    for a in arrs:
        idx = (np.searchsorted(cols, k(a)) + 1).astype(np.uint8); idx[a[..., 3] == 0] = 0
        p = Image.fromarray(idx, "P"); p.putpalette(flat.tolist()); ps.append(p)
    ps[0].save(ruta, save_all=True, append_images=ps[1:], duration=dur, loop=0, transparency=0, disposal=2, optimize=False)


def leer_gif(ruta, rgba=False):
    g = Image.open(ruta); out = []
    for i in range(g.n_frames):
        g.seek(i); out += [np.asarray(g.convert("RGBA" if rgba else "RGB")).astype(int)] * round(g.info["duration"] / TICK)
    return out


def main():
    OUT.mkdir(exist_ok=True); SEP.mkdir(exist_ok=True)
    mn.modo(MODO)
    fondo = Image.open(HERE / "fuentes/fondo.png").convert("RGBA").crop((68, 45, 148, 125))
    piezas = []
    m.main(rayo_fuera=True, fondo=fondo, dy=-30, marco_fn=lambda t: mn.frame_126("acero", t), modo=MODO, piezas=piezas)
    n = len(piezas)
    fin126 = [p["final"] for p in piezas]
    cols = max(len(np.unique(np.asarray(f).reshape(-1, 3), axis=0)) for f in fin126)
    print(f"{n} pasos de {TICK} ms = {n * TICK / 1000:.2f} s; máximo de colores por fotograma: {cols}")
    ag1 = b.gif_local(fin126, OUT / "nova_126.gif", TICK)
    ag4 = b.gif_local([a4(f) for f in fin126], OUT / "nova_x4.gif", TICK)
    print("fotogramas agrupados a 256 colores: 126 ->", ag1, "| x4 ->", ag4)
    fm = [p["fondo_marco"].convert("RGB") for p in piezas]
    b.gif_local(fm, SEP / "marco_y_fondo_126.gif", TICK)
    b.gif_local([a4(f) for f in fm], SEP / "marco_y_fondo_x4.gif", TICK)
    sup = [p["sup"] for p in piezas]
    sup4 = [a4(s) for s in sup]
    sup4[0].save(SEP / "animacion_sola_x4.png", save_all=True, append_images=sup4[1:], duration=TICK, loop=0, disposal=1)
    sb = [binarizar(s) for s in sup]
    gif_transparente(sb, SEP / "animacion_sola_126.gif", TICK)
    gif_transparente([a4(s) for s in sb], SEP / "animacion_sola_x4.gif", TICK)
    # ---------------------------------------------------------------- verificación
    E = [np.asarray(f).astype(int) for f in fin126]                      # fotogramas exactos (126)
    d = lambda x, y: int((np.abs(x - y).sum(-1) > 0).sum())
    g126 = leer_gif(OUT / "nova_126.gif"); g4 = leer_gif(OUT / "nova_x4.gif")
    print("nova_126.gif vs exacto, pasos con diferencia:", [(t, d(E[t], g126[t])) for t in range(n) if d(E[t], g126[t])][:10])
    print("nova_x4.gif vs exacto x4, pasos con diferencia:", [(t, d(np.asarray(a4(fin126[t])).astype(int), g4[t])) for t in range(n) if d(np.asarray(a4(fin126[t])).astype(int), g4[t])][:10])
    # recomposición exacta: marco_y_fondo (gif) + animacion_sola (apng)
    base = leer_gif(SEP / "marco_y_fondo_x4.gif", rgba=True)
    ap = Image.open(SEP / "animacion_sola_x4.png"); capas = []
    for i in range(ap.n_frames):
        ap.seek(i); capas.append(ap.convert("RGBA").copy())
    dif = []
    for t in range(n):
        c = Image.fromarray(base[t].astype(np.uint8), "RGBA"); c.alpha_composite(capas[t])
        x = d(np.asarray(c.convert("RGB")).astype(int), np.asarray(a4(fin126[t])).astype(int))
        if x: dif.append((t, x))
    print("marco_y_fondo + animacion_sola (APNG) vs completo x4, pasos con diferencia (paso, píxeles):", dif[:10], "total", len(dif))
    # con el GIF de la capa de arriba (cristal sin translúcido)
    gs = leer_gif(SEP / "animacion_sola_x4.gif", rgba=True)
    dif2 = []
    for t in range(n):
        c = Image.fromarray(base[t].astype(np.uint8), "RGBA"); c.alpha_composite(Image.fromarray(gs[t].astype(np.uint8), "RGBA"))
        x = d(np.asarray(c.convert("RGB")).astype(int), np.asarray(a4(fin126[t])).astype(int))
        if x: dif2.append((t, x))
    print("marco_y_fondo + animacion_sola (GIF) vs completo x4, pasos con diferencia: %d de %d, máx %d píxeles" % (len(dif2), n, max([x for _, x in dif2] or [0])))
    idx = [0, 4, 8, 12, 16, 19, 22, 26, 30, 33, 36, 41]
    s = Image.new("RGB", (4 * 256, 3 * 256), (20, 20, 20))
    for j, i in enumerate(idx): s.paste(a4(fin126[i]).resize((252, 252), Image.LANCZOS), ((j % 4) * 256, (j // 4) * 256))
    s.save(OUT / "momentos.png")
    for r in sorted(list(OUT.iterdir()) + list(SEP.iterdir())):
        if r.is_file(): print(f"  {r.relative_to(OUT)}: {Image.open(r).size}, {r.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
