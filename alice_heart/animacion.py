"""Alice y Heart chocan los cinco dentro del marco plata y violeta, con las figuras al doble de tamaño por delante del marco.

Lienzo nativo de 126x126 (el marco de 128 recortado 1 px por lado) y su ampliación exacta x4 (504x504).
Capas, de atrás hacia delante: fondo de la ventana -> marco -> Alice y Heart (x2, por delante del marco) -> chispas del choque.
Salida (alice_heart/salida/):
  alice_heart_choque_126.gif / alice_heart_choque_x4.gif                 resultado final
  separado/marco_y_fondo_126.png / _x4.png                               marco con fondo (estático)
  separado/animacion_sola_126.gif / _x4.gif                              Alice, Heart y chispas sobre transparente, en su sitio
Comprueba que (marco y fondo) + animación == GIF final, y que el x4 es la ampliación exacta del de 126.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "secuencia"))
sys.path.insert(0, str(HERE))
import sprites as sp                 # noqa: E402
import marco_alice_heart as mah      # noqa: E402
from choque import mano_derecha, mano_izquierda, holo   # noqa: E402

OUT = HERE / "salida"
SEP = OUT / "separado"
N, Z, TICK, E = 126, 4, 100, 2          # lienzo, ampliación final, ms por paso, escala de las figuras
SUELO = 103                              # fila (en el lienzo de 126) donde apoyan los pies: justo debajo de la ventana (23..102)
key = lambda a: a[..., 0].astype(np.uint32) << 16 | a[..., 1].astype(np.uint32) << 8 | a[..., 2]

FONDO_A, FONDO_B = (24, 31, 48), (19, 25, 40)      # franjas tenues del fondo de la ventana
SUELO_COL, HORIZONTE = (36, 47, 70), (56, 72, 104)
CH_BLANCO, CH_AMARILLO = (255, 255, 255), (255, 226, 120)

# guion a 1x del primer prueba: (Alice, Heart, dx de Heart / 14 de recorrido, elevación Alice (0, 1/2, 1 de "dif"), elevación Heart, holograma, chispas)
GUION = [
    ("H2T8", "H1B0", -14, 0.0, 0, 0, 0),
    ("H2T8", "H1B0", -14, 0.0, 0, 0, 0),
    ("H2T8", "H1B0", -14, 0.0, 0, 0, 0),
    ("H2T0", "H1B2", -14, 0.0, 0, 0, 0),
    ("H2T2", "H2B6", -13, 0.0, 0, 0, 0),
    ("H2T2", "H2B0", -10, 0.5, 1, 0, 0),
    ("H2T4", "H2B2", -5, 0.5, 2, 0, 0),     # la elevación de Alice en este paso es dif//2 + 1 (ver más abajo)
    ("H2T4", "H2B4", 0, 1.0, 0, 0, 1),
    ("H2T4", "H2B4", 0, 1.0, 0, 1, 1),
    ("H2T4", "H2B4", 0, 1.0, 0, 0, 0),
    ("H2T2", "H2B2", -4, 0.5, 1, 0, 0),
    ("H2T0", "H2B0", -9, 0.0, 0, 0, 0),
    ("H2T8", "H1B4", -11, 0.0, 0, 0, 0),
    ("H2T8", "H1B2", -14, 0.0, 0, 0, 0),
    ("H2T8", "H1B0", -14, 0.0, 0, 0, 0),
    ("H2T8", "H1B0", -14, 0.0, 0, 0, 0),
]


def gif_opaco(frames, ruta, dur):
    arrs = [np.asarray(f.convert("RGB")) for f in frames]
    keys = np.unique(np.concatenate([key(a).ravel() for a in arrs]))
    assert len(keys) <= 256, len(keys)
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


def fondo_ventana(win):
    x0, y0, x1, y1 = win
    a = np.zeros((N, N, 3), np.uint8)
    for y in range(N):
        a[y] = FONDO_A if (y % 6) < 4 else FONDO_B
    a[SUELO - 6:] = SUELO_COL
    a[SUELO - 6] = HORIZONTE
    return Image.fromarray(a, "RGB").convert("RGBA")


def main():
    OUT.mkdir(exist_ok=True); SEP.mkdir(exist_ok=True)
    S, _ = sp.cargar()
    esc = lambda im: im.resize((im.width * E, im.height * E), Image.NEAREST)
    SE = {k: esc(v) for k, v in S.items()}

    # ---- geometría del contacto con las figuras al doble
    h4, a4 = SE["H2B4"], SE["H2T4"]
    hx, hy = mano_derecha(h4); ax_, ay_ = mano_izquierda(a4)
    dif = round((SUELO - a4.height + ay_) - (SUELO - h4.height + hy))        # lo que debe saltar Alice para igualar las manos
    off = hx + 1 - ax_                                                      # de la esquina de Heart a la de Alice en el contacto
    anchos_alice = max(SE[k].width for k in {g[0] for g in GUION})
    hxp = min((N - (off + a4.width)) // 2, N - 1 - anchos_alice - off)      # que Alice, incluso en su pose más ancha, quepa en el lienzo
    alice_x = hxp + off
    recorrido = hxp - 1                                                     # lo máximo que puede retroceder Heart sin salirse
    print(f"x2: Heart {h4.size}, Alice {a4.size}; contacto: Heart x={hxp}, Alice x={alice_x}; Alice salta {dif}; recorrido de Heart {recorrido}")
    assert hxp >= 4

    # ---- marco (tonos agrupados para que quepa en 256 colores) y fondo
    spr_cols = {tuple(p[:3]) for im in SE.values() for p in im.getdata() if p[3]}
    extra = {CH_BLANCO, CH_AMARILLO, FONDO_A, FONDO_B, SUELO_COL, HORIZONTE}
    k = 150
    while True:
        img, win = mah.build(k=k)
        op = img[..., 3] > 0
        total = spr_cols | extra | {tuple(c) for c in np.unique(img[op][:, :3], axis=0)}
        if len(total) <= 256:
            break
        k -= max(1, len(total) - 256)
    print(f"marco con {k} tonos; paleta total {len(total)} colores")
    marco126 = Image.fromarray(img, "RGBA").crop((1, 1, 127, 127))
    base = fondo_ventana(win); base.alpha_composite(marco126)

    # ---- capas de animación (por delante del marco)
    capas = []
    for t, (ka, kh, dx, fa, elh, hol, spark) in enumerate(GUION):
        sa = SE[holo(ka) if hol else ka]; sh = SE[holo(kh) if hol else kh]
        if t == 6:
            ela = dif // 2 + E
        else:
            ela = round(dif * fa)
        dxh = round(dx / 14 * recorrido)
        lay = Image.new("RGBA", (N, N), (0, 0, 0, 0))
        lay.alpha_composite(sa, (alice_x, SUELO - sa.height - ela))
        lay.alpha_composite(sh, (hxp + dxh, SUELO - sh.height - elh * E))
        if spark:
            cx, cy = alice_x + ax_ - 1, SUELO - a4.height - dif + round(ay_)
            for (px, py, c) in [(0, -4, "w"), (0, -5, "y"), (-3, -3, "y"), (3, -3, "y"), (-5, 0, "w"), (5, 0, "w"),
                                (-4, 0, "y"), (4, 0, "y"), (-3, 3, "y"), (3, 3, "y"), (0, 4, "w"), (0, 5, "y")]:
                col = CH_BLANCO if c == "w" else CH_AMARILLO
                for ddx in range(E):
                    for ddy in range(E):
                        X, Y = cx + px * E + ddx, cy + py * E + ddy
                        if 0 <= X < N and 0 <= Y < N:
                            lay.putpixel((X, Y), col + (255,))
        capas.append(lay)
    L = len(capas)
    bb = [c.getchannel("A").getbbox() for c in capas]
    print("cajas de la animación (mín. x, mín. y, máx. x, máx. y):",
          min(b[0] for b in bb), min(b[1] for b in bb), max(b[2] for b in bb), max(b[3] for b in bb), "de", N)

    finales = []
    for c in capas:
        f = base.copy(); f.alpha_composite(c); finales.append(f.convert("RGB"))
    up = lambda im: im.resize((N * Z, N * Z), Image.NEAREST)

    # ---- escritura
    n1 = gif_opaco(finales, OUT / "alice_heart_choque_126.gif", TICK)
    gif_opaco([up(f) for f in finales], OUT / "alice_heart_choque_x4.gif", TICK)
    base.convert("RGB").save(SEP / "marco_y_fondo_126.png"); up(base.convert("RGB")).save(SEP / "marco_y_fondo_x4.png")
    n2 = gif_transparente(capas, SEP / "animacion_sola_126.gif", TICK)
    gif_transparente([up(c) for c in capas], SEP / "animacion_sola_x4.gif", TICK)
    print(f"final: {n1} colores; animación sola: {n2} colores")
    for r in ("alice_heart_choque_126.gif", "alice_heart_choque_x4.gif", "separado/marco_y_fondo_126.png", "separado/marco_y_fondo_x4.png",
              "separado/animacion_sola_126.gif", "separado/animacion_sola_x4.gif"):
        pth = OUT / r
        print(f"  {r}: {Image.open(pth).size}, {pth.stat().st_size / 1024:.0f} KB")

    # ---- comprobaciones
    dif_tot = 0
    for tam, suf in ((N, "126"), (N * Z, "x4")):
        fin = por_paso(OUT / f"alice_heart_choque_{suf}.gif", L, TICK)
        png = Image.open(SEP / f"marco_y_fondo_{suf}.png").convert("RGBA")
        sola = por_paso(SEP / f"animacion_sola_{suf}.gif", L, TICK)
        d = 0
        for t in range(L):
            c = png.copy(); c.alpha_composite(sola[t])
            d += int((np.abs(np.asarray(c.convert("RGB")).astype(int) - np.asarray(fin[t].convert("RGB")).astype(int)).sum(-1) > 0).sum())
        print(f"píxeles distintos (marco y fondo + animación) vs final, {suf}, {L} pasos:", d)
        dif_tot += d
    f126 = por_paso(OUT / "alice_heart_choque_126.gif", L, TICK); f4 = por_paso(OUT / "alice_heart_choque_x4.gif", L, TICK)
    d = sum(int((np.asarray(up(f126[t].convert("RGB"))).astype(int) != np.asarray(f4[t].convert("RGB")).astype(int)).any(-1).sum()) for t in range(L))
    print("píxeles distintos entre x4 y la ampliación exacta del 126:", d)

    # hoja de fotogramas
    tmp = Path("/projects/sandbox/tmp/alice_heart"); tmp.mkdir(parents=True, exist_ok=True)
    z, cols = 3, 4
    sh = Image.new("RGB", (cols * N * z, ((L + cols - 1) // cols) * N * z))
    for i, f in enumerate(finales):
        sh.paste(f.resize((N * z, N * z), Image.NEAREST), ((i % cols) * N * z, (i // cols) * N * z))
    sh.save(tmp / "hoja_final.png")


if __name__ == "__main__":
    main()
