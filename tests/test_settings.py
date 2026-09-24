from ocr_tool.settings import Settings, SettingsStore


def test_returns_usable_defaults_when_no_file_exists(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")

    settings = store.load()

    assert settings.hotkey == "Ctrl+Alt+O"
    assert settings.base_url == "https://api.openai.com/v1"
    assert settings.api_key == ""
    assert settings.model == ""
    assert settings.autostart is False


def test_round_trips_all_fields(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")

    store.save(
        Settings(
            base_url="https://example.com/v1",
            api_key="sk-123",
            model="some-vision-model",
            hotkey="Ctrl+Shift+Q",
            autostart=True,
        )
    )

    loaded = store.load()

    assert loaded.base_url == "https://example.com/v1"
    assert loaded.api_key == "sk-123"
    assert loaded.model == "some-vision-model"
    assert loaded.hotkey == "Ctrl+Shift+Q"
    assert loaded.autostart is True


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
