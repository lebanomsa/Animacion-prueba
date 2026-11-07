"""Special Bersek, bucle 2: salta alto, gira en el aire y al caer sube un pilar de fuego bajo él (detrás de Bersek, con las llamas de la base por delante de sus pies).
La cámara sigue el salto (al 65 %) y el fondo (Stage Fukai de Drache) queda fijo en el mundo. Ventana de 80x80 dentro del marco de siempre (rejilla de 126).
  python animacion_pilar.py [X0]   -> bersek/salida_pilar/
Dos variantes: 'vertical' (cae donde salta) y 'avance' (avanza 20 px durante el salto).
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
import bucles_bersek as bb
import marco

HERE = Path(__file__).parent
OUT = HERE / "salida_pilar"
STAGE = HERE.parent / "drache" / "fuentes" / "stage drache.png"
TICK = 70
VX, VY, VN = 23, 23, 80              # ventana en la rejilla de 126
FLOOR_STAGE, FLOOR_WIN = 205, 75     # fila del suelo en el panorama y en la ventana (con la cámara abajo)
ALTO, SEGUIR, AIRE = 70, 0.65, 14    # altura del salto (px), fracción que la cámara sigue, pasos en el aire
PILAR = list(range(16)) + [16, 18, 20, 22, 24, 26]
K_FONDO, K_MARCO = 80, 40


def agrupar(rgb, k):
    q = Image.fromarray(rgb.reshape(-1, 1, 3).astype(np.uint8), "RGB").quantize(colors=k, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = np.array(q.getpalette()[:768], np.uint8).reshape(-1, 3)
    return pal[np.asarray(q).reshape(-1)]


def fondo_mundo(x0):
    a = np.asarray(Image.open(STAGE).convert("RGB"))[17:17 + 219, 5:5 + 2048]
    w = a[:, x0:x0 + VN].copy()
    return agrupar(w, K_FONDO).reshape(w.shape)


def marco_126():
    fr, _ = marco.build()
    img = np.array(fr); o = img[..., 3] > 0
    img[..., :3][o] = agrupar(img[..., :3][o], K_MARCO)
    return Image.fromarray(img, "RGBA").crop((1, 1, 127, 127))


def pegar(canvas, im, x, y):
    """alpha_composite con recorte a los límites del lienzo (x, y pueden ser negativos)."""
    x, y = int(round(x)), int(round(y))
    l, t = max(0, -x), max(0, -y)
    r_, b_ = min(im.width, canvas.width - x), min(im.height, canvas.height - y)
    if r_ > l and b_ > t:
        canvas.alpha_composite(im.crop((l, t, r_, b_)), (x + l, y + t))


def guion(r, variante):
    """Un dict por paso: bers, x (centro en la ventana), h (altura sobre el suelo, px), pilar (índice) o None."""
    x0 = 40 if variante == "vertical" else 28
    dx = 0 if variante == "vertical" else 20
    P = []
    def b(img, n=1, **kw):
        for _ in range(n): P.append(dict(bers=img, x=x0, h=0, pilar=None, **kw))
    for i in (4, 5, 6, 3): b(r.idle[i])
    b(r.contra[16]); b(r.contra[1]); b(r.contra[10])
    giro = [2, 3, 4, 5]
    for i in range(AIRE):
        s = (i + 0.5) / AIRE
        h = 4 * ALTO * s * (1 - s)
        if i == 0: img = r.contra[11]
        elif i >= AIRE - 2: img = r.contra[12 if i == AIRE - 2 else 13]
        else: img = r.contra[giro[(i - 1) % 4]]
        P.append(dict(bers=img, x=x0 + dx * (i + 1) / AIRE, h=h, pilar=None))
    t0 = len(P)
    xl = x0 + dx
    for img in (r.contra[25], r.contra[26], r.contra[27], r.contra[16]):
        P.append(dict(bers=img, x=xl, h=0, pilar=None))
    for k in range(len(PILAR)):
        t = t0 + k
        while len(P) <= t: P.append(dict(bers=None, x=xl, h=0, pilar=None))
        P[t]["pilar"] = PILAR[k]
    for t in range(t0 + 4, len(P)):
        P[t]["bers"] = r.idle[(t - t0 - 4) % 8]
    return P


def render(variante, x0=1650, marco_fn=None):
    r = bb.cargar()
    mundo = fondo_mundo(x0)
    marco_im = marco_126()
    frames = []
    for t, p in enumerate(guion(r, variante)):
        if marco_fn is not None: marco_im = marco_fn(t)
        cam = int(round(SEGUIR * p["h"]))
        top = FLOOR_STAGE - FLOOR_WIN - cam
        ventana = Image.fromarray(mundo[top:top + VN]).convert("RGBA")
        c = Image.new("RGBA", (126, 126), (0, 0, 0, 255)); c.paste(ventana, (VX, VY)); c.alpha_composite(marco_im)
        suelo = VY + FLOOR_WIN + cam                     # fila del suelo (en la rejilla) con esta cámara
        xl = VX + (40 if variante == "vertical" else 48)
        if p["pilar"] is not None:
            pil = r.pilar[p["pilar"]]
            pegar(c, pil, xl - pil.width / 2, suelo + 2 - pil.height)
        cx, by = bb.hb.pies(p["bers"])
        pegar(c, p["bers"], VX + p["x"] - cx, suelo - p["h"] - by)
        if p["pilar"] is not None:                       # llamas de la base por delante de los pies
            pil = r.pilar[p["pilar"]]
            fr = pil.crop((0, max(0, pil.height - 7), pil.width, pil.height))
            pegar(c, fr, xl - pil.width / 2, suelo + 2 - fr.height)
        frames.append(c.convert("RGB"))
    return frames


def main():
    OUT.mkdir(exist_ok=True)
    x0 = int(sys.argv[1]) if len(sys.argv) > 1 else 1650
    for v in ("vertical", "avance"):
        fr = render(v, x0)
        n = max(len(np.unique(np.asarray(f).reshape(-1, 3), axis=0)) for f in fr)
        ag = bb.gif_local([f.resize((504, 504), Image.NEAREST) for f in fr], OUT / f"bersek_pilar_{v}_x4.gif", TICK)
        bb.gif_local(fr, OUT / f"bersek_pilar_{v}_126.gif", TICK)
        print(v, len(fr), "pasos de", TICK, "ms =", round(len(fr) * TICK / 1000, 2), "s; colores máx por fotograma:", n, "; agrupados a 256:", ag)
        idx = [0, 5, 7, 9, 12, 15, 18, 21, 22, 23, 25, 28, 33, 38, 43]
        idx = [i for i in idx if i < len(fr)]
        cols = 5; filas = (len(idx) + cols - 1) // cols
        s = Image.new("RGB", (cols * 254, filas * 254), (20, 20, 20))
        for j, i in enumerate(idx): s.paste(fr[i].resize((252, 252), Image.NEAREST), ((j % cols) * 254, (j // cols) * 254))
        s.save(OUT / f"momentos_{v}.png")


if __name__ == "__main__":
    main()
