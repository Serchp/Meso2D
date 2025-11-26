

# from Main01 import Ui_MainWindow
from Main02 import Ui_MainWindow
from Main_inicio import Ui_MainWindow as Menuinicio
# from GV import MiGraphicsView
from GV import MiGraphicsView
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal, QFileInfo, Qt, QDate, QPropertyAnimation, QPointF
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog, QTableWidget, QTableWidgetItem, QVBoxLayout
import sys
import numpy as np
import matplotlib.pyplot as plt
from PyQt5 import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

# from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QAction, QTableWidget, QTableWidgetItem
# from PyQt5.QtGui import QIcon, QPixmap
# from PyQt5.QtCore import pyqtSlot
# import sys
# import io
# from PIL import Image


class Selector(QtWidgets.QMainWindow, Menuinicio):
    def __init__(self, parent=None):
        super(Selector, self).__init__(parent)

        self.setupUi(self)
        self.pb_circulos.clicked.connect(self.pb_circulos_pulsar)
        # self.graph = Graph(self)

        # just to see the two windows side-by-side
        # self.move(500, 400)
        # self.graph.move(self.x()+self.width()+20, self.y())

    def pb_circulos_pulsar(self):
        print('pb clicked')
        self.close()
        self.circulos = mainProgram(self)
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
    def __init__(self, parent=None):
        super(mainProgram, self).__init__(parent)
        self.setupUi(self)

        self.gv_visor = MiGraphicsView()
        self.gv_visor.setEnabled(False)
        self.gv_visor.setObjectName("gv_visor")
        self.verticalLayout_2.addWidget(self.gv_visor)

        self.a_Acerca.triggered.connect(self.sobre_programa)
        self.a_Salir.triggered.connect(self.close_application)
        # self.a_Abrir.triggered.connect(self.abrir_proyecto)
        # self.a_Abrir.triggered.connect(self.cargar_ejemplo)
        self.a_CargarE.triggered.connect(self.cargar_ejemplo)

        # self.pb_ejecutar.clicked.connect(self.calcular_poros)
        self.pb_ejecutar.clicked.connect(self.ejecutar)
        self.pb_anyadir.clicked.connect(self.actualizar)

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
        self.sieve_size = [19.00, 12.70, 9.50, 4.75, 2.36]
        self.tpp = [100, 97, 61, 10, 1.4]

        self.x = 75
        self.y = 75
        self.Pagg = 0.5
        self.Pporos = 0.02
        self.dporo_min = 2
        self.dporo_max = 4
        self.r_react = 0.05
        self.dpto_max_aridos = 0.1
        self.dpto_min_aridos = 0.1
        self.dpto_max_pasta = 0.1
        self.dpto_min_pasta = 0.1
        self.Ppto_react_aridos = 0.002
        self.Ppto_react_pasta = 0.002

        self.seed = 666

        """"
        Variables necesarias
        """

        self.A = self.x * self.y
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

        self.A_poros = self.A * self.Pporos
        print('el Aporo es ' + str(self.A_poros))

        self.A_puntos_total = (self.Ppto_react_aridos + self.Ppto_react_pasta) * self.A
        self.A_puntos_aridos = self.Ppto_react_aridos * self.A
        self.A_puntos_pasta = self.Ppto_react_pasta * self.A

        # self.actualizar_datos()
        # self. dlg_plotear = Plotear(self.todos_aridos, self.todos_poros, self.todos_ptos_react, self.x, self.y)

        self.existe_estructura = False

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

    def abrir_proyecto(self):
        name, _ = QtWidgets.QFileDialog.getOpenFileName(None, 'Abrir proyecto')
        self.filename = QFileInfo(name).fileName()

    # def actualizar_datos(self):
    #     self.cb_poros.setChecked(True)
    #     self.cb_puntos.setChecked(True)
    #     self.cb_semilla.setChecked(True)
    #     self.le_x.setText(str(self.x))
    #     self.le_y.setText(str(self.y))
    #     self.le_semilla.setText(str(self.seed))
    #
    #     self.le_dmin.setText(str(self.dporo_min))
    #     self.le_dmax.setText(str(self.dporo_max))
    #     self.le_Pporos.setText(str(self.Pporos))
    #
    #     self.le_dmin_ptos.setText(str(self.dpto_min))
    #     self.le_dmax_ptos.setText(str(self.dpto_max))
    #     self.le_Pptos.setText(str(self.Ppto_react))
    #
    #     self.llenar_datos_tabla_dosif()

    def cargar_ejemplo(self):
        self.cb_poros.setChecked(True)
        self.cb_puntos.setChecked(True)
        self.cb_semilla.setChecked(True)
        self.cb_puntos_aridos.setChecked(True)
        self.cb_puntos_pasta.setChecked(True)
        self.le_x.setText(str(self.x))
        self.le_y.setText(str(self.y))
        self.le_semilla.setText(str(self.seed))

        self.le_dmin.setText(str(self.dporo_min))
        self.le_dmax.setText(str(self.dporo_max))
        self.le_Pporos.setText(str(self.Pporos))

        self.le_dmin_ptos_pasta.setText(str(self.dpto_min_pasta))
        self.le_dmax_ptos_pasta.setText(str(self.dpto_max_pasta))
        self.le_Pptos_pasta.setText(str(self.Ppto_react_pasta))

        self.le_dmin_ptos_aridos.setText(str(self.dpto_min_aridos))
        self.le_dmax_ptos_aridos.setText(str(self.dpto_max_aridos))
        self.le_Pptos_aridos.setText(str(self.Ppto_react_aridos))

        self.llenar_datos_tabla_dosif()

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

    """
    calcular y colocar los poros
    """
    def calcular_poros(self):
        while self.A_poros > np.pi * (self.dporo_min / 2) ** 2:
            rporo = (self.dporo_min + np.random.random() * (self.dporo_max - self.dporo_min)) / 2
            Aporo = np.pi * (rporo) ** 2
            self.A_poros = self.A_poros - Aporo
            self.radios_poros.append(rporo)
        self.progressBar.setValue(10)

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
        self.progressBar.setValue(20)

    def calcular_areas_aridos(self):
        i = 0
        while i + 1 < len(self.sieve_size):
            area_intervalo = ((self.tpp[i] - self.tpp[i + 1]) / (self.tpp[0] - self.tpp[-1])) * self.Pagg * self.A
            self.Aagg.append(round(area_intervalo))
            i = i + 1
        print(self.Aagg)
        self.progressBar.setValue(30)

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
        self.progressBar.setValue(40)

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
        self.progressBar.setValue(50)

    def calcular_puntos(self):
        """puntos sobre áridos"""
        if self.cb_puntos_aridos.isChecked():
            if self.Ppto_react_aridos:
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
        """puntos sobre pasta"""
        if self.cb_puntos_pasta.isChecked():
            if self.Ppto_react_pasta:
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

    # def colocar_puntos(self):
    #     while len(self.radios_puntos_aridos) > 0:
    #         r = self.radios_puntos_aridos[0]
    #         loc_pto_x = np.random.uniform(0, self.x)
    #         loc_pto_y = np.random.uniform(0, self.y)
    #         dato_pto = [loc_pto_x, loc_pto_y, r]
    #         punto_react = plt.Circle((loc_pto_x, loc_pto_y), r, color='y')
    #         if self.poros_puestos:
    #             if loc_pto_x + r < self.x and loc_pto_x - r > 0 and loc_pto_y + r < self.y and loc_pto_y - r > 0:
    #                 if self.distancias(self.lista_poros, loc_pto_x, loc_pto_y, r):
    #                     if len(self.lista_ptos_react) == 0:
    #                         self.lista_ptos_react.append(dato_pto)
    #                         self.todos_ptos_react.append(punto_react)
    #                         self.radios_puntos.remove(r)
    #                     elif self.distancias(self.lista_ptos_react, loc_pto_x, loc_pto_y, r):
    #                         self.lista_ptos_react.append(dato_pto)
    #                         self.todos_ptos_react.append(punto_react)
    #                         self.radios_puntos.remove(r)
    #         if not self.poros_puestos:
    #             if loc_pto_x + r < self.x and loc_pto_x - r > 0 and loc_pto_y + r < self.y and loc_pto_y - r > 0:
    #                 if len(self.lista_ptos_react) == 0:
    #                     self.lista_ptos_react.append(dato_pto)
    #                     self.todos_ptos_react.append(punto_react)
    #                     self.radios_puntos.remove(r)
    #                 elif self.distancias(self.lista_ptos_react, loc_pto_x, loc_pto_y, r):
    #                     self.lista_ptos_react.append(dato_pto)
    #                     self.todos_ptos_react.append(punto_react)
    #                     self.radios_puntos.remove(r)
    #     self.progressBar.setValue(70)

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


            # if not self.poros_puestos:
            #     if loc_pto_x + r < self.x and loc_pto_x - r > 0 and loc_pto_y + r < self.y and loc_pto_y - r > 0:
            #         if len(self.lista_ptos_react) == 0:
            #             self.lista_ptos_react.append(dato_pto)
            #             self.todos_ptos_react.append(punto_react)
            #             self.radios_puntos.remove(r)
            #         elif self.distancias(self.lista_ptos_react, loc_pto_x, loc_pto_y, r):
            #             self.lista_ptos_react.append(dato_pto)
            #             self.todos_ptos_react.append(punto_react)
            #             self.radios_puntos.remove(r)
        self.progressBar.setValue(70)


    # def calcular_colocar_puntos(self):
    #     A_react = self.Ppto_react * self.A
    #     N_react = round(A_react / (np.pi * (self.r_react) ** 2))
    #     print('El número de puntos reactivos es ' + str(N_react))
    #     cuenta_N_react = 0
    #     while cuenta_N_react < N_react:
    #         loc_pto_x = np.random.uniform(0, self.x)
    #         loc_pto_y = np.random.uniform(0, self.y)
    #         dato_pto = [loc_pto_x, loc_pto_y, self.r_react]
    #         punto_react = plt.Circle((loc_pto_x, loc_pto_y), self.r_react, color='y')
    #         if self.poros_puestos:
    #             if loc_pto_x + self.r_react < self.x and loc_pto_x - self.r_react > 0 and loc_pto_y + self.r_react < self.y and loc_pto_y - self.r_react > 0:
    #                 if self.distancias(self.lista_poros, loc_pto_x, loc_pto_y, self.r_react):
    #                     if len(self.lista_ptos_react) == 0:
    #                         self.lista_ptos_react.append(dato_pto)
    #                         self.todos_ptos_react.append(punto_react)
    #                     elif self.distancias(self.lista_ptos_react, loc_pto_x, loc_pto_y, self.r_react):
    #                         self.lista_ptos_react.append(dato_pto)
    #                         self.todos_ptos_react.append(punto_react)
    #         if not self.poros_puestos:
    #             if loc_pto_x + self.r_react < self.x and loc_pto_x - self.r_react > 0 and loc_pto_y + self.r_react < self.y and loc_pto_y - self.r_react > 0:
    #                 if len(self.lista_ptos_react) == 0:
    #                     self.lista_ptos_react.append(dato_pto)
    #                     self.todos_ptos_react.append(punto_react)
    #                 elif self.distancias(self.lista_ptos_react, loc_pto_x, loc_pto_y, self.r_react):
    #                     self.lista_ptos_react.append(dato_pto)
    #                     self.todos_ptos_react.append(punto_react)
    #         cuenta_N_react += 1
    #     self.progressBar.setValue(80)

    def plotear_resultados(self):
        self.gv_visor.setEnabled(True)
        self.lb_estructura.setEnabled(True)
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
        pixmap = canvas.grab()
        self.gv_visor.setPhoto(pixmap)

        self.progressBar.setValue(100)

    def ejecutar(self):
        if self.existe_estructura:
            choice = QMessageBox.information(None, 'Información',
                                             "¿Quieres borrar la estructura anterior?", QMessageBox.Yes | QMessageBox.No)
            if choice == QMessageBox.Yes:
                self.limpiar()
                self.actualizar()
                self.simular()
            else:
                # self.plotear_resultados()
                # self.replotear()
                pass
        if not self.existe_estructura:
            self.actualizar()
            self.simular()
            self.existe_estructura = True
        self.resultados()

    def simular(self):
        np.random.seed(self.seed)
        self.calcular_areas_aridos()
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
        # self.lista_ptos_react = []
        self.lista_ptos_react_pasta = []
        self.lista_ptos_react_aridos = []
        self.todos_ptos_react = []

        self.aridos_puestos = False
        self.poros_puestos = False

        # self.A_poros = self.A * self.Pporos
        # self.A_puntos_pasta = self.A * self.Ppto_react_pasta
        # self.A_puntos_aridos = self.A * self.Ppto_react_aridos
        # self.A_puntos_total = self.A * (self.Ppto_react_pasta + self.Ppto_react_aridos)

    def resultados(self):
        self.lb_resultados.setEnabled(True)
        self.label_2.setEnabled(True)
        # area_total = "Área total = " + str(self.A)

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

        self.A_poros = self.A * self.Pporos
        self.A_puntos_pasta = self.A * self.Ppto_react_pasta
        self.A_puntos_aridos = self.A * self.Ppto_react_aridos
        self.A_puntos_total = self.A * (self.Ppto_react_pasta + self.Ppto_react_aridos)


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



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Selector()
    window.show()
    sys.exit(app.exec_())
