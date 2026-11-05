"""Maqueta: Utena a tamaño natural (1x) frente a la actual (2x), con el fondo de la referencia a su resolución nativa en ambos casos de la ventana."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "utena_marco")); sys.path.insert(0, str(HERE))
import marco_animado as ma
import referencia as rf
tr = ma.tr
ref = rf.cargar()                                   # fotogramas nativos 224x336
CHROMA = np.full((63, 63, 3), (255, 0, 255), np.uint8)
caps_cr = tr.cargar_capas(lambda t: (CHROMA, CHROMA))            # solo para extraer el círculo del suelo y el personaje
caps2x = tr.cargar_capas(rf.bgf_para(ref, "nebulosa", None), snap_destello=(0, 38))
marcos, ws, win = ma.construir_marco("vertical", 126)
W = np.zeros((126, 126), bool); W[23:103, 23:103] = True        # ventana visible del marco (en píxeles del lienzo de 126)

def escena_1x(t, x0=140, y0=40, off=(31, 31)):
    bg = ref[rf.indice(t) % len(ref)][y0:y0 + 126, x0:x0 + 126]    # 126x126 píxeles nativos de la referencia (1 px = 1 px)
    img = Image.fromarray(bg, "RGB").convert("RGBA")
    c = caps_cr[t]
    esquina = c.under[0, 0]
    m_circ = (c.under != esquina).any(-1)
    capa = np.zeros((126, 126, 4), np.uint8)
    capa[off[1]:off[1] + 63, off[0]:off[0] + 63][m_circ, :3] = c.under[m_circ]
    capa[off[1]:off[1] + 63, off[0]:off[0] + 63][m_circ, 3] = 255
    img.alpha_composite(Image.fromarray(capa, "RGBA"))
    img.alpha_composite(marcos[t].crop((1, 1, 127, 127)))
    capa2 = np.zeros((126, 126, 4), np.uint8); capa2[off[1]:off[1] + 63, off[0]:off[0] + 63] = c.over
    img.alpha_composite(Image.fromarray(capa2, "RGBA"))
    return img.convert("RGB"), capa2[..., 3] > 0

def ocupado_2x(t):
    o = np.repeat(np.repeat(caps2x[t].over[..., 3] > 0, 2, 0), 2, 1)
    return o

mom = [2, 8, 21, 26]
Z = 2
sh = Image.new("RGB", (len(mom) * 126 * Z, 2 * 126 * Z))
occ1, occ2 = [], []
for j, t in enumerate(mom):
    a = ma.escena(caps2x, marcos, t)
    b, mk = escena_1x(t)
    sh.paste(a.resize((126 * Z, 126 * Z), Image.NEAREST), (j * 126 * Z, 0))
    sh.paste(b.resize((126 * Z, 126 * Z), Image.NEAREST), (j * 126 * Z, 126 * Z))
d = ImageDraw.Draw(sh); d.text((6, 6), "ahora (2x)", fill=(255, 255, 255)); d.text((6, 126 * Z + 6), "propuesta (1x)", fill=(255, 255, 255))
sh.save("/projects/sandbox/tmp/fondo_ref/mock_1x.png")
for t in range(40):
    occ2.append((ocupado_2x(t) & W).sum() / W.sum()); occ1.append((escena_1x(t)[1] & W).sum() / W.sum())
print("fondo tapado por Utena y sus efectos dentro de la ventana, media de los 40 pasos: 2x = %.0f %%, 1x = %.0f %%" % (100 * np.mean(occ2), 100 * np.mean(occ1)))
print("máximo: 2x = %.0f %%, 1x = %.0f %%" % (100 * np.max(occ2), 100 * np.max(occ1)))
print("tamaño de Utena en el lienzo de 126: 2x = 86x102 px; 1x = 43x51 px (ventana de 80x80)")
