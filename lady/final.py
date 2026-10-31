"""Lady completa: marco 'medianoche verde azulado' (cadenas con corazón, cruces, destellos) + escenario B (silueta negra) con relámpago
+ animación de Lady con ondas de arcoíris. 48 pasos de 80 ms (3840 ms), bucle sin saltos.

Capas: negro -> escenario (cuantizado) -> Lady (colores exactos) -> marco (x8). Lady y el escenario se componen a píxeles nativos (128x128) y se amplían
juntos a x5. Paleta global de 256 colores: Lady y los detalles del marco exactos; el escenario y el marco se agrupan en el resto.
Los ciclos del marco son de 6 pasos (48 = 8 ciclos) y el relámpago cae en los pasos 10 y 34.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import animacion as an              # noqa: E402
import escenario as esc             # noqa: E402
import hojas                        # noqa: E402
import marcos as mk                 # noqa: E402
import marco                        # noqa: E402

PREV = HERE / "previews"
N = 48
TICK = 80


def lady_capas():
    g = an.guion("reversa", True, "ondas")
    capas = []
    for t, (k, a) in enumerate(g):
        f = (hojas.ARCO if a is True else hojas.NORMAL)[k]
        img = f["img"]
        if isinstance(a, tuple):
            na, aa = np.array(hojas.NORMAL[k]["img"]), np.array(hojas.ARCO[k]["img"])
            filas = np.arange(na.shape[0])
            m = ((filas >= a[1]) & (filas <= a[2]))[:, None, None]
            img = Image.fromarray(np.where(m, aa, na).astype(np.uint8), "RGBA")
        lay = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
        lay.alpha_composite(img, (int(round(an.X_C - f["pies"])), an.Y_SUELO - hojas.SUELO))
        capas.append(lay)
    return capas


def cuantizar_escenarios(escenas, k):
    """Paleta común de k colores para todas las vistas del escenario (corte mediano, sin tramado)."""
    mosaico = Image.fromarray(np.concatenate([np.asarray(e.convert("RGB")) for e in escenas], axis=0))
    q = mosaico.quantize(colors=k, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    return {id(e): e.convert("RGB").quantize(palette=q, dither=Image.Dither.NONE).convert("RGB") for e in escenas}


def main():
    capas = lady_capas()
    pasos_rel = [an.paso_relampago(t) for t in range(N)]
    distintos = sorted(set(pasos_rel))
    escenas = {p: esc.ventana("B", p) for p in distintos}
    lady_cols = {tuple(p[:3]) for c in capas for p in c.getdata() if p[3]}
    print("pasos de escenario distintos:", len(distintos), "| colores exactos de Lady:", len(lady_cols))
    f0, _ = marco.build(*mk.P2)
    f0 = f0.copy()
    ks, km = 80, 80
    while True:
        qs = cuantizar_escenarios(list(escenas.values()), ks)
        esc_q = {p: qs[id(e)] for p, e in escenas.items()}
        a = np.array(f0); op = a[..., 3] > 0
        a[..., :3][op] = mk.quantize_rgb(a[..., :3][op], km)
        base = Image.fromarray(a, "RGBA")
        marcos_t = []
        for t in range(6):
            fr = base.copy(); mk.det2(fr, t)
            marcos_t.append(fr.resize((1024, 1024), Image.NEAREST))
        out = []
        for t in range(N):
            win = esc_q[pasos_rel[t]].convert("RGBA")
            win.alpha_composite(capas[t])
            img = Image.new("RGBA", (1024, 1024), (0, 0, 0, 255))
            img.alpha_composite(win.resize((640, 640), Image.NEAREST), (192, 192))
            img.alpha_composite(marcos_t[t % 6])
            out.append(img.convert("RGB"))
        arrs = [np.asarray(f) for f in out]
        key = lambda a_: a_[..., 0].astype(np.uint32) << 16 | a_[..., 1].astype(np.uint32) << 8 | a_[..., 2]
        keys = np.unique(np.concatenate([key(a_).ravel() for a_ in arrs]))
        print(f"escenario {ks} + marco {km} tonos -> paleta {len(keys)}")
        if len(keys) <= 256:
            break
        exceso = len(keys) - 256
        ks -= max(2, exceso // 2); km -= max(2, exceso - exceso // 2)
    pal = np.zeros(768, np.uint8)
    pal[0:len(keys) * 3:3], pal[1:len(keys) * 3:3], pal[2:len(keys) * 3:3] = keys >> 16, keys >> 8 & 255, keys & 255
    pp = []
    for a_ in arrs:
        p = Image.fromarray(np.searchsorted(keys, key(a_)).astype(np.uint8), "P"); p.putpalette(pal.tolist()); pp.append(p)
    ruta = HERE / "lady_marco_verde_azulado.gif"
    pp[0].save(ruta, save_all=True, append_images=pp[1:], duration=TICK, loop=0, disposal=1, optimize=False)
    print(f"{ruta.name}: {N} pasos, {len(keys)} colores, escenario {ks} y marco {km} tonos, {ruta.stat().st_size / 1024 / 1024:.1f} MB")
    sel = [0, 6, 10, 12, 16, 22, 30, 36, 40, 44, 46, 47]
    sh = Image.new("RGB", (6 * 340, 2 * 340), (14, 10, 20))
    for i, t in enumerate(sel):
        sh.paste(out[t].resize((340, 340), Image.LANCZOS), ((i % 6) * 340, (i // 6) * 340))
    PREV.mkdir(exist_ok=True)
    sh.save(PREV / "lady_marco_verde_azulado_pasos.png")


if __name__ == "__main__":
    main()
