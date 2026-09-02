"""
Script derived from Meso2D_03_todo_worker_limpio
Main changes:
- paste includes the two fine fractions considered in the mesostructure
- clearer GUI definitions for the updated model
- Add/Remove row support in the gradation table
- stop handling after simulation completion
"""

"""
Version created to test code refactoring
Worker class moved to a separate file and imported here
"""
import json
from src.ui.Main03_EN import Ui_MainWindow
from src.ui.Main_inicio_EN import Ui_MainWindow as Menuinicio
from src.ui.GV_EN import MiGraphicsView
# from Worker import WorkerTodos
from PyQt5.QtGui import QColor
from PyQt5.QtCore import pyqtSignal, QObject, QThread, QFileInfo, Qt, QDate, QPropertyAnimation, QPointF
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog, QTableWidget, QTableWidgetItem, QVBoxLayout
import sys
import numpy as np
import matplotlib.pyplot as plt
from PyQt5 import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from src.ui.dialog_GV_EN import Ui_Dialog_GV
import time
import ezdxf
from pathlib import Path
from src.io.project_EN import build_project_payload, save_project_to_file, load_project_from_file, apply_project_payload
from src.io.structure_export_EN import export_structure_file, StructureExportError
from src.visualization.service_EN import save_current_view, save_viewport_image
from src.simulation.orchestration_EN import SimulationController


class Selector(QtWidgets.QMainWindow, Menuinicio):
    mode_escogido = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.setupUi(self)
        self.pb_circulos.clicked.connect(self.pb_circulos_pulsar)
        self.pb_elipses.clicked.connect(self.pb_ellipses_pulsar)
        self.pb_poligonos.clicked.connect(self.pb_poligonos_pulsar)

    def pb_circulos_pulsar(self):
        print('pb circulos clicked')
        self.mode_escogido.emit('circulos')
        self.close()

    def pb_ellipses_pulsar(self):
        print('pb ellipses clicked')
        self.mode_escogido.emit('ellipses')
        self.close()

    def pb_poligonos_pulsar(self):
        print('pb poligonos clicked')
        self.mode_escogido.emit('poligonos')
        self.close()


class About(QtWidgets.QLabel):
    def __init__(self):
        QtWidgets.QLabel.__init__(self,
                                  "Meso2D 1.0\n\nBy Servando Chinchon Paya, 2022\n\nPlease feel free to share any suggestions\n\nservando@ietcc.csic.es\n\nThank you!")
        self.setAlignment(QtCore.Qt.AlignCenter)

    def initUI(self):
        self.center()

    def center(self):
        qr = self.frameGeometry()
        cp = app.desktop().availableGeometry().centre()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


class mainProgram(QMainWindow, Ui_MainWindow):

    def __init__(self, mode):
        super(mainProgram, self).__init__()
        self.mode = mode

        self.setupUi(self)

        self.dlg = Viewer_image()
        self.dlg.setModal(True)

        self.a_About.triggered.connect(self.sobre_programa)
        self.a_Exit.triggered.connect(self.close_application)
        self.a_Open.triggered.connect(self.open_project)
        self.a_CargarE.triggered.connect(self.load_example)
        self.a_GuardarP.triggered.connect(self.save_project)
        self.a_New.triggered.connect(self.new_project)
        self.a_Structure.triggered.connect(self.exportar_structure)
        self.a_GuardarI.triggered.connect(self.save_image)
        self.a_Tutorial.triggered.connect(self.open_tutorial_pdf)

        self.pb_run.clicked.connect(self.run)
        self.pb_add.clicked.connect(self.add_fila)
        self.pb_remove.clicked.connect(self.update)
        self.pb_ver_structure.clicked.connect(self.ver_structure)

        self.pb_stop.clicked.connect(self.stop_simulation)

        self.cb_pores.toggled.connect(self.habilitar)
        self.cb_points.toggled.connect(self.habilitar)
        self.cb_points_aggregates.toggled.connect(self.habilitar)
        self.cb_points_pasta.toggled.connect(self.habilitar)
        self.cb_seed.toggled.connect(self.habilitar)

        self.tabla_dosif.setColumnCount(2)
        self.tabla_dosif.setRowCount(0)
        self.tabla_dosif.setHorizontalHeaderLabels(["sieve_size", "tpp"])
        self.tabla_dosif.resizeRowsToContents()
        self.tabla_dosif.resizeColumnsToContents()

        self.sieve_size = None  # Sieve mesh size
        self.tpp = None  # Cumulative aggregate percentage passing each sieve size

        self.x = None  # Specimen x dimension
        self.y = None  # Specimen y dimension
        self.Pagg = None  # Coarse aggregate ratio
        self.Pporos = None  # Pore ratio
        self.dporo_min = None  # Minimum pore diameter
        self.dporo_max = None  # Maximum pore diameter
        self.r_react = None  # currently unused
        self.dpto_max_aggregates = None  # Maximum reactive-point diameter in aggregates
        self.dpto_min_aggregates = None  # Minimum reactive-point diameter in aggregates
        self.dpto_max_pasta = None  # Maximum reactive-point diameter in paste
        self.dpto_min_pasta = None  # Minimum reactive-point diameter in paste
        self.Ppto_react_aggregates = None  # Reactive-point ratio in aggregates
        self.Ppto_react_pasta = None  # Reactive-point ratio in paste

        self.seed = None  # Seed for reproducibility

        self.data = None  # Data needed for save/open operations

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

        self.aggregates_puestos = False
        self.pores_puestos = False

        self.list_aggregates_coarse = []
        self.list_aggregates_fine = []

        self.A_pores = None
        print('Pore area is ' + str(self.A_pores))

        self.A_points_aggregates = None
        self.A_points_pasta = None

        self.existe_structure = False

        self.check_pores = False
        self.check_points = False
        self.check_points_aggregates = False
        self.check_points_pasta = False

        self.todo_correcto = False

        self.redColor = QColor(255, 0, 0)
        self.blackColor = QColor(0, 0, 0)
        self.blueColor = QColor(0, 0, 255)

        self.simulation_controller = SimulationController(self)

    def sobre_programa(self):
        self.pop = About()
        self.pop.resize(555, 333)
        self.pop.setWindowTitle("About Meso2D")
        self.pop.show()

    def close_application(self):
        choice = QMessageBox.information(None, 'Confirmation',
                                         "Are you sure you want to exit?", QMessageBox.Yes | QMessageBox.No)
        if choice == QMessageBox.Yes:
            sys.exit()
        else:
            pass

    def llenar_data_tabla_dosif(self):
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

    def add_fila(self):
        rowPosition = self.tabla_dosif.rowCount()
        self.tabla_dosif.insertRow(rowPosition)

    def open_project(self):
        if self.data:
            print("Existing project data detected")
            choice = QMessageBox.information(None, 'Confirmation',
                                             "Do you want to clear the current project and open another one?",
                                             QMessageBox.Ok | QMessageBox.No)
            if choice == QMessageBox.Ok:
                self.variables_limpias()
                self.open()
            else:
                pass
        if not self.data:
            self.open()

    def open(self):
        name, _ = QtWidgets.QFileDialog.getOpenFileName(None, 'Open Project', '*.txt')
        if name == "":
            return
        self.js = load_project_from_file(name)
        self.update_data(self.js)
        self.llenar_data()
        self.log('---PROJECT LOADED---', color=self.blueColor)

    def variables_limpias(self):
        self.sieve_size = None  # Sieve mesh size
        self.tpp = None  # Cumulative aggregate percentage passing each sieve size

        self.x = None  # Specimen x dimension
        self.y = None  # Specimen y dimension
        self.Pagg = None  # Coarse aggregate ratio
        self.Pporos = None  # Pore ratio
        self.dporo_min = None  # Minimum pore diameter
        self.dporo_max = None  # Maximum pore diameter
        self.r_react = None  # currently unused
        self.dpto_max_aggregates = None  # Maximum reactive-point diameter in aggregates
        self.dpto_min_aggregates = None  # Minimum reactive-point diameter in aggregates
        self.dpto_max_pasta = None  # Maximum reactive-point diameter in paste
        self.dpto_min_pasta = None  # Minimum reactive-point diameter in paste
        self.Ppto_react_aggregates = None  # Reactive-point ratio in aggregates
        self.Ppto_react_pasta = None  # Reactive-point ratio in paste

        self.seed = None  # Seed for reproducibility

        self.data = None  # Data needed for save/open operations

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

        self.aggregates_puestos = False
        self.pores_puestos = False

        self.A_pores = None
        self.A_points_aggregates = None
        self.A_points_pasta = None

        self.existe_structure = False

    def new_project(self):
        if self.data:
            print("Existing project data detected")
            choice = QMessageBox.information(None, 'Confirmation',
                                             "Do you want to clear the current project and start a new one?",
                                             QMessageBox.Ok | QMessageBox.No)
            if choice == QMessageBox.Ok:
                self.variables_limpias()
                self.llenar_data()
            else:
                pass
        self.log('---NEW PROJECT---', color=self.blueColor)

    def load_example(self):
        # Keep backward compatibility with the original Spanish example filenames.
        candidates = ["proyecto_ejemplo2.txt", "project_example2.txt", "project_ejemplo2.txt"]
        example_path = None
        for name in candidates:
            p = Path(name)
            if p.exists():
                example_path = p
                break

        if example_path is None:
            QtWidgets.QMessageBox.warning(self, "Example Not Found", "Could not find an example project file.")
            return

        with open(example_path, encoding="utf-8") as f:
            data = f.read()
            js = json.loads(data)
            self.update_data(js)
            self.llenar_data()
        self.log('---EXAMPLE LOADED---', color=self.blueColor)

    """
    Load calculation variables into the GUI
    """
    def llenar_data(self):
        """Check which values exist first to avoid filling unrelated fields."""
        if self.seed:
            self.cb_seed.setChecked(True)
            self.le_seed.setText(str(self.seed))
        else:
            self.cb_seed.setChecked(False)
            self.le_seed.setText("")

        if self.Pporos or self.dporo_min or self.dporo_max:
            self.cb_pores.setChecked(True)
        if self.dpto_min_aggregates or self.dpto_max_aggregates or self.Ppto_react_aggregates \
                or self.dpto_min_pasta or self.dpto_max_pasta or self.Ppto_react_pasta:
            self.cb_points.setChecked(True)
        if self.dpto_min_aggregates or self.dpto_max_aggregates or self.Ppto_react_aggregates:
            self.cb_points_aggregates.setChecked(True)
        if self.dpto_min_pasta or self.dpto_max_pasta or self.Ppto_react_pasta:
            self.cb_points_pasta.setChecked(True)

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

        if self.dpto_min_aggregates:
            self.le_dmin_ptos_aggregates.setText(str(self.dpto_min_aggregates))
        else:
            self.le_dmin_ptos_aggregates.setText("")
        if self.dpto_max_aggregates:
            self.le_dmax_ptos_aggregates.setText(str(self.dpto_max_aggregates))
        else:
            self.le_dmax_ptos_aggregates.setText("")
        if self.Ppto_react_aggregates:
            self.le_Pptos_aggregates.setText(str(self.Ppto_react_aggregates))
        else:
            self.le_Pptos_aggregates.setText("")

        self.llenar_data_tabla_dosif()

    """
    Load project dictionary data into calculation variables
    """
    def update_data(self, diccionario):
        # Accept original Spanish project keys when loading legacy examples or projects.
        aliases = {
            "dpto_max_aridos": "dpto_max_aggregates",
            "dpto_min_aridos": "dpto_min_aggregates",
            "Ppto_react_aridos": "Ppto_react_aggregates",
        }
        for old_key, new_key in aliases.items():
            if old_key in diccionario and new_key not in diccionario:
                diccionario[new_key] = diccionario[old_key]

        self.data = [
            "sieve_size", "tpp", "x", "y", "Pagg", "Pporos", "dporo_min", "dporo_max", "r_react",
            "dpto_max_aggregates", "dpto_min_aggregates", "dpto_max_pasta", "dpto_min_pasta",
            "Ppto_react_aggregates", "Ppto_react_pasta", "seed"
        ]
        apply_project_payload(self, diccionario)

    def save_project(self):
        """Save the current project state to a JSON-backed text file."""

        self.project = build_project_payload(self)

        name, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Save Project", "", "TXT(*.txt)")
        if name == "":
            return
        save_project_to_file(name, self.project)
        self.log('---PROJECT SAVED---', color=self.blueColor)

    def plotear(self, image):
        self.dlg.gv_viewer.setPhoto(image)

        self.dlg.show()
        self.progressBar.setValue(100)
        self.pb_ver_structure.setEnabled(True)
        self.log('* Simulation time: ' + str(round(time.time() - self.start_time, 4)) + ' seconds', color=self.blackColor)
        self.log('---SIMULATION FINISHED---', color=self.blueColor)
        self.a_Structure.setEnabled(True)
        self.a_GuardarI.setEnabled(True)

    def run(self):
        if self.existe_structure:
            choice = QMessageBox.information(None, 'Confirmation',
                                             "Do you want to clear the previous structure?", QMessageBox.Ok | QMessageBox.No)
            if choice == QMessageBox.Ok:
                self.limpiar()
                try:
                    self.update()
                except:
                    self.log('---ERROR: missing required data to start the simulation',
                                  color=self.redColor)
                self.comprobar_data_para_worker()
            else:
                pass
        if not self.existe_structure:
            try:
                self.update()
            except:
                self.log('---ERROR: missing required data to start the simulation', color=self.redColor)

            self.comprobar_data_para_worker()
            self.existe_structure = True

    def comprobar_data_para_worker(self):
        print('checking data')
        self.data_necesarios = [self.sieve_size, self.tpp, self.x, self.y, self.Pagg, self.Pporos, self.dporo_min,
                                 self.dporo_max, self.r_react, self.dpto_max_aggregates, self.dpto_min_aggregates,
                                 self.dpto_max_pasta, self.dpto_min_pasta, self.Ppto_react_aggregates,
                                 self.Ppto_react_pasta, self.seed]
        contador = 0
        for n in self.data_necesarios:
            if n is None:
                contador += 1
        if contador == 0:
            self.todo_correcto = True
            self.simulate()

    def simulate(self):

        if self.cb_seed.isChecked():
            np.random.seed(self.seed)
        else:
            self.seed = np.random.randint(1000000)
            np.random.seed(self.seed)

        if self.cb_pores.isChecked():
            self.check_pores = True
        if self.cb_points.isChecked():
            self.check_points = True
        if self. cb_points_aggregates.isChecked():
            self.check_points_aggregates = True
        if self.cb_points_pasta.isChecked():
            self.check_points_pasta = True

        if not self.cb_pores.isChecked():
            self.check_pores = False
        if not self.cb_points.isChecked():
            self.check_points = False
        if not self. cb_points_aggregates.isChecked():
            self.check_points_aggregates = False
        if not self.cb_points_pasta.isChecked():
            self.check_points_pasta = False

        self.pb_run.setEnabled(False)

        self.start_time = time.time()

        self.log('---SIMULATION STARTED---', color=self.blueColor)
        self.log('Seed value: ' + str(self.seed), color=self.blackColor)

        self.pb_stop.setEnabled(True)
        self.progressBar.setValue(0)

        try:
            self.simulation_controller.start()
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(self, "Undefined Mode", str(exc))
            return


    """
    Kept for compatibility with legacy calls
    """

    def stop(self):
        self.simulation_controller.stop()

    def stop_simulation(self):
        self.simulation_controller.stop()

    """
    Reset variables to run a new simulation
    """
    def limpiar(self):
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
        self.list_ptos_react_pasta = []
        self.list_ptos_react_aggregates = []
        self.todos_ptos_react = []
        self.aggregates_puestos = False
        self.pores_puestos = False
        if not self.cb_seed.isChecked():
            self.le_seed.clear()
            self.seed = None

    def update(self):
        if self.le_seed.text():
            self.seed = int(self.le_seed.text())
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
        if self.le_dmax_ptos_aggregates.text():
            self.dpto_max_aggregates = float(self.le_dmax_ptos_aggregates.text())
        if self.le_dmin_ptos_aggregates.text():
            self.dpto_min_aggregates = float(self.le_dmin_ptos_aggregates.text())
        if self.le_Pptos_aggregates.text():
            self.Ppto_react_aggregates = float(self.le_Pptos_aggregates.text())
        if self.le_dmax_ptos_pasta.text():
            self.dpto_max_pasta = float(self.le_dmax_ptos_pasta.text())
        if self.le_dmin_ptos_pasta.text():
            self.dpto_min_pasta = float(self.le_dmin_ptos_pasta.text())
        if self.le_Pptos_pasta.text():
            self.Ppto_react_pasta = float(self.le_Pptos_pasta.text())
        if self.dsb_coef_f.value():
            self.Pagg = self.dsb_coef_f.value()

        self.A = self.x * self.y
        self.A_pores = self.A * self.Pporos
        self.A_points_pasta = self.A * self.Ppto_react_pasta
        self.A_points_aggregates = self.A * self.Ppto_react_aggregates
        # self.A_points_total = self.A * (self.Ppto_react_pasta + self.Ppto_react_aggregates)

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
        if self.cb_pores.isChecked():
            self.lb_pores.setEnabled(True)
            self.le_dmax.setEnabled(True)
            self.lb_dmax.setEnabled(True)
            self.le_dmin.setEnabled(True)
            self.lb_dmin.setEnabled(True)
            self.le_Pporos.setEnabled(True)
            self.lb_Pporos.setEnabled(True)
        if not self.cb_pores.isChecked():
            self.lb_pores.setEnabled(False)
            self.le_dmax.setEnabled(False)
            self.lb_dmax.setEnabled(False)
            self.le_dmin.setEnabled(False)
            self.lb_dmin.setEnabled(False)
            self.le_Pporos.setEnabled(False)
            self.lb_Pporos.setEnabled(False)

        if self.cb_points.isChecked():
            self.lb_points.setEnabled(True)
            self.lb_dmin_ptos.setEnabled(True)
            self.lb_dmax_ptos.setEnabled(True)
            self.lb_Pptos.setEnabled(True)
            self.cb_points_aggregates.setEnabled(True)
            self.cb_points_pasta.setEnabled(True)
        if not self.cb_points.isChecked():
            self.lb_points.setEnabled(False)
            self.lb_dmin_ptos.setEnabled(False)
            self.lb_dmax_ptos.setEnabled(False)
            self.lb_Pptos.setEnabled(False)
            self.cb_points_aggregates.setEnabled(False)
            self.cb_points_pasta.setEnabled(False)

            self.cb_points_aggregates.setChecked(False)
            self.cb_points_pasta.setChecked(False)

        if self.cb_points_aggregates.isChecked():
            self.lb_points_aggregates.setEnabled(True)
            self.le_dmax_ptos_aggregates.setEnabled(True)
            self.le_dmin_ptos_aggregates.setEnabled(True)
            self.le_Pptos_aggregates.setEnabled(True)
        if not self.cb_points_aggregates.isChecked():
            self.lb_points_aggregates.setEnabled(False)
            self.le_dmax_ptos_aggregates.setEnabled(False)
            self.le_dmin_ptos_aggregates.setEnabled(False)
            self.le_Pptos_aggregates.setEnabled(False)

        if self.cb_points_pasta.isChecked():
            self.lb_points_pasta.setEnabled(True)
            self.le_dmax_ptos_pasta.setEnabled(True)
            self.le_dmin_ptos_pasta.setEnabled(True)
            self.le_Pptos_pasta.setEnabled(True)
        if not self.cb_points_pasta.isChecked():
            self.lb_points_pasta.setEnabled(False)
            self.le_dmax_ptos_pasta.setEnabled(False)
            self.le_dmin_ptos_pasta.setEnabled(False)
            self.le_Pptos_pasta.setEnabled(False)

        if self.cb_seed.isChecked():
            self.lb_seed.setEnabled(True)
            self.le_seed.setEnabled(True)
        if not self.cb_seed.isChecked():
            self.lb_seed.setEnabled(False)
            self.le_seed.setEnabled(False)

    def ver_structure(self):
        self.dlg.show()

    def pasar_list_pores(self, list):
        self.list_pores = list

    def pasar_list_coarse(self, list):
        self.list_aggregates_coarse = list

    def pasar_list_fine(self, list):
        self.list_aggregates_fine= list

    def pasar_list_reactive(self, list):
        self.list_ptos_react = list


    """
    Export aggregate, pore, and reactive-point distribution to DXF
    """

    def exportar_structure(self):
        if self.mode not in ("circulos", "ellipses", "poligonos"):
            QtWidgets.QMessageBox.warning(self, "Undefined Mode", "You must select a mode before exporting.")
            return

        filtros = "DXF (*.dxf);;SVG (*.svg);;JSON (*.json);;Gmsh GEO (*.geo)"
        name, selected_filter = QtWidgets.QFileDialog.getSaveFileName(None, "Export Structure", "", filtros)
        if name == "":
            return

        domain = {
            "x": float(self.x) if self.x else None,
            "y": float(self.y) if self.y else None,
        }

        try:
            export_structure_file(
                path=name,
                selected_filter=selected_filter,
                mode=self.mode,
                list_pores=self.list_pores,
                list_aggregates_coarse=self.list_aggregates_coarse,
                list_aggregates_fine=self.list_aggregates_fine,
                list_ptos_react=self.list_ptos_react,
                domain=domain,
            )
            self.log('---STRUCTURE EXPORTED---', color=self.blueColor)
        except StructureExportError as exc:
            QtWidgets.QMessageBox.warning(self, "Export Error", str(exc))
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self, "Export Error", f"Could not export structure: {exc}")

    def exportar_structure_circulos(self):
        print(self.list_pores)
        print(self.list_aggregates_coarse)
        print(self.list_aggregates_fine)
        print(self.list_ptos_react)
        name, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Export Structure", "", "DXF(*.dxf)")
        if name == "":
            return
        if "." not in name:
            name += ".dxf"
        doc = ezdxf.new()
        doc.layers.new(name='Pores')
        doc.layers.new(name='Aggregates coarse')
        doc.layers.new(name='Aggregates fine')
        doc.layers.new(name='Ptos_reactive')
        msp = doc.modelspace()
        for i in self.list_pores:
            msp.add_circle([i[0], i[1]], i[2], dxfattribs={'layer': 'Pores'})
        for i in self.list_aggregates_coarse:
            msp.add_circle([i[0], i[1]], i[2], dxfattribs={'layer': 'Aggregates coarse'})
        for i in self.list_aggregates_fine:
            msp.add_circle([i[0], i[1]], i[2], dxfattribs={'layer': 'Aggregates fine'})
        for i in self.list_ptos_react:
            msp.add_circle([i[0], i[1]], i[2], dxfattribs={'layer': 'Ptos_reactive'})

        doc.saveas(name)
        self.log('---STRUCTURE EXPORTED---', color=self.blueColor)

    def exportar_structure_ellipses(self):
        name, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Export Structure", "", "DXF(*.dxf)")
        if name == "":
            return
        if "." not in name:
            name += ".dxf"

        doc = ezdxf.new()
        doc.layers.new(name='Pores')
        doc.layers.new(name='Aggregates coarse')
        doc.layers.new(name='Aggregates fine')
        doc.layers.new(name='Ptos_reactive')
        msp = doc.modelspace()

        # Export pores as circles.
        for i in self.list_pores:
            msp.add_circle([i[0], i[1]], i[2], dxfattribs={'layer': 'Pores'})

        # Sample points along a rotated ellipse so it can be exported as a polyline.
        def points_elipse(x, y, a, b, angulo_deg, num_points=60):
            angulo_rad = np.radians(angulo_deg)
            t = np.linspace(0, 2 * np.pi, num_points)
            # Local ellipse coordinates before rotation.
            px = a * np.cos(t)
            py = b * np.sin(t)
            # Rotate and translate the sampled points.
            xr = px * np.cos(angulo_rad) - py * np.sin(angulo_rad) + x
            yr = px * np.sin(angulo_rad) + py * np.cos(angulo_rad) + y
            return list(zip(xr, yr))

        # Export coarse aggregates as ellipses.
        for e in self.list_aggregates_coarse:
            x, y, a, b, angulo = e
            pts = points_elipse(x, y, a, b, angulo)
            msp.add_lwpolyline(pts, close=True, dxfattribs={'layer': 'Aggregates coarse'})

        # Export fine aggregates as ellipses.
        for e in self.list_aggregates_fine:
            x, y, a, b, angulo = e
            pts = points_elipse(x, y, a, b, angulo)
            msp.add_lwpolyline(pts, close=True, dxfattribs={'layer': 'Aggregates fine'})

        # Export reactive points as circles.
        for i in self.list_ptos_react:
            msp.add_circle([i[0], i[1]], i[2], dxfattribs={'layer': 'Ptos_reactive'})

        doc.saveas(name)
        self.log('---STRUCTURE EXPORTED---', color=self.blueColor)

    def exportar_structure_poligonos(self):
        name, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Export Structure", "", "DXF(*.dxf)")
        if name == "":
            return
        if "." not in name:
            name += ".dxf"

        doc = ezdxf.new()
        doc.layers.new(name='Pores')
        doc.layers.new(name='Aggregates coarse')
        doc.layers.new(name='Aggregates fine')
        doc.layers.new(name='Ptos_reactive')
        msp = doc.modelspace()

        # Export pores as circles.
        for pore in self.list_pores:
            if isinstance(pore, (list, tuple)) and len(pore) >= 3:
                msp.add_circle([pore[0], pore[1]], pore[2], dxfattribs={'layer': 'Pores'})
            elif hasattr(pore, "exterior"):
                pts = list(pore.exterior.coords)
                if len(pts) > 1 and pts[0] == pts[-1]:
                    pts = pts[:-1]
                if len(pts) >= 3:
                    msp.add_lwpolyline(pts, close=True, dxfattribs={'layer': 'Pores'})

        # Export aggregates; the input can be Shapely polygons or raw vertex lists.
        def extract_polygon_vertices(obj):
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

        for polygon in self.list_aggregates_coarse:
            pts = extract_polygon_vertices(polygon)
            if pts is not None:
                msp.add_lwpolyline(pts, close=True, dxfattribs={'layer': 'Aggregates coarse'})

        for polygon in self.list_aggregates_fine:
            pts = extract_polygon_vertices(polygon)
            if pts is not None:
                msp.add_lwpolyline(pts, close=True, dxfattribs={'layer': 'Aggregates fine'})

        # Export reactive points as circles.
        for pkreactivo in self.list_ptos_react:
            msp.add_circle([pkreactivo[0], pkreactivo[1]], pkreactivo[2], dxfattribs={'layer': 'Ptos_reactive'})

        doc.saveas(name)
        self.log('---STRUCTURE EXPORTED---', color=self.blueColor)
    """
    Saves the full image, independent of current zoom
    """
    def save_image(self):
        filtros = "PNG (*.png);;JPEG (*.jpg);;TIFF (*.tiff);;BMP (*.bmp)"
        name, selected_filter = QtWidgets.QFileDialog.getSaveFileName(None, "Save Image", "", filtros)
        if name == "":
            return
        save_current_view(self, name, selected_filter)
        self.log('---IMAGE SAVED---', color=self.blueColor)

    def open_tutorial_pdf(self):
        docs_dir = Path(__file__).resolve().parent / "docs"
        primary_pdf = docs_dir / "Meso2D_user_tutorial_EN.pdf"
        fallback_pdf = docs_dir / "Meso2D_user_tutorial.pdf"

        tutorial_path = primary_pdf if primary_pdf.exists() else fallback_pdf
        if not tutorial_path.exists():
            QtWidgets.QMessageBox.warning(
                self,
                "Tutorial Not Found",
                "Could not find the tutorial PDF in the docs folder."
            )
            return

        opened = QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(tutorial_path)))
        if not opened:
            QtWidgets.QMessageBox.warning(
                self,
                "Open Error",
                f"Could not open tutorial file: {tutorial_path}"
            )


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

    def log(self, mensaje=None, color=None):
        self.tb_info.setTextColor(color)
        self.tb_info.append(mensaje)

    def log_worker(self, mensaje=None):
        self.tb_info.setTextColor(self.blackColor)
        self.tb_info.append(mensaje)

    def log_worker_error(self, mensaje=None):
        self.tb_info.setTextColor(self.redColor)
        self.tb_info.append(mensaje)

    def show_progress(self, percentage):
        self.progressBar.setValue(percentage)


class Viewer_image(QtWidgets.QDialog, Ui_Dialog_GV):
    def __init__(self):
        super(Viewer_image, self).__init__()
        self.setupUi(self)

        self.gv_viewer = MiGraphicsView()
        self.gv_viewer.setObjectName("gv_viewer")
        self.gridLayout.addWidget(self.gv_viewer, 0, 0, 1, 2)

        self.pushButton.clicked.connect(self.save)
        self.pushButton_2.clicked.connect(self.close)

    def save(self):
        filtros = "PNG (*.png);;JPEG (*.jpg);;TIFF (*.tiff);;BMP (*.bmp)"
        name, selected_filter = QtWidgets.QFileDialog.getSaveFileName(None, "Save Image", "", filtros)
        if name == "":
            return
        save_viewport_image(self, name, selected_filter)
        """The saved image always corresponds to the full structure, regardless of the viewer zoom."""

    def close(self):
        Viewer_image.hide(self)


class Controlador:
    def __init__(self):
        self.selector = Selector()
        self.selector.mode_escogido.connect(self.open_mainprogram)
        self.selector.show()

    def open_mainprogram(self, mode):
        self.mainprogram = mainProgram(mode)
        self.mainprogram.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    c = Controlador()
    sys.exit(app.exec_())


