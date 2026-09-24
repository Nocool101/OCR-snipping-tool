from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from . import capture

MIN_SIDE = 8


class CaptureOverlay(QWidget):
    """截图模式：覆盖整个虚拟桌面的遮罩，拖框选出**截图**区域。

    遮罩画的是按下热键那一刻抓到的**冻结画面**，因此框选时画面不会动，
    本工具自己的窗口也不可能被截进去。
    """

    captured = Signal(object)
    cancelled = Signal()
    finished = Signal()

    def __init__(self, background: QPixmap):
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool,
        )
        self._background = background
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setGeometry(capture.desktop_geometry())
        self.setMouseTracking(True)
        self._origin = None
        self._selection = QRect()

    def start(self) -> None:
        self._origin = None
        self._selection = QRect()
        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self._background)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 110))
        if self._selection.isNull():
            return
        painter.setClipRect(self._selection)
        painter.drawPixmap(self.rect(), self._background)
        painter.setClipping(False)
        painter.setPen(QPen(QColor(0, 200, 255), 2))
        painter.drawRect(self._selection)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._origin = event.position().toPoint()
            self._selection = QRect()
            self.update()

    def mouseMoveEvent(self, event) -> None:
        if self._origin is None:
            return
        self._selection = QRect(self._origin, event.position().toPoint()).normalized()
        self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton or self._origin is None:
            return
        selection = QRect(self._origin, event.position().toPoint()).normalized()
        self._origin = None
        if selection.width() < MIN_SIDE or selection.height() < MIN_SIDE:
            self._selection = QRect()
            self.update()
            return
        self.captured.emit(self._crop(selection))
        self.close()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.cancelled.emit()
            self.close()

    def closeEvent(self, event) -> None:
        self.finished.emit()
        super().closeEvent(event)

    def _crop(self, selection: QRect):
        rect = capture.crop_rect(
            capture.to_tuple(selection),
            capture.to_size(self.size()),
            capture.to_size(self._background.size()),
        )
        return self._background.copy(*rect).toImage()
