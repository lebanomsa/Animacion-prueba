"""Marco de Utena con el color animado como las fases de la luna.

El marco es el de la animación de vergüenza (diseño de nudos, estrellas en las esquinas, cuernitos, nudo de corbata, corazones y
destellos), con todos sus detalles. Tiene dos estados de color:
  A  morado -> dorado (el degradado de reposo)
  B  el degradado invertido (dorado -> morado)
Una curva vertical, como el límite entre luz y sombra de la luna, barre el marco de izquierda a derecha:
  pasos 0-19   a su izquierda el marco está en B y a su derecha en A (el marco entero pasa de A a B)
  pasos 20-39  a su izquierda en A y a su derecha en B (vuelve de B a A), así que el bucle cierra sin salto.
El ciclo dura 40 pasos de 100 ms (4 s), independiente de la animación de Utena. Los detalles siguen su propio ciclo de 8 pasos
y cambian de color (dorado <-> morado) para contrastar con lo que tienen debajo.

Dos variantes del degradado de reposo: 'vertical' (morado arriba, dorado abajo) y 'diagonal' (como el marco original).
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "secuencia"))
import marco   # noqa: E402  (antes de añadir otras rutas)
sys.path.insert(0, str(ROOT / "utena_transformacion"))
import transformacion as tr   # noqa: E402

pe = tr.hz.pe                 # utilidades de GIF (paleta exacta)
CICLO, L, TICK, N = 8, 40, 100, 128

MORADO = [(0.0, (20, 6, 38)), (0.3, (72, 28, 124)), (0.6, (132, 72, 194)), (0.85, (192, 142, 236)), (1.0, (242, 224, 255))]
DORADO = [(0.0, (40, 24, 4)), (0.3, (130, 90, 16)), (0.6, (212, 160, 40)), (0.85, (250, 214, 90)), (1.0, (255, 246, 190))]
OSC = (24, 10, 34)

# ---------------------------------------------------------------- detalles (los del marco de la animación de vergüenza)
ESTRELLA = ["....a....", "....a....", "...aba...", "..abcba..", "aabcdcbaa", "..abcba..", "...aba...", "....a....", "....a...."]
ESTRELLA_DESTELLO = ["....a....", "...aba...", "...aba...", "..abcba..", "abbcdcbba", "..abcba..", "...aba...", "...aba...", "....a...."]
EST_ORO = {"a": (196, 140, 30), "b": (240, 196, 70), "c": (255, 232, 140), "d": (255, 255, 230)}
EST_MOR = {"a": (100, 44, 160), "b": (150, 84, 216), "c": (200, 150, 248), "d": (250, 236, 255)}
CUERNO = ["....kk", "...kgg", "..kggl", ".kggl.", "kggl..", "ggl..."]
CUERNO_ORO = {"k": (196, 140, 30), "g": (250, 214, 90), "l": (255, 244, 180)}
CUERNO_MOR = {"k": (100, 44, 160), "g": (150, 84, 216), "l": (200, 150, 248)}
ESTRELLITA = ["..a..", ".aba.", "abcba", ".aba.", "..a.."]
CORAZON = [".rr.rr.", "rRRrRRr", "rRhRRRr", "rRRRRRr", ".rRRRr.", "..rRr..", "...r..."]
CORAZON_PEQ = [".r.r.", "rRrRr", "rRRRr", ".rRr.", "..r.."]
COR_C = {"r": (190, 46, 100), "R": (255, 120, 168), "h": (255, 236, 244)}
NUDO = ["mm.....mm", "mMm...mMm", "mMMmnmMMm", "mMMnNnMMm", "mMMmnmMMm", "mMm...mMm", "mm.....mm"]
NUDO_MOR = {"m": (74, 38, 82), "M": (116, 65, 122), "n": (90, 48, 98), "N": (160, 104, 166)}
NUDO_ORO = {"m": (120, 78, 8), "M": (206, 156, 40), "n": (150, 104, 18), "N": (250, 214, 90)}


def blit(img, rows, x, y, cmap):
    px = img.load()
    celdas = {(x + i, y + j): ch for j, row in enumerate(rows) for i, ch in enumerate(row) if ch != "."}
    for (cx, cy) in celdas:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                q = (cx + dx, cy + dy)
                if q not in celdas and 0 <= q[0] < img.width and 0 <= q[1] < img.height:
                    px[q] = (*OSC, 255)
    for (cx, cy), ch in celdas.items():
        if 0 <= cx < img.width and 0 <= cy < img.height:
            px[cx, cy] = (*cmap[ch], 255)


def destello(img, x, y, r, col=(255, 252, 236)):
    d = ImageDraw.Draw(img)
    d.line((x - r, y, x + r, y), fill=col + (255,)); d.line((x, y - r, x, y + r), fill=col + (255,))
    d.point((x, y), fill=(255, 255, 255, 255))


def detalles(fr, t, w):
    """Dibuja los detalles; los colores se eligen según el color que haya debajo (w < 0.5: morado, w >= 0.5: dorado)."""
    t = t % CICLO
    for (x, y), fase in (((2, 2), 0), ((117, 2), 2), ((2, 117), 6), ((117, 117), 4)):
        col = EST_ORO if w[y + 4, x + 4] < 0.5 else EST_MOR
        blit(fr, ESTRELLA_DESTELLO if (t - fase) % CICLO in (0, 1) else ESTRELLA, x, y, col)
    arriba_morado = w[5, 64] < 0.5
    cc, est = (CUERNO_ORO, EST_MOR) if arriba_morado else (CUERNO_MOR, EST_ORO)
    blit(fr, CUERNO, 53, 1, cc)
    blit(fr, [r[::-1] for r in CUERNO], 69, 1, cc)
    blit(fr, ESTRELLITA, 61, 2, est if t % 4 < 2 else {**est, "c": (250, 236, 255)})
    blit(fr, NUDO, 59, 120, NUDO_MOR if w[123, 63] >= 0.5 else NUDO_ORO)
    for (x, y, fase) in ((2, 60, 0), (119, 60, 2)):
        if (t + fase) % 4 < 2:
            blit(fr, CORAZON, x - 1, y - 1, COR_C)
        else:
            blit(fr, CORAZON_PEQ, x, y, COR_C)
    for k, (x, y) in enumerate([(30, 3), (98, 3), (3, 34), (124, 34), (3, 92), (124, 92), (30, 124), (98, 124)]):
        r = (1, 2, 2, 1, 0, 0, 0, 0)[(t + k * 3) % CICLO]
        if r:
            destello(fr, x, y, r)


# ---------------------------------------------------------------- color del marco
def datos_base():
    """sym (imagen del marco original), alpha, v (tono 0..1 de cada píxel) y ventana, sacados de marco.build."""
    cap = {}
    orig = marco.recolor

    def gancho(rgb, top, bot):
        cap["rgb"] = rgb
        return np.zeros(rgb.shape, np.uint8)
    marco.recolor = gancho
    try:
        fr, win = marco.build(MORADO, DORADO)
    finally:
        marco.recolor = orig
    rgb = cap["rgb"]
    lum = rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114
    v = np.clip(lum / np.percentile(lum, 98), 0, 1)
    return v, np.asarray(fr)[..., 3], win


def gradiente(opcion):
    """t_A[y, x] en 0..1 (0 = morado, 1 = dorado): el degradado de reposo."""
    yy, xx = np.mgrid[0:N, 0:N]
    B = marco.BANDS
    if opcion == "vertical":
        band = np.minimum(yy * B // N, B - 1)
        t = np.clip(((band + 0.5) / B - 0.30) / 0.40, 0, 1)
        return t * t * (3 - 2 * t)
    band = np.minimum((xx + yy) * B // (2 * N - 1), B - 1)                  # diagonal, como el marco original
    return np.clip((band / (B - 1) - 0.36) / 0.28, 0, 1)


def mapa_w(tA, t, R=92.0):
    """Cuánto dorado hay en cada píxel en el paso t: el estado A a un lado de la curva y el B (invertido) al otro."""
    fase2 = t >= 20
    k = -1.0 + 2.0 * ((t - 20 * fase2) / 20.0)
    yy, xx = np.mgrid[0:N, 0:N]
    borde = 64 + k * np.sqrt(np.maximum(R * R - (yy + 0.5 - 64) ** 2, 0))
    izq = (xx + 0.5) < borde
    cambiado = ~izq if fase2 else izq
    return np.where(cambiado, 1 - tA, tA)


def colores(v, w):
    top = marco.ramp(MORADO, v)
    bot = marco.ramp(DORADO, v)
    return (top + (bot - top) * w[..., None]).round().astype(np.uint8)


def agrupar(pixeles_por_paso, K):
    """Una sola paleta de K tonos para todos los pasos (el color del marco no 'tiembla' entre pasos)."""
    todo = np.concatenate(pixeles_por_paso)
    img = Image.fromarray(todo.reshape(-1, 1, 3).astype(np.uint8), "RGB")
    q = img.quantize(colors=K, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    return np.array(q.getpalette()[:3 * K], np.uint8).reshape(-1, 3)


def mapear(rgb, pal):
    flat = rgb.reshape(-1, 3).astype(int)
    k = flat[:, 0] << 16 | flat[:, 1] << 8 | flat[:, 2]
    u, inv = np.unique(k, return_inverse=True)
    uc = np.stack([u >> 16, u >> 8 & 255, u & 255], 1)
    d = ((uc[:, None, :] - pal[None].astype(int)) ** 2).sum(-1)
    return pal[d.argmin(1)][inv].reshape(rgb.shape)


def construir_marco(opcion, K=150):
    """Lista de 40 marcos RGBA (128x128) y la lista de mapas w."""
    v, alpha, win = datos_base()
    tA = gradiente(opcion)
    ws = [mapa_w(tA, t) for t in range(L)]
    exactos = [colores(v, w) for w in ws]
    op = alpha > 0
    pal = agrupar([e[op] for e in exactos], K)
    marcos = []
    for t in range(L):
        rgb = mapear(exactos[t], pal)
        fr = Image.fromarray(np.dstack([rgb, alpha]).astype(np.uint8), "RGBA")
        fr_ = fr.copy()
        detalles(fr_, t, ws[t])
        marcos.append(fr_)
    return marcos, ws, win


# ---------------------------------------------------------------- composición con la animación de Utena
def escena(caps, marcos, t):
    up = lambda a: np.repeat(np.repeat(a, 2, axis=0), 2, axis=1)
    out = Image.fromarray(up(caps[t].under), "RGB").convert("RGBA")
    out.alpha_composite(marcos[t].crop((1, 1, 127, 127)))
    out.alpha_composite(Image.fromarray(up(caps[t].over), "RGBA"))
    return out.convert("RGB")


def main():
    out = HERE / "previews"; out.mkdir(exist_ok=True)
    caps = tr.cargar_capas()
    for opcion in ("vertical", "diagonal"):
        K = 150
        while True:
            marcos, ws, win = construir_marco(opcion, K)
            frames = [escena(caps, marcos, t) for t in range(L)]
            n = len({tuple(c) for f in frames for c in np.unique(np.asarray(f).reshape(-1, 3), axis=0)})
            print(f"{opcion}: marco con {K} tonos -> {n} colores")
            if n <= 256:
                break
            K -= max(2, n - 256)
        f504 = [f.resize((504, 504), Image.NEAREST) for f in frames]
        pe.gif_opaco(frames, out / f"marco_{opcion}_con_utena_126.gif", TICK)
        pe.gif_opaco(f504, out / f"marco_{opcion}_con_utena_x4.gif", TICK)
        for r in (f"marco_{opcion}_con_utena_126.gif", f"marco_{opcion}_con_utena_x4.gif"):
            print(f"  {r}: {Image.open(out / r).size}, {(out / r).stat().st_size / 1024:.0f} KB")
        # hojas: Utena dentro (8 momentos) y solo el marco (8 momentos)
        sel = [0, 5, 10, 15, 20, 25, 30, 35]
        z = 2
        sh = Image.new("RGB", (4 * 126 * z, 2 * 126 * z))
        for i, t in enumerate(sel):
            sh.paste(frames[t].resize((126 * z, 126 * z), Image.NEAREST), ((i % 4) * 126 * z, (i // 4) * 126 * z))
            ImageDraw.Draw(sh).text(((i % 4) * 126 * z + 6, (i // 4) * 126 * z + 6), f"t={t}", fill=(255, 255, 255))
        sh.save(out / f"momentos_{opcion}_con_utena.png")
        sh = Image.new("RGB", (4 * 128 * z, 2 * 128 * z), (60, 60, 70))
        for i, t in enumerate(sel):
            f = Image.new("RGBA", (128, 128), (60, 60, 70, 255)); f.alpha_composite(marcos[t])
            sh.paste(f.convert("RGB").resize((128 * z, 128 * z), Image.NEAREST), ((i % 4) * 128 * z, (i // 4) * 128 * z))
            ImageDraw.Draw(sh).text(((i % 4) * 128 * z + 6, (i // 4) * 128 * z + 6), f"t={t}", fill=(255, 255, 255))
        sh.save(out / f"barrido_{opcion}_solo_marco.png")
        # el bucle: último paso vs primero
        d = int((np.abs(np.asarray(frames[-1]).astype(int) - np.asarray(frames[0]).astype(int)).sum(-1) > 0).sum())
        print(f"  píxeles distintos entre el último paso y el primero: {d}")


if __name__ == "__main__":
    main()
