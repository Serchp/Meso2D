import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.io.structure_export import export_structure_file


class StructureExportTests(unittest.TestCase):
    def setUp(self):
        self.poros = [[10.0, 10.0, 1.0]]
        self.reactivos = [[12.0, 10.0, 0.5]]

    def test_export_json_with_filter_adds_extension(self):
        with tempfile.TemporaryDirectory() as td:
            out_path = os.path.join(td, "estructura")
            final_path = export_structure_file(
                path=out_path,
                selected_filter="JSON (*.json)",
                modo="circulos",
                lista_poros=self.poros,
                lista_aridos_gruesos=[[5.0, 5.0, 2.0]],
                lista_aridos_finos=[[15.0, 5.0, 1.5]],
                lista_ptos_react=self.reactivos,
                domain={"x": 20.0, "y": 20.0},
            )

            self.assertTrue(final_path.endswith(".json"))
            self.assertTrue(os.path.exists(final_path))

            with open(final_path, "r", encoding="utf-8") as fh:
                data = fh.read()
            self.assertIn('"mode": "circulos"', data)
            self.assertIn('"type": "circle"', data)

    def test_export_svg_works_for_ellipses(self):
        with tempfile.TemporaryDirectory() as td:
            out_path = os.path.join(td, "estructura.svg")
            final_path = export_structure_file(
                path=out_path,
                selected_filter="SVG (*.svg)",
                modo="elipses",
                lista_poros=self.poros,
                lista_aridos_gruesos=[[5.0, 5.0, 2.0, 1.0, 30.0]],
                lista_aridos_finos=[[15.0, 5.0, 1.5, 0.7, 0.0]],
                lista_ptos_react=self.reactivos,
                domain={"x": 20.0, "y": 20.0},
            )

            self.assertTrue(os.path.exists(final_path))
            with open(final_path, "r", encoding="utf-8") as fh:
                data = fh.read()
            self.assertIn("<svg", data)
            self.assertIn("<ellipse", data)
            self.assertIn('id="layer_Poros"', data)
            self.assertIn('id="layer_Aridos_gruesos"', data)
            self.assertIn('id="layer_Aridos_finos"', data)
            self.assertIn('id="layer_Ptos_reactivos"', data)

    def test_export_geo_works_for_polygons(self):
        with tempfile.TemporaryDirectory() as td:
            out_path = os.path.join(td, "estructura")
            final_path = export_structure_file(
                path=out_path,
                selected_filter="Gmsh GEO (*.geo)",
                modo="poligonos",
                lista_poros=self.poros,
                lista_aridos_gruesos=[[(1.0, 1.0), (4.0, 1.0), (3.0, 3.0)]],
                lista_aridos_finos=[[(6.0, 1.0), (7.0, 3.0), (5.0, 2.5)]],
                lista_ptos_react=self.reactivos,
                domain={"x": 20.0, "y": 20.0},
            )

            self.assertTrue(final_path.endswith(".geo"))
            self.assertTrue(os.path.exists(final_path))

            with open(final_path, "r", encoding="utf-8") as fh:
                data = fh.read()
            self.assertIn("SetFactory", data)
            self.assertIn("Physical Surface", data)


if __name__ == "__main__":
    unittest.main()
