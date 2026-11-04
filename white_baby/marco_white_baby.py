"""Marcos para la animación de pesca de White Baby y Alice: el diseño de nudos de siempre (secuencia/marco.py) recoloreado
y con detalles estáticos en la banda exterior (cuerda o olas + pequeños iconos de pesca y mar).

Tres propuestas ('muelle', 'mar', 'mixto'). La banda exterior (4 px: filas/columnas 1..4 y 123..126) se convierte en un canal oscuro con
un patrón continuo (cuerda trenzada u olas) y casillas con iconos. El diseño de nudos y la ventana de 80x80 no se tocan.

  python marco_white_baby.py    -> opciones de marco con la animación en salida/opciones_marco.png
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "secuencia"))
sys.path.insert(0, str(HERE.parent / "alice_heart"))
import marco   # noqa: E402
from marco_alice_heart import Pincel, quantize_rgb   # noqa: E402

# ---------------------------------------------------------------- paletas (arriba, abajo)
# Tonos tomados de los personajes: cabello y madera del muelle, bikini y cola verde azulados, luz celeste de la caña, aleta plateada.
ORO_CLARO = [(0.0, (40, 24, 10)), (0.3, (112, 76, 36)), (0.6, (190, 142, 70)), (0.85, (232, 196, 120)), (1.0, (255, 240, 196))]
MADERA = [(0.0, (24, 14, 8)), (0.3, (66, 40, 24)), (0.6, (116, 76, 44)), (0.85, (160, 112, 70)), (1.0, (214, 170, 120))]
PLATA = [(0.0, (20, 26, 34)), (0.3, (64, 76, 90)), (0.6, (140, 154, 170)), (0.85, (200, 212, 224)), (1.0, (244, 248, 252))]
VERDE_MAR = [(0.0, (0, 24, 18)), (0.3, (0, 64, 40)), (0.6, (0, 128, 104)), (0.85, (24, 180, 150)), (1.0, (160, 240, 226))]
TEAL = [(0.0, (0, 20, 20)), (0.3, (0, 62, 56)), (0.6, (0, 116, 104)), (0.85, (30, 170, 150)), (1.0, (170, 238, 226))]
ORO = [(0.0, (30, 18, 4)), (0.3, (92, 58, 14)), (0.6, (170, 118, 30)), (0.85, (226, 176, 70)), (1.0, (255, 238, 170))]

TEMAS = {
    "muelle": dict(top=ORO_CLARO, bot=MADERA, canal=(30, 18, 10), patron="cuerda", c1=(222, 178, 124), c2=(122, 84, 48),
                   acento=(0, 150, 124), claro=(240, 226, 196), metal=(206, 214, 224)),
    "mar": dict(top=PLATA, bot=VERDE_MAR, canal=(4, 24, 24), patron="olas", c1=(24, 190, 160), c2=(170, 244, 232),
                acento=(0, 232, 248), claro=(236, 246, 250), metal=(206, 220, 230)),
    "muelle_mar": dict(top=PLATA, bot=VERDE_MAR, canal=(4, 24, 24), patron="cuerda", c1=(170, 244, 232), c2=(0, 104, 88),
                       acento=(0, 232, 248), claro=(236, 246, 250), metal=(206, 220, 230), pez=(24, 190, 160), iconos="muelle"),
    "mixto": dict(top=TEAL, bot=ORO, canal=(10, 26, 24), patron="olas", c1=(226, 176, 70), c2=(255, 236, 168),
                  acento=(0, 232, 248), claro=(244, 240, 220), metal=(206, 214, 224)),
}

# ---------------------------------------------------------------- iconos (4 filas); X principal, o claro, d oscuro, R rojo, W blanco, M metal
ICONOS = {
    "pez": ["..XXX..X", ".XXXXXXX", ".XXXXX.X", "..XXX..."],
    "anzuelo": ["..M", "..M", "M.M", ".MM"],
    "ancla": [".MMM.", "..M..", "M.M.M", ".MMM."],
    "boya": [".R.", "RRR", "WWW", ".W."],
    "concha": [".ooo.", "oXoXo", "XXoXX", ".XXX."],
    "perla": ["WWo", "WWW", ".WW"],
    "burbujas": ["..o.o..", ".o.....", "..o..o.", "o....o."],
}


def _icono(nombre, tema, flip=False):
    filas = ICONOS[nombre]
    if flip:
        filas = [f[::-1] for f in filas]
    cm = {"X": tema["acento"], "o": tema["claro"], "d": (16, 20, 22), "R": (216, 72, 40), "W": (248, 248, 248), "M": tema["metal"]}
    if nombre in ("pez", "concha"):
        cm["X"] = tema.get("pez", tema["c1"])
    return filas, cm


def _pone_icono(p, nombre, x_centro, banda, tema, flip=False):
    filas, cm = _icono(nombre, tema, flip)
    w = len(filas[0])
    x0 = x_centro - w // 2
    y0 = 1 if banda == "arriba" else 123
    for r, fila in enumerate(filas):
        for k, ch in enumerate(fila):
            if ch != ".":
                p.put(x0 + k, y0 + r, cm[ch])
    if nombre == "pez":                       # ojo
        ex = x0 + (6 if flip else 1) if False else x0 + (len(filas[0]) - 3 if flip else 2)
        p.put(ex, y0 + 1, (16, 20, 22))
    return (x0 - 2, x0 + w + 1)


def _patron(a, u, tema):
    if tema["patron"] == "cuerda":
        return tema["c1"] if ((a + u) // 2) % 2 == 0 else tema["c2"]
    y = int(round(1.0 + 1.0 * np.sin(2 * np.pi * a / 8.0)))
    if u == y:
        return tema["c2"]
    if u == y + 1:
        return tema["c1"]
    return None


LADOS = ("arriba", "abajo", "izq", "der")
A0, A1 = 9, 118


def detalles(img, tema_nombre):
    tema = TEMAS[tema_nombre]
    p = Pincel(img)
    from marco_alice_heart import _banda
    # canal oscuro
    for lado in LADOS:
        for a in range(A0, A1 + 1):
            for u in range(4):
                p.put(*_banda(lado, a, u), tema["canal"])
    iconos = {
        "muelle_mar": None,
        "muelle": dict(arriba=[("boya", 24, False), ("pez", 63, False), ("anzuelo", 102, False)],
                       abajo=[("pez", 24, True), ("ancla", 63, False), ("boya", 102, False)]),
        "mar": dict(arriba=[("burbujas", 24, False), ("concha", 63, False), ("burbujas", 102, False)],
                    abajo=[("pez", 24, False), ("perla", 63, False), ("pez", 102, True)]),
        "mixto": dict(arriba=[("pez", 24, False), ("ancla", 63, False), ("pez", 102, True)],
                      abajo=[("anzuelo", 24, False), ("perla", 63, False), ("anzuelo", 102, False)]),
    }
    iconos["muelle_mar"] = iconos["muelle"]
    iconos = iconos[tema_nombre]
    libres = {lado: [] for lado in LADOS}
    for lado in ("arriba", "abajo"):
        for (nom, xc, fl) in iconos[lado]:
            libres[lado].append(_pone_icono(p, nom, xc, lado, tema, fl))
    # patrón continuo en los cuatro lados, saltando las casillas de los iconos
    for lado in LADOS:
        for a in range(A0, A1 + 1):
            if any(l <= a <= r for (l, r) in libres[lado]):
                continue
            if lado in ("izq", "der") and abs(a - 63) <= 2:
                continue
            for u in range(4):
                c = _patron(a, u, tema)
                if c is not None:
                    p.put(*_banda(lado, a, u), c)
    # perla en el centro de los lados
    perla = ICONOS["perla"]
    for lado in ("izq", "der"):
        for r, fila in enumerate(perla):
            for k, ch in enumerate(fila):
                if ch != ".":
                    p.banda(lado, 62 + r, 1 + k, (248, 248, 248) if ch != "o" else tema["claro"])


def build(tema_nombre, k=None):
    """(marco RGBA uint8 de 128x128 con detalles, ventana)."""
    t = TEMAS[tema_nombre]
    fr, win = marco.build(t["top"], t["bot"])
    img = np.array(fr)
    if k:
        op = img[..., 3] > 0
        img[..., :3][op] = quantize_rgb(img[..., :3][op], k)
    detalles(img, tema_nombre)
    return img, win


if __name__ == "__main__":
    import pesca
    from PIL import ImageDraw
    S = pesca.cargar(); bg = pesca.fondo("luna")
    capas = pesca.guion(S, 6)
    Z = 4
    sh = Image.new("RGB", (3 * 126 * Z + 20, 2 * 126 * Z + 10), (0, 0, 0))
    for i, nombre in enumerate(("muelle", "mar", "mixto")):
        img, win = build(nombre)
        fr126 = Image.fromarray(img, "RGBA").crop((1, 1, 127, 127))
        for r, t in enumerate((20, 44)):
            f = bg.copy(); f.alpha_composite(fr126); f.alpha_composite(capas[t])
            sh.paste(f.convert("RGB").resize((126 * Z, 126 * Z), Image.NEAREST), (i * (126 * Z + 10), r * (126 * Z + 10)))
    out = HERE / "salida"; out.mkdir(exist_ok=True)
    sh.save(out / "opciones_marco.png")
    print("listo")
