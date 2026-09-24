import pytest

from ocr_tool import secret_store


pytestmark = pytest.mark.skipif(
    not secret_store.available(), reason="DPAPI 仅在 Windows 上可用"
)


def test_round_trips_a_secret():
    token = secret_store.protect("sk-abc123")

    assert token != "sk-abc123"
    assert secret_store.unprotect(token) == "sk-abc123"


def test_ciphertext_differs_from_plaintext():
    token = secret_store.protect("sk-abc123")

    assert "sk-abc123" not in token


def test_the_same_secret_encrypts_to_different_tokens():
    assert secret_store.protect("sk-abc123") != secret_store.protect("sk-abc123")


def test_rejects_an_empty_secret():
    with pytest.raises(secret_store.SecretStoreError):
        secret_store.protect("")


def test_rejects_a_token_that_is_not_base64():
    with pytest.raises(secret_store.SecretStoreError):
        secret_store.unprotect("不是 base64!!")


def test_rejects_a_blob_that_is_not_dpapi_output():
    # 合法 base64，但不是 DPAPI 密文：解密应失败而不是返回乱码。
    with pytest.raises(secret_store.SecretStoreError):
        secret_store.unprotect("bm90LWEtcmVhbC1kcGFwaS1ibG9i")
