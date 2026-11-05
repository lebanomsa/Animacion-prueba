"""Opciones de tamaño de Drache dentro del marco de siempre (504x504, ventana 320x320 en (92, 92)).
Todo el escenario (fondo + Drache + efectos) se amplía junto con el mismo factor, para que sus píxeles tengan el mismo tamaño.
Escala 1x = la versión actual. Con escalas mayores, la cabeza/cuernos pueden salir por delante del borde de arriba del marco."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).parent
import bucles as b
import entrega_stage as e
import marco_126 as mf

OUT = HERE / "opciones_tamano"
VW, WX, FLOOR_WIN, CXN, FLOORN = 320, 92, 306, 175, 300     # ventana, esquina, suelo dentro de la ventana, centro y suelo nativos
NH = 314                                                    # alto nativo (suelo + 14 px)
TIEMPO = 50
NATIVO_SPRITE = []


def nativo():
    b.W, b.H, b.CX, b.SUELO = 380, 330, CXN, FLOORN
    e.X0, e.W, e.H, e.SUELO = 1500, 380, NH, FLOORN
    R = b.cargar()
    ticks = b.guion_bucle1(R)
    capas = [c.crop((0, 0, 380, NH)) for c in b.dibujar_ticks_bucle1(ticks, R)]
    # solo Drache (sin polvo, pepitas ni bola de fuego): es lo único que puede salir por delante del marco
    solo = [dict(t, fase="vic") for t in ticks]
    for t in solo: t.pop("polvo", None); t.pop("pepitas", None)
    NATIVO_SPRITE[:] = [c.crop((0, 0, 380, NH)) for c in b.dibujar_ticks_bucle1(solo, R)]
    bg = Image.fromarray(e.agrupar(np.asarray(e.con_sombra(e.fondo_rgb())), e.K_FONDO)).convert("RGBA")
    return bg, capas


def escalar(im, s):
    return im.resize((round(im.width * s), round(im.height * s)), Image.NEAREST)


def escena(bg, capas, s):
    """(fondo de la ventana 320x320, [capas de 504x504 con Drache y efectos])."""
    cx, fl = round(CXN * s), round(FLOORN * s)
    bgs = escalar(bg, s)
    fondo = bgs.crop((cx - VW // 2, fl - FLOOR_WIN, cx + VW // 2, fl - FLOOR_WIN + VW))
    caps = [escalar(c, s).crop((cx - (WX + VW // 2), fl - (WX + FLOOR_WIN), cx - (WX + VW // 2) + 504, fl - (WX + FLOOR_WIN) + 504)) for c in capas]
    return fondo, caps


def mascaras():
    dentro = np.zeros((504, 504), bool); dentro[WX:WX + VW, WX:WX + VW] = True
    sobre = np.zeros((504, 504), bool); sobre[:WX, 150:354] = True          # franja de arriba, solo sobre el cuerpo de Drache
    return dentro, sobre


def aplicar(lz, m):
    a = np.array(lz); a[~m] = 0
    return Image.fromarray(a, "RGBA")


def componer(f4, fondo, lz, dentro, sobre, lz_sprite=None):
    c = Image.new("RGBA", f4.size, (0, 0, 0, 255)); c.paste(fondo, (WX, WX))
    c.alpha_composite(aplicar(lz, dentro)); c.alpha_composite(f4); c.alpha_composite(aplicar(lz if lz_sprite is None else lz_sprite, sobre))
    return c.convert("RGB")


def main():
    OUT.mkdir(exist_ok=True)
    img, _ = mf.build(k=40)
    f4 = Image.fromarray(img, "RGBA").crop((1, 1, 127, 127)).resize((504, 504), Image.NEAREST)
    bg, capas = nativo()
    a = np.asarray(capas[36])[..., 3]; ys = np.where((a > 0).any(1))[0]
    print("Drache en reposo (paso 36): alto nativo", ys.max() - ys.min() + 1, "px")
    dentro, sobre = mascaras()
    ticks = [8, 46, 58]
    peq = {}
    for s in (1.0, 1.5, 1.75, 2.0):
        fondo, caps = escena(bg, capas, s)
        ims = [componer(f4, fondo, caps[t], dentro, sobre) for t in ticks]
        hoja = Image.new("RGB", (504 * 3 + 20, 504), (30, 30, 30))
        for i, im in enumerate(ims): hoja.paste(im, (i * 514, 0))
        nombre = f"tamano_{str(s).replace('.', '_')}x"
        hoja.save(OUT / f"{nombre}_504.png")
        peq[s] = ims[2].resize((126, 126), Image.BOX)
        print(nombre, "Drache mide ~", round((ys.max() - ys.min() + 1) * s), "px en 504 y ~", round((ys.max() - ys.min() + 1) * s / 4), "px en 126")
    comp = Image.new("RGB", (4 * 504 + 30, 504), (30, 30, 30))
    for i, s in enumerate(peq):
        comp.paste(peq[s].resize((504, 504), Image.NEAREST), (i * 514, 0))
    comp.save(OUT / "comparacion_126_ampliada.png")


if __name__ == "__main__":
    main()
