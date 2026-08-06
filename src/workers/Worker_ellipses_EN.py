
from worker_base_EN import WorkerBase, SimParams, SimulationStopped
import io
import numpy as np
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtGui import QPixmap, QImage
from matplotlib import pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.collections import PatchCollection
from shapely.geometry import Point, box
from shapely import affinity
from matplotlib.patches import Polygon as MplPolygon
import random
from opensimplex import OpenSimplex


class WorkerElipses(WorkerBase):

    def __init__(self, params: SimParams, todo_correcto: bool = True,
                 check_pores: bool = False, check_points: bool = False,
                 check_points_aggregates: bool = False, check_points_pasta: bool = False):

        super().__init__(params)


        # self.data = None   # variable para necesaria para save/open proyectos

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
        self.list_pores = []
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

    """Distance functions refactored.
    Vectorized with arrays to avoid explicit loops and compute distances in batches
    """
    def distancias(self, list, coor_x, coor_y, radio):
        if not list:
            return True

        list_np = np.array(list)
        dx = list_np[:, 0] - coor_x
        dy = list_np[:, 1] - coor_y
        distancias = np.sqrt(dx ** 2 + dy ** 2)
        radios_sumados = radio + list_np[:, 2]

        return np.all(distancias > radios_sumados)

    def distancias_aggregates_ptos(self, list, coor_x, coor_y, radio):
        """
                Return True if the new point (coor_x, coor_y, radio) intersects
                at least one aggregate in list. Supports:
                    - items [x, y, r] (circles),
                    - items [cx, cy, a, b, angle?] (ellipses, a/b semi-axes, optional angle in degrees),
                    - Shapely objects (Polygon, Geometry).
        """
        if not list:
            return False

        new = Point(coor_x, coor_y).buffer(radio, resolution=32)

        for ar in list:
            # Case: circle defined as [x, y, r]
            if isinstance(ar, (list, tuple)) and len(ar) == 3:
                try:
                    ar_circ = Point(ar[0], ar[1]).buffer(ar[2], resolution=32)
                except Exception:
                    continue
                if new.intersects(ar_circ):
                    return True

            # Case: parameterized ellipse [cx, cy, a, b, angle?]
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
                if new.intersects(elipse):
                    return True

            # Case: already a Shapely geometry
            else:
                try:
                    if new.intersects(ar):
                        return True
                except Exception:
                    continue

        return False

    def distancias_pores_ellipses(self, x, y, radio, list_ellipses):
        pore = Point(x, y).buffer(radio, resolution=64)
        return all(not elipse.intersects(pore) for elipse in list_ellipses)

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
            """Check that the pore is fully inside the domain"""
            return r < x < self.params.x - r and r < y < self.params.y - r

        def intentar_colocar_pore(x, y, r, list_existente, aggregates_puestos):
            if not dentro_de_limites(x, y, r):
                return False
            if aggregates_puestos and not self.distancias_pores_ellipses(x, y, r, self.list_aggregates):
                return False
            if list_existente and not self.distancias(list_existente, x, y, r):
                return False
            return True

        while self.radios_pores:
            self.check_stop()
            r = self.radios_pores[0]
            x = np.random.uniform(0, self.params.x)
            y = np.random.uniform(0, self.params.y)
            if intentar_colocar_pore(x, y, r, self.list_pores, self.aggregates_puestos):
                self.list_pores.append([x, y, r])
                self.todos_pores.append(plt.Circle((x, y), r, color='r'))
                self.radios_pores.pop(0)
                self.pores_puestos = True

        print(len(self.list_pores))
        print(self.A_pores)
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

        for i in range(len(sieve) - 1):  # i+1 stays within range
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

    def calcular_aggregates_por_area_coarse(self):
        """Compute aggregates for coarse fraction"""
        j = 0
        while j < len(self.Aagg_coarse):
            self.check_stop()
            num_particulas = 0
            area_c = 0
            self.Aagg_coarse[j] = self.Aagg_coarse[j] + self.A_remanente
            while self.Aagg_coarse[j] - area_c > np.pi * (self.sieve_size_buena[j + 1] / 2) ** 2:
                self.check_stop()
                d = self.sieve_size_buena[j + 1] + np.random.rand() * (self.sieve_size_buena[j] - self.sieve_size_buena[j + 1])
                b = d / 2 # minor semi-axis
                aspecto = np.random.uniform(1.0, 1.5) # random aspect ratio
                a = b * aspecto # major semi-axis
                area = np.pi * a * b
                if area + area_c < self.Aagg_coarse[j]:
                    area_c = area_c + area
                    self.radios_coarse_ellipses.append((a, b)) # store both semi-axes
                    num_particulas = num_particulas + 1
                self.A_remanente = self.Aagg_coarse[j] - area_c
            self.particulas.append(num_particulas)
            print(self.particulas)
            if j < len(self.Aagg_coarse):
                j += 1
        self.progress.emit(20)
        self.information.emit('Coarse elliptical aggregates computed by area. ' + str(self.particulas))
        print('coarse aggregate list: ' + str(self.list_aggregates_coarse))

    def calcular_aggregates_por_area_fine(self):
        """Compute aggregates for fine fraction"""
        k = len(self.Aagg_coarse)
        l = 0
        while l < len(self.Aagg_fine):
            self.check_stop()
            num_particulas = 0
            area_c = 0
            self.Aagg_fine[l] = self.Aagg_fine[l] + self.A_remanente
            while self.Aagg_fine[l] - area_c > np.pi * (self.params.sieve_size[k + 1] / 2) ** 2:
                self.check_stop()
                d = self.params.sieve_size[k + 1] + np.random.rand() * (self.params.sieve_size[k] - self.params.sieve_size[k + 1])
                b = d / 2 # minor semi-axis
                aspecto = np.random.uniform(1.0, 1.5) # random aspect ratio
                a = b * aspecto # major semi-axis
                area = np.pi * a * b
                if area + area_c < self.Aagg_fine[l]:
                    area_c = area_c + area
                    self.radios_fine_ellipses.append((a, b)) # store both semi-axes
                    num_particulas = num_particulas + 1
                self.A_remanente = self.Aagg_fine[l] - area_c
            self.particulas.append(num_particulas)
            print(self.particulas)
            if l < len(self.Aagg_fine):
                l += 1
                k += 1
                print('one fine fraction')
        self.progress.emit(22)
        self.information.emit('Fine elliptical aggregates computed by area. ' + str(self.particulas))

    def generar_elipse_shapely(self, x, y, a, b, angulo):
        circ = Point(x, y).buffer(1, resolution=64)  # Centered unit circle
        elipse = affinity.scale(circ, a, b)  # Scale to ellipse
        elipse = affinity.rotate(elipse, angulo, origin=(x, y))
        return elipse

    def colocar_aggregates_fine_y_coarse(self):
        dominio = box(0, 0, self.params.x, self.params.y)

        def limpio(geom):
            if geom is None:
                return None
            if not geom.is_valid:
                geom = geom.buffer(0)
            if geom.is_empty:
                return None
            return geom

        def colisiona_con_list(geom, list):
            return any(geom.intersects(e) for e in list)

        def colocar(list_ab, list_data, list_ellipses, progress_val, mensaje):
            intentos_maximos = 3000
            colocadas = 0

            while list_ab:
                self.check_stop()
                a, b = list_ab[0]
                colocada = False

                for _ in range(intentos_maximos):
                    self.check_stop()
                    x = np.random.uniform(0, self.params.x)
                    y = np.random.uniform(0, self.params.y)
                    angulo = np.random.uniform(0, 360)

                    candidata = self.generar_elipse_shapely(x, y, a, b, angulo)
                    candidata = limpio(candidata)
                    if candidata is None:
                        continue

                    if not dominio.contains(candidata):
                        continue
                    if colisiona_con_list(candidata, self.list_aggregates):
                        continue
                    if self.list_pores and colisiona_con_list(candidata, self.list_pores):
                        continue

                    self.list_aggregates.append(candidata)
                    list_data.append([x, y, a, b, angulo])
                    list_ellipses.append(candidata)
                    list_ab.pop(0)
                    self.aggregates_puestos = True
                    colocadas += 1
                    colocada = True
                    break

                if not colocada:
                    # Avoid infinite loops in saturated domains.
                    list_ab.pop(0)

            print(f'ellipse count: {len(self.list_aggregates)}')
            self.progress.emit(progress_val)
            self.information.emit(f'{mensaje} placed. {colocadas}')

        self.list_aggregates = []
        self.todos_aggregates_coarse = []
        self.todos_aggregates_fine = []
        self.list_aggregates_coarse = []
        self.list_aggregates_fine = []
        self.aggregates_puestos = False

        # Place coarse aggregates (ellipses)
        colocar(
            list_ab=self.radios_coarse_ellipses,
            list_data=self.list_aggregates_coarse,
            list_ellipses=self.todos_aggregates_coarse,
            progress_val=30,
            mensaje='Coarse aggregates'
        )

        # Place fine aggregates (ellipses)
        colocar(
            list_ab=self.radios_fine_ellipses,
            list_data=self.list_aggregates_fine,
            list_ellipses=self.todos_aggregates_fine,
            progress_val=32,
            mensaje='Fine aggregates'
        )

    def calcular_points_sin_extrafinos(self):
        """reactive points on coarse aggregates"""
        if self.check_points_aggregates:
            if self.params.Ppto_react_aggregates:
                self.A_points_aggregates = self.params.Ppto_react_aggregates * self.A
                while self.A_points_aggregates > np.pi * (self.params.dpto_min_aggregates / 2) ** 2:
                    self.check_stop()
                    if self.params.dpto_min_aggregates == self.params.dpto_max_aggregates:
                        rpunto = self.params.dpto_min_aggregates /2
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
        """Place reactive points on aggregates and paste, using clusters for aggregates and Simplex noise for paste."""
        def dentro_de_limites(x, y, r):
            return r < x < self.params.x - r and r < y < self.params.y - r

        def intentar_colocar_point(x, y, r, list_existente, evitar_aggregates, pores_puestos):
            if not dentro_de_limites(x, y, r):
                return False
            if pores_puestos and not self.distancias(self.list_pores, x, y, r):
                return False
            if evitar_aggregates and not self.distancias(self.list_aggregates_coarse, x, y, r):
                return False
            if not evitar_aggregates and not self.distancias_aggregates_ptos(self.list_aggregates_coarse, x, y, r):
                return False
            if len(list_existente) > 0 and not self.distancias(list_existente, x, y, r):
                return False
            return True

        def generar_centros_clusters(k_minimo, sigma=5):
            radio_influencia = 3 * sigma
            area_cluster = np.pi * radio_influencia ** 2
            num_clusters = max(k_minimo, int(np.ceil((self.params.x * self.params.y) / area_cluster)))
            return [
                (np.random.uniform(0, self.params.x), np.random.uniform(0, self.params.y))
                for _ in range(num_clusters)
            ]

        def colocar_con_clusters(list_radios, list_save, evitar_aggregates, pores_puestos, k=5, sigma=5):
            centros = generar_centros_clusters(k)
            while list_radios:
                r = list_radios[0]
                for _ in range(1000):
                    cx, cy = random.choice(centros)
                    x = np.random.normal(cx, sigma)
                    y = np.random.normal(cy, sigma)
                    if intentar_colocar_point(x, y, r, list_save, evitar_aggregates, pores_puestos):
                        list_save.append([x, y, r])
                        self.todos_ptos_react.append(plt.Circle((x, y), r, color='y'))
                        list_radios.pop(0)
                        break

        def colocar_con_simplex(list_radios, list_save, evitar_aggregates, pores_puestos, escala=0.05, umbral=0.3):
            ruido = OpenSimplex(seed=42)
            while list_radios:
                r = list_radios[0]
                for _ in range(1000):
                    x = np.random.uniform(0, self.params.x)
                    y = np.random.uniform(0, self.params.y)
                    valor = (ruido.noise2(x * escala, y * escala) + 1) / 2
                    if valor < umbral:
                        continue
                    if intentar_colocar_point(x, y, r, list_save, evitar_aggregates, pores_puestos):
                        list_save.append([x, y, r])
                        self.todos_ptos_react.append(plt.Circle((x, y), r, color='y'))
                        list_radios.pop(0)
                        break

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
            specimen_rect = plt.Rectangle((0, 0), self.params.x, self.params.y, color='black', fill=False, linewidth=2)
            axes.add_patch(specimen_rect)
            axes.autoscale_view()

        """Convert figure to high-resolution QPixmap"""
        canvas = FigureCanvas(figure)
        buf = io.BytesIO()
        canvas.print_figure(buf, format='png', dpi=600, bbox_inches='tight')
        buf.seek(0)
        self.pixmap = QPixmap()
        self.pixmap.loadFromData(buf.read())

        """Emit signals

        First emit lists and then image to avoid exporting stale data.
        """
        self.pore_list.emit(self.list_pores)
        self.coarse_list.emit(self.list_aggregates_coarse)
        self.fine_list.emit(self.list_aggregates_fine)
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
            self.colocar_aggregates_fine_y_coarse()
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

            # Emit final lists when finished
            # (adjust names to your internal naming)
            self.pore_list.emit(getattr(self, "list_pores", []))
            self.coarse_list.emit(getattr(self, "list_aggregates_coarse", []))
            self.fine_list.emit(getattr(self, "list_aggregates_fine", []))
            self.reactive_list.emit(getattr(self, "list_ptos_react", []))

            self.information.emit("Simulation completed successfully.")
            self.progress.emit(100)

        except SimulationStopped:
            self.information.emit("Simulation stopped by user.")
        except Exception as e:
            self.information_error.emit(f"Error in simulate(): {e}")

        finally:
            self.finished.emit()

