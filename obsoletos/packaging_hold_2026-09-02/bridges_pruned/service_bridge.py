from src.visualization.service_EN import _resolve_image_path, _render_widget_to_image


def _resolve_viewer(dialog):
    return getattr(dialog, "gv_viewer", getattr(dialog, "gv_visor", None))


def _resolve_main_viewer(window):
    dialog = getattr(window, "dlg", None)
    if dialog is None:
        return None
    return _resolve_viewer(dialog)


def _save_full_photo_pixmap(graphics_view, path, selected_filter=""):
    if graphics_view is None:
        return

    final_path, ext = _resolve_image_path(path, selected_filter)
    photo_item = getattr(graphics_view, "_photo", None)
    pixmap = photo_item.pixmap() if photo_item is not None else None

    if pixmap is None or pixmap.isNull():
        image = _render_widget_to_image(
            graphics_view.viewport(),
            scale=2,
            white_background=(ext in (".jpg", ".jpeg", ".bmp", ".tif", ".tiff")),
        )
        image.save(final_path)
        return

    image = pixmap.toImage()
    if ext in (".jpg", ".jpeg", ".bmp", ".tif", ".tiff"):
        from PyQt5 import QtCore, QtGui

        rgb = QtGui.QImage(image.size(), QtGui.QImage.Format_RGB32)
        rgb.fill(QtCore.Qt.white)
        painter = QtGui.QPainter(rgb)
        painter.drawImage(0, 0, image)
        painter.end()
        image = rgb
    image.save(final_path)


def save_viewport_image(dialog, path, selected_filter=""):
    _save_full_photo_pixmap(_resolve_viewer(dialog), path, selected_filter)


def save_current_view(window, path, selected_filter=""):
    _save_full_photo_pixmap(_resolve_main_viewer(window), path, selected_filter)
