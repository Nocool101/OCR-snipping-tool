"""把敏感字符串在落盘前用 Windows DPAPI 加密。

DPAPI（`CryptProtectData` / `CryptUnprotectData`）用当前 Windows 账户派生的密钥
加解密，程序不必自己保管密钥，密文也只能被同一账户解开。这能挡住"直接打开配置文件
看到 Key"以及配置被拷贝、进备份、进版本库造成的泄露。

附加熵（optional entropy）是编译进程序的固定字节串。它是廉价的加壳式加固：能让不针对
本程序的通用 DPAPI 解密工具失效，但挡不住专门逆向本程序的人——不是密码学上的额外强度。

边界：以当前用户身份运行的其他程序仍可调用 DPAPI 解开密文，这是本机单用户工具的合理上限。
"""

import base64
import ctypes
import sys

_ENTROPY = b"screenshot-ocr/api-key/v1"
_CRYPTPROTECT_UI_FORBIDDEN = 0x01


class SecretStoreError(Exception):
    """加解密失败，或当前平台不支持 DPAPI。"""


def available() -> bool:
    """当前平台能否使用 DPAPI。本项目面向 Windows。"""
    return sys.platform == "win32"


if not available():

    def protect(text: str) -> str:
        raise SecretStoreError("当前平台不支持 DPAPI，无法加密")

    def unprotect(token: str) -> str:
        raise SecretStoreError("当前平台不支持 DPAPI，无法解密")

else:
    from ctypes import wintypes

    class _DataBlob(ctypes.Structure):
        _fields_ = [
            ("cbData", wintypes.DWORD),
            ("pbData", ctypes.POINTER(ctypes.c_byte)),
        ]

    _crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    _crypt32.CryptProtectData.argtypes = [
        ctypes.POINTER(_DataBlob),
        wintypes.LPCWSTR,
        ctypes.POINTER(_DataBlob),
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(_DataBlob),
    ]
    _crypt32.CryptProtectData.restype = wintypes.BOOL
    _crypt32.CryptUnprotectData.argtypes = [
        ctypes.POINTER(_DataBlob),
        ctypes.c_void_p,
        ctypes.POINTER(_DataBlob),
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(_DataBlob),
    ]
    _crypt32.CryptUnprotectData.restype = wintypes.BOOL
    _kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    _kernel32.LocalFree.restype = ctypes.c_void_p

    def _run(encrypt: bool, data: bytes) -> bytes:
        """调用一次 DPAPI。返回新分配的字节串；输入缓冲在调用期间全程存活。"""
        data_buffer = ctypes.create_string_buffer(data, len(data))
        entropy_buffer = ctypes.create_string_buffer(_ENTROPY, len(_ENTROPY))
        data_blob = _DataBlob(
            len(data), ctypes.cast(data_buffer, ctypes.POINTER(ctypes.c_byte))
        )
        entropy_blob = _DataBlob(
            len(_ENTROPY), ctypes.cast(entropy_buffer, ctypes.POINTER(ctypes.c_byte))
        )
        output = _DataBlob()
        call = (
            _crypt32.CryptProtectData if encrypt else _crypt32.CryptUnprotectData
        )
        ok = call(
            ctypes.byref(data_blob),
            None,
            ctypes.byref(entropy_blob),
            None,
            None,
            _CRYPTPROTECT_UI_FORBIDDEN,
            ctypes.byref(output),
        )
        if not ok:
            raise SecretStoreError(ctypes.WinError(ctypes.get_last_error()))
        try:
            return ctypes.string_at(output.pbData, output.cbData)
        finally:
            _kernel32.LocalFree(output.pbData)

    def protect(text: str) -> str:
        """加密明文，返回可写进 JSON 的 base64 文本。"""
        if not text:
            raise SecretStoreError("空字符串无需加密")
        return base64.b64encode(_run(True, text.encode("utf-8"))).decode("ascii")

    def unprotect(token: str) -> str:
        """还原 `protect` 的结果。密文损坏、或换机器/换账户时抛 `SecretStoreError`。"""
        try:
            raw = base64.b64decode(token, validate=True)
        except ValueError as exc:
            raise SecretStoreError("密文不是合法的 base64") from exc
        if not raw:
            raise SecretStoreError("密文为空")
        try:
            return _run(False, raw).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise SecretStoreError("密文内容不是预期的文本") from exc
