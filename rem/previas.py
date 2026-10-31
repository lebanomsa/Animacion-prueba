"""Vistas previas de cuatro bucles de Rem (sin marco todavía) con los sprites y efectos de rem.png.

  1 idle + círculo mágico     4 fotogramas de pie (grandes, x4) + círculo azul que late, anillos que se expanden y chispas que suben
  2 carga de hechizo          poses de lanzar magia (x8) + orbe rosa que crece, rayos y anillos que estallan
  3 modo oni con llamas       poses con cuerno (x8) + las 10 columnas de llama roja como bucle de fuego + rayos rosas
  4 ataque con onda azul      poses de golpe (x8) + remolino azul y ráfaga que aparece en el golpe
Todas de 24 pasos de 80 ms sobre un fondo azul noche provisional (640 px = la ventana del marco).
"""
import pickle
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).parent
ROOT = HERE.parent
TMP = Path("/projects/sandbox/tmp/rem")
PREV = HERE / "previews"
SHEET = Image.open(TMP / "rem.png").convert("RGBA")
LAB, INFO = pickle.load(open(TMP / "lab.pkl", "rb"))
POR = {r[0]: r for r in INFO}
N = 24
W = 640


def fondo():
    y, x = np.mgrid[0:W, 0:W]
    base = np.zeros((W, W, 3), float)
    t = y / W
    base[..., 0] = 8 + 12 * t; base[..., 1] = 12 + 14 * t; base[..., 2] = 30 + 26 * t
    r = np.hypot(x - 320, y - 330) / 330
    glow = np.clip(1 - r, 0, 1) ** 2
    base += glow[..., None] * np.array([6, 16, 40])
    return base


def sprite(n, m=2):
    """Recorte del componente n (solo sus píxeles y un borde de 3 px) como RGBA."""
    _, x0, y0, w, h = POR[n][:5]
    c = SHEET.crop((x0 - m, y0 - m, x0 + w + m, y0 + h + m))
    mask = (LAB[y0 - m:y0 + h + m, x0 - m:x0 + w + m] == n)
    for _ in range(3):
        d = mask.copy(); d[1:] |= mask[:-1]; d[:-1] |= mask[1:]; d[:, 1:] |= mask[:, :-1]; d[:, :-1] |= mask[:, 1:]; mask = d
    a = np.array(c)
    a[~mask] = 0
    return Image.fromarray(a, "RGBA")


def efecto(n, m=6):
    _, x0, y0, w, h = POR[n][:5]
    return SHEET.crop((x0 - m, y0 - m, x0 + w + m, y0 + h + m))


def idle_frames():
    sub = SHEET.crop((1428, 50, 1500, 560))
    a = np.asarray(sub)[..., 3]
    filas = (a > 60).sum(1)
    ys = np.where(filas > 0)[0]
    top, bot = ys.min(), ys.max()
    paso = (bot - top + 1) / 4
    # cortar por los mínimos de la proyección cerca de los múltiplos del paso
    cortes = [top]
    for k in range(1, 4):
        c = int(top + k * paso)
        rango = range(c - 8, c + 9)
        cortes.append(min(rango, key=lambda y: filas[y]))
    cortes.append(bot + 1)
    return [sub.crop((0, cortes[i], 72, cortes[i + 1])) for i in range(4)]


def a_np(img):
    return np.asarray(img).astype(float)


def pegar(canvas, img, cx, cy, k=1.0, aditivo=False, anclaje="c"):
    """Pega `img` (PIL RGBA) centrada en (cx, cy) (o con la base en cy si anclaje='b')."""
    a = a_np(img)
    h, w = a.shape[:2]
    x0 = int(round(cx - w / 2)); y0 = int(round(cy - h / 2 if anclaje == "c" else cy - h))
    sx, sy = max(-x0, 0), max(-y0, 0)
    ex, ey = min(w, W - x0), min(h, W - y0)
    if ex <= sx or ey <= sy:
        return
    sub = a[sy:ey, sx:ex]
    al = sub[..., 3:4] / 255 * k
    reg = canvas[y0 + sy:y0 + ey, x0 + sx:x0 + ex]
    if aditivo:
        reg += sub[..., :3] * al
    else:
        reg[:] = reg * (1 - al) + sub[..., :3] * al


def esc(img, s, nearest=False):
    return img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))), Image.NEAREST if nearest else Image.LANCZOS)


def blob(r, col, dura=0.5):
    y, x = np.mgrid[-r:r + 1, -r:r + 1]
    d = np.hypot(x, y) / r
    al = np.clip(1 - d, 0, 1) ** (1 + dura)
    a = np.zeros((2 * r + 1, 2 * r + 1, 4), np.uint8)
    a[..., :3] = col; a[..., 3] = (al * 255).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def salir(canvas):
    return Image.fromarray(np.clip(canvas, 0, 255).round().astype(np.uint8), "RGB")


# ---- opción 1 -------------------------------------------------------------------------------------------------------
def op1(fondo_fn=None):
    idle = idle_frames()
    print("idle:", [f.size for f in idle])
    S = 4
    anillo_fijo = efecto(447, 8)
    onda = efecto(184, 8)
    rng = np.random.default_rng(4)
    chispas = [(rng.uniform(-190, 190), rng.uniform(0, 1), int(rng.integers(1, 3)), rng.integers(3, 7)) for _ in range(22)]
    out = []
    for t in range(N):
        cv = fondo_fn(t) if fondo_fn else fondo()
        suelo = 585
        # círculo mágico: late entre 0,92 y 1,06 (ciclo de 12) con brillo variable
        fase = (t % 12) / 12
        pulso = 0.5 + 0.5 * np.sin(2 * np.pi * fase)
        pegar(cv, esc(anillo_fijo, 2.5 + 0.12 * pulso), 320, suelo - 28, k=0.65 + 0.35 * pulso, aditivo=True)
        # ondas que salen del círculo y se desvanecen
        for k in range(2):
            u = ((t / 24) * 2 + k * 0.5) % 1.0
            pegar(cv, esc(onda, 1.8 + 2.0 * u), 320, suelo - 28, k=(1 - u) ** 1.3 * 0.9, aditivo=True)
        # Rem de pie (4 fotogramas, 3 pasos cada uno), x4, con los pies sobre el círculo
        f = esc(idle[(t // 3) % 4], S, nearest=True)
        pegar(cv, f, 320, suelo, anclaje="b")
        # chispas que suben
        for (dx, ph, v, r) in chispas:
            u = (ph + (t / 24) * v) % 1.0
            x = 320 + dx * (0.7 + 0.3 * u) + 10 * np.sin(2 * np.pi * (u * 2 + ph))
            y = suelo - 20 - u * 420
            pegar(cv, blob(int(r), (150, 235, 255)), x, y, k=min(1, (1 - u) * 1.6), aditivo=True)
        out.append(salir(cv))
    return out


# ---- opciones con sprites pequeños (x8) ---------------------------------------------------------------------------------
SP = 8


def rem(cv, n, cx, suelo, k=1.0):
    s = esc(sprite(n), SP, nearest=True)
    pegar(cv, s, cx, suelo, k=k, anclaje="b")
    return s


def orbe_frames():
    return [esc(efecto(n, 4), 1.0) for n in (13, 83, 283, 325)]


def rayo(cv, t, cx, cy, escala, k):
    r = [efecto(363, 4), efecto(412, 4), efecto(421, 4)]
    for j in range(3):
        img = r[(t + j) % 3].rotate(((t * 53 + j * 120) % 360), expand=True, resample=Image.BICUBIC)
        a = 0.5 * np.pi * 2 * ((t + j * 4) % 12) / 12
        pegar(cv, esc(img, escala), cx + 150 * escala * np.cos(a), cy + 120 * escala * np.sin(a), k=k * 0.9, aditivo=True)


def op2():
    poses = [29, 63, 246, 295, 345, 295, 246, 63, 29, 209, 250, 209]
    orbes = orbe_frames()
    ring = efecto(216, 4)
    out = []
    for t in range(N):
        cv = fondo()
        n = poses[(t // 2) % len(poses)]
        rem(cv, n, 300, 600)
        u = (t % 12) / 11                       # carga: el orbe crece durante 12 pasos y estalla
        ox, oy = 440, 330
        pegar(cv, esc(orbes[t % 4], 0.35 + 1.45 * u), ox, oy, k=0.55 + 0.45 * u, aditivo=True)
        if u > 0.4:
            rayo(cv, t, ox, oy, 0.5 + 0.9 * u, (u - 0.4) / 0.6)
        v = ((t % 12) / 12)
        for k in range(2):
            uu = (v + k * 0.5) % 1
            pegar(cv, esc(ring, 2 + 8 * uu), ox, oy, k=(1 - uu) * 0.85, aditivo=True)
        out.append(salir(cv))
    return out


def llamas_frames():
    pan = [(10, 380), (10, 540), (170, 540), (10, 700), (170, 700), (330, 700), (10, 870), (170, 870), (330, 870), (490, 870)]
    fr = []
    for (x, y) in pan:
        c = SHEET.crop((x, y, x + 150, y + 150))
        a = np.array(c).astype(float)
        al = a[..., 3:4] / 255
        a[..., 3:4] = np.clip(al ** 0.7 * 255 * 1.4, 0, 255)       # llamas más densas
        fr.append(Image.fromarray(a.astype(np.uint8), "RGBA"))
    return fr


def op3():
    horn = [43, 37, 36, 61, 62, 36, 37, 43, 209, 220]       # 10 poses x 3 pasos = 30 pasos = 3 vueltas de las 10 columnas de llama
    fl = llamas_frames()
    out = []
    for t in range(30):
        cv = fondo()
        pegar(cv, esc(fl[t % 10], 4.4), 320, 640, k=1.0, aditivo=True, anclaje="b")
        pegar(cv, esc(fl[(t + 5) % 10], 3.4), 320, 640, k=0.7, aditivo=True, anclaje="b")
        n = horn[(t // 3) % len(horn)]
        rem(cv, n, 320, 600)
        if t % 6 in (1, 2):
            rayo(cv, t, 320, 330, 1.0, 0.8)
        out.append(salir(cv))
    return out


def op4():
    poses = [29, 123, 122, 122, 295, 123, 29, 29]
    vort = [11, 10, 8, 183, 190, 105, 224, 228]
    rafaga = [59, 187, 79, 96, 182, 9]
    out = []
    for t in range(N):
        cv = fondo()
        c = t % 12
        n = poses[(c // 2) % 6] if c < 12 else 29
        golpe = c in (4, 5, 6, 7, 8)
        # remolino azul que gira en la mano durante la preparación
        if c < 5:
            pegar(cv, esc(efecto(vort[t % 8], 4), 1.2 + 0.6 * (c / 4)), 150, 380, k=0.8, aditivo=True)
        rem(cv, n, 330, 600)
        if golpe:
            u = (c - 4) / 4
            pegar(cv, esc(efecto(rafaga[min(5, c - 4)], 6), 2.2 + 1.5 * u), 160, 340, k=1 - 0.5 * u, aditivo=True)
            pegar(cv, esc(efecto(253, 4), 1.0 + 1.8 * u), 160, 340, k=0.7 * (1 - u), aditivo=True)
        out.append(salir(cv))
    return out


def gif(frs, ruta):
    arrs = [np.asarray(f) for f in frs]
    mosaico = Image.fromarray(np.concatenate([a[::3, ::3] for a in arrs[::2]], axis=0))
    q = mosaico.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    out = [f.quantize(palette=q, dither=Image.Dither.NONE) for f in frs]
    out[0].save(ruta, save_all=True, append_images=out[1:], duration=80, loop=0, disposal=1, optimize=False)


def main():
    PREV.mkdir(exist_ok=True)
    hoja = Image.new("RGB", (4 * 320, 3 * 320), (14, 10, 20))
    for i, (nombre, fn) in enumerate((("1_idle_circulo_magico", op1), ("2_carga_de_hechizo", op2), ("3_modo_oni_llamas", op3), ("4_ataque_onda_azul", op4))):
        fr = fn()
        ruta = PREV / f"rem_{nombre}.gif"
        gif(fr, ruta)
        print(f"{ruta.name}: {len(fr)} pasos, {ruta.stat().st_size / 1024:.0f} KB")
        for j, t in enumerate((2, 8, 14)):
            hoja.paste(fr[t].resize((320, 320), Image.LANCZOS), (i * 320, j * 320))
    hoja.save(PREV / "rem_opciones.png")


if __name__ == "__main__":
    main()
