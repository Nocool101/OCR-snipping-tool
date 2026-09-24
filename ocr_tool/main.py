import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from .icon import app_icon
from .paths import default_settings_path
from .settings import SettingsStore
from .single_instance import SingleInstance
from .tray import TrayApp


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("screenshot-ocr")
    app.setWindowIcon(app_icon())
    app.setQuitOnLastWindowClosed(False)

    instance = SingleInstance()
    if not instance.acquire():
        QMessageBox.information(
            None, "截图识别", "程序已经在运行，请查看系统托盘图标。"
        )
        return 0
    app.aboutToQuit.connect(instance.release)

    store = SettingsStore(default_settings_path())
    tray = TrayApp(app, store)
    tray.show()

    if not store.path.exists():
        tray.open_settings()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
