import base64
import http.client
import json
import time
import urllib.error
import urllib.request
import uuid
from typing import Iterator, Protocol

USER_AGENT = "screenshot-ocr/0.1 (OpenAI-compatible client)"

DEFAULT_ATTEMPTS = 3
DEFAULT_RETRY_DELAY = 0.4


class ModelError(Exception):
    """与模型通信失败。"""


class MissingApiKey(ModelError):
    """尚未配置 API Key。"""


class ModelAuthError(ModelError):
    """API Key 无效或被拒绝。"""


class ModelResponseError(ModelError):
    """模型服务返回了错误。"""


class ModelTimeout(ModelError):
    """请求超时。"""


class ModelNetworkError(ModelError):
    """网络不通。"""


def _image_media_type(image: bytes) -> str:
    if image.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if image.startswith(b"GIF87a") or image.startswith(b"GIF89a"):
        return "image/gif"
    return "image/png"


class ModelClient(Protocol):
    def stream(self, instruction: str, image: bytes | None = None) -> Iterator[str]:
        """把指令（可带一张图片）交给模型，逐块产出回复文字。"""


class OpenAICompatClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float = 60.0,
        session_id: str | None = None,
        attempts: int = DEFAULT_ATTEMPTS,
        retry_delay: float = DEFAULT_RETRY_DELAY,
    ):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout = timeout
        self._session_id = session_id or uuid.uuid4().hex
        self._attempts = max(1, attempts)
        self._retry_delay = max(0.0, retry_delay)

    def stream(self, instruction: str, image: bytes | None = None) -> Iterator[str]:
        """逐块产出模型回复。

        连接被边缘节点偶发掐断时（一次约百分之几的概率）会重试，
        但**只在还没有产出任何文字之前**重试——已经吐字后再重试会重复输出。
        """
        if not self._api_key:
            raise MissingApiKey("尚未配置 API Key")
        for attempt in range(1, self._attempts + 1):
            produced = False
            try:
                for chunk in self._stream_once(instruction, image):
                    produced = True
                    yield chunk
                return
            except ModelNetworkError:
                if produced or attempt == self._attempts:
                    raise
                time.sleep(self._retry_delay)

    def _stream_once(
        self, instruction: str, image: bytes | None
    ) -> Iterator[str]:
        request = self._build_request(instruction, image)
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                yield from self._parse_events(response)
        except TimeoutError as exc:
            raise ModelTimeout("请求超时") from exc
        except urllib.error.HTTPError as exc:
            detail = self._error_detail(exc)
            if exc.code in (401, 403):
                raise ModelAuthError(f"鉴权失败（HTTP {exc.code}）{detail}") from exc
            raise ModelResponseError(f"模型服务返回错误（HTTP {exc.code}）{detail}") from exc
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise ModelTimeout("请求超时") from exc
            raise ModelNetworkError(f"网络错误：{exc.reason}") from exc
        except OSError as exc:
            # urllib 的 getresponse() 在它自己的 try 之外，服务端在返回响应前
            # 断开时抛出的 RemoteDisconnected 不会被包成 URLError，只能在这里接住。
            raise ModelNetworkError(f"网络错误：{exc}") from exc
        except http.client.HTTPException as exc:
            # BadStatusLine、IncompleteRead 等只继承 HTTPException，不是 OSError。
            raise ModelNetworkError(f"模型服务响应异常：{exc}") from exc

    def _build_request(
        self, instruction: str, image: bytes | None
    ) -> urllib.request.Request:
        if image is None:
            content: str | list = instruction
        else:
            content = [
                {"type": "text", "text": instruction},
                {"type": "image_url", "image_url": {"url": self._data_url(image)}},
            ]
        body = {
            "model": self._model,
            "stream": True,
            "messages": [{"role": "user", "content": content}],
        }
        return urllib.request.Request(
            f"{self._base_url}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
                "User-Agent": USER_AGENT,
                "x-opencode-session": self._session_id,
            },
            method="POST",
        )

    @staticmethod
    def _data_url(image: bytes) -> str:
        encoded = base64.b64encode(image).decode("ascii")
        return f"data:{_image_media_type(image)};base64,{encoded}"

    @staticmethod
    def _parse_events(response) -> Iterator[str]:
        for raw_line in response:
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line.startswith("data:"):
                continue
            payload = line[len("data:") :].strip()
            if payload == "[DONE]":
                return
            try:
                event = json.loads(payload)
            except ValueError:
                continue
            for choice in event.get("choices", []):
                content = choice.get("delta", {}).get("content")
                if content:
                    yield content

    @staticmethod
    def _error_detail(exc: urllib.error.HTTPError) -> str:
        try:
            raw = exc.read().decode("utf-8", errors="replace").strip()
        except Exception:
            return ""
        if not raw:
            return ""
        try:
            return f"：{json.loads(raw)['error']['message']}"
        except (ValueError, KeyError, TypeError):
            return f"：{raw[:200]}"
