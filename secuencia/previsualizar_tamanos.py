"""Vistas previas de distintos tamaños del personaje de la animación de victoria dentro del marco.

Cada opción define la escala del personaje, la del fondo y qué zona del fondo se ve en la ventana
(la ventana mide 640x640 px, así que a escala s se ven 640/s filas y columnas del fondo).
Salida: previews/tamanos_victoria.png (filas = opciones, columnas = fotogramas 4, 9 y 13).
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "victoria"))
import make_victoria as mv      # noqa: E402
import marco                    # noqa: E402

S_FRAME = 8
FRAMES = (3, 8, 12)             # fotogramas 4, 9 y 13: explosión azul, rosa y amarilla
# nombre, escala del personaje, escala del fondo, fila del fondo donde empieza el recorte, apoyo de los pies
OPCIONES = [
    ("Actual: personaje x3, fondo x3", 3, 3, 30, 556),
    ("A: personaje x4, fondo x4", 4, 4, 80, 556),
    ("B: personaje x5, fondo x5", 5, 5, 100, 622),
    ("C: personaje x4, fondo x3 (píxeles distintos)", 4, 3, 30, 556),
]


def componer(sc, sf, fy, feet, cells, frame_big, win, fondo):
    win_x, win_y, win_w, win_h = win
    n = win_w // sf                                   # filas y columnas del fondo visibles
    fx = (fondo.width - n) // 2
    crop = fondo.crop((fx, fy, fx + n, fy + n)).resize((n * sf, n * sf), Image.NEAREST)
    base = Image.new("RGBA", frame_big.size, (0, 0, 0, 255))
    base.alpha_composite(crop.convert("RGBA"), (win_x, win_y))
    out = []
    for k in FRAMES:
        img = base.copy()
        c = cells[k]
        big = c.resize((c.width * sc, c.height * sc), Image.NEAREST)
        ax = win_x + (win_w - big.width) // 2
        ay = win_y + feet - big.height
        assert win_y <= ay and ay + big.height <= win_y + win_h, (sc, ay, big.height)
        img.alpha_composite(big, (ax, ay))
        img.alpha_composite(frame_big)
        out.append(img.convert("RGB"))
    return out


def main():
    frame, (x0, y0, x1, y1) = marco.build()
    frame_big = frame.resize((marco.N * S_FRAME,) * 2, Image.NEAREST)
    win = (x0 * S_FRAME, y0 * S_FRAME, (x1 - x0 + 1) * S_FRAME, (y1 - y0 + 1) * S_FRAME)
    cells = mv.cells()
    fondo = Image.open(ROOT / "fondo 2.PNG").convert("RGB")
    W, T = 512, 18
    sheet = Image.new("RGB", (W * len(FRAMES), (W + T) * len(OPCIONES)), (20, 10, 14))
    d = ImageDraw.Draw(sheet)
    for r, (nombre, sc, sf, fy, feet) in enumerate(OPCIONES):
        d.text((6, r * (W + T) + 4), f"{nombre}  |  personaje {cells[0].width * sc}x{cells[0].height * sc} px"
               f", fondo visible {win[2] // sf}x{win[3] // sf} px del original", fill=(255, 255, 255))
        for c, img in enumerate(componer(sc, sf, fy, feet, cells, frame_big, win, fondo)):
            sheet.paste(img.resize((W, W), Image.NEAREST), (c * W, r * (W + T) + T))
    out = HERE / "previews"; out.mkdir(exist_ok=True)
    sheet.save(out / "tamanos_victoria.png")
    print("ok ->", out / "tamanos_victoria.png", sheet.size)


if __name__ == "__main__":
    main()
