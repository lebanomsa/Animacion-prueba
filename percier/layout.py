"""Disposición de la animación de Percier (se puede cambiar antes de importar `completa`).

Valores por defecto = animación sin marco ya entregada. La versión del marco a x5 usa X_F=80, AX=62 y esperas más cortas
(ver final.py) para que todo quepa en la ventana de 128 píxeles y el ciclo dure 72 pasos.
"""
X_F = 90                      # centro de las botas de Percier
AX = 64                       # esquina inferior derecha de la nube
DUR_A = ((0, 4), (1, 2), (2, 3), (3, 2), (4, 2), (5, 3), (6, 3), (7, 2))     # (fotograma de la hoja 1, pasos)
