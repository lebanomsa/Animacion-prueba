"""Alice y Heart se saludan chocando los cinco (prueba sobre fondo liso, sin marco).

Lienzo nativo 126x126 ampliado 4x (504x504) como en 'gif referencia.gif'. Sprites a tamaño natural (1x).
Heart (pelo corto) a la izquierda salta hacia Alice (coletas); chocan las manos y por un instante se ven en versión holograma.
El rectángulo tenue marca la ventana de 88x88 que damos por supuesta para el marco futuro.

  python choque.py            -> salida/choque_prueba.gif  (+ hoja de fotogramas en /projects/sandbox/tmp/alice_heart)
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import sprites as sp   # noqa: E402

OUT = HERE / "salida"
N, Z, TICK = 126, 4, 100
WIN = 88
WX = (N - WIN) // 2            # 19
SUELO = WX + WIN - 12          # fila donde apoyan los pies
CONTACTO_X = 66                # columna aproximada donde chocan las manos
ESPACIO_IDLE = 14              # separación extra de Heart en reposo
CHISPAS = True
key = lambda a: a[..., 0].astype(np.uint32) << 16 | a[..., 1].astype(np.uint32) << 8 | a[..., 2]


def mano_derecha(s):
    """(x, y) del píxel más a la derecha en el tercio superior del sprite (mano alzada de Heart)."""
    a = np.asarray(s.getchannel("A")) > 0
    top = a[: max(8, s.height // 3)]
    xr = np.nonzero(top.any(0))[0].max()
    ys = np.nonzero(top[:, xr])[0]
    return int(xr), float(ys.mean())


def mano_izquierda(s):
    """(x, y) del píxel más a la izquierda en el 40 % superior del sprite (mano alzada de Alice)."""
    a = np.asarray(s.getchannel("A")) > 0
    top = a[: int(s.height * 0.4)]
    xl = np.nonzero(top.any(0))[0].min()
    ys = np.nonzero(top[:, xl])[0]
    return int(xl), float(ys.mean())


def holo(k):
    """Nombre del holograma de una pose en color (el siguiente índice de la hoja)."""
    return k[:-1] + str(int(k[-1]) + 1)


def main():
    OUT.mkdir(exist_ok=True)
    S, umin = sp.cargar()
    print(f"{len(S)} sprites; uniformidad 3x3 mínima {umin:.3f}")

    # posición de contacto: la mano de Heart (B4) toca la de Alice (T4) sin hueco
    heart_c, alice_c = S["H2B4"], S["H2T4"]
    hx, hy = mano_derecha(heart_c); ax_, ay_ = mano_izquierda(alice_c)
    alice_x = CONTACTO_X                                # esquina izquierda del sprite de Alice
    heart_x = alice_x + ax_ - hx - 1                    # mano de Heart justo a la izquierda de la de Alice
    # con los pies de las dos en el suelo, la mano de Heart queda más alta que la de Alice; Alice salta esa diferencia
    dif = round((SUELO - alice_c.height + ay_) - (SUELO - heart_c.height + hy))
    print(f"contacto: Alice x={alice_x}, Heart x={heart_x}; Alice salta {dif} px para igualar las manos")
    print("  mano Heart", (hx, hy), " mano Alice", (ax_, ay_))

    # (Alice, Heart, dx de Heart, elevación Alice, elevación Heart, holograma, chispas)
    H = heart_x
    I = -ESPACIO_IDLE
    guion = [
        ("H2T8", "H1B0", I, 0, 0, 0, 0),
        ("H2T8", "H1B0", I, 0, 0, 0, 0),
        ("H2T8", "H1B0", I, 0, 0, 0, 0),
        ("H2T0", "H1B2", I, 0, 0, 0, 0),
        ("H2T2", "H2B6", I + 1, 0, 0, 0, 0),
        ("H2T2", "H2B0", -10, dif // 2, 1, 0, 0),
        ("H2T4", "H2B2", -5, dif // 2 + 1, 2, 0, 0),
        ("H2T4", "H2B4", 0, dif, 0, 0, 1),
        ("H2T4", "H2B4", 0, dif, 0, 1, 1),
        ("H2T4", "H2B4", 0, dif, 0, 0, 0),
        ("H2T2", "H2B2", -4, dif // 2, 1, 0, 0),
        ("H2T0", "H2B0", -9, 0, 0, 0, 0),
        ("H2T8", "H1B4", I + 3, 0, 0, 0, 0),
        ("H2T8", "H1B2", I, 0, 0, 0, 0),
        ("H2T8", "H1B0", I, 0, 0, 0, 0),
        ("H2T8", "H1B0", I, 0, 0, 0, 0),
    ]
    frames = []
    for (ka, kh, dx, ela, elh, hol, spark) in guion:
        img = Image.new("RGBA", (N, N), (26, 32, 48, 255))
        d = ImageDraw.Draw(img)
        d.rectangle((0, SUELO, N, N), fill=(38, 48, 70, 255))
        d.rectangle((WX, WX, WX + WIN - 1, WX + WIN - 1), outline=(70, 86, 118, 255))
        sa = S[holo(ka) if hol else ka]; sh = S[holo(kh) if hol else kh]
        # Alice: alineada por los pies; Heart: por los pies (con elevación)
        img.alpha_composite(sa, (alice_x, SUELO - sa.height - ela))
        img.alpha_composite(sh, (H + dx, SUELO - sh.height - elh))
        if spark:
            cx, cy = alice_x + ax_ - 1, SUELO - alice_c.height - dif + round(ay_)
            for (px, py, c) in [(0, -4, "w"), (0, -5, "y"), (-3, -3, "y"), (3, -3, "y"), (-5, 0, "w"), (5, 0, "w"),
                                (-4, 0, "y"), (4, 0, "y"), (-3, 3, "y"), (3, 3, "y"), (0, 4, "w"), (0, 5, "y")]:
                img.putpixel((cx + px, cy + py), (255, 255, 255, 255) if c == "w" else (255, 226, 120, 255))
        frames.append(img.convert("RGB"))

    # GIF 504x504 con paleta global exacta
    big = [f.resize((N * Z, N * Z), Image.NEAREST) for f in frames]
    arrs = [np.asarray(f) for f in big]
    keys = np.unique(np.concatenate([key(a).ravel() for a in arrs]))
    print("colores:", len(keys)); assert len(keys) <= 256
    pal = np.zeros(768, np.uint8)
    pal[0:len(keys) * 3:3], pal[1:len(keys) * 3:3], pal[2:len(keys) * 3:3] = keys >> 16, keys >> 8 & 255, keys & 255
    ps = []
    for a in arrs:
        p = Image.fromarray(np.searchsorted(keys, key(a)).astype(np.uint8), "P"); p.putpalette(pal.tolist()); ps.append(p)
    ruta = OUT / "choque_prueba.gif"
    ps[0].save(ruta, save_all=True, append_images=ps[1:], duration=TICK, loop=0, disposal=1, optimize=False)
    print(f"{ruta.name}: {len(ps)} pasos de {TICK} ms = {len(ps) * TICK} ms, {ruta.stat().st_size / 1024:.0f} KB")

    tmp = Path("/projects/sandbox/tmp/alice_heart"); tmp.mkdir(parents=True, exist_ok=True)
    z = 3; cols = 4; rows = (len(frames) + cols - 1) // cols
    sh = Image.new("RGB", (cols * N * z, rows * N * z), (0, 0, 0))
    for i, f in enumerate(frames):
        sh.paste(f.resize((N * z, N * z), Image.NEAREST), ((i % cols) * N * z, (i // cols) * N * z))
        ImageDraw.Draw(sh).text(((i % cols) * N * z + 4, (i // cols) * N * z + 4), str(i), fill=(255, 255, 255))
    sh.save(tmp / "hoja_choque.png")
    return frames


if __name__ == "__main__":
    main()
