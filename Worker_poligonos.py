
from worker_base import WorkerBase, SimParams
import numpy as np
from PyQt5.QtCore import pyqtSignal, QObject
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.collections import PatchCollection
from shapely.geometry import Point, Polygon, box
from shapely import affinity
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.patches import Circle
from shapely.strtree import STRtree
from shapely.geometry import box


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
        """Verifica que un nuevo círculo colisione con al menos un árido"""
        nuevo_circulo = Point(x, y).buffer(r)
        # return any(nuevo_circulo.intersects(arido) for arido in lista_aridos)

        return any(nuevo_circulo.intersects(Point(ar[0], ar[1]).buffer(ar[2])) for ar in lista_aridos)

    # def distancias_aridos_ptos(self, lista, coor_x, coor_y, radio):
    #     """
    #     Devuelve True si el nuevo punto (coor_x, coor_y, radio) intersecta con
    #     al menos un árido de 'lista'. Soporta:
    #       - elementos [x, y, r] (círculos),
    #       - elementos [cx, cy, a, b, angle?] (elipses, a/b semi-ejes, angle en grados opcional),
    #       - objetos Shapely (Polygon, Geometry).
    #     """
    #     if not lista:
    #         return False
    #
    #     nuevo = Point(coor_x, coor_y).buffer(radio, resolution=32)
    #
    #     for ar in lista:
    #         # Caso: círculo definido como [x, y, r]
    #         if isinstance(ar, (list, tuple)) and len(ar) == 3:
    #             try:
    #                 ar_circ = Point(ar[0], ar[1]).buffer(ar[2], resolution=32)
    #             except Exception:
    #                 continue
    #             if nuevo.intersects(ar_circ):
    #                 return True
    #
    #         # Caso: elipse parametrizada [cx, cy, a, b, angle?]
    #         elif isinstance(ar, (list, tuple)) and len(ar) >= 4:
    #             try:
    #                 cx, cy, a, b = ar[0], ar[1], ar[2], ar[3]
    #                 angle = ar[4] if len(ar) > 4 else 0.0
    #                 base = Point(cx, cy).buffer(1.0, resolution=64)
    #                 elipse = affinity.scale(base, a, b, origin=(cx, cy))
    #                 if angle:
    #                     elipse = affinity.rotate(elipse, angle, origin=(cx, cy))
    #             except Exception:
    #                 continue
    #             if nuevo.intersects(elipse):
    #                 return True
    #
    #         # Caso: ya es una geometría Shapely
    #         else:
    #             try:
    #                 if nuevo.intersects(ar):
    #                     return True
    #             except Exception:
    #                 continue
    #
    #     return False

    def distancias_poros_aridos(self, x, y, r, lista_aridos):
        """Verifica que el poro no colisione con ningún árido poligonal"""
        poro = Point(x, y).buffer(r)
        return all(not poro.intersects(arido) for arido in lista_aridos)

    def calcular_poros(self):
        if self.check_poros:
            self.A_poros = self.A * self.params.Pporos
            while self.A_poros > np.pi * (self.params.dporo_min / 2) ** 2:
                rporo = (self.params.dporo_min + np.random.random() * (self.params.dporo_max - self.params.dporo_min)) / 2
                Aporo = np.pi * (rporo) ** 2
                self.A_poros = self.A_poros - Aporo
                self.radios_poros.append(rporo)
            self.progreso.emit(40)
            self.information.emit('Poros calculados. ' + str(len(self.radios_poros)) + ' Poros')

    # def colocar_poros(self):
    #     def dentro_de_limites(x, y, r):
    #         """Verifica que el poro esté completamente dentro del dominio"""
    #         return r < x < self.x - r and r < y < self.y - r
    #
    #     def intentar_colocar_poro(x, y, r, lista_existente, aridos_puestos):
    #         if not dentro_de_limites(x, y, r):
    #             return False
    #         if aridos_puestos and not self.distancias_poros_aridos(x, y, r, self.lista_aridos):
    #             return False
    #         if lista_existente and not self.distancias(lista_existente, x, y, r):
    #             return False
    #         return True
    #
    #     while self.radios_poros:
    #         r = self.radios_poros[0]
    #         x = np.random.uniform(0, self.x)
    #         y = np.random.uniform(0, self.y)
    #         if intentar_colocar_poro(x, y, r, self.lista_poros, self.aridos_puestos):
    #             self.lista_poros.append([x, y, r])
    #             self.todos_poros.append(plt.Circle((x, y), r, color='r'))
    #             self.radios_poros.pop(0)
    #             self.poros_puestos = True
    #
    #     print(len(self.lista_poros))
    #     print(self.A_poros)
    #     self.progreso.emit(50)
    #     self.information.emit('Poros colocados')

    def colocar_poros(self):
        def dentro_de_limites(x, y, r):
            return r < x < self.params.x - r and r < y < self.params.y - r

        def distancias_poros_aridos(x, y, r, lista_aridos):
            poro = Point(x, y).buffer(r)
            return all(not poro.intersects(arido) for arido in lista_aridos)

        def distancias(lista, x, y, r):
            poro = Point(x, y).buffer(r)
            return all(not poro.intersects(p) for p in lista)

        intentos_maximos = 1000
        while self.radios_poros:
            r = self.radios_poros[0]
            colocado = False
            for _ in range(intentos_maximos):
                x = np.random.uniform(0, self.params.x)
                y = np.random.uniform(0, self.params.y)
                if not dentro_de_limites(x, y, r):
                    continue
                if self.aridos_puestos and not distancias_poros_aridos(x, y, r, self.lista_aridos):
                    continue
                if not distancias(self.lista_poros, x, y, r):
                    continue

                # Si pasa todas las condiciones, colocamos el poro
                self.lista_poros.append(Point(x, y).buffer(r))
                # self.todos_poros.append(plt.Circle((x, y), r, color='r'))
                self.todos_poros.append(Circle((x, y), r, color='r'))
                self.radios_poros.pop(0)
                self.poros_puestos = True
                colocado = True
                break

            if not colocado:
                print(f"⚠️ No se pudo colocar un poro de radio {r} tras {intentos_maximos} intentos.")
                self.radios_poros.pop(0)  # Eliminarlo para evitar bucle infinito

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
        def dentro_de_limites(polygon):
            """Verifica que el polígono esté completamente dentro del dominio"""
            return polygon.bounds[0] >= 0 and polygon.bounds[1] >= 0 and \
                polygon.bounds[2] <= self.params.x and polygon.bounds[3] <= self.params.y

        def colisiona_con_lista(polygon, lista):
            """Verifica si el polígono colisiona con alguno de la lista"""
            return any(polygon.intersects(otro) for otro in lista)

        def intentar_colocar_poligono(vertices, lista_existente, poros_puestos):
            for _ in range(1000):  # Intentos de colocación
                x = np.random.uniform(0, self.params.x)
                y = np.random.uniform(0, self.params.y)
                angulo = np.random.uniform(0, 360)

                poligono = Polygon(vertices)
                poligono = affinity.rotate(poligono, angulo, origin='centroid')
                poligono = affinity.translate(poligono, x - poligono.centroid.x, y - poligono.centroid.y)

                if not dentro_de_limites(poligono):
                    continue
                if poros_puestos and colisiona_con_lista(poligono, self.lista_poros):
                    continue
                if lista_existente and colisiona_con_lista(poligono, lista_existente):
                    continue

                return poligono, [x, y, angulo]

            return None  # No se pudo colocar

        def colocar(lista_poligonos_fuente, lista_datos, lista_destino, progreso_val, mensaje):
            while lista_poligonos_fuente:
                vertices = lista_poligonos_fuente.pop(0)
                resultado = intentar_colocar_poligono(vertices, self.lista_aridos, self.poros_puestos)
                if resultado:
                    poligono_colocado, datos = resultado
                    self.lista_aridos.append(poligono_colocado)
                    lista_datos.append(datos)
                    lista_destino.append(poligono_colocado)
                    self.aridos_puestos = True

            print(f'Tengo tantos áridos: {len(self.lista_aridos)}')
            self.progreso.emit(progreso_val)
            self.information.emit(f'{mensaje} colocados. {len(lista_datos)}')

        # Inicializar listas si no existen
        self.lista_aridos = []
        self.aridos_puestos = False

        # Colocar áridos gruesos
        colocar(
            lista_poligonos_fuente=self.poligonos_gruesos.copy(),
            lista_datos=self.lista_aridos_gruesos,
            lista_destino=self.todos_aridos_gruesos,
            progreso_val=30,
            mensaje='Áridos gruesos'
        )

        # Colocar áridos finos
        colocar(
            lista_poligonos_fuente=self.poligonos_finos.copy(),
            lista_datos=self.lista_aridos_finos,
            lista_destino=self.todos_aridos_finos,
            progreso_val=32,
            mensaje='Áridos finos'
        )

    def calcular_puntos_sin_extrafinos(self):
        """puntos sobre áridos gruesos"""
        if self.check_puntos_aridos:
            if self.params.Ppto_react_aridos:
                self.A_puntos_aridos = self.params.Ppto_react_aridos * self.A
                while self.A_puntos_aridos > np.pi * (self.params.dpto_min_aridos / 2) ** 2:
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

    # def colocar_puntos_sin_extrafinos(self):
    #         def dentro_de_limites(x, y, r):
    #             """equivalente a if loc_pto_x + r < self.x and loc_pto_x - r > 0
    #             and loc_pto_y + r < self.y and loc_pto_y - r > 0:
    #             pero más legible"""
    #             return r < x < self.x - r and r < y < self.y - r
    #
    #         def intentar_colocar_punto(x, y, r, lista_existente, evitar_aridos, poros_puestos):
    #             if not dentro_de_limites(x, y, r):
    #                 print('fuera de límites')
    #                 return False
    #             if poros_puestos and not self.distancias(self.lista_poros, x, y, r):
    #                 print('colisiona con poros')
    #                 return False
    #             if evitar_aridos and not self.distancias(self.lista_aridos_gruesos, x, y, r):
    #                 print('colisiona con aridos')
    #                 return False
    #             if not evitar_aridos and not self.distancias_aridos_ptos(self.lista_aridos_gruesos, x, y, r):
    #                 print('colisión con puntos con aridos')
    #                 return False
    #             if len(lista_existente) > 0 and not self.distancias(lista_existente, x, y, r):
    #                 print('colisión con puntos ya puestos')
    #                 return False
    #             return True
    #
    #         def colocar(lista_radios, lista_guardar, evitar_aridos, poros_puestos):
    #             max_intentos_por_punto = 1000
    #             while lista_radios:
    #                 r = lista_radios[0]
    #                 colocado = False
    #                 for _ in range(max_intentos_por_punto):
    #                     x = np.random.uniform(0, self.x)
    #                     y = np.random.uniform(0, self.y)
    #                     if intentar_colocar_punto(x, y, r, lista_guardar, evitar_aridos, poros_puestos):
    #                         lista_guardar.append([x, y, r])
    #                         self.todos_ptos_react.append(plt.Circle((x, y), r, color='y'))
    #                         colocado = True
    #                         break
    #                 if not colocado:
    #                     print(f"No se pudo colocar punto con radio {r:.3f} tras {max_intentos_por_punto} intentos.")
    #                 lista_radios.pop(0)
    #
    #         # Colocar puntos sobre áridos
    #         colocar(self.radios_puntos_aridos, self.lista_ptos_react_aridos,
    #                 evitar_aridos=False, poros_puestos=self.poros_puestos)
    #
    #         self.progreso.emit(65)
    #         if self.check_puntos_aridos:
    #             self.information.emit('Puntos reactivos sobre los áridos colocados')
    #
    #         # Colocar puntos sobre pasta
    #         colocar(self.radios_puntos_pasta, self.lista_ptos_react_pasta,
    #                 evitar_aridos=True, poros_puestos=self.poros_puestos)
    #
    #         self.progreso.emit(70)
    #         if self.check_puntos_pasta:
    #             self.information.emit('Puntos reactivos sobre la pasta colocados')
    #
    #         self.lista_ptos_react = self.lista_ptos_react_aridos + self.lista_ptos_react_pasta

    # def colocar_puntos_sin_extrafinos(self):
    #     """Coloca los puntos reactivos sobre los áridos y la pasta, utilizando clusters para los áridos y ruido Simplex para la pasta."""
    #     def dentro_de_limites(x, y, r):
    #         return r < x < self.x - r and r < y < self.y - r
    #
    #     def intentar_colocar_punto(x, y, r, lista_existente, evitar_aridos, poros_puestos):
    #         if not dentro_de_limites(x, y, r):
    #             return False
    #         if poros_puestos and not self.distancias(self.lista_poros, x, y, r):
    #             return False
    #         if evitar_aridos and not self.distancias(self.lista_aridos_gruesos, x, y, r):
    #             return False
    #         if not evitar_aridos and not self.distancias_aridos_ptos(self.lista_aridos_gruesos, x, y, r):
    #             return False
    #         if len(lista_existente) > 0 and not self.distancias(lista_existente, x, y, r):
    #             return False
    #         return True
    #
    #     def generar_centros_clusters(k):
    #         return [(np.random.uniform(0, self.x), np.random.uniform(0, self.y)) for _ in range(k)]
    #
    #     def colocar_con_clusters(lista_radios, lista_guardar, evitar_aridos, poros_puestos, k=5, sigma=5):
    #         centros = generar_centros_clusters(k)
    #         while lista_radios:
    #             r = lista_radios[0]
    #             for _ in range(1000):
    #                 cx, cy = random.choice(centros)
    #                 x = np.random.normal(cx, sigma)
    #                 y = np.random.normal(cy, sigma)
    #                 if intentar_colocar_punto(x, y, r, lista_guardar, evitar_aridos, poros_puestos):
    #                     lista_guardar.append([x, y, r])
    #                     self.todos_ptos_react.append(plt.Circle((x, y), r, color='y'))
    #                     lista_radios.pop(0)
    #                     break
    #
    #     def colocar_con_simplex(lista_radios, lista_guardar, evitar_aridos, poros_puestos, escala=0.05, umbral=0.3):
    #         ruido = OpenSimplex(seed=42)
    #         while lista_radios:
    #             r = lista_radios[0]
    #             for _ in range(1000):
    #                 x = np.random.uniform(0, self.x)
    #                 y = np.random.uniform(0, self.y)
    #                 valor = (ruido.noise2(x * escala, y * escala) + 1) / 2
    #                 if valor < umbral:
    #                     continue
    #                 if intentar_colocar_punto(x, y, r, lista_guardar, evitar_aridos, poros_puestos):
    #                     lista_guardar.append([x, y, r])
    #                     self.todos_ptos_react.append(plt.Circle((x, y), r, color='y'))
    #                     lista_radios.pop(0)
    #                     break
    #
    #     # Colocar puntos sobre áridos con clusters
    #     colocar_con_clusters(self.radios_puntos_aridos, self.lista_ptos_react_aridos,
    #                          evitar_aridos=False, poros_puestos=self.poros_puestos)
    #
    #     self.progreso.emit(65)
    #     if self.check_puntos_aridos:
    #         self.information.emit('Puntos reactivos sobre los áridos colocados')
    #
    #     # Colocar puntos sobre pasta con ruido Simplex
    #     colocar_con_simplex(self.radios_puntos_pasta, self.lista_ptos_react_pasta,
    #                         evitar_aridos=True, poros_puestos=self.poros_puestos)
    #
    #     self.progreso.emit(70)
    #     if self.check_puntos_pasta:
    #         self.information.emit('Puntos reactivos sobre la pasta colocados')
    #
    #     self.lista_ptos_react = self.lista_ptos_react_aridos + self.lista_ptos_react_pasta


    # def colocar_puntos_sin_extrafinos(self):
    #     # 1. Crear máscara de áridos como unión de buffers
    #     mascaras_aridos = [Point(x, y).buffer(r) for x, y, r in self.lista_aridos_gruesos]
    #     zona_aridos = unary_union(mascaras_aridos)
    #
    #     # 2. Crear dominio total como un polígono rectangular
    #     dominio_total = Polygon([(0, 0), (self.x, 0), (self.x, self.y), (0, self.y)])
    #
    #     # 3. Zona de pasta = dominio - zona áridos
    #     zona_pasta = dominio_total.difference(zona_aridos)
    #
    #     def intentar_colocar_punto(x, y, r, lista_existente, zona_valida, poros_puestos):
    #         nuevo_circulo = Point(x, y).buffer(r)
    #         if not zona_valida.contains(nuevo_circulo):
    #             return False
    #         if poros_puestos and not self.distancias(self.lista_poros, x, y, r):
    #             return False
    #         if len(lista_existente) > 0 and not self.distancias(lista_existente, x, y, r):
    #             return False
    #         return True
    #
    #     def colocar(lista_radios, lista_guardar, zona_valida, poros_puestos):
    #         max_intentos_por_punto = 1000
    #         while lista_radios:
    #             r = lista_radios[0]
    #             colocado = False
    #             for _ in range(max_intentos_por_punto):
    #                 x = np.random.uniform(0, self.x)
    #                 y = np.random.uniform(0, self.y)
    #                 if intentar_colocar_punto(x, y, r, lista_guardar, zona_valida, poros_puestos):
    #                     lista_guardar.append([x, y, r])
    #                     self.todos_ptos_react.append(plt.Circle((x, y), r, color='y'))
    #                     colocado = True
    #                     break
    #             if not colocado:
    #                 print(f"No se pudo colocar punto con radio {r:.3f} tras {max_intentos_por_punto} intentos.")
    #             lista_radios.pop(0)
    #
    #     # Colocar puntos sobre áridos
    #     colocar(self.radios_puntos_aridos, self.lista_ptos_react_aridos,
    #             zona_valida=zona_aridos, poros_puestos=self.poros_puestos)
    #
    #     self.progreso.emit(65)
    #     if self.check_puntos_aridos:
    #         self.information.emit('Puntos reactivos sobre los áridos colocados')
    #
    #     # Colocar puntos sobre pasta
    #     colocar(self.radios_puntos_pasta, self.lista_ptos_react_pasta,
    #             zona_valida=zona_pasta, poros_puestos=self.poros_puestos)
    #
    #     self.progreso.emit(70)
    #     if self.check_puntos_pasta:
    #         self.information.emit('Puntos reactivos sobre la pasta colocados')

    # def colocar_puntos_sin_extrafinos(self):
    #     # Máscaras
    #     mascaras_aridos = [Point(x, y).buffer(r) for x, y, r in self.lista_aridos_gruesos]
    #     zona_aridos = unary_union(mascaras_aridos)
    #     dominio_total = Polygon([(0, 0), (self.x, 0), (self.x, self.y), (0, self.y)])
    #     zona_pasta = dominio_total.difference(zona_aridos)
    #
    #     def intentar_colocar_punto(x, y, r, lista_existente, zona_valida, poros_puestos):
    #         nuevo_circulo = Point(x, y).buffer(r)
    #         if not zona_valida.contains(nuevo_circulo):
    #             return False
    #         if poros_puestos and not self.distancias(self.lista_poros, x, y, r):
    #             return False
    #         if len(lista_existente) > 0 and not self.distancias(lista_existente, x, y, r):
    #             return False
    #         return True
    #
    #     def colocar(area_objetivo, lista_guardar, zona_valida, dpto_min, dpto_max, poros_puestos):
    #         max_intentos_por_punto = 1000
    #         area_restante = area_objetivo
    #         while area_restante > np.pi * (dpto_min / 2) ** 2:
    #             if dpto_min == dpto_max:
    #                 r = dpto_min / 2
    #             else:
    #                 r = (dpto_min + np.random.random() * (dpto_max - dpto_min)) / 2
    #             Apunto = np.pi * r ** 2
    #             colocado = False
    #             for _ in range(max_intentos_por_punto):
    #                 x = np.random.uniform(0, self.x)
    #                 y = np.random.uniform(0, self.y)
    #                 if intentar_colocar_punto(x, y, r, lista_guardar, zona_valida, poros_puestos):
    #                     lista_guardar.append([x, y, r])
    #                     self.todos_ptos_react.append(plt.Circle((x, y), r, color='y'))
    #                     area_restante -= Apunto
    #                     colocado = True
    #                     break
    #             if not colocado:
    #                 print(f"No se pudo colocar punto con radio {r:.3f} tras {max_intentos_por_punto} intentos.")
    #
    #     # Colocar puntos sobre áridos
    #     if self.check_puntos_aridos and self.Ppto_react_aridos:
    #         A_objetivo_aridos = self.Ppto_react_aridos * self.A
    #         colocar(A_objetivo_aridos, self.lista_ptos_react_aridos, zona_aridos,
    #                 self.dpto_min_aridos, self.dpto_max_aridos, poros_puestos=self.poros_puestos)
    #         self.progreso.emit(65)
    #         self.information.emit('Puntos reactivos sobre los áridos colocados')
    #
    #     # Colocar puntos sobre pasta
    #     if self.check_puntos_pasta and self.Ppto_react_pasta:
    #         A_objetivo_pasta = self.Ppto_react_pasta * self.A
    #         colocar(A_objetivo_pasta, self.lista_ptos_react_pasta, zona_pasta,
    #                 self.dpto_min_pasta, self.dpto_max_pasta, poros_puestos=self.poros_puestos)
    #         self.progreso.emit(70)
    #         self.information.emit('Puntos reactivos sobre la pasta colocados')
    #
    #     self.lista_ptos_react = self.lista_ptos_react_aridos + self.lista_ptos_react_pasta

    # def colocar_puntos_sin_extrafinos(self):
    #     # Preprocesar máscaras de áridos
    #     mascaras_aridos = [Point(x, y).buffer(r, resolution=8) for x, y, r in self.lista_aridos_gruesos]
    #     zona_aridos = unary_union(mascaras_aridos)
    #     dominio_total = box(0, 0, self.x, self.y)  # Más rápido que Polygon
    #     zona_pasta = dominio_total.difference(zona_aridos)
    #
    #     # Cachear zona válida con prepared geometry
    #     zona_pasta_preparada = prep(zona_pasta)
    #     zona_aridos_preparada = prep(zona_aridos)
    #
    #     def intentar_colocar_punto(x, y, r, lista_existente, zona_valida_preparada, poros_puestos):
    #         nuevo_circulo = Point(x, y).buffer(r, resolution=8)
    #         if not zona_valida_preparada.contains(nuevo_circulo):
    #             print('fuera de los límites válidos')
    #             return False
    #         if poros_puestos and not self.distancias(self.lista_poros, x, y, r):
    #             print('colisiona con poros')
    #             return False
    #         if lista_existente and not self.distancias(lista_existente, x, y, r):
    #             print('colisión con algo ya puesto')
    #             return False
    #         return True
    #
    #     def colocar(area_objetivo, lista_guardar, zona_valida_preparada, dpto_min, dpto_max, poros_puestos):
    #         max_intentos_por_punto = 1000
    #         area_restante = area_objetivo
    #         while area_restante > np.pi * (dpto_min / 2) ** 2:
    #             r = (dpto_min + np.random.random() * (dpto_max - dpto_min)) / 2
    #             Apunto = np.pi * r ** 2
    #             colocado = False
    #             for _ in range(max_intentos_por_punto):
    #                 x = np.random.uniform(0, self.x)
    #                 y = np.random.uniform(0, self.y)
    #                 if intentar_colocar_punto(x, y, r, lista_guardar, zona_valida_preparada, poros_puestos):
    #                     lista_guardar.append([x, y, r])
    #                     self.todos_ptos_react.append(plt.Circle((x, y), r, color='y'))
    #                     area_restante -= Apunto
    #                     colocado = True
    #                     break
    #             if not colocado:
    #                 print(f"No se pudo colocar punto con radio {r:.3f} tras {max_intentos_por_punto} intentos.")
    #
    #     # Colocar puntos sobre áridos
    #     if self.check_puntos_aridos and self.Ppto_react_aridos:
    #         A_objetivo_aridos = self.Ppto_react_aridos * self.A
    #         colocar(A_objetivo_aridos, self.lista_ptos_react_aridos, zona_aridos_preparada,
    #                 self.dpto_min_aridos, self.dpto_max_aridos, poros_puestos=self.poros_puestos)
    #         self.progreso.emit(65)
    #         self.information.emit('Puntos reactivos sobre los áridos colocados')
    #
    #     # Colocar puntos sobre pasta
    #     if self.check_puntos_pasta and self.Ppto_react_pasta:
    #         A_objetivo_pasta = self.Ppto_react_pasta * self.A
    #         colocar(A_objetivo_pasta, self.lista_ptos_react_pasta, zona_pasta_preparada,
    #                 self.dpto_min_pasta, self.dpto_max_pasta, poros_puestos=self.poros_puestos)
    #         self.progreso.emit(70)
    #         self.information.emit('Puntos reactivos sobre la pasta colocados')
    #
    #     self.lista_ptos_react = self.lista_ptos_react_aridos + self.lista_ptos_react_pasta

    # def colocar_puntos_sin_extrafinos(self):
    #
    #     # Preparar geometría
    #     mascaras_aridos = [Point(x, y).buffer(r, resolution=8) for x, y, r in self.lista_aridos_gruesos]
    #     zona_aridos = unary_union(mascaras_aridos)
    #     dominio_total = box(0, 0, self.x, self.y)
    #     zona_pasta = dominio_total.difference(zona_aridos)
    #     zona_pasta_preparada = prep(zona_pasta)
    #
    #     # Generar cuadrícula de puntos candidatos
    #     paso = min(self.dpto_min_pasta, self.dpto_max_pasta) / 2
    #     puntos_candidatos = []
    #     for xi in np.arange(0, self.x, paso):
    #         for yi in np.arange(0, self.y, paso):
    #             p = Point(xi, yi)
    #             if zona_pasta_preparada.contains(p):
    #                 puntos_candidatos.append((xi, yi))
    #
    #     np.random.shuffle(puntos_candidatos)
    #
    #     # Colocar puntos
    #     A_objetivo_pasta = self.Ppto_react_pasta * self.A
    #     area_restante = A_objetivo_pasta
    #     print(f"Área objetivo pasta: {A_objetivo_pasta:.2f}")
    #     print(f"Puntos candidatos: {len(puntos_candidatos)}")
    #
    #     for x, y in puntos_candidatos:
    #         if area_restante < np.pi * (self.dpto_min_pasta / 2) ** 2:
    #             print("Área restante demasiado pequeña, se detiene la colocación.")
    #             break
    #
    #         r = (self.dpto_min_pasta + np.random.random() * (self.dpto_max_pasta - self.dpto_min_pasta)) / 2
    #         Apunto = np.pi * r ** 2
    #
    #         if not self.distancias(self.lista_ptos_react_pasta, x, y, r):
    #             print(f"Rechazado por distancias con puntos reactivos existentes en ({x:.2f}, {y:.2f})")
    #             continue
    #
    #         if self.poros_puestos and not self.distancias(self.lista_poros, x, y, r):
    #             print(f"Rechazado por distancias con poros en ({x:.2f}, {y:.2f})")
    #             continue
    #         nuevo_circulo = Point(x, y).buffer(r, resolution=8)
    #         if not zona_pasta_preparada.contains(nuevo_circulo):
    #             print(f"Rechazado por estar fuera de zona pasta en ({x:.2f}, {y:.2f})")
    #             continue
    #         # Si pasa todas las condiciones
    #         self.lista_ptos_react_pasta.append([x, y, r])
    #         self.todos_ptos_react.append(Circle((x, y), r, color='y'))
    #         print(f"Punto reactivo añadido en ({x:.2f}, {y:.2f}) con radio {r:.2f}")
    #         area_restante -= Apunto

    def colocar_puntos_sin_extrafinos(self):
            def dentro_de_limites(x, y, r):
                """equivalente a if loc_pto_x + r < self.x and loc_pto_x - r > 0
                and loc_pto_y + r < self.y and loc_pto_y - r > 0:
                pero más legible"""
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

            def colocar(lista_radios, lista_guardar, evitar_aridos, poros_puestos):
                while lista_radios:
                    r = lista_radios[0]
                    x = np.random.uniform(0, self.params.x)
                    y = np.random.uniform(0, self.params.y)
                    if intentar_colocar_punto(x, y, r, lista_guardar, evitar_aridos, poros_puestos):
                        lista_guardar.append([x, y, r])
                        self.todos_ptos_react.append(plt.Circle((x, y), r, color='y'))
                        lista_radios.pop(0)

            # Colocar puntos sobre áridos
            colocar(self.radios_puntos_aridos, self.lista_ptos_react_aridos,
                    evitar_aridos=False, poros_puestos=self.poros_puestos)

            self.progreso.emit(65)
            if self.check_puntos_aridos:
                self.information.emit('Puntos reactivos sobre los áridos colocados')

            # Colocar puntos sobre pasta
            colocar(self.radios_puntos_pasta, self.lista_ptos_react_pasta,
                    evitar_aridos=True, poros_puestos=self.poros_puestos)

            self.progreso.emit(70)
            if self.check_puntos_pasta:
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
            poros_collection = PatchCollection(self.todos_poros, color='red')
            axes.add_collection(poros_collection)

        if self.todos_aridos_gruesos:
            patches_gruesos = [shapely_to_patch(e) for e in self.todos_aridos_gruesos]
            aridos_collection = PatchCollection(patches_gruesos, color='b')
            axes.add_collection(aridos_collection)

        if self.todos_aridos_finos:
            patches_finos = [shapely_to_patch(e) for e in self.todos_aridos_finos]
            aridos_collection = PatchCollection(patches_finos, color='c')
            axes.add_collection(aridos_collection)
            print('2222hay numerosos puntos reactivos. Estos = ' + str(len(self.todos_ptos_react)))

        if self.todos_ptos_react:
            react_collection = PatchCollection(self.todos_ptos_react, color='y')
            axes.add_collection(react_collection)
            print('hay numerosos puntos reactivos. Estos = ' + str(len(self.todos_ptos_react)))

        """Dibujar el contorno de la probeta"""
        if self.params.x and self.params.y:
            probeta = plt.Rectangle((0, 0), self.params.x, self.params.y, color='black', fill=False)
            axes.add_patch(probeta)
            axes.autoscale_view()

        """Convertir figura a QPixmap"""
        canvas = FigureCanvas(figure)
        self.pixmap = canvas.grab()

        """Emitir señales"""
        self.imagen.emit(self.pixmap)
        self.pore_list.emit(self.lista_poros)
        self.coarse_list.emit(self.lista_aridos_gruesos)
        self.fine_list.emit(self.lista_aridos_finos)
        self.reactive_list.emit(self.lista_ptos_react)
        self.finished.emit()

    # def simular(self):
    #
    #     print('empieza la simulacion')
    #     print('está todo correcto? ' + str(self.todo_correcto))
    #     # self.todo_correcto = False
    #     if self.todo_correcto:
    #         print('todo correcto')
    #         self.dosificacion_sin_extrafinos()
    #         self.calcular_areas_aridos_sin_extrafinos()
    #         self.calcular_aridos_por_area_gruesos()
    #         self.calcular_aridos_por_area_finos()
    #         self.colocar_aridos_poligonales()
    #
    #         if self.check_poros:
    #             self.calcular_poros()
    #             self.colocar_poros()
    #         if self.check_puntos:
    #             self.calcular_puntos_sin_extrafinos()
    #             print('puntos bien calculados')
    #             self.colocar_puntos_sin_extrafinos()
    #             print('puntos bien colocados')
    #         self.plotear_resultados()
    #     else:
    #         self.information_error.emit('--error grave')
    #
    # def colocar_puntos_sin_extrafinos(self):
    #     """
    #     Versión acelerada usando STRtree para los áridos (índice espacial).
    #     - Menos buffers/union costosos.
    #     - Buffer resolution reducido para acelerar (ajustable).
    #     """
    #     resolution = 8  # reducir para acelerar; ajustar si necesitas más precisión
    #
    #     # Construir geometrías y árbol espacial una sola vez
    #     aridos_geoms = [Point(x, y).buffer(r, resolution=resolution) for x, y, r in self.lista_aridos_gruesos]
    #     aridos_tree = STRtree(aridos_geoms) if aridos_geoms else None
    #
    #     dominio = box(0, 0, self.params.x, self.params.y)
    #
    #     def dentro_de_limites(x, y, r):
    #         return r < x < self.params.x - r and r < y < self.params.y - r
    #
    #     def intentar_colocar_punto(x, y, r, lista_existente, evitar_aridos, poros_puestos):
    #         if not dentro_de_limites(x, y, r):
    #             return False
    #
    #         # comprobaciones rápidas con listas existentes (poros / puntos)
    #         if poros_puestos and not self.distancias(self.lista_poros, x, y, r):
    #             return False
    #         if lista_existente and not self.distancias(lista_existente, x, y, r):
    #             return False
    #
    #         # candidato como geometría (baja resolución)
    #         candidato = Point(x, y).buffer(r, resolution=resolution)
    #
    #         # Si queremos colocar EN áridos: debe intersectar al menos uno
    #         if not evitar_aridos:
    #             if not aridos_tree:
    #                 return False
    #             posibles = aridos_tree.query(candidato)
    #             if not any(candidato.intersects(g) for g in posibles):
    #                 return False
    #
    #         # Si queremos colocar EN pasta: no debe intersectar ningún árido
    #         else:
    #             if aridos_tree:
    #                 posibles = aridos_tree.query(candidato)
    #                 if any(candidato.intersects(g) for g in posibles):
    #                     return False
    #
    #         return True
    #
    #     def colocar(lista_radios, lista_guardar, evitar_aridos, poros_puestos):
    #         max_intentos_por_punto = 1000
    #         while lista_radios:
    #             r = lista_radios[0]
    #             colocado = False
    #             for _ in range(max_intentos_por_punto):
    #                 x = np.random.uniform(0, self.params.x)
    #                 y = np.random.uniform(0, self.params.y)
    #                 if intentar_colocar_punto(x, y, r, lista_guardar, evitar_aridos, poros_puestos):
    #                     lista_guardar.append([x, y, r])
    #                     self.todos_ptos_react.append(plt.Circle((x, y), r, color='y'))
    #                     colocado = True
    #                     break
    #             if not colocado:
    #                 # opcional: log corto para saber qué radios fallan
    #                 print(f"No se pudo colocar punto con r={r:.3f} tras {max_intentos_por_punto} intentos.")
    #             lista_radios.pop(0)
    #
    #     # Colocar puntos sobre áridos
    #     if self.check_puntos_aridos:
    #         colocar(self.radios_puntos_aridos, self.lista_ptos_react_aridos,
    #                 evitar_aridos=False, poros_puestos=self.poros_puestos)
    #         self.progreso.emit(65)
    #         self.information.emit('Puntos reactivos sobre los áridos colocados')
    #
    #     # Colocar puntos sobre pasta
    #     if self.check_puntos_pasta:
    #         colocar(self.radios_puntos_pasta, self.lista_ptos_react_pasta,
    #                 evitar_aridos=True, poros_puestos=self.poros_puestos)
    #         self.progreso.emit(70)
    #         self.information.emit('Puntos reactivos sobre la pasta colocados')
    #
    #     self.lista_ptos_react = self.lista_ptos_react_aridos + self.lista_ptos_react_pasta

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

            # Emitir listas reales al terminar
            # (ajusta los nombres por los que uses internamente)
            self.pore_list.emit(getattr(self, "lista_poros", []))
            self.coarse_list.emit(getattr(self, "lista_aridos_gruesos", []))
            self.fine_list.emit(getattr(self, "lista_aridos_finos", []))
            self.reactive_list.emit(getattr(self, "lista_puntos", []))

            self.information.emit("Simulación finalizada correctamente.")
            self.progreso.emit(100)

        except Exception as e:
            self.information_error.emit(f"Error en simular(): {e}")

        finally:
            self.finished.emit()
