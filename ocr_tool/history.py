"""本次运行的**识别**记录。只在内存里，不落盘。"""

from dataclasses import dataclass
from datetime import datetime

DEFAULT_LIMIT = 20
PREVIEW_LENGTH = 24


@dataclass(frozen=True)
class Recognition:
    """一次**识别**的结果：**文本**与发生时刻。"""

    text: str
    at: datetime

    def label(self) -> str:
        """历史菜单里的一行：时间 + 文本开头。"""
        preview = " ".join(self.text.split())[:PREVIEW_LENGTH] or "（空）"
        return f"{self.at:%H:%M:%S}  {preview}"


class History:
    """最新的在前；超过上限丢最旧的。"""

    def __init__(self, limit: int = DEFAULT_LIMIT):
        self._limit = max(1, limit)
        self._entries: list[Recognition] = []

    def add(self, text: str, at: datetime | None = None) -> None:
        self._entries.insert(0, Recognition(text=text, at=at or datetime.now()))
        del self._entries[self._limit :]

    @property
    def entries(self) -> tuple[Recognition, ...]:
        return tuple(self._entries)
