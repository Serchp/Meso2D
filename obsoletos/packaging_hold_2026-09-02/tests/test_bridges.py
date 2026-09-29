import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.io.project_bridge import apply_project_payload, load_project_from_file
from src.io.structure_export_bridge import export_structure_file


class BridgeCompatibilityTests(unittest.TestCase):
    def test_project_bridge_normalizes_spanish_payload_keys(self):
        spanish_payload = {
            "sieve_size": [4, 2],
            "tpp": [50, 100],
            "x": 20.0,
            "y": 10.0,
            "Pagg": 0.4,
            "Pporos": 0.12,
            "dporo_min": 0.4,
            "dporo_max": 1.2,
            "r_react": 0.0,
            "dpto_max_aridos": 1.1,
            "dpto_min_aridos": 0.3,
            "dpto_max_pasta": 0.9,
            "dpto_min_pasta": 0.2,
            "Ppto_react_aridos": 0.04,
            "Ppto_react_pasta": 0.02,
            "seed": 123,
        }

        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "project.txt")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(spanish_payload, fh)

            loaded = load_project_from_file(path)

        self.assertIn("dpto_max_aggregates", loaded)
        self.assertIn("dpto_min_aggregates", loaded)
        self.assertIn("Ppto_react_aggregates", loaded)
        self.assertEqual(loaded["dpto_max_aggregates"], 1.1)
        self.assertEqual(loaded["Ppto_react_aggregates"], 0.04)

        window = type("Window", (), {})()
        apply_project_payload(window, loaded)
        self.assertEqual(window.dpto_max_aggregates, 1.1)
        self.assertEqual(window.dpto_max_aridos, 1.1)
        self.assertEqual(window.Ppto_react_aggregates, 0.04)
        self.assertEqual(window.Ppto_react_aridos, 0.04)

    def test_structure_export_bridge_normalizes_spanish_mode_alias(self):
        with tempfile.TemporaryDirectory() as td:
            out_path = os.path.join(td, "estructura")
            final_path = export_structure_file(
                path=out_path,
                selected_filter="JSON (*.json)",
                modo="elipses",
                lista_poros=[[1.0, 1.0, 0.5]],
                lista_aridos_gruesos=[[2.0, 2.0, 1.0, 0.5, 15.0]],
                lista_aridos_finos=[],
                lista_ptos_react=[],
                domain={"x": 10.0, "y": 10.0},
            )

            self.assertTrue(final_path.endswith(".json"))
            self.assertTrue(os.path.exists(final_path))

            with open(final_path, "r", encoding="utf-8") as fh:
                payload = json.load(fh)

            self.assertEqual(payload["mode"], "ellipses")

    def test_meso2d_controller_opens_mode_window(self):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

        from PyQt5.QtWidgets import QApplication
        import Meso2d

        app = QApplication.instance() or QApplication([])

        with patch.object(Meso2d.Selector, "show", lambda self: None), patch.object(
            Meso2d.mainProgram, "show", lambda self: None
        ):
            controller = Meso2d.Controlador()
            controller.open_mainprogram("circulos")
            self.assertIsNotNone(controller.mainprogram)

            if controller.mainprogram is not None:
                controller.mainprogram.close()
            controller.selector.close()


if __name__ == "__main__":
    unittest.main()
