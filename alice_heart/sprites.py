"""Extrae los sprites de las hojas 'alice and heart' a su resolución original (las hojas están ampliadas 3x, con fondo gris).

Cada pose viene en pares: versión en color (índice par) y su holograma verde azulado (índice impar), en el mismo sitio.
Nombres: H1 / H2 = hoja 1 / 2, T / B = fila de arriba (Alice, coletas) / de abajo (Heart, pelo corto), y el número de sprite.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).parent
SRC = HERE / "fuentes"
MAG = (255, 0, 255)
HOJAS = {"H1": "alice_and_heart_1.PNG", "H2": "alice_and_heart_2.PNG"}


def _runs(mask, gap):
    xs = np.nonzero(mask)[0]
    out, st, pv = [], xs[0], xs[0]
    for x in xs[1:]:
        if x - pv > gap:
            out.append((st, pv)); st = x
        pv = x
    out.append((st, pv))
    return out


def _fondo(im):
    """Máscara de primer plano: quita el blanco exterior y el gris de la mancha."""
    m = im.copy()
    ImageDraw.floodfill(m, (0, 0), MAG, thresh=0)
    a = np.asarray(im)
    ys, xs = np.nonzero((a == (224, 224, 224)).all(-1))
    for y, x in list(zip(ys, xs))[::997]:
        if tuple(np.asarray(m)[y, x]) == (224, 224, 224):
            ImageDraw.floodfill(m, (int(x), int(y)), MAG, thresh=0)
    return ~(np.asarray(m) == MAG).all(-1)


def _bajar(crop_rgba):
    """Reduce 3x buscando la fase (0..2) en x e y donde los bloques de 3x3 son más uniformes."""
    a = np.asarray(crop_rgba).astype(int)
    best = None
    for fy in range(3):
        for fx in range(3):
            sub = a[fy:, fx:]
            H, W = sub.shape[0] // 3 * 3, sub.shape[1] // 3 * 3
            h = sub[:H, :W].reshape(H // 3, 3, W // 3, 3, 4)
            u = float((h == h[:, :1, :, :1, :]).all(axis=(1, 3, 4)).mean())
            if best is None or u > best[0]:
                best = (u, fy, fx, h[:, 1, :, 1, :])
    return best[0], Image.fromarray(best[3].astype(np.uint8), "RGBA")


def _quitar_bolsas(nat, minimo=15):
    """Quita los huecos del fondo gris (224,224,224) que quedaron encerrados dentro del sprite (p. ej. entre el pelo y el cuerpo).
    Los grises sueltos de 1 a 7 píxeles son detalles del dibujo y se conservan."""
    a = np.array(nat)
    m = (a[..., :3] == (224, 224, 224)).all(-1) & (a[..., 3] > 0)
    seen = np.zeros_like(m)
    for y, x in zip(*np.nonzero(m)):
        if seen[y, x]:
            continue
        st, pts = [(y, x)], []
        seen[y, x] = True
        while st:
            cy, cx = st.pop(); pts.append((cy, cx))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = cy + dy, cx + dx
                if 0 <= ny < m.shape[0] and 0 <= nx < m.shape[1] and m[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True; st.append((ny, nx))
        if len(pts) >= minimo:
            for cy, cx in pts:
                a[cy, cx, 3] = 0
    return Image.fromarray(a, "RGBA")


def cargar():
    """Devuelve {nombre: Image RGBA nativa} y la uniformidad mínima de bloques (para comprobar la escala 3x)."""
    out, umin = {}, 1.0
    for hoja, fn in HOJAS.items():
        im = Image.open(SRC / fn).convert("RGB")
        fg = _fondo(im)
        rgba = np.dstack([np.asarray(im), (fg * 255).astype(np.uint8)])
        rows = _runs(fg.any(1), 6)
        rows = [r for r in rows if r[1] - r[0] > 20]
        for fila, (y0, y1) in zip("TB", rows):
            sub = fg[y0:y1 + 1]
            n = 0
            for x0, x1 in _runs(sub.any(0), 3):
                if x1 - x0 < 12:
                    continue
                r = np.nonzero(sub[:, x0:x1 + 1].any(1))[0]
                ya, yb = y0 + r.min(), y0 + r.max() + 1
                crop = Image.fromarray(rgba[ya:yb, x0:x1 + 1], "RGBA")
                u, nat = _bajar(crop)
                umin = min(umin, u)
                nat = _quitar_bolsas(nat)
                # recortar a la caja de contenido
                bb = nat.getchannel("A").getbbox()
                out[f"{hoja}{fila}{n}"] = nat.crop(bb)
                n += 1
    return out, umin


if __name__ == "__main__":
    spr, umin = cargar()
    print("sprites:", len(spr), "uniformidad mínima de bloques 3x3:", round(umin, 3))
    for k, v in spr.items():
        cols = len({tuple(p[:3]) for p in v.getdata() if p[3]})
        print(f"{k}: {v.size[0]}x{v.size[1]}, {cols} colores")
    # hoja de contacto numerada, ampliada 4x sobre fondo liso
    from PIL import ImageFont
    f = ImageFont.load_default()
    tmp = Path("/projects/sandbox/tmp/alice_heart"); tmp.mkdir(parents=True, exist_ok=True)
    for hoja in HOJAS:
        for fila in "TB":
            ks = [k for k in spr if k.startswith(hoja + fila)]
            Z = 4
            W = sum(spr[k].width * Z + 16 for k in ks); H = max(spr[k].height for k in ks) * Z + 24
            sh = Image.new("RGB", (W, H), (70, 70, 90)); d = ImageDraw.Draw(sh); x = 8
            for k in ks:
                s = spr[k]; sh.paste(s.resize((s.width * Z, s.height * Z), Image.NEAREST), (x, 20), s.resize((s.width * Z, s.height * Z), Image.NEAREST))
                d.text((x, 4), k, fill=(255, 255, 255), font=f); x += s.width * Z + 16
            sh.save(tmp / f"contacto_{hoja}{fila}.png")
