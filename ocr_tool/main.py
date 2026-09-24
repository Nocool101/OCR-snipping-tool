import sys

from PySide6.QtWidgets import QApplication

from .paths import default_settings_path
from .settings import SettingsStore
from .tray import TrayApp


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("screenshot-ocr")
    app.setQuitOnLastWindowClosed(False)

    store = SettingsStore(default_settings_path())
    tray = TrayApp(app, store)
    tray.show()

    if not store.path.exists():
        tray.open_settings()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
