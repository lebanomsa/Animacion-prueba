"""Propuestas de marco para Percier: el mismo marco personalizado (sin cambiar su diseño), recoloreado y con detalles de Halloween.

Detalles pixelados sobre la capa del marco: calabazas en las esquinas, murciélagos en el borde, telarañas en las esquinas
de la ventana y una araña colgando. Los colores salen de dos paletas por brillo (arriba y abajo), como los marcos anteriores.
Vista previa con Percier fijo (escala x4) sobre un fondo plano provisional.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "secuencia"))
import marco                    # noqa: E402
import completa                 # noqa: E402

PREV = HERE / "previews"
S_FRAME = 8
WIN = (24, 24, 103, 103)

PALETAS = {
    "violeta": (
        [(0.0, (18, 6, 36)), (0.3, (60, 28, 110)), (0.6, (112, 60, 176)), (0.85, (168, 118, 226)), (1.0, (232, 208, 255))],
        [(0.0, (6, 2, 14)), (0.3, (28, 10, 52)), (0.6, (60, 28, 100)), (0.85, (104, 64, 150)), (1.0, (180, 150, 220))]),
    "naranja": (
        [(0.0, (40, 12, 0)), (0.3, (150, 56, 4)), (0.6, (230, 110, 12)), (0.85, (255, 170, 50)), (1.0, (255, 232, 150))],
        [(0.0, (6, 2, 0)), (0.3, (28, 12, 4)), (0.6, (62, 30, 10)), (0.85, (110, 60, 24)), (1.0, (190, 120, 60))]),
    "verde": (
        [(0.0, (6, 28, 10)), (0.3, (20, 90, 30)), (0.6, (60, 160, 40)), (0.85, (150, 220, 70)), (1.0, (230, 255, 170))],
        [(0.0, (10, 2, 22)), (0.3, (40, 14, 70)), (0.6, (84, 36, 130)), (0.85, (134, 80, 180)), (1.0, (210, 170, 235))]),
    "hueso": (
        [(0.0, (40, 34, 24)), (0.3, (130, 116, 90)), (0.6, (200, 188, 158)), (0.85, (236, 226, 200)), (1.0, (255, 250, 236))],
        [(0.0, (8, 10, 18)), (0.3, (30, 36, 56)), (0.6, (64, 76, 106)), (0.85, (110, 126, 160)), (1.0, (186, 198, 222))]),
}

COL = {"k": (22, 12, 18), "O": (240, 140, 20), "o": (186, 88, 10), "h": (255, 196, 80), "y": (255, 232, 110),
       "g": (84, 170, 44), "G": (36, 100, 36), "r": (220, 40, 40), "w": (228, 228, 242)}

CALABAZA = [
    "....gg.....",
    "...kgGk....",
    "..kkkGkkk..",
    ".kOhOooOOk.",
    "kOhOOoOOOok",
    "kOyyOoOyyOk",
    "kOOyOoOyOOk",
    "koOyOyOyOok",
    "kooOyyyOook",
    ".kkkkkkkkk.",
]
MURCIELAGO = [
    "k.......k",
    "kk.k.k.kk",
    "kkkkkkkkk",
    ".k.kkk.k.",
    "..k...k..",
]
ARANA = [
    ".k...k.",
    "..kkk..",
    "kkkrkkk",
    "..kkk..",
    ".k...k.",
]


def dibujar(img, rows, x, y, flip_y=False, tinte=None):
    px = img.load()
    rr = rows[::-1] if flip_y else rows
    for j, row in enumerate(rr):
        for i, ch in enumerate(row):
            if ch != ".":
                px[x + i, y + j] = (*COL[ch], 255)


def dibujar_contorno(img, rows, x, y, flip_y=False, relleno=(22, 12, 18), contorno=(226, 214, 240), ojos=None):
    """Silueta con contorno claro de 1 px (para que se lea sobre las franjas oscuras del marco)."""
    px = img.load()
    rr = rows[::-1] if flip_y else rows
    celdas = {(x + i, y + j): ch for j, row in enumerate(rr) for i, ch in enumerate(row) if ch != "."}
    for (cx, cy) in celdas:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                q = (cx + dx, cy + dy)
                if q not in celdas and 0 <= q[0] < img.width and 0 <= q[1] < img.height:
                    px[q] = (*contorno, 255)
    for (cx, cy), ch in celdas.items():
        px[cx, cy] = (*(COL["r"] if ch == "r" else relleno), 255)


def telarana(img, esquina, largo=17):
    """Telaraña en una esquina de la ventana: 3 radios y 3 arcos."""
    x0, y0, x1, y1 = WIN
    cx, cy = {"tr": (x1, y0), "tl": (x0, y0), "br": (x1, y1), "bl": (x0, y1)}[esquina]
    sx = -1 if cx == x1 else 1
    sy = 1 if cy == y0 else -1
    d = ImageDraw.Draw(img)
    c = (*COL["w"], 255)
    rayos = [(sx, 0), (sx * 0.8, sy * 0.8), (0, sy)]
    for rr in rayos:
        d.line((cx, cy, cx + rr[0] * largo, cy + rr[1] * largo), fill=c)
    for r in (6, 11, 16):
        pts = [(cx + rr[0] * r, cy + rr[1] * r) for rr in rayos]
        m1 = ((pts[0][0] + pts[1][0]) / 2 - sx * 0, (pts[0][1] + pts[1][1]) / 2)
        m2 = ((pts[1][0] + pts[2][0]) / 2, (pts[1][1] + pts[2][1]) / 2)
        # los arcos se hunden un poco hacia la esquina
        m1 = (m1[0] - (m1[0] - cx) * 0.18, m1[1] - (m1[1] - cy) * 0.18)
        m2 = (m2[0] - (m2[0] - cx) * 0.18, m2[1] - (m2[1] - cy) * 0.18)
        d.line([pts[0], m1, pts[1], m2, pts[2]], fill=c)


def hilo_arana(img, x, largo=13):
    d = ImageDraw.Draw(img)
    d.line((x, WIN[1], x, WIN[1] + largo), fill=(*COL["w"], 255))
    dibujar_contorno(img, ARANA, x - 3, WIN[1] + largo, relleno=(120, 110, 140), contorno=(236, 232, 246))


def construir(nombre, detalles):
    top, bot = PALETAS[nombre]
    marco.recolor = marco.recolor    # (recolor estándar: degradado vertical por bandas)
    fr, _ = marco.build(top, bot)
    fr = fr.copy()
    if "calabazas" in detalles:
        for (x, y) in ((0, 0), (117, 0), (0, 118), (117, 118)):
            dibujar(fr, CALABAZA, x, y)
    if "calabazas_abajo" in detalles:
        for (x, y) in ((0, 118), (117, 118)):
            dibujar(fr, CALABAZA, x, y)
    if "murcielagos" in detalles:
        dibujar_contorno(fr, MURCIELAGO, 59, 1)
        dibujar_contorno(fr, MURCIELAGO, 59, 122, flip_y=True)
    for e in [d for d in detalles if d.startswith("tela_")]:
        telarana(fr, e[5:])
    if "arana" in detalles:
        hilo_arana(fr, 92)
    return fr


def escena():
    """Percier fijo (portrait de la nube) sobre un fondo plano provisional, a x4 en la ventana de 640 px."""
    f = completa.parte_b()[22]
    w, h = 139, 126
    f = f.crop((0, 0, w, h)).resize((w * 4, h * 4), Image.NEAREST)
    win = Image.new("RGBA", (640, 640), (28, 24, 48, 255))
    win.alpha_composite(f, ((640 - f.width) // 2, 640 - f.height - 8))
    return win


def componer(fr, escena_img, ruta):
    base = Image.new("RGBA", (1024, 1024), (0, 0, 0, 255))
    base.alpha_composite(escena_img, (WIN[0] * S_FRAME, WIN[1] * S_FRAME))
    base.alpha_composite(fr.resize((1024, 1024), Image.NEAREST))
    base.convert("RGB").save(ruta)
    return base.convert("RGB")


OPCIONES = [
    ("1_violeta_calabazas", "violeta", ["calabazas", "tela_tr", "tela_bl"]),
    ("2_naranja_noche", "naranja", ["murcielagos", "tela_tr", "tela_br", "arana"]),
    ("3_verde_veneno", "verde", ["calabazas_abajo", "tela_tr", "arana"]),
    ("4_hueso_y_ceniza", "hueso", ["calabazas", "murcielagos", "tela_tr"]),
]

if __name__ == "__main__":
    PREV.mkdir(exist_ok=True)
    esc = escena()
    imgs = []
    for nombre, pal, det in OPCIONES:
        fr = construir(pal, det)
        imgs.append(componer(fr, esc, PREV / f"marco_opcion_{nombre}.png"))
        print(nombre, pal, det)
    hoja = Image.new("RGB", (1024, 1024))
    for i, im in enumerate(imgs):
        hoja.paste(im.resize((512, 512), Image.LANCZOS), ((i % 2) * 512, (i // 2) * 512))
    hoja.save(PREV / "marco_opciones.png")
