"""Animación completa del esqueleto (solo el personaje), transparente y en bucle.

Orden (pasos de 80 ms):
  3.0 reposo (4) -> agachado (1) -> 1.0 (3), 1.1 (2), 1.2 (3) apunta y dispara -> 2.0 (3) zancada -> 2.1 (4) golpe dorado
  -> agachado (1) -> 3.0 (2) -> 3.1, 3.2, 3.3 (2 c/u) -> 3.4 (4) festejo -> 3.3, 3.2, 3.1 (2 c/u) -> vuelve al 3.0 del inicio
El fotograma de paso es el 3.0 aplastado (alto x0,88, ancho x1,06), anclado en la suela. Todo se alinea por la suela y por el
centro de masa del cuerpo (sin contar el arma ni el golpe).
Salida: esqueleto_animacion.gif (x1), _x4 y _x4_fondo (fondo oscuro, para revisar).
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import giros
from giros import F, colocar, agachado

HERE = Path(__file__).parent
TICK = 80
GUION = [("3.0", 4), ("T", 1), ("1.0", 3), ("1.1", 2), ("1.2", 3), ("2.0", 3), ("2.1", 4), ("T", 1), ("3.0", 2),
         ("3.1", 2), ("3.2", 2), ("3.3", 2), ("3.4", 4), ("3.3", 2), ("3.2", 2), ("3.1", 2)]


def pasos():
    T = agachado()
    out = []
    for k, n in GUION:
        out += [T if k == "T" else colocar(F[k])] * n
    return out


def guardar(frames, path, escala=1, fondo=None):
    imgs = [f.resize((f.width * escala, f.height * escala), Image.NEAREST) if escala > 1 else f for f in frames]
    if fondo:
        planos = []
        for im in imgs:
            b = Image.new("RGBA", im.size, fondo + (255,)); b.alpha_composite(im); planos.append(b.convert("RGB"))
        arrs = [np.asarray(p) for p in planos]
        key = lambda a: a[..., 0].astype(np.uint32) << 16 | a[..., 1].astype(np.uint32) << 8 | a[..., 2]
        keys = np.unique(np.concatenate([key(a).ravel() for a in arrs]))
        pal = np.zeros(768, np.uint8)
        pal[0:len(keys) * 3:3], pal[1:len(keys) * 3:3], pal[2:len(keys) * 3:3] = keys >> 16, keys >> 8 & 255, keys & 255
        out = []
        for a in arrs:
            p = Image.fromarray(np.searchsorted(keys, key(a)).astype(np.uint8), "P"); p.putpalette(pal.tolist()); out.append(p)
        out[0].save(path, save_all=True, append_images=out[1:], duration=TICK, loop=0, disposal=1, optimize=False)
        return len(keys)
    colores = sorted({p[:3] for im in imgs for p in im.getdata() if p[3]})
    assert len(colores) <= 255
    index = {c: i + 1 for i, c in enumerate(colores)}
    flat = [255, 0, 255] + [v for c in colores for v in c]
    pal = []
    for im in imgs:
        p = Image.new("P", im.size, 0); p.putpalette(flat + [0] * (768 - len(flat)))
        p.putdata([index[q[:3]] if q[3] else 0 for q in im.getdata()]); pal.append(p)
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=TICK, loop=0, transparency=0, disposal=2, optimize=False)
    return len(colores)


def main():
    fr = pasos()
    print(f"{len(fr)} pasos = {len(fr) * TICK} ms")
    boxes = [f.getchannel("A").getbbox() for f in fr]
    box = (min(b[0] for b in boxes) - 1, min(b[1] for b in boxes) - 1, max(b[2] for b in boxes) + 1, max(b[3] for b in boxes) + 1)
    box = (max(box[0], 0), max(box[1], 0), min(box[2], giros.CW), min(box[3], giros.CH))
    cro = [f.crop(box) for f in fr]
    print("lienzo recortado:", cro[0].size, "origen", box[:2])
    for esc, suf in ((1, ""), (4, "_x4")):
        p = HERE / f"esqueleto_animacion{suf}.gif"
        n = guardar(cro, p, esc)
        print(f"{p.name}: {cro[0].width * esc}x{cro[0].height * esc}, {n} colores, {p.stat().st_size / 1024:.0f} KB")
    p = HERE / "esqueleto_animacion_x4_fondo.gif"
    n = guardar(cro, p, 4, fondo=(44, 52, 80))
    print(f"{p.name}: {n} colores, {p.stat().st_size / 1024:.0f} KB")
    # hoja con un paso por cada fotograma distinto del guion
    idx, t = [], 0
    for k, n_ in GUION:
        idx.append((t, k)); t += n_
    S = 3
    w, h = cro[0].size
    cols = 6
    rows = (len(idx) + cols - 1) // cols
    hoja = Image.new("RGB", (cols * w * S, rows * (h * S + 16)), (20, 14, 24))
    d = ImageDraw.Draw(hoja)
    for i, (t, k) in enumerate(idx):
        x, y = (i % cols) * w * S, (i // cols) * (h * S + 16)
        d.text((x + 4, y + 2), f"paso {t}: {k}", fill=(255, 220, 120))
        b = Image.new("RGBA", cro[t].size, (44, 52, 80, 255)); b.alpha_composite(cro[t])
        hoja.paste(b.convert("RGB").resize((w * S, h * S), Image.NEAREST), (x, y + 16))
    (HERE / "previews").mkdir(exist_ok=True)
    hoja.save(HERE / "previews" / "esqueleto_animacion_pasos.png")
    print("hoja", hoja.size)


if __name__ == "__main__":
    main()
