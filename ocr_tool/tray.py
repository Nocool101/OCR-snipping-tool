from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QDialog, QMenu, QSystemTrayIcon

from . import autostart
from .settings import SettingsStore
from .settings_window import SettingsWindow


def _make_icon() -> QIcon:
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(Qt.GlobalColor.darkCyan)
    painter.drawRoundedRect(4, 4, 56, 56, 14, 14)
    font = painter.font()
    font.setPointSize(26)
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(Qt.GlobalColor.white)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "文")
    painter.end()
    return QIcon(pixmap)


class TrayApp:
    def __init__(self, app, store: SettingsStore):
        self._app = app
        self._store = store
        self._icon = QSystemTrayIcon(_make_icon(), app)
        self._icon.setToolTip("截图识别")

        menu = QMenu()
        settings_action = menu.addAction("设置")
        settings_action.triggered.connect(self._open_settings)
        menu.addSeparator()
        quit_action = menu.addAction("退出")
        quit_action.triggered.connect(app.quit)

        self._menu = menu
        self._icon.setContextMenu(menu)

    def show(self) -> None:
        self._icon.show()

    def _open_settings(self) -> None:
        window = SettingsWindow(self._store.load())
        if window.exec() == QDialog.DialogCode.Accepted:
            settings = window.settings()
            self._store.save(settings)
            autostart.apply(settings.autostart)
