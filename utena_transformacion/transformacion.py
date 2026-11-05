"""Utena: de agente (traje negro y pistola) a chica mágica (traje morado y varita de estrella) y de vuelta. Bucle de 40 pasos (4 s).

Usa el sprite del traje negro ya limpio (sprite_agente_limpio.png, 38x51) y el sprite de la varita recuperado en utena_hechizo.
Se alinean por la cabeza (cuernos, antena y puño izquierdo coinciden); la pistola queda donde está la estrella de la varita.
Lienzo nativo de 63x63 ampliado 2x (126x126) y x4 (504x504), sobre el escenario del propio sprite de la varita.

  0-5    agente respira (torso +1 px, antena)
  6-11   carga: la pistola brilla, partículas se juntan en ella, destellos alrededor
  12-13  destello y silueta blanca
  14-17  la silueta se transforma y se disuelve en la chica mágica
  18-29  chica mágica: círculo, levitación, partículas y rayos (el hechizo)
  30-31  estallido y destello
  32-35  silueta blanca y disolución de vuelta al agente
  36-39  agente respira (enlaza con el paso 0)
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "utena_hechizo"))
import hechizo as hz   # noqa: E402

OUT = HERE / "salida"
NC, L, TICK = hz.NC, 40, 100
WHITE, GOLD, CREAM, LAV = hz.WHITE, hz.GOLD, hz.CREAM, hz.LAV
NZ = np.random.RandomState(5).rand(NC, NC)
VIEJO_ORIGEN = (12, 4)          # esquina del sprite del agente en el lienzo (alineado por la cabeza con el sprite de la varita)
GUN_C = (45, 18)                # centro de la pistola en el lienzo
BODY_C = (32, 29)               # centro del cuerpo


def cargar_viejo():
    return np.array(Image.open(HERE / "sprite_agente_limpio.png").convert("RGBA"))


def capa_viejo(old, resp, ant, brillo):
    """Capa RGBA 63x63 del agente: respira, mece el rulo y, si hay brillo, la pistola se vuelve dorada o blanca."""
    out = old.copy()
    if resp:
        for y in range(2, 31):
            out[y] = old[y + resp]
    o2 = out.copy()
    if ant:
        for y in range(0, 5 - resp):
            o2[y] = np.roll(out[y], ant, axis=0)
    if brillo:
        sub = o2[8:23, 27:]
        a = sub[..., 3] > 0
        rgb = sub[..., :3].astype(int)
        gris = (rgb.max(-1) - rgb.min(-1) < 30) & (rgb.mean(-1) > 45) & a        # carne de la pistola, sin el contorno negro
        col = WHITE if brillo == 2 else GOLD
        sub[..., :3][gris] = col
        o2[8:23, 27:] = sub
    lay = np.zeros((NC, NC, 4), np.uint8)
    ox, oy = VIEJO_ORIGEN
    lay[oy:oy + o2.shape[0], ox:ox + o2.shape[1]] = o2
    return lay


def silueta(lay, col=WHITE):
    s = lay.copy()
    s[lay[..., 3] > 0, :3] = col
    return s


def mezclar(a, b, p):
    m = (NZ < p)[..., None]
    return np.where(m, b, a)


class Cap:
    """Un paso de la animación en dos capas: `under` (escenario y círculo del suelo, RGB) y `over` (personaje y efectos, RGBA)."""
    def __init__(self, under, over):
        self.under, self.over = under, over

    def compuesto(self):
        out = self.under.copy()
        m = self.over[..., 3] > 0
        out[m] = self.over[m][:, :3]
        return out


def componer(bg, lay, delta=0):
    base = np.clip(bg.astype(int) + delta, 0, 255).astype(np.uint8) if delta else bg.copy()
    return Cap(base, lay.copy())


def anillo(img, rx, ry, col=WHITE, cx=BODY_C[0], cy=BODY_C[1]):
    hz.elipse(img, cx, cy, rx, ry, col, paso=1)


def rayos_en(img, cx, cy, r, col, largo=3):
    for k, (dx, dy) in enumerate(((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1))):
        n = 1.0 if dx == 0 or dy == 0 else 0.72
        for q in range(largo):
            hz.px(img, cx + dx * (r + q) * n, cy + dy * (r + q) * n, col)


def convergen(img, t, t0, t1, destino, semilla):
    """Partículas que se juntan en `destino` entre los pasos t0 y t1."""
    rs = np.random.RandomState(semilla)
    for i in range(10):
        ang = rs.rand() * 2 * np.pi
        r0 = 14 + 6 * rs.rand()
        r = r0 * (1 - (t - t0) / float(t1 - t0 + 1))
        if r < 2:
            continue
        hz.px(img, destino[0] + r * np.cos(ang), destino[1] + r * np.sin(ang) * 0.8, GOLD if i % 2 == 0 else WHITE)
        hz.px(img, destino[0] + (r + 2) * np.cos(ang), destino[1] + (r + 2) * np.sin(ang) * 0.8, LAV)


def destellos(img, t, n=6, semilla=9):
    rs = np.random.RandomState(semilla + t)
    for _ in range(n):
        ang = rs.rand() * 2 * np.pi
        r = 17 + 5 * rs.rand()
        x, y = BODY_C[0] + r * np.cos(ang), BODY_C[1] + r * np.sin(ang) * 1.15
        hz.px(img, x, y, WHITE)
        if rs.rand() < .5:
            for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                hz.px(img, x + dx, y + dy, GOLD)


def pasos(spr, bg, bg_peq, old):
    """Lista de 40 Cap (suelo / personaje y efectos)."""
    B = [0, 0, 1, 1, 1, 1, 0, 0]; A = [0, 1, 1, 1, 0, 0, 0, 0]

    def viejo(t, brillo=0):
        return capa_viejo(old, B[t % 8], A[t % 8], brillo)

    def nueva():
        return hz.transformar(spr, 0, 0, 0, 0)
    SIL_V = silueta(viejo(0)); SIL_N = silueta(nueva())
    res = []
    for t in range(L):
        if t < 6 or t >= 36:                                              # agente respirando
            c = componer(bg, viejo(t))
        elif t < 12:                                                      # carga
            brillo = [0, 1, 2, 1, 2, 2][t - 6]
            c = componer(bg, viejo(t, brillo))
            convergen(c.over, t, 6, 11, GUN_C, 21)
            destellos(c.over, t)
        elif t == 12:
            c = componer(bg, mezclar(viejo(t, 2), SIL_V, 0.55), 18)
            destellos(c.over, t, 8)
            anillo(c.over, 12, 16)
        elif t == 13:
            c = componer(bg, SIL_V, 38)
            anillo(c.over, 19, 24); anillo(c.over, 12, 16, CREAM)
            rayos_en(c.over, GUN_C[0], GUN_C[1], 4, WHITE)
        elif t == 14:
            c = componer(bg, mezclar(SIL_V, SIL_N, 0.5), 38)
            anillo(c.over, 26, 32, CREAM); anillo(c.over, 19, 24)
            rayos_en(c.over, 50, 11, 5, WHITE)
        elif t == 15:
            c = componer(bg, SIL_N, 30)
            anillo(c.over, 30, 36, CREAM)
            rayos_en(c.over, 50, 11, 6, GOLD)
        elif t == 16:
            c = componer(bg, mezclar(SIL_N, nueva(), 0.5), 20)
            rayos_en(c.over, 50, 11, 8, GOLD)
        elif t == 17:
            c = componer(bg, nueva(), 10)
            hz.estrella_rayos(c.over, 50, 11, 6, True)
        elif t < 30:                                                      # el hechizo (pasos 12-23 del guion de utena_hechizo)
            u, o = hz.frame(t - 18 + 12, spr, bg, bg_peq, capas=True)
            c = Cap(u, o)
        elif t == 30:
            u, o = hz.frame(28, spr, bg, bg_peq, capas=True)
            c = Cap(u, o)
        elif t == 31:
            c = componer(bg, mezclar(hz.transformar(spr, 0, 0, 1, 2), SIL_N, 0.6), 30)
            anillo(c.over, 14, 20, CREAM)
        elif t == 32:
            c = componer(bg, SIL_N, 38)
            anillo(c.over, 20, 26); anillo(c.over, 12, 16, CREAM)
        elif t == 33:
            c = componer(bg, mezclar(SIL_N, SIL_V, 0.5), 28)
            anillo(c.over, 14, 20, CREAM)
        elif t == 34:
            c = componer(bg, SIL_V, 16)
        else:                                                             # 35
            c = componer(bg, mezclar(SIL_V, viejo(35), 0.5), 6)
        res.append(c)
    return res


def cargar_capas():
    nat, _, _ = hz.recuperar()
    spr, bg, bg_peq = hz.capas_base(nat)
    return pasos(spr, bg, bg_peq, cargar_viejo())


def main():
    OUT.mkdir(exist_ok=True)
    caps = cargar_capas()
    frames = [Image.fromarray(c.compuesto(), "RGB") for c in caps]
    f126 = [f.resize((126, 126), Image.NEAREST) for f in frames]
    f504 = [f.resize((504, 504), Image.NEAREST) for f in f126]
    n = hz.pe.gif_opaco(f126, OUT / "utena_transformacion_126.gif", TICK)
    hz.pe.gif_opaco(f504, OUT / "utena_transformacion_x4.gif", TICK)
    print(f"{L} pasos = {L * TICK / 1000:.1f} s; {n} colores")
    for r in ("utena_transformacion_126.gif", "utena_transformacion_x4.gif"):
        print(f"  {r}: {Image.open(OUT / r).size}, {(OUT / r).stat().st_size / 1024:.0f} KB")
    cols, w = 8, 126
    sh = Image.new("RGB", (cols * w, ((L + cols - 1) // cols) * w))
    for i, f in enumerate(f126):
        sh.paste(f, ((i % cols) * w, (i // cols) * w))
    sh.save(OUT / "hoja_fotogramas.png")
    d = int((np.abs(np.asarray(frames[-1]).astype(int) - np.asarray(frames[0]).astype(int)).sum(-1) > 0).sum())
    print("píxeles nativos distintos entre el último paso y el primero:", d)
    return frames


if __name__ == "__main__":
    main()
