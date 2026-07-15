
from worker_base import WorkerBase, SimParams, SimulationStopped
import io
import numpy as np
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtGui import QPixmap, QImage
from matplotlib import pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.collections import PatchCollection
import random
from opensimplex import OpenSimplex


class WorkerTodos(WorkerBase):

    def __init__(self, params: SimParams, todo_correcto: bool = True,
                 check_poros: bool = False, check_puntos: bool = False,
                 check_puntos_aridos: bool = False, check_puntos_pasta: bool = False):

        super().__init__(params)

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
        self.lista_poros = []
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
        self.radios_gruesos = []
        self.radios_finos = []
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

    """refactorizadas las funciones para el cálculo de las distancias
    vectorizadas con arrays para evitar bucles explícitos y calculando las distancias en bloque
    """
    def distancias(self, lista, coor_x, coor_y, radio):
        """Devuelve True si no hay solapamiento con los elementos de la lista."""
        if not lista:
            return True

        lista_np = np.array(lista)
        dx = lista_np[:, 0] - coor_x
        dy = lista_np[:, 1] - coor_y
        distancias = np.sqrt(dx ** 2 + dy ** 2)
        radios_sumados = radio + lista_np[:, 2]

        return np.all(distancias > radios_sumados)

    def distancias_aridos_ptos(self, lista, coor_x, coor_y, radio):
        if not lista:
            return False  # No hay solapamiento si no hay elementos

        lista_np = np.array(lista)  # Asume que cada n es [x, y, r]
        dx = lista_np[:, 0] - coor_x
        dy = lista_np[:, 1] - coor_y
        distancias = np.sqrt(dx ** 2 + dy ** 2)
        radios_sumados = radio + lista_np[:, 2]

        return np.any(distancias < radios_sumados)

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
            """Verifica que el poro esté completamente dentro del dominio"""
            return r < x < self.params.x - r and r < y < self.params.y - r

        def intentar_colocar_poro(x, y, r, lista_existente, aridos_puestos):
            if not dentro_de_limites(x, y, r):
                return False
            if aridos_puestos and not self.distancias(self.lista_aridos, x, y, r):
                return False
            if lista_existente and not self.distancias(lista_existente, x, y, r):
                return False
            return True

        while self.radios_poros:
            self.check_stop()
            r = self.radios_poros[0]
            x = np.random.uniform(0, self.params.x)
            y = np.random.uniform(0, self.params.y)
            if intentar_colocar_poro(x, y, r, self.lista_poros, self.aridos_puestos):
                self.lista_poros.append([x, y, r])
                self.todos_poros.append(plt.Circle((x, y), r, color='r'))
                self.radios_poros.pop(0)
                self.poros_puestos = True

        print(len(self.lista_poros))
        print(self.A_poros)
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

    def calcular_aridos_por_area_gruesos(self):
        """Calcular los áridos por fracción gruesa"""
        j = 0
        while j < len(self.Aagg_gruesos):
            self.check_stop()
            num_particulas = 0
            area_c = 0
            self.Aagg_gruesos[j] = self.Aagg_gruesos[j] + self.A_remanente
            while self.Aagg_gruesos[j] - area_c > np.pi * (self.sieve_size_buena[j + 1] / 2) ** 2:
                self.check_stop()
                d = self.sieve_size_buena[j + 1] + np.random.rand() * (self.sieve_size_buena[j] - self.sieve_size_buena[j + 1])
                area = np.pi * (d / 2) ** 2
                if area + area_c < self.Aagg_gruesos[j]:
                    area_c = area_c + area
                    self.radios_gruesos.append(d / 2)
                    num_particulas = num_particulas + 1
                self.A_remanente = self.Aagg_gruesos[j] - area_c
            self.particulas.append(num_particulas)
            print(self.particulas)
            if j < len(self.Aagg_gruesos):
                j += 1
        self.progreso.emit(20)
        self.information.emit('Áridos gruesos por área calculados. ' + str(self.particulas))

    def calcular_aridos_por_area_finos(self):
        """Calcular los áridos por fracción fina"""
        k = len(self.Aagg_gruesos)
        l = 0
        while l < len(self.Aagg_finos):
            self.check_stop()
            num_particulas = 0
            area_c = 0
            self.Aagg_finos[l] = self.Aagg_finos[l] + self.A_remanente
            while self.Aagg_finos[l] - area_c > np.pi * (self.params.sieve_size[k + 1] / 2) ** 2:
                self.check_stop()
                d = self.params.sieve_size[k + 1] + np.random.rand() * (self.params.sieve_size[k] - self.params.sieve_size[k + 1])
                area = np.pi * (d / 2) ** 2
                if area + area_c < self.Aagg_finos[l]:
                    area_c = area_c + area
                    self.radios_finos.append(d / 2)
                    num_particulas = num_particulas + 1
                self.A_remanente = self.Aagg_finos[l] - area_c
            self.particulas.append(num_particulas)
            print(self.particulas)
            if l < len(self.Aagg_finos):
                l += 1
                k += 1
                print('un fino')
        self.progreso.emit(22)
        self.information.emit('Áridos finos por área calculados. ' + str(self.particulas))

    def colocar_aridos_finos_y_gruesos(self):
        def dentro_de_limites(x, y, r):
            """Verifica que el árido esté completamente dentro del dominio"""
            return r < x < self.params.x - r and r < y < self.params.y - r

        def intentar_colocar_arido(x, y, r, lista_existente, poros_puestos):
            if not dentro_de_limites(x, y, r):
                return False
            if poros_puestos and not self.distancias(self.lista_poros, x, y, r):
                return False
            if lista_existente and not self.distancias(lista_existente, x, y, r):
                return False
            return True

        def colocar(lista_radios, lista_datos, lista_circulos, progreso_val, mensaje):
            while lista_radios:
                self.check_stop()
                r = lista_radios[0]
                x = np.random.uniform(0, self.params.x)
                y = np.random.uniform(0, self.params.y)
                if intentar_colocar_arido(x, y, r, self.lista_aridos, self.poros_puestos):
                    dato = [x, y, r]
                    self.lista_aridos.append(dato)
                    lista_datos.append(dato)
                    circulo = plt.Circle((x, y), r)
                    self.todos_aridos.append(circulo)
                    lista_circulos.append(circulo)
                    lista_radios.pop(0)
                    self.aridos_puestos = True

            print(f'tengo tantos áridos: {len(self.lista_aridos)}')
            print(len(self.todos_aridos))
            print(f'Radios restantes: {len(lista_radios)}')
            self.progreso.emit(progreso_val)
            self.information.emit(f'{mensaje} colocados. {len(lista_datos)}')

        # Colocar áridos gruesos
        colocar(
            lista_radios=self.radios_gruesos,
            lista_datos=self.lista_aridos_gruesos,
            lista_circulos=self.todos_aridos_gruesos,
            
            progreso_val=30,
            mensaje='Áridos gruesos'
        )

        # Colocar áridos finos
        colocar(
            lista_radios=self.radios_finos,
            lista_datos=self.lista_aridos_finos,
            lista_circulos=self.todos_aridos_finos,
            
            progreso_val=32,
            mensaje='Áridos finos'
        )

    def calcular_puntos_sin_extrafinos(self):
        """puntos sobre áridos gruesos"""
        if self.check_puntos_aridos:
            if self.params.Ppto_react_aridos:
                self.A_puntos_aridos = self.params.Ppto_react_aridos * self.A
                while self.A_puntos_aridos > np.pi * (self.params.dpto_min_aridos / 2) ** 2:
                    self.check_stop()
                    if self.params.dpto_min_aridos == self.params.dpto_max_aridos:
                        rpunto = self.params.dpto_min_aridos /2
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
        """Coloca los puntos reactivos sobre los áridos y la pasta, utilizando clusters para los áridos y ruido Simplex para la pasta."""
        def dentro_de_limites(x, y, r):
            return r < x < self.params.x - r and r < y < self.params.y - r

        def intentar_colocar_punto(x, y, r, lista_existente, evitar_aridos, poros_puestos):
            if not dentro_de_limites(x, y, r):
                return False
            if poros_puestos and not self.distancias(self.lista_poros, x, y, r):
                return False
            if evitar_aridos and not self.distancias(self.lista_aridos_gruesos, x, y, r):
                return False
            if not evitar_aridos and not self.distancias_aridos_ptos(self.lista_aridos_gruesos, x, y, r):
                return False
            if len(lista_existente) > 0 and not self.distancias(lista_existente, x, y, r):
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

        def colocar_con_clusters(lista_radios, lista_guardar, evitar_aridos, poros_puestos, k=5, sigma=5):
            centros = generar_centros_clusters(k)
            while lista_radios:
                self.check_stop()
                r = lista_radios[0]
                for _ in range(1000):
                    self.check_stop()
                    cx, cy = random.choice(centros)
                    x = np.random.normal(cx, sigma)
                    y = np.random.normal(cy, sigma)
                    if intentar_colocar_punto(x, y, r, lista_guardar, evitar_aridos, poros_puestos):
                        lista_guardar.append([x, y, r])
                        self.todos_ptos_react.append(plt.Circle((x, y), r, color='y'))
                        lista_radios.pop(0)
                        break

        def colocar_con_simplex(lista_radios, lista_guardar, evitar_aridos, poros_puestos, escala=0.05, umbral=0.3):
            ruido = OpenSimplex(seed=42)
            while lista_radios:
                self.check_stop()
                r = lista_radios[0]
                for _ in range(1000):
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
                        break

        # Colocar puntos sobre áridos con clusters
        if self.check_puntos_aridos:
            colocar_con_clusters(self.radios_puntos_aridos, self.lista_ptos_react_aridos,
                                 evitar_aridos=False, poros_puestos=self.poros_puestos)
            self.information.emit('Puntos reactivos sobre los áridos colocados')
            self.progreso.emit(65)

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

        """
        Añadir los parches como colecciones para acelerar el render
        """
        if self.todos_poros:
            poros_collection = PatchCollection(self.todos_poros, color='red', edgecolor='none')
            axes.add_collection(poros_collection)

        if self.todos_aridos_gruesos:
            aridos_collection = PatchCollection(
                self.todos_aridos_gruesos, 
                facecolor='lightblue', 
                edgecolor='blue', 
                linewidth=0.5,
                antialiased=True,
                alpha=0.8
            )
            axes.add_collection(aridos_collection)

        if self.todos_aridos_finos:
            aridos_collection = PatchCollection(
                self.todos_aridos_finos,
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

        """Añadir la probeta (el contorno del dominio)"""
        if self.params.x and self.params.y:
            probeta = plt.Rectangle((0, 0), self.params.x, self.params.y, color='black', fill=False, linewidth=2)
            axes.add_patch(probeta)
            axes.autoscale_view()

        """Convertir la figura a QPixmap de alta resolución"""
        canvas = FigureCanvas(figure)
        buf = io.BytesIO()
        canvas.print_figure(buf, format='png', dpi=600, bbox_inches='tight')
        buf.seek(0)
        self.pixmap = QPixmap()
        self.pixmap.loadFromData(buf.read())

        """Emitir las señales"""
        self.imagen.emit(self.pixmap)
        self.pore_list.emit(self.lista_poros)
        self.coarse_list.emit(self.lista_aridos_gruesos)
        self.fine_list.emit(self.lista_aridos_finos)
        self.reactive_list.emit(self.lista_ptos_react)
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
            self.colocar_aridos_finos_y_gruesos()
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

            # Emitir listas reales al terminar
            # (ajusta los nombres por los que uses internamente)
            self.pore_list.emit(getattr(self, "lista_poros", []))
            self.coarse_list.emit(getattr(self, "lista_aridos_gruesos", []))
            self.fine_list.emit(getattr(self, "lista_aridos_finos", []))
            self.reactive_list.emit(getattr(self, "lista_ptos_react", []))

            self.information.emit("Simulación finalizada correctamente.")
            self.progreso.emit(100)

        except SimulationStopped:
            self.information.emit("Simulación parada por el usuario.")
        except Exception as e:
            self.information_error.emit(f"Error en simular(): {e}")

        finally:
            self.finished.emit()

