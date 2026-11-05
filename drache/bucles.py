"""Bucles de victoria de Drache Goldenes (hoja ripeada por SamuelGR/Gestalt) a tamaño natural, sin reducir nada, sin marco.

  bucle 1  reposo (2 vueltas) -> destello de bola de fuego que tapa el cambio de pose -> victoria completa (con polvo y lluvia de pepitas) -> reposo
  bucle 3  saludo coqueto: vaivén entre los fotogramas 1 y 2 de la victoria, con pepitas de oro que suben despacio y destellos de estrella

Reloj de 50 ms (20 fps). Lienzo de 380x330 píxeles; los sprites se alinean por las botas. Salida en drache/salida/:
  *_fondo_1x.gif / *_fondo_2x.gif       sobre fondo oscuro liso (los efectos conservan su transparencia suave)
  *_transparente_1x.gif / _2x.gif       sobre transparente (los efectos se quedan con borde duro, porque el GIF no admite transparencia suave)
"""
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import hoja

HERE = Path(__file__).parent
OUT = HERE / "salida"
W, H = 380, 330
CX, SUELO = 175, 300
TICK = 50
FONDO = (24, 26, 40)
ORO = [(248, 184, 0), (255, 224, 96), (255, 248, 200), (255, 255, 255)]


# ---------------------------------------------------------------- recursos
def cargar():
    idle, _ = hoja.fotogramas("idle")
    vic, _ = hoja.fotogramas("victoria")
    polvo, _ = hoja.efecto("polvo_anillo", minw=3)
    pep, _ = hoja.efecto("pepitas", minw=3)
    fuego, _ = hoja.efecto("fuego", minw=3)
    return dict(idle=idle, vic=vic, polvo=polvo, pep=pep[1:], fuego=fuego)       # pep[0] (la pepita grande) se descarta: quedan 24 de giro


def pegar_sprite(lienzo, img, anc=None, dx=0, dy=0):
    ax, ay = anc if anc else hoja.ancla(img)
    lienzo.alpha_composite(img, (int(round(CX - ax + dx)), int(round(SUELO - ay + dy))))


def pegar_centrado(lienzo, img, cx, y_base):
    """Pone `img` con su centro horizontal en cx y su borde inferior en y_base."""
    x, y = int(round(cx - img.width / 2)), int(round(y_base - img.height))
    sx, sy = max(-x, 0), max(-y, 0)
    if sx < img.width and sy < img.height and x + img.width > 0 and y + img.height > 0 and x < W and y < H:
        rec = img.crop((sx, sy, min(img.width, W - x), min(img.height, H - y)))
        lienzo.alpha_composite(rec, (x + sx, y + sy))


def pegar_recortado(lienzo, img, x, y, alfa=1.0):
    """Pega `img` con su esquina en (x, y); lo que se sale del lienzo se recorta (sale por el borde sin desaparecer de golpe)."""
    x, y = int(round(x)), int(round(y))
    sx, sy = max(-x, 0), max(-y, 0)
    ex, ey = min(img.width, W - x), min(img.height, H - y)
    if ex <= sx or ey <= sy:
        return
    rec = img.crop((sx, sy, ex, ey))
    if alfa < 1.0:
        a = np.array(rec); a[..., 3] = (a[..., 3] * alfa).astype(np.uint8); rec = Image.fromarray(a, "RGBA")
    lienzo.alpha_composite(rec, (x + sx, y + sy))


def estrella(lienzo, x, y, r):
    """Destello de 4 puntas de radio r (0..3) con el oro de la hoja."""
    d = ImageDraw.Draw(lienzo)
    if r <= 0:
        d.point((x, y), fill=ORO[3] + (255,)); return
    for k in range(1, r + 1):
        c = ORO[0] if k == r else ORO[1] if k > r // 2 else ORO[2]
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            d.point((x + dx, y + dy), fill=c + (255,))
    d.point((x, y), fill=ORO[3] + (255,))
    if r >= 2:
        for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            d.point((x + dx, y + dy), fill=ORO[2] + (255,))


# ---------------------------------------------------------------- bucle 1
def guion_bucle1(R):
    """Lista de ticks: cada uno es una función que dibuja el lienzo RGBA (transparente)."""
    idle, vic, polvo, pep, fuego = R["idle"], R["vic"], R["polvo"], R["pep"], R["fuego"]
    ancl_i = [hoja.ancla(f) for f in idle]; ancl_v = [hoja.ancla(f) for f in vic]
    ticks = []                                                                       # (sprite, ancla, extras...)
    for k in range(16):                                                              # 2 vueltas de reposo, empezando donde acaba la victoria
        i = (4 + k) % 8
        for _ in range(2):
            ticks.append(dict(spr=idle[i], anc=ancl_i[i], fase="idle"))
    ticks.append(dict(spr=idle[4], anc=ancl_i[4], fase="flash", bola=1, alfa=1.0))   # destello: la bola de fuego tapa el cambio de pose
    ticks.append(dict(spr=vic[0], anc=ancl_v[0], fase="flash", bola=0, alfa=1.0))
    ticks.append(dict(spr=vic[0], anc=ancl_v[0], fase="flash", bola=1, alfa=0.5))    # y se disipa
    ticks.append(dict(spr=vic[0], anc=ancl_v[0], fase="flash", bola=0, alfa=0.22))
    dur = [3, 3, 2, 2, 2, 2, 3, 8]
    for f, d in enumerate(dur):
        for _ in range(d):
            ticks.append(dict(spr=vic[f], anc=ancl_v[f], fase="vic", f=f))
    # polvo en el suelo desde la caída (fotograma 3)
    seq_polvo = [1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12]
    t3 = next(i for i, t in enumerate(ticks) if t.get("f") == 2)
    for j, p in enumerate(seq_polvo):
        if t3 + j < len(ticks):
            ticks[t3 + j]["polvo"] = p
    # pepitas lanzadas desde las dos manos al abrir los brazos (fotograma 7); siguen su vuelo al empezar la vuelta siguiente (bucle sin salto)
    t7 = next(i for i, t in enumerate(ticks) if t.get("f") == 6)
    n = len(ticks)
    mano_d, mano_i = (CX + 88, SUELO - 118), (CX - 56, SUELO - 100)
    lanz = [(*mano_d, 4.2, -12.5, 0), (*mano_d, 6.6, -10.5, 9), (*mano_d, 2.4, -14.0, 17),
            (*mano_i, -3.4, -12.0, 5), (*mano_i, -6.0, -10.0, 13), (*mano_i, -1.6, -13.5, 21)]
    g = 1.25
    retraso = [0, 2, 4, 1, 3, 5]
    for k, (x0, y0, vx, vy, ph) in enumerate(lanz):
        for t in range(60):
            x, y = x0 + vx * t, y0 + vy * t + 0.5 * g * t * t
            if y > H + 30 or not (-40 < x < W + 40):
                break
            ticks[(t7 + retraso[k] + t) % n].setdefault("pepitas", []).append((x, y, (2 * t + ph) % 24))
    return ticks


def dibujar_ticks_bucle1(ticks, R):
    polvo, pep, fuego = R["polvo"], R["pep"], R["fuego"]
    frames = []
    for t in ticks:
        lz = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if "polvo" in t:
            pegar_centrado(lz, polvo[t["polvo"]], CX + 12, SUELO + 4)
        pegar_sprite(lz, t["spr"], t["anc"])
        for (x, y, k) in t.get("pepitas", []):
            p = pep[k]
            pegar_recortado(lz, p, x - p.width / 2, y - p.height / 2)
        if t["fase"] == "flash":
            b = fuego[t["bola"]]
            pegar_recortado(lz, b, CX + 6 - b.width / 2, SUELO + 6 - b.height, t.get("alfa", 1.0))
        frames.append(lz)
    return frames


# ---------------------------------------------------------------- bucle 3
def bucle3(R):
    vic, pep = R["vic"], R["pep"]
    f1, f2 = vic[0], vic[1]
    a1, a2 = hoja.ancla(f1), hoja.ancla(f2)
    N = 24
    frames = []
    for t in range(N):
        lz = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        usar2 = (t // 4) % 2 == 1
        pegar_sprite(lz, f2 if usar2 else f1, a2 if usar2 else a1)
        # pepitas que suben despacio, escalonadas (periodo = 24 ticks, así que el bucle cierra sin salto)
        for n in range(4):
            ph = n * 6
            u = ((t + ph) % N) / float(N)
            x = CX + 78 + 24 * u + 12 * math.sin(2 * math.pi * (1.5 * u + n * 0.27))
            y = SUELO - 150 - 250 * u
            p = pep[(2 * t + 5 * n) % 24]
            pegar_recortado(lz, p, x - p.width / 2, y - p.height / 2)
        # destellos de estrella en los cuernos y las joyas, desfasados
        spots = [(CX - 6, SUELO - 192, 0), (CX + 30, SUELO - 186, 8), (CX + 4, SUELO - 108, 16), (CX - 34, SUELO - 124, 4)]
        for (x, y, ph) in spots:
            u = (t - ph) % N
            if u < 8:
                estrella(lz, x, y, [0, 2, 4, 3, 4, 3, 2, 0][u])
        frames.append(lz)
    return frames


# ---------------------------------------------------------------- salida
def componer_fondo(capas):
    out = []
    for lz in capas:
        b = Image.new("RGBA", lz.size, FONDO + (255,)); b.alpha_composite(lz); out.append(b.convert("RGB"))
    return out


def binarizar(capas):
    out = []
    for lz in capas:
        a = np.array(lz); a[..., 3] = np.where(a[..., 3] >= 128, 255, 0); a[a[..., 3] == 0, :3] = 0
        out.append(Image.fromarray(a, "RGBA"))
    return out


def exactos(capas):
    cols = set()
    for lz in capas:
        pass
    return cols


def reducir(frames_rgb, exact, margen=1):
    """Si hay más de 256 colores, agrupa solo los colores nuevos (mezclas de efectos); los del sprite y el fondo se conservan."""
    arrs = [np.asarray(f) for f in frames_rgb]
    k = lambda a: a[..., 0].astype(np.uint32) << 16 | a[..., 1].astype(np.uint32) << 8 | a[..., 2]
    todo = np.unique(np.concatenate([k(a).ravel() for a in arrs]))
    if len(todo) <= 256:
        return frames_rgb, len(todo)
    ex = np.array(sorted(exact), np.uint32)
    nuevos = np.setdiff1d(todo, ex)
    K = 256 - len(ex) - margen
    pix = np.concatenate([a.reshape(-1, 3)[~np.isin(k(a).ravel(), ex)] for a in arrs])
    img = Image.fromarray(pix.reshape(-1, 1, 3).astype(np.uint8), "RGB")
    q = img.quantize(colors=K, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = np.array(q.getpalette()[:3 * K], np.uint8).reshape(-1, 3)
    nc = np.stack([nuevos >> 16, nuevos >> 8 & 255, nuevos & 255], 1)
    idx = ((nc[:, None, :].astype(int) - pal[None].astype(int)) ** 2).sum(-1).argmin(1)
    mapa = dict(zip(nuevos.tolist(), (pal[idx][:, 0].astype(np.uint32) << 16 | pal[idx][:, 1].astype(np.uint32) << 8 | pal[idx][:, 2]).tolist()))
    out = []
    for a in arrs:
        kk = k(a); r = kk.copy()
        for c, m in mapa.items():
            r[kk == c] = m
        out.append(Image.fromarray(np.stack([r >> 16 & 255, r >> 8 & 255, r & 255], -1).astype(np.uint8), "RGB"))
    return out, len(np.unique(np.concatenate([k(np.asarray(o)).ravel() for o in out])))


def gif_global(frames, ruta, dur):
    arrs = [np.asarray(f.convert("RGB")) for f in frames]
    k = lambda a: a[..., 0].astype(np.uint32) << 16 | a[..., 1].astype(np.uint32) << 8 | a[..., 2]
    keys = np.unique(np.concatenate([k(a).ravel() for a in arrs]))
    assert len(keys) <= 256, len(keys)
    pal = np.zeros(768, np.uint8)
    pal[0:len(keys) * 3:3], pal[1:len(keys) * 3:3], pal[2:len(keys) * 3:3] = keys >> 16, keys >> 8 & 255, keys & 255
    ps = []
    for a in arrs:
        p = Image.fromarray(np.searchsorted(keys, k(a)).astype(np.uint8), "P"); p.putpalette(pal.tolist()); ps.append(p)
    ps[0].save(ruta, save_all=True, append_images=ps[1:], duration=dur, loop=0, disposal=1, optimize=False)


def gif_local(frames, ruta, dur):
    """GIF con una paleta propia por fotograma (cada uno puede tener hasta 256 colores): los colores no se agrupan si el fotograma cabe en 256."""
    k = lambda a: a[..., 0].astype(np.uint32) << 16 | a[..., 1].astype(np.uint32) << 8 | a[..., 2]
    ps, agrupados = [], 0
    for fr in frames:
        a = np.asarray(fr.convert("RGB"))
        keys = np.unique(k(a))
        if len(keys) <= 256:
            pal = np.zeros(768, np.uint8)
            pal[0:len(keys) * 3:3], pal[1:len(keys) * 3:3], pal[2:len(keys) * 3:3] = keys >> 16, keys >> 8 & 255, keys & 255
            p = Image.fromarray(np.searchsorted(keys, k(a)).astype(np.uint8), "P"); p.putpalette(pal.tolist())
        else:
            p = fr.convert("RGB").quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE); agrupados += 1
        ps.append(p)
    ps[0].save(ruta, save_all=True, append_images=ps[1:], duration=dur, loop=0, disposal=1, optimize=False)
    return agrupados


def gif_transparente(capas, ruta, dur):
    arrs = [np.asarray(c) for c in capas]
    k = lambda a: a[..., 0].astype(np.uint32) << 16 | a[..., 1].astype(np.uint32) << 8 | a[..., 2]
    cols = np.unique(np.concatenate([k(a)[a[..., 3] > 0] for a in arrs]))
    if len(cols) > 255:                                                    # agrupar los colores de efectos si hacen falta
        pix = np.concatenate([a[a[..., 3] > 0][:, :3] for a in arrs])
        q = Image.fromarray(pix.reshape(-1, 1, 3).astype(np.uint8), "RGB").quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        pal = np.array(q.getpalette()[:765], np.uint8).reshape(-1, 3)
        nuevas = []
        for a in arrs:
            m = a[..., 3] > 0; b = a.copy()
            flat = a[m][:, :3].astype(int)
            u, inv = np.unique(flat, axis=0, return_inverse=True)
            near = ((u[:, None, :] - pal[None].astype(int)) ** 2).sum(-1).argmin(1)
            b[m, :3] = pal[near][inv]
            nuevas.append(b)
        arrs = nuevas
        cols = np.unique(np.concatenate([k(a)[a[..., 3] > 0] for a in arrs]))
    flat = np.zeros(768, np.uint8); flat[0:3] = (255, 0, 255)
    flat[3:3 + len(cols) * 3:3], flat[4:4 + len(cols) * 3:3], flat[5:5 + len(cols) * 3:3] = cols >> 16, cols >> 8 & 255, cols & 255
    ps = []
    for a in arrs:
        idx = (np.searchsorted(cols, k(a)) + 1).astype(np.uint8); idx[a[..., 3] == 0] = 0
        p = Image.fromarray(idx, "P"); p.putpalette(flat.tolist()); ps.append(p)
    ps[0].save(ruta, save_all=True, append_images=ps[1:], duration=dur, loop=0, transparency=0, disposal=2, optimize=False)


def exportar(nombre, capas, exact):
    OUT.mkdir(exist_ok=True)
    fondo = componer_fondo(capas)
    fondo, n = reducir(fondo, exact | {FONDO[0] << 16 | FONDO[1] << 8 | FONDO[2]})
    gif_global(fondo, OUT / f"{nombre}_fondo_1x.gif", TICK)
    gif_global([f.resize((W * 2, H * 2), Image.NEAREST) for f in fondo], OUT / f"{nombre}_fondo_2x.gif", TICK)
    bi = binarizar(capas)
    gif_transparente(bi, OUT / f"{nombre}_transparente_1x.gif", TICK)
    gif_transparente([c.resize((W * 2, H * 2), Image.NEAREST) for c in bi], OUT / f"{nombre}_transparente_2x.gif", TICK)
    print(f"{nombre}: {len(capas)} ticks de {TICK} ms = {len(capas) * TICK / 1000:.2f} s; {n} colores con fondo")
    for r in sorted(OUT.glob(f"{nombre}_*.gif")):
        print(f"  {r.name}: {Image.open(r).size}, {r.stat().st_size / 1024:.0f} KB")
    return fondo


def colores_sprite(R):
    cols = set()
    for f in R["idle"] + R["vic"]:
        a = np.asarray(f)
        m = a[..., 3] == 255
        cols |= {int(r) << 16 | int(g) << 8 | int(b) for r, g, b in a[m][:, :3]}
    return cols


def hoja_contacto(frames, indices, ruta, z=1, cols=6):
    filas = (len(indices) + cols - 1) // cols
    sh = Image.new("RGB", (cols * W * z, filas * H * z))
    d = ImageDraw.Draw(sh)
    for j, i in enumerate(indices):
        im = frames[i].resize((W * z, H * z), Image.NEAREST) if z != 1 else frames[i]
        sh.paste(im, ((j % cols) * W * z, (j // cols) * H * z)); d.text(((j % cols) * W * z + 6, (j // cols) * H * z + 6), f"tick {i}", fill=(255, 255, 255))
    sh.save(ruta)


def main():
    R = cargar()
    ex = colores_sprite(R)
    t1 = guion_bucle1(R)
    c1 = dibujar_ticks_bucle1(t1, R)
    f1 = exportar("bucle1_reposo_victoria", c1, ex)
    # duraciones: ticks por fase
    from collections import Counter
    print("  ticks por fase:", dict(Counter(t["fase"] for t in t1)))
    c3 = bucle3(R)
    f3 = exportar("bucle3_saludo", c3, ex)
    OUT.mkdir(exist_ok=True)
    sel = [0, 8, 31, 32, 33, 34, 35, 36, 39, 42, 44, 46, 48, 50, 52, 54, 58, 61]
    sel = [i for i in sel if i < len(f1)]
    hoja_contacto(f1, sel, OUT / "bucle1_momentos.png", z=1, cols=6)
    hoja_contacto(f3, [0, 3, 4, 8, 12, 16, 20, 23], OUT / "bucle3_momentos.png", z=1, cols=4)
    return t1


if __name__ == "__main__":
    main()
