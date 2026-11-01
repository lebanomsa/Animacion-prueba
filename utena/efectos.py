"""Detalles de vergüenza para la animación de Utena con el traje (se dibujan sobre cada fotograma, a tamaño real).

Opciones (solo desde el sobresalto, paso 7, hasta el final del bucle):
  A sonrojo     rayitas rosas en las mejillas, que laten (más intensas en pasos alternos)
  B gotita      gota de sudor junto a la cabeza que resbala 1 px cada 2 pasos
  C vapor       nubecitas que suben de la cabeza, como si echara humo de la vergüenza
  D sobresalto  rayitas de sorpresa sobre la cabeza en el sobresalto, y un temblor (rayitas a los lados) en el balanceo
  E combinación sonrojo + gotita + rayitas de sorpresa (sin temblor)
Las posiciones están en coordenadas de la pose 1 y se mueven con la cabeza de cada fotograma.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import animacion

HERE = Path(__file__).parent
PREV = HERE / "previews"
ROSA, ROSA_O = (237, 143, 138), (200, 87, 97)
GOTA = {"w": (240, 250, 255), "b": (130, 200, 245), "B": (70, 130, 210), "o": (40, 60, 110)}
VAPOR = [(250, 250, 255), (205, 205, 220), (150, 150, 170)]
LINEA = (246, 246, 255)


def offsets(origen):
    """Desplazamiento de la cabeza (dx, dy) de cada paso respecto de la pose 1."""
    out = []
    for o in origen:
        k = int(o.split()[0])
        if k <= 5:
            out.append((0, 0))
        elif k == 6:
            out.append((-2, 3))
        elif k == 7 or k % 2 == 0:
            out.append((-4, 4))
        else:
            out.append((-3, 4))
    return out


def px(a, x, y, c):
    if 0 <= x < a.shape[1] and 0 <= y < a.shape[0]:
        a[y, x, :3] = c
        a[y, x, 3] = 255


def sonrojo(a, dx, dy, fuerte):
    for (x0, y0) in ((39, 35), (41, 35), (48, 35), (50, 35)):      # dos rayitas "//" en cada mejilla
        px(a, x0 + dx, y0 + dy, ROSA_O)
        px(a, x0 - 1 + dx, y0 + 1 + dy, ROSA_O)
        if fuerte:
            px(a, x0 + 1 + dx, y0 + dy, ROSA)
            px(a, x0 + dx, y0 + 1 + dy, ROSA)


def gotita(a, dx, dy, t):
    filas = ["..b..", "..b..", ".bwb.", ".wbb.", "bwbbB", "bbbBB", ".bBB."]   # gota: punta arriba, panza redonda abajo
    caida = (t // 2) % 4                                               # resbala 3 px y vuelve a empezar
    x0, y0 = 58 + dx, 24 + dy + caida
    for j, f in enumerate(filas):
        for i, ch in enumerate(f):
            if ch != ".":
                px(a, x0 + i, y0 + j, GOTA[ch])
    for j, f in enumerate(filas):                                      # contorno fino
        for i, ch in enumerate(f):
            if ch == ".":
                continue
            for (ex, ey) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ii, jj = i + ex, j + ey
                if not (0 <= jj < len(filas) and 0 <= ii < len(filas[0])) or filas[jj][ii] == ".":
                    xx, yy = x0 + ii, y0 + jj
                    if 0 <= xx < a.shape[1] and 0 <= yy < a.shape[0] and a[yy, xx, 3] == 0:
                        px(a, xx, yy, GOTA["o"])


def vapor(a, dx, dy, t):
    """Tres nubecitas de vapor que salen de la cabeza, crecen al subir y se desvanecen (ciclo de 6 pasos)."""
    for k, (x0, fase) in enumerate(((39, 0), (46, 2), (53, 4))):
        u = (t + fase) % 6
        cx = x0 + dx + (1 if u in (2, 3) else (0 if u < 2 else -1))
        cy = 16 + dy - u * 2
        r = (1.3, 1.8, 2.3, 2.6, 2.6, 2.2)[u]
        base, luz, borde = ((236, 236, 246), (255, 255, 255), (150, 150, 172)) if u < 4 else ((190, 190, 206), (220, 220, 232), (120, 120, 140))
        for ey in range(-3, 4):
            for ex in range(-3, 4):
                d = np.hypot(ex, ey * 1.15)
                x, y = int(cx + ex), int(cy + ey)
                if 0 <= x < a.shape[1] and 0 <= y < a.shape[0] and a[y, x, 3] == 0:
                    if d <= r - 0.8:
                        px(a, x, y, luz if (ex < 0 and ey < 0) else base)
                    elif d <= r:
                        px(a, x, y, borde)


def sorpresa(a, dx, dy):
    for (xa, ya, xb, yb) in ((37, 11, 39, 14), (44, 8, 44, 12), (51, 11, 49, 14)):
        n = max(abs(xb - xa), abs(yb - ya))
        for i in range(n + 1):
            x = round(xa + (xb - xa) * i / n) + dx; y = round(ya + (yb - ya) * i / n) + dy
            if a[y, x, 3] == 0:
                px(a, x, y, LINEA)


def temblor(a, dx, dy, t):
    """Dos pares de rayitas a los lados del cuerpo que alternan de posición (sensación de temblar)."""
    pares = (((24, 48), (21, 50)), ((66, 48), (69, 50))) if t % 2 == 0 else (((23, 52), (20, 54)), ((67, 52), (70, 54)))
    for (p0, p1) in pares:
        for (x, y0) in (p0, p1):
            for j in range(4):
                yy = y0 + dy + j
                if a[yy, x + dx, 3] == 0:
                    px(a, x + dx, yy, (226, 226, 240))


def aplicar(cuadros, origen, opcion):
    offs = offsets(origen)
    out = []
    for t, (c, (dx, dy)) in enumerate(zip(cuadros, offs)):
        a = np.array(c)
        k = int(origen[t].split()[0])
        verguenza = t >= 6                                              # desde el sobresalto (paso 7)
        if verguenza:
            if opcion in ("A", "E"):
                sonrojo(a, dx, dy, fuerte=(t % 2 == 0))
            if opcion in ("B", "E"):
                gotita(a, dx, dy, t)
            if opcion == "C":
                vapor(a, dx, dy, t)
            if opcion in ("D", "E") and k == 6:
                sorpresa(a, dx, dy)
            if opcion == "D" and k >= 8:
                temblor(a, dx, dy, t)
        out.append(Image.fromarray(a, "RGBA"))
    return out


NOMBRES = {"A": "sonrojo", "B": "gotita", "C": "vapor", "D": "sobresalto_y_temblor", "E": "combinacion"}


def main():
    PREV.mkdir(exist_ok=True)
    cuadros, durs, origen = animacion.secuencia()
    S = 6
    rec = (16, 2, 76, 70)
    pasos = (6, 7, 10, 15)
    filas = []
    for op, nombre in NOMBRES.items():
        fr = aplicar(cuadros, origen, op)
        ruta = PREV / f"verguenza_{op}_{nombre}.gif"
        n = animacion.guardar(fr, durs, ruta, 4, fondo=(46, 46, 56))
        print(f"{ruta.name}: {n} colores, {ruta.stat().st_size / 1024:.0f} KB")
        fila = []
        for t in pasos:
            b = Image.new("RGBA", fr[t].size, (46, 46, 56, 255)); b.alpha_composite(fr[t])
            fila.append(b.convert("RGB").crop(rec).resize(((rec[2] - rec[0]) * S, (rec[3] - rec[1]) * S), Image.NEAREST))
        filas.append((f"{op} {nombre.replace('_', ' ')}", fila))
    w, h = filas[0][1][0].size
    hoja = Image.new("RGB", (len(pasos) * (w + 6) + 6, len(filas) * (h + 22)), (30, 30, 40))
    d = ImageDraw.Draw(hoja)
    for r, (titulo, fila) in enumerate(filas):
        y = r * (h + 22)
        for i, p in enumerate(fila):
            hoja.paste(p, (i * (w + 6), y + 20))
            d.text((i * (w + 6) + 4, y + 4), f"{titulo} - paso {pasos[i] + 1}", fill=(255, 230, 120))
    hoja.save(PREV / "verguenza_opciones.png")
    print(hoja.size)


if __name__ == "__main__":
    main()
