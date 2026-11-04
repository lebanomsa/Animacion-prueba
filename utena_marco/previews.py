"""Previews del marco de Utena (morado arriba -> dorado abajo) con lunas de fases en pixel art.

Salida (en /projects/sandbox/tmp/ref_marco y utena_marco/previews): degradados y ubicaciones de las lunas, con la animación dentro.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "utena_transformacion")); sys.path.insert(0, str(HERE.parent / "utena_hechizo"))
import marco_base as mb       # noqa: E402
import luna as lu             # noqa: E402
import transformacion as tr   # noqa: E402
import hechizo as hz          # noqa: E402

PREV = HERE / "previews"; PREV.mkdir(exist_ok=True)
GEMAS = [(18, 18), (109, 18), (18, 109), (109, 109)]          # círculos de las esquinas del marco (coordenadas de 128x128)


def poner_luna(img, fase, r, cx, cy):
    m = np.asarray(lu.luna(fase, r))
    h = m.shape[0]
    y0, x0 = cy - h // 2, cx - h // 2
    for y in range(h):
        for x in range(h):
            if m[y, x, 3] and 0 <= y0 + y < 128 and 0 <= x0 + x < 128 and img[y0 + y, x0 + x, 3] > 0:
                img[y0 + y, x0 + x, :3] = m[y, x, :3]


def marco_con_lunas(estilo, colocacion, t=0, total=40):
    img, win = mb.build(estilo)
    p0 = (0.5 + t / float(total)) % 1.0                      # llena -> nueva -> llena a lo largo del bucle
    if colocacion == "esquinas":                             # las cuatro, en la misma fase
        for (x, y) in GEMAS:
            poner_luna(img, p0, 4, x, y)
    elif colocacion == "escalonadas":                        # cada esquina va un cuarto de ciclo por delante de la anterior
        for k, (x, y) in enumerate(GEMAS):
            poner_luna(img, (p0 + 0.25 * [0, 1, 3, 2][k]) % 1.0, 4, x, y)
    elif colocacion == "grande":                             # una luna grande en la esquina de arriba a la izquierda
        poner_luna(img, p0, 6, 15, 15)
        for (x, y) in GEMAS[1:]:
            pass
    return img, win


def escena(t):
    """(imagen 126x126 con escenario + personaje, máscara del personaje y efectos) para el paso t de la transformación."""
    nat, _, _ = hz.recuperar()
    spr, bg, bg_peq = hz.capas_base(nat)
    A = _frames[t]
    B = bg_peq if t in (21, 22, 23) else bg
    A = np.asarray(A).astype(int)
    mask = (np.abs(A - B.astype(int)).sum(-1) > 0)
    up = lambda a: np.repeat(np.repeat(a, 2, axis=0), 2, axis=1)
    return up(A.astype(np.uint8)), up(mask)


def componer(img128, t):
    fr = Image.fromarray(img128, "RGBA").crop((1, 1, 127, 127))
    esc, mask = escena(t)
    out = Image.fromarray(esc, "RGB").convert("RGBA")
    out.alpha_composite(fr)
    ch = Image.fromarray(np.dstack([esc, (mask * 255).astype(np.uint8)]), "RGBA")      # personaje por delante del marco
    out.alpha_composite(ch)
    return out.convert("RGB")


_frames = None


def main():
    global _frames
    _frames = tr.main()
    Z = 4
    # 1) degradados
    sh = Image.new("RGB", (3 * 126 * Z + 20, 126 * Z), (0, 0, 0))
    for i, est in enumerate(("suave", "bandas", "corte")):
        img, _ = marco_con_lunas(est, "esquinas", t=0)
        sh.paste(componer(img, 21).resize((126 * Z, 126 * Z), Image.NEAREST), (i * (126 * Z + 10), 0))
    sh.save(PREV / "degradados.png")
    # 2) lunas
    sh = Image.new("RGB", (3 * 126 * Z + 20, 126 * Z), (0, 0, 0))
    for i, col in enumerate(("esquinas", "escalonadas", "grande")):
        img, _ = marco_con_lunas("bandas", col, t=10)
        sh.paste(componer(img, 2).resize((126 * Z, 126 * Z), Image.NEAREST), (i * (126 * Z + 10), 0))
    sh.save(PREV / "lunas.png")
    print("listo")


if __name__ == "__main__":
    main()
