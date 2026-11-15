"""Entrega final de Aswang: bucle de la lengua fuera a 2x (secuencia 2 del ataque especial) con dos murciélagos en órbita (cortados por el borde de la ventana),
fondo del salón de Percier y marco 'sangre y oro'. Todo en la rejilla nativa de 126 px; la versión de 504 px es el mismo fotograma ampliado x4 sin suavizar.
Salida en aswang/entrega/: aswang_126.gif, aswang_x4.gif y separado/ (marco_y_fondo_*.gif y animacion_sola_*.gif)."""
import math
from pathlib import Path
import numpy as np
from PIL import Image
import bucles_aswang as ba
import bucle_lengua_fondos as bf
import marco_aswang as mk

HERE = Path(__file__).parent
OUT = HERE / "entrega"; SEP = OUT / "separado"
TICK = ba.TICK
OPCION = "sangre"


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
    assert len(cols) <= 255, len(cols)
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
    r = ba.cargar()
    seq2 = [bf.x2(f) for f in r.seq2]; seq1 = [bf.x2(f) for f in r.seq1]
    bg = bf.recorte("percier")
    ventana = np.zeros((126, 126), bool); ventana[23:103, 23:103] = True
    head = (bf.CX + 2 * bf.Z, bf.SUELO_G - 31 * bf.Z)

    def capa(bs):
        lz = Image.new("RGBA", (126, 126), (0, 0, 0, 0))
        for im, x, y in bs: ba.pegar(lz, im, x - im.width / 2, y - im.height / 2)
        a = np.array(lz); a[~ventana] = 0
        return Image.fromarray(a, "RGBA")

    fin, inf, sup = [], [], []
    for t in range(8):
        c = Image.new("RGBA", (126, 126), (0, 0, 0, 255)); c.paste(bg, (23, 23)); c.alpha_composite(mk.frame_126(OPCION, t))
        inf.append(c.copy())
        det, del_ = [], []
        for b in (0, 1):
            ang = math.radians(bf.GRADOS * t + 180 * b)
            x, y, prof = head[0] + bf.RX * math.cos(ang), head[1] + bf.RY * math.sin(ang), math.sin(ang)
            (del_ if prof > 0 else det).append((seq1[(t + 4 * b) % 8], x, y))
        L = Image.new("RGBA", (126, 126), (0, 0, 0, 0))
        L.alpha_composite(capa(det))
        cx, by = ba.ha.pies(seq2[t]); ba.pegar(L, seq2[t], bf.CX - cx, bf.SUELO_G - by)
        L.alpha_composite(capa(del_))
        sup.append(L)
        c.alpha_composite(L); fin.append(c.convert("RGB"))
    n = len(fin)
    cols = max(len(np.unique(np.asarray(f).reshape(-1, 3), axis=0)) for f in fin)
    print(f"{n} pasos de {TICK} ms = {n * TICK / 1000:.2f} s; máximo de colores por fotograma: {cols}")
    ag1 = ba.gif_local(fin, OUT / "aswang_126.gif", TICK)
    ag4 = ba.gif_local([a4(f) for f in fin], OUT / "aswang_x4.gif", TICK)
    print("agrupados a 256: 126 ->", ag1, "| x4 ->", ag4)
    ba.gif_local([f.convert("RGB") for f in inf], SEP / "marco_y_fondo_126.gif", TICK)
    ba.gif_local([a4(f.convert("RGB")) for f in inf], SEP / "marco_y_fondo_x4.gif", TICK)
    nc = gif_transparente(sup, SEP / "animacion_sola_126.gif"); nc4 = gif_transparente([a4(s) for s in sup], SEP / "animacion_sola_x4.gif")
    print("colores de la capa de arriba:", nc, nc4)
    # verificación
    E = [np.asarray(f).astype(int) for f in fin]
    d = lambda x, y: int((np.abs(x - y).sum(-1) > 0).sum())
    g126, g4 = leer(OUT / "aswang_126.gif"), leer(OUT / "aswang_x4.gif")
    print("aswang_126.gif vs exacto, pasos con diferencia:", [t for t in range(n) if d(E[t], g126[t])])
    print("aswang_x4.gif vs exacto x4, pasos con diferencia:", [t for t in range(n) if d(np.asarray(a4(fin[t])).astype(int), g4[t])])
    base = leer(SEP / "marco_y_fondo_x4.gif", rgba=True); gs = leer(SEP / "animacion_sola_x4.gif", rgba=True); dif = []
    for t in range(n):
        c = Image.fromarray(base[t].astype(np.uint8), "RGBA"); c.alpha_composite(Image.fromarray(gs[t].astype(np.uint8), "RGBA"))
        x = d(np.asarray(c.convert("RGB")).astype(int), np.asarray(a4(fin[t])).astype(int))
        if x: dif.append((t, x))
    print("marco_y_fondo + animacion_sola (GIF) vs completo x4, pasos con diferencia:", dif)
    g = Image.open(OUT / "aswang_126.gif"); d0 = [d(E[7], E[0])]
    print("último vs primero:", d0[0], "px de", 126 * 126)
    s = Image.new("RGB", (4 * 254, 2 * 254), (20, 20, 20))
    for j in range(8): s.paste(a4(fin[j]).resize((252, 252), Image.LANCZOS), ((j % 4) * 254, (j // 4) * 254))
    s.save(OUT / "momentos.png")
    for rr in sorted(list(OUT.iterdir()) + list(SEP.iterdir())):
        if rr.is_file(): print(f"  {rr.relative_to(OUT)}: {Image.open(rr).size}, {rr.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
