

from Main import Ui_MainWindow
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal, QFileInfo, Qt, QDate, QPropertyAnimation, QPointF
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog, QTableWidget, QTableWidgetItem
import sys
import numpy as np
import matplotlib.pyplot as plt
from PyQt5 import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QAction, QTableWidget, QTableWidgetItem, QVBoxLayout
# from PyQt5.QtGui import QIcon
# from PyQt5.QtCore import pyqtSlot
# import sys
# import io
# from PIL import Image


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

        self.a_Acerca.triggered.connect(self.sobre_programa)
        self.a_Salir.triggered.connect(self.close_application)
        # self.a_Abrir.triggered.connect(self.abrir_proyecto)
        self.a_Abrir.triggered.connect(self.actualizar_datos)

        # self.pb_ejecutar.clicked.connect(self.calcular_poros)
        self.pb_ejecutar.clicked.connect(self.ejecutar)
        self.pb_anyadir.clicked.connect(self.actualizar)

        self.cb_poros.toggled.connect(self.habilitar)
        self.cb_puntos.toggled.connect(self.habilitar)

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
        self.dpto_max = 0.1
        self.dpto_min = 0.1
        self.Ppto_react = 0.002

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
        self.todos_ptos_react = []

        self.radios_puntos = []

        self.aridos_puestos = False
        self.poros_puestos = False

        self.A_poros = self.A * self.Pporos
        print('el Aporo es ' + str(self.A_poros))

        self.A_puntos = self.Ppto_react * self.A

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

    def actualizar_datos(self):
        self.cb_poros.setChecked(True)
        self.cb_puntos.setChecked(True)
        self.le_x.setText(str(self.x))
        self.le_y.setText(str(self.y))
        
        self.le_dmin.setText(str(self.dporo_min))
        self.le_dmax.setText(str(self.dporo_max))
        self.le_Pporos.setText(str(self.Pporos))

        self.le_dmin_ptos.setText(str(self.dpto_min))
        self.le_dmax_ptos.setText(str(self.dpto_max))
        self.le_Pptos.setText(str(self.Ppto_react))

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

    def calcular_areas_aridos(self):
        i = 0
        while i + 1 < len(self.sieve_size):
            area_intervalo = ((self.tpp[i] - self.tpp[i + 1]) / (self.tpp[0] - self.tpp[-1])) * self.Pagg * self.A
            self.Aagg.append(round(area_intervalo))
            i = i + 1
        print(self.Aagg)

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

    def calcular_puntos(self):
        while self.A_puntos > np.pi * (self.dpto_min / 2) ** 2:
            if self.dpto_min == self.dpto_max:
                rpunto = self.dpto_min/2
            else:
                rpunto = (self.dpto_min + np.random.random() * (self.dpto_max - self.dpto_min)) / 2
            Apunto = np.pi * (rpunto) ** 2
            self.A_puntos = self.A_puntos - Apunto
            self.radios_puntos.append(rpunto)

    def colocar_puntos(self):
        while len(self.radios_puntos) > 0:
            r = self.radios_puntos[0]
            loc_pto_x = np.random.uniform(0, self.x)
            loc_pto_y = np.random.uniform(0, self.y)
            dato_pto = [loc_pto_x, loc_pto_y, r]
            punto_react = plt.Circle((loc_pto_x, loc_pto_y), r, color='y')
            if self.poros_puestos:
                if loc_pto_x + r < self.x and loc_pto_x - r > 0 and loc_pto_y + r < self.y and loc_pto_y - r > 0:
                    if self.distancias(self.lista_poros, loc_pto_x, loc_pto_y, r):
                        if len(self.lista_ptos_react) == 0:
                            self.lista_ptos_react.append(dato_pto)
                            self.todos_ptos_react.append(punto_react)
                            self.radios_puntos.remove(r)
                        elif self.distancias(self.lista_ptos_react, loc_pto_x, loc_pto_y, r):
                            self.lista_ptos_react.append(dato_pto)
                            self.todos_ptos_react.append(punto_react)
                            self.radios_puntos.remove(r)
            if not self.poros_puestos:
                if loc_pto_x + r < self.x and loc_pto_x - r > 0 and loc_pto_y + r < self.y and loc_pto_y - r > 0:
                    if len(self.lista_ptos_react) == 0:
                        self.lista_ptos_react.append(dato_pto)
                        self.todos_ptos_react.append(punto_react)
                        self.radios_puntos.remove(r)
                    elif self.distancias(self.lista_ptos_react, loc_pto_x, loc_pto_y, r):
                        self.lista_ptos_react.append(dato_pto)
                        self.todos_ptos_react.append(punto_react)
                        self.radios_puntos.remove(r)

    def calcular_colocar_puntos(self):
        A_react = self.Ppto_react * self.A
        N_react = round(A_react / (np.pi * (self.r_react) ** 2))
        print('El número de puntos reactivos es ' + str(N_react))
        cuenta_N_react = 0
        while cuenta_N_react < N_react:
            loc_pto_x = np.random.uniform(0, self.x)
            loc_pto_y = np.random.uniform(0, self.y)
            dato_pto = [loc_pto_x, loc_pto_y, self.r_react]
            punto_react = plt.Circle((loc_pto_x, loc_pto_y), self.r_react, color='y')
            if self.poros_puestos:
                if loc_pto_x + self.r_react < self.x and loc_pto_x - self.r_react > 0 and loc_pto_y + self.r_react < self.y and loc_pto_y - self.r_react > 0:
                    if self.distancias(self.lista_poros, loc_pto_x, loc_pto_y, self.r_react):
                        if len(self.lista_ptos_react) == 0:
                            self.lista_ptos_react.append(dato_pto)
                            self.todos_ptos_react.append(punto_react)
                        elif self.distancias(self.lista_ptos_react, loc_pto_x, loc_pto_y, self.r_react):
                            self.lista_ptos_react.append(dato_pto)
                            self.todos_ptos_react.append(punto_react)
            if not self.poros_puestos:
                if loc_pto_x + self.r_react < self.x and loc_pto_x - self.r_react > 0 and loc_pto_y + self.r_react < self.y and loc_pto_y - self.r_react > 0:
                    if len(self.lista_ptos_react) == 0:
                        self.lista_ptos_react.append(dato_pto)
                        self.todos_ptos_react.append(punto_react)
                    elif self.distancias(self.lista_ptos_react, loc_pto_x, loc_pto_y, self.r_react):
                        self.lista_ptos_react.append(dato_pto)
                        self.todos_ptos_react.append(punto_react)
            cuenta_N_react += 1

    def plotear_resultados(self):
        self.gv_visor.setEnabled(True)
        self.lb_estructura.setEnabled(True)
        figure, axes = plt.subplots(figsize=(4, 4))
        axes.set_xlim(0, self.x)
        axes.set_ylim(0, self.y)

        for i in self.todos_poros:
            axes.add_patch(i)

        for i in self.todos_aridos:
            axes.add_patch(i)

        for i in self.todos_ptos_react:
            axes.add_patch(i)

        # crear el erctángulo de la probeta
        probeta = plt.Rectangle((0, 0), self.x, self.y, color='black', fill=False)
        axes.add_patch(probeta)
        # plt.title('áridos en la probeta')
        axes.autoscale_view()
        # fig = plt.gcf()

        # self.imagen = self.fig2img(fig)
        scene = QtWidgets.QGraphicsScene()
        self.gv_visor.setScene(scene)
        canvas = FigureCanvas(figure)
        proxy_widget = scene.addWidget(canvas)
        scene.addItem(proxy_widget)
        self.gv_visor.show()

        # plt.show()

    def ejecutar(self):
        if self.existe_estructura:
            choice = QMessageBox.information(None, 'Información',
                                             "¿Quieres borrar la estructura anterior?", QMessageBox.Yes | QMessageBox.No)
            if choice == QMessageBox.Yes:
                self.limpiar()
                # self.actualizar()
                self.simular()
            else:
                # self.plotear_resultados()
                # self.replotear()
                pass
        if not self.existe_estructura:
            self.simular()
            self.existe_estructura = True
        self.resultados()

    def simular(self):
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
        self.lista_ptos_react = []
        self.todos_ptos_react = []

        self.aridos_puestos = False
        self.poros_puestos = False

        self.A_poros = self.A * self.Pporos
        self.A_puntos = self.A * self.Ppto_react

    def resultados(self):
        self.lb_resultados.setEnabled(True)
        self.label_2.setEnabled(True)
        # area_total = "Área total = " + str(self.A)

    def actualizar(self):
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
        if self.le_dmax_ptos.text():
            self.dpto_max = float(self.le_dmax_ptos.text())
        if self.le_dmin_ptos.text():
            self.dpto_min = float(self.le_dmin_ptos.text())
        if self.le_Pptos.text():
            self.Ppto_react = float(self.le_Pptos.text())

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
            self.le_dmax_ptos.setEnabled(True)
            self.lb_dmax_ptos.setEnabled(True)
            self.le_dmin_ptos.setEnabled(True)
            self.lb_dmin_ptos.setEnabled(True)
            self.le_Pptos.setEnabled(True)
            self.lb_Pptos.setEnabled(True)
        if not self.cb_puntos.isChecked():
            self.lb_puntos.setEnabled(False)
            self.le_dmax_ptos.setEnabled(False)
            self.lb_dmax_ptos.setEnabled(False)
            self.le_dmin_ptos.setEnabled(False)
            self.lb_dmin_ptos.setEnabled(False)
            self.le_Pptos.setEnabled(False)
            self.lb_Pptos.setEnabled(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = mainProgram()
    window.show()
    sys.exit(app.exec_())
