from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QGuiApplication, QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .controller import AppController
from .qt_support import describe, keep_alive


class _RecognitionWorker(QThread):
    chunk = Signal(str)
    failed = Signal(str)
    completed = Signal()

    def __init__(self, controller: AppController, image: bytes):
        super().__init__()
        self._controller = controller
        self._image = image

    def run(self) -> None:
        try:
            for piece in self._controller.recognize(self._image):
                self.chunk.emit(piece)
        except BaseException as exc:
            self.failed.emit(describe(exc))
        else:
            self.completed.emit()


class ResultWindow(QWidget):
    """**结果窗口**：上半区是识别出的**文本**，底部是复制按钮。"""

    closed = Signal(object)

    def __init__(self, controller: AppController):
        super().__init__()
        self._controller = controller
        self._worker: _RecognitionWorker | None = None
        self._streaming = False

        self.setWindowTitle("识别结果")
        self.resize(560, 340)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self._editor = QPlainTextEdit()
        self._editor.setPlaceholderText("识别出的文字会出现在这里")
        self._editor.setReadOnly(True)
        self._editor.textChanged.connect(self._on_edited)

        self._status = QLabel("")
        self._copy = QPushButton("复制")
        self._copy.clicked.connect(self._copy_to_clipboard)

        actions = QHBoxLayout()
        actions.addWidget(self._copy)
        actions.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addWidget(self._editor, stretch=1)
        layout.addWidget(self._status)
        layout.addLayout(actions)

    def start_recognition(self, image: bytes) -> None:
        self._status.setText("识别中…")
        self._streaming = True
        self._editor.setReadOnly(True)
        self._copy.setEnabled(False)

        worker = _RecognitionWorker(self._controller, image)
        keep_alive(worker)
        worker.chunk.connect(self._append)
        worker.failed.connect(self._show_failure)
        worker.completed.connect(self._finish)
        self._worker = worker
        worker.start()

    def _append(self, piece: str) -> None:
        self._editor.moveCursor(QTextCursor.MoveOperation.End)
        self._editor.insertPlainText(piece)

    def _finish(self) -> None:
        self._streaming = False
        self._status.setText("识别完成")
        self._editor.setReadOnly(False)
        self._copy.setEnabled(True)
        self._controller.set_text(self._editor.toPlainText())

    def _show_failure(self, message: str) -> None:
        self._streaming = False
        self._status.setText(f"识别失败：{message}")
        self._editor.setReadOnly(False)
        self._copy.setEnabled(True)
        self._controller.set_text(self._editor.toPlainText())

    def _on_edited(self) -> None:
        if self._streaming:
            return
        self._controller.set_text(self._editor.toPlainText())

    def _copy_to_clipboard(self) -> None:
        QGuiApplication.clipboard().setText(self._editor.toPlainText())
        self._status.setText("已复制到剪贴板")

    def closeEvent(self, event) -> None:
        self.closed.emit(self)
        super().closeEvent(event)
