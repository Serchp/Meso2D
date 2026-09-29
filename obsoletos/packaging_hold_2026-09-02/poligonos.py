import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, MultiPoint
from shapely.affinity import translate
import random

def generar_poligono_irregular(n_lados, radio=1.0, ruido=0.3):
    """
    Genera un polígono irregular con n lados.
    - radio: radio medio
    - ruido: desviación aleatoria del radio
    """
    angulos = np.linspace(0, 2 * np.pi, n_lados, endpoint=False)
    np.random.shuffle(angulos)  # para evitar formas simétricas
    radios = np.clip(np.random.normal(loc=radio, scale=ruido, size=n_lados), 0.1*radio, 2*radio)
    puntos = [(np.cos(a)*r, np.sin(a)*r) for a, r in zip(angulos, radios)]

    # Convex hull para asegurar contorno válido y cerrado
    multip = MultiPoint(puntos)
    poligono = multip.convex_hull
    return poligono

def colocar_poligono_irregular(no_colisiona_con, tamaño_area=(10, 10), intentos_max=1000):
    for _ in range(intentos_max):
        n_lados = random.randint(4, 8)
        radio = random.uniform(0.4, 0.8)
        p = generar_poligono_irregular(n_lados=n_lados, radio=radio, ruido=0.25)

        x = random.uniform(0, tamaño_area[0])
        y = random.uniform(0, tamaño_area[1])
        p = translate(p, xoff=x, yoff=y)

        if p.bounds[0] < 0 or p.bounds[2] > tamaño_area[0]:
            continue
        if p.bounds[1] < 0 or p.bounds[3] > tamaño_area[1]:
            continue

        if all(not p.intersects(otro) for otro in no_colisiona_con):
            return p
    return None

# Parámetros
num_poligonos = 20
tamaño_area = (10, 10)
poligonos = []

for _ in range(num_poligonos):
    pol = colocar_poligono_irregular(poligonos, tamaño_area)
    if pol:
        poligonos.append(pol)

# Visualización
fig, ax = plt.subplots()
for poly in poligonos:
    x, y = poly.exterior.xy
    ax.fill(x, y, alpha=0.5, edgecolor='black')

ax.set_xlim(0, tamaño_area[0])
ax.set_ylim(0, tamaño_area[1])
ax.set_aspect('equal')
plt.show()
