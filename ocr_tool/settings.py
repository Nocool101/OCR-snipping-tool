import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path


DEFAULT_FONT_SIZE = 14
MIN_FONT_SIZE = 8
MAX_FONT_SIZE = 40


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
        return Settings(**values)

    def save(self, settings: Settings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(asdict(settings), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
