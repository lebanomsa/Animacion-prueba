"""Fondo de Percier convertido a escenario de Halloween: recolor por paleta, calabaza y velas animadas, niebla baja.

Se recorta una ventana de 128x128 píxeles del 'fondo percier.PNG' (que se ve a x5 como Percier) y se transforma:
  * recolor: cada color del original se pasa a una paleta violeta/verde con luz de luna (el original solo tiene 51 colores)
  * calabaza grande con los ojos y la boca que brillan al mismo compás que las del marco, y dos velas con la llama parpadeando
  * niebla baja que avanza por el suelo, en 2 densidades, en un ciclo de 12 pasos que enlaza
"""
import colorsys
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).parent.parent
CICLO = 12
NIVELES = [3, 3, 3, 2, 1, 0, 0, 0, 1, 2, 3, 3]
CROP = (420, 232)                 # esquina del recorte (corte de la derecha: alfombra a la izquierda y luz en el suelo)
OSCURO = (22, 12, 18)


def cargar():
    return Image.open(ROOT / "fondo percier.PNG").convert("RGB")


def recolor_color(c):
    r, g, b = [v / 255 for v in c]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    h *= 360
    if v > 0.50 and s < 0.5:                                      # luz pálida (manchas del suelo, ventanas) -> luz de luna
        h2, s2, v2 = 178, min(0.42, s * 0.8 + 0.12), min(1.0, v * 1.12)
    elif r > g + 0.10 and r > b + 0.10 and h < 25:                # alfombras rojas -> ciruela
        h2, s2, v2 = 318, min(0.75, s * 0.9), v * 0.9
    elif g > r and b > r - 0.02 and 150 < h < 215:               # alfombras verde azuladas -> verde veneno
        h2, s2, v2 = 130, min(0.7, s * 1.1), v * 0.95
    else:                                                          # marrones y olivas (piedra, suelo, madera) -> violeta
        h2, s2, v2 = 268 + (h - 40) * 0.25, min(0.55, 0.30 + s * 0.45), min(1.0, (v ** 0.8) * 1.22)
    r, g, b = colorsys.hsv_to_rgb((h2 % 360) / 360, max(0, min(1, s2)), max(0, min(1, v2)))
    return (round(r * 255), round(g * 255), round(b * 255))


def recolorear(img):
    a = np.asarray(img).copy()
    cols = np.unique(a.reshape(-1, 3), axis=0)
    mapa = {tuple(c): recolor_color(tuple(c)) for c in cols}
    out = np.zeros_like(a)
    for k, v in mapa.items():
        out[(a == k).all(-1)] = v
    return Image.fromarray(out, "RGB"), mapa


def ventana_base():
    bg = cargar()
    x, y = CROP
    crop = bg.crop((x, y, x + 128, y + 128))
    return recolorear(crop)[0]


# ---- elementos nuevos -----------------------------------------------------------------------------------------------
COLOR_OJOS = {0: (66, 26, 6), 1: (176, 88, 14), 2: (255, 232, 110), 3: (255, 252, 200)}
HALO = (255, 206, 96)


def _dil(m):
    d = m.copy()
    d[1:] |= m[:-1]; d[:-1] |= m[1:]; d[:, 1:] |= m[:, :-1]; d[:, :-1] |= m[:, 1:]
    return d


def calabaza_grande(nivel):
    """Calabaza con cara de 23x24 píxeles; los ojos y la boca brillan según `nivel` (0 apagada .. 3 brillo máximo)."""
    W, H = 23, 24
    yy, xx = np.mgrid[0:H, 0:W]
    el = lambda cx, cy, rx, ry: ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1
    cuerpo = el(11.5, 13, 6.4, 7.8) | el(6.5, 13.8, 5.3, 6.8) | el(16.5, 13.8, 5.3, 6.8)
    tallo = (xx >= 11) & (xx <= 13) & (yy >= 2) & (yy <= 5)
    contorno = _dil(cuerpo | tallo) & ~(cuerpo | tallo)
    img = np.zeros((H, W, 4), np.uint8)
    img[contorno] = (*OSCURO, 255)
    img[cuerpo] = (240, 140, 20, 255)
    img[cuerpo & ((np.abs(xx - 9) < 0.8) | (np.abs(xx - 14) < 0.8) | (yy >= 19))] = (186, 88, 10, 255)
    img[cuerpo & el(4.8, 10.5, 1.8, 2.4)] = (255, 196, 80, 255)
    img[tallo] = (84, 170, 44, 255)
    img[tallo & (xx == 13)] = (36, 100, 36, 255)
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    d.polygon([(5, 11.5), (9, 11.5), (7, 7.5)], fill=255)
    d.polygon([(14, 11.5), (18, 11.5), (16, 7.5)], fill=255)
    d.polygon([(5.5, 15), (18, 15), (16.5, 18.5), (14.5, 16.5), (12, 19), (9.5, 16.5), (7.5, 18.5)], fill=255)
    luz = (np.asarray(m) > 0) & cuerpo
    if nivel == 3:
        img[_dil(luz) & cuerpo & ~luz & (img[..., 0] > 150)] = (*HALO, 255)
    img[luz] = (*COLOR_OJOS[nivel], 255)
    return Image.fromarray(img, "RGBA")


LLAMAS = [["..O..", ".OyO.", ".OyO."], ["...O.", ".OyO.", ".OyO."], ["..O..", ".OOO.", ".OyO."], [".O...", ".OyO.", ".OyO."]]
CMAP_VELA = {"c": (240, 228, 196), "d": (196, 178, 140), "O": (255, 140, 30), "y": (255, 236, 120), "k": OSCURO}


def vela(t, alto, fase):
    """Vela de 5 px de ancho con la llama parpadeando (4 posturas)."""
    cuerpo = ["ccccd", "ccccd", "cdccd", "ccccd"] + ["ccccd"] * (alto - 5) + ["ddddd"]
    rows = LLAMAS[(t + fase) % 4] + ["..k.."] + cuerpo
    img = Image.new("RGBA", (5, len(rows)), (0, 0, 0, 0))
    px = img.load()
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch != ".":
                px[i, j] = (*CMAP_VELA[ch], 255)
    return img


# ---- niebla ---------------------------------------------------------------------------------------------------------
def campo_niebla(seed=7):
    """Ruido suave y periódico en horizontal (período 48 px): desplazarlo 4 px por paso enlaza tras 12 pasos."""
    rng = np.random.default_rng(seed)
    g = rng.random((12, 3))                                      # manchas alargadas: 16 px de ancho y unos 10 de alto
    g = np.tile(g, (1, 5))                                        # 15 columnas = 5 períodos
    return np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((240, 128), Image.BICUBIC)).astype(float) / 255


def niveles_niebla(t, campo=None):
    campo = campo_niebla() if campo is None else campo
    n = campo[:, 4 * t: 4 * t + 128]
    y = np.arange(128)[:, None]
    w = np.clip((y - 58) / 70.0, 0, 1) ** 1.1
    v = n * 0.60 + w * 0.70
    lv = np.zeros((128, 128), np.uint8)
    lv[v > 0.78] = 1
    lv[v > 1.00] = 2
    lv[(y < 60).repeat(128, 1)] = 0
    return lv


FOG = (176, 208, 222)


def aplicar_niebla(img, lv):
    a = np.asarray(img).astype(float)
    out = a.copy()
    for nivel, op in ((1, 0.20), (2, 0.36)):
        m = lv == nivel
        out[m] = a[m] * (1 - op) + np.array(FOG) * op
    return Image.fromarray(out.round().astype(np.uint8), "RGB")


def escenario(t, niebla=True, campo=None, base=None):
    """Ventana de 128x128 (RGB) del escenario en el paso t del ciclo de 12."""
    img = (base or ventana_base()).copy()
    if niebla:
        img = aplicar_niebla(img, niveles_niebla(t, campo))
    rgba = img.convert("RGBA")
    rgba.alpha_composite(calabaza_grande(NIVELES[t % CICLO]), (3, 96))
    for (x, alto, fase) in ((29, 10, 0), (37, 7, 2)):
        v = vela(t, alto, fase)
        rgba.alpha_composite(v, (x, 120 - v.height))
    return rgba.convert("RGB")
