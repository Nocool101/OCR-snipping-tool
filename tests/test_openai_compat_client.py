import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from ocr_tool.model_client import (
    ModelAuthError,
    ModelNetworkError,
    ModelResponseError,
    ModelTimeout,
    MissingApiKey,
    OpenAICompatClient,
)


class _FakeModelServer(BaseHTTPRequestHandler):
    status = 200
    sse_lines = []
    delay = 0.0
    received = None

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        type(self).received = {
            "path": self.path,
            "authorization": self.headers.get("Authorization"),
            "user_agent": self.headers.get("User-Agent"),
            "session": self.headers.get("x-opencode-session"),
            "body": json.loads(raw.decode("utf-8")),
        }
        if type(self).delay:
            import time

            time.sleep(type(self).delay)
        self.send_response(type(self).status)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for line in type(self).sse_lines:
            self.wfile.write((line + "\n").encode("utf-8"))
        self.wfile.flush()

    def log_message(self, *args):
        pass


@pytest.fixture(autouse=True)
def _no_proxy(monkeypatch):
    monkeypatch.setenv("no_proxy", "127.0.0.1,localhost")
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")


@pytest.fixture
def fake_server():
    _FakeModelServer.status = 200
    _FakeModelServer.sse_lines = []
    _FakeModelServer.delay = 0.0
    _FakeModelServer.received = None

    server = HTTPServer(("127.0.0.1", 0), _FakeModelServer)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        thread.join()


@pytest.fixture
def base_url(fake_server):
    return f"http://127.0.0.1:{fake_server.server_port}/v1"


def test_streams_deltas_and_sends_expected_request(base_url):
    _FakeModelServer.sse_lines = [
        'data: {"choices":[{"delta":{"content":"你"}}]}',
        'data: {"choices":[{"delta":{"content":"好"}}]}',
        "data: [DONE]",
    ]
    client = OpenAICompatClient(
        base_url=base_url, api_key="sk-test", model="vision-model"
    )

    chunks = list(client.stream("提取文字"))

    assert chunks == ["你", "好"]
    sent = _FakeModelServer.received
    assert sent["path"] == "/v1/chat/completions"
    assert sent["authorization"] == "Bearer sk-test"
    assert sent["body"]["model"] == "vision-model"
    assert sent["body"]["stream"] is True
    assert sent["body"]["messages"][-1]["content"] == "提取文字"


def test_missing_api_key_raises_without_making_request(base_url):
    client = OpenAICompatClient(base_url=base_url, api_key="", model="vision-model")

    with pytest.raises(MissingApiKey):
        list(client.stream("提取文字"))

    assert _FakeModelServer.received is None


def test_http_401_is_reported_as_auth_failure(base_url):
    _FakeModelServer.status = 401
    _FakeModelServer.sse_lines = ['{"error":{"message":"Invalid API key"}}']
    client = OpenAICompatClient(base_url=base_url, api_key="sk-bad", model="m")

    with pytest.raises(ModelAuthError):
        list(client.stream("提取文字"))


def test_refused_connection_is_reported_as_network_failure():
    import socket

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    dead_port = sock.getsockname()[1]
    sock.close()

    client = OpenAICompatClient(
        base_url=f"http://127.0.0.1:{dead_port}/v1", api_key="sk", model="m"
    )

    with pytest.raises(ModelNetworkError):
        list(client.stream("提取文字"))


def test_slow_server_is_reported_as_timeout(base_url):
    _FakeModelServer.delay = 1.0
    client = OpenAICompatClient(
        base_url=base_url, api_key="sk", model="m", timeout=0.1
    )

    with pytest.raises(ModelTimeout):
        list(client.stream("提取文字"))


def test_sends_a_non_default_user_agent(base_url):
    _FakeModelServer.sse_lines = [
        'data: {"choices":[{"delta":{"content":"x"}}]}',
        "data: [DONE]",
    ]
    client = OpenAICompatClient(base_url=base_url, api_key="sk", model="m")

    list(client.stream("提取文字"))

    user_agent = _FakeModelServer.received["user_agent"]
    assert user_agent, "必须发送 User-Agent"
    assert "Python-urllib" not in user_agent, user_agent


def test_sends_a_stable_session_id(base_url):
    _FakeModelServer.sse_lines = [
        'data: {"choices":[{"delta":{"content":"x"}}]}',
        "data: [DONE]",
    ]
    client = OpenAICompatClient(base_url=base_url, api_key="sk", model="m")

    list(client.stream("提取文字"))
    first = _FakeModelServer.received["session"]

    list(client.stream("提取文字"))
    second = _FakeModelServer.received["session"]

    assert first, "必须发送 x-opencode-session"
    assert first == second, "同一次会话内 session 应稳定"
    other = OpenAICompatClient(base_url=base_url, api_key="sk", model="m")
    list(other.stream("提取文字"))
    assert _FakeModelServer.received["session"] != first, "不同会话应不同"


def test_accepts_an_explicit_session_id(base_url):
    _FakeModelServer.sse_lines = [
        'data: {"choices":[{"delta":{"content":"x"}}]}',
        "data: [DONE]",
    ]
    client = OpenAICompatClient(
        base_url=base_url, api_key="sk", model="m", session_id="my-session"
    )

    list(client.stream("提取文字"))

    assert _FakeModelServer.received["session"] == "my-session"


def test_sends_image_as_base64_data_url(base_url):
    _FakeModelServer.sse_lines = [
        'data: {"choices":[{"delta":{"content":"x"}}]}',
        "data: [DONE]",
    ]
    client = OpenAICompatClient(base_url=base_url, api_key="sk", model="m")

    list(client.stream("识别这张图", image=b"\x89PNG\r\n\x1a\nfake"))

    parts = _FakeModelServer.received["body"]["messages"][-1]["content"]
    assert parts[0] == {"type": "text", "text": "识别这张图"}
    assert parts[1]["type"] == "image_url"
    assert parts[1]["image_url"]["url"].startswith("data:image/png;base64,")


def test_jpeg_image_is_labelled_as_jpeg(base_url):
    _FakeModelServer.sse_lines = [
        'data: {"choices":[{"delta":{"content":"x"}}]}',
        "data: [DONE]",
    ]
    client = OpenAICompatClient(base_url=base_url, api_key="sk", model="m")

    list(client.stream("识别这张图", image=b"\xff\xd8\xff\xe0fake"))

    url = _FakeModelServer.received["body"]["messages"][-1]["content"][1][
        "image_url"
    ]["url"]
    assert url.startswith("data:image/jpeg;base64,")


def test_http_500_is_reported_as_model_error(base_url):
    _FakeModelServer.status = 500
    _FakeModelServer.sse_lines = ['{"error":{"message":"upstream exploded"}}']
    client = OpenAICompatClient(base_url=base_url, api_key="sk", model="m")

    with pytest.raises(ModelResponseError):
        list(client.stream("提取文字"))
