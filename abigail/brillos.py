"""Destello con contorno y brillos en cruz para el parpadeo final de Abigail.

flash(img, 4): 'blanco por tonos' con contorno doble. La luminosidad del dibujo original decide el tono
(blanco en las luces, amarillo en las medias, ámbar y marrón en las sombras) y la silueta lleva un
contorno doble (amarillo por dentro, ámbar por fuera). Conserva el volumen del dibujo.
star / draw_star / sparkle_points: brillos de cuatro puntas, de dos tamaños, repartidos alrededor de la silueta.
Solo colores sólidos (nada de semitransparencias), aptos para GIF.
"""
import random

import numpy as np
from PIL import Image

WHITE, YEL, AMB, AMB2, BROWN = (248, 248, 248), (248, 232, 112), (224, 136, 48), (240, 176, 64), (96, 32, 0)
SP = 2                      # escala de los brillos (igual que la caída y la explosión)
SMALL = [0, 1, 2, 1, 0]     # fases del brillo pequeño (5)
LARGE = [1, 2, 3, 2, 1]     # fases del brillo grande (5, desde la cruz)


def dilate(mask, n=1):
    m = mask.copy()
    for _ in range(n):
        p = np.pad(m, 1)
        m = m | p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
    return m


def flash(img, variant=4):
    """Silueta con destello y contorno. 1: blanca + contorno ámbar. 2: blanca + contorno doble.
    3: como la 2 conservando el trazo oscuro. 4: blanco por tonos + contorno doble (la elegida)."""
    a = np.asarray(img).copy()
    alpha = a[..., 3] > 0
    out = np.zeros_like(a)
    out[alpha] = WHITE + (255,)
    if variant == 4:
        lum = a[..., :3].astype(int) @ np.array([0.299, 0.587, 0.114])
        out[alpha & (lum < 150)] = YEL + (255,)
        out[alpha & (lum < 85)] = AMB + (255,)
        out[alpha & (lum < 28)] = BROWN + (255,)
    if variant == 3:
        out[alpha & (a[..., :3].sum(axis=2) < 70)] = BROWN + (255,)
    d1, d2 = dilate(alpha, 1), dilate(alpha, 2)
    if variant == 1:
        out[d1 & ~alpha] = AMB2 + (255,)
    else:
        out[d1 & ~alpha] = YEL + (255,)
        out[d2 & ~d1] = AMB + (255,)
    return Image.fromarray(out, "RGBA")


def star(phase):
    """Píxeles (dx, dy, color) de un brillo en cruz. Fases 0..3: punto, cruz, estrella, estrella grande."""
    px = [(0, 0, WHITE)]
    if phase >= 1:
        px += [(1, 0, YEL), (-1, 0, YEL), (0, 1, YEL), (0, -1, YEL)]
    if phase >= 2:
        px += [(2, 0, AMB), (-2, 0, AMB), (0, 2, AMB), (0, -2, AMB)]
    if phase >= 3:
        px = [(0, 0, WHITE), (1, 0, WHITE), (-1, 0, WHITE), (0, 1, WHITE), (0, -1, WHITE),
              (2, 0, YEL), (-2, 0, YEL), (0, 2, YEL), (0, -2, YEL),
              (3, 0, AMB), (-3, 0, AMB), (0, 3, AMB), (0, -3, AMB)]
    return px


def draw_star(img, x, y, phase, sp=None):
    sp = sp or SP
    for dx, dy, col in star(phase):
        for ix in range(sp):
            for iy in range(sp):
                px, py = x + dx * sp + ix, y + dy * sp + iy
                if 0 <= px < img.width and 0 <= py < img.height:
                    img.putpixel((px, py), col + (255,))


def sparkle_points(mask, n=9, seed=7, min_d=18):
    """Puntos de brillo alrededor de la silueta (sobre su contorno y 4 px hacia fuera).
    Devuelve [(x, y, fases, paso_de_inicio)]: 3 grandes y 6 pequeños, desfasados en el tiempo."""
    ys, xs = np.nonzero(mask)
    cx, cy = xs.mean(), ys.mean()
    edge = mask & (~np.roll(mask, 1, 0) | ~np.roll(mask, -1, 0) | ~np.roll(mask, 1, 1) | ~np.roll(mask, -1, 1))
    ey, ex = np.nonzero(edge)
    rnd = random.Random(seed)
    idx = list(range(len(ex))); rnd.shuffle(idx)
    pts = []
    for i in idx:
        x, y = int(ex[i]), int(ey[i])
        v = np.array([x - cx, y - cy], float); nrm = np.linalg.norm(v) or 1.0
        x += int(round(4 * v[0] / nrm)); y += int(round(4 * v[1] / nrm))
        if all((x - px) ** 2 + (y - py) ** 2 >= min_d ** 2 for px, py, *_ in pts):
            pts.append((x, y))
        if len(pts) == n:
            break
    out, li, si = [], 0, 0
    starts_large, starts_small = [1, 2, 3], [1, 2, 2, 3, 3, 1]
    for k, (x, y) in enumerate(pts):
        if k % 3 == 0 and li < 3:
            out.append((x, y, LARGE, starts_large[li])); li += 1
        else:
            out.append((x, y, SMALL, starts_small[si % 6])); si += 1
    return out


def sparkles_at(img, pts, t):
    """Dibuja sobre img los brillos que están encendidos en el paso t del parpadeo (a partir del paso 1)."""
    for x, y, phases, start in pts:
        i = t - start
        if t >= 1 and 0 <= i < len(phases):
            draw_star(img, x, y, phases[i])
