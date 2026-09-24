import itertools

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from .hotkey import combination_from, is_valid, normalize
from .model_client import OpenAICompatClient
from .qt_support import describe, keep_alive
from .settings import Settings

TEST_PROMPT = "连接测试：请只回复两个字「正常」。"


def _valid_hotkey(text: str) -> str:
    """配置被手工改坏时回落到默认热键。"""
    return normalize(text) if is_valid(text) else Settings().hotkey


class HotkeyEdit(QLineEdit):
    """**热键**输入框：点进来，直接按组合键即可记录。"""

    def __init__(self, value: str, parent=None):
        super().__init__(value, parent)
        self.setReadOnly(True)
        self.setPlaceholderText("点这里，然后按组合键（如 Ctrl+Alt+O）")

    def keyPressEvent(self, event) -> None:
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.clearFocus()
            return
        if key in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
            self.clear()
            return
        combination = combination_from(event.modifiers(), key)
        if combination is not None:
            self.setText(combination)


class _ConnectionTest(QThread):
    succeeded = Signal(str)
    failed = Signal(str)

    def __init__(self, client: OpenAICompatClient):
        super().__init__()
        self._client = client

    def run(self) -> None:
        try:
            stream = self._client.stream(TEST_PROMPT)
            try:
                text = "".join(itertools.islice(stream, 40)).strip()
            finally:
                stream.close()
        except BaseException as exc:
            self.failed.emit(describe(exc))
            return
        if not text:
            self.failed.emit("模型返回了空内容，请检查接口地址与模型名")
            return
        self.succeeded.emit(text)


class SettingsWindow(QDialog):
    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(460)
        self._thread: _ConnectionTest | None = None

        self._base_url = QLineEdit(settings.base_url)
        self._api_key = QLineEdit(settings.api_key)
        self._api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._model = QLineEdit(settings.model)
        self._hotkey = HotkeyEdit(settings.hotkey)
        self._autostart = QCheckBox("开机自启")
        self._autostart.setChecked(settings.autostart)

        form = QFormLayout()
        form.addRow("接口地址", self._base_url)
        form.addRow("API Key", self._api_key)
        form.addRow("模型名", self._model)
        form.addRow("热键", self._hotkey)
        form.addRow("", self._autostart)

        self._test_button = QPushButton("测试连接")
        self._test_button.clicked.connect(self._test_connection)
        self._status = QLabel("")
        self._status.setWordWrap(True)

        test_row = QHBoxLayout()
        test_row.addWidget(self._test_button)
        test_row.addWidget(self._status, stretch=1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("保存")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(test_row)
        layout.addWidget(buttons)

    def settings(self) -> Settings:
        return Settings(
            base_url=self._base_url.text().strip(),
            api_key=self._api_key.text().strip(),
            model=self._model.text().strip(),
            hotkey=_valid_hotkey(self._hotkey.text()),
            autostart=self._autostart.isChecked(),
        )

    def _test_connection(self) -> None:
        client = OpenAICompatClient(
            base_url=self._base_url.text().strip(),
            api_key=self._api_key.text().strip(),
            model=self._model.text().strip(),
            timeout=20.0,
        )
        self._status.setText("测试中…")
        self._test_button.setEnabled(False)

        worker = _ConnectionTest(client)
        keep_alive(worker)
        worker.succeeded.connect(self._show_success)
        worker.failed.connect(self._show_failure)
        worker.finished.connect(self._on_test_finished)
        self._thread = worker
        worker.start()

    def _on_test_finished(self) -> None:
        self._test_button.setEnabled(True)

    def _show_success(self, message: str) -> None:
        self._set_status("连接成功", message)

    def _show_failure(self, message: str) -> None:
        self._set_status("连接失败", message)

    def _set_status(self, prefix: str, message: str = "") -> None:
        self._status.setText(f"{prefix}：{message}" if message else prefix)
