"""单实例：用 Windows 命名互斥量保证同一时间只有一个副本在跑。

双击 exe 第二次启动时，若不加约束会多出一个托盘图标并抢占全局**热键**失败。
命名互斥量随进程退出自动释放，不留残留锁文件。
"""

import ctypes

ERROR_ALREADY_EXISTS = 183
MUTEX_NAME = r"Local\screenshot-ocr"

_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_kernel32.CreateMutexW.argtypes = (ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p)
_kernel32.CreateMutexW.restype = ctypes.c_void_p
_kernel32.CloseHandle.argtypes = (ctypes.c_void_p,)
_kernel32.CloseHandle.restype = ctypes.c_int


class SingleInstance:
    """持有命名互斥量；先到者拿到，后来者被拒。"""

    def __init__(self, name: str = MUTEX_NAME):
        self._name = name
        self._handle = None

    @property
    def is_held(self) -> bool:
        return self._handle is not None

    def acquire(self) -> bool:
        if self._handle is not None:
            return True
        ctypes.set_last_error(0)
        handle = _kernel32.CreateMutexW(None, 0, self._name)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
            _kernel32.CloseHandle(handle)
            return False
        self._handle = handle
        return True

    def release(self) -> None:
        if self._handle is None:
            return
        _kernel32.CloseHandle(self._handle)
        self._handle = None
