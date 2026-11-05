"""Entrega final de Utena (1x), por partes:

  marco_y_fondo_*.gif        marco animado (barrido tipo luna y detalles) + cielo de la referencia + nebulosa violeta + cometa, 40 pasos
  animacion_sola_*.gif       Utena, sus efectos y el círculo mágico del suelo sobre fondo transparente, en su sitio (40 pasos)
  animacion_recortada_*.gif  lo mismo recortado a su caja
Comprueba que (marco y fondo) + animación == GIF final, en 126 y x4.
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "utena_marco")); sys.path.insert(0, str(HERE))
import marco_animado as ma
import referencia as rf
import nebulosa_foto as nf
import fondo_final as ff
tr, pe = ma.tr, ma.pe
OUT = HERE / "entrega"
K_MARCO, L, TICK = 98, 40, 100


def main():
    OUT.mkdir(exist_ok=True)
    ref = rf.cargar()
    neb = nf.capa(nf.CAJAS[ff.CAJA_NEBULOSA], ff.INTENSIDAD)
    bgf = ff.bgf_final(ref, neb)
    caps = tr.cargar_capas_1x(bgf)
    marcos, ws, win = ma.construir_marco("vertical", K_MARCO)

    fondos, animaciones, finales = [], [], []
    for t in range(L):
        bg = bgf(t)[0]
        under, over = caps[t].under, caps[t].over
        base = bg if (under[0, 0] == bg[0, 0]).all() else np.clip(bg.astype(int) + 38, 0, 255).astype(np.uint8)     # el destello aclara el fondo
        circulo = (under != base).any(-1)                                                                        # lo que se dibujó encima: el círculo mágico
        assert circulo.sum() < 900, circulo.sum()
        fondo = Image.fromarray(base, "RGB").convert("RGBA")
        fondo.alpha_composite(marcos[t].crop((1, 1, 127, 127)))
        capa = over.copy()
        libre = (capa[..., 3] == 0) & circulo
        capa[libre, :3] = under[libre]; capa[libre, 3] = 255
        anim = Image.fromarray(capa, "RGBA")
        fondos.append(fondo.convert("RGB")); animaciones.append(anim)
        f = fondo.copy(); f.alpha_composite(anim)
        finales.append(f.convert("RGB"))
        ref_f = ma.escena(caps, marcos, t, esc=1)
        assert (np.asarray(f.convert("RGB")) == np.asarray(ref_f)).all(), f"paso {t}: la separación cambia la imagen"
    print("separación por capas: idéntica al resultado original en los 40 pasos")

    up = lambda im: im.resize((504, 504), Image.NEAREST)
    n1 = pe.gif_opaco(fondos, OUT / "marco_y_fondo_126.gif", TICK)
    pe.gif_opaco([up(f) for f in fondos], OUT / "marco_y_fondo_x4.gif", TICK)
    n2 = pe.gif_transparente(animaciones, OUT / "animacion_sola_126.gif", TICK)
    pe.gif_transparente([up(a) for a in animaciones], OUT / "animacion_sola_x4.gif", TICK)
    pe.gif_opaco(finales, OUT / "utena_final_126.gif", TICK)
    pe.gif_opaco([up(f) for f in finales], OUT / "utena_final_x4.gif", TICK)
    bb = [a.getchannel("A").getbbox() for a in animaciones if a.getchannel("A").getbbox()]
    caja = (min(b[0] for b in bb), min(b[1] for b in bb), max(b[2] for b in bb), max(b[3] for b in bb))
    pe.gif_transparente([a.crop(caja) for a in animaciones], OUT / "animacion_recortada_126.gif", TICK)
    pe.gif_transparente([up(a).crop(tuple(v * 4 for v in caja)) for a in animaciones], OUT / "animacion_recortada_x4.gif", TICK)
    print(f"colores: marco y fondo {n1}, animación sola {n2}; caja de la animación (x0,y0,x1,y1) en 126: {caja} = {caja[2] - caja[0]}x{caja[3] - caja[1]}")
    for r in sorted(p.name for p in OUT.glob("*.gif")):
        print(f"  {r}: {Image.open(OUT / r).size}, {(OUT / r).stat().st_size / 1024:.0f} KB")

    # comprobación leyendo los GIF guardados
    d = 0
    for suf, fx in (("126", lambda im: im), ("x4", up)):
        fin = pe.por_paso(OUT / f"utena_final_{suf}.gif", L, TICK)
        fon = pe.por_paso(OUT / f"marco_y_fondo_{suf}.gif", L, TICK)
        ani = pe.por_paso(OUT / f"animacion_sola_{suf}.gif", L, TICK)
        for t in range(L):
            c = fon[t].copy(); c.alpha_composite(ani[t])
            d += int((np.abs(np.asarray(c.convert("RGB")).astype(int) - np.asarray(fin[t].convert("RGB")).astype(int)).sum(-1) > 0).sum())
    print("píxeles distintos entre (marco y fondo + animación) y el GIF final, en 126 y x4 (40 pasos cada uno):", d)
    ant = pe.por_paso(HERE / "salida" / "utena_nebulosa_cometa_126.gif", L, TICK)
    nuevo = pe.por_paso(OUT / "utena_final_126.gif", L, TICK)
    print("píxeles distintos entre el GIF final de ahora y el que ya vio (126):", sum(int((np.asarray(a.convert('RGB')) != np.asarray(b.convert('RGB'))).any(-1).sum()) for a, b in zip(ant, nuevo)))
    # imagen de muestra: marco y fondo | animación sobre ajedrez | juntos, en tres momentos
    from PIL import ImageDraw
    Z = 2; mom = (2, 14, 27)
    sh = Image.new("RGB", (3 * 126 * Z, len(mom) * 126 * Z))
    for j, t in enumerate(mom):
        aj = Image.new("RGBA", (126, 126))
        for yy in range(0, 126, 6):
            for xx in range(0, 126, 6):
                aj.paste(((120, 120, 120, 255) if (xx // 6 + yy // 6) % 2 else (90, 90, 90, 255)), (xx, yy, xx + 6, yy + 6))
        aj.alpha_composite(animaciones[t])
        for i, im in enumerate((fondos[t], aj.convert("RGB"), finales[t])):
            sh.paste(im.resize((126 * Z, 126 * Z), Image.NEAREST), (i * 126 * Z, j * 126 * Z))
    d_ = ImageDraw.Draw(sh)
    for i, tx in enumerate(("marco y fondo", "animación sola", "juntos")):
        d_.text((i * 126 * Z + 6, 6), tx, fill=(255, 255, 255))
    sh.save(OUT / "muestra_por_partes.png")


if __name__ == "__main__":
    main()
