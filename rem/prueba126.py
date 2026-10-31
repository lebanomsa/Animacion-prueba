"""Prueba de formato 126x126: marco a su resolución nativa (128x128, recortando 1 px por lado) y la ventana de 640 px reducida a 80x80."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import final as fi                  # noqa: E402
import marcos as mk                 # noqa: E402
import marco                        # noqa: E402
import fondos                       # noqa: E402
import previas                      # noqa: E402

PREV = HERE / "previews"


def main(modo="lanczos"):
    ventanas = previas.op1(lambda t: fondos.a_float(fondos.bosque(t % 24)))
    res = Image.LANCZOS if modo == "lanczos" else Image.BOX
    peq = [v.resize((80, 80), res) for v in ventanas]
    vq = fi.cuantizar_ventanas([p.resize((80, 80)) for p in peq], 150)
    top, bot = mk.P3
    f0, _ = marco.build(top, bot)
    base = f0.copy()
    out = []
    for t in range(24):
        fr = base.copy(); mk.det3(fr, t)
        img = Image.new("RGBA", (128, 128), (0, 0, 0, 255))
        img.alpha_composite(vq[t].convert("RGBA"), (24, 24))
        img.alpha_composite(fr)
        out.append(img.convert("RGB").crop((1, 1, 127, 127)))
    arrs = [np.asarray(f) for f in out]
    key = lambda a: a[..., 0].astype(np.uint32) << 16 | a[..., 1].astype(np.uint32) << 8 | a[..., 2]
    keys = np.unique(np.concatenate([key(a).ravel() for a in arrs]))
    print("colores:", len(keys))
    if len(keys) > 256:
        mos = Image.fromarray(np.concatenate(arrs[::2], axis=0))
        q = mos.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        pp = [f.quantize(palette=q, dither=Image.Dither.NONE) for f in out]
    else:
        pal = np.zeros(768, np.uint8)
        pal[0:len(keys) * 3:3], pal[1:len(keys) * 3:3], pal[2:len(keys) * 3:3] = keys >> 16, keys >> 8 & 255, keys & 255
        pp = []
        for a_ in arrs:
            p = Image.fromarray(np.searchsorted(keys, key(a_)).astype(np.uint8), "P"); p.putpalette(pal.tolist()); pp.append(p)
    ruta = PREV / "rem_126_prueba.gif"
    pp[0].save(ruta, save_all=True, append_images=pp[1:], duration=80, loop=0, disposal=1, optimize=False)
    print(f"{ruta.name}: {pp[0].size}, {ruta.stat().st_size / 1024:.0f} KB")
    sh = Image.new("RGB", (126 * 6 * 2, 126 * 6), (14, 10, 20))
    for i, t in enumerate((3, 15)):
        sh.paste(out[t].resize((126 * 6, 126 * 6), Image.NEAREST), (i * 126 * 6, 0))
    sh.save(PREV / "rem_126_prueba.png")


if __name__ == "__main__":
    main()
