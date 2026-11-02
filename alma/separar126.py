"""Versión 126x126 de Alma: marco + fondo y animación por separado.

El marco se usa a su resolución nativa (128x128, recortando 1 px por cada lado -> 126x126), así que sus líneas quedan intactas.
La ventana de 640 px (escenario + Alma) se reduce a 80x80, es decir, cada píxel nuevo promedia 2x2 píxeles del dibujo original.
Alma va por detrás del marco. En la capa de animación el borde de Alma es de 1 bit (GIF no admite semitransparencia).

  marco_y_fondo_alma_126.gif / .png   126x126, 67 pasos de 70 ms
  alma_animacion_126.gif              126x126 transparente, en su sitio (se pone encima de marco_y_fondo_alma_126.gif)
  alma_marco_azul_oro_126.gif         el resultado juntos (referencia): es exactamente (marco+fondo) + animación

Uso:  python separar126.py [lanczos|box]
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import separar as sp                                   # noqa: E402
from separar import ca, an, quantize_rgb, TICK, key, gif_opaco, gif_transparente, por_paso   # noqa: E402

OUT = HERE / "salida_separada"
WIN, WX = 80, 24          # ventana nativa 80x80 en (24, 24) del marco de 128x128
CROP = (1, 1, 127, 127)
K_MARCO, K_ESC, K_ALMA = 96, 112, 44


def main(modo="lanczos"):
    OUT.mkdir(exist_ok=True)
    res = Image.LANCZOS if modo == "lanczos" else Image.BOX
    P = sp.preparar()
    S, win, L = P["S"], P["win"], P["L"]
    assert win == WIN * 8
    idx = ca.reparto_estrellas(L)

    # marco nativo, tonos agrupados
    mb = np.asarray(P["marco_big"].resize((128, 128), Image.NEAREST))
    op = mb[..., 3] > 0
    mq = mb[..., :3].copy(); mq[op] = quantize_rgb(mb[..., :3][op], K_MARCO)
    marco_nat = Image.fromarray(np.dstack([mq, mb[..., 3]]), "RGBA")
    tapa = np.asarray(marco_nat)[..., 3] > 0

    # escenario 640 -> 80, tonos agrupados entre los 9 fotogramas del cielo
    esc = [np.asarray(Image.fromarray(b, "RGB").resize((WIN, WIN), res)) for b in P["big"]]
    flat = quantize_rgb(np.concatenate([e.reshape(-1, 3) for e in esc]), K_ESC)
    esc = [flat[i * WIN * WIN:(i + 1) * WIN * WIN].reshape(WIN, WIN, 3) for i in range(len(esc))]

    # Alma 640 -> 80 (con alfa premultiplicado), alfa a 1 bit
    capas = []
    for t in range(L):
        lay = Image.new("RGBA", (win, win), (0, 0, 0, 0))
        a = P["alma"][t].resize((P["aw"] * S, P["ah"] * S), Image.NEAREST)
        an.paste_clip(lay, a, P["ax"], P["ay"])
        capas.append(np.asarray(lay.resize((WIN, WIN), res)).copy())
    solid = [c[..., 3] >= 128 for c in capas]
    allp = np.concatenate([c[..., :3][s] for c, s in zip(capas, solid)])
    flat = quantize_rgb(allp, K_ALMA)
    pos = 0
    for c, s in zip(capas, solid):
        n = int(s.sum()); c[..., :3][s] = flat[pos:pos + n]; pos += n
        c[..., 3] = np.where(s, 255, 0)
        c[..., :3][~s] = 0

    # composición por capas (126x126)
    def lienzo(rgb_esc):
        base = Image.new("RGBA", (128, 128), (0, 0, 0, 255))
        base.alpha_composite(Image.fromarray(rgb_esc, "RGB").convert("RGBA"), (WX, WX))
        return base
    fondo, anim, junto = [], [], []
    for t in range(L):
        b = lienzo(esc[idx[t]])
        f = b.copy(); f.alpha_composite(marco_nat)
        fondo.append(f.crop(CROP))
        lay = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
        lay.alpha_composite(Image.fromarray(capas[t], "RGBA"), (WX, WX))
        arr = np.array(lay); arr[tapa] = 0
        lay = Image.fromarray(arr, "RGBA")
        anim.append(lay.crop(CROP))
        j = b.copy(); j.alpha_composite(Image.fromarray(capas[t], "RGBA"), (WX, WX)); j.alpha_composite(marco_nat)
        junto.append(j.crop(CROP))

    cols = len(np.unique(np.concatenate([key(np.asarray(j.convert("RGB"))).ravel() for j in junto])))
    print(f"modo {modo}: marco {K_MARCO}, escenario {K_ESC}, Alma {K_ALMA} -> {cols} colores en el resultado junto")
    assert cols <= 256
    gif_opaco(junto, OUT / "alma_marco_azul_oro_126.gif", TICK)
    n = gif_opaco(fondo, OUT / "marco_y_fondo_alma_126.gif", TICK)
    fondo[0].convert("RGB").save(OUT / "marco_y_fondo_alma_126.png")
    na = gif_transparente(anim, OUT / "alma_animacion_126.gif", TICK)
    for r in ("alma_marco_azul_oro_126.gif", "marco_y_fondo_alma_126.gif", "alma_animacion_126.gif"):
        print(f"  {r}: {Image.open(OUT / r).size}, {(OUT / r).stat().st_size / 1024:.0f} KB")

    # comprobación: marco+fondo + animación == resultado junto
    fon = por_paso(OUT / "marco_y_fondo_alma_126.gif", L, TICK)
    sola = por_paso(OUT / "alma_animacion_126.gif", L, TICK)
    jun = por_paso(OUT / "alma_marco_azul_oro_126.gif", L, TICK)
    dif = 0
    for t in range(L):
        c = fon[t].copy(); c.alpha_composite(sola[t])
        dif += int((np.abs(np.asarray(c.convert("RGB")).astype(int) - np.asarray(jun[t].convert("RGB")).astype(int)).sum(-1) > 0).sum())
    print("píxeles distintos (marco+fondo + animación) vs resultado junto:", dif)

    # vistas previas a 6x
    prev = Path("/projects/sandbox/tmp/alma_sep"); prev.mkdir(parents=True, exist_ok=True)
    sh = Image.new("RGB", (126 * 6 * 3, 126 * 6), (60, 60, 60))
    for i, t in enumerate((0, 30, 59)):
        sh.paste(jun[t].convert("RGB").resize((756, 756), Image.NEAREST), (i * 756, 0))
    sh.save(prev / f"alma126_{modo}.png")
    ch = Image.new("RGBA", (756, 756))
    sq = 21
    for yy in range(0, 756, sq):
        for xx in range(0, 756, sq):
            ch.paste(((200, 200, 200, 255) if (xx // sq + yy // sq) % 2 else (150, 150, 150, 255)), (xx, yy, xx + sq, yy + sq))
    ch.alpha_composite(sola[30].resize((756, 756), Image.NEAREST))
    ch.save(prev / f"alma126_anim_{modo}.png")


if __name__ == "__main__":
    main(*(sys.argv[1:2]))
