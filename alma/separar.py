"""Separa la composición final de Alma (alma_marco_azul_oro.gif) en marco + fondo y animación.

  marco_y_fondo_alma.gif          1024x1024: marco fijo + escenario de nieve con las estrellas parpadeando (67 pasos de 70 ms)
  marco_y_fondo_alma.png          primer fotograma del anterior
  alma_animacion_sola.gif         1024x1024 transparente: Alma + zarpazos en su sitio, mismos 67 pasos
  alma_animacion_recortada.gif    la misma animación recortada a su tamaño

Alma va por DETRÁS del marco: donde el marco la tapa, la capa es transparente.
Usa los mismos parámetros que componer_marco_alma.py y comprueba que (marco+fondo) + animación == GIF final.
Salida: salida_separada/
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import componer_marco_alma as ca          # noqa: E402
from componer_marco_alma import cp, rn, marco, an, st, quantize_rgb, SIZE, S_FRAME, TICK  # noqa: E402

OUT = HERE / "salida_separada"
key = lambda a: a[..., 0].astype(np.uint32) << 16 | a[..., 1].astype(np.uint32) << 8 | a[..., 2]


def gif_opaco(frames, ruta, dur):
    arrs = [np.asarray(f.convert("RGB")) for f in frames]
    keys = np.unique(np.concatenate([key(a).ravel() for a in arrs]))
    assert len(keys) <= 256
    pal = np.zeros(768, np.uint8)
    pal[0:len(keys) * 3:3], pal[1:len(keys) * 3:3], pal[2:len(keys) * 3:3] = keys >> 16, keys >> 8 & 255, keys & 255
    out = []
    for a in arrs:
        p = Image.fromarray(np.searchsorted(keys, key(a)).astype(np.uint8), "P"); p.putpalette(pal.tolist()); out.append(p)
    out[0].save(ruta, save_all=True, append_images=out[1:], duration=dur, loop=0, disposal=1, optimize=False)
    return len(keys)


def gif_transparente(frames, ruta, dur):
    arrs = [np.asarray(f) for f in frames]
    cols = np.unique(np.concatenate([key(a)[a[..., 3] > 0] for a in arrs]))
    assert len(cols) <= 255, len(cols)
    flat = np.zeros(768, np.uint8); flat[0:3] = (255, 0, 255)
    flat[3:3 + len(cols) * 3:3], flat[4:4 + len(cols) * 3:3], flat[5:5 + len(cols) * 3:3] = cols >> 16, cols >> 8 & 255, cols & 255
    out = []
    for a in arrs:
        idx = (np.searchsorted(cols, key(a)) + 1).astype(np.uint8)
        idx[a[..., 3] == 0] = 0
        p = Image.fromarray(idx, "P"); p.putpalette(flat.tolist()); out.append(p)
    out[0].save(ruta, save_all=True, append_images=out[1:], duration=dur, loop=0, transparency=0, disposal=2, optimize=False)
    return len(cols)


def por_paso(ruta, total, tick):
    g = Image.open(ruta); out = []
    for i in range(g.n_frames):
        g.seek(i); f = g.convert("RGBA")
        out += [f] * round(g.info.get("duration", tick) / tick)
    assert len(out) == total, (ruta.name, len(out))
    return out


def preparar(S=4, ground_row=104, feet_row=130, x0=170, moon_col=115, k_stage=110):
    """Misma preparación que componer_marco_alma.main(); devuelve lo necesario para componer por capas."""
    marco.recolor = ca.recolor_azul_oro
    frame, (wx0, wy0, wx1, wy1) = marco.build(ca.AZUL_CIELO, ca.ORO)
    win_x, win_y = wx0 * S_FRAME, wy0 * S_FRAME
    win = (wx1 - wx0 + 1) * S_FRAME
    wn = win // S
    frames, sched, L, _ = cp.componer("C")
    boxes = [b for b in (f.getchannel("A").getbbox() for f in frames) if b]
    box = (max(min(b[0] for b in boxes) - 2, 0), max(min(b[1] for b in boxes) - 2, 0),
           min(max(b[2] for b in boxes) + 2, rn.CWE), min(max(b[3] for b in boxes) + 2, rn.CHE))
    alma = [f.crop(box) for f in frames]
    aw, ah = alma[0].size
    ax = win // 2 - (ca.CENTRO_X - box[0]) * S
    ax = min(max(ax, 0), win - aw * S)
    ay = feet_row * S - (ca.FEET_LIENZO - box[1]) * S
    sheet = st.load_sheet(); sky = st.skies(sheet); ground = st.ground(sheet)
    native = [np.asarray(ca.ventana_nativa(wn, x0, moon_col, ground_row, sky[i], ground)) for i in an.MOON_FRAMES]
    pal, _, _ = an.paleta(native, k_stage)
    red = [an.reducir(f, pal) for f in native]
    big = [np.asarray(Image.fromarray(r).resize((win, win), Image.NEAREST)) for r in red]
    stage_cols = {tuple(c) for c in np.unique(np.concatenate([b.reshape(-1, 3) for b in big]), axis=0)}
    alma_cols = {tuple(p[:3]) for f in alma for p in f.getdata() if p[3]}
    m = np.asarray(frame); op = m[..., 3] > 0
    km = 170
    while True:
        mq = m[..., :3].copy(); mq[op] = quantize_rgb(m[..., :3][op], km)
        total = stage_cols | alma_cols | {tuple(c) for c in np.unique(mq[op], axis=0)}
        if len(total) <= 256:
            break
        km -= max(1, len(total) - 256)
    marco_big = Image.fromarray(np.dstack([mq, m[..., 3]]), "RGBA").resize((marco.N * S_FRAME,) * 2, Image.NEAREST)
    return dict(S=S, win=win, win_x=win_x, win_y=win_y, L=L, alma=alma, aw=aw, ah=ah, ax=ax, ay=ay, big=big,
                marco_big=marco_big, km=km)


def main():
    OUT.mkdir(exist_ok=True)
    P = preparar()
    S, win, win_x, win_y, L = P["S"], P["win"], P["win_x"], P["win_y"], P["L"]
    aw, ah, ax, ay, marco_big = P["aw"], P["ah"], P["ax"], P["ay"], P["marco_big"]
    print(f"marco con {P['km']} tonos (igual que el final)")
    idx = ca.reparto_estrellas(L)
    tapa = np.asarray(marco_big)[..., 3] > 0

    # 1. marco + fondo (un fotograma por paso; el GIF fusiona los repetidos)
    bases = []
    for b in P["big"]:
        base = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 255))
        base.alpha_composite(Image.fromarray(b, "RGB").convert("RGBA"), (win_x, win_y))
        base.alpha_composite(marco_big)
        bases.append(base)
    fondo = [bases[idx[t]] for t in range(L)]
    n = gif_opaco(fondo, OUT / "marco_y_fondo_alma.gif", TICK)
    fondo[0].convert("RGB").save(OUT / "marco_y_fondo_alma.png")
    print(f"marco_y_fondo_alma.gif: {n} colores, {(OUT / 'marco_y_fondo_alma.gif').stat().st_size / 1024:.0f} KB")

    # 2. animación: Alma sin lo que tapa el marco
    alfas = np.unique(np.concatenate([np.unique(np.asarray(f.getchannel("A"))) for f in P["alma"]]))
    print("valores de alfa de Alma:", alfas.tolist())
    capas = []
    for t in range(L):
        lay = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        a = P["alma"][t].resize((aw * S, ah * S), Image.NEAREST)
        an.paste_clip(lay, a, win_x + ax, win_y + ay)
        arr = np.array(lay); arr[tapa] = 0
        capas.append(Image.fromarray(arr, "RGBA"))
    n = gif_transparente(capas, OUT / "alma_animacion_sola.gif", TICK)
    boxes = [c.getchannel("A").getbbox() for c in capas if c.getchannel("A").getbbox()]
    box = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
    gif_transparente([c.crop(box) for c in capas], OUT / "alma_animacion_recortada.gif", TICK)
    print(f"alma_animacion_sola.gif: {L} pasos de {TICK} ms = {L * TICK} ms, {n} colores, "
          f"{(OUT / 'alma_animacion_sola.gif').stat().st_size / 1024:.0f} KB; recorte {box[2] - box[0]}x{box[3] - box[1]} en {box[:2]}")

    # comprobación contra el GIF final
    final = por_paso(HERE / "alma_marco_azul_oro.gif", L, TICK)
    fon = por_paso(OUT / "marco_y_fondo_alma.gif", L, TICK)
    sola = por_paso(OUT / "alma_animacion_sola.gif", L, TICK)
    dif = 0
    for t in range(L):
        comp = fon[t].copy(); comp.alpha_composite(sola[t])
        dif += int((np.abs(np.asarray(comp.convert("RGB")).astype(int)
                           - np.asarray(final[t].convert("RGB")).astype(int)).sum(-1) > 0).sum())
    print(f"píxeles distintos entre (marco+fondo + animación) y el GIF final, en los {L} pasos:", dif)


if __name__ == "__main__":
    main()
