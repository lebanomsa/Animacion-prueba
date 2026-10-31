"""Vista previa: marco verde veneno (luna y estrellas) + escenario de Halloween con niebla + Percier a x5 (nube más cerca).

Salidas en previews/: fondo_halloween_niebla.gif (12 pasos), fondo_halloween_sin_niebla.png, nube_cerca_comparacion.png
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import completa                 # noqa: E402
import fondo                    # noqa: E402
import marcos2 as m2            # noqa: E402

PREV = HERE / "previews"
BASE_BG = fondo.ventana_base()
CAMPO = fondo.campo_niebla()


def capa_percier(posar, x_f, ax, window=128):
    """Capa RGBA 128x128 de Percier con la nube, con la disposición (x_f, ax) elegida."""
    ant = completa.X_F, completa.AX
    completa.X_F, completa.AX = x_f, ax
    try:
        f = posar()
    finally:
        completa.X_F, completa.AX = ant
    return f.crop((0, 0, window, 128))


def ventana(t, niebla, percier_rgba):
    esc = fondo.escenario(t, niebla, CAMPO, BASE_BG).convert("RGBA")
    esc.alpha_composite(percier_rgba)
    return esc.resize((640, 640), Image.NEAREST)


def main():
    PREV.mkdir(exist_ok=True)
    cerca = capa_percier(lambda: completa.parte_b()[22], 81, 63)
    # --- GIF con niebla (12 pasos), marco cuantizado para que todo quepa en 256 colores
    km = 150
    while True:
        base = m2.marco_base(km)
        frs = [m2.componer(m2.marco_t(base, "luna", t), ventana(t, True, cerca)) for t in range(12)]
        arrs = [np.asarray(f) for f in frs]
        key = lambda a: a[..., 0].astype(np.uint32) << 16 | a[..., 1].astype(np.uint32) << 8 | a[..., 2]
        n = len(np.unique(np.concatenate([key(a).ravel() for a in arrs])))
        if n <= 256:
            break
        km -= 8
    r = m2.guardar_gif(frs, PREV / "fondo_halloween_niebla.gif")
    print(f"fondo_halloween_niebla.gif: {r} colores, marco {km} tonos, {(PREV / 'fondo_halloween_niebla.gif').stat().st_size / 1024:.0f} KB")
    # --- estáticas
    b = m2.marco_base()
    m2.componer(m2.marco_t(b, "luna", 0), ventana(0, False, cerca)).save(PREV / "fondo_halloween_sin_niebla.png")
    m2.componer(m2.marco_t(b, "luna", 0), ventana(0, True, cerca)).save(PREV / "fondo_halloween_con_niebla.png")
    # --- comparación de la nube: disposición anterior (se corta a x5) frente a la nube más cerca
    paneles = []
    for posar, nombre in ((lambda: completa.parte_b()[22], "reposo"), (lambda: completa.parte_a()[14], "pose ancha")):
        for (xf, ax) in ((90, 64), (81, 63)):
            p = capa_percier(posar, xf, ax)
            paneles.append(m2.componer(m2.marco_t(b, "luna", 0), ventana(0, False, p)).resize((512, 512), Image.LANCZOS))
    hoja = Image.new("RGB", (1024, 1024))
    for i, p in enumerate(paneles):
        hoja.paste(p, ((i % 2) * 512, (i // 2) * 512))
    hoja.save(PREV / "nube_cerca_comparacion.png")


if __name__ == "__main__":
    main()
