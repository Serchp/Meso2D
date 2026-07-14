"""
Script heredero de Meso2D_03_todo_worker_limpio
Cambios principales:
- la pasta incorpora las dos fracciones finas consideradas en la mesoestructura
- Mejores definiciones en el GUI en relación a lo anterior
- Implementación de Añadir y Quitar filas en la tabla de dosificación
- Error en el Stop al acabar la simulación
"""

"""
Versión creada para probar refactorización del código
La clase worker trasladada a un archivo a parte e importada aquí
"""
import json
from src.ui.Main03 import Ui_MainWindow
from src.ui.Main_inicio import Ui_MainWindow as Menuinicio
from src.ui.GV import MiGraphicsView
# from Worker import WorkerTodos
from PyQt5.QtGui import QColor
from PyQt5.QtCore import pyqtSignal, QObject, QThread, QFileInfo, Qt, QDate, QPropertyAnimation, QPointF
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog, QTableWidget, QTableWidgetItem, QVBoxLayout
import sys
import numpy as np
import matplotlib.pyplot as plt
from PyQt5 import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from src.ui.dialog_GV import Ui_Dialog_GV
import time
import ezdxf
from src.io.project import build_project_payload, save_project_to_file, load_project_from_file, apply_project_payload
from src.visualization.service import save_current_view, save_viewport_image
from src.simulation.orchestration import SimulationController


class Selector(QtWidgets.QMainWindow, Menuinicio):
    modo_escogido = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.setupUi(self)
        self.pb_circulos.clicked.connect(self.pb_circulos_pulsar)
        self.pb_elipses.clicked.connect(self.pb_elipses_pulsar)
        self.pb_poligonos.clicked.connect(self.pb_poligonos_pulsar)

    def pb_circulos_pulsar(self):
        print('pb circulos clicked')
        self.modo_escogido.emit('circulos')
        self.close()

    def pb_elipses_pulsar(self):
        print('pb elipses clicked')
        self.modo_escogido.emit('elipses')
        self.close()

    def pb_poligonos_pulsar(self):
        print('pb poligonos clicked')
        self.modo_escogido.emit('poligonos')
        self.close()


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

    def __init__(self, modo):
        super(mainProgram, self).__init__()
        self.modo = modo

        self.setupUi(self)

        self.dlg = Visor_imagen()
        self.dlg.setModal(True)

        self.a_Acerca.triggered.connect(self.sobre_programa)
        self.a_Salir.triggered.connect(self.close_application)
        self.a_Abrir.triggered.connect(self.abrir_proyecto)
        self.a_CargarE.triggered.connect(self.cargar_ejemplo)
        self.a_GuardarP.triggered.connect(self.guardar_proyecto)
        self.a_Nuevo.triggered.connect(self.nuevo_proyecto)
        self.a_Estructura.triggered.connect(self.exportar_estructura)
        self.a_GuardarI.triggered.connect(self.guardar_imagen)

        self.pb_ejecutar.clicked.connect(self.ejecutar)
        self.pb_anyadir.clicked.connect(self.anyadir_fila)
        self.pb_eliminar.clicked.connect(self.actualizar)
        self.pb_ver_estructura.clicked.connect(self.ver_estructura)

        self.pb_stop.clicked.connect(self.stop_simulation)

        self.cb_poros.toggled.connect(self.habilitar)
        self.cb_puntos.toggled.connect(self.habilitar)
        self.cb_puntos_aridos.toggled.connect(self.habilitar)
        self.cb_puntos_pasta.toggled.connect(self.habilitar)
        self.cb_semilla.toggled.connect(self.habilitar)

        self.tabla_dosif.setColumnCount(2)
        self.tabla_dosif.setRowCount(0)
        self.tabla_dosif.setHorizontalHeaderLabels(["sieve_size", "tpp"])
        self.tabla_dosif.resizeRowsToContents()
        self.tabla_dosif.resizeColumnsToContents()

        self.sieve_size = None  # tamaño de malla del tamiz?
        self.tpp = None  # porcentaje acumulado de áridos que pasan por el correspondiente sieve_size

        self.x = None  # variable dimensión x de la probeta
        self.y = None  # variable dimensión y de la probeta
        self.Pagg = None  # coarse aggregate ratio
        self.Pporos = None  # porcentaje de poros
        self.dporo_min = None  # diámetro mínimo de los poros
        self.dporo_max = None  # diámetro máximo de los poros
        self.r_react = None  # creo que no está en uso
        self.dpto_max_aridos = None  # diámetro máximo de los ptos reactivos en los áridos
        self.dpto_min_aridos = None  # diámetro mínimo de los ptos reactivos en los áridos
        self.dpto_max_pasta = None  # diámetro máximo de los ptos reactivos en la pasta
        self.dpto_min_pasta = None  # diámetro mínimo de los ptos reactivos en la pasta
        self.Ppto_react_aridos = None  # porcentaje de puntos reactivos en los áridos
        self.Ppto_react_pasta = None  # porcentaje de puntos reactivos en la pasta

        self.seed = None  # semilla para evitar el random y poder recuperar proyectos

        self.datos = None  # variable para necesaria para guardar/abrir proyectos

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

        self.aridos_puestos = False
        self.poros_puestos = False

        self.lista_aridos_gruesos = []
        self.lista_aridos_finos = []

        self.A_poros = None
        print('el Aporo es ' + str(self.A_poros))

        self.A_puntos_aridos = None
        self.A_puntos_pasta = None

        self.existe_estructura = False

        self.check_poros = False
        self.check_puntos = False
        self.check_puntos_aridos = False
        self.check_puntos_pasta = False

        self.todo_correcto = False

        self.redColor = QColor(255, 0, 0)
        self.blackColor = QColor(0, 0, 0)
        self.blueColor = QColor(0, 0, 255)

        self.simulation_controller = SimulationController(self)

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

    def anyadir_fila(self):
        rowPosition = self.tabla_dosif.rowCount()
        self.tabla_dosif.insertRow(rowPosition)

    def abrir_proyecto(self):
        if self.datos:
            print("hay datos")
            choice = QMessageBox.information(None, 'Información',
                                             "¿Quieres borrar el proyecto actual y abrir uno anterior?",
                                             QMessageBox.Ok | QMessageBox.No)
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
        self.js = load_project_from_file(name)
        self.actualizar_datos(self.js)
        self.llenar_datos()
        self.informar('---PROYECTO IMPORTADO---', color=self.blueColor)

    def variables_limpias(self):
        self.sieve_size = None  # tamaño de malla del tamiz?
        self.tpp = None  # porcentaje acumulado de áridos que pasan por el correspondiente sieve_size

        self.x = None  # variable dimensión x de la probeta
        self.y = None  # variable dimensión y de la probeta
        self.Pagg = None  # coarse aggregate ratio
        self.Pporos = None  # porcentaje de poros
        self.dporo_min = None  # diámetro mínimo de los poros
        self.dporo_max = None  # diámetro máximo de los poros
        self.r_react = None  # creo que no está en uso
        self.dpto_max_aridos = None  # diámetro máximo de los ptos reactivos en los áridos
        self.dpto_min_aridos = None  # diámetro mínimo de los ptos reactivos en los áridos
        self.dpto_max_pasta = None  # diámetro máximo de los ptos reactivos en la pasta
        self.dpto_min_pasta = None  # diámetro mínimo de los ptos reactivos en la pasta
        self.Ppto_react_aridos = None  # porcentaje de puntos reactivos en los áridos
        self.Ppto_react_pasta = None  # porcentaje de puntos reactivos en la pasta

        self.seed = None  # semilla para evitar el random y poder recuperar proyectos

        self.datos = None  # variable para necesaria para guardar/abrir proyectos

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
                                             "¿Quieres borrar el proyecto actual y empezar uno nuevo?",
                                             QMessageBox.Ok | QMessageBox.No)
            if choice == QMessageBox.Ok:
                self.variables_limpias()
                self.llenar_datos()
            else:
                pass
        self.informar('---NUEVO EJEMPLO---', color=self.blueColor)

    def cargar_ejemplo(self):
        # with open('proyecto_ejemplo.txt') as f:
        with open('proyecto_ejemplo2.txt') as f:
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
        if self.dpto_min_aridos or self.dpto_max_aridos or self.Ppto_react_aridos \
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
        self.datos = [
            "sieve_size", "tpp", "x", "y", "Pagg", "Pporos", "dporo_min", "dporo_max", "r_react",
            "dpto_max_aridos", "dpto_min_aridos", "dpto_max_pasta", "dpto_min_pasta",
            "Ppto_react_aridos", "Ppto_react_pasta", "seed"
        ]
        apply_project_payload(self, diccionario)

    def guardar_proyecto(self):
        """import json

        details = {'Name': "Bob", 'Age' :28}

        with open('convert.txt', 'w') as convert_file:
            convert_file.write(json.dumps(details))"""

        self.proyecto = build_project_payload(self)

        name, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Guardar Proyecto", "", "TXT(*.txt)")
        if name == "":
            return
        save_project_to_file(name, self.proyecto)
        self.informar('---PROYECTO GUARDADO---', color=self.blueColor)

    def plotear(self, imagen):
        self.dlg.gv_visor.setPhoto(imagen)

        self.dlg.show()
        self.progressBar.setValue(100)
        self.pb_ver_estructura.setEnabled(True)
        self.informar('* El tiempo necesario para la simulación ha sido ' + str(
            round(time.time() - self.start_time, 4)) + ' segundos', color=self.blackColor)
        self.informar('---FIN DE LA SIMULACIÓN---', color=self.blueColor)
        self.a_Estructura.setEnabled(True)
        self.a_GuardarI.setEnabled(True)

    def ejecutar(self):
        if self.existe_estructura:
            choice = QMessageBox.information(None, 'Información',
                                             "¿Quieres borrar la estructura anterior?", QMessageBox.Ok | QMessageBox.No)
            if choice == QMessageBox.Ok:
                self.limpiar()
                try:
                    self.actualizar()
                except:
                    self.informar('---ERROR: faltan datos imprescindibles para empezar la simulación',
                                  color=self.redColor)
                self.comprobar_datos_para_worker()
            else:
                pass
        if not self.existe_estructura:
            try:
                self.actualizar()
            except:
                self.informar('---ERROR: faltan datos imprescindibles para empezar la simulación', color=self.redColor)

            self.comprobar_datos_para_worker()
            self.existe_estructura = True

    def comprobar_datos_para_worker(self):
        print('comprobando datos')
        self.datos_necesarios = [self.sieve_size, self.tpp, self.x, self.y, self.Pagg, self.Pporos, self.dporo_min,
                                 self.dporo_max, self.r_react, self.dpto_max_aridos, self.dpto_min_aridos,
                                 self.dpto_max_pasta, self.dpto_min_pasta, self.Ppto_react_aridos,
                                 self.Ppto_react_pasta, self.seed]
        contador = 0
        for n in self.datos_necesarios:
            if n is None:
                contador += 1
        if contador == 0:
            self.todo_correcto = True
            self.simular()

    def simular(self):

        if self.cb_semilla.isChecked():
            np.random.seed(self.seed)
        else:
            self.seed = np.random.randint(1000000)
            np.random.seed(self.seed)

        if self.cb_poros.isChecked():
            self.check_poros = True
        if self.cb_puntos.isChecked():
            self.check_puntos = True
        if self. cb_puntos_aridos.isChecked():
            self.check_puntos_aridos = True
        if self.cb_puntos_pasta.isChecked():
            self.check_puntos_pasta = True

        if not self.cb_poros.isChecked():
            self.check_poros = False
        if not self.cb_puntos.isChecked():
            self.check_puntos = False
        if not self. cb_puntos_aridos.isChecked():
            self.check_puntos_aridos = False
        if not self.cb_puntos_pasta.isChecked():
            self.check_puntos_pasta = False

        self.pb_ejecutar.setEnabled(False)

        self.start_time = time.time()

        self.informar('---COMIENZO DE LA SIMULACIÓN---', color=self.blueColor)
        self.informar('El valor de la semilla es ' + str(self.seed), color=self.blackColor)

        self.pb_stop.setEnabled(True)
        self.progressBar.setValue(0)

        try:
            self.simulation_controller.start()
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(self, "Modo no definido", str(exc))
            return


    """
    He de implementarlo porque no funciona
    """

    def stop(self):
        self.simulation_controller.stop()

    def stop_simulation(self):
        self.simulation_controller.stop()

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

        self.sieve_size = []
        for row in range(self.tabla_dosif.rowCount()):
            item = self.tabla_dosif.item(row, 0)
            text = item.text() if item is not None else ""
            self.sieve_size.append(int(text))
        print(self.sieve_size)

        self.tpp = []
        for row in range(self.tabla_dosif.rowCount()):
            item = self.tabla_dosif.item(row, 1)
            text = item.text() if item is not None else ""
            self.tpp.append(int(text))
        print(self.tpp)

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

    def pasar_lista_poros(self, lista):
        self.lista_poros = lista

    def pasar_lista_gruesos(self, lista):
        self.lista_aridos_gruesos = lista

    def pasar_lista_finos(self, lista):
        self.lista_aridos_finos= lista

    def pasar_lista_reactivos(self, lista):
        self.lista_ptos_react = lista


    """
    Exportar distribución de áridos, poros y puntos reactivos en dxf
    """

    def exportar_estructura(self):
        if self.modo == "circulos":
            self.exportar_estructura_circulos()
        elif self.modo == "elipses":
            self.exportar_estructura_elipses()
        elif self.modo == "poligonos":
            self.exportar_estructura_poligonos()
        else:
            QtWidgets.QMessageBox.warning(self, "Modo no definido", "Debes seleccionar un modo antes de exportar.")

    def exportar_estructura_circulos(self):
        print(self.lista_poros)
        print(self.lista_aridos_gruesos)
        print(self.lista_aridos_finos)
        print(self.lista_ptos_react)
        name, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Exportar Estructura", "", "DXF(*.dxf)")
        if name == "":
            return
        if "." not in name:
            name += ".dxf"
        doc = ezdxf.new()
        doc.layers.new(name='Poros')
        doc.layers.new(name='Aridos gruesos')
        doc.layers.new(name='Aridos finos')
        doc.layers.new(name='Ptos_reactivos')
        msp = doc.modelspace()
        for i in self.lista_poros:
            msp.add_circle([i[0], i[1]], i[2], dxfattribs={'layer': 'Poros'})
        for i in self.lista_aridos_gruesos:
            msp.add_circle([i[0], i[1]], i[2], dxfattribs={'layer': 'Aridos gruesos'})
        for i in self.lista_aridos_finos:
            msp.add_circle([i[0], i[1]], i[2], dxfattribs={'layer': 'Aridos finos'})
        for i in self.lista_ptos_react:
            msp.add_circle([i[0], i[1]], i[2], dxfattribs={'layer': 'Ptos_reactivos'})

        doc.saveas(name)
        self.informar('---ESTRUCTURA EXPORTADA---', color=self.blueColor)

    def exportar_estructura_elipses(self):
        name, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Exportar Estructura", "", "DXF(*.dxf)")
        if name == "":
            return
        if "." not in name:
            name += ".dxf"

        doc = ezdxf.new()
        doc.layers.new(name='Poros')
        doc.layers.new(name='Aridos gruesos')
        doc.layers.new(name='Aridos finos')
        doc.layers.new(name='Ptos_reactivos')
        msp = doc.modelspace()

        # Exportar poros (circulos)
        for i in self.lista_poros:
            msp.add_circle([i[0], i[1]], i[2], dxfattribs={'layer': 'Poros'})

        # Función para generar puntos de la elipse rotada
        def puntos_elipse(x, y, a, b, angulo_deg, num_puntos=60):
            angulo_rad = np.radians(angulo_deg)
            t = np.linspace(0, 2 * np.pi, num_puntos)
            # Elipse sin rotar
            px = a * np.cos(t)
            py = b * np.sin(t)
            # Rotar puntos
            xr = px * np.cos(angulo_rad) - py * np.sin(angulo_rad) + x
            yr = px * np.sin(angulo_rad) + py * np.cos(angulo_rad) + y
            return list(zip(xr, yr))

        # Exportar áridos gruesos (elipses)
        for e in self.lista_aridos_gruesos:
            x, y, a, b, angulo = e
            pts = puntos_elipse(x, y, a, b, angulo)
            msp.add_lwpolyline(pts, close=True, dxfattribs={'layer': 'Aridos gruesos'})

        # Exportar áridos finos (elipses)
        for e in self.lista_aridos_finos:
            x, y, a, b, angulo = e
            pts = puntos_elipse(x, y, a, b, angulo)
            msp.add_lwpolyline(pts, close=True, dxfattribs={'layer': 'Aridos finos'})

        # Exportar puntos reactivos (suponiendo círculos también)
        for i in self.lista_ptos_react:
            msp.add_circle([i[0], i[1]], i[2], dxfattribs={'layer': 'Ptos_reactivos'})

        doc.saveas(name)
        self.informar('---ESTRUCTURA EXPORTADA---', color=self.blueColor)

    def exportar_estructura_poligonos(self):
        name, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Exportar Estructura", "", "DXF(*.dxf)")
        if name == "":
            return
        if "." not in name:
            name += ".dxf"

        doc = ezdxf.new()
        doc.layers.new(name='Poros')
        doc.layers.new(name='Aridos gruesos')
        doc.layers.new(name='Aridos finos')
        doc.layers.new(name='Ptos_reactivos')
        msp = doc.modelspace()

        # Exportar poros (círculos)
        for poro in self.lista_poros:
            if isinstance(poro, (list, tuple)) and len(poro) >= 3:
                msp.add_circle([poro[0], poro[1]], poro[2], dxfattribs={'layer': 'Poros'})
            elif hasattr(poro, "exterior"):
                pts = list(poro.exterior.coords)
                if len(pts) > 1 and pts[0] == pts[-1]:
                    pts = pts[:-1]
                if len(pts) >= 3:
                    msp.add_lwpolyline(pts, close=True, dxfattribs={'layer': 'Poros'})

        # Exportar áridos (acepta Polygon Shapely o listas de vértices)
        def extraer_vertices_poligono(obj):
            if hasattr(obj, "exterior"):
                pts = list(obj.exterior.coords)
            elif isinstance(obj, (list, tuple)) and len(obj) >= 3 and all(
                    isinstance(p, (list, tuple)) and len(p) >= 2 for p in obj):
                pts = [(p[0], p[1]) for p in obj]
            else:
                return None

            if len(pts) > 1 and pts[0] == pts[-1]:
                pts = pts[:-1]
            if len(pts) < 3:
                return None
            return pts

        for polygon in self.lista_aridos_gruesos:
            pts = extraer_vertices_poligono(polygon)
            if pts is not None:
                msp.add_lwpolyline(pts, close=True, dxfattribs={'layer': 'Aridos gruesos'})

        for polygon in self.lista_aridos_finos:
            pts = extraer_vertices_poligono(polygon)
            if pts is not None:
                msp.add_lwpolyline(pts, close=True, dxfattribs={'layer': 'Aridos finos'})

        # Exportar puntos reactivos (círculos)
        for pkreactivo in self.lista_ptos_react:
            msp.add_circle([pkreactivo[0], pkreactivo[1]], pkreactivo[2], dxfattribs={'layer': 'Ptos_reactivos'})

        doc.saveas(name)
        self.informar('---ESTRUCTURA EXPORTADA---', color=self.blueColor)
    """
    Se guarda completa, sin el zoom
    """
    def guardar_imagen(self):
        name, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Guardar Imagen", "", "PNG(*.png);;JPEG(*.jpg)")
        if name == "":
            return
        save_current_view(self, name)
        self.informar('---IMAGEN GUARDADA---', color=self.blueColor)


    def informar2(self, mensaje=None, color=None):
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

    def informar_worker(self, mensaje=None):
        self.tb_info.setTextColor(self.blackColor)
        self.tb_info.append(mensaje)

    def informar_worker_error(self, mensaje=None):
        self.tb_info.setTextColor(self.redColor)
        self.tb_info.append(mensaje)

    def mostrar_progreso(self, porcentaje):
        self.progressBar.setValue(porcentaje)


class Visor_imagen(QtWidgets.QDialog, Ui_Dialog_GV):
    def __init__(self):
        super(Visor_imagen, self).__init__()
        self.setupUi(self)

        self.gv_visor = MiGraphicsView()
        self.gv_visor.setObjectName("gv_visor")
        self.gridLayout.addWidget(self.gv_visor, 0, 0, 1, 2)

        self.pushButton.clicked.connect(self.guardar)
        self.pushButton_2.clicked.connect(self.cerrar)

    def guardar(self):
        name, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Guardar Imagen", "", "PNG(*.png);;JPEG(*.jpg)")
        if name == "":
            return
        save_viewport_image(self, name)
        """La imagen que se guarda es la visualizada exactamente en el visor. Si la quiero completa he de hacer zoom"""

    def cerrar(self):
        Visor_imagen.hide(self)


class Controlador:
    def __init__(self):
        self.selector = Selector()
        self.selector.modo_escogido.connect(self.abrir_mainprogram)
        self.selector.show()

    def abrir_mainprogram(self, modo):
        self.mainprogram = mainProgram(modo)
        self.mainprogram.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    c = Controlador()
    sys.exit(app.exec_())

