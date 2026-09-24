from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
)

from .settings import Settings


class SettingsWindow(QDialog):
    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(420)

        self._base_url = QLineEdit(settings.base_url)
        self._api_key = QLineEdit(settings.api_key)
        self._api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._model = QLineEdit(settings.model)
        self._hotkey = QLineEdit(settings.hotkey)
        self._autostart = QCheckBox("开机自启")
        self._autostart.setChecked(settings.autostart)

        form = QFormLayout()
        form.addRow("接口地址", self._base_url)
        form.addRow("API Key", self._api_key)
        form.addRow("模型名", self._model)
        form.addRow("热键", self._hotkey)
        form.addRow("", self._autostart)

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
        layout.addWidget(buttons)

    def settings(self) -> Settings:
        return Settings(
            base_url=self._base_url.text().strip(),
            api_key=self._api_key.text().strip(),
            model=self._model.text().strip(),
            hotkey=self._hotkey.text().strip() or Settings().hotkey,
            autostart=self._autostart.isChecked(),
        )
