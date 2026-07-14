from PyQt5 import QtGui


def save_viewport_image(dialog, path):
    if "." not in path:
        path += ".png"
    pixmap = QtGui.QPixmap(dialog.gv_visor.viewport().size())
    dialog.gv_visor.viewport().render(pixmap)
    pixmap.save(path)


def save_current_view(window, path):
    if "." not in path:
        path += ".png"
    pixmap = QtGui.QPixmap(window.dlg.gv_visor.viewport().size())
    window.dlg.gv_visor.viewport().render(pixmap)
    pixmap.save(path)
