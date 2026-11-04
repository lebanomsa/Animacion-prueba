"""Animación de pesca de White Baby y Alice dentro del marco elegido: diseño 'muelle' (cuerda trenzada + iconos de pesca) con la paleta
'mar' (plata arriba, verde mar abajo, acentos celestes).

Capas, de atrás hacia delante: fondo (cielo, lago, muelle, reflejo de luna) -> marco -> White Baby, caña, hilo, ondas, Alice y chispas.
Salida (white_baby/salida/con_marco/):
  pesca_marco_ciclo_completo_126.gif / _x4.gif, pesca_marco_con_escena_final_126.gif / _x4.gif   resultado final
  separado/marco_y_fondo_126.png / _x4.png                                                          marco con fondo (estático)
  separado/<ciclo>_animacion_sola_126.gif / _x4.gif                                                 animación sola sobre transparente
Comprueba que (marco y fondo) + animación == GIF final en 126 y x4, y que el x4 es la ampliación exacta del 126.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import pesca as pe                  # noqa: E402
import marco_white_baby as mw       # noqa: E402

TEMA = "muelle_mar"
OUT = HERE / "salida" / "con_marco"
SEP = OUT / "separado"
N, Z, TICK = pe.N, pe.Z, pe.TICK


def componer(bg, marco126, capas):
    base = bg.copy(); base.alpha_composite(marco126)
    fin = []
    for c in capas:
        f = base.copy(); f.alpha_composite(c); fin.append(f.convert("RGB"))
    return base, fin


def contar(fin):
    return len(np.unique(np.concatenate([pe.key(np.asarray(f)).ravel() for f in fin])))


def main():
    OUT.mkdir(parents=True, exist_ok=True); SEP.mkdir(exist_ok=True)
    S = pe.cargar(); bg = pe.fondo("luna")
    ciclos = {"pesca_marco_ciclo_completo": pe.guion(S, 6), "pesca_marco_con_escena_final": pe.guion(S, 26)}
    # tonos del marco: bajar hasta que todos los fotogramas quepan en 256 colores
    k = 120
    while True:
        img, win = mw.build(TEMA, k=k)
        marco126 = Image.fromarray(img, "RGBA").crop((1, 1, 127, 127))
        peor = max(contar(componer(bg, marco126, capas)[1]) for capas in ciclos.values())
        if peor <= 256:
            break
        k -= max(1, peor - 256)
    print(f"marco con {k} tonos (+ detalles); paleta máxima por GIF: {peor} colores; ventana {win}")
    up = lambda im: im.resize((N * Z, N * Z), Image.NEAREST)

    for nombre, capas in ciclos.items():
        base, fin = componer(bg, marco126, capas)
        L = len(capas)
        n1 = pe.gif_opaco(fin, OUT / f"{nombre}_126.gif", TICK)
        pe.gif_opaco([up(f) for f in fin], OUT / f"{nombre}_x4.gif", TICK)
        n2 = pe.gif_transparente(capas, SEP / f"{nombre}_animacion_sola_126.gif", TICK)
        pe.gif_transparente([up(c) for c in capas], SEP / f"{nombre}_animacion_sola_x4.gif", TICK)
        base.convert("RGB").save(SEP / "marco_y_fondo_126.png"); up(base.convert("RGB")).save(SEP / "marco_y_fondo_x4.png")
        print(f"{nombre}: {L} pasos = {L * TICK / 1000:.1f} s; colores: final {n1}, animación sola {n2}")
        d = 0
        for suf, fondo_img in (("126", base), ("x4", up(base))):
            f_ = pe.por_paso(OUT / f"{nombre}_{suf}.gif", L, TICK)
            s_ = pe.por_paso(SEP / f"{nombre}_animacion_sola_{suf}.gif", L, TICK)
            for t in range(L):
                c = fondo_img.copy(); c.alpha_composite(s_[t])
                d += int((np.abs(np.asarray(c.convert("RGB")).astype(int) - np.asarray(f_[t].convert("RGB")).astype(int)).sum(-1) > 0).sum())
        f126 = pe.por_paso(OUT / f"{nombre}_126.gif", L, TICK); f4 = pe.por_paso(OUT / f"{nombre}_x4.gif", L, TICK)
        d2 = sum(int((np.asarray(up(f126[t].convert("RGB"))).astype(int) != np.asarray(f4[t].convert("RGB")).astype(int)).any(-1).sum()) for t in range(L))
        print(f"  píxeles distintos (marco y fondo + animación vs final, 126 y x4): {d}; (x4 vs ampliación exacta del 126): {d2}")
        for r in (f"{nombre}_126.gif", f"{nombre}_x4.gif", f"separado/{nombre}_animacion_sola_126.gif", f"separado/{nombre}_animacion_sola_x4.gif"):
            print(f"  {r}: {Image.open(OUT / r).size}, {(OUT / r).stat().st_size / 1024:.0f} KB")
        if nombre == "pesca_marco_ciclo_completo":
            pe.hoja(fin, Path("/projects/sandbox/tmp/baby/hoja_marco.png"))
            sel = [8, 12, 24, 29, 33, 37, 44, 50]
            sh = Image.new("RGB", (4 * 252, 2 * 252))
            for i, t in enumerate(sel):
                sh.paste(fin[t].resize((252, 252), Image.NEAREST), ((i % 4) * 252, (i // 4) * 252))
            sh.save(Path("/projects/sandbox/tmp/baby/muestra_marco.png"))
    mw_img = Image.fromarray(img, "RGBA")
    mw_img.save(HERE / "salida" / "marco_muelle_mar_128.png")


if __name__ == "__main__":
    main()
