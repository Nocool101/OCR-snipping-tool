import pytest

from ocr_tool.controller import Action, AppController
from ocr_tool.model_client import (
    MissingApiKey,
    ModelAuthError,
    ModelNetworkError,
)
from ocr_tool.prompt_builder import RECOGNIZE_INSTRUCTION


class FakeModelClient:
    def __init__(self, chunks):
        self._chunks = chunks
        self.instructions = []
        self.images = []

    def stream(self, instruction, image=None):
        self.instructions.append(instruction)
        self.images.append(image)
        yield from self._chunks


def test_recognize_streams_chunks_and_joins_them_into_text():
    client = FakeModelClient(["你", "好"])
    controller = AppController(client)

    chunks = list(controller.recognize(b"png-bytes"))

    assert chunks == ["你", "好"]
    assert controller.text == "你好"


def test_recognize_sends_the_image_with_the_recognition_instruction():
    client = FakeModelClient(["x"])
    controller = AppController(client)

    list(controller.recognize(b"png-bytes"))

    assert client.images == [b"png-bytes"]
    assert client.instructions == [RECOGNIZE_INSTRUCTION]


def test_edited_text_replaces_the_recognized_text():
    controller = AppController(FakeModelClient(["你好"]))
    list(controller.recognize(b"png-bytes"))

    controller.set_text("你好，世界！")

    assert controller.text == "你好，世界！"


def test_perform_processes_the_given_text():
    client = FakeModelClient(["译", "文"])
    controller = AppController(client)

    chunks = list(controller.perform(Action.TRANSLATE, "编辑后的文本"))

    assert chunks == ["译", "文"]
    instruction = client.instructions[-1]
    assert "编辑后的文本" in instruction
    assert "翻译" in instruction


def test_perform_can_run_repeatedly_with_different_actions():
    client = FakeModelClient(["答"])
    controller = AppController(client)

    list(controller.perform(Action.SUMMARIZE, "一段文字"))
    list(controller.perform(Action.CONVERT_TABLE, "一段文字"))

    assert "概括" in client.instructions[-2]
    assert "表格" in client.instructions[-1]


def test_perform_ask_carries_the_question_and_the_text():
    client = FakeModelClient(["答"])
    controller = AppController(client)

    chunks = list(controller.perform(Action.ASK, "被处理的文本", "这段代码有问题吗？"))

    assert chunks == ["答"]
    instruction = client.instructions[-1]
    assert "这段代码有问题吗？" in instruction
    assert "被处理的文本" in instruction


def test_ask_is_an_action_but_not_a_button():
    from ocr_tool.controller import ACTION_ORDER

    assert Action.ASK.value == "自定义提问"
    assert Action.ASK not in ACTION_ORDER


def test_ask_without_a_question_is_rejected():
    controller = AppController(FakeModelClient(["答"]))

    with pytest.raises(ValueError):
        list(controller.perform(Action.ASK, "被处理的文本"))


class FailingModelClient:
    def __init__(self, error):
        self._error = error

    def stream(self, instruction, image=None):
        raise self._error
        yield


@pytest.mark.parametrize(
    "error",
    [
        MissingApiKey("尚未配置 API Key"),
        ModelNetworkError("网络错误：连接被重置"),
        ModelAuthError("鉴权失败（HTTP 401）：Invalid API key"),
    ],
    ids=["missing-key", "network", "model-error"],
)
def test_failures_pass_through_the_controller_unchanged(error):
    controller = AppController(FailingModelClient(error))

    with pytest.raises(type(error)) as raised:
        list(controller.recognize(b"png-bytes"))

    assert str(raised.value) == str(error), "分类与原因都应原样传上去"


def test_a_failed_recognition_leaves_the_previous_text_alone():
    controller = AppController(FakeModelClient(["旧"]))
    list(controller.recognize(b"png-bytes"))
    controller = AppController(FailingModelClient(ModelNetworkError("网络错误")))

    with pytest.raises(ModelNetworkError):
        list(controller.recognize(b"png-bytes"))

    assert controller.text == ""
