"""Maqueta: bucle 3 de Nova dentro del marco de siempre (rejilla de 126, ventana de 80x80), para comprobar si cabe.
Nova y cápsula se acercan (Nova delante del borde derecho de la cápsula); el sombrero de la cápsula puede asomar por delante de la banda de arriba."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "secuencia"))
import marco
import bucles_nova as b

OUT = HERE / "salida"
VX, VY, VN = 23, 23, 80          # ventana en la rejilla de 126 (el marco de 128 recortado 1 px por lado)
DX, DY = -13, -28                # escena -> ventana (capsula+Nova centradas, suelo a 3 px del borde de abajo)


def main(nova_x=72, ventana_color=(32, 34, 44, 255), rayo_fuera=False, fondo=None, dy=None, marco_im=None, marco_fn=None, modo=None, piezas=None):
    b.FONDO = b.SUELO_COL = (0, 0, 0, 0)
    b.NOVA_X = nova_x
    r = b.cargar()
    global DY
    if dy is not None: DY = dy
    if marco_im is None and marco_fn is None:
        fr, win = marco.build()
        marco_im = fr.crop((1, 1, 127, 127))
    pasos = b.guion3(r, modo=modo)
    ims = []
    for t, (n, tm, c) in enumerate(pasos):
        if callable(marco_fn): marco_im = marco_fn(t)
        cap_l = b.escena(None, r.cap[c])
        nova_l = b.escena(n, None, timor=tm)
        # mover de la escena (176x112) a la rejilla de 126: la posición (sx, sy) de la escena cae en (sx + DX + VX, sy + DY + VY)
        def a_rejilla(lz):
            g = Image.new("RGBA", (126, 126), (0, 0, 0, 0))
            g.alpha_composite(lz, (DX + VX, DY + VY)) if (DX + VX) >= 0 and (DY + VY) >= 0 else g.paste(lz.crop((max(0, -(DX + VX)), max(0, -(DY + VY)), lz.width, lz.height)), (max(0, DX + VX), max(0, DY + VY)))
            return g
        cap_g, nova_g = a_rejilla(cap_l), a_rejilla(nova_l)
        dentro = np.zeros((126, 126), bool); dentro[VY:VY + VN, VX:VX + VN] = True
        def recortar(g, m):
            a = np.array(g); a[~m] = 0; return Image.fromarray(a, "RGBA")
        base = Image.new("RGBA", (126, 126), (0, 0, 0, 255)); base.paste(Image.new("RGBA", (VN, VN), ventana_color) if fondo is None else fondo, (VX, VY))
        base.alpha_composite(recortar(cap_g, dentro)); base.alpha_composite(recortar(nova_g, dentro))
        base.alpha_composite(marco_im)
        base.alpha_composite(recortar(cap_g, ~dentro))      # el sombrero de la cápsula asoma por delante del marco
        if rayo_fuera:                                        # el rayo (y la esfera) atraviesan la banda derecha del marco
            franja = np.zeros((126, 126), bool); franja[VY + 10:VY + 62, VX + VN:] = True
            base.alpha_composite(recortar(nova_g, franja))
        if piezas is not None:
            # capa de abajo (fondo + marco) y capa de arriba (cápsula + Nova + efectos, con transparencia parcial en el cristal)
            fm = Image.new("RGBA", (126, 126), (0, 0, 0, 255)); fm.paste(Image.new("RGBA", (VN, VN), ventana_color) if fondo is None else fondo, (VX, VY)); fm.alpha_composite(marco_im)
            sup = Image.new("RGBA", (126, 126), (0, 0, 0, 0)); sup.alpha_composite(cap_g)
            permitido = dentro | (franja if rayo_fuera else np.zeros((126, 126), bool))
            sup.alpha_composite(recortar(nova_g, permitido))
            piezas.append(dict(final=base.convert("RGB"), fondo_marco=fm, sup=sup))
        ims.append(base.convert("RGB").resize((504, 504), Image.NEAREST))
    return ims


if __name__ == "__main__":
    idx = [14, 17, 19, 22]
    for nombre, kw in {"A_rayo_cruza_el_marco": dict(rayo_fuera=True), "B_rayo_cruza_y_Nova_mas_a_la_izquierda": dict(rayo_fuera=True, nova_x=58)}.items():
        ims = main(**kw)
        s = Image.new("RGB", (504 * 2 + 10, 504 * 2 + 10), (30, 30, 30))
        for j, i in enumerate(idx):
            s.paste(ims[i], ((j % 2) * 514, (j // 2) * 514))
        s.save(OUT / f"opcion_rayo_{nombre}.png"); print(nombre, s.size)
