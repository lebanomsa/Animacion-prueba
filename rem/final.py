"""Rem completa: idle + círculo mágico (opción 1) sobre el bosque nevado con aurora, dentro del marco 'aurora de medianoche'.

24 pasos de 80 ms (1920 ms), bucle sin saltos: idle de 4 fotogramas x 3 pasos, círculo que late (12), ondas (12), chispas y nieve (24), aurora (24).
Capas: bosque 160x160 a x4 + Rem y efectos (ventana de 640 px, cuantizada en conjunto) -> marco (x8, cuantizado) con detalles de colores exactos.
La franja de luz y las gemas usan 8 pasos de color (en vez de un degradado continuo) para caber en 256 colores.
Salida: rem_marco_aurora.gif y una hoja de pasos.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import marcos as mk             # noqa: E402
import marco                    # noqa: E402
import fondos                   # noqa: E402
import previas                  # noqa: E402

PREV = HERE / "previews"
N = 24
_orig = mk.color_aurora
mk.color_aurora = lambda u: _orig(round(u * 8) / 8)


def cuantizar_ventanas(frames, k):
    mosaico = Image.fromarray(np.concatenate([np.asarray(f)[::2, ::2] for f in frames], axis=0))
    q = mosaico.quantize(colors=k, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    return [f.quantize(palette=q, dither=Image.Dither.NONE).convert("RGB") for f in frames]


def main():
    ventanas = previas.op1(lambda t: fondos.a_float(fondos.bosque(t % 24)))
    assert len(ventanas) == N
    top, bot = mk.P3
    f0, _ = marco.build(top, bot)
    f0 = f0.copy()
    kw, km = 160, 90
    while True:
        vq = cuantizar_ventanas(ventanas, kw)
        a = np.array(f0); op = a[..., 3] > 0
        a[..., :3][op] = mk.quantize_rgb(a[..., :3][op], km)
        base = Image.fromarray(a, "RGBA")
        out = []
        for t in range(N):
            fr = base.copy(); mk.det3(fr, t)
            img = Image.new("RGBA", (1024, 1024), (0, 0, 0, 255))
            img.alpha_composite(vq[t].convert("RGBA"), (192, 192))
            img.alpha_composite(fr.resize((1024, 1024), Image.NEAREST))
            out.append(img.convert("RGB"))
        arrs = [np.asarray(f) for f in out]
        key = lambda a_: a_[..., 0].astype(np.uint32) << 16 | a_[..., 1].astype(np.uint32) << 8 | a_[..., 2]
        keys = np.unique(np.concatenate([key(a_).ravel() for a_ in arrs]))
        print(f"ventana {kw} + marco {km} tonos -> paleta {len(keys)}")
        if len(keys) <= 256:
            break
        ex = len(keys) - 256
        kw -= max(2, int(ex * 0.6)); km -= max(2, ex - int(ex * 0.6))
    pal = np.zeros(768, np.uint8)
    pal[0:len(keys) * 3:3], pal[1:len(keys) * 3:3], pal[2:len(keys) * 3:3] = keys >> 16, keys >> 8 & 255, keys & 255
    pp = []
    for a_ in arrs:
        p = Image.fromarray(np.searchsorted(keys, key(a_)).astype(np.uint8), "P"); p.putpalette(pal.tolist()); pp.append(p)
    ruta = HERE / "rem_marco_aurora.gif"
    pp[0].save(ruta, save_all=True, append_images=pp[1:], duration=80, loop=0, disposal=1, optimize=False)
    print(f"{ruta.name}: {N} pasos, {len(keys)} colores, ventana {kw} y marco {km} tonos, {ruta.stat().st_size / 1024 / 1024:.1f} MB")
    sel = [0, 3, 6, 9, 12, 15, 18, 21]
    sh = Image.new("RGB", (4 * 480, 2 * 480), (14, 10, 20))
    for i, t in enumerate(sel):
        sh.paste(out[t].resize((480, 480), Image.LANCZOS), ((i % 4) * 480, (i // 4) * 480))
    sh.save(PREV / "rem_marco_aurora_pasos.png")


if __name__ == "__main__":
    main()
