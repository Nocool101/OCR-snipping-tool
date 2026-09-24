import json

import pytest

from ocr_tool import secret_store
from ocr_tool.settings import (
    DEFAULT_FONT_SIZE,
    MAX_FONT_SIZE,
    MIN_FONT_SIZE,
    Settings,
    SettingsStore,
)

needs_dpapi = pytest.mark.skipif(
    not secret_store.available(), reason="DPAPI 仅在 Windows 上可用"
)


def test_returns_usable_defaults_when_no_file_exists(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")

    settings = store.load()

    assert settings.hotkey == "Ctrl+Alt+O"
    assert settings.base_url == "https://api.openai.com/v1"
    assert settings.api_key == ""
    assert settings.model == ""
    assert settings.autostart is False
    assert settings.font_size == DEFAULT_FONT_SIZE


def test_round_trips_all_fields(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")

    store.save(
        Settings(
            base_url="https://example.com/v1",
            api_key="sk-123",
            model="some-vision-model",
            hotkey="Ctrl+Shift+Q",
            autostart=True,
            font_size=22,
        )
    )

    loaded = store.load()

    assert loaded.base_url == "https://example.com/v1"
    assert loaded.api_key == "sk-123"
    assert loaded.model == "some-vision-model"
    assert loaded.hotkey == "Ctrl+Shift+Q"
    assert loaded.autostart is True
    assert loaded.font_size == 22


def test_font_size_beyond_the_range_is_clamped(tmp_path):
    path = tmp_path / "settings.json"

    path.write_text('{"font_size": 999}', encoding="utf-8")
    assert SettingsStore(path).load().font_size == MAX_FONT_SIZE

    path.write_text('{"font_size": 1}', encoding="utf-8")
    assert SettingsStore(path).load().font_size == MIN_FONT_SIZE


def test_a_broken_font_size_falls_back_to_the_default(tmp_path):
    path = tmp_path / "settings.json"

    path.write_text('{"font_size": "huge"}', encoding="utf-8")
    assert SettingsStore(path).load().font_size == DEFAULT_FONT_SIZE

    path.write_text('{"font_size": true}', encoding="utf-8")
    assert SettingsStore(path).load().font_size == DEFAULT_FONT_SIZE


def test_missing_fields_fall_back_to_defaults(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text('{"api_key": "sk-abc"}', encoding="utf-8")

    settings = SettingsStore(path).load()

    assert settings.api_key == "sk-abc"
    assert settings.hotkey == "Ctrl+Alt+O"
    assert settings.base_url == "https://api.openai.com/v1"


def test_corrupt_file_falls_back_to_defaults(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{ this is not json", encoding="utf-8")

    settings = SettingsStore(path).load()

    assert settings.hotkey == "Ctrl+Alt+O"
    assert settings.api_key == ""
    assert settings.model == ""


@needs_dpapi
def test_api_key_is_encrypted_on_save(tmp_path):
    path = tmp_path / "settings.json"

    SettingsStore(path).save(Settings(api_key="sk-secret"))

    raw = path.read_text(encoding="utf-8")
    payload = json.loads(raw)
    assert "api_key" not in payload
    assert payload["api_key_enc"]
    assert "sk-secret" not in raw


@needs_dpapi
def test_encrypted_key_round_trips(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")

    store.save(Settings(api_key="sk-secret"))

    assert store.load().api_key == "sk-secret"


@needs_dpapi
def test_undecryptable_key_degrades_to_unconfigured(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps({"api_key_enc": "bm90LWEtcmVhbC1kcGFwaS1ibG9i"}),
        encoding="utf-8",
    )

    assert SettingsStore(path).load().api_key == ""


@needs_dpapi
def test_legacy_plaintext_key_is_migrated_on_load(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps({"api_key": "sk-old", "model": "m"}), encoding="utf-8"
    )

    loaded = SettingsStore(path).load()

    assert loaded.api_key == "sk-old"
    assert loaded.model == "m"
    raw = path.read_text(encoding="utf-8")
    assert "api_key" not in json.loads(raw)
    assert "sk-old" not in raw


@needs_dpapi
def test_migration_does_not_rewrite_an_already_encrypted_file(tmp_path):
    path = tmp_path / "settings.json"
    store = SettingsStore(path)
    store.save(Settings(api_key="sk-secret"))
    before = path.read_text(encoding="utf-8")

    store.load()

    assert path.read_text(encoding="utf-8") == before
