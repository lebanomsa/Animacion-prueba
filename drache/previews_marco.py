"""Vista previa: los tres marcos con la animación del bucle 1 dentro (ticks 8, 46 y 58)."""
from pathlib import Path
import numpy as np
from PIL import Image
import bucles as b
import entrega_stage as e
import marco_drache as m

OUT = Path(__file__).parent / "marco_previews"
T = 28

def main():
    OUT.mkdir(exist_ok=True)
    b.H, b.SUELO = e.H, e.SUELO
    R = b.cargar()
    capas = b.dibujar_ticks_bucle1(b.guion_bucle1(R), R)
    bg = Image.fromarray(e.agrupar(np.asarray(e.con_sombra(e.fondo_rgb())), e.K_FONDO)).convert("RGBA")
    ticks = [8, 46, 58]
    for tema in m.TEMAS:
        fr = m.construir(e.W, e.H, tema)
        al = np.asarray(fr)[T:T + e.H, T:T + e.W, 3]
        print(tema, fr.size, "píxeles opacos dentro de la ventana:", int((al > 0).sum()))
        tiras = []
        for t in ticks:
            c = Image.new("RGBA", fr.size, (0, 0, 0, 255))
            esc = bg.copy(); esc.alpha_composite(capas[t]); c.paste(esc, (T, T))
            c.alpha_composite(fr)
            tiras.append(c.convert("RGB"))
        W, H = tiras[0].size
        hoja = Image.new("RGB", (W * 3 + 20, H), (30, 30, 30))
        for i, c in enumerate(tiras):
            hoja.paste(c, (i * (W + 10), 0))
        hoja.save(OUT / f"marco_{tema}_preview.png")
        fr.save(OUT / f"marco_{tema}.png")

if __name__ == "__main__":
    main()
