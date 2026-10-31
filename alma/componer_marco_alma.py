"""Alma (reinicio C, zarpazos de tigre) dentro del marco azul cielo -> dorado, con el escenario de nieve animado.

Capas: negro -> escenario de nieve (cielo con estrellas que parpadean) -> Alma (+ zarpazos) -> marco (x8).
Personaje y escenario usan la misma escala (S) para que los píxeles midan lo mismo.
El ciclo de Alma son 67 pasos de 70 ms; el parpadeo del cielo son 9 fotogramas. Como 67 no es múltiplo de 18, el
parpadeo se reparte en 4 vueltas completas dentro de los 67 pasos (36 fotogramas: 31 de 2 pasos y 5 de 1 paso, repartidos
a lo largo del ciclo) para que el bucle no tenga salto.

Uso:  python componer_marco_alma.py [S] [fila_suelo] [fila_pies] [x0] [col_luna] [salida]
  S           escala de personaje y escenario (4 -> la ventana de 640 px enseña 160x160 píxeles del escenario)
  fila_suelo  fila (en píxeles nativos de la ventana) donde empieza la nieve
  fila_pies   fila donde apoyan los pies de Alma
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
ROOT = HERE.parent
for d in (HERE, ROOT / "secuencia", ROOT / "nieve", ROOT / "agalia"):
    sys.path.insert(0, str(d))
import completa as cp           # noqa: E402
import reinicio as rn           # noqa: E402
import marco                    # noqa: E402
import animar as an             # noqa: E402
import stage as st              # noqa: E402
from componer_marco_agalia import quantize_rgb   # noqa: E402

SIZE, S_FRAME = 1024, 8
TICK = cp.TICK
FEET_LIENZO = 108 + rn.OFF[1]      # fila del lienzo de Alma donde apoyan sus pies (SUELO + desplazamiento)
CENTRO_X = rn.CX                   # columna del lienzo donde está el centro de la figura

# Paletas por brillo (V entre 0 y 1). Arriba azul cielo, abajo oro.
AZUL_CIELO = [(0.0, (6, 36, 84)), (0.3, (24, 92, 164)), (0.6, (80, 164, 228)),
              (0.85, (150, 210, 248)), (1.0, (232, 248, 255))]
ORO = [(0.0, (16, 9, 2)), (0.3, (68, 42, 8)), (0.6, (150, 106, 22)),
       (0.85, (214, 168, 56)), (1.0, (255, 236, 150))]
BANDS = 12
T0, T1 = 0.46, 0.54                # el cambio de azul a oro es un único salto de banda en el 50 % de la altura
SOMBRA_AZUL = (0.78, 1.06)         # factor de brillo del azul: más oscuro arriba, más claro hacia el centro
SOMBRA_ORO = (1.12, 0.74)          # factor de brillo del oro: más claro bajo el centro, más oscuro abajo


def recolor_azul_oro(rgb, top_stops, bot_stops):
    """Como marco.recolor, pero el degradado vertical es azul arriba, oro abajo y cambia en una franja media."""
    N = marco.N
    y = np.repeat(np.arange(N)[:, None], N, axis=1)
    lum = rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114
    v = np.clip(lum / np.percentile(lum, 98), 0, 1)
    band = np.minimum(y * BANDS // N, BANDS - 1)
    t = np.clip(((band + 0.5) / BANDS - T0) / (T1 - T0), 0, 1)
    top, bot = marco.ramp(top_stops, v), marco.ramp(bot_stops, v)
    u = np.clip(band / (BANDS / 2 - 1), 0, 1)                        # 0 -> 1 en la mitad superior
    w = np.clip((band - BANDS // 2) / (BANDS / 2 - 1), 0, 1)         # 0 -> 1 en la mitad inferior
    top = top * (SOMBRA_AZUL[0] + (SOMBRA_AZUL[1] - SOMBRA_AZUL[0]) * u)[..., None]
    bot = bot * (SOMBRA_ORO[0] + (SOMBRA_ORO[1] - SOMBRA_ORO[0]) * w)[..., None]
    return np.clip(top + (bot - top) * t[..., None], 0, 255).round().astype(np.uint8)


def reparto_estrellas(n_pasos, ciclos=4, n_fot=9):
    """Fotograma del cielo para cada paso: `ciclos` vueltas completas repartidas en n_pasos (fotogramas de 2 o 1 pasos)."""
    total = ciclos * n_fot
    cortos = 2 * total - n_pasos
    assert 0 <= cortos <= total
    dur = [2] * total
    for j in range(cortos):
        dur[int((j + 0.5) * total / cortos)] = 1
    out = []
    for i, d in enumerate(dur):
        out += [i % n_fot] * d
    assert len(out) == n_pasos
    return out


def ventana_nativa(wn, x0, moon_col, ground_row, sky_img, ground):
    y0 = st.SUELO_Y - ground_row
    can = Image.new("RGBA", (wn, wn), an.SKY + (255,))
    an.paste_clip(can, sky_img.convert("RGBA"), moon_col - 287, st.SKY_Y - y0)
    an.paste_clip(can, ground, -x0, st.SUELO_Y - st.GROUND_FLAT_Y - y0)
    return can.convert("RGB")


def main(S=4, ground_row=84, feet_row=130, x0=100, moon_col=125, salida="alma_marco_azul_oro.gif", k_stage=110):
    marco.recolor = recolor_azul_oro
    frame, (wx0, wy0, wx1, wy1) = marco.build(AZUL_CIELO, ORO)
    win_x, win_y = wx0 * S_FRAME, wy0 * S_FRAME
    win = (wx1 - wx0 + 1) * S_FRAME
    assert win % S == 0
    wn = win // S

    # ---- Alma con el reinicio C, recortada igual que su GIF
    frames, sched, L, _ = cp.componer("C")
    boxes = [b for b in (f.getchannel("A").getbbox() for f in frames) if b]
    box = (max(min(b[0] for b in boxes) - 2, 0), max(min(b[1] for b in boxes) - 2, 0),
           min(max(b[2] for b in boxes) + 2, rn.CWE), min(max(b[3] for b in boxes) + 2, rn.CHE))
    alma = [f.crop(box) for f in frames]
    aw, ah = alma[0].size
    ax = win // 2 - (CENTRO_X - box[0]) * S
    ax = min(max(ax, 0), win - aw * S)               # que los zarpazos no rebasen la ventana
    ay = feet_row * S - (FEET_LIENZO - box[1]) * S
    print(f"ventana {win}x{win} en ({win_x},{win_y}); Alma C {aw}x{ah} px -> {aw * S}x{ah * S}; origen en ventana ({ax},{ay}); "
          f"ocupa x {ax}..{ax + aw * S}, y {ay}..{ay + ah * S}")
    fuera = [(ax < 0), (ay < 0), (ax + aw * S > win), (ay + ah * S > win)]
    if any(fuera):
        print("  AVISO: Alma (o sus zarpazos) rebasa la ventana por [izq, arriba, der, abajo] =", fuera)

    # ---- escenario nativo (wn x wn), paleta común y ampliación
    sheet = st.load_sheet(); sky = st.skies(sheet); ground = st.ground(sheet)
    native = [np.asarray(ventana_nativa(wn, x0, moon_col, ground_row, sky[i], ground)) for i in an.MOON_FRAMES]
    pal, n_res, n_cambian = an.paleta(native, k_stage)
    red = [an.reducir(f, pal) for f in native]
    big = [np.asarray(Image.fromarray(r).resize((win, win), Image.NEAREST)) for r in red]
    stage_cols = {tuple(c) for c in np.unique(np.concatenate([b.reshape(-1, 3) for b in big]), axis=0)}
    alma_cols = {tuple(p[:3]) for f in alma for p in f.getdata() if p[3]}
    print(f"escenario {wn}x{wn} nativos, {len(stage_cols)} colores; Alma {len(alma_cols)} colores")

    # ---- marco: agrupar tonos para completar los 256 colores
    m = np.asarray(frame); op = m[..., 3] > 0
    km = 170
    while True:
        mq = m[..., :3].copy(); mq[op] = quantize_rgb(m[..., :3][op], km)
        total = stage_cols | alma_cols | {tuple(c) for c in np.unique(mq[op], axis=0)}
        if len(total) <= 256:
            break
        km -= max(1, len(total) - 256)
    print(f"marco: {km} tonos, paleta total {len(total)}")
    marco_big = Image.fromarray(np.dstack([mq, m[..., 3]]), "RGBA").resize((marco.N * S_FRAME,) * 2, Image.NEAREST)

    # ---- composición
    idx = reparto_estrellas(L)
    bases = []
    for b in big:
        base = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 255))
        base.alpha_composite(Image.fromarray(b, "RGB").convert("RGBA"), (win_x, win_y))
        bases.append(base)
    out_rgb = []
    for t in range(L):
        img = bases[idx[t]].copy()
        a = alma[t].resize((aw * S, ah * S), Image.NEAREST)
        # recorte a la ventana: lo que rebase queda tapado por el marco, salvo que se dibuje encima
        an.paste_clip(img, a, win_x + ax, win_y + ay)
        img.alpha_composite(marco_big)
        out_rgb.append(img.convert("RGB"))

    # ---- GIF con paleta global exacta
    arrs = [np.asarray(f) for f in out_rgb]
    key = lambda a: a[..., 0].astype(np.uint32) << 16 | a[..., 1].astype(np.uint32) << 8 | a[..., 2]
    keys = np.unique(np.concatenate([key(a).ravel() for a in arrs]))
    print("paleta global:", len(keys), "colores")
    assert len(keys) <= 256
    pal_g = np.zeros(768, np.uint8)
    pal_g[0:len(keys) * 3:3], pal_g[1:len(keys) * 3:3], pal_g[2:len(keys) * 3:3] = keys >> 16, keys >> 8 & 255, keys & 255
    outp = []
    for a in arrs:
        p = Image.fromarray(np.searchsorted(keys, key(a)).astype(np.uint8), "P"); p.putpalette(pal_g.tolist()); outp.append(p)
    path = HERE / salida
    outp[0].save(path, save_all=True, append_images=outp[1:], duration=TICK, loop=0, disposal=1, optimize=False)
    print(f"{path.name}: {len(outp)} pasos de {TICK} ms = {len(outp) * TICK} ms, {path.stat().st_size / 1024:.0f} KB")
    tmp = Path("/projects/sandbox/tmp"); tmp.mkdir(exist_ok=True)
    stem = Path(salida).stem
    for t in (0, 30, 59, 62, 64, 1):
        out_rgb[t].save(tmp / f"{stem}_t{t}.png")
    return out_rgb


if __name__ == "__main__":
    a = sys.argv[1:]
    kw = {}
    if len(a) > 0: kw["S"] = int(a[0])
    if len(a) > 1: kw["ground_row"] = int(a[1])
    if len(a) > 2: kw["feet_row"] = int(a[2])
    if len(a) > 3: kw["x0"] = int(a[3])
    if len(a) > 4: kw["moon_col"] = int(a[4])
    if len(a) > 5: kw["salida"] = a[5]
    main(**kw)
