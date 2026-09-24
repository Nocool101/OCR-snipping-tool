import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from . import secret_store

DEFAULT_FONT_SIZE = 14
MIN_FONT_SIZE = 8
MAX_FONT_SIZE = 40

# 落盘时 API Key 不用明文字段 `api_key`，而是加密后的 `api_key_enc`。
_ENCRYPTED_KEY_FIELD = "api_key_enc"


@dataclass(frozen=True)
class Settings:
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = ""
    hotkey: str = "Ctrl+Alt+O"
    autostart: bool = False
    font_size: int = DEFAULT_FONT_SIZE


def clamp_font_size(value) -> int:
    """把配置里的文字大小收敛到可用范围；坏值回落到默认。"""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return DEFAULT_FONT_SIZE
    return min(MAX_FONT_SIZE, max(MIN_FONT_SIZE, round(value)))


class SettingsStore:
    def __init__(self, path):
        self.path = Path(path)

    def load(self) -> Settings:
        try:
            raw = self.path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except (OSError, ValueError):
            return Settings()
        if not isinstance(data, dict):
            return Settings()
        known = {field.name for field in fields(Settings)}
        values = {key: value for key, value in data.items() if key in known}
        if "font_size" in values:
            values["font_size"] = clamp_font_size(values["font_size"])
        encrypted = data.get(_ENCRYPTED_KEY_FIELD)
        if isinstance(encrypted, str) and encrypted:
            # 密文优先于可能残留的旧明文；解不开（换机器/换账户）时当作未配置，让程序照常启动。
            values["api_key"] = _decrypt(encrypted)
        settings = Settings(**values)
        if not encrypted and settings.api_key:
            self._migrate_plaintext(settings)
        return settings

    def save(self, settings: Settings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = asdict(settings)
        api_key = data.pop("api_key")
        if api_key:
            if secret_store.available():
                data[_ENCRYPTED_KEY_FIELD] = secret_store.protect(api_key)
            else:
                # 非 Windows 没有 DPAPI，退回明文，好让开发与测试仍能跑。
                data["api_key"] = api_key
        self.path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _migrate_plaintext(self, settings: Settings) -> None:
        """旧版把 Key 存成明文；读到明文的这一次顺手加密回写。

        迁移后文件里不再有明文，所以只会发生一次。文件不可写时静默跳过，不影响本次读取。
        """
        if not secret_store.available():
            return
        try:
            self.save(settings)
        except (OSError, secret_store.SecretStoreError):
            pass


def _decrypt(token: str) -> str:
    try:
        return secret_store.unprotect(token)
    except secret_store.SecretStoreError:
        return ""
