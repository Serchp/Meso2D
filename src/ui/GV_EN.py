# Copied from AgCl3 and adapted for this project

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal, QObject, Qt
# from preferencias2 import Ui_Preferencias as preferencias
# from distCarb import Ui_MainWindow
# from dC import pref

from PyQt5.QtWidgets import QMessageBox, QFileDialog, QTableWidget, QTableWidgetItem, QGraphicsItem, QGraphicsLineItem, \
    QGraphicsEllipseItem
# import cv2


class MiGraphicsView(QtWidgets.QGraphicsView):

    def __init__(self):
        QtWidgets.QGraphicsView.__init__(self)
        # super(MiGraphicsView, self).__init__()

        self._zoom = 0
        self.scene = QtWidgets.QGraphicsScene(self)
        self._photo = QtWidgets.QGraphicsPixmapItem()
        self.scene.addItem(self._photo)
        self.setScene(self.scene)

        self.empty = True

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


    def mousePressEvent(self, event):
        # if event.button() == Qt.LeftButton:
        #     e = QtCore.QPointF(self.mapToScene(event.pos()))
        #     self.startX = e.x()
        #     self.startY = e.y()
        if event.button() == Qt.RightButton:
            self._dragPos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseReleaseEvent(self, event):
        # if event.button() == Qt.LeftButton:
        #     e = QtCore.QPointF(self.mapToScene(event.pos()))
        #     self.paintObject(e)
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

