"""定位随程序分发的数据文件。

源码运行时以仓库根为基准；PyInstaller 打包后以解包目录（`_MEIPASS`）为基准。
"""

import sys
from pathlib import Path


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        unpacked = getattr(sys, "_MEIPASS", None)
        if unpacked:
            return Path(unpacked)
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def resource_path(relative: str) -> Path:
    """把相对路径（如 `assets/app.ico`）变成可读取的绝对路径。"""
    return _base_dir() / relative
