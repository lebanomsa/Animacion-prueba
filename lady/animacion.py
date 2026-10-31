"""Animación de Lady sobre el escenario B (silueta negra) con relámpago, con distintas opciones de cierre del bucle (48 pasos de 80 ms).

  reposo (5) -> ignición (7: 1.1, 1.2, 1.3 destello arcoíris, 1.3, 1.4 destello arcoíris) -> llamas (30 = ciclo de 15 dos veces) -> cierre (6)
Cierres: 'reversa' (la ignición al revés: 1.3, 1.2, 1.1), 'relampago' (las llamas siguen y un destello blanco cubre el corte al reposo),
         'corte' (las llamas siguen y se corta al reposo).  'arco' = si se usa el destello arcoíris.
El relámpago del escenario arranca justo cuando el pelo se enciende (paso 10); el segundo cae hacia el final.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import escenario as esc
import hojas

HERE = Path(__file__).parent
PREV = HERE / "previews"
TICK = 80
N = 48
X_C, Y_SUELO = 64, 118
FLASH = (235, 252, 252)


def banda(paso, alto=34):
    """Estado 'banda': franja de arcoíris que baja del pelo a las botas en 10 pasos (filas de la celda de 110)."""
    centro = -alto / 2 + paso * (110 + alto) / 9
    return ("banda", centro - alto / 2, centro + alto / 2)


def guion(cierre, arco, efecto=None):
    """efecto: None (como la opción 1), 'destellos' (parpadeos de arcoíris completos) u 'ondas' (franja de arcoíris que baja)."""
    g = [("1.0", False)] * 5
    g += [("1.1", False)] * 2 + [("1.2", False)] * 2 + [("1.3", arco), ("1.3", False), ("1.4", arco)]
    llamas = [(k, False) for k in hojas.LLAMAS]
    quema = llamas * 2
    if efecto == "destellos":                     # 2 pasos de arcoíris cada 6: pasos 4-5, 10-11, 16-17, 22-23, 28-29 de las llamas
        quema = [(k, (i % 6) in (4, 5)) for i, (k, _) in enumerate(quema)]
    elif efecto == "ondas":                       # tres barridos de 10 pasos
        quema = [(k, banda(i % 10)) for i, (k, _) in enumerate(quema)]
    g += quema
    if cierre == "reversa":
        g += [("1.3", False)] * 2 + [("1.2", False)] * 2 + [("1.1", False)] * 2
    else:
        g += llamas[:6]
    assert len(g) == N, len(g)
    return g


def paso_relampago(t):
    """Paso del relámpago del escenario en el paso t de Lady: primero a los 10 (ignición), segundo a los 34."""
    for ini in (10, 34):
        d = (t - ini) % N
        if d < 8:
            return d
    return -1


def alfa_flash(cierre, t):
    if cierre != "relampago":
        return 0.0
    tabla = {43: 0.25, 44: 0.5, 45: 0.75, 46: 0.9, 47: 1.0, 0: 0.9, 1: 0.6, 2: 0.3}
    return tabla.get(t, 0.0)


def cuadro(cierre, arco, efecto=None):
    g = guion(cierre, arco, efecto)
    frames = []
    for t, (k, a) in enumerate(g):
        win = esc.ventana("B", paso_relampago(t))
        f = (hojas.ARCO if a is True else hojas.NORMAL)[k]
        img = f["img"]
        if isinstance(a, tuple):                   # franja de arcoíris sobre la versión normal
            na, aa = np.array(hojas.NORMAL[k]["img"]), np.array(hojas.ARCO[k]["img"])
            filas = np.arange(na.shape[0])
            m = ((filas >= a[1]) & (filas <= a[2]))[:, None, None]
            img = Image.fromarray(np.where(m, aa, na).astype(np.uint8), "RGBA")
        ox, oy = int(round(X_C - f["pies"])), Y_SUELO - hojas.SUELO
        win.alpha_composite(img, (ox, oy)) if ox >= 0 and ox + img.width <= 128 else None
        rgb = np.asarray(win.convert("RGB")).astype(float)
        al = alfa_flash(cierre, t)
        if al:
            rgb = rgb + (np.array(FLASH) - rgb) * al
        frames.append(Image.fromarray(rgb.round().astype(np.uint8), "RGB").resize((640, 640), Image.NEAREST))
    return frames


def gif(frs, ruta):
    arrs = [np.asarray(f) for f in frs]
    key = lambda a: a[..., 0].astype(np.uint32) << 16 | a[..., 1].astype(np.uint32) << 8 | a[..., 2]
    keys = np.unique(np.concatenate([key(a).ravel() for a in arrs]))
    n = len(keys)
    if n <= 256:
        pal = np.zeros(768, np.uint8)
        pal[0:n * 3:3], pal[1:n * 3:3], pal[2:n * 3:3] = keys >> 16, keys >> 8 & 255, keys & 255
        out = []
        for a in arrs:
            p = Image.fromarray(np.searchsorted(keys, key(a)).astype(np.uint8), "P"); p.putpalette(pal.tolist()); out.append(p)
    else:
        mosaico = Image.fromarray(np.concatenate([a[::4, ::4] for a in arrs[::2]], axis=0))
        q = mosaico.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        out = [f.quantize(palette=q, dither=Image.Dither.NONE) for f in frs]
    out[0].save(ruta, save_all=True, append_images=out[1:], duration=TICK, loop=0, disposal=1, optimize=False)
    return n


OPCIONES = [("1_reversa_con_arcoiris", "reversa", True, None), ("2_reversa_sin_arcoiris", "reversa", False, None),
            ("3_corte_tapado_por_relampago", "relampago", True, None), ("4_corte_directo", "corte", True, None)]
EFECTOS = [("5_arcoiris_destellos", "reversa", True, "destellos"), ("6_arcoiris_ondas", "reversa", True, "ondas")]


def main(solo_efectos=False):
    PREV.mkdir(exist_ok=True)
    todo = {}
    for nombre, cierre, arco, efecto in (EFECTOS if solo_efectos else OPCIONES):
        fr = cuadro(cierre, arco, efecto)
        todo[nombre] = fr
        ruta = PREV / f"lady_{nombre}.gif"
        n = gif(fr, ruta)
        print(f"{ruta.name}: {n} tonos, {ruta.stat().st_size / 1024:.0f} KB")
    if solo_efectos:
        S = 214
        h3 = Image.new("RGB", (6 * S, len(EFECTOS) * (S + 14)), (14, 10, 20))
        d = ImageDraw.Draw(h3)
        for r, (nombre, _, _, _) in enumerate(EFECTOS):
            d.text((4, r * (S + 14) + 1), nombre, fill=(255, 220, 120))
            for c, t in enumerate((13, 16, 19, 22, 25, 28)):
                h3.paste(todo[nombre][t].resize((S, S), Image.LANCZOS), (c * S, r * (S + 14) + 14))
        h3.save(PREV / "lady_arcoiris_pasos.png")
        return
    # hoja del cierre y la ignición
    cols = 5
    S = 256
    hoja = Image.new("RGB", (cols * S, 4 * (S + 14)), (14, 10, 20))
    d = ImageDraw.Draw(hoja)
    for r, (nombre, _, _, _) in enumerate(OPCIONES):
        d.text((4, r * (S + 14) + 1), nombre, fill=(255, 220, 120))
        for c, t in enumerate((43, 46, 47, 0, 2)):
            hoja.paste(todo[nombre][t].resize((S, S), Image.LANCZOS), (c * S, r * (S + 14) + 14))
    hoja.save(PREV / "lady_cierres.png")
    h2 = Image.new("RGB", (6 * 214, 214 * 2), (14, 10, 20))
    for i, t in enumerate((0, 5, 7, 9, 10, 11, 12, 14, 20, 30, 40, 45)):
        h2.paste(todo[OPCIONES[0][0]][t].resize((214, 214), Image.LANCZOS), ((i % 6) * 214, (i // 6) * 214))
    h2.save(PREV / "lady_secuencia_pasos.png")


if __name__ == "__main__":
    import sys
    main(solo_efectos=len(sys.argv) > 1 and sys.argv[1] == "efectos")
