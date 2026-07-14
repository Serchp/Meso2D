
from worker_base import WorkerBase, SimParams, SimulationStopped
import io
import numpy as np
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtGui import QPixmap, QImage
from matplotlib import pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.collections import PatchCollection
from shapely.geometry import Point, Polygon, box
from shapely import affinity
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.patches import Circle
from shapely.strtree import STRtree
from shapely.geometry import box
import random
from opensimplex import OpenSimplex


class WorkerPoligonos(WorkerBase):

    def __init__(self, params: SimParams, todo_correcto: bool = True,
                 check_poros: bool = False, check_puntos: bool = False,
                 check_puntos_aridos: bool = False, check_puntos_pasta: bool = False):

        super().__init__(params)


        self.datos = None   # variable para necesaria para guardar/abrir proyectos

        """"
        Variables necesarias
        """
        self.A = None
        self.Aagg = []
        self.A_remanente = 0
        self.num_particulas = 0
        self.particulas = []
        self.radios = []
        self.lista_aridos = []
        self.todos_aridos = []
        self.radios_poros = []
        self.todos_poros = []
        self.lista_poros = []  # Shapely geometries for collision detection
        self.lista_poros_data = []  # [x, y, r] tuples for export
        self.lista_ptos_react = []
        self.lista_ptos_react_aridos = []
        self.lista_ptos_react_pasta = []
        self.todos_ptos_react = []

        self.radios_puntos = []
        self.radios_puntos_aridos = []
        self.radios_puntos_pasta = []

        self.sieve_size_buena = []
        self.lista_aridos_gruesos = []
        self.lista_aridos_finos = []
        self.Aagg_gruesos = []
        self.Aagg_finos = []
        # self.radios_gruesos_elipses = []
        self.radios_gruesos_elipses = []
        # self.radios_finos_elipses = []
        self.radios_finos_elipses = []
        self.todos_aridos_gruesos = []
        self.todos_aridos_finos = []

        self.aridos_puestos = False
        self.poros_puestos = False
        self.A_poros = None
        self.A_puntos_aridos = None
        self.A_puntos_pasta = None
        self.existe_estructura = False

        self.todo_correcto = todo_correcto

        self.check_poros = check_poros
        self.check_puntos = check_puntos
        self.check_puntos_aridos = check_puntos_aridos
        self.check_puntos_pasta = check_puntos_pasta

    """refactorizadas las funcianes para el cálculo de las distancias
    vectorizadas con arrays para evitar bucles explícitos y calculando las distancias en bloque
    """

    def distancias(self, lista_geometrias, x, y, r):
        """Verifica que un nuevo círculo no colisione con ninguna geometría en la lista"""
        nuevo_circulo = Point(x, y).buffer(r)
        # return all(not nuevo_circulo.intersects(geom) for geom in lista_geometrias)
        return all(not nuevo_circulo.intersects(Point(g[0], g[1]).buffer(g[2])) for g in lista_geometrias)

    def distancias(self, lista_geometrias, x, y, r):
        nuevo_circulo = Point(x, y).buffer(r)
        resultado = []
        for g in lista_geometrias:
            if isinstance(g, Polygon):
                resultado.append(not nuevo_circulo.intersects(g))
            elif isinstance(g, list) and len(g) == 3:
                resultado.append(not nuevo_circulo.intersects(Point(g[0], g[1]).buffer(g[2])))
            else:
                raise TypeError(f"Elemento inválido en lista_geometrias: {g}")
        return all(resultado)

    def distancias_aridos_ptos(self, lista_aridos, x, y, r):
        """Verifica que un nuevo círculo colisione con al menos un árido.

        Soporta:
          - círculos [x, y, r]
          - elipses [cx, cy, a, b, angle?]
          - geometrías Shapely (Polygon, Geometry)
        """
        if not lista_aridos:
            return False

        nuevo_circulo = Point(x, y).buffer(r, resolution=32)
        for ar in lista_aridos:
            if isinstance(ar, (list, tuple)) and len(ar) == 3:
                try:
                    ar_circ = Point(ar[0], ar[1]).buffer(ar[2], resolution=32)
                except Exception:
                    continue
                if nuevo_circulo.intersects(ar_circ):
                    return True
            elif isinstance(ar, (list, tuple)) and len(ar) >= 4:
                try:
                    cx, cy, a, b = ar[0], ar[1], ar[2], ar[3]
                    angle = ar[4] if len(ar) > 4 else 0.0
                    base = Point(cx, cy).buffer(1.0, resolution=64)
                    elipse = affinity.scale(base, a, b, origin=(cx, cy))
                    if angle:
                        elipse = affinity.rotate(elipse, angle, origin=(cx, cy))
                except Exception:
                    continue
                if nuevo_circulo.intersects(elipse):
                    return True
            else:
                try:
                    if nuevo_circulo.intersects(ar):
                        return True
                except Exception:
                    continue
        return False

    def distancias_poros_aridos(self, x, y, r, lista_aridos):
        """Verifica que el poro no colisione con ningún árido poligonal"""
        poro = Point(x, y).buffer(r)
        return all(not poro.intersects(arido) for arido in lista_aridos)

    def calcular_poros(self):
        if self.check_poros:
            self.A_poros = self.A * self.params.Pporos
            while self.A_poros > np.pi * (self.params.dporo_min / 2) ** 2:
                self.check_stop()
                rporo = (self.params.dporo_min + np.random.random() * (self.params.dporo_max - self.params.dporo_min)) / 2
                Aporo = np.pi * (rporo) ** 2
                self.A_poros = self.A_poros - Aporo
                self.radios_poros.append(rporo)
            self.progreso.emit(40)
            self.information.emit('Poros calculados. ' + str(len(self.radios_poros)) + ' Poros')

    def colocar_poros(self):
        def dentro_de_limites(x, y, r):
            return r < x < self.params.x - r and r < y < self.params.y - r

        def intersecta_con_algo(geom, geoms):
            for g in geoms:
                if geom.intersects(g):
                    return True
            return False

        intentos_maximos = 3000
        while self.radios_poros:
            self.check_stop()
            r = self.radios_poros.pop(0)
            colocado = False

            for _ in range(intentos_maximos):
                x = np.random.uniform(0, self.params.x)
                y = np.random.uniform(0, self.params.y)
                if not dentro_de_limites(x, y, r):
                    continue

                poro = Point(x, y).buffer(r, resolution=64)
                if self.aridos_puestos and intersecta_con_algo(poro, self.lista_aridos):
                    continue
                if intersecta_con_algo(poro, self.lista_poros):
                    continue

                self.lista_poros.append(poro)
                self.lista_poros_data.append([x, y, r])
                self.todos_poros.append(Circle((x, y), r, color='r'))
                self.poros_puestos = True
                colocado = True
                break

            if not colocado:
                print(f"No se pudo colocar un poro de radio {r:.3f} tras {intentos_maximos} intentos.")

        print(f"Poros colocados: {len(self.lista_poros)}")
        self.progreso.emit(50)
        self.information.emit('Poros colocados')

    """
    chequear si exinten tamaños de áridos menores a dos y eliminarlos
    """
    def dosificacion_sin_extrafinos(self):
        print('la sieve size es ' + str(self.params.sieve_size))
        print('la sieve size buena es ' + str(self.sieve_size_buena))
        n = 0
        while self.params.sieve_size[n] >= 2:
            self.sieve_size_buena.append(self.params.sieve_size[n])
            n = n + 1
            # return self.sieve_size_buena
        self.information.emit('Quitados los extrafinos de la dosificación.')
        self.progreso.emit(15)
        print('la buena dosificacion es ' + str(self.sieve_size_buena))

    def calcular_areas_aridos_sin_extrafinos(self):
        self.A = float(self.params.x) * float(self.params.y)
        self.Aagg = []

        # Aseguramos que los tamaños de tamiz y TPP estén en float
        sieve = [float(s) for s in self.sieve_size_buena]
        tpp = [float(p) for p in self.params.tpp]

        for i in range(len(sieve) - 1):  # i+1 no se sale del rango
            fraccion = (tpp[i] - tpp[i + 1]) / (tpp[0] - tpp[-1])
            area_intervalo = fraccion * self.params.Pagg * self.A
            self.Aagg.append(area_intervalo)  # No redondeamos aquí

        print([round(a, 2) for a in self.Aagg])
        print('áreas calculadas')

        self.progreso.emit(10)
        self.information.emit(
            'Área de cada fracción de áridos calculada. ' +
            str([round(a, 2) for a in self.Aagg])
        )
        print('estás informado')

        # Clasificación en gruesos (>4 mm) y finos (≤4 mm) con punto flotante
        self.Aagg_gruesos = []
        self.Aagg_finos = []

        for tam, area in zip(sieve[:-1], self.Aagg):  # Último tamiz no tiene área
            if tam > 4.0:
                self.Aagg_gruesos.append(area)
            else:
                self.Aagg_finos.append(area)

        print('la Aagg es ' + str([round(a, 2) for a in self.Aagg]))
        print('la Aagg de los gruesos es ' + str([round(a, 2) for a in self.Aagg_gruesos]))
        print('la Aagg de los finos es ' + str([round(a, 2) for a in self.Aagg_finos]))

    import numpy as np

    def generar_poligono_irregular(self, area_objetivo, intentos=100):
        for _ in range(intentos):
            n_lados = np.random.randint(5, 11)
            angulos = np.linspace(0, 2 * np.pi, n_lados, endpoint=False)
            radios = np.random.uniform(0.8, 1.2, n_lados)
            x = radios * np.cos(angulos)
            y = radios * np.sin(angulos)
            x -= np.mean(x)
            y -= np.mean(y)
            area_actual = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
            if area_actual == 0:
                continue
            escala = np.sqrt(area_objetivo / area_actual)
            x *= escala
            y *= escala
            area_final = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
            if np.abs(area_final - area_objetivo) / area_objetivo < 0.05:
                return list(zip(x, y)), area_final
        return None

    def calcular_aridos_por_area_gruesos(self):
        self.poligonos_gruesos = []
        j = 0
        while j < len(self.Aagg_gruesos):
            num_particulas = 0
            area_c = 0
            if j + 1 >= len(self.sieve_size_buena):
                print(f"Índice fuera de rango en sieve_size_buena: j={j}")
                break
            self.Aagg_gruesos[j] += self.A_remanente
            while self.Aagg_gruesos[j] - area_c > 0.0001:
                d = self.sieve_size_buena[j + 1] + np.random.rand() * (
                        self.sieve_size_buena[j] - self.sieve_size_buena[j + 1])
                area_max = np.pi * (d / 2) ** 2
                resultado = self.generar_poligono_irregular(area_max * np.random.uniform(0.5, 1.0))
                if resultado is None:
                    print(f"No se pudo generar polígono válido en j={j}")
                    break
                # poligono, area = resultado
                coordenadas, area = resultado
                if area + area_c < self.Aagg_gruesos[j]:
                    area_c += area
                    poligono = Polygon(coordenadas)
                    if not poligono.is_valid:
                        poligono = poligono.buffer(0)
                    self.poligonos_gruesos.append(poligono)
                    num_particulas += 1
                else:
                    break
            self.A_remanente = self.Aagg_gruesos[j] - area_c
            self.particulas.append(num_particulas)
            j += 1
        self.progreso.emit(20)
        self.information.emit('Áridos gruesos (polígonos) por área calculados. ' + str(self.particulas))
        print('la lista de áridos gruesos es ' + str(self.lista_aridos_gruesos))

    def calcular_aridos_por_area_finos(self):
        self.poligonos_finos = []
        k = len(self.Aagg_gruesos)
        l = 0
        while l < len(self.Aagg_finos):
            num_particulas = 0
            area_c = 0
            if k + 1 >= len(self.params.sieve_size):
                print(f"Índice fuera de rango en sieve_size: k={k}")
                break
            self.Aagg_finos[l] += self.A_remanente
            while self.Aagg_finos[l] - area_c > 0.0001:
                d = self.params.sieve_size[k + 1] + np.random.rand() * (
                        self.params.sieve_size[k] - self.params.sieve_size[k + 1])
                area_max = np.pi * (d / 2) ** 2
                resultado = self.generar_poligono_irregular(area_max * np.random.uniform(0.5, 1.0))
                if resultado is None:
                    print(f"No se pudo generar polígono válido en l={l}")
                    break
                # poligono, area = resultado
                coordenadas, area = resultado
                if area + area_c < self.Aagg_finos[l]:
                    area_c += area
                    poligono = Polygon(coordenadas)
                    if not poligono.is_valid:
                        poligono = poligono.buffer(0)
                    self.poligonos_finos.append(poligono)
                    num_particulas += 1
                else:
                    break
            self.A_remanente = self.Aagg_finos[l] - area_c
            self.particulas.append(num_particulas)
            l += 1
            k += 1
        self.progreso.emit(22)
        self.information.emit('Áridos finos (polígonos) por área calculados. ' + str(self.particulas))

    def colocar_aridos_poligonales(self):
        dominio = box(0, 0, self.params.x, self.params.y)

        def limpio(poly):
            if poly is None:
                return None
            if not poly.is_valid:
                poly = poly.buffer(0)
            if poly.is_empty:
                return None
            return poly

        def colocar(lista_fuente, lista_datos, lista_destino, progreso, mensaje):
            intentos_maximos = 3000
            colocados = 0

            for base in lista_fuente:
                self.check_stop()
                base = limpio(base)
                if base is None:
                    continue

                for _ in range(intentos_maximos):
                    x = np.random.uniform(0, self.params.x)
                    y = np.random.uniform(0, self.params.y)
                    angulo = np.random.uniform(0, 360)

                    candidato = affinity.rotate(base, angulo, origin='centroid')
                    candidato = affinity.translate(candidato, x - candidato.centroid.x, y - candidato.centroid.y)
                    candidato = limpio(candidato)
                    if candidato is None:
                        continue

                    if not dominio.contains(candidato):
                        continue
                    if any(candidato.intersects(g) for g in self.lista_aridos):
                        continue
                    if any(candidato.intersects(p) for p in self.lista_poros):
                        continue

                    self.lista_aridos.append(candidato)
                    lista_destino.append(candidato)
                    lista_datos.append([x, y, angulo])
                    self.aridos_puestos = True
                    colocados += 1
                    break

            self.progreso.emit(progreso)
            self.information.emit(f'{mensaje} colocados. {colocados}')

        self.lista_aridos = []
        self.todos_aridos_gruesos = []
        self.todos_aridos_finos = []
        self.lista_aridos_gruesos = []
        self.lista_aridos_finos = []
        self.aridos_puestos = False

        colocar(self.poligonos_gruesos, self.lista_aridos_gruesos, self.todos_aridos_gruesos, 30, 'Áridos gruesos')
        colocar(self.poligonos_finos, self.lista_aridos_finos, self.todos_aridos_finos, 32, 'Áridos finos')

    def calcular_puntos_sin_extrafinos(self):
        """puntos sobre áridos gruesos"""
        if self.check_puntos_aridos:
            if self.params.Ppto_react_aridos:
                self.A_puntos_aridos = self.params.Ppto_react_aridos * self.A
                while self.A_puntos_aridos > np.pi * (self.params.dpto_min_aridos / 2) ** 2:
                    self.check_stop()
                    if self.params.dpto_min_aridos == self.params.dpto_max_aridos:
                        rpunto = self.params.dpto_min_aridos / 2
                    else:
                        rpunto = (self.params.dpto_min_aridos + np.random.random() *
                                  (self.params.dpto_max_aridos - self.params.dpto_min_aridos)) / 2
                    Apunto = np.pi * (rpunto) ** 2
                    self.A_puntos_aridos = self.A_puntos_aridos - Apunto
                    self.radios_puntos.append(rpunto)  # ¿sobra?
                    self.radios_puntos_aridos.append(rpunto)
            self.progreso.emit(55)
            self.information.emit('Puntos reactivos sobre los áridos calculados')

        """puntos sobre los finos (y pasta)"""
        if self.check_puntos_pasta:
            if self.params.Ppto_react_pasta:
                self.A_puntos_pasta = self.params.Ppto_react_pasta * self.A
                while self.A_puntos_pasta > np.pi * (self.params.dpto_min_pasta / 2) ** 2:
                    self.check_stop()
                    if self.params.dpto_min_pasta == self.params.dpto_max_pasta:
                        rpunto = self.params.dpto_min_pasta / 2
                    else:
                        rpunto = (self.params.dpto_min_pasta + np.random.random() * (
                                self.params.dpto_max_pasta - self.params.dpto_min_pasta)) / 2
                    Apunto = np.pi * (rpunto) ** 2
                    self.A_puntos_pasta = self.A_puntos_pasta - Apunto
                    self.radios_puntos.append(rpunto)  # ¿sobra?
                    self.radios_puntos_pasta.append(rpunto)
            self.progreso.emit(60)
            self.information.emit('Puntos reactivos sobre la pasta calculados')

    def colocar_puntos_sin_extrafinos(self):
        """Coloca los puntos reactivos sobre los áridos y la pasta."""
        def dentro_de_limites(x, y, r):
            return r < x < self.params.x - r and r < y < self.params.y - r

        def intentar_colocar_punto(x, y, r, lista_existente, evitar_aridos, poros_puestos):
            if not dentro_de_limites(x, y, r):
                return False
            if poros_puestos and not self.distancias(self.lista_poros, x, y, r):
                return False
            if evitar_aridos and not self.distancias(self.lista_aridos, x, y, r):
                return False
            if not evitar_aridos and not self.distancias_aridos_ptos(self.lista_aridos, x, y, r):
                return False
            if len(lista_existente) > 0 and not self.distancias(lista_existente, x, y, r):
                return False
            return True

        def colocar_lista(lista_radios, lista_guardar, evitar_aridos, poros_puestos, max_intentos=1000):
            while lista_radios:
                self.check_stop()
                r = lista_radios[0]
                colocado = False
                for _ in range(max_intentos):
                    x = np.random.uniform(0, self.params.x)
                    y = np.random.uniform(0, self.params.y)
                    if intentar_colocar_punto(x, y, r, lista_guardar, evitar_aridos, poros_puestos):
                        lista_guardar.append([x, y, r])
                        self.todos_ptos_react.append(plt.Circle((x, y), r, color='y'))
                        lista_radios.pop(0)
                        colocado = True
                        break
                if not colocado:
                    print(f"⚠️ No se pudo colocar punto con radio {r:.3f} tras {max_intentos} intentos.")
                    lista_radios.pop(0)

        def generar_centros_clusters(k_minimo, sigma=5):
            radio_influencia = 3 * sigma
            area_cluster = np.pi * radio_influencia ** 2
            num_clusters = max(k_minimo, int(np.ceil((self.params.x * self.params.y) / area_cluster)))
            return [
                (np.random.uniform(0, self.params.x), np.random.uniform(0, self.params.y))
                for _ in range(num_clusters)
            ]

        def colocar_con_clusters(lista_radios, lista_guardar, evitar_aridos, poros_puestos, k=5, sigma=5, max_intentos=1000):
            centros = generar_centros_clusters(k)
            while lista_radios:
                self.check_stop()
                r = lista_radios[0]
                colocado = False
                for _ in range(max_intentos):
                    self.check_stop()
                    cx, cy = random.choice(centros)
                    x = np.random.normal(cx, sigma)
                    y = np.random.normal(cy, sigma)
                    if intentar_colocar_punto(x, y, r, lista_guardar, evitar_aridos, poros_puestos):
                        lista_guardar.append([x, y, r])
                        self.todos_ptos_react.append(plt.Circle((x, y), r, color='y'))
                        lista_radios.pop(0)
                        colocado = True
                        break
                if not colocado:
                    print(f"⚠️ No se pudo colocar punto con radio {r:.3f} tras {max_intentos} intentos (clusters).")
                    lista_radios.pop(0)

        def colocar_con_simplex(lista_radios, lista_guardar, evitar_aridos, poros_puestos, escala=0.05, umbral=0.3, max_intentos=1000):
            ruido = OpenSimplex(seed=42)
            while lista_radios:
                self.check_stop()
                r = lista_radios[0]
                colocado = False
                for _ in range(max_intentos):
                    self.check_stop()
                    x = np.random.uniform(0, self.params.x)
                    y = np.random.uniform(0, self.params.y)
                    valor = (ruido.noise2(x * escala, y * escala) + 1) / 2
                    if valor < umbral:
                        continue
                    if intentar_colocar_punto(x, y, r, lista_guardar, evitar_aridos, poros_puestos):
                        lista_guardar.append([x, y, r])
                        self.todos_ptos_react.append(plt.Circle((x, y), r, color='y'))
                        lista_radios.pop(0)
                        colocado = True
                        break
                if not colocado:
                    print(f"⚠️ No se pudo colocar punto con radio {r:.3f} tras {max_intentos} intentos (simplex).")
                    lista_radios.pop(0)

        # Colocar puntos sobre áridos con clusters
        if self.check_puntos_aridos:
            colocar_con_clusters(self.radios_puntos_aridos, self.lista_ptos_react_aridos,
                                 evitar_aridos=False, poros_puestos=self.poros_puestos)
            self.progreso.emit(65)
            self.information.emit('Puntos reactivos sobre los áridos colocados')

        # Colocar puntos sobre pasta con ruido Simplex
        if self.check_puntos_pasta:
            colocar_con_simplex(self.radios_puntos_pasta, self.lista_ptos_react_pasta,
                                evitar_aridos=True, poros_puestos=self.poros_puestos)
            self.progreso.emit(70)
            self.information.emit('Puntos reactivos sobre la pasta colocados')

        self.lista_ptos_react = self.lista_ptos_react_aridos + self.lista_ptos_react_pasta

    def plotear_resultados(self):
        figure, axes = plt.subplots(dpi=200)
        plt.axis("equal")
        axes.set_xlim(0, self.params.x)
        axes.set_ylim(0, self.params.y)

        """Convertir Shapely Polygons a matplotlib.patches.Polygon"""

        def shapely_to_patch(polygon):
            return MplPolygon(list(polygon.exterior.coords), closed=True)

        """Añadir colecciones de parches"""
        if self.todos_poros:
            print('hay numerosos poros. Estos = ' + str(len(self.todos_poros)))
            poros_collection = PatchCollection(self.todos_poros, color='red', edgecolor='none')
            axes.add_collection(poros_collection)

        if self.todos_aridos_gruesos:
            patches_gruesos = [shapely_to_patch(e) for e in self.todos_aridos_gruesos]
            aridos_collection = PatchCollection(
                patches_gruesos, 
                facecolor='lightblue', 
                edgecolor='blue', 
                linewidth=0.5,
                antialiased=True,
                alpha=0.8
            )
            axes.add_collection(aridos_collection)

        if self.todos_aridos_finos:
            patches_finos = [shapely_to_patch(e) for e in self.todos_aridos_finos]
            aridos_collection = PatchCollection(
                patches_finos, 
                facecolor='lightcyan', 
                edgecolor='darkblue', 
                linewidth=0.3,
                antialiased=True,
                alpha=0.6
            )
            axes.add_collection(aridos_collection)

        if self.todos_ptos_react:
            react_collection = PatchCollection(
                self.todos_ptos_react, 
                facecolor='yellow', 
                edgecolor='orange', 
                linewidth=0.5,
                alpha=0.9
            )
            axes.add_collection(react_collection)

        """Dibujar el contorno de la probeta"""
        if self.params.x and self.params.y:
            probeta = plt.Rectangle((0, 0), self.params.x, self.params.y, color='black', fill=False, linewidth=2)
            axes.add_patch(probeta)
            axes.autoscale_view()

        """Convertir figura a QPixmap de alta resolución"""
        canvas = FigureCanvas(figure)
        buf = io.BytesIO()
        canvas.print_figure(buf, format='png', dpi=600, bbox_inches='tight')
        buf.seek(0)
        self.pixmap = QPixmap()
        self.pixmap.loadFromData(buf.read())

        """Emitir señales

        Importante: primero enviamos las listas de geometrías y después la imagen.
        Así, cuando la UI habilita "Exportar" al recibir la imagen, los datos
        de exportación ya pertenecen a la estructura recién renderizada.
        """
        self.pore_list.emit(self.lista_poros_data)  # Coordinate data for export
        self.coarse_list.emit(self.todos_aridos_gruesos)
        self.fine_list.emit(self.todos_aridos_finos)
        self.reactive_list.emit(self.lista_ptos_react)
        self.imagen.emit(self.pixmap)
        self.finished.emit()

    def simular(self):
        try:
            self.information.emit("Empieza la simulación...")
            self.information.emit(f"¿Todo correcto? {self.todo_correcto}")

            if not self.todo_correcto:
                self.information_error.emit("--error grave")
                self.finished.emit()
                return

            # Paso 1: dosificación
            if self._stop: return
            self.dosificacion_sin_extrafinos()
            self.progreso.emit(5)

            # Paso 2: cálculo de áreas
            if self._stop: return
            self.calcular_areas_aridos_sin_extrafinos()
            self.progreso.emit(10)

            # Paso 3: aridos gruesos por área
            if self._stop: return
            self.calcular_aridos_por_area_gruesos()
            self.progreso.emit(20)

            # Paso 4: aridos finos por área
            if self._stop: return
            self.calcular_aridos_por_area_finos()
            self.progreso.emit(30)

            # Paso 5: colocar áridos (fino + grueso)
            if self._stop: return
            self.colocar_aridos_poligonales()
            self.progreso.emit(50)

            # Paso 6: poros (opcional)
            if self.check_poros:
                if self._stop: return
                self.calcular_poros()
                self.colocar_poros()
                self.progreso.emit(65)

            # Paso 7: puntos reactivos (opcional)
            if self.check_puntos:
                if self._stop: return
                self.calcular_puntos_sin_extrafinos()
                self.colocar_puntos_sin_extrafinos()
                self.progreso.emit(80)

            # Paso 8: ploteo (si lo usas dentro del Worker)
            if not self._stop:
                self.plotear_resultados()
                self.progreso.emit(95)

            # Emitir datos en el formato esperado por la UI/exportación
            # - poros y puntos reactivos: [x, y, r]
            # - áridos: geometrías poligonales Shapely colocadas
            self.pore_list.emit(getattr(self, "lista_poros_data", []))
            self.coarse_list.emit(getattr(self, "todos_aridos_gruesos", []))
            self.fine_list.emit(getattr(self, "todos_aridos_finos", []))
            self.reactive_list.emit(getattr(self, "lista_ptos_react", []))

            self.information.emit("Simulación finalizada correctamente.")
            self.progreso.emit(100)

        except SimulationStopped:
            self.information.emit("Simulación parada por el usuario.")
        except Exception as e:
            self.information_error.emit(f"Error en simular(): {e}")

        finally:
            self.finished.emit()
