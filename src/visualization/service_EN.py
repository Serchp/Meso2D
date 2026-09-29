import os

from PyQt5 import QtCore, QtGui


def _resolve_image_path(path, selected_filter=""):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"):
        return path, ext

    selected_filter_lower = (selected_filter or "").lower()
    if "tiff" in selected_filter_lower or "tif" in selected_filter_lower:
        return path + ".tiff", ".tiff"
    if "bmp" in selected_filter_lower:
        return path + ".bmp", ".bmp"
    if "jpeg" in selected_filter_lower or "jpg" in selected_filter_lower:
        return path + ".jpg", ".jpg"
    return path + ".png", ".png"


def _render_widget_to_image(widget, scale=1, white_background=False):
    width = max(1, widget.width() * scale)
    height = max(1, widget.height() * scale)
    image = QtGui.QImage(width, height, QtGui.QImage.Format_ARGB32)
    if white_background:
        image.fill(QtCore.Qt.white)
    else:
        image.fill(QtCore.Qt.transparent)

    painter = QtGui.QPainter(image)
    painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
    painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)
    if scale != 1:
        painter.scale(scale, scale)
    widget.render(painter)
    painter.end()
    return image


def _save_widget_image(widget, path, selected_filter=""):
    final_path, ext = _resolve_image_path(path, selected_filter)
    image = _render_widget_to_image(widget, scale=2, white_background=(ext in (".jpg", ".jpeg", ".bmp", ".tif", ".tiff")))
    image.save(final_path)


def _save_full_photo_pixmap(graphics_view, path, selected_filter=""):
    if graphics_view is None:
        return

    final_path, ext = _resolve_image_path(path, selected_filter)
    photo_item = getattr(graphics_view, "_photo", None)
    pixmap = photo_item.pixmap() if photo_item is not None else QtGui.QPixmap()

    if pixmap.isNull():
        _save_widget_image(graphics_view.viewport(), path, selected_filter)
        return

    image = pixmap.toImage()
    if ext in (".jpg", ".jpeg", ".bmp", ".tif", ".tiff"):
        rgb = QtGui.QImage(image.size(), QtGui.QImage.Format_RGB32)
        rgb.fill(QtCore.Qt.white)
        painter = QtGui.QPainter(rgb)
        painter.drawImage(0, 0, image)
        painter.end()
        image = rgb
    image.save(final_path)


def save_viewport_image(dialog, path, selected_filter=""):
    graphics_view = getattr(dialog, "gv_viewer", getattr(dialog, "gv_visor", None))
    _save_full_photo_pixmap(graphics_view, path, selected_filter)


def save_current_view(window, path, selected_filter=""):
    dialog = getattr(window, "dlg", None)
    graphics_view = None if dialog is None else getattr(dialog, "gv_viewer", getattr(dialog, "gv_visor", None))
    _save_full_photo_pixmap(graphics_view, path, selected_filter)
