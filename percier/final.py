"""Percier completo: marco verde veneno (luna y estrellas, calabazas con ojos que brillan, telaraña), escenario de Halloween
con niebla baja, y la animación completa de Percier a x5. 72 pasos de 80 ms (5760 ms), bucle sin saltos.

Capas (de atrás hacia delante): negro -> escenario (recolor, niebla, calabaza y velas) -> Percier + nube -> marco (x8).
Escenario y Percier se componen a píxeles nativos (128x128) y se amplían juntos a x5, así miden lo mismo.
Los ciclos animados del marco y del escenario duran 12 pasos (o un divisor), y 72 = 6 ciclos, por eso enlazan.
Salida: percier_marco_halloween.gif y vistas previas.
"""
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import layout                                   # noqa: E402

# disposición para la ventana de 128 px a x5: Percier 10 px a la izquierda, nube 8 px más cerca, esperas más cortas (72 pasos)
layout.X_F, layout.AX = 80, 62
layout.DUR_A = ((0, 3), (1, 2), (2, 2), (3, 2), (4, 2), (5, 3), (6, 3), (7, 2))

import numpy as np                              # noqa: E402
from PIL import Image                           # noqa: E402

import completa                                 # noqa: E402
import fondo                                    # noqa: E402
import marcos2 as m2                            # noqa: E402

PREV = HERE / "previews"
TMP = Path("/projects/sandbox/tmp/percier")
TICK = 80


def pasos():
    return completa.parte_a() + completa.parte_b() + completa.parte_c() + completa.parte_d()


def main():
    frames = pasos()
    n = len(frames)
    print("pasos:", n, "=", n * TICK, "ms")
    assert n == 72
    lays = [f.crop((0, 0, 128, 128)) for f in frames]
    # nada de Percier fuera de la ventana por la derecha / izquierda
    fuera = sum(int((np.asarray(f)[:, 128:, 3] > 0).sum()) for f in frames)
    print("píxeles de Percier fuera de la ventana (derecha):", fuera)
    assert fuera == 0
    campo = fondo.campo_niebla()
    base_bg = fondo.ventana_base()
    escena = [fondo.escenario(t, True, campo, base_bg).convert("RGBA") for t in range(12)]
    # ventana de 640 px por paso
    ventanas = []
    for t in range(n):
        e = escena[t % 12].copy()
        e.alpha_composite(lays[t])
        ventanas.append(e.resize((640, 640), Image.NEAREST))
    km = 140
    while True:
        base = m2.marco_base(km)
        marcos = [m2.marco_t(base, "luna", t) for t in range(12)]
        out = [m2.componer(marcos[t % 12], ventanas[t]) for t in range(n)]
        arrs = [np.asarray(f) for f in out]
        key = lambda a: a[..., 0].astype(np.uint32) << 16 | a[..., 1].astype(np.uint32) << 8 | a[..., 2]
        cols = len(np.unique(np.concatenate([key(a).ravel() for a in arrs])))
        print(f"marco {km} tonos -> paleta {cols}")
        if cols <= 256:
            break
        km -= max(4, cols - 256)
    path = HERE / "percier_marco_halloween.gif"
    r = m2.guardar_gif(out, path, TICK)
    print(f"{path.name}: {n} pasos, {r} colores, marco {km} tonos, {path.stat().st_size / 1024 / 1024:.1f} MB")
    TMP.mkdir(parents=True, exist_ok=True)
    for t in (0, 12, 22, 40, 56, 63, 67):
        out[t].save(TMP / f"final_t{t}.png")
    # hoja de pasos clave (mitad de tamaño)
    sel = [0, 6, 14, 19, 23, 30, 45, 54, 58, 63, 66, 70]
    S = 4
    hoja = Image.new("RGB", (4 * 1024 // S * 1, 3 * 1024 // S * 1), (14, 10, 20))
    for i, t in enumerate(sel):
        hoja.paste(out[t].resize((1024 // S, 1024 // S), Image.LANCZOS), ((i % 4) * 1024 // S, (i // 4) * 1024 // S))
    hoja = hoja.resize((hoja.width * 2, hoja.height * 2), Image.LANCZOS)
    hoja.save(PREV / "percier_marco_halloween_pasos.png")
    print("hoja:", hoja.size)


if __name__ == "__main__":
    main()
