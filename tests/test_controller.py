from ocr_tool.controller import AppController
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
