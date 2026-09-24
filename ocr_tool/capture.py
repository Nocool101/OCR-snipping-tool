"""**截图**：把整个虚拟桌面抓成一张图，再从中裁出框选区域。

坐标一律用逻辑坐标（与 Qt 一致）；抓到的图是设备像素，故裁剪时要按比例放大。
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QPainter, QPixmap

Rect = tuple[int, int, int, int]


def screen_relative_rect(selection: Rect, screen: Rect) -> Rect | None:
    """选出 `selection` 落在某块屏幕内的部分，坐标相对该屏幕左上角。

    逻辑坐标下多屏可能是负坐标，因此用交集而不是简单相减。
    """
    sel_left, sel_top, sel_width, sel_height = selection
    sel_right = sel_left + sel_width
    sel_bottom = sel_top + sel_height

    scr_left, scr_top, scr_width, scr_height = screen
    scr_right = scr_left + scr_width
    scr_bottom = scr_top + scr_height

    left = max(sel_left, scr_left)
    top = max(sel_top, scr_top)
    right = min(sel_right, scr_right)
    bottom = min(sel_bottom, scr_bottom)
    if right <= left or bottom <= top:
        return None
    return (left - scr_left, top - scr_top, right - left, bottom - top)


def crop_rect(selection: Rect, widget_size: tuple[int, int], image_size: tuple[int, int]) -> Rect:
    """把控件逻辑坐标下的选区，换算成图像上的设备像素矩形。"""
    widget_width, widget_height = widget_size
    image_width, image_height = image_size
    scale_x = image_width / max(1, widget_width)
    scale_y = image_height / max(1, widget_height)
    left, top, width, height = selection
    return (
        round(left * scale_x),
        round(top * scale_y),
        round(width * scale_x),
        round(height * scale_y),
    )


def to_tuple(rect) -> Rect:
    return (rect.x(), rect.y(), rect.width(), rect.height())


def to_size(size) -> tuple[int, int]:
    return (size.width(), size.height())


def desktop_geometry():
    """所有屏幕的并集（逻辑坐标）。"""
    screens = QGuiApplication.screens()
    geometry = screens[0].geometry()
    for screen in screens[1:]:
        geometry = geometry.united(screen.geometry())
    return geometry


def grab_desktop() -> QPixmap:
    """抓取整个虚拟桌面；多屏时按主屏比例拼成一张设备像素图。"""
    screens = QGuiApplication.screens()
    if not screens:
        return QPixmap()

    desktop = desktop_geometry()
    scale = (QGuiApplication.primaryScreen() or screens[0]).devicePixelRatio()

    composed = QPixmap(
        round(desktop.width() * scale), round(desktop.height() * scale)
    )
    composed.fill(Qt.GlobalColor.black)
    painter = QPainter(composed)
    for screen in screens:
        placement = screen_relative_rect(
            to_tuple(screen.geometry()), to_tuple(desktop)
        )
        if placement is None:
            continue
        shot = screen.grabWindow(0)
        if shot.isNull():
            continue
        left, top, width, height = placement
        painter.drawPixmap(
            round(left * scale),
            round(top * scale),
            round(width * scale),
            round(height * scale),
            shot,
        )
    painter.end()
    return composed
