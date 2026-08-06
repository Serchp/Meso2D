

from dataclasses import dataclass
from typing import List, Optional
from PyQt5.QtCore import QObject, pyqtSignal, QThread
import time


class SimulationStopped(Exception):
    """Internal signal used to cooperatively abort a simulation."""
    pass


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
    dpto_max_aggregates: Optional[float]
    dpto_min_aggregates: Optional[float]
    dpto_max_pasta: Optional[float]
    dpto_min_pasta: Optional[float]
    Ppto_react_aggregates: float
    Ppto_react_pasta: float
    seed: int


class WorkerBase(QObject):
    # Signals compatible with Meso2D_refactor.py
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    information = pyqtSignal(str)
    information_error = pyqtSignal(str)
    image = pyqtSignal(object)
    pore_list = pyqtSignal(list)
    coarse_list = pyqtSignal(list)
    fine_list = pyqtSignal(list)
    reactive_list = pyqtSignal(list)

    def __init__(self, params):
        super().__init__()
        self.params = params
        self._stop = False

    def stop(self):
        """Signal to cooperatively stop the worker."""
        self._stop = True
        self.information.emit("Worker stop requested.")

    def check_stop(self):
        """Check whether simulation stop was requested and abort cooperatively."""
        if self._stop:
            self.information.emit("Simulation stopped by user.")
            raise SimulationStopped()

    def simulate(self):
        """
        Example implementation: concrete workers should override
        this method. It shows the expected pattern: periodically check self._stop.
        """
        try:
            steps = 100
            for i in range(steps):
                if self._stop:
                    self.information.emit("Simulation stopped by user.")
                    break
                # dummy work / placeholder
                time.sleep(0.01)
                # percentage = int((i + 1) / steps * 100)
                percentage = 0
                self.progress.emit(percentage)
            # emit example (empty) outputs to maintain compatibility
            self.pore_list.emit([])
            self.coarse_list.emit([])
            self.fine_list.emit([])
            self.reactive_list.emit([])
            self.finished.emit()
        except Exception as e:
            self.information_error.emit(f"Worker error: {e}")
            self.finished.emit()

    def start_on_thread(self) -> QThread:
        """
        Move this worker to a QThread and connect basic signals.
        Returns the QThread instance (caller must start it with thread.start()).
        """
        thread = QThread()
        self.moveToThread(thread)
        thread.started.connect(self.simulate)
        self.finished.connect(thread.quit)
        self.finished.connect(self.deleteLater)
        thread.finished.connect(thread.deleteLater)
        return thread

