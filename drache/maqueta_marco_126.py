"""Maqueta: Drache dentro del marco de siempre (secuencia/marco.py, rejilla 128 -> lienzo 126 -> x4 = 504).
La ventana del marco es de 80x80 px de 126 (320x320 en 504). Aquí la escena va a resolución nativa de Drache (1x) dentro de esa ventana.
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "secuencia"))
import marco
import bucles as b
import entrega_stage as e

OUT = HERE / "maqueta_126"
Z = 4
VW = 320                       # ventana en px de 504

TIERRA = [(0.0, (8, 5, 4)), (0.3, (34, 20, 12)), (0.6, (82, 50, 28)), (0.85, (140, 92, 48)), (1.0, (214, 170, 98))]
ORO = [(0.0, (30, 16, 4)), (0.3, (92, 56, 8)), (0.6, (170, 112, 12)), (0.85, (232, 176, 32)), (1.0, (255, 232, 140))]
VIOLETA = [(0.0, (10, 4, 24)), (0.3, (36, 18, 70)), (0.6, (76, 48, 124)), (0.85, (122, 90, 172)), (1.0, (196, 170, 236))]


def escena(tick):
    b.W, b.H, b.CX, b.SUELO = VW, VW, 160, 306
    e.X0, e.W, e.H, e.SUELO = 1515, VW, VW, 306
    R = b.cargar()
    capas = b.dibujar_ticks_bucle1(b.guion_bucle1(R), R)
    bg = Image.fromarray(e.agrupar(np.asarray(e.con_sombra(e.fondo_rgb())), e.K_FONDO)).convert("RGBA")
    out = []
    for t in tick:
        c = bg.copy(); c.alpha_composite(capas[t]); out.append(c)
    return out


def componer(esc, top, bot):
    fr, (x0, y0, x1, y1) = marco.build(top, bot)
    f4 = fr.crop((1, 1, 127, 127)).resize((126 * Z, 126 * Z), Image.NEAREST)
    wx, wy = (x0 - 1) * Z, (y0 - 1) * Z
    assert (x1 - x0 + 1) * Z == VW and (y1 - y0 + 1) * Z == VW, (x0, x1, y0, y1)
    lienzo = Image.new("RGBA", f4.size, (0, 0, 0, 255))
    lienzo.paste(esc, (wx, wy)); lienzo.alpha_composite(f4)
    return lienzo.convert("RGB")


def main():
    OUT.mkdir(exist_ok=True)
    ticks = [8, 58]
    es = escena(ticks)
    for nombre, (top, bot) in {"tierra_oro": (TIERRA, ORO), "violeta_oro": (VIOLETA, ORO)}.items():
        ims = [componer(s, top, bot) for s in es]
        ims_126 = [i.resize((126, 126), Image.BOX) for i in ims]
        hoja = Image.new("RGB", (504 * 2 + 10 + 126 * 4 + 10, 504), (30, 30, 30))
        hoja.paste(ims[0], (0, 0)); hoja.paste(ims[1], (514, 0))
        hoja.paste(ims_126[0].resize((504, 504), Image.NEAREST).crop((0, 0, 504, 504)).resize((504, 504)), (0, 0)) if False else None
        hoja.save(OUT / f"maqueta_{nombre}_504.png")
        pequ = Image.new("RGB", (126 * 2 * 4 + 10, 126 * 4), (30, 30, 30))
        pequ.paste(ims_126[0].resize((504, 504), Image.NEAREST), (0, 0)); pequ.paste(ims_126[1].resize((504, 504), Image.NEAREST), (514, 0))
        pequ.save(OUT / f"maqueta_{nombre}_126_ampliado.png")
        print(nombre, ims[0].size)

if __name__ == "__main__":
    main()
