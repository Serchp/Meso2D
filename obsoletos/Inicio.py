"""
Código de inicio.ui a Main_inicio.py
Modificado para incluir las funciones

Pretende ser un programa inicial que al pulsar en el botón correspondiente abra programa círculos o elipses
"""

import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from Main_inicio import Ui_MainWindow as Menuinicio
from Main02 import Ui_MainWindow as circulos


class Window(QtWidgets.QMainWindow, Menuinicio):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)

        self.setupUi(self)
        self.pb_circulos.clicked.connect(self.pb_circulos_pulsar)
        # self.graph = Graph(self)

        # just to see the two windows side-by-side
        # self.move(500, 400)
        # self.graph.move(self.x()+self.width()+20, self.y())

    def pb_circulos_pulsar(self):
        print('pb clicked')
        self.close()
        self.graph = Graph(self)
        self.graph.show()


class Graph(QtWidgets.QMainWindow, circulos):

    # def __init__(self, parent=None):
    def __init__(self, parent=Window):
        super(Graph, self).__init__(parent)
        self.setupUi(self)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = Window()
    MainWindow.show()
    app.exec()