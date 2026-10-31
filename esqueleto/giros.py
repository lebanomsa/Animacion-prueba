"""Vista previa de las dos opciones para el fotograma de paso entre el 3.0 (de frente) y el 1.0 (de perfil), y entre el 2.1 y el 3.0.

  A giro:     el 3.0 se estrecha a la mitad de su ancho durante un paso (el rifle se ve en escorzo)
  B agachado: el 3.0 se aplasta un 12 % en altura y se ensancha un 6 %, como tomando impulso
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import hojas

HERE = Path(__file__).parent
PREV = HERE / "previews"
CW, CH = 140, 124
X_C, G = 70, 116
FONDO = (44, 52, 80)
TICK = 80
F = hojas.todos()


def colocar(f, sx=1.0, sy=1.0):
    """Capa RGBA CWxCH con el fotograma f, escalado (sx, sy) con vecino más cercano, anclado en (X_C, G)."""
    img = f["img"]
    if sx != 1.0 or sy != 1.0:
        img = img.resize((max(1, round(img.width * sx)), max(1, round(img.height * sy))), Image.NEAREST)
    x = round(X_C - f["ancla_x"] * sx)
    y = round(G - f["suelo"] * sy)
    lay = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    sx_, sy_ = max(-x, 0), max(-y, 0)
    dx, dy = max(x, 0), max(y, 0)
    w, h = min(img.width - sx_, CW - dx), min(img.height - sy_, CH - dy)
    lay.alpha_composite(img.crop((sx_, sy_, sx_ + w, sy_ + h)), (dx, dy))
    return lay


def giro():
    return colocar(F["3.0"], sx=0.5)


def agachado():
    return colocar(F["3.0"], sx=1.06, sy=0.88)


def fondo(lay):
    b = Image.new("RGBA", (CW, CH), FONDO + (255,))
    ImageDraw.Draw(b).line((0, G + 1, CW, G + 1), fill=(30, 36, 58, 255))
    b.alpha_composite(lay)
    return b.convert("RGB")


def secuencia(T):
    """3.0 -> T -> 1.0 ... 2.1 -> T -> 3.0, con una pausa corta en las poses largas."""
    c = colocar
    f = []
    f += [c(F["3.0"])] * 4 + [T] + [c(F["1.0"])] * 4 + [c(F["1.1"])] * 2 + [c(F["1.2"])] * 2
    f += [c(F["2.0"])] * 3 + [c(F["2.1"])] * 4 + [T] + [c(F["3.0"])] * 3
    return f


def main():
    PREV.mkdir(exist_ok=True)
    opciones = (("A_giro", giro()), ("B_agachado", agachado()))
    for nombre, T in opciones:
        fr = [fondo(x) for x in secuencia(T)]
        # GIF x4
        imgs = [f.resize((CW * 4, CH * 4), Image.NEAREST) for f in fr]
        arrs = [np.asarray(i) for i in imgs]
        key = lambda a: a[..., 0].astype(np.uint32) << 16 | a[..., 1].astype(np.uint32) << 8 | a[..., 2]
        keys = np.unique(np.concatenate([key(a).ravel() for a in arrs]))
        pal = np.zeros(768, np.uint8)
        pal[0:len(keys) * 3:3], pal[1:len(keys) * 3:3], pal[2:len(keys) * 3:3] = keys >> 16, keys >> 8 & 255, keys & 255
        out = []
        for a in arrs:
            p = Image.fromarray(np.searchsorted(keys, key(a)).astype(np.uint8), "P"); p.putpalette(pal.tolist()); out.append(p)
        out[0].save(PREV / f"giro_{nombre}.gif", save_all=True, append_images=out[1:], duration=TICK, loop=0, disposal=1, optimize=False)
        # tira: dos transiciones
        S = 3
        par = [[F["3.0"], T, F["1.0"]], [F["2.1"], T, F["3.0"]]]
        hoja = Image.new("RGB", (3 * CW * S, 2 * (CH * S + 16)), (20, 14, 24))
        d = ImageDraw.Draw(hoja)
        for r, trio in enumerate(par):
            for k, x in enumerate(trio):
                lay = x if isinstance(x, Image.Image) else colocar(x)
                nom = ["antes", "paso", "después"][k]
                d.text((k * CW * S + 4, r * (CH * S + 16) + 2), f"{nom}", fill=(255, 220, 120))
                hoja.paste(fondo(lay).resize((CW * S, CH * S), Image.NEAREST), (k * CW * S, r * (CH * S + 16) + 16))
        hoja.save(PREV / f"giro_{nombre}.png")
        print(nombre, len(fr), "pasos", len(keys), "colores")


if __name__ == "__main__":
    main()
