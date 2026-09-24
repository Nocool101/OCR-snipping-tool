import sys
import winreg
from pathlib import Path

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "screenshot-ocr"


def _launch_command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    repo_root = Path(__file__).resolve().parent.parent
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    launcher = repo_root / "launcher.pyw"
    return f'"{pythonw}" "{launcher}"'


def apply(enabled: bool) -> bool:
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            if enabled:
                winreg.SetValueEx(
                    key, VALUE_NAME, 0, winreg.REG_SZ, _launch_command()
                )
            else:
                try:
                    winreg.DeleteValue(key, VALUE_NAME)
                except FileNotFoundError:
                    pass
        return True
    except OSError:
        return False
