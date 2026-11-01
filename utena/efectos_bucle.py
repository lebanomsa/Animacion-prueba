"""Cuatro efectos para tapar el corte del bucle de Utena (del balanceo a los brazos abiertos), relacionados con la vergüenza.

Secuencia base: la animación con la combinación de detalles (sonrojo + gotita + rayitas), sin el regreso al revés, y con el
primer fotograma (brazos abiertos, 300 ms) partido en tres de 100 ms para que el efecto se disipe paso a paso.
El efecto dura 8 pasos: s0-s4 en los 5 últimos del balanceo y s5-s7 en los 3 primeros de los brazos abiertos.
El cambio de pose ocurre entre s4 y s5, y ahí el efecto tapa el cuerpo entero.

  1 humo rosa      bomba de humo rosa que crece desde el pecho, cubre todo y se rompe en bolitas
  2 corazones      corazones y destellos que salen del pecho; en el cambio, un destello blanco
  3 vapor          el vapor de la cabeza crece hasta envolverla en una nube blanca que se disipa hacia arriba
  4 sonrojo total  el cuerpo se pone rosa y un destello blanco tapa el cambio
El lienzo se amplía (12 px a los lados, 6 arriba y abajo) para que quepa el efecto.
"""
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import animacion
import efectos

HERE = Path(__file__).parent
PREV = HERE / "previews"
PX, PY = 12, 6
W, H = 96 + 2 * PX, 128 + 2 * PY
YY, XX = np.mgrid[0:H, 0:W]
CENTRO = (47.5 + PX, 66 + PY)          # centro de la zona que hay que tapar (unión de las dos poses)
RX, RY = 41, 58                        # semiejes de la nube completa
PECHO = (46 + PX, 58 + PY)
CABEZA = (45 + PX, 22 + PY)


def secuencia_base():
    cuadros, durs, origen = animacion.secuencia()
    fr = efectos.aplicar(cuadros, origen, "E")[:30]
    durs = durs[:30]
    fr = [fr[0]] * 3 + fr[1:]
    durs = [100, 100, 100] + durs[1:]
    lienzo = []
    for f in fr:
        c = Image.new("RGBA", (W, H), (0, 0, 0, 0)); c.alpha_composite(f, (PX, PY)); lienzo.append(c)
    n = len(lienzo)
    paso = {n - 5 + i: i for i in range(5)}
    paso.update({0: 5, 1: 6, 2: 7})
    return lienzo, durs, paso


# ---- nube con forma de algodón ---------------------------------------------------------------------------------------
def mascara_nube(cx, cy, rx, ry, bultos=14, rb=None, fase=0.0):
    rb = rb or max(3.0, min(rx, ry) * 0.28)
    m = ((XX - cx) / max(rx, 0.5)) ** 2 + ((YY - cy) / max(ry, 0.5)) ** 2 <= 1
    centros = []
    for k in range(bultos):
        a = 2 * math.pi * k / bultos + fase
        bx, by = cx + rx * math.cos(a) * 0.92, cy + ry * math.sin(a) * 0.92
        r = rb * (0.85 + 0.3 * ((k * 7) % 5) / 4)
        m |= np.hypot(XX - bx, YY - by) <= r
        centros.append((bx, by, r))
    return m, centros


def pintar_nube(rgba, m, centros, col):
    base, luz, sombra, borde = col
    if not m.any():
        return
    rgba[m, :3] = base
    rgba[m, 3] = 255
    def fuera(dx, dy):
        p = np.pad(m, 4)
        return ~p[4 + dy:4 + dy + H, 4 + dx:4 + dx + W]
    rgba[m & fuera(-3, -3), :3] = luz                      # luz arriba a la izquierda
    rgba[m & fuera(3, 3), :3] = sombra                     # sombra abajo a la derecha
    for (bx, by, r) in centros:                            # arco interior de cada bulto (textura de algodón)
        anillo = (np.abs(np.hypot(XX - bx, YY - by) - (r - 1.5)) < 0.6) & (YY > by) & m & ~fuera(2, 2)
        rgba[anillo, :3] = sombra
    p = np.pad(m, 1)
    bd = m & (~p[:-2, 1:-1] | ~p[2:, 1:-1] | ~p[1:-1, :-2] | ~p[1:-1, 2:])
    rgba[bd, :3] = borde


def bolitas(rgba, s, col, origen, n=10, lejos=1.15, r=6):
    for k in range(n):
        a = 2 * math.pi * k / n + 0.3
        bx = origen[0] + RX * lejos * math.cos(a)
        by = origen[1] + RY * lejos * math.sin(a)
        mk, cs = mascara_nube(bx, by, r, r, bultos=0, rb=r * 0.3, fase=k)
        pintar_nube(rgba, mk, cs, col)


def destello(rgba, x, y, r, col=(255, 255, 255)):
    for d in range(-r, r + 1):
        for (xx, yy) in ((x + d, y), (x, y + d)):
            if 0 <= xx < W and 0 <= yy < H:
                rgba[yy, xx, :3] = col; rgba[yy, xx, 3] = 255


CORAZON = [".rr.rr.", "rRRrRRr", "rRhRRRr", "rRRRRRr", ".rRRRr.", "..rRr..", "...r..."]
CC = {"r": (180, 40, 95), "R": (255, 115, 165), "h": (255, 255, 255)}


def corazon(rgba, x, y):
    for j, f in enumerate(CORAZON):
        for i, ch in enumerate(f):
            if ch != ".":
                xx, yy = int(x) + i - 3, int(y) + j - 3
                if 0 <= xx < W and 0 <= yy < H:
                    rgba[yy, xx, :3] = CC[ch]; rgba[yy, xx, 3] = 255


ROSA = ((250, 190, 215), (255, 232, 242), (226, 142, 182), (130, 56, 100))
BLANCO = ((234, 234, 244), (255, 255, 255), (188, 188, 208), (96, 96, 122))
FLASH = ((255, 250, 252), (255, 255, 255), (255, 210, 228), (246, 160, 196))


def lerp(a, b, t):
    return a + (b - a) * t


def capa_humo(s):
    rgba = np.zeros((H, W, 4), np.uint8)
    if s <= 5:
        e = (0.22, 0.42, 0.64, 0.86, 1.0, 1.04)[s]
        cx, cy = lerp(PECHO[0], CENTRO[0], e), lerp(PECHO[1], CENTRO[1], e)
        m, cs = mascara_nube(cx, cy, RX * e, RY * e, fase=s * 0.4)
        pintar_nube(rgba, m, cs, ROSA)
    elif s == 6:
        m, cs = mascara_nube(CENTRO[0], CENTRO[1], RX * 0.55, RY * 0.5, fase=1.0)
        bolitas(rgba, s, ROSA, CENTRO, n=11, lejos=1.0, r=8)
    else:
        bolitas(rgba, s, ROSA, CENTRO, n=11, lejos=1.25, r=4)
    return rgba


def capa_corazones(s):
    rgba = np.zeros((H, W, 4), np.uint8)
    if s in (4, 5):
        m, cs = mascara_nube(CENTRO[0], CENTRO[1], RX, RY, bultos=16, rb=7, fase=0.2)
        pintar_nube(rgba, m, cs, FLASH)
    cuantos = (3, 6, 9, 12, 12, 12, 12, 8)[s]
    dist = (8, 16, 24, 32, 46, 50, 54, 60)[s]
    for k in range(cuantos):
        a = 2 * math.pi * k / 12 + 0.25
        x = PECHO[0] + dist * math.cos(a) * 0.8
        y = PECHO[1] + dist * math.sin(a)
        if s < 7:
            corazon(rgba, x, y)
        else:
            destello(rgba, int(x), int(y), 2)
    for k in range(6):                                     # destellos sueltos
        a = 2 * math.pi * k / 6 + s
        destello(rgba, int(PECHO[0] + (dist * 0.6) * math.cos(a)), int(PECHO[1] + (dist * 0.6) * math.sin(a)), 1 + (s + k) % 2)
    return rgba


def capa_vapor(s):
    rgba = np.zeros((H, W, 4), np.uint8)
    if s <= 5:
        e = (0.15, 0.3, 0.55, 0.82, 1.0, 1.04)[s]
        cx, cy = lerp(CABEZA[0], CENTRO[0], e), lerp(CABEZA[1] - 6, CENTRO[1], e)
        m, cs = mascara_nube(cx, cy, RX * e, RY * e, fase=s * 0.5)
        pintar_nube(rgba, m, cs, BLANCO)
        if s <= 3:                                         # chorritos que siguen saliendo de la cabeza
            for k, ox in enumerate((-8, 0, 8)):
                mk, cc = mascara_nube(CABEZA[0] + ox, CABEZA[1] - 10 - 3 * k, 3, 3, bultos=0, rb=1.0, fase=k)
                pintar_nube(rgba, mk, cc, BLANCO)
    else:
        sube = (12, 26)[s - 6]
        for k in range(7):
            a = math.pi + math.pi * k / 6
            bx = CENTRO[0] + RX * 0.9 * math.cos(a)
            by = CENTRO[1] - sube + RY * 0.5 * math.sin(a) - 10
            r = (7, 4)[s - 6]
            mk, cc = mascara_nube(bx, by, r, r, bultos=0, rb=r * 0.3, fase=k)
            pintar_nube(rgba, mk, cc, BLANCO)
    return rgba


def capa_sonrojo(s):
    rgba = np.zeros((H, W, 4), np.uint8)
    if s in (4, 5):
        m = ((XX - CENTRO[0]) / RX) ** 2 + ((YY - CENTRO[1]) / RY) ** 2 <= 1
        m2 = ((XX - CENTRO[0]) / (RX - 3)) ** 2 + ((YY - CENTRO[1]) / (RY - 3)) ** 2 <= 1
        rgba[m, :3] = (255, 196, 220); rgba[m, 3] = 255
        rgba[m2, :3] = (255, 240, 246)
        rgba[((XX - CENTRO[0]) / (RX - 9)) ** 2 + ((YY - CENTRO[1]) / (RY - 9)) ** 2 <= 1, :3] = (255, 255, 255)
    elif s in (6, 7):
        r = (1.06, 1.14)[s - 6]
        anillo = np.abs(np.hypot((XX - CENTRO[0]) / RX, (YY - CENTRO[1]) / RY) - r) < (0.04 if s == 6 else 0.025)
        rgba[anillo, :3] = (255, 180, 210); rgba[anillo, 3] = 255
        for k in range(8):
            a = 2 * math.pi * k / 8 + s
            destello(rgba, int(CENTRO[0] + RX * 0.7 * math.cos(a)), int(CENTRO[1] + RY * 0.7 * math.sin(a)), 2 if s == 6 else 1)
    return rgba


def tinte(personaje, s):
    """Para la opción 4: el cuerpo se va tiñendo de rosa en s0-s3."""
    if s > 3:
        return personaje
    k = (0.15, 0.3, 0.45, 0.6)[s]
    a = np.array(personaje).astype(float)
    m = a[..., 3] > 0
    a[m, :3] = a[m, :3] + (np.array([255, 120, 160]) - a[m, :3]) * k
    return Image.fromarray(a.round().astype(np.uint8), "RGBA")


OPCIONES = [("1_humo_rosa", capa_humo, False), ("2_corazones", capa_corazones, False),
            ("3_vapor", capa_vapor, False), ("4_sonrojo_total", capa_sonrojo, True)]


def construir(capa, con_tinte):
    base, durs, paso = secuencia_base()
    out, visibles = [], {}
    for i, f in enumerate(base):
        if i in paso:
            s = paso[i]
            per = tinte(f, s) if con_tinte else f
            fx = capa(s)
            img = per.copy(); img.alpha_composite(Image.fromarray(fx, "RGBA"))
            if s in (4, 5):
                visibles[s] = int(((np.asarray(f)[..., 3] > 0) & (fx[..., 3] == 0)).sum())
            out.append(img)
        else:
            out.append(f)
    return out, durs, paso, visibles


def main():
    PREV.mkdir(exist_ok=True)
    S = 3
    filas = []
    for nombre, capa, con_tinte in OPCIONES:
        fr, durs, paso, vis = construir(capa, con_tinte)
        ruta = PREV / f"bucle_{nombre}.gif"
        n = animacion.guardar(fr, durs, ruta, 4, fondo=(46, 46, 56))
        print(f"{ruta.name}: {len(fr)} pasos, {sum(durs)} ms, {n} colores, {ruta.stat().st_size / 1024:.0f} KB; "
              f"píxeles de Utena a la vista en el cambio: antes {vis.get(4)} / después {vis.get(5)}")
        orden = sorted(paso, key=lambda i: paso[i])
        fila = []
        for i in orden:
            b = Image.new("RGBA", fr[i].size, (46, 46, 56, 255)); b.alpha_composite(fr[i])
            fila.append(b.convert("RGB").resize((W * S, H * S), Image.NEAREST))
        filas.append((nombre.replace("_", " "), fila))
    hoja = Image.new("RGB", (8 * (W * S + 6), len(filas) * (H * S + 22)), (30, 30, 40))
    d = ImageDraw.Draw(hoja)
    etiquetas = ["fin -4", "fin -3", "fin -2", "fin -1", "último del balanceo", "1º brazos abiertos", "+100 ms", "+200 ms"]
    for r, (titulo, fila) in enumerate(filas):
        y = r * (H * S + 22)
        for i, p in enumerate(fila):
            hoja.paste(p, (i * (W * S + 6), y + 20))
            d.text((i * (W * S + 6) + 4, y + 4), f"{titulo}: {etiquetas[i]}", fill=(255, 230, 120))
    hoja.save(PREV / "bucle_opciones.png")
    print(hoja.size)


if __name__ == "__main__":
    main()
