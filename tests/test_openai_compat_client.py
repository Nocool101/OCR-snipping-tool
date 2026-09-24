import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from ocr_tool.model_client import (
    ModelAuthError,
    ModelNetworkError,
    ModelResponseError,
    ModelTimeout,
    ModelTruncated,
    MissingApiKey,
    OpenAICompatClient,
)


class _FakeModelServer(BaseHTTPRequestHandler):
    status = 200
    sse_lines = []
    delay = 0.0
    received = None
    requests = 0
    fail_first = False
    fail_always = False
    garbage = False
    first_lines = None
    stall_before_first_line = 0.0
    stall_every_request = False
    stall_after_first_line = 0.0

    def do_POST(self):
        type(self).requests += 1
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        type(self).received = {
            "path": self.path,
            "authorization": self.headers.get("Authorization"),
            "user_agent": self.headers.get("User-Agent"),
            "session": self.headers.get("x-opencode-session"),
            "body": json.loads(raw.decode("utf-8")),
        }
        if type(self).fail_always or (
            type(self).fail_first and type(self).requests == 1
        ):
            self.close_connection = True
            return
        if type(self).garbage:
            self.wfile.write(b"not-http-at-all\r\n\r\n")
            self.wfile.flush()
            self.close_connection = True
            return
        lines = type(self).sse_lines
        if type(self).first_lines is not None and type(self).requests == 1:
            lines = type(self).first_lines
        if type(self).delay:
            time.sleep(type(self).delay)
        self.send_response(type(self).status)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        try:
            if type(self).stall_before_first_line and (
                type(self).stall_every_request or type(self).requests == 1
            ):
                time.sleep(type(self).stall_before_first_line)
            for index, line in enumerate(lines):
                self.wfile.write((line + "\n").encode("utf-8"))
                self.wfile.flush()
                if index == 0 and type(self).stall_after_first_line:
                    time.sleep(type(self).stall_after_first_line)
        except (BrokenPipeError, ConnectionResetError):
            pass

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
    _FakeModelServer.requests = 0
    _FakeModelServer.fail_first = False
    _FakeModelServer.fail_always = False
    _FakeModelServer.garbage = False
    _FakeModelServer.first_lines = None
    _FakeModelServer.stall_before_first_line = 0.0
    _FakeModelServer.stall_every_request = False
    _FakeModelServer.stall_after_first_line = 0.0

    server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeModelServer)
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


def test_retries_a_transient_network_failure_before_any_output(base_url):
    _FakeModelServer.fail_first = True
    _FakeModelServer.sse_lines = [
        'data: {"choices":[{"delta":{"content":"好"}}]}',
        "data: [DONE]",
    ]
    client = OpenAICompatClient(
        base_url=base_url, api_key="sk", model="m", attempts=3, retry_delay=0.01
    )

    chunks = list(client.stream("提取文字"))

    assert chunks == ["好"]
    assert _FakeModelServer.requests == 2


def test_gives_up_after_the_configured_attempts(base_url):
    _FakeModelServer.fail_always = True
    client = OpenAICompatClient(
        base_url=base_url, api_key="sk", model="m", attempts=2, retry_delay=0.01
    )

    with pytest.raises(ModelNetworkError):
        list(client.stream("提取文字"))

    assert _FakeModelServer.requests == 2


def test_a_single_attempt_means_no_retry(base_url):
    _FakeModelServer.fail_always = True
    client = OpenAICompatClient(
        base_url=base_url, api_key="sk", model="m", attempts=1, retry_delay=0.01
    )

    with pytest.raises(ModelNetworkError):
        list(client.stream("提取文字"))

    assert _FakeModelServer.requests == 1


def test_a_non_http_response_is_classified_as_network_failure(base_url):
    _FakeModelServer.garbage = True
    client = OpenAICompatClient(
        base_url=base_url, api_key="sk", model="m", attempts=1
    )

    with pytest.raises(ModelNetworkError):
        list(client.stream("提取文字"))


def test_stream_without_done_marker_is_reported_as_truncated(base_url):
    _FakeModelServer.sse_lines = ['data: {"choices":[{"delta":{"content":"你"}}]}']
    client = OpenAICompatClient(
        base_url=base_url, api_key="sk", model="m", attempts=1
    )

    chunks = []
    with pytest.raises(ModelTruncated) as raised:
        for chunk in client.stream("提取文字"):
            chunks.append(chunk)

    assert chunks == ["你"], "截断前已产出的内容应仍然可见"
    assert "接口地址" in str(raised.value), "提示里应引导检查配置"


def test_truncation_before_any_output_is_retried(base_url):
    _FakeModelServer.first_lines = []
    _FakeModelServer.sse_lines = [
        'data: {"choices":[{"delta":{"content":"好"}}]}',
        "data: [DONE]",
    ]
    client = OpenAICompatClient(
        base_url=base_url, api_key="sk", model="m", attempts=3, retry_delay=0.01
    )

    assert list(client.stream("提取文字")) == ["好"]
    assert _FakeModelServer.requests == 2


def test_a_stalled_first_token_switches_to_a_fresh_attempt(base_url):
    _FakeModelServer.stall_before_first_line = 0.5
    _FakeModelServer.sse_lines = [
        'data: {"choices":[{"delta":{"content":"好"}}]}',
        "data: [DONE]",
    ]
    client = OpenAICompatClient(
        base_url=base_url,
        api_key="sk",
        model="m",
        timeout=30.0,
        first_token_timeout=0.1,
        attempts=3,
        retry_delay=0.01,
    )

    assert list(client.stream("提取文字")) == ["好"]
    assert _FakeModelServer.requests == 2, "首字卡住应换一次连接重试"


def test_a_stalled_first_token_retries_only_once(base_url):
    _FakeModelServer.stall_before_first_line = 0.5
    _FakeModelServer.stall_every_request = True
    client = OpenAICompatClient(
        base_url=base_url,
        api_key="sk",
        model="m",
        timeout=30.0,
        first_token_timeout=0.1,
        attempts=3,
        retry_delay=0.01,
    )

    with pytest.raises(ModelTimeout):
        list(client.stream("提取文字"))

    assert _FakeModelServer.requests == 2, "首字超时只换一次，不跟着 attempts 反复重试"


def test_a_stall_after_output_is_not_retried(base_url):
    _FakeModelServer.sse_lines = [
        'data: {"choices":[{"delta":{"content":"你"}}]}',
        "data: [DONE]",
    ]
    _FakeModelServer.stall_after_first_line = 0.6
    client = OpenAICompatClient(
        base_url=base_url,
        api_key="sk",
        model="m",
        timeout=0.3,
        first_token_timeout=5.0,
        attempts=3,
        retry_delay=0.01,
    )

    chunks = []
    with pytest.raises(ModelTimeout):
        for chunk in client.stream("提取文字"):
            chunks.append(chunk)

    assert chunks == ["你"], "已经吐出的内容应仍然可见"
    assert _FakeModelServer.requests == 1, "吐字之后再卡住不应重试（会重复输出）"


def test_first_token_timeout_leaves_long_output_alone(base_url):
    _FakeModelServer.stall_after_first_line = 0.5
    _FakeModelServer.sse_lines = [
        'data: {"choices":[{"delta":{"content":"好"}}]}',
        'data: {"choices":[{"delta":{"content":"了"}}]}',
        "data: [DONE]",
    ]
    client = OpenAICompatClient(
        base_url=base_url,
        api_key="sk",
        model="m",
        timeout=30.0,
        first_token_timeout=0.2,
        attempts=1,
    )

    assert list(client.stream("提取文字")) == ["好", "了"], (
        "首字到手后超时应放宽，长回答里的停顿不算超时"
    )
