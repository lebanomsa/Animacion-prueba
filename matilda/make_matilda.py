"""Animaciones de Matilda a partir de un único fotograma (Matilda.png, 148x125).

Versión 1 - idle (8 fotogramas): respiración, pelo/lazo con retraso, vaivén de la punta
            de la vara, pulso de brillo en el adorno y mano que sigue al cuerpo con retraso.
Versión 2 - destello (10 fotogramas): preparación, brazo que se extiende, flash en la
            vara con chispas y brillo en la punta del dedo, y vuelta a la postura.

Todo se hace con desplazamientos de píxeles enteros y la paleta original (24 colores).
Salida (transparente, bucle infinito): matilda_idle*.gif y matilda_destello*.gif
(el sufijo _x4 es la misma animación ampliada x4 con vecino más cercano).
"""
from pathlib import Path

from PIL import Image

HERE = Path(__file__).parent
SRC = HERE.parent / "Matilda.png"

# Lienzo de salida en coordenadas del PNG original (deja margen para brazo y chispas)
X0, Y0, CW, CH = 12, -14, 120, 142
T0 = (0, 0, 0, 0)

# Zonas del sprite (coordenadas del PNG original)
XA = 51        # a la izquierda de esta columna, por encima del torso, solo hay vara
XH = 96        # desde aquí empieza la mano que señala
Y_BOW, Y_HEAD, Y_TORSO, Y_WAIST = 36, 49, 66, 89
ARM_X0, ARM_Y0, ARM_Y1 = 92, 62, 90
SWAY_ROWS = 24  # filas superiores (adorno + vara) que oscilan de lado
ORN = (28, 0, 56, 26)   # caja del adorno de la vara (x0, y0, x1, y1)
ORN_CENTER = (40, 11)

W_ = (248, 248, 248)
C_ = (240, 216, 184)
O_ = (240, 176, 128)
R_ = (224, 128, 80)
D_ = (176, 64, 32)
RAMP = [(120, 16, 0), (176, 64, 32), (192, 64, 0), (224, 128, 80),
        (240, 176, 128), (240, 216, 184), (248, 248, 248)]
ALIAS = {(192, 48, 0): (192, 64, 0)}


# ---------------------------------------------------------------- rejilla
def blank():
    return [[T0] * CW for _ in range(CH)]


def get(g, x, y):
    xi, yi = x - X0, y - Y0
    return g[yi][xi] if 0 <= xi < CW and 0 <= yi < CH else T0


def put(g, x, y, c):
    xi, yi = x - X0, y - Y0
    if 0 <= xi < CW and 0 <= yi < CH:
        g[yi][xi] = c + (255,)


def load_source():
    im = Image.open(SRC).convert("RGBA")
    g = blank()
    for y in range(im.height):
        for x in range(im.width):
            xi, yi = x - X0, y - Y0
            if 0 <= xi < CW and 0 <= yi < CH:
                g[yi][xi] = im.getpixel((x, y))
    return g


# ---------------------------------------------------------------- efectos
def glow(src, k):
    """Sube k escalones de la rampa los rojos del adorno (brillo de la punta)."""
    if k == 0:
        return src
    g = [row[:] for row in src]
    for y in range(ORN[1], ORN[3]):
        for x in range(ORN[0], ORN[2]):
            r, gg, b, a = get(src, x, y)
            if not a:
                continue
            col = ALIAS.get((r, gg, b), (r, gg, b))
            if col in RAMP:
                put(g, x, y, RAMP[min(RAMP.index(col) + k, len(RAMP) - 1)])
    return g


def vwarp(src, p):
    """Desplazamiento vertical por zonas (cabeza, lazo, torso, mano); piernas fijas."""
    def shift(x, y):
        if y >= Y_WAIST:
            return 0
        if x < XA:
            return p["T"] if y >= Y_TORSO else 0
        if x >= XH and y >= ARM_Y0:
            return p["T"] + p["f"]
        if y >= Y_TORSO:
            return p["T"]
        if y >= Y_HEAD:
            return p["H"]
        return p["B"]

    g = blank()
    for y in range(Y0, Y0 + CH):
        for x in range(X0, X0 + CW):
            g[y - Y0][x - X0] = get(src, x, y + shift(x, y))
    return g


def sway(src, a):
    if a == 0:
        return src
    g = [row[:] for row in src]
    for y in range(Y0, SWAY_ROWS):
        for x in range(X0, X0 + CW):
            g[y - Y0][x - X0] = get(src, x - a, y)
    return g


def arm_extend(src, n):
    """Alarga (n>0) o acorta (n<0) el antebrazo repitiendo/quitando columnas."""
    if n == 0:
        return src
    g = [row[:] for row in src]
    for y in range(ARM_Y0, ARM_Y1):
        for x in range(ARM_X0, X0 + CW):
            if n > 0:
                sx = ARM_X0 - 1 if x < ARM_X0 + n else x - n
            else:
                sx = x - n
            g[y - Y0][x - X0] = get(src, sx, y)
    return g


def sparks(g, stage, arm):
    import math
    cx, cy = ORN_CENTER

    def free(x, y):
        return get(g, x, y)[3] == 0      # las chispas nunca pisan píxeles del sprite

    def dot(x, y, col):
        if free(x, y):
            put(g, x, y, col)

    def plus(x, y, core, arm_col, n=1):
        dot(x, y, core)
        for d in range(1, n + 1):
            for dx, dy in ((d, 0), (-d, 0), (0, d), (0, -d)):
                dot(x + dx, y + dy, arm_col)

    def at(r, i, n, off=0.0):
        a = off + 2 * math.pi * i / n
        return round(cx + r * math.cos(a)), round(cy + r * math.sin(a))

    if stage == 1:                        # carga: puntos que se acercan
        for i in range(4):
            dot(*at(12, i, 4, 0.78), W_)
    elif stage == 2:                      # flash: cruces grandes y brillantes
        for i in range(8):
            plus(*at(14, i, 8), W_, C_, 1)
        for i in range(8):
            dot(*at(19, i, 8, 0.39), O_)
    elif stage == 3:                      # expansión: cruces y rayas
        for i in range(8):
            plus(*at(18, i, 8, 0.39), C_, O_, 1)
        for i in range(8):
            x, y = at(23, i, 8)
            dot(x, y, R_)
    elif stage == 4:                      # se disipa
        for i in range(8):
            x, y = at(22, i, 8, 0.2)
            dot(x, y, O_)
            dot(*at(25, i, 8, 0.2), D_)
    elif stage == 5:
        for i in range(4):
            dot(*at(26, i, 4, 0.9), D_)
    # destello en la punta del dedo (sigue la extensión del brazo)
    tx, ty = 119 + arm, 77
    if stage == 1:
        dot(tx, ty, W_)
    elif stage in (2, 3):
        plus(tx, ty, W_, C_, 2 if stage == 2 else 1)
        dot(tx + 4, ty, O_)
    elif stage == 4:
        plus(tx, ty, C_, O_, 1)
    elif stage == 5:
        dot(tx, ty, R_)
    return g


def render(p, src):
    g = glow(src, p["glow"])
    g = vwarp(g, p)
    g = arm_extend(g, p["arm"])
    g = sway(g, p["a"])
    if p.get("sp"):
        g = sparks(g, p["sp"], p["arm"])
    return g


def P(T=0, H=0, B=0, f=0, glow=0, arm=0, a=0, sp=0):
    return dict(T=T, H=H, B=B, f=f, glow=glow, arm=arm, a=a, sp=sp)


# ---------------------------------------------------------------- guiones
IDLE_T = [0, 1, 1, 1, 1, 0, 0, 0]
IDLE_H = [0, 0, 1, 1, 1, 1, 0, 0]
IDLE_B = [0, 0, 0, 1, 2, 2, 1, 0]
IDLE_G = [0, 1, 2, 2, 1, 0, 0, 0]
IDLE_A = [0, 1, 1, 0, 0, -1, -1, 0]
IDLE = [P(T=IDLE_T[i], H=IDLE_H[i], B=IDLE_B[i], f=IDLE_H[i] - IDLE_T[i],
          glow=IDLE_G[i], a=IDLE_A[i]) for i in range(8)]
IDLE_MS = [110] * 8

FLASH = [
    P(),
    P(T=-1, H=-1, B=0, f=0, glow=1, arm=-1, a=-1),
    P(T=1, H=0, B=-1, f=0, glow=3, arm=2, a=1, sp=1),
    P(T=1, H=1, B=0, f=0, glow=4, arm=3, a=1, sp=2),
    P(T=1, H=1, B=1, f=0, glow=3, arm=3, a=0, sp=3),
    P(T=0, H=1, B=1, f=0, glow=3, arm=2, a=-1, sp=4),
    P(T=0, H=0, B=1, f=0, glow=2, arm=1, a=-1, sp=5),
    P(T=0, H=0, B=0, f=0, glow=1, arm=0, a=0),
    P(),
    P(),
]
FLASH_MS = [150, 90, 60, 60, 70, 80, 90, 100, 120, 200]


# ---------------------------------------------------------------- exportación
def to_image(g):
    im = Image.new("RGBA", (CW, CH))
    im.putdata([c for row in g for c in row])
    return im


def save_gif(frames, durations, path, scale=1):
    imgs = [f.resize((f.width * scale, f.height * scale), Image.NEAREST) if scale > 1 else f
            for f in frames]
    colors = sorted({c[:3] for im in imgs for c in im.getdata() if c[3]})
    assert len(colors) <= 255, len(colors)
    index = {c: i + 1 for i, c in enumerate(colors)}          # 0 = transparente
    flat = [255, 0, 255] + [v for c in colors for v in c]
    pal = []
    for im in imgs:
        p = Image.new("P", im.size, 0)
        p.putpalette(flat + [0] * (768 - len(flat)))
        p.putdata([index[c[:3]] if c[3] else 0 for c in im.getdata()])
        pal.append(p)
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=durations, loop=0,
                transparency=0, disposal=2, optimize=False)
    return len(colors)


def main():
    src = load_source()
    sprite_colors = {c[:3] for row in src for c in row if c[3]}
    print("colores del sprite original:", len(sprite_colors))
    for name, script, ms in (("idle", IDLE, IDLE_MS), ("destello", FLASH, FLASH_MS)):
        frames = [to_image(render(p, src)) for p in script]
        used = {c[:3] for im in frames for c in im.getdata() if c[3]}
        assert used <= sprite_colors, f"colores nuevos: {used - sprite_colors}"
        for scale, suf in ((1, ""), (4, "_x4")):
            path = HERE / f"matilda_{name}{suf}.gif"
            n = save_gif(frames, ms, path, scale)
            print(f"{path.name}: {len(frames)} fotogramas, {n} colores, "
                  f"{path.stat().st_size / 1024:.1f} KB")
        # hoja de contacto para revisar (no se versiona)
        sheet = Image.new("RGBA", (CW * 4 * 5, CH * 4 * ((len(frames) + 4) // 5)), (60, 20, 30, 255))
        for i, f in enumerate(frames):
            big = f.resize((CW * 4, CH * 4), Image.NEAREST)
            sheet.alpha_composite(big, ((i % 5) * CW * 4, (i // 5) * CH * 4))
        sheet.save(Path("/projects/sandbox/tmp") / f"matilda_{name}_sheet.png")


if __name__ == "__main__":
    main()
