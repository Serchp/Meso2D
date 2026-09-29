#!/usr/bin/env python3
"""Test visual: generar imagen de polígonos para verificar si hay solapamientos"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import PatchCollection
from shapely.geometry import Polygon
from shapely import affinity
import numpy as np

from Worker_poligonos import WorkerPoligonos
from simulation_model import SimulationModel

# Parámetros
params = SimulationModel(
    x=250, y=250,
    Pagg=0.6,
    sieve_size=[16, 8, 4, 2, 1, 0.5, 0.125],
    tpp=[100, 90, 70, 50, 30, 15, 0],
    Pporos=0.15,
    dporo_min=0.5, dporo_max=2.0,
    dpto_min_aridos=0.1, dpto_max_aridos=0.5,
    Ppto_react_aridos=0.05,
    dpto_min_pasta=0.1, dpto_max_pasta=0.5,
    Ppto_react_pasta=0.05
)

worker = WorkerPoligonos(params)

# Mock signals
class MockSignal:
    def emit(self, *args): pass

worker.progreso = MockSignal()
worker.information = MockSignal()
worker.information_error = MockSignal()
worker.imagen = MockSignal()
worker.pore_list = MockSignal()
worker.coarse_list = MockSignal()
worker.fine_list = MockSignal()
worker.reactive_list = MockSignal()

print("Generando simulación...")
worker.dosificacion_sin_extrafinos()
worker.calcular_areas_aridos_sin_extrafinos()
worker.calcular_aridos_por_area_gruesos()
worker.calcular_aridos_por_area_finos()
worker.colocar_aridos_poligonales()

print(f"\nPolígonos generados:")
print(f"  - Gruesos: {len(worker.lista_aridos_gruesos)}")
print(f"  - Finos: {len(worker.lista_aridos_finos)}")

# Crear figura
fig, ax = plt.subplots(figsize=(12, 12))
ax.set_aspect('equal')
ax.set_xlim(0, params.x)
ax.set_ylim(0, params.y)
ax.set_title(f"Mesostructure - Aggregates Placement\n{len(worker.lista_aridos)} polygons total")

# Función para convertir Shapely a matplotlib patch
def shapely_to_patch(polygon):
    return mpatches.Polygon(list(polygon.exterior.coords), closed=True)

# Dibujar áridosgruesos (azul)
if worker.todos_aridos_gruesos:
    patches_gruesos = [shapely_to_patch(e) for e in worker.todos_aridos_gruesos]
    gruesos_collection = PatchCollection(patches_gruesos, facecolor='lightblue', edgecolor='blue', linewidth=1, alpha=0.7)
    ax.add_collection(gruesos_collection)

# Dibujar áridos finos (cyan)
if worker.todos_aridos_finos:
    patches_finos = [shapely_to_patch(e) for e in worker.todos_aridos_finos]
    finos_collection = PatchCollection(patches_finos, facecolor='lightcyan', edgecolor='darkblue', linewidth=0.5, alpha=0.5)
    ax.add_collection(finos_collection)

# Dibujar contorno
probeta = mpatches.Rectangle((0, 0), params.x, params.y, color='black', fill=False, linewidth=2)
ax.add_patch(probeta)

# Guardar imagen
output_file = "debug_visualization.png"
plt.savefig(output_file, dpi=150, bbox_inches='tight')
print(f"\n✅ Imagen guardada: {output_file}")

# Verificar solapamientos matemáticamente
print("\nVerificando solapamientos...")
solapamientos_encontrados = []
for i in range(len(worker.lista_aridos)):
    for j in range(i+1, len(worker.lista_aridos)):
        poly1 = worker.lista_aridos[i]
        poly2 = worker.lista_aridos[j]
        intersection = poly1.intersection(poly2)
        if intersection.area > 1e-8:
            solapamientos_encontrados.append((i, j, intersection.area))

if solapamientos_encontrados:
    print(f"❌ Solapamientos detectados: {len(solapamientos_encontrados)}")
    for i, j, area in solapamientos_encontrados[:5]:
        print(f"   - Polígono {i} ∩ {j} = {area:.6f}")
else:
    print("✅ NO hay solapamientos - El código está funcionando correctamente")

print("\nAbre la imagen 'debug_visualization.png' para inspeccionar visualmente")
