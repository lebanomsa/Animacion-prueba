"""Fondos cósmicos para la animación de Utena (lienzo nativo de 63x63; el suelo empieza en la fila 43).

Cada fondo es una función de t (0..39) que devuelve una imagen RGB de 63x63. Todos se repiten sin salto en los 40 pasos:
las estrellas titilan con ciclo de 8 pasos y lo demás se mueve con un ciclo que divide a 40.
  nebulosa    nubes de gas magenta y azul, con estrellas
  galaxia     una galaxia espiral que gira despacio, con un suelo de rejilla
  planeta     un planeta dorado con anillos y una luna pequeña
  viaLactea   la banda de la Vía Láctea con una estrella fugaz y un suelo que la refleja
  agujero     un agujero negro con su disco de acreción dorado y púrpura
La sombra de Utena (misma forma que en el escenario original) se pinta con un color oscuro al final.
"""
import numpy as np

NC, HORIZ = 63, 43
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
YY, XX = np.mgrid[0:NC, 0:NC]
DIT = BAYER[YY % 4, XX % 4]

ESTRELLAS = {   # tipo: (tenue, media, brillante)
    "b": ((120, 120, 160), (200, 204, 232), (252, 252, 255)),
    "c": ((90, 130, 170), (160, 206, 244), (226, 246, 255)),
    "o": ((150, 110, 60), (226, 180, 96), (255, 232, 160)),
    "v": ((110, 80, 160), (176, 140, 232), (238, 214, 255)),
}
BRILLO = [1, 2, 1, 0, 0, 0, 1, 1]            # ciclo de titileo de 8 pasos (0 tenue, 1 media, 2 brillante)


def ruido(seed, escala):
    rs = np.random.RandomState(seed)
    gw, gh = int(NC / escala) + 3, int(NC / escala) + 3
    g = rs.rand(gh, gw)
    fx, fy = XX / escala, YY / escala
    x0, y0 = fx.astype(int), fy.astype(int)
    tx, ty = fx - x0, fy - y0
    sx, sy = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    a = g[y0, x0] * (1 - sx) + g[y0, x0 + 1] * sx
    b = g[y0 + 1, x0] * (1 - sx) + g[y0 + 1, x0 + 1] * sx
    return a * (1 - sy) + b * sy


def degradado(colores, h=HORIZ):
    pos = np.arange(h)[:, None] / (h - 1) * (len(colores) - 1) * np.ones((1, NC))
    i0 = np.floor(pos).astype(int)
    i1 = np.minimum(i0 + 1, len(colores) - 1)
    usa1 = (pos - i0) > DIT[:h]
    return np.array(colores, np.uint8)[np.where(usa1, i1, i0)]


def estrellas(img, t, n, seed, tipos="bbbcov", zona=(0, HORIZ), evitar=None, grandes=3):
    rs = np.random.RandomState(seed)
    for k in range(n):
        x, y = rs.randint(0, NC), rs.randint(zona[0], zona[1])
        tp = tipos[rs.randint(0, len(tipos))]
        fase = rs.randint(0, 8)
        if evitar is not None and evitar(x, y):
            continue
        lvl = BRILLO[(t + fase) % 8]
        img[y, x] = ESTRELLAS[tp][lvl]
        if k < grandes and lvl == 2:                       # las primeras estrellas brillan con cruz
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if 0 <= x + dx < NC and 0 <= y + dy < HORIZ:
                    img[y + dy, x + dx] = ESTRELLAS[tp][1]


def suelo(img, base, horizonte, lineas=None):
    img[HORIZ:] = base
    img[HORIZ] = horizonte
    if lineas:
        for y, c in lineas:
            img[y] = c


# ------------------------------------------------------------------------------------------------ nebulosa
def nebulosa(t):
    img = degradado([(8, 6, 28), (12, 8, 36), (18, 10, 46), (26, 14, 58), (34, 18, 68), (42, 22, 78)]).copy()
    img = np.vstack([img, np.zeros((NC - HORIZ, NC, 3), np.uint8)])
    off = int(round(1.4 * np.sin(2 * np.pi * t / 40)))
    n1 = np.roll(0.6 * ruido(1, 15) + 0.4 * ruido(2, 6), off, axis=1) + (DIT - 0.5) * 0.10
    n2 = np.roll(0.6 * ruido(5, 13) + 0.4 * ruido(6, 5), -off, axis=1) + (DIT - 0.5) * 0.10
    mag = [(78, 24, 92), (122, 44, 130), (172, 82, 172), (232, 150, 214)]
    azu = [(22, 52, 108), (36, 92, 150), (78, 150, 196)]
    for thr, c in zip((0.56, 0.66, 0.76, 0.86), mag):
        img[:HORIZ][n1[:HORIZ] > thr] = c
    for thr, c in zip((0.62, 0.72, 0.82), azu):
        m = (n2[:HORIZ] > thr) & (n1[:HORIZ] < 0.66)
        img[:HORIZ][m] = c
    estrellas(img, t, 46, 3)
    suelo(img, (14, 8, 36), (110, 60, 150), [(44, (52, 28, 96)), (47, (24, 14, 54)), (52, (22, 12, 50)), (58, (20, 12, 46))])
    return img


# ------------------------------------------------------------------------------------------------ galaxia
def galaxia(t):
    img = degradado([(4, 3, 18), (8, 5, 26), (12, 8, 34), (16, 10, 42)]).copy()
    img = np.vstack([img, np.zeros((NC - HORIZ, NC, 3), np.uint8)])
    cx, cy, R = 21, 20, 25
    dx, dy = XX - cx, (YY - cy) * 1.55
    r = np.hypot(dx, dy)
    th = np.arctan2(dy, dx)
    ang = th - np.pi * t / 40.0 - np.log(np.maximum(r, 1.0)) / 0.30        # girar media vuelta = misma imagen (dos brazos)
    brazo = (0.5 + 0.5 * np.cos(2 * ang)) ** 1.6
    inten = brazo * np.exp(-r / (R * 0.55)) + 1.4 * np.exp(-(r / (R * 0.15)) ** 2)
    inten = inten + (DIT - 0.5) * 0.08
    cols = [(28, 18, 62), (52, 30, 100), (88, 54, 148), (138, 90, 190), (206, 152, 226), (255, 232, 188)]
    for thr, c in zip((0.05, 0.12, 0.22, 0.38, 0.62, 0.95), cols):
        m = inten[:HORIZ] > thr
        img[:HORIZ][m] = c
    estrellas(img, t, 40, 7, evitar=lambda x, y: inten[y, x] > 0.5)
    suelo(img, (8, 5, 24), (96, 56, 150))
    # rejilla en perspectiva
    for k in range(-9, 10):
        for y in range(HORIZ + 1, NC):
            f = (y - HORIZ) / float(NC - HORIZ)
            x = int(round(31 + k * (3 + 14 * f)))
            if 0 <= x < NC:
                img[y, x] = (44, 26, 92)
    for y in (45, 48, 52, 57, 62):
        img[y] = np.where((img[y] == (8, 5, 24)).all(-1)[:, None], (30, 18, 66), img[y])
    return img


# ------------------------------------------------------------------------------------------------ planeta
def disco(img, cx, cy, r, bandas, luz=(0.6, -0.7)):
    for y in range(max(0, cy - r), min(NC, cy + r + 1)):
        for x in range(max(0, cx - r), min(NC, cx + r + 1)):
            d = np.hypot(x - cx, y - cy)
            if d <= r + 0.2:
                nx, ny = (x - cx) / r, (y - cy) / r
                sh = (nx * luz[0] + ny * luz[1]) / np.hypot(*luz)          # 1 cerca de la luz, -1 lejos
                banda = int((y - cy + r) * len(bandas) / (2 * r + 1)) % len(bandas)
                nivel = 0 if sh > 0.35 else 1 if sh > -0.1 else 2 if sh > -0.55 else 3
                img[y, x] = bandas[banda][nivel]


def anillo(img, cx, cy, a, b, ang, delante, ancho=(0.78, 1.0), cols=((120, 90, 170), (180, 150, 214), (232, 206, 244))):
    ca, sa = np.cos(ang), np.sin(ang)
    for y in range(NC):
        for x in range(NC):
            u, v = (x - cx) * ca + (y - cy) * sa, -(x - cx) * sa + (y - cy) * ca
            n = np.hypot(u / a, v / b)
            if ancho[0] <= n <= ancho[1] and ((v > 0) == delante) and y < HORIZ:
                k = 0 if n < 0.87 else 1 if n < 0.95 else 2
                img[y, x] = cols[k]


def planeta(t):
    img = degradado([(6, 4, 22), (10, 6, 30), (16, 10, 40), (24, 14, 54)]).copy()
    img = np.vstack([img, np.zeros((NC - HORIZ, NC, 3), np.uint8)])
    estrellas(img, t, 44, 11, evitar=lambda x, y: np.hypot(x - 15, y - 17) < 20)
    anillo(img, 15, 17, 19, 5.2, -0.38, False)
    gold = [((255, 230, 140), (232, 184, 74), (176, 120, 40), (110, 70, 34)),
            ((250, 214, 110), (214, 160, 52), (156, 104, 34), (96, 62, 32)),
            ((240, 196, 120), (200, 140, 60), (140, 92, 40), (92, 58, 40)),
            ((250, 214, 110), (214, 160, 52), (156, 104, 34), (96, 62, 32))]
    disco(img, 15, 17, 10, gold)
    anillo(img, 15, 17, 19, 5.2, -0.38, True)
    disco(img, 54, 31, 2, [((226, 214, 240), (170, 156, 204), (110, 96, 150), (70, 60, 110))], luz=(0.6, -0.5))
    suelo(img, (16, 10, 40), (84, 56, 126), [(44, (40, 26, 80))])
    rs = np.random.RandomState(4)
    for (cx_, cy_, rx) in ((10, 50, 6), (44, 55, 8), (26, 60, 5), (54, 48, 4)):         # cráteres
        for i in range(0, 360, 6):
            a_ = np.deg2rad(i)
            x, y = int(round(cx_ + rx * np.cos(a_))), int(round(cy_ + rx * 0.3 * np.sin(a_)))
            if 0 <= x < NC and HORIZ < y < NC:
                img[y, x] = (46, 30, 92) if np.sin(a_) > 0 else (26, 16, 56)
    for _ in range(40):
        x, y = rs.randint(0, NC), rs.randint(HORIZ + 2, NC)
        img[y, x] = (30, 20, 66)
    return img


# ------------------------------------------------------------------------------------------------ Vía Láctea
def via_lactea(t):
    img = degradado([(4, 3, 18), (8, 5, 28), (12, 8, 36)]).copy()
    img = np.vstack([img, np.zeros((NC - HORIZ, NC, 3), np.uint8)])
    # banda diagonal de (0, 40) a (62, 6)
    x0, y0, x1, y1 = 0.0, 40.0, 62.0, 6.0
    L_ = np.hypot(x1 - x0, y1 - y0)
    d = ((XX - x0) * (y1 - y0) - (YY - y0) * (x1 - x0)) / L_
    dens = np.exp(-(d / 8.5) ** 2) * (0.55 + 0.6 * ruido(21, 9)) - 0.35 * np.exp(-(d / 1.6) ** 2) * ruido(22, 5)
    dens = dens + (DIT - 0.5) * 0.10
    cols = [(20, 14, 52), (36, 26, 84), (62, 46, 124), (100, 78, 164), (150, 128, 204), (214, 198, 238)]
    for thr, c in zip((0.14, 0.26, 0.42, 0.6, 0.8, 1.05), cols):
        m = dens[:HORIZ] > thr
        img[:HORIZ][m] = c
    rs = np.random.RandomState(31)
    for _ in range(190):                                   # estrellitas densas dentro de la banda
        x, y = rs.randint(0, NC), rs.randint(0, HORIZ)
        if dens[y, x] > 0.2 and rs.rand() < 0.7:
            img[y, x] = ESTRELLAS["b"][1 + (rs.rand() < 0.25)] if rs.rand() < 0.5 else ESTRELLAS["v"][1]
    estrellas(img, t, 26, 33, evitar=lambda x, y: dens[y, x] > 0.5)
    if 24 <= t <= 31:                                      # estrella fugaz
        s = (t - 24) / 7.0
        hx, hy = 58 - 34 * s, 3 + 20 * s
        for k in range(8):
            px_, py_ = int(round(hx + k * 1.7)), int(round(hy - k * 1.0))
            if 0 <= px_ < NC and 0 <= py_ < HORIZ:
                img[py_, px_] = [(252, 252, 255), (226, 236, 255), (176, 196, 240), (130, 150, 210), (90, 104, 170), (60, 70, 130), (40, 46, 96), (30, 34, 70)][k]
    # suelo: reflejo del cielo, apagado
    suelo(img, (10, 6, 28), (84, 60, 130))
    for k in range(1, NC - HORIZ):
        y_src = HORIZ - 1 - int(k * 0.85)
        if y_src < 0:
            break
        fila = img[y_src].astype(int)
        mezcla = (fila * 0.42 + np.array((10, 6, 28)) * 0.58).astype(int)
        mezcla = (mezcla // 12) * 12                       # menos tonos distintos
        keep = (k % 2 == 0) | (DIT[HORIZ + k] > 0.5)
        img[HORIZ + k] = np.where(keep[..., None] if hasattr(keep, "shape") else keep, mezcla, (10, 6, 28)).astype(np.uint8)
    img[HORIZ] = (84, 60, 130)
    return img


# ------------------------------------------------------------------------------------------------ agujero negro
def agujero(t):
    img = degradado([(4, 2, 14), (8, 4, 22), (14, 6, 30), (22, 10, 40)]).copy()
    img = np.vstack([img, np.zeros((NC - HORIZ, NC, 3), np.uint8)])
    cx, cy = 16, 19
    estrellas(img, t, 40, 41, evitar=lambda x, y: np.hypot(x - cx, y - cy) < 17)
    ang, a, b = -0.30, 17.0, 4.6
    ca, sa = np.cos(ang), np.sin(ang)

    def disco_acrecion(parte):
        for y in range(NC):
            for x in range(NC):
                u, v = (x - cx) * ca + (y - cy) * sa, -(x - cx) * sa + (y - cy) * ca
                n = np.hypot(u / a, v / b)
                if 0.38 <= n <= 1.0 and y < HORIZ and ((v > 0) == parte):
                    th = np.arctan2(v / b, u / a)
                    giro = (np.cos(2 * th - 2 * np.pi * t / 40.0 * 2) + 1) / 2          # zonas brillantes que giran
                    k = (1 - (n - 0.38) / 0.62)                                        # más caliente por dentro
                    nivel = k * 0.75 + giro * 0.35
                    c = ((70, 30, 130), (150, 60, 170), (232, 120, 70), (250, 190, 80), (255, 236, 170))[min(4, int(nivel * 4.2))]
                    img[y, x] = c
    disco_acrecion(False)                                  # parte de atrás
    for y in range(NC):
        for x in range(NC):
            if np.hypot(x - cx, y - cy) <= 6.2:
                img[y, x] = (1, 0, 6)
            elif np.hypot(x - cx, y - cy) <= 7.2 and y < HORIZ:
                img[y, x] = (255, 214, 140) if np.hypot(x - cx, (y - cy) * 1.0) <= 6.9 else (150, 80, 160)
    # arco por encima: la luz del disco de atrás curvada por la gravedad
    for i in range(200, 340, 3):
        r_ = 9.6
        x, y = int(round(cx + r_ * np.cos(np.deg2rad(i)))), int(round(cy + r_ * 0.82 * np.sin(np.deg2rad(i))))
        if 0 <= x < NC and 0 <= y < HORIZ:
            img[y, x] = (214, 120, 60) if i % 2 else (170, 80, 150)
    disco_acrecion(True)                                   # parte de delante
    suelo(img, (8, 4, 20), (120, 60, 70))
    for k, y in enumerate(range(44, 62, 2)):               # reflejo dorado del disco
        for x in range(10 + k, 22 - k // 2):
            img[y, x] = (96 - 4 * k, 48 - 2 * k, 40) if (x + y) % 2 else (8, 4, 20)
    return img


FONDOS = {"nebulosa": nebulosa, "galaxia": galaxia, "planeta": planeta, "viaLactea": via_lactea, "agujero": agujero}
SOMBRA = (4, 2, 12)


def con_sombras(nombre, mask_normal, mask_peq):
    """bgf(t) -> (fondo, fondo con sombra pequeña) listo para la animación."""
    fn = FONDOS[nombre]
    cache = {}

    def bgf(t):
        if t not in cache:
            base = np.clip(fn(t), 0, 255).astype(np.uint8)
            a, b = base.copy(), base.copy()
            a[mask_normal] = SOMBRA
            b[mask_peq] = SOMBRA
            cache[t] = (a, b)
        return cache[t]
    return bgf
