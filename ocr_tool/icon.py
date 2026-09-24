"""应用图标：托盘、窗口与 exe 共用同一份图标。

优先读取随包分发的 `assets/app.ico`（打包时生成，见 `packaging/make_icon.py`），
读不到时按同一份设计现画一个，保证源码运行也不缺图标。
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap

from .resources import resource_path

ICON_ASSET = "assets/app.ico"
_DESIGN_SIZE = 64


def icon_pixmap(size: int = _DESIGN_SIZE) -> QPixmap:
    """画图标：深青圆角方块，中间一个白色的「文」。"""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(Qt.GlobalColor.darkCyan)
    margin = round(size * 4 / _DESIGN_SIZE)
    corner = round(size * 14 / _DESIGN_SIZE)
    painter.drawRoundedRect(
        margin, margin, size - 2 * margin, size - 2 * margin, corner, corner
    )
    font = painter.font()
    font.setPixelSize(round(size * 36 / _DESIGN_SIZE))
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(Qt.GlobalColor.white)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "文")
    painter.end()
    return pixmap


def app_icon() -> QIcon:
    asset = resource_path(ICON_ASSET)
    if asset.exists():
        icon = QIcon(str(asset))
        if not icon.isNull():
            return icon
    return QIcon(icon_pixmap())
