# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\48560330q\PycharmProjects\meso_2D\visor.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Visor(object):
    def setupUi(self, Visor):
        Visor.setObjectName("Visor")
        Visor.resize(560, 469)
        self.centralwidget = QtWidgets.QWidget(Visor)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.graphicsView = QtWidgets.QGraphicsView(self.centralwidget)
        self.graphicsView.setObjectName("graphicsView")
        self.gridLayout.addWidget(self.graphicsView, 0, 0, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)
        Visor.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(Visor)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 560, 21))
        self.menubar.setObjectName("menubar")
        self.menuArchivo = QtWidgets.QMenu(self.menubar)
        self.menuArchivo.setObjectName("menuArchivo")
        Visor.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(Visor)
        self.statusbar.setObjectName("statusbar")
        Visor.setStatusBar(self.statusbar)
        self.actionGuardar_Imagen = QtWidgets.QAction(Visor)
        self.actionGuardar_Imagen.setObjectName("actionGuardar_Imagen")
        self.actionExportar_DXF = QtWidgets.QAction(Visor)
        self.actionExportar_DXF.setObjectName("actionExportar_DXF")
        self.actionSalir = QtWidgets.QAction(Visor)
        self.actionSalir.setObjectName("actionSalir")
        self.menuArchivo.addAction(self.actionGuardar_Imagen)
        self.menuArchivo.addAction(self.actionExportar_DXF)
        self.menuArchivo.addSeparator()
        self.menuArchivo.addAction(self.actionSalir)
        self.menubar.addAction(self.menuArchivo.menuAction())

        self.retranslateUi(Visor)
        QtCore.QMetaObject.connectSlotsByName(Visor)

    def retranslateUi(self, Visor):
        _translate = QtCore.QCoreApplication.translate
        Visor.setWindowTitle(_translate("Visor", "MainWindow"))
        self.menuArchivo.setTitle(_translate("Visor", "Archivo"))
        self.actionGuardar_Imagen.setText(_translate("Visor", "Guardar Imagen"))
        self.actionExportar_DXF.setText(_translate("Visor", "Exportar DXF"))
        self.actionSalir.setText(_translate("Visor", "Salir"))

