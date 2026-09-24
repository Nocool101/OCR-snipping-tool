import os
from pathlib import Path

APP_DIR_NAME = "screenshot-ocr"


def default_settings_path() -> Path:
    appdata = os.environ.get("APPDATA")
    base = Path(appdata) if appdata else Path.home() / ".config"
    return base / APP_DIR_NAME / "settings.json"
