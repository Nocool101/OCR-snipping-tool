from functools import partial

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QGuiApplication, QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from .controller import ACTION_ORDER, Action, AppController
from .qt_support import describe, keep_alive


class _StreamWorker(QThread):
    chunk = Signal(str)
    failed = Signal(str)
    completed = Signal()

    def __init__(self, start):
        super().__init__()
        self._start = start

    def run(self) -> None:
        try:
            for piece in self._start():
                self.chunk.emit(piece)
        except BaseException as exc:
            self.failed.emit(describe(exc))
        else:
            self.completed.emit()


class ResultWindow(QWidget):
    """**结果窗口**：上半区是识别出的**文本**，下半区是**动作**的答案。"""

    closed = Signal(object)

    def __init__(self, controller: AppController):
        super().__init__()
        self._controller = controller
        self._worker: _StreamWorker | None = None
        self._filling_text = False
        self._answer_markdown = ""
        self._activity = ""

        self.setWindowTitle("识别结果")
        self.resize(640, 520)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self._editor = QPlainTextEdit()
        self._editor.setPlaceholderText("识别出的文字会出现在这里")
        self._editor.setReadOnly(True)
        self._editor.textChanged.connect(self._on_edited)

        self._answer = QTextBrowser()
        self._answer.setPlaceholderText("翻译、总结、表格转换的答案会出现在这里")
        self._answer.setOpenExternalLinks(True)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self._editor)
        splitter.addWidget(self._answer)

        self._status = QLabel("")
        self._copy = QPushButton("复制")
        self._copy.clicked.connect(self._copy_to_clipboard)

        self._action_buttons: list[QPushButton] = []
        actions = QHBoxLayout()
        actions.addWidget(self._copy)
        for action in ACTION_ORDER:
            button = QPushButton(action.value)
            button.clicked.connect(partial(self._run_action, action))
            self._action_buttons.append(button)
            actions.addWidget(button)
        actions.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addWidget(splitter, stretch=1)
        layout.addWidget(self._status)
        layout.addLayout(actions)

    def start_recognition(self, image: bytes) -> None:
        if self.is_busy():
            return
        self._filling_text = True
        self._editor.clear()
        self._answer.clear()
        self._answer_markdown = ""
        self._editor.setReadOnly(True)
        self._activity = "识别"
        self._begin()
        self._start_worker(
            lambda: self._controller.recognize(image),
            self._append_text,
            self._finish_recognition,
        )

    def _run_action(self, action: Action) -> None:
        if self.is_busy():
            return
        text = self._editor.toPlainText()
        if not text.strip():
            self._status.setText("还没有可处理的文字")
            return
        self._answer.clear()
        self._answer_markdown = ""
        self._activity = action.value
        self._begin()
        self._start_worker(
            lambda: self._controller.perform(action, text),
            self._append_answer,
            self._finish_action,
        )

    def is_busy(self) -> bool:
        return self._worker is not None and self._worker.isRunning()

    def _start_worker(self, start, on_chunk, on_completed) -> None:
        worker = _StreamWorker(start)
        keep_alive(worker)
        worker.chunk.connect(on_chunk)
        worker.failed.connect(self._fail)
        worker.completed.connect(on_completed)
        self._worker = worker
        worker.start()

    def _begin(self) -> None:
        self._status.setText(f"{self._activity}中…")
        self._set_busy(True)

    def _end(self) -> None:
        self._status.setText(f"{self._activity}完成")
        self._set_busy(False)

    def _set_busy(self, busy: bool) -> None:
        for button in self._action_buttons:
            button.setEnabled(not busy)
        self._copy.setEnabled(not busy)

    @staticmethod
    def _append_plain(widget, piece: str) -> None:
        cursor = widget.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(piece)
        widget.setTextCursor(cursor)
        scrollbar = widget.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _append_text(self, piece: str) -> None:
        self._append_plain(self._editor, piece)

    def _append_answer(self, piece: str) -> None:
        self._answer_markdown += piece
        self._append_plain(self._answer, piece)

    def _finish_recognition(self) -> None:
        self._filling_text = False
        self._editor.setReadOnly(False)
        self._end()
        self._controller.set_text(self._editor.toPlainText())

    def _finish_action(self) -> None:
        self._answer.setMarkdown(self._answer_markdown)
        self._end()

    def _fail(self, message: str) -> None:
        if self._filling_text:
            self._filling_text = False
            self._editor.setReadOnly(False)
            self._controller.set_text(self._editor.toPlainText())
        self._set_busy(False)
        self._status.setText(f"{self._activity}失败：{message}")

    def _on_edited(self) -> None:
        if self._filling_text:
            return
        self._controller.set_text(self._editor.toPlainText())

    def _copy_to_clipboard(self) -> None:
        QGuiApplication.clipboard().setText(self._editor.toPlainText())
        self._status.setText("已复制到剪贴板")

    def closeEvent(self, event) -> None:
        self.closed.emit(self)
        super().closeEvent(event)
