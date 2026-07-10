import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from simulation_controller import SimulationController


class DummyWidget:
    def __init__(self, value=""):
        self._value = value

    def text(self):
        return self._value


class DummySpin:
    def __init__(self, value=0.25):
        self._value = value

    def value(self):
        return self._value


class DummyTable:
    def __init__(self, rows):
        self._rows = rows

    def rowCount(self):
        return len(self._rows)

    def item(self, row, column):
        if row >= len(self._rows):
            return None
        value = self._rows[row][column]
        return type("Item", (), {"text": lambda self: value})()


class SimulationControllerTests(unittest.TestCase):
    def test_update_from_window_reads_numeric_fields(self):
        window = type("Window", (), {})()
        window.le_semilla = DummyWidget("123")
        window.le_y = DummyWidget("10")
        window.le_x = DummyWidget("20")
        window.le_dmax = DummyWidget("4")
        window.le_dmin = DummyWidget("2")
        window.le_Pporos = DummyWidget("15")
        window.le_dmax_ptos_aridos = DummyWidget("6")
        window.le_dmin_ptos_aridos = DummyWidget("1")
        window.le_Pptos_aridos = DummyWidget("3")
        window.le_dmax_ptos_pasta = DummyWidget("5")
        window.le_dmin_ptos_pasta = DummyWidget("2")
        window.le_Pptos_pasta = DummyWidget("4")
        window.dsb_coef_f = DummySpin(0.4)
        window.tabla_dosif = DummyTable([["4", "50"], ["2", "100"]])

        controller = SimulationController(window)
        controller.update_from_window()

        self.assertEqual(controller.model.seed, 123)
        self.assertEqual(controller.model.y, 10.0)
        self.assertEqual(controller.model.x, 20.0)
        self.assertEqual(controller.model.dporo_max, 4.0)
        self.assertEqual(controller.model.dporo_min, 2.0)
        self.assertEqual(controller.model.Pporos, 15.0)
        self.assertEqual(controller.model.dpto_max_aridos, 6.0)
        self.assertEqual(controller.model.dpto_min_aridos, 1.0)
        self.assertEqual(controller.model.Ppto_react_aridos, 3.0)
        self.assertEqual(controller.model.dpto_max_pasta, 5.0)
        self.assertEqual(controller.model.dpto_min_pasta, 2.0)
        self.assertEqual(controller.model.Ppto_react_pasta, 4.0)
        self.assertEqual(controller.model.Pagg, 0.4)
        self.assertEqual(controller.model.sieve_size, [4, 2])
        self.assertEqual(controller.model.tpp, [50, 100])


if __name__ == "__main__":
    unittest.main()
