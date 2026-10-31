"""Vista previa de los dos fondos pixel art con Rem (opción 1: idle + círculo mágico)."""
from pathlib import Path

import numpy as np
from PIL import Image

import fondos
import previas

PREV = Path(__file__).parent / "previews"


def main():
    hoja = Image.new("RGB", (2 * 480, 3 * 480), (14, 10, 20))
    for i, (nombre, fn) in enumerate((("bosque_nevado", fondos.bosque), ("salon_mansion", fondos.salon))):
        cache = {}

        def bg(t, fn=fn, cache=cache):
            return fondos.a_float(fn(t % 24))

        fr = previas.op1(bg)
        ruta = PREV / f"rem_fondo_{nombre}.gif"
        previas.gif(fr, ruta)
        print(f"{ruta.name}: {len(fr)} pasos, {ruta.stat().st_size / 1024:.0f} KB")
        fondos.bosque if False else None
        for j, t in enumerate((0, 8, 16)):
            hoja.paste(fr[t].resize((480, 480), Image.LANCZOS), (i * 480, j * 480))
        fondos_solo = fn(6).resize((640, 640), Image.NEAREST)
        fondos_solo.save(PREV / f"rem_fondo_{nombre}_solo.png")
    hoja.save(PREV / "rem_fondos_comparacion.png")


if __name__ == "__main__":
    main()
