

from dataclasses import dataclass
from typing import List, Optional
from PyQt5.QtCore import QObject, pyqtSignal, QThread
import time


@dataclass
class SimParams:
    sieve_size: List[int]
    tpp: List[int]
    x: float
    y: float
    Pagg: float
    Pporos: float
    dporo_min: float
    dporo_max: float
    r_react: Optional[float]
    dpto_max_aridos: Optional[float]
    dpto_min_aridos: Optional[float]
    dpto_max_pasta: Optional[float]
    dpto_min_pasta: Optional[float]
    Ppto_react_aridos: float
    Ppto_react_pasta: float
    seed: int


class WorkerBase(QObject):
    # señales compatibles con Meso2D_refactor.py
    progreso = pyqtSignal(int)
    finished = pyqtSignal()
    information = pyqtSignal(str)
    information_error = pyqtSignal(str)
    imagen = pyqtSignal(object)
    pore_list = pyqtSignal(list)
    coarse_list = pyqtSignal(list)
    fine_list = pyqtSignal(list)
    reactive_list = pyqtSignal(list)

    def __init__(self, params):
        super().__init__()
        self.params = params
        self._stop = False

    def stop(self):
        """Señal para parar cooperativamente el worker."""
        self._stop = True
        self.information.emit("Parada solicitada al worker.")

    def simular(self):
        """
        Implementación de ejemplo: los workers concretos deben sobreescribir
        este método. Aquí se muestra el patrón: comprobar self._stop periódicamente.
        """
        try:
            pasos = 100
            for i in range(pasos):
                if self._stop:
                    self.information.emit("Simulación parada por el usuario.")
                    break
                # trabajo ficticio / placeholder
                time.sleep(0.01)
                # porcentaje = int((i + 1) / pasos * 100)
                porcentaje = 0
                self.progreso.emit(porcentaje)
            # emitir resultados de ejemplo (vacíos) para mantener la compatibilidad
            self.pore_list.emit([])
            self.coarse_list.emit([])
            self.fine_list.emit([])
            self.reactive_list.emit([])
            self.finished.emit()
        except Exception as e:
            self.information_error.emit(f"Error en worker: {e}")
            self.finished.emit()

    def start_on_thread(self) -> QThread:
        """
        Mueve este worker a un QThread y conecta las señales básicas.
        Devuelve la instancia de QThread (el caller debe iniciar con thread.start()).
        """
        thread = QThread()
        self.moveToThread(thread)
        thread.started.connect(self.simular)
        self.finished.connect(thread.quit)
        self.finished.connect(self.deleteLater)
        thread.finished.connect(thread.deleteLater)
        return thread
