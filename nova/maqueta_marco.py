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


def main(nova_x=72, ventana_color=(32, 34, 44, 255)):
    b.FONDO = b.SUELO_COL = (0, 0, 0, 0)
    b.NOVA_X = nova_x
    r = b.cargar()
    fr, win = marco.build()
    marco_im = fr.crop((1, 1, 127, 127))
    pasos = b.guion3(r)
    ims = []
    for n, tm, c in pasos:
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
        base = Image.new("RGBA", (126, 126), (0, 0, 0, 255)); base.paste(Image.new("RGBA", (VN, VN), ventana_color), (VX, VY))
        base.alpha_composite(recortar(cap_g, dentro)); base.alpha_composite(recortar(nova_g, dentro))
        base.alpha_composite(marco_im)
        base.alpha_composite(recortar(cap_g, ~dentro))      # el sombrero de la cápsula asoma por delante del marco
        ims.append(base.convert("RGB").resize((504, 504), Image.NEAREST))
    return ims


if __name__ == "__main__":
    ims = main()
    idx = [0, 5, 9, 13, 17, 25]
    s = Image.new("RGB", (504 * 3 + 20, 504 * 2 + 10), (30, 30, 30))
    for j, i in enumerate(idx):
        s.paste(ims[i], ((j % 3) * 514, (j // 3) * 514))
    s.save(OUT / "maqueta_marco_bucle3.png"); print("ok", s.size)
