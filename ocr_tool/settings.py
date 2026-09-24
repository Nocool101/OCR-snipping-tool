import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = ""
    hotkey: str = "Ctrl+Alt+O"
    autostart: bool = False


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
        return Settings(**{key: value for key, value in data.items() if key in known})

    def save(self, settings: Settings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(asdict(settings), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
