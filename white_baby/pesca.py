"""White Baby pesca y de la caña sale Alice en forma de sirena.

Lienzo nativo de 126x126 (ampliación exacta x4 = 504x504), sprites a tamaño natural (1x), 10 fps como 'gif referencia'.
Capas: fondo (cielo, orilla lejana, agua y muelle; estático) -> animación (White Baby, caña, hilo, ondas, Alice, chispas).
Todo el contenido importante queda dentro de la ventana de 80x80 del marco (23..102), que se elegirá más adelante.

Historia (opción 1, ~5,5 s): reposo -> invoca la caña de luz -> lanza -> espera -> pica -> tirón -> columna de ruido que sube del agua ->
holograma -> Alice a color -> la caña se disuelve, Alice se hunde y White Baby vuelve al reposo (bucle sin salto).
Opción 1+3: igual, pero con la escena final (Alice flotando y parpadeando como holograma) alargada.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "alice_heart"))
import sprites as ah   # noqa: E402   (utilidades de extracción de las hojas x3 con fondo gris)

SRC = HERE / "fuentes"
OUT = HERE / "salida"
N, Z, TICK = 126, 4, 100
key = lambda a: a[..., 0].astype(np.uint32) << 16 | a[..., 1].astype(np.uint32) << 8 | a[..., 2]

# ---- geometría de la escena (lienzo de 126x126; ventana 23..102)
PIES = 84                    # fila donde apoyan los pies de White Baby (suelo del muelle)
X0 = 25                      # columna del borde izquierdo de la pose de reposo (el osito queda fijo en todas las poses)
SUPERFICIE = 91              # fila del agua donde cae la boya y donde flota Alice
ALICE_X = 75                 # esquina izquierda de Alice (21 px de ancho -> centro en 85)
BOYA_X = 85
# punta de la caña dentro de cada pose (x, y) y desplazamiento x para que el osito no se mueva
PUNTA = {"p1": (50, 2), "p2": (53, 4), "p3": (54, 5)}
DX_POSE = {"p1": 0, "p2": -1, "p3": 0}

CIAN = [(152, 248, 248), (0, 232, 248), (0, 192, 224)]
HILO = (248, 248, 248)
ROJO_BOYA = (216, 72, 40)


# ====================================================================== sprites
def _componentes(mask):
    seen = np.zeros_like(mask); out = []
    for y, x in zip(*np.nonzero(mask)):
        if seen[y, x]:
            continue
        st, pts = [(y, x)], []
        seen[y, x] = True
        while st:
            cy, cx = st.pop(); pts.append((cy, cx))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1] and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True; st.append((ny, nx))
        out.append(pts)
    return out


def _extraer(fn):
    """Sprites de una hoja (x3, fondo gris) a tamaño natural y fondo transparente, de izquierda a derecha."""
    im = Image.open(SRC / fn).convert("RGB")
    fg = ah._fondo(im)
    rgba = np.dstack([np.asarray(im), (fg * 255).astype(np.uint8)])
    out = []
    for x0, x1 in ah._runs(fg.any(0), 3):
        if x1 - x0 < 8:
            continue
        r = np.nonzero(fg[:, x0:x1 + 1].any(1))[0]
        crop = Image.fromarray(rgba[r.min():r.max() + 1, x0:x1 + 1], "RGBA")
        u, nat = ah._bajar(crop)
        nat = ah._quitar_bolsas(nat)
        out.append(nat.crop(nat.getchannel("A").getbbox()))
    return out


def cargar():
    idle = _extraer("baby_1.png")                   # 6 poses de reposo
    cana = _extraer("baby_2.png")[:3]               # p1, p2, p3 (la cuarta pose es idéntica a la tercera)
    sir = _extraer("baby_3.png")                    # columna de ruido, holograma, color
    # Alice: quitar la pieza oscura que flota (el componente más pequeño de cada estado)
    limpias = []
    for s in sir:
        a = np.array(s)
        comps = _componentes(a[..., 3] > 0)
        comps.sort(key=len)
        for c in comps[:-1]:
            for (y, x) in c:
                a[y, x, 3] = 0
        im = Image.fromarray(a, "RGBA")
        limpias.append(im.crop(im.getchannel("A").getbbox()))
    # p3 sin el hilo que cuelga (se dibuja aparte): se borra la zona del hilo, la boya y el anzuelo
    p3 = np.array(cana[2]); p3[6:, 51:, 3] = 0
    p2 = np.array(cana[1]); p2[6:, 51:, 3] = 0
    return dict(idle=idle, p1=cana[0], p2=cana[1], p3=cana[2],
                p2l=Image.fromarray(p2, "RGBA"), p3l=Image.fromarray(p3, "RGBA"), sir=limpias)


# ====================================================================== fondo
def fondo(estilo="actual"):
    """Fondo estático. estilo: 'actual' (puntos bajo la luna), 'sin' (agua sin reflejo), 'luna' (reflejo de luna), 'faro' (faro en la orilla con su reflejo)."""
    a = np.zeros((N, N, 3), np.uint8)
    cielo = [(8, 12, 34), (12, 20, 46), (16, 30, 58), (22, 42, 72), (30, 58, 90), (42, 78, 108), (60, 100, 124), (84, 124, 142)]
    for y in range(0, 74):
        a[y] = cielo[min(y * len(cielo) // 74, len(cielo) - 1)]
    rs = np.random.RandomState(11)
    for _ in range(26):                                   # estrellas
        x, y = rs.randint(0, N), rs.randint(0, 46)
        a[y, x] = (214, 226, 240) if rs.rand() < .5 else (140, 168, 200)
    # luna
    cx, cy, r = 100, 29, 6
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                a[y, x] = (236, 238, 216)
    for (x, y) in [(98, 27), (99, 27), (102, 31), (100, 32), (97, 30)]:
        a[y, x] = (200, 204, 184)
    # orilla lejana
    for x in range(N):
        h = 5 + int(2 * np.sin(x / 7.0) + 1.5 * np.sin(x / 3.1 + 1))
        for y in range(74 - h, 76):
            a[y, x] = (14, 30, 46)
    for x in (70, 74, 96, 108):
        a[72, x] = (240, 210, 120)
    # agua
    agua = [(40, 86, 116), (34, 76, 106), (28, 66, 96), (24, 58, 88), (20, 50, 80), (16, 42, 70), (12, 34, 60)]
    for y in range(76, N):
        a[y] = agua[min((y - 76) * len(agua) // (N - 76), len(agua) - 1)]
        if (y % 4) == 1:
            a[y] = np.clip(a[y].astype(int) + 10, 0, 255)
    if estilo == "actual":
        for k, y in enumerate(range(78, 104, 3)):           # reflejo de la luna (puntos)
            for x in range(cx - 4 + (k % 2), cx + 5 - (k % 2), 1):
                if (x + k) % 2 == 0:
                    a[y, x] = (150, 176, 170)
    elif estilo == "luna":
        # camino de destellos horizontales bajo la luna: más anchos y más separados hacia abajo, siempre cortados
        rs2 = np.random.RandomState(8)
        y = 77
        while y < 112:
            prof = (y - 77) / 35.0
            ancho = int(round(3 + 8 * prof)) + rs2.randint(-1, 2)
            off = rs2.randint(-2, 3)
            col = tuple(int(c) for c in (np.array((214, 226, 206)) * (1 - 0.55 * prof) + np.array((60, 96, 112)) * 0.55 * prof))
            x0 = cx - ancho // 2 + off
            for x in range(x0, x0 + ancho):
                if 0 <= x < N:
                    a[y, x] = col
            if ancho > 6 and rs2.rand() < .6:                 # el destello se parte en dos
                a[y, x0 + ancho // 2] = a[y - 1, x0 + ancho // 2] if y > 77 else a[y, x0 + ancho // 2]
            y += 2 + (1 if rs2.rand() < .5 else 0)
    elif estilo == "faro":
        # faro en la orilla lejana (x 93..99) con su lámpara y el reflejo de la lámpara en el agua
        cuerpo, franja, tejado, lampara = (22, 36, 54), (58, 80, 104), (14, 24, 38), (252, 228, 142)
        base_y, top_y = 74, 52
        for y in range(top_y, base_y + 1):
            t = (y - top_y) / (base_y - top_y)
            w = 2 + int(round(2 * t))                         # de 5 px arriba a 9 px abajo
            for x in range(96 - w, 96 + w + 1):
                a[y, x] = franja if ((y - top_y) // 5) % 2 == 1 else cuerpo
        for x in range(92, 101):                              # galería
            a[top_y - 1, x] = tejado
        for x in range(94, 99):                               # lámpara
            for y in range(top_y - 4, top_y - 1):
                a[y, x] = lampara
        for x in range(95, 98):
            a[top_y - 5, x] = tejado
        a[top_y - 6, 96] = tejado
        a[top_y + 4, 95:98] = lampara                         # ventanita
        # reflejo: la lámpara en trazos verticales rotos y la silueta del faro apagada
        for k, y in enumerate(range(77, 100)):
            fuerza = max(0.0, 1.0 - (y - 77) / 24.0)
            if k % 3 != 2:
                for x in (95, 96, 97):
                    c = np.array(lampara) * fuerza + a[y, x] * (1 - fuerza)
                    a[y, x] = c.astype(np.uint8)
            if k % 2 == 0:
                for x in (93, 94, 98, 99):
                    c = np.array(cuerpo) * 0.9 * fuerza + a[y, x] * (1 - 0.9 * fuerza)
                    a[y, x] = c.astype(np.uint8)
    # muelle
    top, cara, sombra, junta = (122, 86, 52), (92, 62, 38), (58, 40, 26), (74, 50, 32)
    a[PIES:PIES + 2, 0:60] = top
    a[PIES + 2:PIES + 9, 0:60] = cara
    a[PIES + 8, 0:60] = sombra
    for x in range(6, 60, 12):
        a[PIES:PIES + 9, x] = junta
    for x in range(0, 60, 12):
        a[PIES, x:x + 11] = (136, 98, 60)
    a[PIES + 2:PIES + 9, 59] = sombra
    for px in (6, 22, 40, 54):
        a[PIES + 9:N, px:px + 4] = (44, 30, 22)
        a[PIES + 9:N, px] = (66, 46, 32)
    a[PIES + 9:N, 0:60] = (a[PIES + 9:N, 0:60].astype(int) * 0.72).astype(np.uint8) + np.where(
        (a[PIES + 9:N, 0:60] == 0).all(-1)[..., None], 0, 0).astype(np.uint8)
    for px in (6, 22, 40, 54):
        a[PIES + 9:N, px:px + 4] = (44, 30, 22)
        a[PIES + 9:N, px] = (66, 46, 32)
    return Image.fromarray(a, "RGB").convert("RGBA")


# ====================================================================== utilidades de dibujo
def pegar(lay, spr, x, y):
    sx, sy = max(-x, 0), max(-y, 0)
    dx, dy = max(x, 0), max(y, 0)
    w = min(spr.width - sx, lay.width - dx); h = min(spr.height - sy, lay.height - dy)
    if w > 0 and h > 0:
        lay.alpha_composite(spr.crop((sx, sy, sx + w, sy + h)), (dx, dy))


def punto(lay, x, y, col):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < N and 0 <= y < N:
        lay.putpixel((x, y), tuple(col) + (255,))


def linea(lay, p0, p1, col, ctrl=None):
    """Línea de 1 px (recta o curva de Bézier cuadrática si se da `ctrl`)."""
    n = 220
    for i in range(n + 1):
        t = i / n
        if ctrl is None:
            x = p0[0] + (p1[0] - p0[0]) * t; y = p0[1] + (p1[1] - p0[1]) * t
        else:
            x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * ctrl[0] + t * t * p1[0]
            y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * ctrl[1] + t * t * p1[1]
        c = col[i % len(col)] if isinstance(col, list) else col
        punto(lay, x, y, c)


def anillo(lay, cx, cy, rx, ry, col):
    for i in range(0, 360, 3):
        t = np.deg2rad(i)
        punto(lay, cx + rx * np.cos(t), cy + ry * np.sin(t), col)


def ondas(lay, paso, cx=BOYA_X, cy=SUPERFICIE, activo=True):
    """Dos anillos que se expanden y se apagan (ciclo de 4 pasos, el segundo desfasado 2 pasos)."""
    if not activo:
        return
    cols = [(226, 240, 250), (170, 208, 228), (112, 158, 188), (78, 122, 154)]
    for edad in (paso % 4, (paso + 2) % 4):
        rx = 4 + 2 * edad
        ry = max(1, round(rx / 3.2))
        for i in range(0, 360, 2):
            t = np.deg2rad(i)
            punto(lay, cx + rx * np.cos(t), cy + ry * np.sin(t), cols[edad])


def boya(lay, x, y, hundida=0):
    """Boya de 2 px de ancho: 2 filas rojas y 2 blancas (hundida: solo se ve la parte de arriba)."""
    filas = [ROJO_BOYA, ROJO_BOYA, (248, 248, 248), (248, 248, 248)]
    for k, c in enumerate(filas[: 4 - hundida] if hundida < 4 else []):
        for dx in (0, 1):
            punto(lay, x + dx, y + k, c)


# ====================================================================== pose de White Baby
def chica(S, pose, lay):
    """Pone a White Baby: pose = ('idle', k) | 'p1' | 'p2' | 'p3' | 'p2l' | 'p3l'."""
    if isinstance(pose, tuple):
        s = S["idle"][pose[1]]; x = X0
    else:
        s = S[pose]; x = X0 + DX_POSE[pose[:2]]
    y = PIES - s.height
    pegar(lay, s, x, y)
    return x, y


def punta_abs(pose):
    k = pose[:2]
    s = {"p1": 63, "p2": 61, "p3": 60}[k]
    return (X0 + DX_POSE[k] + PUNTA[k][0], PIES - s + PUNTA[k][1])


# ====================================================================== Alice
NZ = np.random.RandomState(3).rand(N, N)


def sir_array(S, estado):
    """Lienzo de 126x126 (RGBA) con el estado de Alice (0 columna, 1 holograma, 2 color) apoyado en la superficie del agua."""
    s = S["sir"][estado]
    lay = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    pegar(lay, s, ALICE_X, SUPERFICIE - s.height)
    return np.array(lay)


def flujo(a, t):
    """Hace correr los colores de la columna de ruido hacia arriba sin cambiar su silueta."""
    out = a.copy()
    for x in range(N):
        ys = np.nonzero(a[:, x, 3] > 0)[0]
        if len(ys) > 2:
            sh = (t * (2 + x % 2)) % len(ys)
            out[ys, x, :3] = a[ys, x, :3][np.roll(np.arange(len(ys)), sh)]
    return out


def parpadeo(a, t):
    """Holograma: algunas filas se desplazan 1 px a un lado, cambiando con el tiempo."""
    out = a.copy()
    for y in range(N):
        if (y + t) % 6 == 0:
            out[y] = np.roll(a[y], 1 if (y // 6 + t) % 2 else -1, axis=0)
    return out


def revelar(a, p):
    """Muestra solo la parte de abajo del sprite (sube desde el agua): p = 0..1 de su altura."""
    ys = np.nonzero(a[..., 3].any(1))[0]
    top, bot = ys.min(), ys.max()
    h = bot - top + 1
    corte = bot - int(round(h * p)) + 1
    out = a.copy(); out[:corte] = 0
    return out


def mezcla(a, b, p):
    """Disolución píxel a píxel de a hacia b (p = 0..1) con un ruido fijo."""
    m = (NZ < p)[..., None]
    return np.where(m, b, a)


def desplazar(a, dy):
    return np.roll(a, dy, axis=0) if dy else a


def poner(lay, arr):
    lay.alpha_composite(Image.fromarray(arr.astype(np.uint8), "RGBA"))


def chispas(lay, puntos, paso, rs_seed=0):
    rs = np.random.RandomState(rs_seed + paso)
    for (x, y) in puntos:
        for _ in range(2):
            punto(lay, x + rs.randint(-2, 3), y + rs.randint(-2, 3), CIAN[rs.randint(0, 3)])


# ====================================================================== guion
def guion(S, escena_final):
    capas = []

    def nueva():
        return Image.new("RGBA", (N, N), (0, 0, 0, 0))

    base_cana = np.array([X0 + 1, PIES - 63 + 52])      # base de la caña de luz (abajo-izquierda de p1)
    # A. reposo (el pelo se abre)
    for k in (0, 0, 1, 2, 3, 4, 5):
        l = nueva(); chica(S, ("idle", k), l); capas.append(l)
    # B. invoca la caña: partículas que se juntan, caña de luz, caña sólida
    rs = np.random.RandomState(5)
    ang = rs.rand(8) * 2 * np.pi
    for f in (0.55, 0.22):
        l = nueva(); chica(S, ("idle", 5), l)
        for a_ in ang:
            punto(l, base_cana[0] + 22 * f * np.cos(a_) * 1.4, base_cana[1] + 18 * f * np.sin(a_), CIAN[int(a_ * 3) % 3])
        capas.append(l)
    for pose in ("p1", "p2", "p2"):
        l = nueva(); chica(S, pose, l); capas.append(l)
    for _ in range(2):                                     # caña sólida con el hilo que cuelga (la pose original)
        l = nueva(); chica(S, "p3", l); capas.append(l)
    # C. lanza: la boya vuela hasta el agua
    tip = punta_abs("p3l")
    vuelo = [(tip[0] + 2, tip[1] - 3), (tip[0] + 4, tip[1] + 26), (BOYA_X, SUPERFICIE - 1)]
    for i, (bx, by) in enumerate(vuelo):
        l = nueva(); chica(S, "p3l", l)
        linea(l, tip, (bx, by), HILO)
        boya(l, bx, by - 1 if i < 2 else by - 3)
        if i == 2:
            ondas(l, 0)
            for (dx, dy) in [(-3, -3), (-1, -5), (2, -4), (4, -2), (0, -2)]:
                punto(l, bx + dx, SUPERFICIE + dy, (230, 242, 250))
        capas.append(l)
    # D. espera: la boya sube y baja, ondas
    bob = [0, 0, 1, 1, 0, 0, -1]
    for i in range(7):
        l = nueva(); chica(S, "p3l", l)
        by = SUPERFICIE - 3 + bob[i]
        linea(l, tip, (BOYA_X, by), HILO, ctrl=((tip[0] + BOYA_X) / 2 - 5, (tip[1] + by) / 2 + 6))
        boya(l, BOYA_X, by)
        ondas(l, i + 1)
        capas.append(l)
    # E. pica: la boya se hunde
    for i, h in enumerate((2, 3)):
        l = nueva(); chica(S, "p3l", l)
        by = SUPERFICIE - 3 + h
        linea(l, tip, (BOYA_X, by), HILO)
        boya(l, BOYA_X, by, hundida=h)
        ondas(l, 2 * i + 1)
        capas.append(l)
    # F. tirón: la caña vuelve a brillar y el hilo se vuelve de luz
    for i, pose in enumerate(("p2l", "p1", "p2l", "p2l")):
        l = nueva(); chica(S, pose, l)
        t0 = punta_abs(pose)
        linea(l, t0, (BOYA_X, SUPERFICIE - 1), CIAN)
        puntos = [(t0[0] + (BOYA_X - t0[0]) * f, t0[1] + (SUPERFICIE - t0[1]) * f) for f in (0.3, 0.55, 0.8)]
        chispas(l, puntos, i, 20)
        ondas(l, i * 2)
        capas.append(l)
    # G. sube la columna de ruido
    col = sir_array(S, 0)
    for i, p in enumerate((0.25, 0.5, 0.75, 1.0, 1.0)):
        l = nueva(); chica(S, "p2l" if i == 0 else "p3l", l)
        poner(l, revelar(flujo(col, i), p))
        if i == 0:
            linea(l, punta_abs("p2l"), (BOYA_X, SUPERFICIE - 1), CIAN)
        ondas(l, i)
        capas.append(l)
    # H. columna -> holograma (disolución) y parpadeo
    hol = sir_array(S, 1)
    for i, p in enumerate((0.35, 0.7)):
        l = nueva(); chica(S, "p3l", l)
        poner(l, mezcla(flujo(col, 5 + i), parpadeo(hol, i), p)); ondas(l, i + 1); capas.append(l)
    for i in range(3):
        l = nueva(); chica(S, "p3l", l)
        poner(l, desplazar(parpadeo(hol, i + 2), -1 if i == 1 else 0)); ondas(l, i + 3); capas.append(l)
    # I. holograma -> color
    color = sir_array(S, 2)
    for i, p in enumerate((0.4, 0.8)):
        l = nueva(); chica(S, "p3l", l)
        poner(l, mezcla(parpadeo(hol, i), color, p)); ondas(l, i); capas.append(l)
    # escena final: Alice flota (sube y baja) y de vez en cuando parpadea como holograma
    flota = [0, -1, -1, 0, 0, 0]
    for i in range(escena_final):
        l = nueva(); chica(S, "p3l", l)
        dy = flota[i % 6]
        if i % 10 == 7:                                   # destello holograma de un paso
            poner(l, desplazar(parpadeo(hol, i), dy))
        else:
            poner(l, desplazar(color, dy))
        ondas(l, i + 2); capas.append(l)
    # J. vuelta: la caña se disuelve, Alice vuelve a holograma, columna y se hunde; White Baby recupera el reposo
    pasos = [("p2l", 0.5, "mezcla"), ("p1", 1.0, "hol"), (("idle", 5), 0.5, "hol_col"), (("idle", 4), 0.55, "hund"),
             (("idle", 3), 0.25, "hund"), (("idle", 2), 0, None), (("idle", 1), 0, None)]
    for i, (pose, p, modo) in enumerate(pasos):
        l = nueva(); chica(S, pose, l)
        if modo == "mezcla":
            poner(l, mezcla(color, hol, p))
        elif modo == "hol":
            poner(l, parpadeo(hol, i))
        elif modo == "hol_col":
            poner(l, mezcla(hol, flujo(col, i), p))
        elif modo == "hund":
            poner(l, revelar(flujo(col, i), p))
        if isinstance(pose, str):
            chispas(l, [(base_cana[0] + 4, base_cana[1] - 6), (base_cana[0] + 12, base_cana[1] - 16), (base_cana[0] + 20, base_cana[1] - 26)], i, 40)
        if i < 5:
            ondas(l, i + 1)
        capas.append(l)
    return capas


# ====================================================================== GIF
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


def generar(nombre, escena_final, S, bg):
    capas = guion(S, escena_final)
    L = len(capas)
    # la animación debe quedarse dentro del lienzo y de la ventana (23..102) salvo la caña/sprites que pueden asomar al marco
    bb = [c.getchannel("A").getbbox() for c in capas]
    print(f"{nombre}: {L} pasos = {L * TICK / 1000:.1f} s; caja de la animación x {min(b[0] for b in bb)}..{max(b[2] for b in bb)}, "
          f"y {min(b[1] for b in bb)}..{max(b[3] for b in bb)} (ventana 23..102)")
    finales = []
    for c in capas:
        f = bg.copy(); f.alpha_composite(c); finales.append(f.convert("RGB"))
    up = lambda im: im.resize((N * Z, N * Z), Image.NEAREST)
    SEP = OUT / "separado"; SEP.mkdir(parents=True, exist_ok=True)
    n1 = gif_opaco(finales, OUT / f"{nombre}_126.gif", TICK)
    gif_opaco([up(f) for f in finales], OUT / f"{nombre}_x4.gif", TICK)
    n2 = gif_transparente(capas, SEP / f"{nombre}_animacion_sola_126.gif", TICK)
    gif_transparente([up(c) for c in capas], SEP / f"{nombre}_animacion_sola_x4.gif", TICK)
    print(f"  colores: final {n1}, animación sola {n2}")
    # comprobación: fondo + animación == final (126 y x4), y x4 == ampliación exacta de 126
    d = 0
    for tam, suf, fondo_img in ((N, "126", bg), (N * Z, "x4", up(bg))):
        fin = por_paso(OUT / f"{nombre}_{suf}.gif", L, TICK)
        sola = por_paso(SEP / f"{nombre}_animacion_sola_{suf}.gif", L, TICK)
        for t in range(L):
            c = fondo_img.copy(); c.alpha_composite(sola[t])
            d += int((np.abs(np.asarray(c.convert("RGB")).astype(int) - np.asarray(fin[t].convert("RGB")).astype(int)).sum(-1) > 0).sum())
    f126 = por_paso(OUT / f"{nombre}_126.gif", L, TICK); f4 = por_paso(OUT / f"{nombre}_x4.gif", L, TICK)
    d2 = sum(int((np.asarray(up(f126[t].convert("RGB"))).astype(int) != np.asarray(f4[t].convert("RGB")).astype(int)).any(-1).sum()) for t in range(L))
    print(f"  píxeles distintos (fondo + animación vs final, 126 y x4): {d}; (x4 vs ampliación exacta del 126): {d2}")
    for r in (f"{nombre}_126.gif", f"{nombre}_x4.gif", f"separado/{nombre}_animacion_sola_126.gif", f"separado/{nombre}_animacion_sola_x4.gif"):
        print(f"  {r}: {Image.open(OUT / r).size}, {(OUT / r).stat().st_size / 1024:.0f} KB")
    return finales


def hoja(finales, ruta, cols=10, z=2):
    rows = (len(finales) + cols - 1) // cols
    sh = Image.new("RGB", (cols * N * z, rows * N * z))
    for i, f in enumerate(finales):
        sh.paste(f.resize((N * z, N * z), Image.NEAREST), ((i % cols) * N * z, (i // cols) * N * z))
    sh.save(ruta)


def main():
    OUT.mkdir(exist_ok=True)
    S = cargar()
    bg = fondo()
    bg.convert("RGB").save(OUT / "fondo_126.png"); bg.convert("RGB").resize((N * Z, N * Z), Image.NEAREST).save(OUT / "fondo_x4.png")
    f1 = generar("pesca_ciclo_completo", 6, S, bg)
    f2 = generar("pesca_ciclo_con_escena_final", 26, S, bg)
    tmp = Path("/projects/sandbox/tmp/baby"); tmp.mkdir(parents=True, exist_ok=True)
    hoja(f1, tmp / "hoja_pesca.png")
    return S, f1, f2


if __name__ == "__main__":
    main()
