from typing import Iterator

from .model_client import ModelClient
from .prompt_builder import RECOGNIZE_INSTRUCTION


class AppController:
    """行为中枢：把**截图**交给**模型**识别成**文本**。不依赖 Qt。"""

    def __init__(self, client: ModelClient):
        self._client = client
        self._text = ""

    @property
    def text(self) -> str:
        """当前**文本**——识别结果，或用户编辑后的内容。"""
        return self._text

    def set_text(self, text: str) -> None:
        """记录用户编辑后的文本。"""
        self._text = text

    def recognize(self, image: bytes) -> Iterator[str]:
        """识别一张**截图**，逐块产出文本；结束后把完整结果记为当前文本。"""
        buffer: list[str] = []
        for chunk in self._client.stream(RECOGNIZE_INSTRUCTION, image=image):
            buffer.append(chunk)
            yield chunk
        self._text = "".join(buffer)
