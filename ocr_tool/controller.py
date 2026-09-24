from enum import Enum
from typing import Iterator

from . import prompt_builder
from .model_client import ModelClient
from .prompt_builder import RECOGNIZE_INSTRUCTION


class Action(Enum):
    """对**文本**的一种加工。枚举值即按钮上的名字。"""

    TRANSLATE = "翻译成中文"
    SUMMARIZE = "总结"
    CONVERT_TABLE = "表格转换"


ACTION_ORDER = (Action.TRANSLATE, Action.SUMMARIZE, Action.CONVERT_TABLE)

_ACTION_INSTRUCTIONS = {
    Action.TRANSLATE: prompt_builder.translate_instruction,
    Action.SUMMARIZE: prompt_builder.summarize_instruction,
    Action.CONVERT_TABLE: prompt_builder.convert_table_instruction,
}


class AppController:
    """行为中枢：把**截图**识别成**文本**，并对**文本**执行**动作**。不依赖 Qt。"""

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

    def perform(self, action: Action, text: str) -> Iterator[str]:
        """对**文本**执行一个**动作**，逐块产出答案。"""
        instruction = _ACTION_INSTRUCTIONS[action](text)
        yield from self._client.stream(instruction)
