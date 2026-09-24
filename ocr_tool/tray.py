from PySide6.QtCore import QBuffer, QIODevice, Qt
from PySide6.QtGui import QGuiApplication, QIcon, QImage, QPainter, QPixmap
from PySide6.QtWidgets import QDialog, QMenu, QSystemTrayIcon

from . import autostart
from .controller import AppController
from .model_client import OpenAICompatClient
from .result_window import ResultWindow
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


def _to_png(image: QImage) -> bytes:
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    return bytes(buffer.data())


class TrayApp:
    def __init__(self, app, store: SettingsStore):
        self._app = app
        self._store = store
        self._windows: list[ResultWindow] = []
        self._icon = QSystemTrayIcon(_make_icon(), app)
        self._icon.setToolTip("截图识别")

        menu = QMenu()
        recognize_action = menu.addAction("识别剪贴板图片")
        recognize_action.triggered.connect(self.recognize_clipboard)
        menu.addSeparator()
        settings_action = menu.addAction("设置")
        settings_action.triggered.connect(self.open_settings)
        menu.addSeparator()
        quit_action = menu.addAction("退出")
        quit_action.triggered.connect(app.quit)

        self._menu = menu
        self._icon.setContextMenu(menu)
        self._icon.activated.connect(self._on_activated)

    def show(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            raise RuntimeError("系统托盘不可用，程序无法常驻")
        self._icon.show()
        self._icon.showMessage(
            "截图识别",
            "已在后台运行。右键托盘图标可打开设置（图标可能收在 ^ 折叠区）。",
            QSystemTrayIcon.MessageIcon.Information,
            5000,
        )

    def _on_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.open_settings()

    def open_settings(self) -> None:
        window = SettingsWindow(self._store.load())
        if window.exec() == QDialog.DialogCode.Accepted:
            settings = window.settings()
            self._store.save(settings)
            autostart.apply(settings.autostart)

    def recognize_clipboard(self) -> None:
        image = QGuiApplication.clipboard().image()
        if image.isNull():
            self._icon.showMessage(
                "截图识别",
                "剪贴板里没有图片。先用 Win+Shift+S 截一张，再来点这里。",
                QSystemTrayIcon.MessageIcon.Warning,
                5000,
            )
            return

        settings = self._store.load()
        client = OpenAICompatClient(
            base_url=settings.base_url,
            api_key=settings.api_key,
            model=settings.model,
        )
        window = ResultWindow(AppController(client))
        self._windows.append(window)
        window.closed.connect(self._forget)
        window.show()
        window.start_recognition(_to_png(image))

    def _forget(self, window: ResultWindow) -> None:
        self._windows = [w for w in self._windows if w is not window]
