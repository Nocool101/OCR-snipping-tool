"""全局**热键**：用 Windows 的 RegisterHotKey，事件在 Qt 事件循环里取回。"""

import ctypes
from ctypes import wintypes

from PySide6.QtCore import QAbstractNativeEventFilter, QObject, Signal

from .hotkey import win_parts

WM_HOTKEY = 0x0312
HOTKEY_ID = 0xA0C1


class _HotkeyFilter(QAbstractNativeEventFilter):
    def __init__(self, on_pressed, hotkey_id: int):
        super().__init__()
        self._on_pressed = on_pressed
        self._hotkey_id = hotkey_id

    def nativeEventFilter(self, event_type, message):
        if event_type == b"windows_generic_MSG":
            msg = ctypes.cast(int(message), ctypes.POINTER(_MSG)).contents
            if msg.message == WM_HOTKEY and msg.wParam == self._hotkey_id:
                self._on_pressed()
        return False, 0


class _MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt_x", wintypes.LONG),
        ("pt_y", wintypes.LONG),
    ]


class HotkeyManager(QObject):
    """注册一个全局热键；被别的软件占用时注册会失败。"""

    pressed = Signal()

    def __init__(self, app, hotkey_id: int = HOTKEY_ID, parent=None):
        super().__init__(parent)
        self._app = app
        self._hotkey_id = hotkey_id
        self._registered = False
        self._filter = _HotkeyFilter(self.pressed.emit, hotkey_id)
        app.installNativeEventFilter(self._filter)

    @property
    def is_registered(self) -> bool:
        return self._registered

    def register(self, hotkey: str) -> bool:
        self.unregister()
        try:
            modifiers, virtual_key = win_parts(hotkey)
        except ValueError:
            return False
        ctypes.windll.user32.RegisterHotKey.restype = wintypes.BOOL
        ok = bool(
            ctypes.windll.user32.RegisterHotKey(
                None, self._hotkey_id, modifiers, virtual_key
            )
        )
        self._registered = ok
        return ok

    def unregister(self) -> None:
        if self._registered:
            ctypes.windll.user32.UnregisterHotKey(None, self._hotkey_id)
            self._registered = False
