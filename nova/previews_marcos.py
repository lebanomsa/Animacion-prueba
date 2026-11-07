"""Vista previa de las tres opciones de marco con el bucle 3 de Nova (opción A: el rayo cruza el marco), fondo 'fondo.png' recortado, 48 pasos."""
from pathlib import Path
from PIL import Image
import maqueta_marco as m
import marco_nova as mn
import bucles_nova as b

HERE = Path(__file__).parent
OUT = HERE / "salida"
X0, Y0 = 68, 45          # recorte de 80x80 de fondo.png (suelo en las últimas 17 filas)


def main():
    fondo = Image.open(HERE / "fuentes/fondo.png").convert("RGBA").crop((X0, Y0, X0 + 80, Y0 + 80))
    for op in mn.PALETAS:
        ims = m.main(rayo_fuera=True, fondo=fondo, dy=-30, marco_fn=lambda t, op=op: mn.frame_126(op, t))
        b.gif_local(ims, OUT / f"marco_{op}_con_nova_x4.gif", b.TICK)
        idx = [4, 18, 26]
        s = Image.new("RGB", (504 * 3 + 20, 504), (30, 30, 30))
        for j, i in enumerate(idx): s.paste(ims[i], (j * 514, 0))
        s.save(OUT / f"marco_{op}_con_nova.png"); print(op, len(ims))


if __name__ == "__main__":
    main()
