
from worker_base_EN import WorkerBase, SimParams, SimulationStopped
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
import random
from opensimplex import OpenSimplex


class WorkerPoligonos(WorkerBase):

    def __init__(self, params: SimParams, todo_correcto: bool = True,
                 check_pores: bool = False, check_points: bool = False,
                 check_points_aggregates: bool = False, check_points_pasta: bool = False):

        super().__init__(params)


        self.data = None   # variable para necesaria para save/open proyectos

        """"
        Required variables
        """
        self.A = None
        self.Aagg = []
        self.A_remanente = 0
        self.num_particulas = 0
        self.particulas = []
        self.radios = []
        self.list_aggregates = []
        self.todos_aggregates = []
        self.radios_pores = []
        self.todos_pores = []
        self.list_pores = []  # Shapely geometries for collision detection
        self.list_pores_data = []  # [x, y, r] tuples for export
        self.list_ptos_react = []
        self.list_ptos_react_aggregates = []
        self.list_ptos_react_pasta = []
        self.todos_ptos_react = []

        self.radios_points = []
        self.radios_points_aggregates = []
        self.radios_points_pasta = []

        self.sieve_size_buena = []
        self.list_aggregates_coarse = []
        self.list_aggregates_fine = []
        self.Aagg_coarse = []
        self.Aagg_fine = []
        # self.radios_coarse_ellipses = []
        self.radios_coarse_ellipses = []
        # self.radios_fine_ellipses = []
        self.radios_fine_ellipses = []
        self.todos_aggregates_coarse = []
        self.todos_aggregates_fine = []

        self.aggregates_puestos = False
        self.pores_puestos = False
        self.A_pores = None
        self.A_points_aggregates = None
        self.A_points_pasta = None
        self.existe_structure = False

        self.todo_correcto = todo_correcto

        self.check_pores = check_pores
        self.check_points = check_points
        self.check_points_aggregates = check_points_aggregates
        self.check_points_pasta = check_points_pasta

    """Distance helpers.

    Vectorized and geometry-based checks to avoid explicit nested loops.
    """

    def distancias(self, list_geometrias, x, y, r):
        new_circulo = Point(x, y).buffer(r)
        resultado = []
        for g in list_geometrias:
            if isinstance(g, Polygon):
                resultado.append(not new_circulo.intersects(g))
            elif isinstance(g, list) and len(g) == 3:
                resultado.append(not new_circulo.intersects(Point(g[0], g[1]).buffer(g[2])))
            else:
                raise TypeError(f"Invalid element in geometry list: {g}")
        return all(resultado)

    def distancias_aggregates_ptos(self, list_aggregates, x, y, r):
        """Check whether a new circle intersects at least one aggregate.

        Soporta:
          - circles [x, y, r]
          - ellipses [cx, cy, a, b, angle?]
                    - Shapely geometries (Polygon, Geometry)
        """
        if not list_aggregates:
            return False

        new_circulo = Point(x, y).buffer(r, resolution=32)
        for ar in list_aggregates:
            if isinstance(ar, (list, tuple)) and len(ar) == 3:
                try:
                    ar_circ = Point(ar[0], ar[1]).buffer(ar[2], resolution=32)
                except Exception:
                    continue
                if new_circulo.intersects(ar_circ):
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
                if new_circulo.intersects(elipse):
                    return True
            else:
                try:
                    if new_circulo.intersects(ar):
                        return True
                except Exception:
                    continue
        return False

    def distancias_pores_aggregates(self, x, y, r, list_aggregates):
        """Check that a pore does not intersect any polygonal aggregate."""
        pore = Point(x, y).buffer(r)
        return all(not pore.intersects(aggregate) for aggregate in list_aggregates)

    def calcular_pores(self):
        if self.check_pores:
            self.A_pores = self.A * self.params.Pporos
            while self.A_pores > np.pi * (self.params.dporo_min / 2) ** 2:
                self.check_stop()
                rporo = (self.params.dporo_min + np.random.random() * (self.params.dporo_max - self.params.dporo_min)) / 2
                Aporo = np.pi * (rporo) ** 2
                self.A_pores = self.A_pores - Aporo
                self.radios_pores.append(rporo)
            self.progress.emit(40)
            self.information.emit('Pores computed. ' + str(len(self.radios_pores)) + ' Pores')

    def colocar_pores(self):
        def dentro_de_limites(x, y, r):
            return r < x < self.params.x - r and r < y < self.params.y - r

        def intersecta_con_algo(geom, geoms):
            for g in geoms:
                if geom.intersects(g):
                    return True
            return False

        intentos_maximos = 3000
        while self.radios_pores:
            self.check_stop()
            r = self.radios_pores.pop(0)
            colocado = False

            for _ in range(intentos_maximos):
                x = np.random.uniform(0, self.params.x)
                y = np.random.uniform(0, self.params.y)
                if not dentro_de_limites(x, y, r):
                    continue

                pore = Point(x, y).buffer(r, resolution=64)
                if self.aggregates_puestos and intersecta_con_algo(pore, self.list_aggregates):
                    continue
                if intersecta_con_algo(pore, self.list_pores):
                    continue

                self.list_pores.append(pore)
                self.list_pores_data.append([x, y, r])
                self.todos_pores.append(Circle((x, y), r, color='r'))
                self.pores_puestos = True
                colocado = True
                break

            if not colocado:
                print(f"Could not place a pore with radius {r:.3f} after {intentos_maximos} attempts.")

        print(f"Pores placed: {len(self.list_pores)}")
        self.progress.emit(50)
        self.information.emit('Pores placed')

    """
    Check whether there are aggregate sizes smaller than 2 and remove them
    """
    def gradation_sin_extrafinos(self):
        print('sieve_size: ' + str(self.params.sieve_size))
        print('filtered sieve_size: ' + str(self.sieve_size_buena))
        n = 0
        while self.params.sieve_size[n] >= 2:
            self.sieve_size_buena.append(self.params.sieve_size[n])
            n = n + 1
            # return self.sieve_size_buena
        self.information.emit('Removed ultra-fine fraction from gradation.')
        self.progress.emit(15)
        print('filtered gradation: ' + str(self.sieve_size_buena))

    def calcular_areas_aggregates_sin_extrafinos(self):
        self.A = float(self.params.x) * float(self.params.y)
        self.Aagg = []

        # Ensure sieve sizes and TPP are float values
        sieve = [float(s) for s in self.sieve_size_buena]
        tpp = [float(p) for p in self.params.tpp]

        for i in range(len(sieve) - 1):  # i+1 always stays in range
            fraccion = (tpp[i] - tpp[i + 1]) / (tpp[0] - tpp[-1])
            area_intervalo = fraccion * self.params.Pagg * self.A
            self.Aagg.append(area_intervalo)  # Do not round here

        print([round(a, 2) for a in self.Aagg])
        print('areas computed')

        self.progress.emit(10)
        self.information.emit(
            'Computed area for each aggregate fraction. ' +
            str([round(a, 2) for a in self.Aagg])
        )
        print('status emitted')

        # Classification into coarse (>4 mm) and fine (<=4 mm) using float values
        self.Aagg_coarse = []
        self.Aagg_fine = []

        for tam, area in zip(sieve[:-1], self.Aagg):  # Last sieve has no associated area
            if tam > 4.0:
                self.Aagg_coarse.append(area)
            else:
                self.Aagg_fine.append(area)

        print('Aagg: ' + str([round(a, 2) for a in self.Aagg]))
        print('coarse Aagg: ' + str([round(a, 2) for a in self.Aagg_coarse]))
        print('fine Aagg: ' + str([round(a, 2) for a in self.Aagg_fine]))

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

    def calcular_aggregates_por_area_coarse(self):
        self.poligonos_coarse = []
        j = 0
        while j < len(self.Aagg_coarse):
            num_particulas = 0
            area_c = 0
            if j + 1 >= len(self.sieve_size_buena):
                print(f"Index out of range in filtered sieve_size: j={j}")
                break
            self.Aagg_coarse[j] += self.A_remanente
            while self.Aagg_coarse[j] - area_c > 0.0001:
                d = self.sieve_size_buena[j + 1] + np.random.rand() * (
                        self.sieve_size_buena[j] - self.sieve_size_buena[j + 1])
                area_max = np.pi * (d / 2) ** 2
                resultado = self.generar_poligono_irregular(area_max * np.random.uniform(0.5, 1.0))
                if resultado is None:
                    print(f"Could not generate a valid polygon at j={j}")
                    break
                # poligono, area = resultado
                coordenadas, area = resultado
                if area + area_c < self.Aagg_coarse[j]:
                    area_c += area
                    poligono = Polygon(coordenadas)
                    if not poligono.is_valid:
                        poligono = poligono.buffer(0)
                    self.poligonos_coarse.append(poligono)
                    num_particulas += 1
                else:
                    break
            self.A_remanente = self.Aagg_coarse[j] - area_c
            self.particulas.append(num_particulas)
            j += 1
        self.progress.emit(20)
        self.information.emit('Coarse polygonal aggregates computed by area. ' + str(self.particulas))
        print('coarse aggregate metadata list: ' + str(self.list_aggregates_coarse))

    def calcular_aggregates_por_area_fine(self):
        self.poligonos_fine = []
        k = len(self.Aagg_coarse)
        l = 0
        while l < len(self.Aagg_fine):
            num_particulas = 0
            area_c = 0
            if k + 1 >= len(self.params.sieve_size):
                print(f"Index out of range in sieve_size: k={k}")
                break
            self.Aagg_fine[l] += self.A_remanente
            while self.Aagg_fine[l] - area_c > 0.0001:
                d = self.params.sieve_size[k + 1] + np.random.rand() * (
                        self.params.sieve_size[k] - self.params.sieve_size[k + 1])
                area_max = np.pi * (d / 2) ** 2
                resultado = self.generar_poligono_irregular(area_max * np.random.uniform(0.5, 1.0))
                if resultado is None:
                    print(f"Could not generate a valid polygon at l={l}")
                    break
                # poligono, area = resultado
                coordenadas, area = resultado
                if area + area_c < self.Aagg_fine[l]:
                    area_c += area
                    poligono = Polygon(coordenadas)
                    if not poligono.is_valid:
                        poligono = poligono.buffer(0)
                    self.poligonos_fine.append(poligono)
                    num_particulas += 1
                else:
                    break
            self.A_remanente = self.Aagg_fine[l] - area_c
            self.particulas.append(num_particulas)
            l += 1
            k += 1
        self.progress.emit(22)
        self.information.emit('Fine polygonal aggregates computed by area. ' + str(self.particulas))

    def colocar_aggregates_poligonales(self):
        dominio = box(0, 0, self.params.x, self.params.y)

        def limpio(poly):
            if poly is None:
                return None
            if not poly.is_valid:
                poly = poly.buffer(0)
            if poly.is_empty:
                return None
            return poly

        def colocar(list_fuente, list_data, list_destino, progress, mensaje):
            intentos_maximos = 3000
            colocados = 0

            for base in list_fuente:
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
                    if any(candidato.intersects(g) for g in self.list_aggregates):
                        continue
                    if any(candidato.intersects(p) for p in self.list_pores):
                        continue

                    self.list_aggregates.append(candidato)
                    list_destino.append(candidato)
                    list_data.append([x, y, angulo])
                    self.aggregates_puestos = True
                    colocados += 1
                    break

            self.progress.emit(progress)
            self.information.emit(f'{mensaje} placed. {colocados}')

        self.list_aggregates = []
        self.todos_aggregates_coarse = []
        self.todos_aggregates_fine = []
        self.list_aggregates_coarse = []
        self.list_aggregates_fine = []
        self.aggregates_puestos = False

        colocar(self.poligonos_coarse, self.list_aggregates_coarse, self.todos_aggregates_coarse, 30, 'Coarse aggregates')
        colocar(self.poligonos_fine, self.list_aggregates_fine, self.todos_aggregates_fine, 32, 'Fine aggregates')

    def calcular_points_sin_extrafinos(self):
        """reactive points on coarse aggregates"""
        if self.check_points_aggregates:
            if self.params.Ppto_react_aggregates:
                self.A_points_aggregates = self.params.Ppto_react_aggregates * self.A
                while self.A_points_aggregates > np.pi * (self.params.dpto_min_aggregates / 2) ** 2:
                    self.check_stop()
                    if self.params.dpto_min_aggregates == self.params.dpto_max_aggregates:
                        rpunto = self.params.dpto_min_aggregates / 2
                    else:
                        rpunto = (self.params.dpto_min_aggregates + np.random.random() *
                                  (self.params.dpto_max_aggregates - self.params.dpto_min_aggregates)) / 2
                    Apunto = np.pi * (rpunto) ** 2
                    self.A_points_aggregates = self.A_points_aggregates - Apunto
                    self.radios_points.append(rpunto)  # Keep a global point-radius trace.
                    self.radios_points_aggregates.append(rpunto)
            self.progress.emit(55)
            self.information.emit('Reactive points on aggregates computed')

        """reactive points on fine fraction (and paste)"""
        if self.check_points_pasta:
            if self.params.Ppto_react_pasta:
                self.A_points_pasta = self.params.Ppto_react_pasta * self.A
                while self.A_points_pasta > np.pi * (self.params.dpto_min_pasta / 2) ** 2:
                    self.check_stop()
                    if self.params.dpto_min_pasta == self.params.dpto_max_pasta:
                        rpunto = self.params.dpto_min_pasta / 2
                    else:
                        rpunto = (self.params.dpto_min_pasta + np.random.random() * (
                                self.params.dpto_max_pasta - self.params.dpto_min_pasta)) / 2
                    Apunto = np.pi * (rpunto) ** 2
                    self.A_points_pasta = self.A_points_pasta - Apunto
                    self.radios_points.append(rpunto)  # Keep a global point-radius trace.
                    self.radios_points_pasta.append(rpunto)
            self.progress.emit(60)
            self.information.emit('Reactive points in paste computed')

    def colocar_points_sin_extrafinos(self):
        """Coloca los points reactive sobre los aggregates y la pasta."""
        def dentro_de_limites(x, y, r):
            return r < x < self.params.x - r and r < y < self.params.y - r

        def intentar_colocar_point(x, y, r, list_existente, evitar_aggregates, pores_puestos):
            if not dentro_de_limites(x, y, r):
                return False
            if pores_puestos and not self.distancias(self.list_pores, x, y, r):
                return False
            if evitar_aggregates and not self.distancias(self.list_aggregates, x, y, r):
                return False
            if not evitar_aggregates and not self.distancias_aggregates_ptos(self.list_aggregates, x, y, r):
                return False
            if len(list_existente) > 0 and not self.distancias(list_existente, x, y, r):
                return False
            return True

        def colocar_list(list_radios, list_save, evitar_aggregates, pores_puestos, max_intentos=1000):
            while list_radios:
                self.check_stop()
                r = list_radios[0]
                colocado = False
                for _ in range(max_intentos):
                    x = np.random.uniform(0, self.params.x)
                    y = np.random.uniform(0, self.params.y)
                    if intentar_colocar_point(x, y, r, list_save, evitar_aggregates, pores_puestos):
                        list_save.append([x, y, r])
                        self.todos_ptos_react.append(plt.Circle((x, y), r, color='y'))
                        list_radios.pop(0)
                        colocado = True
                        break
                if not colocado:
                    print(f"Warning: could not place point with radius {r:.3f} after {max_intentos} attempts.")
                    list_radios.pop(0)

        def generar_centros_clusters(k_minimo, sigma=5):
            radio_influencia = 3 * sigma
            area_cluster = np.pi * radio_influencia ** 2
            num_clusters = max(k_minimo, int(np.ceil((self.params.x * self.params.y) / area_cluster)))
            return [
                (np.random.uniform(0, self.params.x), np.random.uniform(0, self.params.y))
                for _ in range(num_clusters)
            ]

        def colocar_con_clusters(list_radios, list_save, evitar_aggregates, pores_puestos, k=5, sigma=5, max_intentos=1000):
            centros = generar_centros_clusters(k)
            while list_radios:
                self.check_stop()
                r = list_radios[0]
                colocado = False
                for _ in range(max_intentos):
                    self.check_stop()
                    cx, cy = random.choice(centros)
                    x = np.random.normal(cx, sigma)
                    y = np.random.normal(cy, sigma)
                    if intentar_colocar_point(x, y, r, list_save, evitar_aggregates, pores_puestos):
                        list_save.append([x, y, r])
                        self.todos_ptos_react.append(plt.Circle((x, y), r, color='y'))
                        list_radios.pop(0)
                        colocado = True
                        break
                if not colocado:
                    print(f"Warning: could not place point with radius {r:.3f} after {max_intentos} attempts (clusters).")
                    list_radios.pop(0)

        def colocar_con_simplex(list_radios, list_save, evitar_aggregates, pores_puestos, escala=0.05, umbral=0.3, max_intentos=1000):
            ruido = OpenSimplex(seed=42)
            while list_radios:
                self.check_stop()
                r = list_radios[0]
                colocado = False
                for _ in range(max_intentos):
                    self.check_stop()
                    x = np.random.uniform(0, self.params.x)
                    y = np.random.uniform(0, self.params.y)
                    valor = (ruido.noise2(x * escala, y * escala) + 1) / 2
                    if valor < umbral:
                        continue
                    if intentar_colocar_point(x, y, r, list_save, evitar_aggregates, pores_puestos):
                        list_save.append([x, y, r])
                        self.todos_ptos_react.append(plt.Circle((x, y), r, color='y'))
                        list_radios.pop(0)
                        colocado = True
                        break
                if not colocado:
                    print(f"Warning: could not place point with radius {r:.3f} after {max_intentos} attempts (simplex).")
                    list_radios.pop(0)

        # Place points on aggregates using clusters
        if self.check_points_aggregates:
            colocar_con_clusters(self.radios_points_aggregates, self.list_ptos_react_aggregates,
                                 evitar_aggregates=False, pores_puestos=self.pores_puestos)
            self.progress.emit(65)
            self.information.emit('Reactive points on aggregates placed')

        # Place points in paste using Simplex noise
        if self.check_points_pasta:
            colocar_con_simplex(self.radios_points_pasta, self.list_ptos_react_pasta,
                                evitar_aggregates=True, pores_puestos=self.pores_puestos)
            self.progress.emit(70)
            self.information.emit('Reactive points in paste placed')

        self.list_ptos_react = self.list_ptos_react_aggregates + self.list_ptos_react_pasta

    def plotear_resultados(self):
        figure, axes = plt.subplots(dpi=200)
        plt.axis("equal")
        axes.set_xlim(0, self.params.x)
        axes.set_ylim(0, self.params.y)

        """Convert Shapely polygons to matplotlib patches"""

        def shapely_to_patch(polygon):
            return MplPolygon(list(polygon.exterior.coords), closed=True)

        """Add patch collections"""
        if self.todos_pores:
            print('pores count: ' + str(len(self.todos_pores)))
            pores_collection = PatchCollection(self.todos_pores, color='red', edgecolor='none')
            axes.add_collection(pores_collection)

        if self.todos_aggregates_coarse:
            patches_coarse = [shapely_to_patch(e) for e in self.todos_aggregates_coarse]
            aggregates_collection = PatchCollection(
                patches_coarse, 
                facecolor='lightblue', 
                edgecolor='blue', 
                linewidth=0.5,
                antialiased=True,
                alpha=0.8
            )
            axes.add_collection(aggregates_collection)

        if self.todos_aggregates_fine:
            patches_fine = [shapely_to_patch(e) for e in self.todos_aggregates_fine]
            aggregates_collection = PatchCollection(
                patches_fine, 
                facecolor='lightcyan', 
                edgecolor='darkblue', 
                linewidth=0.3,
                antialiased=True,
                alpha=0.6
            )
            axes.add_collection(aggregates_collection)

        if self.todos_ptos_react:
            react_collection = PatchCollection(
                self.todos_ptos_react, 
                facecolor='yellow', 
                edgecolor='orange', 
                linewidth=0.5,
                alpha=0.9
            )
            axes.add_collection(react_collection)

        """Draw specimen boundary"""
        if self.params.x and self.params.y:
            probeta = plt.Rectangle((0, 0), self.params.x, self.params.y, color='black', fill=False, linewidth=2)
            axes.add_patch(probeta)
            axes.autoscale_view()

        """Convert figure to high-resolution QPixmap"""
        canvas = FigureCanvas(figure)
        buf = io.BytesIO()
        canvas.print_figure(buf, format='png', dpi=600, bbox_inches='tight')
        buf.seek(0)
        self.pixmap = QPixmap()
        self.pixmap.loadFromData(buf.read())

        """Emit signals

        Important: first emit geometry lists, then the image.
        This ensures that when the UI enables export after receiving the image, the data
        already belong to the freshly rendered structure.
        """
        self.pore_list.emit(self.list_pores_data)  # Coordinate data for export
        self.coarse_list.emit(self.todos_aggregates_coarse)
        self.fine_list.emit(self.todos_aggregates_fine)
        self.reactive_list.emit(self.list_ptos_react)
        self.image.emit(self.pixmap)
        self.finished.emit()

    def simulate(self):
        try:
            self.information.emit("Simulation started...")
            self.information.emit(f"All inputs valid? {self.todo_correcto}")

            if not self.todo_correcto:
                self.information_error.emit("--critical error")
                self.finished.emit()
                return

            # Step 1: gradation
            if self._stop: return
            self.gradation_sin_extrafinos()
            self.progress.emit(5)

            # Step 2: area calculation
            if self._stop: return
            self.calcular_areas_aggregates_sin_extrafinos()
            self.progress.emit(10)

            # Step 3: coarse aggregates by area
            if self._stop: return
            self.calcular_aggregates_por_area_coarse()
            self.progress.emit(20)

            # Step 4: fine aggregates by area
            if self._stop: return
            self.calcular_aggregates_por_area_fine()
            self.progress.emit(30)

            # Step 5: place aggregates (fine + coarse)
            if self._stop: return
            self.colocar_aggregates_poligonales()
            self.progress.emit(50)

            # Step 6: pores (optional)
            if self.check_pores:
                if self._stop: return
                self.calcular_pores()
                self.colocar_pores()
                self.progress.emit(65)

            # Step 7: reactive points (optional)
            if self.check_points:
                if self._stop: return
                self.calcular_points_sin_extrafinos()
                self.colocar_points_sin_extrafinos()
                self.progress.emit(80)

            # Step 8: plotting (if used inside the worker)
            if not self._stop:
                self.plotear_resultados()
                self.progress.emit(95)

            # Emit data in the format expected by UI/export
            # - pores and reactive points: [x, y, r]
            # - aggregates: placed Shapely polygon geometries
            self.pore_list.emit(getattr(self, "list_pores_data", []))
            self.coarse_list.emit(getattr(self, "todos_aggregates_coarse", []))
            self.fine_list.emit(getattr(self, "todos_aggregates_fine", []))
            self.reactive_list.emit(getattr(self, "list_ptos_react", []))

            self.information.emit("Simulation completed successfully.")
            self.progress.emit(100)

        except SimulationStopped:
            self.information.emit("Simulation stopped by user.")
        except Exception as e:
            self.information_error.emit(f"Error in simulate(): {e}")

        finally:
            self.finished.emit()

