
from worker_base import WorkerBase, SimParams
import numpy as np
from PyQt5.QtCore import pyqtSignal, QObject
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.collections import PatchCollection
from shapely.geometry import Point
from shapely import affinity
from matplotlib.patches import Polygon as MplPolygon
import random
from opensimplex import OpenSimplex


class WorkerElipses(WorkerBase):

    def __init__(self, params: SimParams, todo_correcto: bool = True,
                 check_poros: bool = False, check_puntos: bool = False,
                 check_puntos_aridos: bool = False, check_puntos_pasta: bool = False):

        super().__init__(params)


        # self.datos = None   # variable para necesaria para guardar/abrir proyectos

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
    def distancias(self, lista, coor_x, coor_y, radio):
        if not lista:
            return True

        lista_np = np.array(lista)
        dx = lista_np[:, 0] - coor_x
        dy = lista_np[:, 1] - coor_y
        distancias = np.sqrt(dx ** 2 + dy ** 2)
        radios_sumados = radio + lista_np[:, 2]

        return np.all(distancias > radios_sumados)

    # def distancias_aridos_ptos(self, lista, coor_x, coor_y, radio):
    #     if not lista:
    #         return False  # No hay solapamiento si no hay elementos
    #
    #     lista_np = np.array(lista)  # Asume que cada n es [x, y, r]
    #     dx = lista_np[:, 0] - coor_x
    #     dy = lista_np[:, 1] - coor_y
    #     distancias = np.sqrt(dx ** 2 + dy ** 2)
    #     radios_sumados = radio + lista_np[:, 2]
    #
    #     return np.any(distancias < radios_sumados)

    def distancias_aridos_ptos(self, lista, coor_x, coor_y, radio):
        """
        Devuelve True si el nuevo punto (coor_x, coor_y, radio) intersecta con
        al menos un árido de 'lista'. Soporta:
          - elementos [x, y, r] (círculos),
          - elementos [cx, cy, a, b, angle?] (elipses, a/b semi-ejes, angle en grados opcional),
          - objetos Shapely (Polygon, Geometry).
        """
        if not lista:
            return False

        nuevo = Point(coor_x, coor_y).buffer(radio, resolution=32)

        for ar in lista:
            # Caso: círculo definido como [x, y, r]
            if isinstance(ar, (list, tuple)) and len(ar) == 3:
                try:
                    ar_circ = Point(ar[0], ar[1]).buffer(ar[2], resolution=32)
                except Exception:
                    continue
                if nuevo.intersects(ar_circ):
                    return True

            # Caso: elipse parametrizada [cx, cy, a, b, angle?]
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
                if nuevo.intersects(elipse):
                    return True

            # Caso: ya es una geometría Shapely
            else:
                try:
                    if nuevo.intersects(ar):
                        return True
                except Exception:
                    continue

        return False

    def distancias_poros_elipses(self, x, y, radio, lista_elipses):
        poro = Point(x, y).buffer(radio)
        return all(not elipse.intersects(poro) for elipse in lista_elipses)

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

    def colocar_poros(self):
        def dentro_de_limites(x, y, r):
            """Verifica que el poro esté completamente dentro del dominio"""
            return r < x < self.params.x - r and r < y < self.params.y - r

        def intentar_colocar_poro(x, y, r, lista_existente, aridos_puestos):
            if not dentro_de_limites(x, y, r):
                return False
            if aridos_puestos and not self.distancias_poros_elipses(x, y, r, self.lista_aridos):
                return False
            if lista_existente and not self.distancias(lista_existente, x, y, r):
                return False
            return True

        while self.radios_poros:
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

    # def calcular_aridos_por_area_gruesos(self):
    #     """Calcular los áridos por fracción gruesa"""
    #     j = 0
    #     while j < len(self.Aagg_gruesos):
    #         num_particulas = 0
    #         area_c = 0
    #         self.Aagg_gruesos[j] = self.Aagg_gruesos[j] + self.A_remanente
    #         while self.Aagg_gruesos[j] - area_c > np.pi * (self.sieve_size_buena[j + 1] / 2) ** 2:
    #             d = self.sieve_size_buena[j + 1] + np.random.rand() * (self.sieve_size_buena[j] - self.sieve_size_buena[j + 1])
    #             a = d / 2 # semieje mayor
    #             aspecto = np.random.uniform(0.5, 1.0) # relación de aspecto aleatoria
    #             b = a * aspecto # semieje menor
    #             area = np.pi * a * b
    #             if area + area_c < self.Aagg_gruesos[j]:
    #                 area_c = area_c + area
    #                 self.radios_gruesos_elipses.append((a, b)) # guardamos ambos semiejes
    #                 num_particulas = num_particulas + 1
    #             self.A_remanente = self.Aagg_gruesos[j] - area_c
    #         self.particulas.append(num_particulas)
    #         print(self.particulas)
    #         if j < len(self.Aagg_gruesos):
    #             j += 1
    #     self.progreso.emit(20)
    #     self.information.emit('Áridos gruesos (elípticos) por área calculados. ' + str(self.particulas))

    def calcular_aridos_por_area_gruesos(self):
        """Calcular los áridos por fracción gruesa"""
        j = 0
        while j < len(self.Aagg_gruesos):
            num_particulas = 0
            area_c = 0
            self.Aagg_gruesos[j] = self.Aagg_gruesos[j] + self.A_remanente
            while self.Aagg_gruesos[j] - area_c > np.pi * (self.sieve_size_buena[j + 1] / 2) ** 2:
                d = self.sieve_size_buena[j + 1] + np.random.rand() * (self.sieve_size_buena[j] - self.sieve_size_buena[j + 1])
                b = d / 2 # semieje menor
                aspecto = np.random.uniform(1.0, 1.5) # relación de aspecto aleatoria
                a = b * aspecto # semieje mayor
                area = np.pi * a * b
                if area + area_c < self.Aagg_gruesos[j]:
                    area_c = area_c + area
                    self.radios_gruesos_elipses.append((a, b)) # guardamos ambos semiejes
                    num_particulas = num_particulas + 1
                self.A_remanente = self.Aagg_gruesos[j] - area_c
            self.particulas.append(num_particulas)
            print(self.particulas)
            if j < len(self.Aagg_gruesos):
                j += 1
        self.progreso.emit(20)
        self.information.emit('Áridos gruesos (elípticos) por área calculados. ' + str(self.particulas))
        print('la lista de áridos gruesos es ' + str(self.lista_aridos_gruesos))

    # def calcular_aridos_por_area_finos(self):
    #     """Calcular los áridos por fracción fina"""
    #     k = len(self.Aagg_gruesos)
    #     l = 0
    #     while l < len(self.Aagg_finos):
    #         num_particulas = 0
    #         area_c = 0
    #         self.Aagg_finos[l] = self.Aagg_finos[l] + self.A_remanente
    #         while self.Aagg_finos[l] - area_c > np.pi * (self.sieve_size[k + 1] / 2) ** 2:
    #             d = self.sieve_size[k + 1] + np.random.rand() * (self.sieve_size[k] - self.sieve_size[k + 1])
    #             a = d / 2 # semieje mayor
    #             aspecto = np.random.uniform(0.5, 1.0) # relación de aspecto aleatoria
    #             b = a * aspecto # semieje menor
    #             area = np.pi * a * b
    #             if area + area_c < self.Aagg_finos[l]:
    #                 area_c = area_c + area
    #                 self.radios_finos_elipses.append((a, b)) # guardamos ambos semiejes
    #                 num_particulas = num_particulas + 1
    #             self.A_remanente = self.Aagg_finos[l] - area_c
    #         self.particulas.append(num_particulas)
    #         print(self.particulas)
    #         if l < len(self.Aagg_finos):
    #             l += 1
    #             k += 1
    #             print('un fino')
    #     self.progreso.emit(22)
    #     self.information.emit('Áridos finos  (elípticos) por área calculados. ' + str(self.particulas))

    def calcular_aridos_por_area_finos(self):
        """Calcular los áridos por fracción fina"""
        k = len(self.Aagg_gruesos)
        l = 0
        while l < len(self.Aagg_finos):
            num_particulas = 0
            area_c = 0
            self.Aagg_finos[l] = self.Aagg_finos[l] + self.A_remanente
            while self.Aagg_finos[l] - area_c > np.pi * (self.params.sieve_size[k + 1] / 2) ** 2:
                d = self.params.sieve_size[k + 1] + np.random.rand() * (self.params.sieve_size[k] - self.params.sieve_size[k + 1])
                b = d / 2 # semieje menor
                aspecto = np.random.uniform(1.0, 1.5) # relación de aspecto aleatoria
                a = b * aspecto # semieje menor
                area = np.pi * a * b
                if area + area_c < self.Aagg_finos[l]:
                    area_c = area_c + area
                    self.radios_finos_elipses.append((a, b)) # guardamos ambos semiejes
                    num_particulas = num_particulas + 1
                self.A_remanente = self.Aagg_finos[l] - area_c
            self.particulas.append(num_particulas)
            print(self.particulas)
            if l < len(self.Aagg_finos):
                l += 1
                k += 1
                print('un fino')
        self.progreso.emit(22)
        self.information.emit('Áridos finos  (elípticos) por área calculados. ' + str(self.particulas))

    def generar_elipse_shapely(self,x, y, a, b, angulo):
        circ = Point(x, y).buffer(1)  # Círculo unitario centrado
        elipse = affinity.scale(circ, a, b)  # Escala a elipse
        elipse = affinity.rotate(elipse, angulo, origin=(x, y))
        return elipse

    def colisiona_con_lista(self, elipse, lista):
        for otra in lista:
            if elipse.intersects(otra):
                return True
        return False

    def distancias_elipses(self, lista, x, y, a, b):
        """
        Intenta colocar una elipse con centro (x,y), semiejes a,b.
        Si choca con alguna en lista, prueba rotaciones de 1° a 180°.
        Retorna (True, angulo) si no hay colisión en alguna orientación, False en caso contrario.
        """
        for angulo in range(0, 181):
            nueva_elipse = self.generar_elipse_shapely(x, y, a, b, angulo)
            if not self.colisiona_con_lista(nueva_elipse, lista):
                return True, angulo  # Colocación posible
        return False, None  # No se puede colocar sin colisión

    def colocar_elipses(self):
        def dentro_de_limites(x, y, a, b):
            """Verifica que la elipse esté completamente dentro del dominio"""
            return a < x < self.params.x - a and b < y < self.params.y - b

        def generar_elipse_shapely(x, y, a, b, angulo):
            circ = Point(x, y).buffer(1)
            elipse = affinity.scale(circ, a, b)
            return affinity.rotate(elipse, angulo, origin=(x, y))

        def colisiona_con_lista(elipse, lista):
            """Determina si la elipse colisiona con alguna de la lista de elipses existentes.
            Si al menos una colisiona, devuelve True; si ninguna colisiona, devuelve False"""
            return any(elipse.intersects(e) for e in lista)

        def intentar_colocar_elipse(x, y, a, b, lista_existente, poros_puestos):
            if not dentro_de_limites(x, y, a, b):
                return False  # Fuera de dominio

            for angulo in range(0, 181):
                nueva_elipse = generar_elipse_shapely(x, y, a, b, angulo)

                if poros_puestos and colisiona_con_lista(nueva_elipse, self.lista_poros):
                    continue
                if lista_existente and colisiona_con_lista(nueva_elipse, lista_existente):
                    continue

                return nueva_elipse, [x, y, a, b, angulo]

            return None  # No pudo colocarse sin colisión

        def colocar(lista_ab, lista_datos, lista_poligonos, color, progreso_val, mensaje):
            while lista_ab:
                a, b = lista_ab[0]
                x = np.random.uniform(0, self.params.x)
                y = np.random.uniform(0, self.params.y)
                resultado = intentar_colocar_elipse(x, y, a, b, self.params.lista_elipses, self.poros_puestos)
                if resultado:
                    elipse_shapely, datos = resultado
                    self.params.lista_elipses.append(elipse_shapely)
                    lista_datos.append(datos)
                    lista_poligonos.append(elipse_shapely)
                    lista_ab.pop(0)
                    self.aridos_puestos = True

            print(f'Tengo tantas elipses: {len(self.params.lista_elipses)}')
            self.progreso.emit(progreso_val)
            self.information.emit(f'{mensaje} colocadas. {len(lista_datos)}')

        # Colocar áridos gruesos (elipses)
        colocar(
            lista_ab=self.radios_gruesos_elipses,
            lista_datos=self.ista_elipses_gruesos_datos,
            lista_poligonos=self.lista_elipses_gruesos,
            color='b',
            progreso_val=30,
            mensaje='Áridos gruesos'
        )

        # Colocar áridos finos (elipses)
        colocar(
            lista_ab=self.radios_finos_elipses,
            lista_datos=self.lista_elipses_finos_datos,
            lista_poligonos=self.lista_elipses_finos,
            color='c',
            progreso_val=32,
            mensaje='Áridos finos'
        )

    def colocar_aridos_finos_y_gruesos(self):
        def dentro_de_limites(x, y, a, b):
            """Verifica que la elipse esté completamente dentro del dominio"""
            return a < x < self.params.x - a and b < y < self.params.y - b

        def generar_elipse_shapely(x, y, a, b, angulo):
            circ = Point(x, y).buffer(1)
            elipse = affinity.scale(circ, a, b)
            return affinity.rotate(elipse, angulo, origin=(x, y))

        def colisiona_con_lista(elipse, lista):
            """Determina si la elipse colisiona con alguna de la lista de elipses existentes.
            Si al menos una colisiona, devuelve True; si ninguna colisiona, devuelve False"""
            return any(elipse.intersects(e) for e in lista)

        def intentar_colocar_elipse(x, y, a, b, lista_existente, poros_puestos):
            if not dentro_de_limites(x, y, a, b):
                return False  # Fuera de dominio

            for angulo in range(0, 181):
                nueva_elipse = generar_elipse_shapely(x, y, a, b, angulo)

                if poros_puestos and colisiona_con_lista(nueva_elipse, self.lista_poros):
                    continue
                if lista_existente and colisiona_con_lista(nueva_elipse, lista_existente):
                    continue

                return nueva_elipse, [x, y, a, b, angulo]

            return None  # No pudo colocarse sin colisión

        def colocar(lista_ab, lista_datos, lista_elipses, color, progreso_val, mensaje):
            while lista_ab:
                a, b = lista_ab[0]
                x = np.random.uniform(0, self.params.x)
                y = np.random.uniform(0, self.params.y)
                resultado = intentar_colocar_elipse(x, y, a, b, self.lista_aridos, self.poros_puestos)
                if resultado:
                    elipse_shapely, datos = resultado
                    self.lista_aridos.append(elipse_shapely)
                    lista_datos.append(datos)
                    lista_elipses.append(elipse_shapely)
                    lista_ab.pop(0)
                    self.aridos_puestos = True

            print(f'Tengo tantas elipses: {len(self.lista_aridos)}')
            self.progreso.emit(progreso_val)
            self.information.emit(f'{mensaje} colocadas. {len(lista_datos)}')

        # Colocar áridos gruesos (elipses)
        colocar(
            lista_ab=self.radios_gruesos_elipses,
            lista_datos=self.lista_aridos_gruesos,
            lista_elipses= self.todos_aridos_gruesos,
            color='b',
            progreso_val=30,
            mensaje='Áridos gruesos'
        )

        # Colocar áridos finos (elipses)
        colocar(
            lista_ab=self.radios_finos_elipses,
            lista_datos=self.lista_aridos_finos,
            lista_elipses=self.todos_aridos_finos,
            color='c',
            progreso_val=32,
            mensaje='Áridos finos'
        )

    # def colocar_aridos_finos_y_gruesos(self):
    #     def dentro_de_limites(x, y, a, b):
    #         """Verifica que la elipse esté completamente dentro del dominio."""
    #         return max(a, b) < x < self.x - max(a, b) and max(a, b) < y < self.y - max(a, b)
    #
    #     def intentar_colocar_elipse(x, y, a, b):
    #         if not dentro_de_limites(x, y, a, b):
    #             return False
    #         if self.poros_puestos and not self.distancias_elipses(self.lista_poros, x, y, a, b):
    #             return False
    #         if self.lista_aridos and not self.distancias_elipses(self.lista_aridos, x, y, a, b):
    #             return False
    #         return True
    #
    #     def colocar(lista_radios, lista_datos, lista_elipses, color, progreso_val, mensaje):
    #         while lista_radios:
    #             a, b = lista_radios[0]
    #             x = np.random.uniform(0, self.x)
    #             y = np.random.uniform(0, self.y)
    #             if intentar_colocar_elipse(x, y, a, b):
    #                 dato = [x, y, a, b, 0]  # Se guarda con rotación inicial 0°
    #                 self.lista_aridos.append(dato)
    #                 lista_datos.append(dato)
    #                 ellipse = plt.Circle((x, y), max(a, b),
    #                                      color=color)  # Puedes cambiar por matplotlib.patches.Ellipse si quieres visualización real
    #                 self.todos_aridos.append(ellipse)
    #                 lista_elipses.append(ellipse)
    #                 lista_radios.pop(0)
    #                 self.aridos_puestos = True
    #
    #         print(f'tengo tantos áridos: {len(self.lista_aridos)}')
    #         print(len(self.todos_aridos))
    #         print(f'Elipses restantes: {len(lista_radios)}')
    #         self.progreso.emit(progreso_val)
    #         self.information.emit(f'{mensaje} colocados. {len(lista_datos)}')
    #
    #     # Colocar áridos gruesos elípticos
    #     colocar(
    #         self.radios_gruesos_elipses,
    #         self.lista_aridos_gruesos,
    #         self.todos_aridos_gruesos,
    #         color='b',
    #         progreso_val=30,
    #         mensaje='Áridos gruesos elípticos'
    #     )
    #
    #     # Colocar áridos finos elípticos
    #     colocar(
    #         self.radios_finos_elipses,
    #         self.lista_aridos_finos,
    #         self.todos_aridos_finos,
    #         color='c',
    #         progreso_val=32,
    #         mensaje='Áridos finos elípticos'
    #     )
    #
    # def colocar_aridos_finos_y_gruesos(self):
    #     def dentro_de_limites(x, y, r):
    #         """Verifica que el árido esté completamente dentro del dominio"""
    #         return r < x < self.x - r and r < y < self.y - r
    #
    #     def intentar_colocar_arido(x, y, r, lista_existente, poros_puestos):
    #         if not dentro_de_limites(x, y, r):
    #             return False
    #         if poros_puestos and not self.distancias(self.lista_poros, x, y, r):
    #             return False
    #         if lista_existente and not self.distancias(lista_existente, x, y, r):
    #             return False
    #         return True
    #
    #     def colocar(lista_radios, lista_datos, lista_circulos, color, progreso_val, mensaje):
    #         while lista_radios:
    #             r = lista_radios[0]
    #             x = np.random.uniform(0, self.x)
    #             y = np.random.uniform(0, self.y)
    #             if intentar_colocar_arido(x, y, r, self.lista_aridos, self.poros_puestos):
    #                 dato = [x, y, r]
    #                 self.lista_aridos.append(dato)
    #                 lista_datos.append(dato)
    #                 circulo = plt.Circle((x, y), r, color=color)
    #                 self.todos_aridos.append(circulo)
    #                 lista_circulos.append(circulo)
    #                 lista_radios.pop(0)
    #                 self.aridos_puestos = True
    #
    #         print(f'tengo tantos áridos: {len(self.lista_aridos)}')
    #         print(len(self.todos_aridos))
    #         print(f'Radios restantes: {len(lista_radios)}')
    #         self.progreso.emit(progreso_val)
    #         self.information.emit(f'{mensaje} colocados. {len(lista_datos)}')
    #
    #     # Colocar áridos gruesos
    #     colocar(
    #         lista_radios=self.radios_gruesos,
    #         lista_datos=self.lista_aridos_gruesos,
    #         lista_circulos=self.todos_aridos_gruesos,
    #         color='b',
    #         progreso_val=30,
    #         mensaje='Áridos gruesos'
    #     )
    #
    #     # Colocar áridos finos
    #     colocar(
    #         lista_radios=self.radios_finos,
    #         lista_datos=self.lista_aridos_finos,
    #         lista_circulos=self.todos_aridos_finos,
    #         color='c',
    #         progreso_val=32,
    #         mensaje='Áridos finos'
    #     )

    def calcular_puntos_sin_extrafinos(self):
        """puntos sobre áridos gruesos"""
        if self.check_puntos_aridos:
            if self.params.Ppto_react_aridos:
                self.A_puntos_aridos = self.params.Ppto_react_aridos * self.A
                while self.A_puntos_aridos > np.pi * (self.params.dpto_min_aridos / 2) ** 2:
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
    #                 return False
    #             if poros_puestos and not self.distancias(self.lista_poros, x, y, r):
    #                 return False
    #             if evitar_aridos and not self.distancias(self.lista_aridos_gruesos, x, y, r):
    #                 return False
    #             if not evitar_aridos and not self.distancias_aridos_ptos(self.lista_aridos_gruesos, x, y, r):
    #                 return False
    #             if len(lista_existente) > 0 and not self.distancias(lista_existente, x, y, r):
    #                 return False
    #             return True
    #
    #         def colocar(lista_radios, lista_guardar, evitar_aridos, poros_puestos):
    #             while lista_radios:
    #                 r = lista_radios[0]
    #                 x = np.random.uniform(0, self.x)
    #                 y = np.random.uniform(0, self.y)
    #                 if intentar_colocar_punto(x, y, r, lista_guardar, evitar_aridos, poros_puestos):
    #                     lista_guardar.append([x, y, r])
    #                     self.todos_ptos_react.append(plt.Circle((x, y), r, color='y'))
    #                     lista_radios.pop(0)
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

    # def plotear_resultados(self):
    #     figure, axes = plt.subplots()
    #     plt.axis("equal")
    #     axes.set_xlim(0, self.x)
    #     axes.set_ylim(0, self.y)
    #
    #     """
    #     Añadir los parches como colecciones para acelerar el render
    #     """
    #     if self.todos_poros:
    #         poros_collection = PatchCollection(self.todos_poros, color='red')
    #         axes.add_collection(poros_collection)
    #
    #     if self.todos_aridos_gruesos:
    #         aridos_collection = PatchCollection(self.todos_aridos_gruesos, color='b')
    #         axes.add_collection(aridos_collection)
    #
    #     if self.todos_aridos_finos:
    #         aridos_collection = PatchCollection(self.todos_aridos_finos, color='c')
    #         axes.add_collection(aridos_collection)
    #
    #     if self.todos_ptos_react:
    #         react_collection = PatchCollection(self.todos_ptos_react, color='y')
    #         axes.add_collection(react_collection)
    #
    #     """Añadir la probeta (el contorno del dominio)"""
    #     if self.x and self.y:
    #         probeta = plt.Rectangle((0, 0), self.x, self.y, color='black', fill=False)
    #         axes.add_patch(probeta)
    #         axes.autoscale_view()
    #
    #     """Convertir la figura a QPixmap"""
    #     canvas = FigureCanvas(figure)
    #     self.pixmap = canvas.grab()
    #
    #     """Emitir las señales"""
    #     self.imagen.emit(self.pixmap)
    #     self.pore_list.emit(self.lista_poros)
    #     self.coarse_list.emit(self.lista_aridos_gruesos)
    #     self.fine_list.emit(self.lista_aridos_finos)
    #     self.reactive_list.emit(self.lista_ptos_react)
    #     self.finished.emit()


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

        def generar_centros_clusters(k):
            return [(np.random.uniform(0, self.params.x), np.random.uniform(0, self.params.y)) for _ in range(k)]

        def colocar_con_clusters(lista_radios, lista_guardar, evitar_aridos, poros_puestos, k=5, sigma=5):
            centros = generar_centros_clusters(k)
            while lista_radios:
                r = lista_radios[0]
                for _ in range(1000):
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
                r = lista_radios[0]
                for _ in range(1000):
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

        if self.todos_ptos_react:
            react_collection = PatchCollection(self.todos_ptos_react, color='y')
            axes.add_collection(react_collection)

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
    #         self.colocar_aridos_finos_y_gruesos()
    #
    #         if self.check_poros:
    #             self.calcular_poros()
    #             self.colocar_poros()
    #         if self.check_puntos:
    #             self.calcular_puntos_sin_extrafinos()
    #             self.colocar_puntos_sin_extrafinos()
    #         self.plotear_resultados()
    #     else:
    #         self.information_error.emit('--error grave')

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
            self.reactive_list.emit(getattr(self, "lista_puntos", []))

            self.information.emit("Simulación finalizada correctamente.")
            self.progreso.emit(100)

        except Exception as e:
            self.information_error.emit(f"Error en simular(): {e}")

        finally:
            self.finished.emit()
