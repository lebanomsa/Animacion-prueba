"""Fotogramas de 'utena 2.gif' a su tamaño real (el GIF está ampliado exactamente a x3: 288x384 -> 96x128)."""
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).parent.parent
ESC = 3


def fotogramas():
    g = Image.open(ROOT / "utena 2.gif")
    out, dur = [], []
    for i in range(g.n_frames):
        g.seek(i)
        f = g.convert("RGBA")
        out.append(f.resize((f.width // ESC, f.height // ESC), Image.NEAREST))
        dur.append(g.info.get("duration", 100))
    return out, dur
