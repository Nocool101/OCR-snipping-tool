from PySide6.QtCore import QBuffer, QIODevice, Qt, QTimer
from PySide6.QtGui import QGuiApplication, QIcon, QImage, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QDialog, QMenu, QSystemTrayIcon

from . import autostart
from .capture import grab_desktop
from .controller import AppController
from .hotkey_manager import HotkeyManager
from .model_client import OpenAICompatClient
from .overlay import CaptureOverlay
from .qt_support import describe
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
        self._overlay: CaptureOverlay | None = None
        self._capture_pending = False
        self._hidden: list = []
        self._icon = QSystemTrayIcon(_make_icon(), app)
        self._icon.setToolTip("截图识别")

        self._hotkeys = HotkeyManager(app)
        self._hotkeys.pressed.connect(self.start_capture)

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
        if self._apply_hotkey():
            self._icon.showMessage(
                "截图识别",
                "已在后台运行。按热键即可截图；右键托盘图标可打开设置。",
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
            self._apply_hotkey()

    def _apply_hotkey(self) -> bool:
        hotkey = self._store.load().hotkey
        if self._hotkeys.register(hotkey):
            self._icon.setToolTip(f"截图识别（{hotkey}）")
            return True
        self._icon.setToolTip(f"截图识别：热键 {hotkey} 注册失败，请打开设置改键")
        self._warn(
            f"热键 {hotkey} 注册失败，可能已被别的软件占用。请在设置里换一个。"
        )
        return False

    def start_capture(self) -> None:
        if self._overlay is not None or self._capture_pending:
            return
        self._capture_pending = True
        self._hidden = []
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, (ResultWindow, SettingsWindow)) and widget.isVisible():
                widget.hide()
                self._hidden.append(widget)
        QTimer.singleShot(150, self._grab_and_show)

    def _grab_and_show(self) -> None:
        try:
            background = grab_desktop()
        except Exception as exc:
            background = None
            self._warn(f"截屏失败：{describe(exc)}")
        finally:
            self._restore_hidden()
            self._capture_pending = False
        if background is None or background.isNull():
            return

        overlay = CaptureOverlay(background)
        self._overlay = overlay
        overlay.captured.connect(self._recognize_capture)
        overlay.finished.connect(self._capture_finished)
        overlay.start()

    def _restore_hidden(self) -> None:
        for widget in self._hidden:
            widget.show()
        self._hidden = []

    def _capture_finished(self) -> None:
        self._overlay = None

    def _recognize_capture(self, image: QImage) -> None:
        if image.isNull():
            self._warn("没有截到内容，请再试一次。")
            return
        self._start_recognition(_to_png(image))

    def recognize_clipboard(self) -> None:
        image = QGuiApplication.clipboard().image()
        if image.isNull():
            self._warn("剪贴板里没有图片。先用 Win+Shift+S 截一张，再来点这里。")
            return
        self._start_recognition(_to_png(image))

    def _warn(self, message: str) -> None:
        self._icon.showMessage(
            "截图识别", message, QSystemTrayIcon.MessageIcon.Warning, 6000
        )

    def _start_recognition(self, png: bytes) -> None:
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
        window.start_recognition(png)

    def _forget(self, window: ResultWindow) -> None:
        self._windows = [w for w in self._windows if w is not window]
