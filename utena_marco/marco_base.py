"""Marco morado (arriba) -> dorado (abajo) para Utena: el diseño de nudos de siempre (secuencia/marco.py) con degradado vertical suave."""
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "secuencia"))
import marco   # noqa: E402

MORADO = [(0.0, (16, 6, 36)), (0.3, (52, 24, 100)), (0.6, (104, 60, 170)), (0.85, (160, 116, 224)), (1.0, (222, 200, 250))]
ORO = [(0.0, (30, 18, 4)), (0.3, (92, 58, 14)), (0.6, (170, 118, 30)), (0.85, (226, 176, 70)), (1.0, (255, 238, 170))]
BANDS = 12
ESTILO = {"suave": (0.30, 0.70, "continuo"), "bandas": (0.30, 0.70, 4), "corte": (0.46, 0.54, "continuo")}
_actual = ["suave"]


def recolor_morado_oro(rgb, top_stops, bot_stops):
    N = marco.N
    y = np.repeat(np.arange(N)[:, None], N, axis=1)
    lum = rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114
    v = np.clip(lum / np.percentile(lum, 98), 0, 1)
    band = np.minimum(y * BANDS // N, BANDS - 1)
    T0, T1, pasos = ESTILO[_actual[0]]
    t = np.clip(((band + 0.5) / BANDS - T0) / (T1 - T0), 0, 1)
    t = t * t * (3 - 2 * t)                                   # suavizado
    if pasos != "continuo":                                   # degradado en pocos escalones, al estilo pixel art
        t = np.round(t * (pasos - 1)) / (pasos - 1)
    top, bot = marco.ramp(top_stops, v), marco.ramp(bot_stops, v)
    return np.clip(top + (bot - top) * t[..., None], 0, 255).round().astype(np.uint8)


def build(estilo="suave"):
    """(marco RGBA uint8 de 128x128, (x0, y0, x1, y1) de la ventana). estilo: 'suave', 'bandas' o 'corte'."""
    _actual[0] = estilo
    marco.recolor = recolor_morado_oro
    fr, win = marco.build(MORADO, ORO)
    return np.array(fr), win
