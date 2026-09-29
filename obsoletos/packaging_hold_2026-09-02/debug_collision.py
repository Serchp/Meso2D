#!/usr/bin/env python3
"""Script rápido para verificar si hay overlap real en lista_aridos"""

import numpy as np
from shapely.geometry import Polygon
from shapely import affinity

# Crear 3 polígonos de prueba
def crear_poligono_simple(cx, cy, tamaño=10):
    """Crea un polígono cuadrado simple"""
    s = tamaño / 2
    coords = [(cx-s, cy-s), (cx+s, cy-s), (cx+s, cy+s), (cx-s, cy+s)]
    return Polygon(coords)

# Caso de prueba 1: dos polígonos que SI solapan
p1 = crear_poligono_simple(50, 50, tamaño=20)
p2 = crear_poligono_simple(55, 55, tamaño=20)

print("="*60)
print("TEST 1: Polígonos que DEBERÍAN solapar")
print("="*60)
print(f"P1 bounds: {p1.bounds}")
print(f"P2 bounds: {p2.bounds}")
print(f"P1.intersects(P2): {p1.intersects(p2)}")
print(f"P1.intersection(P2).area: {p1.intersection(p2).area}")
print()

# Caso de prueba 2: dos polígonos que NO solapan
p3 = crear_poligono_simple(100, 100, tamaño=10)
p4 = crear_poligono_simple(200, 200, tamaño=10)

print("="*60)
print("TEST 2: Polígonos que NO deberían solapar")
print("="*60)
print(f"P3 bounds: {p3.bounds}")
print(f"P4 bounds: {p4.bounds}")
print(f"P3.intersects(P4): {p3.intersects(p4)}")
print(f"P3.intersection(P4).area: {p3.intersection(p4).area}")
print()

# Ahora hacer el test REAL con los datos del worker
print("="*60)
print("TEST 3: Verificación con Worker_poligonos (DOMINIO PEQUEÑO)")
print("="*60)

try:
    from Worker_poligonos import WorkerPoligonos
    from simulation_model import SimulationModel
    
    params = SimulationModel(
        x=100, y=100,  # Dominio pequeño para rápido debug
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
    
    # Run simulation
    print("Generando y colocando polígonos en dominio 100x100...")
    worker.dosificacion_sin_extrafinos()
    worker.calcular_areas_aridos_sin_extrafinos()
    worker.calcular_aridos_por_area_gruesos()
    worker.calcular_aridos_por_area_finos()
    worker.colocar_aridos_poligonales()
    
    print(f"✓ Total polígonos en lista_aridos: {len(worker.lista_aridos)}")
    print()
    
    # Verificar solapamientos
    print("Buscando solapamientos...")
    solapamientos = []
    for i in range(len(worker.lista_aridos)):
        poly1 = worker.lista_aridos[i]
        for j in range(i+1, len(worker.lista_aridos)):
            poly2 = worker.lista_aridos[j]
            intersection = poly1.intersection(poly2)
            if intersection.area > 1e-8:
                solapamientos.append((i, j, intersection.area))
                if len(solapamientos) <= 5:  # Mostrar solo primeros 5
                    print(f"  ⚠️  Solapamiento: [{i}] ∩ [{j}] = {intersection.area:.6f}")
    
    print()
    if solapamientos:
        print(f"❌ TOTAL SOLAPAMIENTOS ENCONTRADOS: {len(solapamientos)}")
        print("   → El problema persiste, la detección de colisiones no funciona")
    else:
        print("✅ NO HAY SOLAPAMIENTOS - La función está funcionando correctamente!")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
