"""GIF final de Utena: traje, combinación de vergüenza (sonrojo + gotita + rayitas) y el corte del bucle tapado con el
'sonrojo total' (el cuerpo se pone rosa y un destello blanco tapa el cambio de pose). 32 pasos, 4,2 s, en bucle.
Lienzo de 120x140 (el sprite de 96x128 con margen para el destello).
Salida: utena_final.gif (x1), utena_final_x5.gif (600x700, transparente) y utena_final_x5_fondo.gif (fondo oscuro).
"""
from pathlib import Path

from PIL import Image, ImageDraw

import animacion
import efectos_bucle as eb

HERE = Path(__file__).parent


def main():
    fr, durs, paso, vis = eb.construir(eb.capa_sonrojo, True)
    print(f"{len(fr)} pasos, {sum(durs)} ms; píxeles de Utena a la vista en el cambio: {vis}")
    for esc, suf in ((1, ""), (5, "_x5")):
        ruta = HERE / f"utena_final{suf}.gif"
        n = animacion.guardar(fr, durs, ruta, esc)
        print(f"{ruta.name}: {fr[0].width * esc}x{fr[0].height * esc}, {n} colores, {ruta.stat().st_size / 1024:.0f} KB")
    ruta = HERE / "utena_final_x5_fondo.gif"
    n = animacion.guardar(fr, durs, ruta, 5, fondo=(46, 46, 56))
    print(f"{ruta.name}: {n} colores, {ruta.stat().st_size / 1024:.0f} KB")
    sel = [0, 3, 5, 6, 8, 20, 27, 29, 31, 1]
    S = 2
    w, h = fr[0].width * S, fr[0].height * S
    hoja = Image.new("RGB", (len(sel) * (w + 6), h + 20), (30, 30, 40))
    d = ImageDraw.Draw(hoja)
    for i, t in enumerate(sel):
        b = Image.new("RGBA", fr[t].size, (46, 46, 56, 255)); b.alpha_composite(fr[t])
        hoja.paste(b.convert("RGB").resize((w, h), Image.NEAREST), (i * (w + 6), 20))
        d.text((i * (w + 6) + 4, 4), f"paso {t + 1}", fill=(255, 230, 120))
    hoja.save(HERE / "previews" / "utena_final_pasos.png")


if __name__ == "__main__":
    main()
