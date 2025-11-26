

import json
from Main03 import Ui_MainWindow
from Main_inicio import Ui_MainWindow as Menuinicio
from GV import MiGraphicsView
from PyQt5.QtGui import QColor
from PyQt5.QtCore import pyqtSignal, QObject, QThread, QFileInfo, Qt, QDate, QPropertyAnimation, QPointF
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog, QTableWidget, QTableWidgetItem, QVBoxLayout
import sys
import numpy as np
import matplotlib.pyplot as plt
from PyQt5 import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from dialog_GV import Ui_Dialog_GV
import time
import ezdxf

# from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QAction, QTableWidget, QTableWidgetItem
# from PyQt5.QtGui import QIcon, QPixmap
# from PyQt5.QtCore import pyqtSlot
# import sys
# import io
# from PIL import Image

class Worker (QObject):
    finished = pyqtSignal()
    imagen = pyqtSignal(object)

    def __init__(self, x, y, lista1, lista2, lista3):
        QObject.__init__(self)
        self.x = x
        self.y = y
        self.todos_poros = lista1
        self.todos_aridos = lista2
        self.todos_ptos_react = lista3

    def plotear_resultados(self):
        figure, axes = plt.subplots()
        plt.axis("equal")
        axes.set_xlim(0, self.x)
        axes.set_ylim(0, self.y)

        for i in self.todos_poros:
            axes.add_patch(i)

        for i in self.todos_aridos:
            axes.add_patch(i)

        for i in self.todos_ptos_react:
            axes.add_patch(i)

        if self.x and self.y:
            probeta = plt.Rectangle((0, 0), self.x, self.y, color='black', fill=False)
            axes.add_patch(probeta)
            axes.autoscale_view()

        canvas = FigureCanvas(figure)
        self.pixmap = canvas.grab()

        """
        mandar el self.pixmap a la clase principal para plotearlo
        """
        self.imagen.emit(self.pixmap)
        self.finished.emit()


class Selector(QtWidgets.QMainWindow, Menuinicio):
    def __init__(self):
        super(Selector, self).__init__()

        self.setupUi(self)
        self.pb_circulos.clicked.connect(self.pb_circulos_pulsar)
        # self.graph = Graph(self)

        # just to see the two windows side-by-side
        # self.move(500, 400)
        # self.graph.move(self.x()+self.width()+20, self.y())

    def pb_circulos_pulsar(self):
        print('pb clicked')
        self.close()
        self.circulos = mainProgram()
        self.circulos.show()


class About(QtWidgets.QLabel):
    def __init__(self):
        QtWidgets.QLabel.__init__(self,
                                  "Meso2D 1.0\n\nPor Servando Chinchón Payá, 2022\n\nPor favor no dude en comentar cualquier sugerencia\n\nservando@ietcc.csic.es\n\n¡Gracias!")
        self.setAlignment(QtCore.Qt.AlignCenter)

    def initUI(self):
        self.center()

    def center(self):
        qr = self.frameGeometry()
        cp = app.desktop().availableGeometry().centre()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


class mainProgram(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(mainProgram, self).__init__()
        self.setupUi(self)

        # self.gv_visor = MiGraphicsView()
        # # self.gv_visor.setEnabled(False)
        # self.gv_visor.setObjectName("gv_visor")
        # self.gridLayout.addWidget(self.gv_visor, 0, 0, 1, 2)
        # # self.verticalLayout_2.addWidget(self.gv_visor)

        self.dlg = Visor_imagen()
        self.dlg.setModal(True)

        self.a_Acerca.triggered.connect(self.sobre_programa)
        self.a_Salir.triggered.connect(self.close_application)
        self.a_Abrir.triggered.connect(self.abrir_proyecto)
        # self.a_Abrir.triggered.connect(self.cargar_ejemplo)
        self.a_CargarE.triggered.connect(self.cargar_ejemplo)
        self.a_GuardarP.triggered.connect(self.guardar_proyecto)
        self.a_Nuevo.triggered.connect(self.nuevo_proyecto)
        self.a_Estructura.triggered.connect(self.exportar_estructura)
        self.a_GuardarI.triggered.connect(self.guardar_imagen)

        # self.pb_ejecutar.clicked.connect(self.calcular_poros)
        self.pb_ejecutar.clicked.connect(self.ejecutar)
        self.pb_anyadir.clicked.connect(self.actualizar)
        self.pb_ver_estructura.clicked.connect(self.ver_estructura)

        self.cb_poros.toggled.connect(self.habilitar)
        self.cb_puntos.toggled.connect(self.habilitar)
        self.cb_puntos_aridos.toggled.connect(self.habilitar)
        self.cb_puntos_pasta.toggled.connect(self.habilitar)
        self.cb_semilla.toggled.connect(self.habilitar)

        # self.data = data
        # self.llenar_datos_tabla_dosif()
        self.tabla_dosif.setColumnCount(2)
        self.tabla_dosif.setRowCount(0)
        self.tabla_dosif.setHorizontalHeaderLabels(["sieve_size", "tpp"])
        self.tabla_dosif.resizeRowsToContents()
        self.tabla_dosif.resizeColumnsToContents()

        """
        Variables que declara el usuario
        """
        # self.sieve_size = [19.00, 12.70, 9.50, 4.75, 2.36]
        # self.tpp = [100, 97, 61, 10, 1.4]
        #
        # self.x = 75
        # self.y = 75
        # self.Pagg = 0.5
        # self.Pporos = 0.02
        # self.dporo_min = 2
        # self.dporo_max = 4
        # self.r_react = 0.05
        # self.dpto_max_aridos = 0.1
        # self.dpto_min_aridos = 0.1
        # self.dpto_max_pasta = 0.1
        # self.dpto_min_pasta = 0.1
        # self.Ppto_react_aridos = 0.002
        # self.Ppto_react_pasta = 0.002
        #
        # self.seed = None

        self.sieve_size = None  # tamaño de malla del tamiz?
        self.tpp = None # porcentaje acumulado de áridos que pasan por el correspondiente sieve_size

        self.x = None   # variable dimensión x de la probeta
        self.y = None   # variable dimensión y de la probeta
        self.Pagg = None    # coarse aggregate ratio
        self.Pporos = None  # porcentaje de poros
        self.dporo_min = None   # diámetro mínimo de los poros
        self.dporo_max = None   # diámetro máximo de los poros
        self.r_react = None # creo que no está en uso
        self.dpto_max_aridos = None # diámetro máximo de los ptos reactivos en los áridos
        self.dpto_min_aridos = None # diámetro mínimo de los ptos reactivos en los áridos
        self.dpto_max_pasta = None  # diámetro máximo de los ptos reactivos en la pasta
        self.dpto_min_pasta = None  # diámetro mínimo de los ptos reactivos en la pasta
        self.Ppto_react_aridos = None   # porcentaje de puntos reactivos en los áridos
        self.Ppto_react_pasta = None    # porcentaje de puntos reactivos en la pasta

        self.seed = None    # semilla para evitar el random y poder recuperar proyectos

        self.datos = None   # variable para necesaria para guardar/abrir proyectos

        """"
        Variables necesarias
        """

        # self.A = self.x * self.y
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

        self.aridos_puestos = False
        self.poros_puestos = False

        # self.A_poros = self.A * self.Pporos
        self.A_poros = None
        print('el Aporo es ' + str(self.A_poros))

        # self.A_puntos_total = (self.Ppto_react_aridos + self.Ppto_react_pasta) * self.A
        # self.A_puntos_aridos = self.Ppto_react_aridos * self.A
        self.A_puntos_aridos = None
        # self.A_puntos_pasta = self.Ppto_react_pasta * self.A
        self.A_puntos_pasta = None

        # self.actualizar_datos()
        # self. dlg_plotear = Plotear(self.todos_aridos, self.todos_poros, self.todos_ptos_react, self.x, self.y)

        self.existe_estructura = False

        self.redColor = QColor(255, 0, 0)
        self.blackColor = QColor(0, 0, 0)
        self.blueColor = QColor(0, 0, 255)

    def sobre_programa(self):
        self.pop = About()
        self.pop.resize(555, 333)
        self.pop.setWindowTitle("Sobre Meso2D")
        self.pop.show()

    def close_application(self):
        choice = QMessageBox.information(None, 'Información',
                                         "¿Estás seguro de que quieres salir?", QMessageBox.Yes | QMessageBox.No)
        if choice == QMessageBox.Yes:
            sys.exit()
        else:
            pass

    def llenar_datos_tabla_dosif(self):
        if self.sieve_size and self.tpp:
            n = 0
            self.tabla_dosif.setRowCount(len(self.sieve_size))
            for item in self.sieve_size:
                self.tabla_dosif.setItem(n, 0, QTableWidgetItem(str(int(item))))
                n += 1
            m = 0
            for item in self.tpp:
                self.tabla_dosif.setItem(m, 1, QTableWidgetItem(str(int(item))))
                m += 1
            self.tabla_dosif.resizeRowsToContents()
            self.tabla_dosif.resizeColumnsToContents()
        else:
            self.tabla_dosif.clear()
            self.tabla_dosif.setHorizontalHeaderLabels(["sieve_size", "tpp"])
            self.tabla_dosif.setRowCount(0)

    def abrir_proyecto(self):
        if self.datos:
            print("hay datos")
            choice = QMessageBox.information(None, 'Información',
                                             "¿Quieres borrar el proyecto actual y abrir uno anterior?", QMessageBox.Ok | QMessageBox.No)
            if choice == QMessageBox.Ok:
                self.variables_limpias()
                self.abrir()
            else:
                pass
        if not self.datos:
            self.abrir()

    def abrir(self):
        name, _ = QtWidgets.QFileDialog.getOpenFileName(None, 'Abrir proyecto', '*.txt')
        if name == "":
            return
        with open(name) as f:
            data = f.read()
            self.js = json.loads(data)
            f.close()
        self.actualizar_datos(self.js)
        self.llenar_datos()
        self.informar('---PROYECTO IMPORTADO---', color=self.blueColor)

    def variables_limpias(self):
        self.sieve_size = None  # tamaño de malla del tamiz?
        self.tpp = None # porcentaje acumulado de áridos que pasan por el correspondiente sieve_size

        self.x = None   # variable dimensión x de la probeta
        self.y = None   # variable dimensión y de la probeta
        self.Pagg = None    # coarse aggregate ratio
        self.Pporos = None  # porcentaje de poros
        self.dporo_min = None   # diámetro mínimo de los poros
        self.dporo_max = None   # diámetro máximo de los poros
        self.r_react = None # creo que no está en uso
        self.dpto_max_aridos = None # diámetro máximo de los ptos reactivos en los áridos
        self.dpto_min_aridos = None # diámetro mínimo de los ptos reactivos en los áridos
        self.dpto_max_pasta = None  # diámetro máximo de los ptos reactivos en la pasta
        self.dpto_min_pasta = None  # diámetro mínimo de los ptos reactivos en la pasta
        self.Ppto_react_aridos = None   # porcentaje de puntos reactivos en los áridos
        self.Ppto_react_pasta = None    # porcentaje de puntos reactivos en la pasta

        self.seed = None    # semilla para evitar el random y poder recuperar proyectos

        self.datos = None   # variable para necesaria para guardar/abrir proyectos

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

        self.aridos_puestos = False
        self.poros_puestos = False

        self.A_poros = None
        self.A_puntos_aridos = None
        self.A_puntos_pasta = None

        self.existe_estructura = False

    def nuevo_proyecto(self):
        if self.datos:
            print("hay datos")
            choice = QMessageBox.information(None, 'Información',
                                             "¿Quieres borrar el proyecto actual y empezar uno nuevo?", QMessageBox.Ok | QMessageBox.No)
            if choice == QMessageBox.Ok:
                self.variables_limpias()
                self.llenar_datos()
            else:
                pass
        self.informar('---NUEVO EJEMPLO---', color=self.blueColor)

    def cargar_ejemplo(self):
        with open('proyecto_ejemplo.txt') as f:
            data = f.read()
            js = json.loads(data)
            self.actualizar_datos(js)
            self.llenar_datos()
            f.close()
        self.informar('---EJEMPLO IMPORTADO---', color=self.blueColor)

    """
    Pasar los datos de las variables de cálculo al entorno gráfico
    """
    def llenar_datos(self):
        """chequear primero qué datos hay para no meter cosas de más"""
        if self.seed:
            self.cb_semilla.setChecked(True)
            self.le_semilla.setText(str(self.seed))
        else:
            self.cb_semilla.setChecked(False)
            self.le_semilla.setText("")

        if self.Pporos or self.dporo_min or self.dporo_max:
            self.cb_poros.setChecked(True)
        if self.dpto_min_aridos or self.dpto_max_aridos or self.Ppto_react_aridos\
                or self.dpto_min_pasta or self.dpto_max_pasta or self.Ppto_react_pasta:
            self.cb_puntos.setChecked(True)
        if self.dpto_min_aridos or self.dpto_max_aridos or self.Ppto_react_aridos:
            self.cb_puntos_aridos.setChecked(True)
        if self.dpto_min_pasta or self.dpto_max_pasta or self.Ppto_react_pasta:
            self.cb_puntos_pasta.setChecked(True)

        if self.x:
            self.le_x.setText(str(self.x))
        else:
            self.le_x.setText("")
        if self.y:
            self.le_y.setText(str(self.y))
        else:
            self.le_y.setText("")

        if self.Pagg:
            self.dsb_coef_f.setValue(self.Pagg)
        else:
            self.dsb_coef_f.setValue(0.25)

        if self.dporo_min:
            self.le_dmin.setText(str(self.dporo_min))
        else:
            self.le_dmin.setText("")
        if self.dporo_max:
            self.le_dmax.setText(str(self.dporo_max))
        else:
            self.le_dmax.setText("")
        if self.Pporos:
            self.le_Pporos.setText(str(self.Pporos))
        else:
            self.le_Pporos.setText("")

        if self.dpto_min_pasta:
            self.le_dmin_ptos_pasta.setText(str(self.dpto_min_pasta))
        else:
            self.le_dmin_ptos_pasta.setText("")
        if self.dpto_max_pasta:
            self.le_dmax_ptos_pasta.setText(str(self.dpto_max_pasta))
        else:
            self.le_dmax_ptos_pasta.setText("")
        if self.Ppto_react_pasta:
            self.le_Pptos_pasta.setText(str(self.Ppto_react_pasta))
        else:
            self.le_Pptos_pasta.setText("")

        if self.dpto_min_aridos:
            self.le_dmin_ptos_aridos.setText(str(self.dpto_min_aridos))
        else:
            self.le_dmin_ptos_aridos.setText("")
        if self.dpto_max_aridos:
            self.le_dmax_ptos_aridos.setText(str(self.dpto_max_aridos))
        else:
            self.le_dmax_ptos_aridos.setText("")
        if self.Ppto_react_aridos:
            self.le_Pptos_aridos.setText(str(self.Ppto_react_aridos))
        else:
            self.le_Pptos_aridos.setText("")

        self.llenar_datos_tabla_dosif()

    """
    Pasar datos del diccionario (Importar proyecto) a las variables de cálculo
    """
    def actualizar_datos(self, diccionario):
        self.datos = ["sieve_size", "tpp", "x", "y", "Pagg", "Pporos", "dporo_min", "dporo_max", "r_react", "dpto_max_aridos",
                 "dpto_min_aridos", "dpto_max_pasta", "dpto_min_pasta", "Ppto_react_aridos", "Ppto_react_pasta", "seed"]
        for n in self.datos:
            if n in diccionario:
                setattr(self, str(n), diccionario[n])
            else:
                setattr(self, str(n), "")

    def guardar_proyecto(self):
        """import json

        details = {'Name': "Bob", 'Age' :28}

        with open('convert.txt', 'w') as convert_file:
            convert_file.write(json.dumps(details))"""

        self.proyecto = {"sieve_size": self.sieve_size,
                        "tpp": self.tpp,
                        "x": self.x,
                        "y": self.y,
                        "Pagg": self.Pagg,
                        "Pporos": self.Pporos,
                        "dporo_min": self.dporo_min,
                        "dporo_max": self.dporo_max,
                        "r_react": self.r_react,
                        "dpto_max_aridos": self.dpto_max_aridos,
                        "dpto_min_aridos": self.dpto_min_aridos,
                        "dpto_max_pasta": self.dpto_max_pasta,
                        "dpto_min_pasta": self.dpto_min_pasta,
                        "Ppto_react_aridos": self.Ppto_react_aridos,
                        "Ppto_react_pasta": self.Ppto_react_pasta,
                        "seed": self.seed}

        name, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Guardar Proyecto", "", "TXT(*.txt)")
        if name == "":
            return
        if "." not in name:
            name += ".txt"
        with open(name, 'w') as archivo:
            archivo.write(json.dumps(self.proyecto))
        self.informar('---PROYECTO GUARDADO---', color=self.blueColor)

    """
    función para calcular distancias euclideas de un elemento x1 con todos los pertenecientes a una lista (x2 en Y)
    """
    def distancias(self, lista, coor_x, coor_y, radio):
        contador = 0
        for n in lista:
            dist = np.sqrt((coor_x - n[0]) ** 2 + (coor_y - n[1]) ** 2)
            if dist > radio + n[2]:
                contador += 1
            if contador == len(lista):
                return True

    def distancias_aridos_ptos(self, lista, coor_x, coor_y, radio):
        """intento de acelerar el algoritmo"""
        # contador = 0
        for n in lista:
            dist = np.sqrt((coor_x - n[0]) ** 2 + (coor_y - n[1]) ** 2)
            if dist < radio + n[2]:
                # contador += 1
            # if contador == len(lista):
                return True

    """
    calcular y colocar los poros
    """
    def calcular_poros(self):
        self.A_poros = self.A * self.Pporos
        while self.A_poros > np.pi * (self.dporo_min / 2) ** 2:
            rporo = (self.dporo_min + np.random.random() * (self.dporo_max - self.dporo_min)) / 2
            Aporo = np.pi * (rporo) ** 2
            self.A_poros = self.A_poros - Aporo
            self.radios_poros.append(rporo)
        self.progressBar.setValue(40)
        self.informar('Poros calculados. ' + str(len(self.radios_poros)) + ' Poros', color=self.blackColor)
        # self.informar('...', color=self.blackColor)

    def colocar_poros(self):
        while len(self.radios_poros) > 0:
            r = self.radios_poros[0]
            loc_poro_x = np.random.uniform(0, self.x)
            loc_poro_y = np.random.uniform(0, self.y)
            dato_poro = [loc_poro_x, loc_poro_y, r]
            poro = plt.Circle((loc_poro_x, loc_poro_y), r, color='r')
            if self.aridos_puestos == False:
                if loc_poro_x + r < self.x and loc_poro_x - r > 0 and loc_poro_y + r < self.y and loc_poro_y - r > 0:
                    if len(self.lista_poros) == 0:
                        self.lista_poros.append(dato_poro)
                        self.todos_poros.append(poro)
                        self.radios_poros.remove(r)
                    elif self.distancias(self.lista_poros, loc_poro_x, loc_poro_y, r):
                        self.lista_poros.append(dato_poro)
                        self.todos_poros.append(poro)
                        self.radios_poros.remove(r)
            else:
                if loc_poro_x + r < self.x and loc_poro_x - r > 0 and loc_poro_y + r < self.y and loc_poro_y - r > 0:
                    if self.distancias(self.lista_aridos, loc_poro_x, loc_poro_y, r):
                        if len(self.lista_poros) == 0:
                            self.lista_poros.append(dato_poro)
                            self.todos_poros.append(poro)
                            self.radios_poros.remove(r)
                        elif self.distancias(self.lista_poros, loc_poro_x, loc_poro_y, r):
                            self.lista_poros.append(dato_poro)
                            self.todos_poros.append(poro)
                            self.radios_poros.remove(r)
            self.poros_puestos = True

        print(len(self.lista_poros))
        print(self.A_poros)
        self.progressBar.setValue(50)
        self.informar('Poros colocados', color=self.blackColor)
        # self.informar('...', color=self.blackColor)

    def calcular_areas_aridos(self):
        print(self.x, self.y, self.A)

        self.A = self.x * self.y
        i = 0
        while i + 1 < len(self.sieve_size):
            area_intervalo = ((self.tpp[i] - self.tpp[i + 1]) / (self.tpp[0] - self.tpp[-1])) * self.Pagg * self.A
            self.Aagg.append(round(area_intervalo))
            i = i + 1
        print(self.Aagg)
        self.progressBar.setValue(10)
        self.informar('Área de cada fracción de áridos calculada. ' + str(self.Aagg), color=self.blackColor)
        # self.informar('...', color=self.blackColor)

    def calcular_aridos_por_area(self):
        j = 0
        while j < len(self.Aagg):
            num_particulas = 0
            print(self.Aagg[j])
            area_c = 0
            self.Aagg[j] = self.Aagg[j] + self.A_remanente
            print(self.Aagg[j])
            while self.Aagg[j] - area_c > np.pi * (self.sieve_size[j + 1] / 2) ** 2:
                d = self.sieve_size[j + 1] + np.random.rand() * (self.sieve_size[j] - self.sieve_size[j + 1])
                area = np.pi * (d / 2) ** 2
                if area + area_c < self.Aagg[j]:
                    area_c = area_c + area
                    self.radios.append(d / 2)
                    num_particulas = num_particulas + 1
                self.A_remanente = self.Aagg[j] - area_c
            print(self.A_remanente)
            print(num_particulas)
            self.particulas.append(num_particulas)
            if j < len(self.Aagg):
                j += 1
        print(j)
        print(self.particulas)
        # print(radios)
        print(len(self.radios))
        self.progressBar.setValue(20)
        self.informar(mensaje='Áridos por área calculados. ' + str(self.particulas), color=self.blackColor)
        # self.informar('...', color=self.blackColor)

    def colocar_aridos(self):
        while len(self.radios) > 0:
            i = self.radios[0]
            loc_x = np.random.uniform(0, self.x)
            loc_y = np.random.uniform(0, self.y)
            dato_arido = [loc_x, loc_y, i]
            arido = plt.Circle((loc_x, loc_y), i)
            if self.poros_puestos == False:
                if loc_x + i < self.x and loc_x - i > 0 and loc_y + i < self.y and loc_y - i > 0:
                    if len(self.todos_aridos) == 0:
                        self.lista_aridos.append(dato_arido)
                        self.todos_aridos.append(arido)
                        self.radios.remove(i)
                    elif self.distancias(self.lista_aridos, loc_x, loc_y, i):
                        self.lista_aridos.append(dato_arido)
                        self.todos_aridos.append(arido)
                        self.radios.remove(i)
            else:
                if loc_x + i < self.x and loc_x - i > 0 and loc_y + i < self.y and loc_y - i > 0:
                    if self.distancias(self.lista_poros, loc_x, loc_y, i):
                        if len(self.todos_aridos) == 0:
                            self.lista_aridos.append(dato_arido)
                            self.todos_aridos.append(arido)
                            self.radios.remove(i)
                        elif self.distancias(self.lista_aridos, loc_x, loc_y, i):
                            self.lista_aridos.append(dato_arido)
                            self.todos_aridos.append(arido)
                            self.radios.remove(i)
            self.aridos_puestos = True

        print(len(self.lista_aridos))
        print(len(self.todos_aridos))
        print(len(self.radios))
        self.progressBar.setValue(30)
        self.informar('Áridos colocados', color=self.blackColor)
        # self.informar('...', color=self.blackColor)

    def calcular_puntos(self):
        """puntos sobre áridos"""
        if self.cb_puntos_aridos.isChecked():
            if self.Ppto_react_aridos:
                self.A_puntos_aridos = self.Ppto_react_aridos * self.A
                while self.A_puntos_aridos > np.pi * (self.dpto_min_aridos / 2) ** 2:
                    if self.dpto_min_aridos == self.dpto_max_aridos:
                        rpunto = self.dpto_min_aridos/2
                    else:
                        rpunto = (self.dpto_min_aridos + np.random.random() * (self.dpto_max_aridos - self.dpto_min_aridos)) / 2
                    Apunto = np.pi * (rpunto) ** 2
                    self.A_puntos_aridos = self.A_puntos_aridos - Apunto
                    self.radios_puntos.append(rpunto)   #¿sobra?
                    self.radios_puntos_aridos.append(rpunto)
        else:
            pass
        self.progressBar.setValue(55)
        self.informar('Puntos reactivos sobre los áridos calculados', color=self.blackColor)
        # self.informar('...', color=self.blackColor)

        """puntos sobre pasta"""
        if self.cb_puntos_pasta.isChecked():
            if self.Ppto_react_pasta:
                self.A_puntos_pasta = self.Ppto_react_pasta * self.A
                while self.A_puntos_pasta > np.pi * (self.dpto_min_pasta / 2) ** 2:
                    if self.dpto_min_pasta == self.dpto_max_pasta:
                        rpunto = self.dpto_min_pasta/2
                    else:
                        rpunto = (self.dpto_min_pasta + np.random.random() * (self.dpto_max_pasta - self.dpto_min_pasta)) / 2
                    Apunto = np.pi * (rpunto) ** 2
                    self.A_puntos_pasta = self.A_puntos_pasta - Apunto
                    self.radios_puntos.append(rpunto)   #¿sobra?
                    self.radios_puntos_pasta.append(rpunto)
        else:
            pass
        self.progressBar.setValue(60)
        self.informar('Puntos reactivos sobre la pasta calculados', color=self.blackColor)
        # self.informar('...', color=self.blackColor)

    def colocar_puntos_funciona(self):
        """puntos sobre áridos"""
        while len(self.radios_puntos_aridos) > 0:
            r = self.radios_puntos_aridos[0]
            loc_pto_x = np.random.uniform(0, self.x)
            loc_pto_y = np.random.uniform(0, self.y)
            dato_pto = [loc_pto_x, loc_pto_y, r]
            punto_react = plt.Circle((loc_pto_x, loc_pto_y), r, color='y')
            if self.poros_puestos:
                if loc_pto_x + r < self.x and loc_pto_x - r > 0 and loc_pto_y + r < self.y and loc_pto_y - r > 0:
                    if self.distancias(self.lista_poros, loc_pto_x, loc_pto_y, r):
                        if not self.distancias(self.lista_aridos, loc_pto_x, loc_pto_y, r):
                            if len(self.lista_ptos_react_aridos) == 0:
                                self.lista_ptos_react_aridos.append(dato_pto)
                                self.todos_ptos_react.append(punto_react)
                                self.radios_puntos_aridos.remove(r)
                            elif self.distancias(self.lista_ptos_react_aridos, loc_pto_x, loc_pto_y, r):
                                self.lista_ptos_react_aridos.append(dato_pto)
                                self.todos_ptos_react.append(punto_react)
                                self.radios_puntos_aridos.remove(r)
            if not self.poros_puestos:
                if loc_pto_x + r < self.x and loc_pto_x - r > 0 and loc_pto_y + r < self.y and loc_pto_y - r > 0:
                    if not self.distancias(self.lista_aridos, loc_pto_x, loc_pto_y, r):
                        if len(self.lista_ptos_react_aridos) == 0:
                            self.lista_ptos_react_aridos.append(dato_pto)
                            self.todos_ptos_react.append(punto_react)
                            self.radios_puntos_aridos.remove(r)
                        elif self.distancias(self.lista_ptos_react_aridos, loc_pto_x, loc_pto_y, r):
                            self.lista_ptos_react_aridos.append(dato_pto)
                            self.todos_ptos_react.append(punto_react)
                            self.radios_puntos_aridos.remove(r)
        self.informar('Puntos reactivos sobre los áridos colocados', color=self.blackColor)
        # self.informar('...', color=self.blackColor)

        """colocar sobre pasta"""
        while len(self.radios_puntos_pasta) > 0:
            r = self.radios_puntos_pasta[0]
            loc_pto_x = np.random.uniform(0, self.x)
            loc_pto_y = np.random.uniform(0, self.y)
            dato_pto = [loc_pto_x, loc_pto_y, r]
            punto_react = plt.Circle((loc_pto_x, loc_pto_y), r, color='y')
            if self.poros_puestos:
                if loc_pto_x + r < self.x and loc_pto_x - r > 0 and loc_pto_y + r < self.y and loc_pto_y - r > 0:
                    if self.distancias(self.lista_poros, loc_pto_x, loc_pto_y, r):
                        if self.distancias(self.lista_aridos, loc_pto_x, loc_pto_y, r):
                            if len(self.lista_ptos_react_pasta) == 0:
                                self.lista_ptos_react_pasta.append(dato_pto)
                                self.todos_ptos_react.append(punto_react)
                                self.radios_puntos_pasta.remove(r)
                            elif self.distancias(self.lista_ptos_react_pasta, loc_pto_x, loc_pto_y, r):
                                self.lista_ptos_react_pasta.append(dato_pto)
                                self.todos_ptos_react.append(punto_react)
                                self.radios_puntos_pasta.remove(r)
            if not self.poros_puestos:
                if loc_pto_x + r < self.x and loc_pto_x - r > 0 and loc_pto_y + r < self.y and loc_pto_y - r > 0:
                    if self.distancias(self.lista_aridos, loc_pto_x, loc_pto_y, r):
                        if len(self.lista_ptos_react_pasta) == 0:
                            self.lista_ptos_react_pasta.append(dato_pto)
                            self.todos_ptos_react.append(punto_react)
                            self.radios_puntos_pasta.remove(r)
                        elif self.distancias(self.lista_ptos_react_pasta, loc_pto_x, loc_pto_y, r):
                            self.lista_ptos_react_pasta.append(dato_pto)
                            self.todos_ptos_react.append(punto_react)
                            self.radios_puntos_pasta.remove(r)
        self.progressBar.setValue(70)
        self.informar('Puntos reactivos sobre la pasta colocados', color=self.blackColor)
        # self.informar('...', color=self.blackColor)

    def colocar_puntos(self):
        """puntos sobre áridos"""
        while len(self.radios_puntos_aridos) > 0:
            r = self.radios_puntos_aridos[0]
            loc_pto_x = np.random.uniform(0, self.x)
            loc_pto_y = np.random.uniform(0, self.y)
            dato_pto = [loc_pto_x, loc_pto_y, r]
            punto_react = plt.Circle((loc_pto_x, loc_pto_y), r, color='y')
            if self.poros_puestos:
                if loc_pto_x + r < self.x and loc_pto_x - r > 0 and loc_pto_y + r < self.y and loc_pto_y - r > 0:
                    if self.distancias(self.lista_poros, loc_pto_x, loc_pto_y, r):
                        if self.distancias_aridos_ptos(self.lista_aridos, loc_pto_x, loc_pto_y, r):
                            if len(self.lista_ptos_react_aridos) == 0:
                                self.lista_ptos_react_aridos.append(dato_pto)
                                self.todos_ptos_react.append(punto_react)
                                self.radios_puntos_aridos.remove(r)
                            elif self.distancias(self.lista_ptos_react_aridos, loc_pto_x, loc_pto_y, r):
                                self.lista_ptos_react_aridos.append(dato_pto)
                                self.todos_ptos_react.append(punto_react)
                                self.radios_puntos_aridos.remove(r)
            if not self.poros_puestos:
                if loc_pto_x + r < self.x and loc_pto_x - r > 0 and loc_pto_y + r < self.y and loc_pto_y - r > 0:
                    if not self.distancias(self.lista_aridos, loc_pto_x, loc_pto_y, r):
                        if len(self.lista_ptos_react_aridos) == 0:
                            self.lista_ptos_react_aridos.append(dato_pto)
                            self.todos_ptos_react.append(punto_react)
                            self.radios_puntos_aridos.remove(r)
                        elif self.distancias(self.lista_ptos_react_aridos, loc_pto_x, loc_pto_y, r):
                            self.lista_ptos_react_aridos.append(dato_pto)
                            self.todos_ptos_react.append(punto_react)
                            self.radios_puntos_aridos.remove(r)
        self.progressBar.setValue(65)
        self.informar('Puntos reactivos sobre los áridos colocados', color=self.blackColor)
        # self.informar('...', color=self.blackColor)

        """colocar sobre pasta"""
        while len(self.radios_puntos_pasta) > 0:
            r = self.radios_puntos_pasta[0]
            loc_pto_x = np.random.uniform(0, self.x)
            loc_pto_y = np.random.uniform(0, self.y)
            dato_pto = [loc_pto_x, loc_pto_y, r]
            punto_react = plt.Circle((loc_pto_x, loc_pto_y), r, color='y')
            if self.poros_puestos:
                if loc_pto_x + r < self.x and loc_pto_x - r > 0 and loc_pto_y + r < self.y and loc_pto_y - r > 0:
                    if self.distancias(self.lista_poros, loc_pto_x, loc_pto_y, r):
                        if self.distancias(self.lista_aridos, loc_pto_x, loc_pto_y, r):
                            if len(self.lista_ptos_react_pasta) == 0:
                                self.lista_ptos_react_pasta.append(dato_pto)
                                self.todos_ptos_react.append(punto_react)
                                self.radios_puntos_pasta.remove(r)
                            elif self.distancias(self.lista_ptos_react_pasta, loc_pto_x, loc_pto_y, r):
                                self.lista_ptos_react_pasta.append(dato_pto)
                                self.todos_ptos_react.append(punto_react)
                                self.radios_puntos_pasta.remove(r)
            if not self.poros_puestos:
                if loc_pto_x + r < self.x and loc_pto_x - r > 0 and loc_pto_y + r < self.y and loc_pto_y - r > 0:
                    if self.distancias(self.lista_aridos, loc_pto_x, loc_pto_y, r):
                        if len(self.lista_ptos_react_pasta) == 0:
                            self.lista_ptos_react_pasta.append(dato_pto)
                            self.todos_ptos_react.append(punto_react)
                            self.radios_puntos_pasta.remove(r)
                        elif self.distancias(self.lista_ptos_react_pasta, loc_pto_x, loc_pto_y, r):
                            self.lista_ptos_react_pasta.append(dato_pto)
                            self.todos_ptos_react.append(punto_react)
                            self.radios_puntos_pasta.remove(r)
        self.progressBar.setValue(70)
        self.informar('Puntos reactivos sobre la pasta colocados', color=self.blackColor)
        # self.informar('...', color=self.blackColor)

    def plotear_resultados_preworker(self):

        # self.gv_visor.setEnabled(True)
        # self.lb_estructura.setEnabled(True)
        # figure, axes = plt.subplots(figsize=(4, 4))
        figure, axes = plt.subplots()
        # figure = plt.Figure()
        # axes = figure.gca()
        plt.axis("equal")
        axes.set_xlim(0, self.x)
        axes.set_ylim(0, self.y)

        for i in self.todos_poros:
            axes.add_patch(i)

        for i in self.todos_aridos:
            axes.add_patch(i)

        for i in self.todos_ptos_react:
            axes.add_patch(i)

        probeta = plt.Rectangle((0, 0), self.x, self.y, color='black', fill=False)
        axes.add_patch(probeta)
        axes.autoscale_view()

        canvas = FigureCanvas(figure)
        self.pixmap = canvas.grab()
        self.dlg.gv_visor.setPhoto(self.pixmap)

        self.dlg.show()
        self.progressBar.setValue(100)
        self.pb_ver_estructura.setEnabled(True)
        self.informar('* El tiempo necesario para la simulación ha sido ' + str(round(time.time() - self.start_time, 4)) + ' segundos', color=self.blackColor)
        self.informar('---FIN DE LA SIMULACIÓN---', color=self.blueColor)
        self.a_Estructura.setEnabled(True)
        self.a_GuardarI.setEnabled(True)

    def plotear_resultados(self):
        self.thread = QThread()
        self.worker = Worker(self.x, self.y, self.todos_poros, self.todos_aridos, self.todos_ptos_react)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.plotear_resultados)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.imagen.connect(self.plotear)
        self.thread.start()

        # self.pb_ejecutar.setEnabled(False)
        self.thread.finished.connect(
            lambda: self.pb_ejecutar.setEnabled(True)
        )

    def plotear(self, imagen):
        self.dlg.gv_visor.setPhoto(imagen)

        self.dlg.show()
        self.progressBar.setValue(100)
        self.pb_ver_estructura.setEnabled(True)
        self.informar('* El tiempo necesario para la simulación ha sido ' + str(round(time.time() - self.start_time, 4)) + ' segundos', color=self.blackColor)
        self.informar('---FIN DE LA SIMULACIÓN---', color=self.blueColor)
        self.a_Estructura.setEnabled(True)
        self.a_GuardarI.setEnabled(True)

    def ejecutar(self):
        if self.existe_estructura:
            choice = QMessageBox.information(None, 'Información',
                                             "¿Quieres borrar la estructura anterior?", QMessageBox.Ok | QMessageBox.No)
            if choice == QMessageBox.Ok:
                self.limpiar()
                self.actualizar()
                self.simular()
            else:
                # self.plotear_resultados()
                # self.replotear()
                pass
        if not self.existe_estructura:
            try:
                self.actualizar()
            except:
                self.informar('---ERROR: faltan datos imprescindibles para empezar la simulación', color=self.redColor)

            self.simular()
            self.existe_estructura = True

    def simular(self):
        if self.cb_semilla.isChecked():
            np.random.seed(self.seed)
        else:
            self.seed = np.random.randint(1000000)
            np.random.seed(self.seed)

        self.pb_ejecutar.setEnabled(False)

        self.start_time = time.time()

        # self.tb_info.setTextColor(self.redColor)
        self.informar('---COMIENZO DE LA SIMULACIÓN---', color=self.blueColor)
        self.informar('El valor de la semilla es ' + str(self.seed), color=self.blackColor)
        # self.tb_info.setTextColor(self.blackColor)
        try:
            self.calcular_areas_aridos()
        except:
            self.informar('---ERROR: no es posible calcular areas', color=self.redColor)
        self.calcular_aridos_por_area()
        self.colocar_aridos()
        if self.cb_poros.isChecked():
            self.calcular_poros()
            self.colocar_poros()
        if self.cb_puntos.isChecked():
            self.calcular_puntos()
            self.colocar_puntos()
            # self.calcular_colocar_puntos()
        self.plotear_resultados()
        print('la semilla es ')
        print(self.seed)

    """
    limpiar variables para ejecutar una nueva simulación
    """
    def limpiar(self):
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
        self.lista_ptos_react_pasta = []
        self.lista_ptos_react_aridos = []
        self.todos_ptos_react = []
        self.aridos_puestos = False
        self.poros_puestos = False
        if not self.cb_semilla.isChecked():
            self.le_semilla.clear()
            self.seed = None

    def actualizar(self):
        if self.le_semilla.text():
            self.seed = int(self.le_semilla.text())
        if self.le_y.text():
            self.y = float(self.le_y.text())
        if self.le_x.text():
            self.x = float(self.le_x.text())
        if self.le_dmax.text():
            self.dporo_max = float(self.le_dmax.text())
        if self.le_dmin.text():
            self.dporo_min = float(self.le_dmin.text())
        if self.le_Pporos.text():
            self.Pporos = float(self.le_Pporos.text())
        if self.le_dmax_ptos_aridos.text():
            self.dpto_max_aridos = float(self.le_dmax_ptos_aridos.text())
        if self.le_dmin_ptos_aridos.text():
            self.dpto_min_aridos = float(self.le_dmin_ptos_aridos.text())
        if self.le_Pptos_aridos.text():
            self.Ppto_react_aridos = float(self.le_Pptos_aridos.text())
        if self.le_dmax_ptos_pasta.text():
            self.dpto_max_pasta = float(self.le_dmax_ptos_pasta.text())
        if self.le_dmin_ptos_pasta.text():
            self.dpto_min_pasta = float(self.le_dmin_ptos_pasta.text())
        if self.le_Pptos_pasta.text():
            self.Ppto_react_pasta = float(self.le_Pptos_pasta.text())
        if self.dsb_coef_f.value():
            self.Pagg = self.dsb_coef_f.value()

        self.A = self.x * self.y
        self.A_poros = self.A * self.Pporos
        self.A_puntos_pasta = self.A * self.Ppto_react_pasta
        self.A_puntos_aridos = self.A * self.Ppto_react_aridos
        # self.A_puntos_total = self.A * (self.Ppto_react_pasta + self.Ppto_react_aridos)

    def habilitar(self):
        if self.cb_poros.isChecked():
            self.lb_poros.setEnabled(True)
            self.le_dmax.setEnabled(True)
            self.lb_dmax.setEnabled(True)
            self.le_dmin.setEnabled(True)
            self.lb_dmin.setEnabled(True)
            self.le_Pporos.setEnabled(True)
            self.lb_Pporos.setEnabled(True)
        if not self.cb_poros.isChecked():
            self.lb_poros.setEnabled(False)
            self.le_dmax.setEnabled(False)
            self.lb_dmax.setEnabled(False)
            self.le_dmin.setEnabled(False)
            self.lb_dmin.setEnabled(False)
            self.le_Pporos.setEnabled(False)
            self.lb_Pporos.setEnabled(False)

        if self.cb_puntos.isChecked():
            self.lb_puntos.setEnabled(True)
            self.lb_dmin_ptos.setEnabled(True)
            self.lb_dmax_ptos.setEnabled(True)
            self.lb_Pptos.setEnabled(True)
            self.cb_puntos_aridos.setEnabled(True)
            self.cb_puntos_pasta.setEnabled(True)
        if not self.cb_puntos.isChecked():
            self.lb_puntos.setEnabled(False)
            self.lb_dmin_ptos.setEnabled(False)
            self.lb_dmax_ptos.setEnabled(False)
            self.lb_Pptos.setEnabled(False)
            self.cb_puntos_aridos.setEnabled(False)
            self.cb_puntos_pasta.setEnabled(False)

            self.cb_puntos_aridos.setChecked(False)
            self.cb_puntos_pasta.setChecked(False)

        if self.cb_puntos_aridos.isChecked():
            self.lb_puntos_aridos.setEnabled(True)
            self.le_dmax_ptos_aridos.setEnabled(True)
            self.le_dmin_ptos_aridos.setEnabled(True)
            self.le_Pptos_aridos.setEnabled(True)
        if not self.cb_puntos_aridos.isChecked():
            self.lb_puntos_aridos.setEnabled(False)
            self.le_dmax_ptos_aridos.setEnabled(False)
            self.le_dmin_ptos_aridos.setEnabled(False)
            self.le_Pptos_aridos.setEnabled(False)

        if self.cb_puntos_pasta.isChecked():
            self.lb_puntos_pasta.setEnabled(True)
            self.le_dmax_ptos_pasta.setEnabled(True)
            self.le_dmin_ptos_pasta.setEnabled(True)
            self.le_Pptos_pasta.setEnabled(True)
        if not self.cb_puntos_pasta.isChecked():
            self.lb_puntos_pasta.setEnabled(False)
            self.le_dmax_ptos_pasta.setEnabled(False)
            self.le_dmin_ptos_pasta.setEnabled(False)
            self.le_Pptos_pasta.setEnabled(False)

        if self.cb_semilla.isChecked():
            self.lb_semilla.setEnabled(True)
            self.le_semilla.setEnabled(True)
        if not self.cb_semilla.isChecked():
            self.lb_semilla.setEnabled(False)
            self.le_semilla.setEnabled(False)

    def ver_estructura(self):
        self.dlg.show()

    """
    Exportar distribución de áridos, poros y puntos reactivos en dxf
    """
    def exportar_estructura(self):
        name, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Exportar Estructura", "", "DXF(*.dxf)")
        if name == "":
            return
        if "." not in name:
            name += ".dxf"
        doc = ezdxf.new()
        doc.layers.new(name='Poros')
        doc.layers.new(name='Aridos')
        doc.layers.new(name='Ptos_reactivos')
        msp = doc.modelspace()
        for i in self.lista_poros:
            msp.add_circle([i[0], i[1]], i[2], dxfattribs={'layer': 'Poros'})
        for i in self.lista_aridos:
            msp.add_circle([i[0], i[1]], i[2], dxfattribs={'layer': 'Aridos'})
        for i in self.lista_ptos_react:
            msp.add_circle([i[0], i[1]], i[2], dxfattribs={'layer': 'Ptos_reactivos'})

        doc.saveas(name)
        self.informar('---ESTRUCTURA EXPORTADA---', color=self.blueColor)

    """
    Guardar la imagen de la estructura desde el menú
    Se guarda completa, sin el zoom
    """
    def guardar_imagen(self):
        name, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Guardar Imagen", "", "PNG(*.png);;JPEG(*.jpg)")
        if name == "":
            return
        if "." not in name:
            name += ".png"
        # self.pixmap.save(name, dpi=600)
        pixmap = QtGui.QPixmap(self.dlg.gv_visor.viewport().size())
        self.dlg.gv_visor.viewport().render(pixmap)
        pixmap.save(name)

    # def informar(self, mensaje=None):
    def informar2(self, mensaje=None, color=None):
        # get the last line
        self.tb_info.moveCursor(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor)
        self.tb_info.moveCursor(QtGui.QTextCursor.StartOfLine, QtGui.QTextCursor.MoveAnchor)
        self.tb_info.moveCursor(QtGui.QTextCursor.End, QtGui.QTextCursor.KeepAnchor)
        ultimalinea = self.tb_info.textCursor().selectedText()

        if ultimalinea == '...':
            self.tb_info.textCursor().removeSelectedText()
            self.tb_info.textCursor().deletePreviousChar()
            self.tb_info.setTextColor(color)
            self.tb_info.append(mensaje)
        else:
            self.tb_info.setTextColor(color)
            self.tb_info.append(mensaje)
    def informar(self, mensaje=None, color=None):
        self.tb_info.setTextColor(color)
        self.tb_info.append(mensaje)

    def informar_QLabel(self, mensaje=None, color=None):
        # # get the last line
        # self.tb_info.moveCursor(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor)
        # self.tb_info.moveCursor(QtGui.QTextCursor.StartOfLine, QtGui.QTextCursor.MoveAnchor)
        # self.tb_info.moveCursor(QtGui.QTextCursor.End, QtGui.QTextCursor.KeepAnchor)
        # ultimalinea = self.tb_info.textCursor().selectedText()
        #
        # if ultimalinea == '...':
        #     self.tb_info.textCursor().removeSelectedText()
        #     self.tb_info.textCursor().deletePreviousChar()
        #     self.tb_info.setTextColor(color)
        #     self.tb_info.append(mensaje)
        # else:
        #     self.tb_info.setTextColor(color)
        #     self.tb_info.append(mensaje)
        self.tb_info.setStyleSheet("color: red")
        self.tb_info.setText(mensaje)


class Visor_imagen(QtWidgets.QDialog, Ui_Dialog_GV):
    def __init__(self):
        super(Visor_imagen, self).__init__()
        self.setupUi(self)

        # self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)

        self.gv_visor = MiGraphicsView()
        self.gv_visor.setObjectName("gv_visor")
        self.gridLayout.addWidget(self.gv_visor, 0, 0, 1, 2)

        self.pushButton.clicked.connect(self.guardar)
        self.pushButton_2.clicked.connect(self.cerrar)

    def guardar(self):
        name, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Guardar Imagen", "", "PNG(*.png);;JPEG(*.jpg)")
        if name == "":
            return
        if "." not in name:
            name += ".png"
        pixmap = QtGui.QPixmap(self.gv_visor.viewport().size())
        self.gv_visor.viewport().render(pixmap)
        pixmap.save(name)
        """La imagen que se guarda es la visualizada exactamente en el visor. Si la quiero completa he de hacer zoom"""

    def cerrar(self):
        Visor_imagen.hide(self)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Selector()
    window.show()
    sys.exit(app.exec_())
