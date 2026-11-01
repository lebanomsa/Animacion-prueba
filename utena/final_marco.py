"""GIF final de Utena: animación con el traje, la vergüenza y el sonrojo total, en el marco morado->dorado en diagonal,
con el fondo de la oficina de noche. 32 pasos, 4,2 s, en bucle, 1024x1024.
Paleta: el sprite de Utena y el fondo con sus colores exactos si caben; el marco y los tonos intermedios del sonrojo se
agrupan solo lo necesario para no pasar de 256.
"""
from pathlib import Path

import numpy as np
from PIL import Image

import fondos
import marco_utena as mu

HERE = Path(__file__).parent


def main():
    raw = {t: fondos.oficina(t) for t in range(32)}
    n_bg = len(np.unique(np.concatenate([np.asarray(f.convert("RGB")).reshape(-1, 3) for f in raw.values()]), axis=0))
    print("colores del fondo:", n_bg)
    for k_tinte, k_fondo in ((48, None), (32, None), (24, 48)):
        fondo = raw if k_fondo is None else fondos.cuantizar(raw, k_fondo)
        pers, durs = mu.animacion_utena(k_tinte)
        ventanas = [mu.ventana(p, fondo[t % 32]) for t, p in enumerate(pers)]
        km = 120
        while km >= 40:
            base = mu.marco_base(km)
            marcos = []
            for t in range(mu.CICLO):
                m = base.copy(); mu.detalles(m, t); marcos.append(m)
            frames = [mu.componer(marcos[i % mu.CICLO], v) for i, v in enumerate(ventanas)]
            ruta = HERE / "utena_marco_final.gif"
            n = mu.guardar(frames, durs, ruta)
            print(f"tinte {k_tinte}, fondo {k_fondo}, marco {km} tonos -> {n} colores")
            if n <= 256:
                print(f"{ruta.name}: {len(frames)} pasos, {sum(durs)} ms, {ruta.stat().st_size / 1024 / 1024:.1f} MB")
                frames[0].save(HERE / "previews" / "utena_marco_final.png")
                hoja = Image.new("RGB", (4 * 512, 2 * 512))
                for i, t in enumerate((0, 3, 4, 6, 14, 24, 28, 30)):
                    hoja.paste(frames[t].resize((512, 512), Image.LANCZOS), ((i % 4) * 512, (i // 4) * 512))
                hoja.save(HERE / "previews" / "utena_marco_final_pasos.png")
                return
            km -= max(4, n - 256)
    raise SystemExit("no cabe en 256 colores")


if __name__ == "__main__":
    main()
