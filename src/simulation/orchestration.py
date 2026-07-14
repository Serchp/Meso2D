from dataclasses import dataclass
from typing import List, Optional

from PyQt5 import QtWidgets

from worker_base import SimParams
from src.workers import WorkerTodos, WorkerElipses, WorkerPoligonos


@dataclass
class SimulationModel:
    sieve_size: Optional[List[int]] = None
    tpp: Optional[List[int]] = None
    x: Optional[float] = None
    y: Optional[float] = None
    Pagg: Optional[float] = None
    Pporos: Optional[float] = None
    dporo_min: Optional[float] = None
    dporo_max: Optional[float] = None
    r_react: Optional[float] = None
    dpto_max_aridos: Optional[float] = None
    dpto_min_aridos: Optional[float] = None
    dpto_max_pasta: Optional[float] = None
    dpto_min_pasta: Optional[float] = None
    Ppto_react_aridos: Optional[float] = None
    Ppto_react_pasta: Optional[float] = None
    seed: Optional[int] = None

    def to_dict(self):
        return {
            "sieve_size": self.sieve_size,
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
            "seed": self.seed,
        }


def create_worker(modo, params, todo_correcto, check_poros, check_puntos, check_puntos_aridos, check_puntos_pasta):
    if modo == "circulos":
        return WorkerTodos(
            params,
            todo_correcto=todo_correcto,
            check_poros=check_poros,
            check_puntos=check_puntos,
            check_puntos_aridos=check_puntos_aridos,
            check_puntos_pasta=check_puntos_pasta,
        )
    if modo == "elipses":
        return WorkerElipses(
            params,
            todo_correcto=todo_correcto,
            check_poros=check_poros,
            check_puntos=check_puntos,
            check_puntos_aridos=check_puntos_aridos,
            check_puntos_pasta=check_puntos_pasta,
        )
    if modo == "poligonos":
        return WorkerPoligonos(
            params,
            todo_correcto=todo_correcto,
            check_poros=check_poros,
            check_puntos=check_puntos,
            check_puntos_aridos=check_puntos_aridos,
            check_puntos_pasta=check_puntos_pasta,
        )
    raise ValueError("Modo no definido")


class SimulationController:
    def __init__(self, window):
        self.window = window
        self.model = SimulationModel()

    def build_params(self):
        return SimParams(
            sieve_size=self.model.sieve_size,
            tpp=self.model.tpp,
            x=self.model.x,
            y=self.model.y,
            Pagg=self.model.Pagg,
            Pporos=self.model.Pporos,
            dporo_min=self.model.dporo_min,
            dporo_max=self.model.dporo_max,
            r_react=self.model.r_react,
            dpto_max_aridos=self.model.dpto_max_aridos,
            dpto_min_aridos=self.model.dpto_min_aridos,
            dpto_max_pasta=self.model.dpto_max_pasta,
            dpto_min_pasta=self.model.dpto_min_pasta,
            Ppto_react_aridos=self.model.Ppto_react_aridos,
            Ppto_react_pasta=self.model.Ppto_react_pasta,
            seed=self.model.seed,
        )

    def create_worker(self, params):
        return create_worker(
            self.window.modo,
            params,
            todo_correcto=self.window.todo_correcto,
            check_poros=self.window.check_poros,
            check_puntos=self.window.check_puntos,
            check_puntos_aridos=self.window.check_puntos_aridos,
            check_puntos_pasta=self.window.check_puntos_pasta,
        )

    def sync_from_window(self):
        self.model.sieve_size = getattr(self.window, "sieve_size", None)
        self.model.tpp = getattr(self.window, "tpp", None)
        self.model.x = getattr(self.window, "x", None)
        self.model.y = getattr(self.window, "y", None)
        self.model.Pagg = getattr(self.window, "Pagg", None)
        self.model.Pporos = getattr(self.window, "Pporos", None)
        self.model.dporo_min = getattr(self.window, "dporo_min", None)
        self.model.dporo_max = getattr(self.window, "dporo_max", None)
        self.model.r_react = getattr(self.window, "r_react", None)
        self.model.dpto_max_aridos = getattr(self.window, "dpto_max_aridos", None)
        self.model.dpto_min_aridos = getattr(self.window, "dpto_min_aridos", None)
        self.model.dpto_max_pasta = getattr(self.window, "dpto_max_pasta", None)
        self.model.dpto_min_pasta = getattr(self.window, "dpto_min_pasta", None)
        self.model.Ppto_react_aridos = getattr(self.window, "Ppto_react_aridos", None)
        self.model.Ppto_react_pasta = getattr(self.window, "Ppto_react_pasta", None)
        self.model.seed = getattr(self.window, "seed", None)

    def sync_to_window(self):
        self.window.sieve_size = self.model.sieve_size
        self.window.tpp = self.model.tpp
        self.window.x = self.model.x
        self.window.y = self.model.y
        self.window.Pagg = self.model.Pagg
        self.window.Pporos = self.model.Pporos
        self.window.dporo_min = self.model.dporo_min
        self.window.dporo_max = self.model.dporo_max
        self.window.r_react = self.model.r_react
        self.window.dpto_max_aridos = self.model.dpto_max_aridos
        self.window.dpto_min_aridos = self.model.dpto_min_aridos
        self.window.dpto_max_pasta = self.model.dpto_max_pasta
        self.window.dpto_min_pasta = self.model.dpto_min_pasta
        self.window.Ppto_react_aridos = self.model.Ppto_react_aridos
        self.window.Ppto_react_pasta = self.model.Ppto_react_pasta
        self.window.seed = self.model.seed

    def update_from_window(self):
        self._read_form_values()
        self.sync_to_window()

    def _read_form_values(self):
        self.model.seed = self._read_text_value(getattr(self.window, "le_semilla", None), int)
        self.model.y = self._read_text_value(getattr(self.window, "le_y", None), float)
        self.model.x = self._read_text_value(getattr(self.window, "le_x", None), float)
        self.model.dporo_max = self._read_text_value(getattr(self.window, "le_dmax", None), float)
        self.model.dporo_min = self._read_text_value(getattr(self.window, "le_dmin", None), float)
        self.model.Pporos = self._read_text_value(getattr(self.window, "le_Pporos", None), float)
        self.model.dpto_max_aridos = self._read_text_value(getattr(self.window, "le_dmax_ptos_aridos", None), float)
        self.model.dpto_min_aridos = self._read_text_value(getattr(self.window, "le_dmin_ptos_aridos", None), float)
        self.model.Ppto_react_aridos = self._read_text_value(getattr(self.window, "le_Pptos_aridos", None), float)
        self.model.dpto_max_pasta = self._read_text_value(getattr(self.window, "le_dmax_ptos_pasta", None), float)
        self.model.dpto_min_pasta = self._read_text_value(getattr(self.window, "le_dmin_ptos_pasta", None), float)
        self.model.Ppto_react_pasta = self._read_text_value(getattr(self.window, "le_Pptos_pasta", None), float)
        self.model.Pagg = self._read_spin_value(getattr(self.window, "dsb_coef_f", None))
        self.model.sieve_size = self._read_table_column(getattr(self.window, "tabla_dosif", None), 0)
        self.model.tpp = self._read_table_column(getattr(self.window, "tabla_dosif", None), 1)

    def _read_text_value(self, widget, cast):
        if widget is None:
            return None
        text = widget.text()
        if text is None or str(text).strip() == "":
            return None
        return cast(text)

    def _read_spin_value(self, widget):
        if widget is None:
            return None
        value = widget.value()
        if value in (None, ""):
            return None
        return value

    def _read_table_column(self, table, column):
        if table is None:
            return None
        values = []
        for row in range(table.rowCount()):
            item = table.item(row, column)
            text = item.text() if item is not None else ""
            if str(text).strip():
                values.append(int(text))
        return values or None

    def start(self):
        self.sync_from_window()
        params = self.build_params()
        worker = self.create_worker(params)
        self.window.worker = worker
        self.window.thread = worker.start_on_thread()

        worker.progreso.connect(self.window.mostrar_progreso)
        worker.information.connect(self.window.informar_worker)
        worker.information_error.connect(self.window.informar_worker_error)
        worker.imagen.connect(self.window.plotear)
        worker.pore_list.connect(self.window.pasar_lista_poros)
        worker.coarse_list.connect(self.window.pasar_lista_gruesos)
        worker.fine_list.connect(self.window.pasar_lista_finos)
        worker.reactive_list.connect(self.window.pasar_lista_reactivos)

        self.window.thread.start()
        self.window.thread.finished.connect(lambda: self.window.pb_ejecutar.setEnabled(True))
        self.window.thread.finished.connect(lambda: self.window.pb_stop.setEnabled(False))

    def stop(self):
        if getattr(self.window, "worker", None) is not None:
            self.window.worker.stop()
        self.window.pb_stop.setEnabled(False)
        self.window.pb_ejecutar.setEnabled(True)
        self.window.progressBar.setValue(0)
        self.window.informar(
            "Parada solicitada. La simulacion terminara en el siguiente punto de control.",
            color=self.window.blackColor,
        )
