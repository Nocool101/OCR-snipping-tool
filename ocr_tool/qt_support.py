"""Qt 的公共支撑。"""

from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtGui import QFont, QImage

_RUNNING_WORKERS: set = set()


def to_png(image: QImage) -> bytes:
    """把 QImage 编码成 PNG 字节。"""
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    return bytes(buffer.data())


def set_point_size(widget, size: int) -> None:
    """把控件文字的字号设成 `size` 磅（保留其字体族）。"""
    font = QFont(widget.font())
    font.setPointSize(size)
    widget.setFont(font)


def describe(exc: BaseException) -> str:
    """把异常变成能给用户看的一句话。"""
    return str(exc).strip() or type(exc).__name__


def keep_alive(worker) -> None:
    """在后台线程结束前持有它的引用，避免对象被回收导致进程崩溃。"""
    _RUNNING_WORKERS.add(worker)
    worker.finished.connect(lambda: _RUNNING_WORKERS.discard(worker))
