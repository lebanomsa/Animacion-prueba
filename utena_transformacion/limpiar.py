"""Limpia 'Utena.PNG' (traje negro y pistola): recupera su cuadrícula original y deja una paleta corta y limpia.

La imagen está ampliada ~6,55x con suavizado y ruido de compresión (11.786 colores). Se muestrea la mediana del centro de cada celda
y se agrupan los colores con k-means en el espacio Lab, empezando por los colores limpios del sprite 'utena sprite'
(pelo, piel, dorado), para que no se apaguen, más tonos neutros para el traje.
Salida: sprite_agente_limpio.png (RGBA, fondo transparente) y una comparación en /projects/sandbox/tmp/utena_sprite.
"""
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
ROOT = HERE.parent
BG = np.array((40, 40, 45))


def a_lab(rgb):
    c = np.asarray(rgb, float) / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    m = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ m.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def muestrear(a, p, fx, fy, r=1):
    H, W = a.shape[:2]
    nx, ny = int((W - fx) / p), int((H - fy) / p)
    out = np.zeros((ny, nx, 3), float)
    for j in range(ny):
        cy = int((j + 0.5) * p + fy)
        for i in range(nx):
            cx = int((i + 0.5) * p + fx)
            out[j, i] = np.median(a[max(cy - r, 0):cy + r + 1, max(cx - r, 0):cx + r + 1].reshape(-1, 3), axis=0)
    return out


def recuperar():
    a = np.asarray(Image.open(ROOT / "utena_transformacion" / "fuentes" / "Utena.PNG").convert("RGB")).astype(int)
    isbg = np.abs(a - BG).sum(-1) <= 6
    ys, xs = np.nonzero(~isbg)
    y0b, y1b, x0b, x1b = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    sub = a[y0b:y1b, x0b:x1b]
    dx = (np.abs(np.diff(sub, axis=1)).sum(-1) > 40).sum(0).astype(float)
    dy = (np.abs(np.diff(sub, axis=0)).sum(-1) > 40).sum(1).astype(float)

    def fase(d, p):
        i = np.arange(len(d)); z = (d * np.exp(-2j * np.pi * i / p)).sum()
        return (np.angle(z) / (2 * np.pi)) % 1 * p
    best = None
    for p in np.arange(6.45, 6.70, 0.01):
        fx = (fase(dx, p) + 1 + x0b) % p; fy = (fase(dy, p) + 1 + y0b) % p
        nat = muestrear(a, p, fx, fy)
        q = len(np.unique((nat // 12).reshape(-1, 3), axis=0))
        if best is None or q < best[0]:
            best = (q, p, nat)
    return best[1], best[2]


def referencia():
    """Colores limpios del 'utena sprite' (sin fondo ni suelo ni sombra)."""
    n = np.asarray(Image.open(ROOT / "utena_hechizo" / "sprite_recuperado_52x68.png").convert("RGB")).astype(int)
    cols = np.unique(n.reshape(-1, 3), axis=0)
    quitar = [(97, 158, 155), (59, 95, 94), (29, 51, 50)]
    return np.array([c for c in cols if tuple(c) not in quitar])


def kmeans(lab, init, it=20):
    cen = init.copy()
    for _ in range(it):
        d = ((lab[:, None, :] - cen[None]) ** 2).sum(-1)
        asg = d.argmin(1)
        for k in range(len(cen)):
            m = asg == k
            if m.sum() >= 1:
                cen[k] = lab[m].mean(0)
    d = ((lab[:, None, :] - cen[None]) ** 2).sum(-1)
    return d.argmin(1), cen


PIXELES_NEGROS_EXTRA = [(36, 12), (37, 12)]      # (x, y) del sprite limpio: cierran el contorno del extremo del cañón de la pistola


def cerrar_punta(img, pixeles=PIXELES_NEGROS_EXTRA):
    """El extremo del cañón (una barra diagonal de 2 píxeles de ancho) tenía el contorno abierto: sobre el píxel gris oscuro (36,13) no había
    nada. Se añaden en negro (36,12), justo encima, y la esquina (37,12) para que el borde no quede cortado."""
    a = np.array(img)
    for x, y in pixeles:
        a[y, x] = (1, 2, 1, 255)
    print("píxeles de contorno añadidos en la punta de la pistola:", pixeles)
    return Image.fromarray(a, "RGBA")


def contorno_negro(img, region=None):
    """El contorno del sprite es negro, pero algunos píxeles del borde quedaron en un gris oscuro neutro (el negro mezclado con el gris del
    fondo de la imagen, p. ej. en la punta del cañón de la pistola). Los píxeles del borde con ese gris (luminancia < 36 y sin color) se llevan
    al negro del contorno. Los grises claros (cuerpo y brillos del arma) y los tonos con color (el marrón oscuro del pelo) no se tocan.
    `region` = (x0, y0, x1, y1) para limitarlo a una zona; None = todo el sprite."""
    a = np.array(img)
    op = a[..., 3] > 0
    H, W = op.shape
    negro = a[op][np.argmin(a[op][:, :3].sum(-1))][:3].copy()
    cambios = []
    for y in range(H):
        for x in range(W):
            if not op[y, x]:
                continue
            borde = any(not (0 <= y + dy < H and 0 <= x + dx < W and op[y + dy, x + dx]) for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            c = a[y, x, :3].astype(int)
            lum = 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
            en_region = region is None or (region[0] <= x < region[2] and region[1] <= y < region[3])
            if en_region and borde and lum < 36 and c.max() - c.min() <= 6 and tuple(c) != tuple(negro):
                a[y, x, :3] = negro
                cambios.append((x, y, tuple(int(v) for v in c)))
    print("píxeles de contorno llevados al negro:", cambios)
    return Image.fromarray(a, "RGBA")


def main():
    p, nat = recuperar()
    # fondo = píxeles casi iguales al gris del fondo CONECTADOS con el borde de la imagen. Los grises oscuros del traje, aunque se parezcan
    # al fondo, están encerrados por el contorno y se conservan (si no, el traje se vería agujereado sobre otros fondos).
    cerca = np.abs(nat - BG).sum(-1) <= 14
    inund = np.zeros_like(cerca)
    cola = [(y, x) for y in range(cerca.shape[0]) for x in range(cerca.shape[1])
            if cerca[y, x] and (y in (0, cerca.shape[0] - 1) or x in (0, cerca.shape[1] - 1))]
    for y, x in cola:
        inund[y, x] = True
    while cola:
        y, x = cola.pop()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < cerca.shape[0] and 0 <= nx < cerca.shape[1] and cerca[ny, nx] and not inund[ny, nx]:
                inund[ny, nx] = True; cola.append((ny, nx))
    fgm = ~inund
    from itertools import product
    fg = fgm.copy()
    for y, x in zip(*np.nonzero(fgm)):                       # quitar motas sueltas de 1 px (ruido)
        vec = sum(fgm[y + dy, x + dx] for dy, dx in product((-1, 0, 1), repeat=2)
                  if (dy or dx) and 0 <= y + dy < fgm.shape[0] and 0 <= x + dx < fgm.shape[1])
        if vec == 0:
            fg[y, x] = False
    pix = nat[fg]
    lab = a_lab(pix)
    ref = referencia()
    # semillas: colores de referencia + neutros del traje (picos de gris oscuro y medio presentes en la imagen)
    grises = np.array([(0, 0, 0), (22, 22, 24), (36, 36, 40), (58, 58, 62), (90, 90, 96), (150, 150, 156)])
    init = a_lab(np.vstack([ref, grises]))
    asg, cen = kmeans(lab, init.copy())
    # descartar clusters casi vacíos y reasignar
    cuenta = np.bincount(asg, minlength=len(cen))
    vivos = np.nonzero(cuenta >= 4)[0]
    d = ((lab[:, None, :] - cen[vivos][None]) ** 2).sum(-1)
    asg2 = d.argmin(1)
    # color final de cada cluster: el color RGB real más cercano a su centro (sin inventar tonos)
    paleta = []
    for k in range(len(vivos)):
        m = asg2 == k
        medio = np.median(pix[m], axis=0)
        paleta.append(medio.round().astype(int))
    paleta = np.array(paleta)
    out = np.zeros(nat.shape[:2] + (4,), np.uint8)
    out[fg, :3] = paleta[asg2]
    out[fg, 3] = 255
    ys, xs = np.nonzero(fg)
    box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
    img = Image.fromarray(out, "RGBA").crop(box)
    img = contorno_negro(img)
    img = cerrar_punta(img)
    img.save(HERE / "sprite_agente_limpio.png")
    cols = len({tuple(p_[:3]) for p_ in img.getdata() if p_[3]})
    print(f"período {p:.2f}; cuadrícula {nat.shape[1]}x{nat.shape[0]}; personaje {img.size[0]}x{img.size[1]}; {cols} colores")
    # comparación: original recortado | recuperado sin limpiar | limpio
    tmp = Path("/projects/sandbox/tmp/utena_sprite"); tmp.mkdir(parents=True, exist_ok=True)
    orig = Image.open(ROOT / "utena_transformacion" / "fuentes" / "Utena.PNG").convert("RGB")
    Z = 8
    sin = Image.fromarray(nat.astype(np.uint8)).crop(box)
    lim = Image.new("RGB", img.size, tuple(BG)); lim.paste(img, (0, 0), img)
    W = img.size[0] * Z
    sheet = Image.new("RGB", (W * 2 + 10, img.size[1] * Z), (20, 20, 20))
    sheet.paste(sin.resize((W, img.size[1] * Z), Image.NEAREST), (0, 0))
    sheet.paste(lim.resize((W, img.size[1] * Z), Image.NEAREST), (W + 10, 0))
    sheet.save(tmp / "limpieza_comparada.png")
    print("paleta:", [tuple(int(v) for v in c) for c in paleta])


if __name__ == "__main__":
    main()
