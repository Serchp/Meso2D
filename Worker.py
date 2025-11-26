import numpy as np
from PyQt5.QtCore import pyqtSignal, QObject
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.collections import PatchCollection


class WorkerTodos(QObject):
    finished = pyqtSignal()
    imagen = pyqtSignal(object)
    datos = pyqtSignal(dict)
    information = pyqtSignal(str)
    information_error = pyqtSignal(str)
    progreso = pyqtSignal(int)
    pore_list = pyqtSignal(list)
    coarse_list = pyqtSignal(list)
    fine_list = pyqtSignal(list)
    reactive_list = pyqtSignal(list)

    def __init__(self, sieve_size, tpp, x, y, Pagg, Pporos, dporo_min, dporo_max, r_react, dpto_max_aridos,
                 dpto_min_aridos, dpto_max_pasta, dpto_min_pasta, Ppto_react_aridos, Ppto_react_pasta, seed,
                 todo_correcto, check_poros, check_puntos, check_puntos_aridos, check_puntos_pasta):

        QObject.__init__(self)

        self.sieve_size = sieve_size  # tamaño de malla del tamiz?
        self.tpp = tpp # porcentaje acumulado de áridos que pasan por el correspondiente sieve_size

        self.x = x   # variable dimensión x de la probeta
        self.y = y   # variable dimensión y de la probeta
        self.Pagg = Pagg    # coarse aggregate ratio
        self.Pporos = Pporos  # porcentaje de poros
        self.dporo_min = dporo_min   # diámetro mínimo de los poros
        self.dporo_max = dporo_max   # diámetro máximo de los poros
        self.r_react = r_react # creo que no está en uso
        self.dpto_max_aridos = dpto_max_aridos # diámetro máximo de los ptos reactivos en los áridos
        self.dpto_min_aridos = dpto_min_aridos # diámetro mínimo de los ptos reactivos en los áridos
        self.dpto_max_pasta = dpto_max_pasta  # diámetro máximo de los ptos reactivos en la pasta
        self.dpto_min_pasta = dpto_min_pasta  # diámetro mínimo de los ptos reactivos en la pasta
        self.Ppto_react_aridos = Ppto_react_aridos   # porcentaje de puntos reactivos en los áridos
        self.Ppto_react_pasta = Ppto_react_pasta    # porcentaje de puntos reactivos en la pasta
        self.seed = seed    # semilla para evitar el random y poder recuperar proyectos

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

    """refactorizadas las funcianes para el cálculo de las distancias
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
            self.A_poros = self.A * self.Pporos
            while self.A_poros > np.pi * (self.dporo_min / 2) ** 2:
                rporo = (self.dporo_min + np.random.random() * (self.dporo_max - self.dporo_min)) / 2
                Aporo = np.pi * (rporo) ** 2
                self.A_poros = self.A_poros - Aporo
                self.radios_poros.append(rporo)
            self.progreso.emit(40)
            self.information.emit('Poros calculados. ' + str(len(self.radios_poros)) + ' Poros')

    # def colocar_poros(self):
    #     while len(self.radios_poros) > 0:
    #         r = self.radios_poros[0]
    #         loc_poro_x = np.random.uniform(0, self.x)
    #         loc_poro_y = np.random.uniform(0, self.y)
    #         dato_poro = [loc_poro_x, loc_poro_y, r]
    #         poro = plt.Circle((loc_poro_x, loc_poro_y), r, color='r')
    #         if self.aridos_puestos == False:
    #             if loc_poro_x + r < self.x and loc_poro_x - r > 0 and loc_poro_y + r < self.y and loc_poro_y - r > 0:
    #                 if len(self.lista_poros) == 0:
    #                     self.lista_poros.append(dato_poro)
    #                     self.todos_poros.append(poro)
    #                     self.radios_poros.remove(r)
    #                 elif self.distancias(self.lista_poros, loc_poro_x, loc_poro_y, r):
    #                     self.lista_poros.append(dato_poro)
    #                     self.todos_poros.append(poro)
    #                     self.radios_poros.remove(r)
    #         else:
    #             if loc_poro_x + r < self.x and loc_poro_x - r > 0 and loc_poro_y + r < self.y and loc_poro_y - r > 0:
    #                 if self.distancias(self.lista_aridos, loc_poro_x, loc_poro_y, r):
    #                     if len(self.lista_poros) == 0:
    #                         self.lista_poros.append(dato_poro)
    #                         self.todos_poros.append(poro)
    #                         self.radios_poros.remove(r)
    #                     elif self.distancias(self.lista_poros, loc_poro_x, loc_poro_y, r):
    #                         self.lista_poros.append(dato_poro)
    #                         self.todos_poros.append(poro)
    #                         self.radios_poros.remove(r)
    #         self.poros_puestos = True
    #
    #     print(len(self.lista_poros))
    #     print(self.A_poros)
    #     self.progreso.emit(50)
    #     self.information.emit('Poros colocados')

    def colocar_poros(self):
        def dentro_de_limites(x, y, r):
            """Verifica que el poro esté completamente dentro del dominio"""
            return r < x < self.x - r and r < y < self.y - r

        def intentar_colocar_poro(x, y, r, lista_existente, aridos_puestos):
            if not dentro_de_limites(x, y, r):
                return False
            if aridos_puestos and not self.distancias(self.lista_aridos, x, y, r):
                return False
            if lista_existente and not self.distancias(lista_existente, x, y, r):
                return False
            return True

        while self.radios_poros:
            r = self.radios_poros[0]
            x = np.random.uniform(0, self.x)
            y = np.random.uniform(0, self.y)
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
        print('la sieve size es ' + str(self.sieve_size))
        print('la sieve size buena es ' + str(self.sieve_size_buena))
        n = 0
        while self.sieve_size[n] >= 2:
            self.sieve_size_buena.append(self.sieve_size[n])
            n = n + 1
            # return self.sieve_size_buena
        self.information.emit('Quitados los extrafinos de la dosificación.')
        self.progreso.emit(15)
        print('la buena dosificacion es ' + str(self.sieve_size_buena))

    def calcular_areas_aridos_sin_extrafinos(self):
        self.A = float(self.x) * float(self.y)
        self.Aagg = []

        # Aseguramos que los tamaños de tamiz y TPP estén en float
        sieve = [float(s) for s in self.sieve_size_buena]
        tpp = [float(p) for p in self.tpp]

        for i in range(len(sieve) - 1):  # i+1 no se sale del rango
            fraccion = (tpp[i] - tpp[i + 1]) / (tpp[0] - tpp[-1])
            area_intervalo = fraccion * self.Pagg * self.A
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
            num_particulas = 0
            area_c = 0
            self.Aagg_gruesos[j] = self.Aagg_gruesos[j] + self.A_remanente
            while self.Aagg_gruesos[j] - area_c > np.pi * (self.sieve_size_buena[j + 1] / 2) ** 2:
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
            num_particulas = 0
            area_c = 0
            self.Aagg_finos[l] = self.Aagg_finos[l] + self.A_remanente
            while self.Aagg_finos[l] - area_c > np.pi * (self.sieve_size[k + 1] / 2) ** 2:
                d = self.sieve_size[k + 1] + np.random.rand() * (self.sieve_size[k] - self.sieve_size[k + 1])
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

    def calcular_aridos_por_area(self):
        """Calcula los áridos circulares por área para fracciones gruesas y finas."""

        def calcular_para_fraccion(Aagg, radios_lista, sieve, inicio_idx):
            for i in range(len(Aagg)):
                Aagg[i] += self.A_remanente
                area_acumulada = 0
                num_particulas = 0

                while Aagg[i] - area_acumulada > np.pi * (sieve[inicio_idx + 1] / 2) ** 2:
                    d = sieve[inicio_idx + 1] + np.random.rand() * (sieve[inicio_idx] - sieve[inicio_idx + 1])
                    radio = d / 2
                    area = np.pi * radio ** 2

                    if area_acumulada + area < Aagg[i]:
                        area_acumulada += area
                        radios_lista.append(radio)
                        num_particulas += 1

                    self.A_remanente = Aagg[i] - area_acumulada

                self.particulas.append(num_particulas)

        # Áridos gruesos
        calcular_para_fraccion(
            Aagg=self.Aagg_gruesos,
            radios_lista=self.radios_gruesos,
            sieve=self.sieve_size_buena,
            inicio_idx=0
        )
        self.progreso.emit(20)
        self.information.emit('Áridos gruesos por área calculados. ' + str(self.particulas))

        # Áridos finos
        inicio_finos = len(self.Aagg_gruesos)
        calcular_para_fraccion(
            Aagg=self.Aagg_finos,
            radios_lista=self.radios_finos,
            sieve=self.sieve_size,
            inicio_idx=inicio_finos
        )
        self.progreso.emit(22)
        self.information.emit('Áridos finos por área calculados. ' + str(self.particulas))

    # def colocar_aridos_finos_y_gruesos(self):
    #     """primero coloco los áridos gruesos"""
    #     while len(self.radios_gruesos) > 0:
    #         i = self.radios_gruesos[0]
    #         loc_x = np.random.uniform(0, self.x)
    #         loc_y = np.random.uniform(0, self.y)
    #         dato_arido = [loc_x, loc_y, i]
    #         arido = plt.Circle((loc_x, loc_y), i, color='b')
    #         if self.poros_puestos == False:
    #             if loc_x + i < self.x and loc_x - i > 0 and loc_y + i < self.y and loc_y - i > 0:
    #                 if len(self.todos_aridos) == 0:
    #                     self.lista_aridos.append(dato_arido)
    #                     self.lista_aridos_gruesos.append(dato_arido)
    #                     self.todos_aridos.append(arido)
    #                     self.todos_aridos_gruesos.append(arido)
    #                     self.radios_gruesos.remove(i)
    #                 elif self.distancias(self.lista_aridos, loc_x, loc_y, i):
    #                     self.lista_aridos.append(dato_arido)
    #                     self.lista_aridos_gruesos.append(dato_arido)
    #                     self.todos_aridos.append(arido)
    #                     self.todos_aridos_gruesos.append(arido)
    #                     self.radios_gruesos.remove(i)
    #         else:
    #             if loc_x + i < self.x and loc_x - i > 0 and loc_y + i < self.y and loc_y - i > 0:
    #                 if self.distancias(self.lista_poros, loc_x, loc_y, i):
    #                     if len(self.todos_aridos) == 0:
    #                         self.lista_aridos.append(dato_arido)
    #                         self.lista_aridos_gruesos.append(dato_arido)
    #                         self.todos_aridos.append(arido)
    #                         self.todos_aridos_gruesos.append(arido)
    #                         self.radios_gruesos.remove(i)
    #                     elif self.distancias(self.lista_aridos, loc_x, loc_y, i):
    #                         self.lista_aridos.append(dato_arido)
    #                         self.lista_aridos_gruesos.append(dato_arido)
    #                         self.todos_aridos.append(arido)
    #                         self.todos_aridos_gruesos.append(arido)
    #                         self.radios_gruesos.remove(i)
    #         self.aridos_puestos = True
    #
    #     print('tengo tantos áridos ' + str(len(self.lista_aridos)))
    #     print(len(self.todos_aridos))
    #     print(len(self.radios_gruesos))
    #     self.progreso.emit(32)
    #     self.information.emit('Áridos gruesos colocados. ' + str(len(self.lista_aridos_gruesos)))
    #
    #     """luego coloco los áridos finos"""
    #     while len(self.radios_finos) > 0:
    #         i = self.radios_finos[0]
    #         loc_x = np.random.uniform(0, self.x)
    #         loc_y = np.random.uniform(0, self.y)
    #         dato_arido = [loc_x, loc_y, i]
    #         arido = plt.Circle((loc_x, loc_y), i, color='c')
    #         if self.poros_puestos == False:
    #             if loc_x + i < self.x and loc_x - i > 0 and loc_y + i < self.y and loc_y - i > 0:
    #                 if len(self.todos_aridos) == 0:
    #                     self.lista_aridos.append(dato_arido)
    #                     self.lista_aridos_finos.append(dato_arido)
    #                     self.todos_aridos.append(arido)
    #                     self.todos_aridos_finos.append(arido)
    #                     self.radios_finos.remove(i)
    #                 elif self.distancias(self.lista_aridos, loc_x, loc_y, i):
    #                     self.lista_aridos.append(dato_arido)
    #                     self.lista_aridos_finos.append(dato_arido)
    #                     self.todos_aridos.append(arido)
    #                     self.todos_aridos_finos.append(arido)
    #                     self.radios_finos.remove(i)
    #         else:
    #             if loc_x + i < self.x and loc_x - i > 0 and loc_y + i < self.y and loc_y - i > 0:
    #                 if self.distancias(self.lista_poros, loc_x, loc_y, i):
    #                     if len(self.todos_aridos) == 0:
    #                         self.lista_aridos.append(dato_arido)
    #                         self.lista_aridos_finos.append(dato_arido)
    #                         self.todos_aridos.append(arido)
    #                         self.todos_aridos_finos.append(arido)
    #                         self.radios_finos.remove(i)
    #                     elif self.distancias(self.lista_aridos, loc_x, loc_y, i):
    #                         self.lista_aridos.append(dato_arido)
    #                         self.lista_aridos_finos.append(dato_arido)
    #                         self.todos_aridos.append(arido)
    #                         self.todos_aridos_finos.append(arido)
    #                         self.radios_finos.remove(i)
    #         self.aridos_puestos = True
    #
    #     print('tengo tantos áridos ' + str(len(self.lista_aridos)))
    #     print(len(self.todos_aridos))
    #     print(len(self.radios_gruesos))
    #     self.progreso.emit(30)
    #     self.information.emit('Áridos finos colocados. ' + str(len(self.lista_aridos_finos)))

    def colocar_aridos_finos_y_gruesos(self):
        def dentro_de_limites(x, y, r):
            """Verifica que el árido esté completamente dentro del dominio"""
            return r < x < self.x - r and r < y < self.y - r

        def intentar_colocar_arido(x, y, r, lista_existente, poros_puestos):
            if not dentro_de_limites(x, y, r):
                return False
            if poros_puestos and not self.distancias(self.lista_poros, x, y, r):
                return False
            if lista_existente and not self.distancias(lista_existente, x, y, r):
                return False
            return True

        def colocar(lista_radios, lista_datos, lista_circulos, color, progreso_val, mensaje):
            while lista_radios:
                r = lista_radios[0]
                x = np.random.uniform(0, self.x)
                y = np.random.uniform(0, self.y)
                if intentar_colocar_arido(x, y, r, self.lista_aridos, self.poros_puestos):
                    dato = [x, y, r]
                    self.lista_aridos.append(dato)
                    lista_datos.append(dato)
                    circulo = plt.Circle((x, y), r, color=color)
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
            color='b',
            progreso_val=30,
            mensaje='Áridos gruesos'
        )

        # Colocar áridos finos
        colocar(
            lista_radios=self.radios_finos,
            lista_datos=self.lista_aridos_finos,
            lista_circulos=self.todos_aridos_finos,
            color='c',
            progreso_val=32,
            mensaje='Áridos finos'
        )

    def calcular_puntos_sin_extrafinos(self):
        """puntos sobre áridos gruesos"""
        if self.check_puntos_aridos:
            if self.Ppto_react_aridos:
                self.A_puntos_aridos = self.Ppto_react_aridos * self.A
                while self.A_puntos_aridos > np.pi * (self.dpto_min_aridos / 2) ** 2:
                    if self.dpto_min_aridos == self.dpto_max_aridos:
                        rpunto = self.dpto_min_aridos /2
                    else:
                        rpunto = (self.dpto_min_aridos + np.random.random() *
                                    (self.dpto_max_aridos - self.dpto_min_aridos)) / 2
                    Apunto = np.pi * (rpunto) ** 2
                    self.A_puntos_aridos = self.A_puntos_aridos - Apunto
                    self.radios_puntos.append(rpunto)  # ¿sobra?
                    self.radios_puntos_aridos.append(rpunto)
            self.progreso.emit(55)
            self.information.emit('Puntos reactivos sobre los áridos calculados')

        """puntos sobre los finos (y pasta)"""
        if self.check_puntos_pasta:
            if self.Ppto_react_pasta:
                self.A_puntos_pasta = self.Ppto_react_pasta * self.A
                while self.A_puntos_pasta > np.pi * (self.dpto_min_pasta / 2) ** 2:
                    if self.dpto_min_pasta == self.dpto_max_pasta:
                        rpunto = self.dpto_min_pasta / 2
                    else:
                        rpunto = (self.dpto_min_pasta + np.random.random() * (
                                    self.dpto_max_pasta - self.dpto_min_pasta)) / 2
                    Apunto = np.pi * (rpunto) ** 2
                    self.A_puntos_pasta = self.A_puntos_pasta - Apunto
                    self.radios_puntos.append(rpunto)  # ¿sobra?
                    self.radios_puntos_pasta.append(rpunto)
            self.progreso.emit(60)
            self.information.emit('Puntos reactivos sobre la pasta calculados')

    def colocar_puntos_sin_extrafinos(self):
            def dentro_de_limites(x, y, r):
                """equivalente a if loc_pto_x + r < self.x and loc_pto_x - r > 0
                and loc_pto_y + r < self.y and loc_pto_y - r > 0:
                pero más legible"""
                return r < x < self.x - r and r < y < self.y - r

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
                    x = np.random.uniform(0, self.x)
                    y = np.random.uniform(0, self.y)
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
        figure, axes = plt.subplots()
        plt.axis("equal")
        axes.set_xlim(0, self.x)
        axes.set_ylim(0, self.y)

        """
        Añadir los parches como colecciones para acelerar el render
        """
        if self.todos_poros:
            poros_collection = PatchCollection(self.todos_poros, color='red')
            axes.add_collection(poros_collection)

        if self.todos_aridos_gruesos:
            aridos_collection = PatchCollection(self.todos_aridos_gruesos, color='b')
            axes.add_collection(aridos_collection)

        if self.todos_aridos_finos:
            aridos_collection = PatchCollection(self.todos_aridos_finos, color='c')
            axes.add_collection(aridos_collection)

        if self.todos_ptos_react:
            react_collection = PatchCollection(self.todos_ptos_react, color='y')
            axes.add_collection(react_collection)

        """Añadir la probeta (el contorno del dominio)"""
        if self.x and self.y:
            probeta = plt.Rectangle((0, 0), self.x, self.y, color='black', fill=False)
            axes.add_patch(probeta)
            axes.autoscale_view()

        """Convertir la figura a QPixmap"""
        canvas = FigureCanvas(figure)
        self.pixmap = canvas.grab()

        """Emitir las señales"""
        self.imagen.emit(self.pixmap)
        self.pore_list.emit(self.lista_poros)
        self.coarse_list.emit(self.lista_aridos_gruesos)
        self.fine_list.emit(self.lista_aridos_finos)
        self.reactive_list.emit(self.lista_ptos_react)
        self.finished.emit()

    def simular(self):

        print('empieza la simulacion')
        print('está todo correcto? ' + str(self.todo_correcto))
        # self.todo_correcto = False
        if self.todo_correcto:
            print('todo correcto')
            self.dosificacion_sin_extrafinos()
            self.calcular_areas_aridos_sin_extrafinos()
            self.calcular_aridos_por_area_gruesos()
            self.calcular_aridos_por_area_finos()
            # self.calcular_aridos_por_area()
            self.colocar_aridos_finos_y_gruesos()

            if self.check_poros:
                self.calcular_poros()
                self.colocar_poros()
            if self.check_puntos:
                self.calcular_puntos_sin_extrafinos()
                self.colocar_puntos_sin_extrafinos()
            self.plotear_resultados()
        else:
            self.information_error.emit('--error grave')
