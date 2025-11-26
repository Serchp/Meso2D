# Copiado desde el AgCl3' y editado para la ocasión

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal, QObject, Qt
# from preferencias2 import Ui_Preferencias as preferencias
# from distCarb import Ui_MainWindow
# from dC import pref

from PyQt5.QtWidgets import QMessageBox, QFileDialog, QTableWidget, QTableWidgetItem, QGraphicsItem, QGraphicsLineItem, \
    QGraphicsEllipseItem
# import cv2


class MiGraphicsView(QtWidgets.QGraphicsView):
    senyal_escala = pyqtSignal()
    senyal_linea = pyqtSignal()
    senyal_punto = pyqtSignal()

    def __init__(self):
        QtWidgets.QGraphicsView.__init__(self)
        # super(MiGraphicsView, self).__init__()

        self._zoom = 0
        self.scene = QtWidgets.QGraphicsScene(self)
        self._photo = QtWidgets.QGraphicsPixmapItem()
        self.scene.addItem(self._photo)
        self.setScene(self.scene)

        self.escala = []
        self.linea = []
        self.puntos = []
        self.distancias = []
        self.distanciasreales = []

        self.elipses = []

        self.apintar = None

        self.existeescala = False
        self.existelinea = False
        self.valor_de_escala = None
        self.empty = True

        self.pen_escala = QtGui.QPen(Qt.green)
        self.pen_linea = QtGui.QPen(Qt.red)
        self.pen_punto = QtGui.QPen(Qt.red)
        self.brush = QtGui.QBrush(Qt.SolidPattern)
        self.brush.setColor(Qt.red)

        self.grosor_escala = 1
        self.grosor_linea = 1
        self.grosor_puntos = 1

        self.color_escala = 0
        self.color_linea = 0
        self.color_puntos = 0

        self.elipses_cara_1 =[]
        self.elipses_cara_2 =[]
        self.elipses_cara_3 =[]
        self.elipses_cara_4 =[]

        self.puntos_1 = []
        self.distancias_1 = []
        self.distanciasreales_1 = []

        self.puntos_2 = []
        self.distancias_2 = []
        self.distanciasreales_2 = []

        self.puntos_3 = []
        self.distancias_3 = []
        self.distanciasreales_3 = []

        self.puntos_4 = []
        self.distancias_4 = []
        self.distanciasreales_4 = []

        self.distanciasreales = self.distanciasreales_1 + self.distanciasreales_2 + self.distanciasreales_3 + self.distanciasreales_4

    def hasPhoto(self):
        return not self.empty

    def fitInView(self, scale=True):
        rect = QtCore.QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if self.hasPhoto():
                unity = self.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                viewrect = self.viewport().rect()
                scenerect = self.transform().mapRect(rect)
                factor = min(viewrect.width() / scenerect.width(),
                             viewrect.height() / scenerect.height())
                self.scale(factor, factor)
            self._zoom = 0
            print('fitInView')

    def setPhoto(self, pixmap=None):
        self._zoom = 0
        # im = QtGui.QPixmap('C:\\Users\\48560330Q\\PycharmProjects\\DCarb\\distCarb.jpg')
        if pixmap and not pixmap.isNull():
            self.empty = False
            # self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
            self._photo.setPixmap(pixmap)
        else:
            self.empty = True
            # self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            self._photo.setPixmap(QtGui.QPixmap())
        # print('setPhoto')
        self.fitInView()

    def wheelEvent(self, event):
        if self.hasPhoto():
            if event.angleDelta().y() > 0:
                factor = 1.25
                self._zoom += 1
            else:
                factor = 0.8
                self._zoom -= 1
            if self._zoom > 0:
                self.scale(factor, factor)
            elif self._zoom == 0:
                self.fitInView()
            else:
                self._zoom = 0

    def paintObject(self, e):
        if self.apintar != None:
            object = self.apintar
            if object == 1:  # Escala
                if self.existeescala == False:
                    self.escala = []
                    self.laescala = QGraphicsLineItem(self.startX, self.startY, e.x(), e.y())
                    self.pen_escala.setWidth(self.grosor_escala)
                    if self.color_escala == 0:
                        self.pen_escala.setColor(Qt.green)
                    elif self.color_escala == 1:
                        self.pen_escala.setColor(Qt.red)
                    elif self.color_escala == 2:
                        self.pen_escala.setColor(Qt.blue)
                    elif self.color_escala == 3:
                        self.pen_escala.setColor(Qt.yellow)
                    elif self.color_escala == 4:
                        self.pen_escala.setColor(Qt.black)
                    elif self.color_escala == 5:
                        self.pen_escala.setColor(Qt.white)
                    # for key in self.colores:
                    #     if str(self.color_escala) == key:
                    #         self.pen_escala.setColor(self.colores[key])
                    self.laescala.setPen(self.pen_escala)
                    self.scene.addItem(self.laescala)
                    self.setScene(self.scene)
                    self.escala.extend((self.startX, self.startY, e.x(), e.y()))
                    self.existeescala = True
                    self.apintar = None
                    self.senyal_escala.emit()
            elif object == 2:  # Linea
                if self.existelinea == False:
                    self.linea = []
                    # pen = QtGui.QPen(Qt.red)
                    self.lalinea = QGraphicsLineItem(self.startX, self.startY, e.x(), e.y())
                    self.pen_linea.setWidth(self.grosor_linea)
                    if self.color_linea == 0:
                        self.pen_linea.setColor(Qt.red)
                    elif self.color_linea == 1:
                        self.pen_linea.setColor(Qt.green)
                    elif self.color_linea == 2:
                        self.pen_linea.setColor(Qt.blue)
                    elif self.color_linea == 3:
                        self.pen_linea.setColor(Qt.yellow)
                    elif self.color_linea == 4:
                        self.pen_linea.setColor(Qt.black)
                    elif self.color_linea == 5:
                        self.pen_linea.setColor(Qt.white)
                    self.lalinea.setPen(self.pen_linea)
                    self.scene.addItem(self.lalinea)
                    self.setScene(self.scene)
                    self.linea.extend((self.startX, self.startY, e.x(), e.y()))
                    self.existelinea = True
                    self.apintar = None
                    self.senyal_linea.emit()
            elif object == 3:  # Puntos
                # pen = QtGui.QPen(Qt.red)
                # self.scene.addItem(self.scene.addEllipse(e.x(), e.y(), 2, 2, self.pen_punto, brush))
                if self.color_puntos == 0:
                    self.pen_punto.setColor(Qt.red)
                    self.brush.setColor(Qt.red)
                elif self.color_puntos == 1:
                    self.pen_punto.setColor(Qt.green)
                    self.brush.setColor(Qt.green)
                elif self.color_puntos == 2:
                    self.pen_punto.setColor(Qt.blue)
                    self.brush.setColor(Qt.blue)
                elif self.color_puntos == 3:
                    self.pen_punto.setColor(Qt.yellow)
                    self.brush.setColor(Qt.yellow)
                elif self.color_puntos == 4:
                    self.pen_punto.setColor(Qt.black)
                    self.brush.setColor(Qt.black)
                elif self.color_puntos == 5:
                    self.pen_punto.setColor(Qt.white)
                    self.brush.setColor(Qt.white)
                # self.scene.addItem(self.scene.addEllipse(e.x(), e.y(), self.grosor_puntos, self.grosor_puntos, self.pen_punto, self.brush)) # funciona
                newpos = 0.5*self.grosor_puntos
                # self.elipse = self.scene.addEllipse(e.x()-newpos, e.y()-newpos, self.grosor_puntos, self.grosor_puntos, self.pen_punto, self.brush) # funciona
                self.elipse = self.scene.addEllipse(e.x()-newpos, e.y()-newpos, self.grosor_puntos, self.grosor_puntos, self.pen_punto, self.brush) # funciona
                """
                funciona
                """
                # self.elipses.append(self.elipse)
                # self.puntos.append(e.__pos__())
                self.setScene(self.scene)
                # self.senyal_punto.emit()
                """
                hasta aquí
                """
                self.position = e.__pos__()
                # print(self.position)
                # print(e.__pos__())
                self.senyal_punto.emit()

    def borrarescala(self):
        if self.existeescala:
            self.scene.removeItem(self.laescala)
            self.existeescala = False

    def borrarlinea(self):
        if self.existelinea:
            self.scene.removeItem(self.lalinea)
            self.existelinea = False

    def borrarpunto(self, puntiko):
        self.puntos.pop(puntiko)
        self.scene.removeItem(puntiko)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            e = QtCore.QPointF(self.mapToScene(event.pos()))
            self.startX = e.x()
            self.startY = e.y()
        if event.button() == Qt.RightButton:
            self._dragPos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            e = QtCore.QPointF(self.mapToScene(event.pos()))
            self.paintObject(e)
        if self.cursor() == Qt.ClosedHandCursor:
            self.setCursor(Qt.ArrowCursor)

    def mouseMoveEvent(self, event):
        if event.button() == Qt.LeftButton:
            e = QtCore.QPointF(self.mapToScene(event.pos()))
        if event.buttons() == Qt.RightButton:
            newPos = event.pos()
            diff = newPos - self._dragPos
            self._dragPos = newPos
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - diff.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - diff.y())
